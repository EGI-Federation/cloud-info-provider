import json
import logging
import re
from urllib.parse import urljoin

import glanceclient
import novaclient.client
from cloud_info_provider import exceptions, glue, utils
from cloud_info_provider.providers import base
from keystoneauth1 import loading
from keystoneauth1.exceptions import http as http_exc
from keystoneauth1.loading import base as loading_base
from keystoneauth1.loading import session as loading_session
from novaclient.exceptions import Forbidden


class OpenStackProvider(base.BaseProvider):
    goc_service_type = "org.openstack.nova"
    interface_name = "org.openstack.nova"

    def setup_logging(self):
        super().setup_logging()
        # Remove info log messages from output
        external_logs = [
            "stevedore.extension",
            "requests",
            "urllib3",
            "novaclient",
            "keystoneauth",
            "keystoneclient",
        ]
        log_level = logging.DEBUG if self.opts.debug else logging.WARNING
        for log in external_logs:
            logging.getLogger(log).setLevel(log_level)

    def __init__(self, opts, **kwargs):
        super().__init__(opts, **kwargs)

        # NOTE(aloga): we do not want a project to be passed from the CLI,
        # as we will iterate over it for each configured VO and project.  We
        # have not added these arguments to the parser, but, since the plugin
        # is expecting them when parsing the arguments we need to set them to
        # None before calling the load_auth_from_argparse_arguments. However,
        # we may receive this in the "opts" namespace, therefore we do not set
        # it this is passed.
        if "os_project_name" not in opts:
            opts.os_project_name = None
            opts.os_tenant_name = None
        if "os_project_id" not in opts:
            opts.os_project_id = None
            opts.os_tenant_id = None
        self.project_id = None
        opts.os_auth_url = self.site_config["endpoint"]
        self.os_region = opts.os_region
        self.all_images = not opts.only_appdb_images

        # Select 'public', 'private' or 'all' (default) templates.
        self.select_flavors = opts.select_flavors

        self.flavor_properties = {}
        self.image_properties = {}
        for _opt in vars(self.opts):
            if _opt.startswith("property_flavor_") and not _opt.endswith("_value"):
                opts_k = vars(self.opts)[_opt]
                property_id = re.search(r"property_(\w+)", _opt).group(1)
                opts_v = vars(self.opts).get("_".join([_opt, "value"]), None)
                self.flavor_properties[property_id] = {"key": opts_k, "value": opts_v}
            elif _opt.startswith("property_image"):
                opts_k = vars(self.opts)[_opt]
                property_id = re.search(r"property_(\w+)", _opt).group(1)
                # keep the same structure, although we are not using the _value here
                self.image_properties[property_id] = {"key": opts_k, "value": None}
        self.last_working_auth = None
        self.exit_on_share_errors = self.opts.exit_on_share_errors

    def get_endpoint_id(self):
        return f"{self.site_config['endpoint']}_OpenStack_v3_oidc"

    def get_service_id(self):
        return f"{self.site_config['endpoint']}_cloud.compute"

    def get_manager_id(self):
        return f"{self.site_config['endpoint']}_cloud.compute_manager"

    def build_endpoint(self):
        return super().build_endpoint(
            implementor="OpenStack Foundation",
            implementation_name="OpenStack Nova",
            semantics="https://developer.openstack.org/api-ref/compute",
            # assuming this is correct,
            authentication="oidc",
        )

    def rescope_project(self, auth):
        """Switch to OS project whenever there is a change.

        It updates every OpenStack client used in case of new project.
        """
        project_id = auth["project_id"]
        region_name = auth.get("region_name", None)
        if self.project_id == project_id:
            return
        self.opts.os_project_id = project_id
        self.auth_plugin = loading.load_auth_from_argparse_arguments(self.opts)
        self.session = loading.load_session_from_argparse_arguments(
            self.opts, auth=self.auth_plugin
        )
        self.auth_plugin.invalidate()
        try:
            self.project_id = self.session.get_project_id()
        except http_exc.Unauthorized:
            # FIXME - this should be just reported in the glue and not break anything
            msg = "Could not authorize user in project '%s'" % project_id
            raise exceptions.OpenStackProviderException(msg)

        self.last_working_auth = auth

        # make sure the clients know about the change
        self.nova = novaclient.client.Client(
            2,
            session=self.session,
            region_name=region_name,
        )
        self.glance = glanceclient.Client(
            "2",
            session=self.session,
            region_name=region_name,
        )

    def build_instance_type(self, flavor, share):
        itype = glue.CloudComputingInstanceType(
            id=flavor.id,
            disk=flavor.disk,
            cpu=flavor.vcpus,
            name=flavor.name,
            ram=flavor.ram,
            platform="amd64",
        )
        itype.add_associated_object(share)
        itype.add_associated_object(self.endpoint)
        itype.add_associated_object(self.manager)
        # TODO add infiniband stuff, unclear where that lives in glue
        self.add_glue(itype)

        extra_properties = {}
        for property_id, opt in self.flavor_properties.items():
            v = flavor.get_keys().get(opt["key"])
            if v:
                opts_v = opt["value"]
                if opts_v:
                    extra_properties[property_id] = v == opts_v
                else:
                    extra_properties[property_id] = v
        if extra_properties.get("flavor_gpu_number"):
            acc = glue.CloudComputingVirtualAccelerator(
                id=f"{flavor.id}_gpu",
                name=f"{flavor.name}_gpu",
                type="GPU",
                number=extra_properties.get("flavor_gpu_number"),
                vendor=extra_properties.get("flavor_gpu_vendor", "UNKNOWN"),
                model=extra_properties.get("flavor_gpu_model", "UNKNOWN"),
            )
            acc.add_associated_object(itype)
            itype.add_associated_object(acc)
            self.add_glue(acc)
        return itype

    def build_share_instance_types(self, share):
        ram = []
        cpu = []
        add_all = self.select_flavors == "all"
        itypes = []
        for flavor in self.nova.flavors.list(detailed=True, is_public=None):
            add_pub = self.select_flavors == "public" and flavor.is_public
            add_priv = self.select_flavors == "private" and not flavor.is_public
            if not (add_all or add_pub or add_priv):
                continue
            itype = self.build_instance_type(flavor, share)
            ram.append(itype.ram)
            cpu.append(itype.cpu)
            itypes.append(itype)
        # update share max/min ram and cpu
        share.instance_max_ram = max(ram) if ram else 0
        share.instance_min_ram = min(ram) if ram else 0
        share.instance_max_cpu = max(cpu) if cpu else 0
        share.instance_min_cpu = min(cpu) if cpu else 0
        return itypes

    def build_image(self, image, share):
        image_descr = image.get(
            "vmcatcher_event_dc_description",
            image.get("vmcatcher_event_dc_title", "UNKNOWN"),
        )
        marketplace_url = image.get(
            "vmcatcher_event_ad_mpuri", image.get("marketplace")
        )

        other_info = {}
        try:
            extra_attrs = json.loads(image.get("APPLIANCE_ATTRIBUTES", "{}"))
        except ValueError:
            logging.warning(
                "Unexpected issue while getting json for '%s'",
                image.get("APPLIANCE_ATTRIBUTES", "{}"),
            )
            extra_attrs = {}
        # AppDB and cloud-info-api expect base_mpuri in OtherInfo
        # However atrope/cloudkeeper will push the attribute ad:base_mpuri instead
        # so we need to duplicate this for the time being
        if "ad:base_mpuri" in extra_attrs:
            other_info["base_mpuri"] = extra_attrs["ad:base_mpuri"]
        other_info.update(extra_attrs)

        if not marketplace_url:
            if self.all_images:
                link = urljoin(
                    self.glance.http_client.get_endpoint(), image.get("file")
                )
                marketplace_url = link
            else:
                return None

        glue_image = glue.CloudComputingImage(
            id=image["id"],
            name=image["name"],
            osName=image.get("os_distro", "UNKNOWN"),
            osVersion=image.get("os_version", "UNKNOWN"),
            osPlatform=image.get("architecture", "UNKNOWN"),
            description=image_descr,
            marketplace_url=marketplace_url,
            other_info=other_info,
        )
        glue_image.add_associated_object(share)
        glue_image.add_associated_object(self.endpoint)
        glue_image.add_associated_object(self.manager)
        self.add_glue(glue_image)
        # TODO add associated image objects (Image Network)
        return glue_image

    def build_share_images(self, share):
        image_list = []
        for image in self.glance.images.list(
            detailed=True, filters={"status": "active"}
        ):
            glue_img = self.build_image(image, share)
            if glue_img:
                image_list.append(glue_img)
        return image_list

    def build_share_quotas(self, share):
        """Return the quotas set for the current project."""
        quota_resources = [
            "instances",
            "cores",
            "ram",
            "floating_ips",
            "fixed_ips",
            "metadata_items",
            "injected_files",
            "injected_file_content_bytes",
            "injected_file_path_bytes",
            "key_pairs",
            "security_groups",
            "security_group_rules",
            "server_groups",
            "server_group_members",
        ]
        quotas = {}
        try:
            project_quotas = self.nova.quotas.get(self.project_id)
            for resource in quota_resources:
                try:
                    quotas[resource] = getattr(project_quotas, resource)
                except AttributeError:
                    pass
        except Forbidden:
            # Should we raise an error and make this mandatory?
            pass
        share.max_vm = quotas.get("instances", 0)
        share.other_info.update({"quotas": quotas})
        # also compute current instance count
        running_vm, halted_vm, suspended_vm = 0, 0, 0
        for s in self.nova.servers.list():
            if s.status == "SHUTOFF":
                halted_vm += 1
            elif s.status == "SUSPENDED":
                suspended_vm += 1
            else:  # this includes several cases (i.e. errors), but assume that's ok
                running_vm += 1
        share.running_vm = running_vm
        share.halted_vm = halted_vm
        share.suspended_vm = suspended_vm
        share.total_vm = running_vm + halted_vm + suspended_vm

    def build_shares(self):
        """Builds the share information for every VO"""
        share_objs = []
        rules = []
        total_vm, running_vm, halted_vm, suspended_vm = 0, 0, 0, 0
        max_cpu, min_cpu, max_ram, min_ram = 0, 0, 0, 0
        for vo in self.site_config["vos"]:
            try:
                self.rescope_project(vo["auth"])
            except exceptions.OpenStackProviderException as e:
                if self.exit_on_share_errors:
                    raise e
                else:
                    self.endpoint.health_state = "warn"
                    self.endpoint.health_state_info = str(e)
                    continue
            share_id = f"{self.get_endpoint_id()}_share_{vo['name']}_{self.project_id}"
            name = f"{vo['name']} - {self.project_id} share"
            description = f"Share in service {self.get_endpoint_id()} for VO {vo['name']} (Project {self.project_id})"
            access = self.auth_plugin.get_access(self.session)
            other_info = {
                "project_name": access.project_name,
                "project_domain_name": access.project_domain_name,
            }
            share = glue.Share(
                id=share_id,
                name=name,
                project_id=self.project_id,
                other_info=other_info,
                description=description,
            )
            share.add_associated_object(self.service)
            share.add_associated_object(self.endpoint)
            self.build_share_images(share)
            self.build_share_instance_types(share)
            self.build_share_quotas(share)
            max_ram = max(0, share.instance_max_ram)
            min_ram = min(0, share.instance_min_ram)
            max_cpu = max(0, share.instance_max_cpu)
            min_cpu = min(0, share.instance_min_cpu)
            self.add_glue(share)

            # policies
            rule = f"VO:{vo['name']}"
            rules.append(rule)
            mapping_policy = glue.MappingPolicy(id=f"{share_id}_Policy", rule=[rule])
            mapping_policy.add_associated_object(share)
            mapping_policy.add_association("PolicyUserDomain", vo["name"])
            self.add_glue(mapping_policy)

            running_vm += share.running_vm
            halted_vm += share.halted_vm
            suspended_vm += share.suspended_vm
            total_vm += share.total_vm

        # global policy
        access_policy = glue.AccessPolicy(
            id=f"{self.endpoint.id}_policy",
            rule=rules,
        )
        access_policy.add_associated_object(self.endpoint)
        self.add_glue(access_policy)

        # numbers about VMs in service or manager
        self.service.running_vm = running_vm
        self.service.halted_vm = halted_vm
        self.service.suspended_vm = suspended_vm
        self.service.total_vm = total_vm
        self.manager.instance_max_ram = max_ram
        self.manager.instance_min_ram = min_ram
        self.manager.instance_max_cpu = max_cpu
        self.manager.instance_min_cpu = min_cpu
        return share_objs

    def fetch(self):
        super().fetch()
        if self.last_working_auth:
            self.rescope_project(self.last_working_auth)
            self.endpoint.interface_version = self.nova.api_version.get_string()
            self.endpoint.implementation_version = (
                self.nova.versions.get_current().version
            )
        else:
            self.endpoint.health_state = "UNKNOWN"
            self.endpoint.health_state_info = "No working authentication configured"
        return self.objs

    @staticmethod
    def populate_parser(parser):
        """Populate the argparser 'parser' with the needed options."""
        base.BaseProvider.populate_parser(parser)

        plugins = loading_base.get_available_plugin_names()
        default_auth = "v3password"

        parser.add_argument(
            "--os-auth-type",
            "--os-auth-plugin",
            metavar="<name>",
            default=utils.env("OS_AUTH_TYPE", default=default_auth),
            choices=plugins,
            help="Authentication type to use, available "
            "types are: %s" % ", ".join(plugins),
        )

        # arguments come from session and plugins
        loading_session.register_argparse_arguments(parser)
        for plugin_name in plugins:
            plugin = loading_base.get_plugin_loader(plugin_name)
            # NOTE(aloga): we do not want a project to be passed from the
            # CLI, as we will iterate over it for each configured VO and
            # project. However, as the plugin is expecting them when
            # parsing the arguments we need to set them to None before
            # calling the load_auth_from_argparse_arguments method in the
            # __init__ method of this class.
            for opt in filter(
                lambda x: x.name not in ("project-name", "project-id"),
                plugin.get_options(),
            ):
                parser.add_argument(
                    *opt.argparse_args,
                    default=opt.argparse_default,
                    metavar="<auth-%s>" % opt.name,
                    help=opt.help,
                    dest="os_%s" % opt.dest.replace("-", "_"),
                )

        # somehow region is missing, so adding explicitly
        parser.add_argument("--os-region", default=None, help="OpenStack region to use")

        parser.add_argument(
            "--select-flavors",
            default="all",
            choices=["all", "public", "private"],
            help="Select all (default), public or private flavors.",
        )

        parser.add_argument(
            "--only-appdb-images",
            action="store_true",
            default=False,
            help=(
                "If set, only publish images with AppDB metadata, ignoring the others."
            ),
        )

        # PROPERTIES
        # If "property-<property>-value" is provided, the capability will only
        # be published when the given value matches the one in the flavor
        parser.add_argument(
            "--property-flavor-infiniband",
            metavar="PROPERTY_KEY",
            default="infiniband",
            help='Flavor"s property key for Infiniband support.',
        )

        parser.add_argument(
            "--property-flavor-infiniband-value",
            metavar="PROPERTY_VALUE",
            default="true",
            help=(
                "When Infiniband is supported, this option specifies the "
                "value to match."
            ),
        )

        parser.add_argument(
            "--property-flavor-gpu-number",
            metavar="PROPERTY_KEY",
            default="Accelerator:Number",
            help='Flavor"s property key pointing to number of GPUs.',
        )

        parser.add_argument(
            "--property-flavor-gpu-memory",
            metavar="PROPERTY_KEY",
            default="Accelerator:Memory",
            help='Flavor"s property key pointing to GPU memory.',
        )

        parser.add_argument(
            "--property-flavor-gpu-virt-type",
            metavar="PROPERTY_KEY",
            default="Accelerator:VirtualizationType",
            help='Flavor"s property key pointing to virtualization type.',
        )

        parser.add_argument(
            "--property-flavor-gpu-vendor",
            metavar="PROPERTY_KEY",
            default="Accelerator:Vendor",
            help='Flavor"s property key pointing to the GPU vendor.',
        )

        parser.add_argument(
            "--property-flavor-gpu-model",
            metavar="PROPERTY_KEY",
            default="Accelerator:Model",
            help='Flavor"s property key pointing to the GPU model.',
        )

        parser.add_argument(
            "--property-flavor-gpu-number",
            metavar="PROPERTY_KEY",
            default="Accelerator:Number",
            help='Flavor"s property key pointing to number of GPUs.',
        )

        parser.add_argument(
            "--property-image-gpu-driver",
            metavar="PROPERTY_KEY",
            default="gpu_driver",
            help='Image"s property key to specify the GPU driver version',
        )

        parser.add_argument(
            "--property-image-gpu-cuda",
            metavar="PROPERTY_KEY",
            default="gpu_cuda",
            help='Image"s property key to specify the CUDA toolkit version',
        )

        parser.add_argument(
            "--property-image-gpu-cudnn",
            metavar="PROPERTY_KEY",
            default="gpu_cudnn",
            help='Image"s property key to specify the cuDNN library version',
        )
