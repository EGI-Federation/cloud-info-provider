import json
from datetime import datetime

from cloud_info_provider import glue
from cloud_info_provider.formatters import base


class GLUE21Json(base.BaseFormatter):
    def dump_glue_manager(self, mgr):
        return self.dump_glue_fields(
            mgr,
            {
                "ProductName": "product_name",
                "ProductVersion": "product_version",
                "HypervisorName": "hypervisor_name",
                "HypervisorVersion": "hypervisor_version",
                "TotalCPUs": "total_cpus",
                "TotalRAM": "total_ram",
                "InstanceMaxCPU": "instance_max_cpu",
                "InstanceMinCPU": "instance_min_cpu",
                "InstanceMaxRAM": "instance_max_ram",
                "InstanceMinRAM": "instance_min_ram",
                "NetworkVirtualizationType": "network_virtualization_type",
                "CPUVirtualizationType": "cpu_virtualization_type",
                "ManagerVirtualdiskFormat": "virtual_disk_format",
                "ManagerFailover": "failover",
                "ManagerLiveMigration": "live_migration",
                "ManagerVMBackupRestore": "vm_backup_restore",
            },
        )

    def dump_glue_endpoint(self, ept):
        return self.dump_glue_fields(
            ept,
            {
                "Capability": "capability",
                "QualityLevel": "quality_level",
                "InterfaceName": "interface_name",
                "InterfaceVersion": "interface_version",
                "HealthState": "health_state",
                "HealthStateInfo": "health_state_info",
                "ServingState": "serving_state",
                "Technology": "technology",
                "Implementor": "implementor",
                "ImplementationName": "implementation_name",
                "ImplementationVersion": "implementation_version",
                "DowntimeInfo": "downtime_info",
                "Semantics": "semantics",
                "Authentication": "authentication",
                "IssuerCA": "issuer_ca",
                "TrustedCA": "trusted_cas",
                "URL": "url",
            },
        )

    def dump_glue_image(self, img):
        return self.dump_glue_fields(
            img,
            {
                "MarketplaceURL": "marketplace_url",
                "OSPlatform": "osPlatform",
                "OSName": "osName",
                "OSVersion": "osVersion",
                "Description": "description",
                "AccessInfo": "access_info",
            },
        )

    def dump_glue_instance_type(self, itype):
        return self.dump_glue_fields(
            itype,
            {
                "Platform": "platform",
                "CPU": "cpu",
                "RAM": "ram",
                "Disk": "disk",
                "NetworkIn": "network_in",
                "NetworkOut": "network_out",
                "NetworkInfo": "network_info",
            },
        )

    def dump_glue_share(self, share):
        return self.dump_glue_fields(
            share,
            {
                "InstanceMaxCPU": "instance_max_cpu",
                "InstanceMaxRAM": "instance_max_ram",
                "SLA": "sla",
                "TotalVM": "total_vm",
                "RunningVM": "running_vm",
                "SuspendedVM": "suspended_vm",
                "HaltedVM": "halted_vm",
                "MaxVM": "max_vm",
                "NetworkInfo": "network_info",
                "DefaultNetworkType": "default_network_type",
                "PublicNetworkName": "public_network_name",
                "ProjectID": "project_id",
            },
        )

    def dump_glue_policy(self, policy):
        return self.dump_glue_fields(
            policy,
            {
                "Rule": "rule",
                "Scheme": "scheme",
            },
        )

    def dump_glue_accelerator(self, acc):
        return self.dump_glue_fields(
            acc,
            {
                "Type": "type",
                "Number": "number",
                "Vendor": "vendor",
                "Model": "model",
                "Version": "version",
                "ClockSpeed": "clock_speed",
                "Memory": "memory",
                "ComputeCapability": "compute_capability",
                "VirtualizationType": "virtualization_type",
            },
        )

    def dump_glue_service(self, svc):
        return self.dump_glue_fields(
            svc,
            {
                "Type": "type",
                "QualityLevel": "quality_level",
                "StatusInfo": "status_info",
                "ServiceAUP": "service_aup",
                "Complexity": "complexity",
                "Capability": "capability",
                "TotalVM": "total_vm",
                "RunningVM": "running_vm",
                "SuspendedVM": "suspended_vm",
                "HaltedVM": "halted_vm",
            },
        )

    def dump_glue_fields(self, obj, field_mapping):
        o = {}
        for name, field in field_mapping.items():
            v = getattr(obj, field, None)
            if v is not None:
                if isinstance(v, glue.BoolEnum):
                    o[name] = v.value
                elif isinstance(v, datetime):
                    o[name] = v.isoformat()
                else:
                    o[name] = v
        return o

    def dump_glue_object(self, obj):
        o = self.dump_glue_fields(
            obj,
            {
                "ID": "id",
                "Validity": "validity",
                "CreationTime": "creation_time",
                "Name": "name",
            },
        )
        if obj.other_info:
            o["OtherInfo"] = obj.other_info
        if obj.associations:
            o["Associations"] = obj.associations
        obj_mapping = {
            glue.CloudComputingService: self.dump_glue_service,
            glue.CloudComputingManager: self.dump_glue_manager,
            glue.CloudComputingEndpoint: self.dump_glue_endpoint,
            glue.CloudComputingImage: self.dump_glue_image,
            glue.CloudComputingInstanceType: self.dump_glue_instance_type,
            glue.Share: self.dump_glue_share,
            glue.MappingPolicy: self.dump_glue_policy,
            glue.AccessPolicy: self.dump_glue_policy,
            glue.CloudComputingVirtualAccelerator: self.dump_glue_accelerator,
        }
        f = obj_mapping.get(obj.__class__, None)
        if f:
            o.update(f(obj))
        return o

    def format(self, opts, glue):
        glue_output = {}
        for name, glue_objects in glue.items():
            glue_output[name] = [self.dump_glue_object(o) for o in glue_objects]

        return json.dumps(glue_output, default=str)
