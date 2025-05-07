"""Test fixtures"""


class Data(object):
    @property
    def site_name(self):
        return "SITE_NAME"

    @property
    def endpoint_url(self):
        return "https://foo.example.org:5000/v3"

    @property
    def site_config(self):
        return {
            "gocdb": self.site_name,
            "endpoint": self.endpoint_url,
            "vos": [
                {"name": "foo1", "auth": {"project_id": "bar"}},
                {"name": "foo2", "auth": {"project_id": "baz"}},
            ],
        }


DATA = Data()


class OpenStackFakes(object):
    def __init__(self):
        class FakeObject(object):
            def __init__(self, **kwargs):
                self.d = kwargs
                for k, v in kwargs.items():
                    setattr(self, k, v)

            def get_keys(self):
                return vars(self)

            def get_dict(self):
                return self.d

        flavors = (
            {
                "id": "1",
                "name": "m1.foo",
                "ram": 10,
                "vcpus": 20,
                "is_public": True,
                "disk": 0,
                "ephemeral": 10,
                "infiniband": "true",
            },
            {
                "id": "2",
                "name": "m1 bar",
                "ram": 20,
                "vcpus": 30,
                "is_public": False,
                "disk": 10,
                "ephemeral": 10,
                "gpu_number": 23,
            },
            {
                "id": "3",
                "name": "m1.baz",
                "ram": 2,
                "vcpus": 3,
                "is_public": True,
                "disk": 5,
                "ephemeral": 10,
            },
        )

        self.flavors = [FakeObject(**f) for f in flavors]

        self.servers = [
            FakeObject(status=s)
            for s in (
                "SHUTOFF",
                "SUSPENDED",
                "SUSPENDED",
                "SUSPENDED",
                "SUSPENDED",
                "RUNNING",
                "RUNNING",
                "RUNNING",
            )
        ]

        # XXX add docker information
        # XXX some fake images should include more information from AppDB
        self.images = (
            {
                "name": "fooimage",
                "id": "foo.id",
                "metadata": {},
                "file": "v2/foo.id/file",
                "marketplace": "http://example.org/",
                "APPLIANCE_ATTRIBUTES": '{"ad:base_mpuri": "foobar"}',
                "gpu_driver": "driver-x",
                "gpu_cuda": "CUDA_x.y",
            },
            {
                "name": "barimage",
                "id": "bar id",
                "metadata": {},
                "file": "v2/bar id/file",
            },
            {
                "name": "bazimage",
                "id": "baz id",
                "docker_id": "sha1:xxxxxxxxxxxxxxxxxxxxxxxxxx",
                "docker_tag": "latest",
                "docker_name": "test/image",
                "file": "v2/baz id/file",
            },
        )

        self.quotas = FakeObject(
            instances=4,
            cores=5,
            ram=7,
            floating_ips=1,
            fixed_ips=0,
            metadata_items=4,
            injected_files=7,
            injected_file_content_bytes=8,
            injected_file_path_bytes=9,
            key_pairs=10,
            security_groups=1,
            security_group_rules=2,
            server_groups=4,
            server_group_members=5,
        )

        self.access = FakeObject(project_name="project", project_domain_name="default")

        self.version = FakeObject(version="vy.x")


OS_FAKES = OpenStackFakes()
