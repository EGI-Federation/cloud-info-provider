import copy
from datetime import datetime
from dateutil.relativedelta import relativedelta
import re

from cloud_info_provider import exceptions, utils
from cloud_info_provider.providers import base, static

try:
    import boto3
except ImportError:
    msg = "Cannot import boto3."
    raise exceptions.AwsProviderException(msg)


class AwsProvider(base.BaseProvider):
    service_type = "compute"
    goc_service_type = None

    def __init__(self, opts):
        super(AwsProvider, self).__init__(opts)

        if not opts.aws_region_code:
            msg = ("You must provide a AWS Region")
            raise exceptions.AwsProviderException(msg)

        self.aws_region_code = opts.aws_region_code
        options = {"region_name": self.aws_region_code}
        if opts.aws_access_key and opts.aws_secret_key:
            options.update({
                "aws_access_key_id": opts.aws_access_key,
                "aws_secret_access_key": opts.aws_secret_key})

        self.aws_client = boto3.client(
            "ec2",
            **options)

        self.goc_service_type = "com.amazonaws.ec2"
        self.all_amis_from = opts.all_amis_from
        self.static = static.StaticProvider(opts)

    def get_site_info(self, **kwargs):
        _fields = (
            "name",
            "is_public",
            "id",
            "country",
            "country_code",
            "roc",
            "subgrid",
            "giis_url",
            "owner_contacts",
            "owner_contacts_iam",
        )
        return self.static.get_site_info(fields=_fields)

    def _normalize_image_values(self, d_images):
        normalized_values = {
            # image_os_type
            "Linux/UNIX": "linux",
            "Windows": "windows",
            "Windows with SQL Server Standard": "windows",
            # image_architecture
            "i386": "i686"
        }
        d = {}
        for k, v in d_images.items():
            value = None
            try:
                value = normalized_values[v]
            except Exception:
                value = v
            d[k] = value
        return d

    def _get_distro_version(self, image_name, distro):
        os_regexp = {
            "centos": r"CentOS Linux ([0-9]) .+",
            "ubuntu": r"ubuntu/images/[\w-].+/ubuntu-\w+-([0-9]{2}\.[0-9]{2})",
            "windows": r"Windows_Server-([0-9]{4})-"
        }
        try:
            version = re.search(os_regexp[distro], image_name).groups()[0]
        except KeyError:
            msg = "Distribution \"%s\" not supported." % distro
            raise exceptions.AwsProviderException(msg)
        except IndexError:
            version = None
        return version

    def _filter_amis_by_creation_date(self, amis):
        l_amis = []
        all_amis_from_datetime = datetime.strptime(
            self.all_amis_from,
            "%Y-%m-%d")
        for ami in amis:
            creation_datetime = datetime.strptime(
                ami["CreationDate"],
                "%Y-%m-%dT%H:%M:%S.%fZ")
            if creation_datetime > all_amis_from_datetime:
                l_amis.append(ami)
        return l_amis

    def get_images(self, **kwargs):
        images = {}

        template = {
            "image_name": None,
            "image_id": None,
            "image_native_id": None,
            "image_description": None,
            "image_version": None,
            "image_marketplace_id": None,
            "image_platform": "amd64",
            "image_os_family": None,
            "image_os_name": None,
            "image_os_version": None,
            "image_os_type": None,
            "image_minimal_cpu": None,
            "image_recommended_cpu": None,
            "image_minimal_ram": None,
            "image_recommended_ram": None,
            "image_minimal_accel": None,
            "image_recommended_accel": None,
            "image_accel_type": None,
            "image_size": None,
            "image_traffic_in": [],
            "image_traffic_out": [],
            "image_access_info": "none",
            "image_context_format": None,
            "image_software": [],
            "other_info": [],
            "architecture": None,
            "os_distro": None,
        }
        defaults = self.static.get_image_defaults(prefix=True)

        # FIXME(orviz) Use filters from file
        _filters = {
            "ubuntu": [
                {"Name": "architecture",
                    "Values": ["x86_64"]},
                {"Name": "state",
                    "Values": ["available"]},
                {"Name": "root-device-type",
                    "Values": ["ebs"]},
                {"Name": "is-public",
                    "Values": ["true"]},
                {"Name": "name",
                    "Values": ["ubuntu/images/*"]},
                {"Name": "owner-id",
                    "Values": ["099720109477"]}
            ],
            "centos": [
                {"Name": "architecture",
                    "Values": ["x86_64"]},
                {"Name": "state",
                    "Values": ["available"]},
                {"Name": "root-device-type",
                    "Values": ["ebs"]},
                {"Name": "is-public",
                    "Values": ["true"]},
                {"Name": "product-code",
                    "Values": ["aw0evgkw8e5c1q413zgy5pjce"]},
                {"Name": "owner-id",
                    "Values": ["679593333241"]}
            ],
            "windows": [
                {"Name": "platform",
                    "Values": ["windows"]},
                {"Name": "owner-id",
                    "Values": ["801119661308"]},
                {"Name": "name",
                    "Values": ["Windows_Server*English*Standard*"]}
            ]
        }
        for _distro, _filter in _filters.items():
            image_data = self.aws_client.describe_images(
                ExecutableUsers=["all"],
                Filters=_filter)
            _images = self._filter_amis_by_creation_date(
                image_data["Images"])
            for image in _images:
                img_id = image.get("ImageId")

                aux_img = copy.deepcopy(template)
                aux_img.update(defaults)
                aux_img.update(image)

                _image_os_version = self._get_distro_version(
                    image.get("Name"),
                    _distro)
                aux_img.update({
                    "id": image.get("ImageId"),
                    "image_name": image.get("Name"),
                    "image_architecture": image.get("Architecture"),
                    "image_os_type": image.get("PlatformDetails"),
                    "image_os_name": _distro,
                    "image_os_version": _image_os_version,
                    "image_marketplace_id": image.get("ImageLocation"),
                })
                images[img_id] = self._normalize_image_values(aux_img)

        return images

    def get_templates(self, **kwargs):
        flavors = {}
        defaults = {
            "template_platform": "amd64",
            "template_network": "private",
            "template_memory": 0,
            "template_ephemeral": 0,
            "template_disk": 0,
            "template_cpu": 0,
            "template_infiniband": False,
            "template_flavor_gpu_number": 0,
            "template_flavor_gpu_vendor": None,
            "template_flavor_gpu_model": None,
        }
        defaults.update(self.static.get_template_defaults(prefix=True))

        _filters = [
            {"Name": "bare-metal",
                "Values": ["false"]},
            {"Name": "current-generation",
                "Values": ["true"]},
        ]

        _flavors = self.aws_client.describe_instance_types(Filters=_filters)
        for flavor in _flavors["InstanceTypes"]:
            flavor_id = flavor.get("InstanceType")
            aux = defaults.copy()
            vcpu_info = flavor.get("VCpuInfo")
            mem_info = flavor.get("MemoryInfo")
            storage_info = flavor.get("InstanceStorageInfo")
            if None in (vcpu_info, mem_info, storage_info):
                continue
            aux.update({"flavor_id": flavor_id,
                        "flavor_name": flavor_id,
                        "tenant_id": flavor_id,
                        "template_memory": mem_info.get("SizeInMiB"),
                        "template_disk": storage_info.get("TotalSizeInGB"),
                        "template_cpu": vcpu_info.get("DefaultVCpus")})
            flavors[flavor_id] = aux
        return flavors

    def get_compute_endpoints(self, **kwargs):
        endp = [
            region["Endpoint"]
            for region in self.aws_client.describe_regions()["Regions"]
            if region["RegionName"] == self.aws_region_code][0]
        return {"compute_service_name": endp}

    @staticmethod
    def populate_parser(parser):
        parser.add_argument(
            "--aws-region",
            default=utils.env("AWS_DEFAULT_REGION"),
            dest="aws_region_code",
            help=(
                "Specify AWS Region Code "
                "(e.g. us-east-2, ap-south-1, eu-west-3))"
            ),
        )
        parser.add_argument(
            "--aws-access-key",
            default=utils.env("AWS_ACCESS_KEY_ID"),
            dest="aws_access_key",
            help="Specify AWS Access Key ID",
        )
        parser.add_argument(
            "--aws-secret-key",
            default=utils.env("AWS_SECRET_ACCESS_KEY"),
            dest="aws_secret_key",
            help=(
                "Specify AWS Secret Access Key for "
                "the provided AWS Access Key ID"
            ),
        )
        parser.add_argument(
            "--all-amis-from",
            metavar="DATE",
            default=(
                datetime.now() - relativedelta(years=1)).strftime("%Y-%m-%d"),
            dest="all_amis_from",
            help=(
                "Starting date from which the creation date "
                "of the AMIs are valid. Date format is "
                "YYYY-MM-DD, and the default is one year "
                "back from the current date."
            ),
        )
