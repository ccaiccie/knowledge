from pathlib import Path

p = Path('09-07-26_GCP_Firewall_Insertion_Summary.md')
s = p.read_text()
repls = {
'| **Cloud NGFW Enterprise** |': '| **[Cloud NGFW Enterprise](09-07-26-07-05_GCP_Cloud_NGFW_Enterprise_Firewall_Endpoints_Deep_Dive.md)** |',
'| **VM-Series + NSI** |': '| **[VM-Series + NSI](09-07-26-07-03_Palo_Alto_Networks_Firewalling_in_GCP_Deep_Dive.md)** |',
'| **VM-Series + PBR + internal passthrough NLB** |': '| **[VM-Series + PBR + internal passthrough NLB](09-05-26-08-12_GCP_Policy_Based_Routing_Study_Guide.md)** |',
'| **VM-Series + static route + internal passthrough NLB** |': '| **[VM-Series + static route + internal passthrough NLB](09-06-26-18-58_GCP_Firewall_Inspection_Insertion_Comprehensive_Study_Guide.md)** |',
'| **NCC Router Appliance + BGP** |': '| **[NCC Router Appliance + BGP](09-07-26-09-03_GCP_NCC_Router_Appliance_BGP_Firewall_Insertion_Deep_Dive.md)** |',
'| **Shared VPC centralized architecture** |': '| **[Shared VPC centralized architecture](09-07-26_GCP_Shared_VPC_Centralized_Firewall_Insertion_Method_11_Deep_Dive.md)** |',
}
for old, new in repls.items():
    if old not in s:
        raise SystemExit(f'Missing expected row: {old}')
    s = s.replace(old, new, 1)
p.write_text(s)
