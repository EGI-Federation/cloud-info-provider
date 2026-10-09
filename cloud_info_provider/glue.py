"""
GlueSchema 2.1 Objects
"""

import datetime
from enum import Enum
from typing import Literal

from pydantic import BaseModel


class BoolEnum(Enum):
    """A class to deal with true/false or not known"""

    TRUE = True
    FALSE = False
    UNKNOWN = "UNKNOWN"


class GlueBase(BaseModel):
    id: str
    name: str | None = None
    creation_time: datetime.datetime = datetime.datetime.now(datetime.timezone.utc)
    # 12 hours validity
    validity: int = 3600 * 12
    other_info: dict = {}
    associations: dict = {}

    def add_association(self, name, value):
        assoc = self.associations.get(name, [])
        assoc.append(value)
        self.associations[name] = assoc

    def add_associated_object(self, obj):
        class_name = obj.__class__.__name__
        self.add_association(class_name, obj.id)


class CloudComputingService(GlueBase):
    type: str = "org.cloud.iaas"
    quality_level: Literal["development", "pre-production", "production", "testing"] = (
        "production"
    )
    status_info: str
    service_aup: str = "http://go.egi.eu/aup"
    complexity: str | None = None
    capability: list[str] = [
        "executionmanagement.dynamicvmdeploy",
        "security.accounting",
    ]
    total_vm: int | None = None
    running_vm: int | None = None
    suspended_vm: int | None = None
    halted_vm: int | None = None


class CloudComputingManager(GlueBase):
    product_name: str | None = None
    product_version: str | None = None
    hypervisor_name: str | None = None
    hypervisor_version: str | None = None
    total_cpus: int | None = None
    total_ram: int | None = None
    instance_max_cpu: int | None = None
    instance_min_cpu: int | None = None
    instance_max_ram: int | None = None
    instance_min_ram: int | None = None
    network_virtualization_type: str | None = None
    cpu_virtualization_type: str | None = None
    virtual_disk_format: str | None = None
    failover: BoolEnum | None = None
    live_migration: BoolEnum | None = None
    vm_backup_restore: BoolEnum | None = None


class CloudComputingEndpoint(GlueBase):
    url: str
    capability: list[str] = []
    quality_level: Literal["development", "pre-production", "production", "testing"] = (
        "production"
    )
    serving_state: Literal["closed", "draining", "production", "queueing"] = (
        "production"
    )
    interface_name: str
    interface_version: str | None = None
    # FIXME: This should be actually computed
    health_state: Literal[
        "critical", "ok", "other", "unknown", "warning", "downtime"
    ] = "ok"
    health_state_info: str | None = None
    technology: str = "webservice"
    implementor: str | None = None
    implementation_name: str | None = None
    implementation_version: str | None = None
    downtime_info: str | None = None
    semantics: str | None = None
    authentication: str | None = None
    issuer_ca: str | None = None
    trusted_cas: list[str] | None = None


class CloudComputingImage(GlueBase):
    marketplace_url: str | None = None
    osPlatform: str = ""
    osName: str = ""
    osVersion: str | None = None
    description: str | None = None
    access_info: Literal["none", "passwd", "rsa"] = "none"


class CloudComputingInstanceType(GlueBase):
    platform: str = "UNKNOWN"
    cpu: int = 0
    ram: int = 0
    disk: int = 0
    network_in: BoolEnum = BoolEnum.UNKNOWN
    network_out: BoolEnum = BoolEnum.TRUE
    network_info: str | None = None


class CloudComputingVirtualAccelerator(GlueBase):
    type: str
    number: int = 0
    vendor: str | None = None
    model: str | None = None
    version: str | None = None
    clock_speed: int | None = None
    memory: int | None = None
    compute_capability: list[str] = []
    virtualization_type: str | None = None


class Policy(GlueBase):
    scheme: str = "org.glite.standard"
    rule: list[str] = []


# These two just have different names, but nothing else
class MappingPolicy(Policy):
    pass


class AccessPolicy(Policy):
    pass


class Share(GlueBase):
    instance_max_cpu: int | None = None
    instance_max_ram: int | None = None
    instance_min_cpu: int | None = None
    instance_min_ram: int | None = None
    sla: str | None = None
    total_vm: int | None = None
    running_vm: int | None = None
    suspended_vm: int | None = None
    halted_vm: int | None = None
    max_vm: int | None = None
    project_id: str | None = None
    network_info: str | None = None
    default_network_type: str | None = None
    public_network_name: str | None = None
