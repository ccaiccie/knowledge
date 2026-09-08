from pathlib import Path

p = Path('09-07-26_Azure_Firewall_Insertion_Summary.md')
s = p.read_text()

replacements = {
"| **Azure Firewall in customer-managed hub** |": "| **[Azure Firewall in customer-managed hub](09-05-26-18-55_Azure_Firewall_Customer_Managed_Hub_VNet_Method_1_Deep_Dive.md)** |",
"| **Third-party NVA in customer-managed hub** |": "| **[Third-party NVA in customer-managed hub](09-05-26-19-45_Third_Party_NGFW_NVA_Customer_Managed_Hub_VNet_Method_2_Deep_Dive.md)** |",
"| **Azure Route Server + NVA** |": "| **[Azure Route Server + NVA](09-05-26-13-55_Azure_Route_Server_Third_Party_NVA_Dynamic_Service_Insertion_Study_Guide.md)** |",
"| **Virtual WAN secured hub + Azure Firewall** |": "| **[Virtual WAN secured hub + Azure Firewall](09-05-26-15-56_Azure_Virtual_WAN_Secured_Hub_Method_4_Study_Guide.md)** |",
"| **Integrated NVA in Virtual WAN hub** |": "| **[Integrated NVA in Virtual WAN hub](09-05-26-20-00_Azure_Virtual_WAN_Integrated_Third_Party_NGFW_Direct_Hub_Deep_Dive.md)** |",
"| **Security SaaS Provider in Virtual WAN** |": "| **[Security SaaS Provider in Virtual WAN](09-05-26-16-44_Azure_Virtual_WAN_Security_SaaS_Provider_Method_6_Deep_Dive.md)** |",
"| **Gateway Load Balancer** |": "| **[Gateway Load Balancer](09-05-26-17-03_Gateway_Load_Balancer_Transparent_NVA_Insertion_Study_Guide.md)** |",
"| **Forced tunnel to on-premises** |": "| **[Forced tunnel to on-premises](09-05-26-20-53_Azure_Forced_Tunneling_On_Premises_Internet_Inspection_Deep_Dive.md)** |",
"| **Front Door / Application Gateway WAF** |": "| **[Front Door / Application Gateway WAF](09-06-26-10-24_Azure_Front_Door_Application_Gateway_WAF_Method_9_Deep_Dive.md)** |",
}

for old, new in replacements.items():
    count = s.count(old)
    if count != 1:
        raise SystemExit(f'Expected exactly one match for {old!r}, found {count}')
    s = s.replace(old, new, 1)

p.write_text(s)
