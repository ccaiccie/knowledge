from pathlib import Path

p = Path('09-07-26_Azure_Firewall_Insertion_Summary.md')
s = p.read_text()
anchor = "For exhaustive details, use the linked deep-dive guides in this repository.\n\n## Core mental model\n"

toc = """For exhaustive details, use the linked deep-dive guides in this repository.

## Table of contents

- [Purpose](#purpose)
- [Core mental model](#core-mental-model)
- [1. Azure Firewall in a customer-managed hub VNet](#1-azure-firewall-in-a-customer-managed-hub-vnet)
- [2. Third-party NVA in a customer-managed hub VNet](#2-third-party-nva-in-a-customer-managed-hub-vnet)
- [3. UDR versus Azure Route Server](#3-udr-versus-azure-route-server)
  - [UDR = explicit destination steering](#udr--explicit-destination-steering)
  - [Azure Route Server = dynamic BGP control plane](#azure-route-server--dynamic-bgp-control-plane)
- [4. Azure Route Server + third-party NVA](#4-azure-route-server--third-party-nva)
- [5. Same-VNet east-west inspection](#5-same-vnet-east-west-inspection)
- [6. Inter-VNet / hub-and-spoke inspection](#6-inter-vnet--hub-and-spoke-inspection)
- [7. Virtual WAN secured hub + Azure Firewall](#7-virtual-wan-secured-hub--azure-firewall)
- [8. Integrated third-party NVA directly in the Virtual WAN hub](#8-integrated-third-party-nva-directly-in-the-virtual-wan-hub)
- [9. Virtual WAN Security SaaS Provider](#9-virtual-wan-security-saas-provider)
- [10. Gateway Load Balancer: transparent NVA insertion](#10-gateway-load-balancer-transparent-nva-insertion)
- [11. Internet egress through a customer-managed firewall](#11-internet-egress-through-a-customer-managed-firewall)
  - [Azure Firewall](#azure-firewall)
  - [Third-party NVA](#third-party-nva)
- [12. Internet ingress](#12-internet-ingress)
  - [Azure Firewall DNAT](#azure-firewall-dnat)
  - [Integrated vWAN NVA DNAT](#integrated-vwan-nva-dnat)
  - [Gateway Load Balancer](#gateway-load-balancer)
  - [WAF](#waf)
- [13. Front Door WAF and Application Gateway WAF](#13-front-door-waf-and-application-gateway-waf)
- [14. Private Endpoint inspection](#14-private-endpoint-inspection)
- [15. ExpressRoute and VPN hybrid inspection](#15-expressroute-and-vpn-hybrid-inspection)
  - [Azure-side inspection](#azure-side-inspection)
  - [On-premises forced-tunnel inspection](#on-premises-forced-tunnel-inspection)
- [16. Forced tunneling to on-premises](#16-forced-tunneling-to-on-premises)
- [17. UDR recursion, bypass, and post-inspection routing](#17-udr-recursion-bypass-and-post-inspection-routing)
- [18. Stateful symmetry](#18-stateful-symmetry)
- [19. One-page cheat sheet](#19-one-page-cheat-sheet)
- [20. Decision tree](#20-decision-tree)
- [21. Quick method-selection table](#21-quick-method-selection-table)
- [22. Final mental model](#22-final-mental-model)
- [Detailed Azure guides in this repository](#detailed-azure-guides-in-this-repository)
- [Sources](#sources)

---

## Core mental model
"""

if '## Table of contents\n' in s:
    raise SystemExit('TOC already present')
if anchor not in s:
    raise SystemExit('anchor not found')
s = s.replace(anchor, toc, 1)
p.write_text(s)
