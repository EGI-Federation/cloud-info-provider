from datetime import datetime

from cloud_info_provider.formatters import base


class GLUE(base.BaseFormatter):
    def __init__(self):
        self.template_extension = "ldif"
        self.templates = [
            "headers",
            "clouddomain",
            "compute",
            "storage",
        ]


class GLUE21(base.BaseFormatter):
    def __init__(self):
        self.template_extension = "glue21"
        self.templates = [
            "headers",
            "clouddomain",
            "compute",
            "storage",
        ]


class GLUE21Json(base.BaseFormatter):
    def __init__(self):
        self.template_extension = "glue21.json.tpl"
        self.templates = [
            "compute",
        ]
        self.glue_dict = {}
        self.creation_time = datetime.now().isoformat()
        self.validity = 3600

    def _glue_dict_if_def(self, what, name, where):
        if what in where:
            return {name: where[what]}
        else:
            return {}

    def _dict_append(self, new):
        for k, v in new.items():
            if k in self.glue_dict:
                self.glue_dict[k].extend(v)
            else:
                self.glue_dict[k] = v

    def _glue_obj(self, obj_id, name):
        return {
            "CreationTime": self.creation_time,
            "Validity": self.validity,
            "ID": obj_id,
            "Name": name,
        }

    def glue_manager(self, info):
        # We may not have any template!
        templates_cpu = [
            tpl["template_cpu"]
            for vo, share in self.shares.items()
            for tpl_id, tpl in share["templates"].items()
        ]
        if templates_cpu:
            template_max_cpu = max(templates_cpu)
            template_min_cpu = min(templates_cpu)
        else:
            template_max_cpu = 0
            template_min_cpu = 0

        templates_memory = [
            tpl["template_memory"]
            for vo, share in self.shares.items()
            for tpl_id, tpl in share["templates"].items()
        ]
        if templates_memory:
            template_max_memory = max(templates_memory)
            template_min_memory = min(templates_memory)
        else:
            template_max_memory = 0
            template_min_memory = 0
        manager = self._glue_obj(
            self.compute_service_manager,
            f"Cloud Manager for {self.static_compute_info['compute_service_name']}",
        )
        manager.update(
            {
                "ProductName": self.static_compute_info["compute_hypervisor"],
                "ProductVersion": self.static_compute_info[
                    "compute_hypervisor_version"
                ],
                "HypervisorName": self.static_compute_info["compute_hypervisor"],
                "HypervisorVersion": self.static_compute_info[
                    "compute_hypervisor_version"
                ],
                "Associations": {
                    "CloudComputingService": self.compute_service_id,
                },
                "TotalCPUs": self.static_compute_info["compute_total_cores"],
                "TotalRAM": self.static_compute_info["compute_total_ram"],
                "InstanceMaxCPU": template_max_cpu,
                "InstanceMinCPU": template_min_cpu,
                "InstanceMaxRAM": template_max_memory,
                "InstanceMinRAM": template_min_memory,
            }
        )
        manager.update(
            self._glue_dict_if_def(
                "compute_network_virt_type",
                "NetworkVirtualizationType",
                self.static_compute_info,
            )
        )
        manager.update(
            self._glue_dict_if_def(
                "compute_cpu_virt_type",
                "CPUVirtualizationType",
                self.static_compute_info,
            )
        )
        manager.update(
            self._glue_dict_if_def(
                "compute_virtual_disk_formats",
                "ManagerVirtualdiskFormat",
                self.static_compute_info,
            )
        )
        manager.update(
            self._glue_dict_if_def(
                "compute_failover",
                "ManagerFailover",
                self.static_compute_info,
            )
        )
        manager.update(
            self._glue_dict_if_def(
                "compute_live_migration",
                "ManagerLiveMigration",
                self.static_compute_info,
            )
        )
        manager.update(
            self._glue_dict_if_def(
                "compute_vm_backup_restore",
                "ManagerVMBackupRestore",
                self.static_compute_info,
            )
        )
        self._dict_append({"CloudComputingManager": manager})

    def _endpoint_id(self, ep):
        return (
            f"{ep['compute_endpoint_url']}_{ep['compute_api_type']}"
            f"_{ep['compute_api_version']}_{ep['compute_api_authn_method']}"
        )

    def glue_endpoints(self, info):
        endpoints = []
        for url, endpoint in self.all_endpoints.items():
            if endpoint["compute_api_type"] == "OpenStack":
                interface_name = "org.openstack.nova"
                endpoint_semantics = "https://developer.openstack.org/api-ref/compute"
            elif endpoint["compute_api_type"] == "OpenNebula":
                interface_name = "org.opennebula.compute"
                endpoint_semantics = "UNKNOWN"
            else:
                endpoint_semantics = "http://occi-wg.org/about/specification"
                interface_name = "eu.egi.cloud.vm-management.occi"
            endpoint_id = self._endpoint_id(endpoint)
            ep_obj = self._glue_obj(
                endpoint_id, f"Cloud computing endpoint for {endpoint_id}"
            )
            ep_obj.update(
                {
                    "URL": endpoint["compute_endpoint_url"],
                    "Associations": {
                        "CloudComputingService": [self.compute_service_id],
                    },
                    "Capability": endpoint.get("compute_capabiliities", []),
                    "QualityLevel": endpoint["compute_production_level"],
                    "InterfaceName": interface_name,
                    "InterfaceVersion": endpoint["compute_api_version"],
                    "HealthState": "ok",
                    "HealthStateInfo": "Endpoint functioning properly",
                    "ServingState": endpoint["compute_production_level"],
                    "Technology": endpoint["compute_api_endpoint_technology"],
                    "Implementor": endpoint["compute_middleware_developer"],
                    "ImplementationName": endpoint["compute_middleware"],
                    "ImplementationVersion": endpoint["compute_middleware_version"],
                    "DowntimeInfo": (
                        "See the GOC DB for downtimes: "
                        f"https://goc.egi.eu/portal/index.php?Page_Type=Downtimes_Calendar&site={self.site_name}"
                    ),
                    "Semantics": endpoint_semantics,
                    "Authentication": endpoint["compute_api_authn_method"],
                    "IssuerCA": endpoint["endpoint_issuer"],
                    "TrustedCA": endpoint["endpoint_trusted_cas"],
                }
            )
            endpoints.append(ep_obj)
        self._dict_append({"CloudComputingEndpoint": endpoints})

    def count_instance_status(self, instances, status):
        return len([i for i in instances.values() if i["instance_status"] == status])

    def glue_service(self):
        instances = {
            instance_id: instance
            for vo, share in self.shares.items()
            for instance_id, instance in share["instances"].items()
        }
        service = self._glue_obj(
            self.compute_service_id, f"Cloud Compute service on {self.site_name}"
        )
        service.update(
            {
                "Type": "org.cloud.iaas",
                "QualityLevel": self.static_compute_info[
                    "compute_service_production_level"
                ],
                "StatusInfo": f"http://argo.egi.eu/lavoisier/status_report-sf?site={self.site_name}",
                "ServiceAUP": "http://go.egi.eu/aup",
                "Complexity": f"endpointType=2,share={len(self.shares)}",
                "Capability": [
                    c for c in self.static_compute_info["compute_capabilities"]
                ],
                "TotalVM": len(instances),
                "RunningVM": self.count_instance_status(instances, "ACTIVE"),
                "SuspendedVM": self.count_instance_status(instances, "SUSPENDED"),
                "HaltedVM": self.count_instance_status(instances, "SHUTOFF"),
                "Associations": [{"AdminDomain": [self.site_name]}],
            }
        )
        if "gocdb_id" in self.static_compute_info:
            service.update(
                {"OtherInfo": {"gocdb_id": self.static_compute_info["gocdb_id"]}}
            )
        self._dict_append({"CloudComputingService": [service]})

    def glue_templates(self, share, share_id):
        templates = []
        gpu_templates = []
        for template_native_id, template in share["templates"].items():
            for ep in share.get("endpoints", {}).get("endpoints", {}).values():
                native_endpoint = ep["compute_api_type"] != "OCCI"
                id_field = "template_native_id" if native_endpoint else "template_id"
                name_field = (
                    "template_name" if "template_name" in template else id_field
                )
                tpl_obj = self._glue_obj(template[id_field], template[name_field])
                gpu_number = template.get("template_flavor_gpu_number", 0)

                tpl_obj.update(
                    {
                        "Associations": {
                            "Share": [share_id],
                            "CloudComputingManager": self.compute_service_manager,
                            "CloudComputingEndpoint": [self._endpoint_id(ep)],
                        },
                        "Platform": template["template_platform"],
                        "CPU": template["template_cpu"],
                        "RAM": template["template_memory"],
                        "NetworkIn": template.get("template_network_in", "UNKNOWN"),
                        "NetworkOut": template.get("template_network_out", "UNKNOWN"),
                        "NetworkInfo": share["network_info"],
                        "Disk": template["template_disk"],
                    }
                )
                if template.get("template_ephemeral"):
                    tpl_obj["EphemeralStorage"] = template["template_ephemeral"]
                if gpu_number:
                    gpu_tpl_id = f"{template[id_field]}_gpu"
                    gpu_tpl_name = f"{template[name_field]}_gpu"
                    tpl_obj["Associations"][
                        "CloudComputingInstanceTypeCloudComputingVirtualAccelerator"
                    ] = gpu_tpl_id
                    gpu_obj = {
                        "ID": gpu_tpl_id,
                        "Name": gpu_tpl_name,
                        "Associations": {
                            "CloudComputingVirtualAcceleratorCloudComputingInstanceType": template[
                                id_field
                            ],
                        },
                        "Type": "GPU",
                        "Number": gpu_number,
                    }
                    for field_name, field_value in (
                        ("Vendor", "template_flavor_gpu_vendor"),
                        ("Model", "template_flavor_gpu_model"),
                        ("Version", "template_flavor_gpu_version"),
                        ("Memory", "template_flavor_gpu_memory"),
                    ):
                        if field_value in template:
                            gpu_obj[field_name] = template[field_value]
                    gpu_templates.append(gpu_obj)
                templates.append(tpl_obj)
        self._dict_append(
            {
                "CloudComputingInstanceType": templates,
                "CloudComputingVirtualAccelerator": gpu_templates,
            }
        )

    def glue_images(self, share, share_id):
        images = []
        image_network = []
        # XXX wrong
        field_mapping = [
            ("MarketPlaceURL", "image_marketplace_id"),
            ("OSPlatform", "image_platform"),
            ("OSFamily", "image_os_family"),
            ("OSName", "image_os_name"),
            ("OSVersion", "image_os_version"),
            ("Version", "image_version"),
            ("MinCPU", "image_minimal_cpu"),
            ("RecommendedCPU", "image_recommended_cpu"),
            ("MinRAM", "image_minimal_ram"),
            ("RecommendedRAM", "image_recommended_ram"),
            ("MinAccelerators", "image_minimal_accel"),
            ("RecommendedAccelerators", "image_recommended_accel"),
            ("RecommendedAcceleratorType", "image_accel_type"),
            ("Description", "image_description"),
            ("DiskSize", "image_size"),
            ("AccessInfo", "image_access_info"),
            ("ContextualizationName", "image_context_format"),
            ("Installedsoftware", "image_software"),
            ("OtherInfo", "other_info"),
        ]

        for image_native_id, image in share["images"].items():
            for ep in share.get("endpoints", {}).get("endpoints", {}).values():
                native_endpoint = ep["compute_api_type"] != "OCCI"
                id_field = "image_native_id" if native_endpoint else "image_id"
                img_obj = self._glue_obj(image[id_field], image["image_name"])
                img_obj["Associations"] = {
                    "Share": [share_id],
                    "CloudComputingManager": self.compute_service_manager,
                    "CloudComputingEndpoint": [self._endpoint_id(ep)],
                }

                for field_name, field_value in field_mapping:
                    if image.get(field_value, None):
                        img_obj[field_name] = image[field_value]

                images.append(img_obj)

                # image network configuration
                network_types = (
                    ("inbound", "network_traffic_in"),
                    ("outbound", "network_traffic_out"),
                )
                for network_type, network_traffic in network_types:
                    for idx, network_conf in enumerate(image.get(network_traffic, [])):
                        network_conf_id = (
                            f"{network_type}_{network_conf['ad:net_protocol']}_{idx}"
                        )
                        network_obj = {
                            "ID": network_conf_id,
                            "Associations": {
                                "CloudComputingImage": image[id_field],
                            },
                            "Direction": network_type,
                            "Protocol": network_conf["ad:net_protocol"],
                            "Port": network_conf["ad:net_port"],
                            "AddressRange": network_conf["ad:net_range"],
                        }
                        img_assoc = image["Associations"].get(
                            "ImageNetworkConfiguration", []
                        )
                        img_assoc.append(network_conf_id)
                        img_obj["Associations"]["ImageNetworkConfiguration"] = img_assoc
                        image_network.append(network_obj)

        self._dict_append(
            {
                "CloudComputingImage": images,
                "CloudComputingImageNetwokConfiguration": image_network,
            }
        )

    def glue_access_policy(self, share, share_id, vo):
        for ep in share.get("endpoints", {}).get("endpoints", {}).values():
            endpoint_id = self._endpoint_id(ep)
            self._dict_append(
                {
                    "AccessPolicy": [
                        {
                            "ID": f"{endpoint_id}_Policy",
                            "Name": f"Access control rules for {vo} on {endpoint_id}",
                            "Associations": {
                                "CloudComputingEndpoint": endpoint_id,
                            },
                            "Scheme": "org.glite.standard",
                            "PolicyRule": f"VO:{vo}",
                        }
                    ]
                }
            )
        self._dict_append(
            {
                "MappingPolicy": [
                    {
                        "ID": f"{share_id}_Policy",
                        "Associations": {
                            "Share": share_id,
                            # XXX this seems wrong
                            "PolicyUserDomain": vo,
                        },
                        "Rule": share["membership"],
                    }
                ],
            }
        )

    def glue_shares(self, info):
        shares = []
        for vo, share in self.shares.items():
            share_id = "%s_share_%s_%s" % (
                self.compute_service_id,
                vo,
                share["project"],
            )
            share_instances = share["instances"]

            running_instances = len(
                [
                    i
                    for i in share_instances.values()
                    if i["instance_status"] == "ACTIVE"
                ]
            )
            suspended_instances = len(
                [
                    i
                    for i in share_instances.values()
                    if i["instance_status"] == "SUSPENDED"
                ]
            )
            halted_instances = len(
                [
                    i
                    for i in share_instances.values()
                    if i["instance_status"] == "SHUTOFF"
                ]
            )

            share_templates_cpu = [
                tpl["template_cpu"] for tpl_id, tpl in share["templates"].items()
            ]
            if share_templates_cpu:
                share_template_max_cpu = max(share_templates_cpu)
            else:
                share_template_max_cpu = 0

            share_templates_memory = [
                tpl["template_memory"] for tpl_id, tpl in share["templates"].items()
            ]
            if share_templates_memory:
                share_template_max_memory = max(share_templates_memory)
            else:
                share_template_max_memory = 0

            endpoints = share.get("endpoints", {}).get("endpoints", {})

            # This is commented out as we are not using it
            # if share["instance_max_accelerators"]:
            #     share_max_accelerators = share["instance_max_accelerators"]
            # else:
            #     share_max_accelerators = self.static_compute_info[
            #         "compute_max_accelerators"
            #     ]

            quotas = share["quotas"]
            if "instances" in quotas:
                share_max_vm = quotas["instances"]
            else:
                share_max_vm = False

            fields = {
                "sla",
                "network_info",
                "default_network_type",
                "public_network_name",
            }
            for field in fields:
                if field not in share or share[field] is None:
                    share[field] = "UNKNOWN"

            share_dict = {
                "ID": share_id,
                "Name": f"Share in service {self.compute_service_id} for VO {vo} (Project {share['project']})",
                "Associations": {
                    "CloudComputingService": [self.compute_service_id],
                    "CloudComputingEndpoint": [
                        self._endpoint_id(ep) for ep in endpoints.values()
                    ],
                },
                "Description": f"Share in service {self.compute_service_id} for VO {vo} (Project {share['project']})",
                "InstanceMaxCPU": share_template_max_cpu,
                "InstanceMaxRAM": share_template_max_memory,
                "SLA": share["sla"],
                "TotalVM": len(share_instances),
                "RunningVM": running_instances,
                "SuspendedVM": suspended_instances,
                "HaltedVM": halted_instances,
                "NetworkInfo": share["network_info"],
                "DefaultNetworkType": share["default_network_type"],
                "PublicNetworkName": share["public_network_name"],
                "ProjectID": share["project"],
            }
            if share_max_vm:
                share_dict.update({"MaxVM": share_max_vm})
            other_info = {}
            if share["project_name"]:
                other_info["project_name"] = share["project_name"]
            if share["project_domain_name"]:
                other_info["project_domain_name"] = share["project_domain_name"]
            if other_info:
                share_dict.update({"OtherInfo": other_info})
            shares.append(share_dict)
            self.glue_images(share, share_id)
            self.glue_templates(share, share_id)
            self.glue_access_policy(share, share_id, vo)
        self._dict_append({"Share": shares})

    def build_glue(self, info):
        self.static_compute_info = info["static_compute_info"]
        self.site_name = self.static_compute_info["site_name"]
        self.shares = info["shares"]
        self.compute_service_id = (
            self.static_compute_info["compute_service_name"] + "_cloud.compute"
        )
        self.compute_service_manager = self.compute_service_id + "_manager"
        self.all_endpoints = {
            url: endpoint
            for vo, share in self.shares.items()
            for url, endpoint in share.get("endpoints", {}).get("endpoints", {}).items()
        }
        self.glue_service()
        self.glue_manager(info)
        self.glue_endpoints(info)
        self.glue_shares(info)
        return self.glue_dict

    def _format_template(self, template, info, extra={}):
        # do not mess with formatting in mako, build here our JSON
        glue_info = self.build_glue(info)
        extra.update({"glue": glue_info})
        return super()._format_template(template, info, extra)
