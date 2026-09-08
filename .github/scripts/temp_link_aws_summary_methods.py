from pathlib import Path

p = Path('09-07-26_AWS_Firewall_Insertion_Summary.md')
s = p.read_text()

replacements = {
"| **AWS Network Firewall in a VPC** |": "| **[AWS Network Firewall in a VPC](09-06-26-15-03_AWS_Firewall_Inspection_Insertion_Comprehensive_Study_Guide.md)** |",
"| **TGW-attached AWS Network Firewall** |": "| **[TGW-attached AWS Network Firewall](09-06-26-15-03_AWS_Firewall_Inspection_Insertion_Comprehensive_Study_Guide.md)** |",
"| **Distributed GWLBE** |": "| **[Distributed GWLBE](09-06-26-15-23_Distributed_GWLBE_Centralized_Third_Party_Firewall_Fleet_Deep_Dive.md)** |",
"| **TGW + GWLB inspection VPC** |": "| **[TGW + GWLB inspection VPC](09-06-26-15-45_TGW_Centralized_GWLB_GWLBE_Inspection_VPC_Deep_Dive.md)** |",
"| **Legacy TGW + direct NVA VPC** |": "| **[Legacy TGW + direct NVA VPC](09-06-26-16-41_Legacy_TGW_NVA_VPC_Attachment_Deep_Dive.md)** |",
"| **Cloud WAN service insertion** |": "| **[Cloud WAN service insertion](09-06-26-17-01_AWS_Cloud_WAN_Service_Insertion_Deep_Dive.md)** |",
"| **VPC Route Server + NVA** |": "| **[VPC Route Server + NVA](09-06-26-17-01_AWS_VPC_Route_Server_NVA_Dynamic_Service_Insertion_Deep_Dive.md)** |",
"| **AWS WAF / CloudFront / ALB** |": "| **[AWS WAF / CloudFront / ALB](09-06-26-15-03_AWS_Firewall_Inspection_Insertion_Comprehensive_Study_Guide.md)** |",
}

for old, new in replacements.items():
    count = s.count(old)
    if count != 1:
        raise SystemExit(f'Expected exactly one match for {old!r}, found {count}')
    s = s.replace(old, new, 1)

p.write_text(s)
