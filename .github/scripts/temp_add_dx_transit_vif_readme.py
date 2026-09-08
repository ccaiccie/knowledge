from pathlib import Path
p = Path('README.md')
s = p.read_text()
entry = '''### [AWS Direct Connect Transit VIF — Deep Dive](09-08-26_AWS_Direct_Connect_Transit_VIF_Deep_Dive.md)\nDeep dive into AWS Direct Connect transit virtual interfaces for Transit Gateway connectivity. Separates the physical Direct Connect connection, transit VIF, Direct Connect gateway, Transit Gateway, TGW route tables, and VPC route tables; explains BGP adjacency and ASN behavior, DXGW allowed-prefix semantics, exact on-premises-to-VPC and return packet walks, multi-VPC and multi-Region designs, redundant-circuit failover, AWS CLI deployment, verification, troubleshooting, and common mistakes, with matching SVG/editable draw.io architecture and route-flow diagrams.\n\n'''
anchor = '## AWS Networking\n\n'
if entry not in s:
    if anchor not in s:
        raise SystemExit('AWS Networking heading not found')
    s = s.replace(anchor, anchor + entry, 1)
    p.write_text(s)
