"""
GlueSchema 2.1 Objects
"""

import datetime
from enum import Enum
from typing import Optional

from pydantic import BaseModel


class BoolEnum(Enum):
    """A class to deal with true/false or not known"""

    TRUE = True
    FALSE = False
    UNKNOWN = "UNKNOWN"


class GlueBase(BaseModel):
    id: str
    name: Optional[str] = None
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
    quality_level: str = "production"
    status_info: str
    service_aup: str = "http://go.egi.eu/aup"
    complexity: Optional[str] = None
    capability: list[str] = [
        "executionmanagement.dynamicvmdeploy",
        "security.accounting",
    ]
    total_vm: Optional[int] = None
    running_vm: Optional[int] = None
    suspended_vm: Optional[int] = None
    halted_vm: Optional[int] = None


class CloudComputingManager(GlueBase):
    product_name: Optional[str] = None
    product_version: Optional[str] = None
    hypervisor_name: Optional[str] = None
    hypervisor_version: Optional[str] = None
    total_cpus: Optional[int] = None
    total_ram: Optional[int] = None
    instance_max_cpu: Optional[int] = None
    instance_min_cpu: Optional[int] = None
    instance_max_ram: Optional[int] = None
    instance_min_ram: Optional[int] = None
    network_virtualization_type: Optional[str] = None
    cpu_virtualization_type: Optional[str] = None
    virtual_disk_format: Optional[str] = None
    failover: Optional[BoolEnum] = None
    live_migration: Optional[BoolEnum] = None
    vm_backup_restore: Optional[BoolEnum] = None


class CloudComputingEndpoint(GlueBase):
    url: str
    capability: list[str] = []
    quality_level: str = "production"
    serving_state: str = "production"
    interface_name: str
    interface_version: Optional[str] = None
    # FIXME: This should be actually computed
    health_state: str = "ok"
    health_state_info: Optional[str] = None
    technology: str = "webservice"
    implementor: Optional[str] = None
    implementation_name: Optional[str] = None
    implementation_version: Optional[str] = None
    downtime_info: Optional[str] = None
    semantics: Optional[str] = None
    authentication: Optional[str] = None
    issuer_ca: Optional[str] = None
    trusted_cas: Optional[list[str]] = None


class CloudComputingImage(GlueBase):
    marketplace_url: Optional[str] = None
    osPlatform: str = ""
    osName: str = ""
    osVersion: Optional[str] = None
    description: Optional[str] = None
    access_info: str = "none"


class CloudComputingInstanceType(GlueBase):
    platform: str = "UNKNOWN"
    cpu: int = 0
    ram: int = 0
    disk: int = 0
    network_in: BoolEnum = BoolEnum.UNKNOWN
    network_out: BoolEnum = BoolEnum.TRUE
    network_info: Optional[str] = None


class CloudComputingVirtualAccelerator(GlueBase):
    type: str
    number: int = 0
    vendor: Optional[str] = None
    model: Optional[str] = None
    version: Optional[str] = None
    clock_speed: Optional[int] = None
    memory: Optional[int] = None
    compute_capability: list[str] = []
    virtualization_type: Optional[str] = None


class Policy(GlueBase):
    scheme: str = "org.glite.standard"
    rule: list[str] = []


# These two just have different names, but nothing else
class MappingPolicy(Policy):
    pass


class AccessPolicy(Policy):
    pass


class Share(GlueBase):
    instance_max_cpu: Optional[int] = None
    instance_max_ram: Optional[int] = None
    instance_min_cpu: Optional[int] = None
    instance_min_ram: Optional[int] = None
    sla: Optional[str] = None
    total_vm: Optional[int] = None
    running_vm: Optional[int] = None
    suspended_vm: Optional[int] = None
    halted_vm: Optional[int] = None
    max_vm: Optional[int] = None
    project_id: Optional[str] = None
    network_info: Optional[str] = None
    default_network_type: Optional[str] = None
    public_network_name: Optional[str] = None
