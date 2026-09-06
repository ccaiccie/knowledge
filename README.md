# Daily Knowledge Snippets

A browsable index of the technical study guides and labs in this repository. Each entry links directly to the Markdown article and summarizes the major concepts it covers.

## Network Security

### [DNSSEC (Domain Name System Security Extensions) — Comprehensive Network & Security Study Guide](09-05-26-12-14_DNSSEC_Comprehensive_Study_Guide.md)
Comprehensive guide to DNSSEC authenticity and integrity, the root-to-child chain of trust, DS/DNSKEY/RRSIG relationships, KSK and ZSK roles, NSEC/NSEC3 authenticated denial, Secure/Insecure/Bogus validation states, `dig` verification, EDNS/UDP/TCP/MTU considerations, key rollover and provider migration, Amazon Route 53 DNSSEC signing/validation behavior, and symptom-based troubleshooting, with matching SVG and editable draw.io diagrams.

### [MACsec (IEEE 802.1AE) — Comprehensive Network Engineering Study Guide](09-05-26-09-16_MACsec_IEEE8021AE_Study_Guide.md)
Deep dive into Layer 2 MACsec encryption and IEEE 802.1AE behavior. Covers MKA control-plane operation, CAK/CKN/SAK relationships, Secure Channels and Secure Associations, GCM-AES cipher suites, replay protection, WAN MACsec over carrier Ethernet, EAPOL transparency, MTU and Port-Channel considerations, Cisco IOS XE and Junos configuration patterns, packet flow, verification, failover, common mistakes, and symptom-based troubleshooting.

## GCP Networking

### [Google Cloud Policy-Based Routing (PBR) — Comprehensive Study Guide](09-05-26-08-12_GCP_Policy_Based_Routing_Study_Guide.md)
Deep dive into Google Cloud VPC Policy-Based Routing for source/destination/protocol-based traffic steering and service insertion. Covers routing order, internal passthrough Network Load Balancer next hops, stateful NVA/firewall symmetry, VM-tag and Cloud Interconnect scopes, `DEFAULT_ROUTING` bypass policies, Google APIs/GKE/Private Service Connect caveats, Console configuration, `gcloud` examples, Terraform resources and lab skeletons, official Google diagrams/screenshots, verification, and symptom-based troubleshooting.

## Azure Networking

### [Azure ExpressRoute — Comprehensive Routing, Multi-Circuit, Virtual WAN, and Route Server Study Guide](09-06-26-12-40_Azure_ExpressRoute_Comprehensive_Study_Guide.md)
Deep dive into ExpressRoute circuit anatomy, Azure private and Microsoft peering, connectivity models, Local/Standard/Premium SKUs, ExpressRoute Direct, Metro, Global Reach, BGP route engineering, multi-site/multi-circuit ECMP and active/standby failover using AS-path prepending and LOCAL_PREF, Virtual WAN ExpressRoute gateways and vHub route-table propagation, Azure Route Server/NVA integration, FastPath, packet flow, Azure CLI configuration, verification, troubleshooting, and four matching SVG/editable draw.io diagrams.

### [Azure Private Endpoint Inspection — Azure Firewall and ILB-Backed Third-Party NVA Deep Dive](09-06-26-12-37_Azure_Private_Endpoint_Inspection_Azure_Firewall_Deep_Dive.md)
Detailed Private Endpoint inspection guide covering both Azure Firewall and Standard Internal Load Balancer + HA Ports + third-party NVA designs. Includes PE network-policy requirements, route-precedence behavior, UDR-to-ILB frontend service insertion, NVA IP forwarding, SNAT/state symmetry, exact forward/return packet walks, HA and health-probe behavior, backend-to-own-frontend hairpin caveats, Azure CLI deployment/verification commands, failover analysis, and matching SVG/editable draw.io diagrams.

### [Azure Front Door WAF and Application Gateway WAF — Method 9 Deep Dive](09-06-26-10-24_Azure_Front_Door_Application_Gateway_WAF_Method_9_Deep_Dive.md)
Deep dive into Layer-7 HTTP/HTTPS firewall inspection with Azure Front Door WAF and Application Gateway WAF v2. Covers global-edge versus regional reverse-proxy architecture, Front Door origin lockdown with Private Link or `AzureFrontDoor.Backend` plus `X-Azure-FDID`, managed/custom rules and anomaly scoring, rate limiting, three-leg TLS and client-IP behavior, Front Door-to-Application-Gateway layering, Azure CLI deployment, backend routing, Azure Firewall coexistence, HA/failover, verification, and symptom-based troubleshooting, with matching SVG and editable draw.io diagrams.

### [Azure Forced Tunneling — Inspect Internet Traffic On-Premises](09-05-26-20-53_Azure_Forced_Tunneling_On_Premises_Internet_Inspection_Deep_Dive.md)
Deep dive into forcing Azure Internet-bound traffic to on-premises inspection using VPN Gateway BGP defaults, VPN Gateway Default Site, and ExpressRoute private peering. Covers exact packet and return paths, on-premises SNAT, stateful symmetry, route selection and BGP/UDR precedence, hub-spoke gateway transit, fail-open behavior when learned defaults disappear, optional Azure-Firewall-to-on-premises double inspection, effective-route/Network-Watcher verification, MTU considerations, failover, common mistakes, and symptom-based troubleshooting, with matching SVG and editable draw.io diagrams.

### [Integrated Third-Party NGFW Directly Inside an Azure Virtual WAN Hub — Deep Dive](09-05-26-20-00_Azure_Virtual_WAN_Integrated_Third_Party_NGFW_Direct_Hub_Deep_Dive.md)
Focused deep dive into Microsoft/vendor-qualified Integrated NVAs deployed directly inside a Standard Azure Virtual WAN hub. Covers current Check Point, Fortinet, and Cisco NGFW eligibility, the Palo Alto SaaS distinction, Routing Intent for private and Internet traffic, NVA Infrastructure Units, managed VMSS/load-balancer/health behavior, east-west/branch/Internet packet flows, Internet-inbound DNAT and SNAT symmetry limits, Azure health probes, MANA migration considerations, Azure CLI verification, vendor-specific notes, common mistakes, and symptom-based troubleshooting, with redesigned color-coded architecture/control-plane diagrams and independent forward/return SVG + editable draw.io packet-flow pairs for east-west, branch/ExpressRoute, Internet egress, and Internet-inbound DNAT.

### [Third-Party NGFW/NVA in a Customer-Managed Hub VNet — Method 2 Deep Dive](09-05-26-19-45_Third_Party_NGFW_NVA_Customer_Managed_Hub_VNet_Method_2_Deep_Dive.md)
Deep dive into customer-managed hub/spoke inspection with third-party VM-based firewalls and NVAs. Covers single-appliance versus HA-Ports next-hop models, UDRs, VNet peering and forwarded-traffic settings, Azure NIC IP forwarding, stateful symmetry, east-west inspection, Internet egress and vendor-specific SNAT, hybrid VPN/ExpressRoute reverse-path routing, Internal Standard Load Balancer HA Ports, effective-route and Network Watcher verification, expected CLI results, failover, common mistakes, and symptom-based troubleshooting, with three focused matching SVG and editable draw.io diagrams.

### [Azure Gateway Load Balancer for Transparent NVA Insertion — Comprehensive Study Guide](09-05-26-17-03_Gateway_Load_Balancer_Transparent_NVA_Insertion_Study_Guide.md)
Deep dive into Azure Gateway Load Balancer as a transparent bump-in-the-wire service for third-party NVAs. Covers the exact `gatewayLoadBalancer` frontend resource reference that creates the service chain, Standard Public Load Balancer and VM public-IP chaining, inbound and outbound packet walks, outbound-rule frontend selection, NAT Gateway precedence/bypass behavior, VXLAN internal/external tunnel interfaces, HA Ports, flow symmetry and stateful-firewall stickiness, provider/consumer separation across subscriptions or tenants, MTU requirements, portal and Azure CLI deployment, limitations, verification, failover behavior, common mistakes, and troubleshooting, with matching SVG and editable draw.io diagrams.

### [Azure Virtual WAN Security SaaS Provider — Method 6 Deep Dive](09-05-26-16-44_Azure_Virtual_WAN_Security_SaaS_Provider_Method_6_Deep_Dive.md)
Deep dive into Azure Firewall Manager Security Partner Provider service insertion for VNet-to-Internet and Branch-to-Internet inspection. Covers the external SECaaS architecture, required vHub S2S VPN Gateway/IPsec service tunnel, secured `0.0.0.0/0` route programming and connection opt-in, VNet and branch packet walks, Microsoft 365 local-breakout guidance, the supported split of SECaaS for Internet and Azure Firewall for private traffic, current Zscaler-specific integration caveats, provider-list documentation conflicts, verification, HA/failure behavior, and symptom-based troubleshooting, with matching SVG and editable draw.io diagrams.

### [Azure Virtual WAN Secured Hub with Azure Firewall or Integrated NVA — Method 4 Study Guide](09-05-26-15-56_Azure_Virtual_WAN_Secured_Hub_Method_4_Study_Guide.md)
Deep dive into Virtual WAN secured hubs for centralized inspection. Covers Azure Firewall versus supported hub-integrated NVAs, Routing Intent and Private/Internet traffic policies, route association/propagation, spoke-to-spoke and branch-to-spoke packet walks, inter-hub inspection, Internet egress/DNAT, Private Endpoint caveats, HA/asymmetry, verification, troubleshooting, and configuration steps, with matching SVG and editable draw.io diagrams.

### [Azure Virtual WAN Multi-Region Hubs — Deep Dive Expansion for Method 4](09-05-26-16-05_Azure_Virtual_WAN_Multi_Region_Hubs_Deep_Dive.md)
Detailed multi-region expansion covering the global Virtual WAN versus regional vHub model, automatic full-mesh hub-to-hub transit over Microsoft's backbone, regional route learning and propagation, West-to-East packet walks with and without inter-hub inspection, the one-VNet-to-one-vHub constraint, regional branch and ExpressRoute designs, per-hub Routing Intent, regional firewall placement, route symmetry, address overlap, and cross-region troubleshooting, with matching SVG and editable draw.io topology.

### [Azure Route Server + Third-Party NVA for Dynamic Service Insertion — Comprehensive Study Guide](09-05-26-13-55_Azure_Route_Server_Third_Party_NVA_Dynamic_Service_Insertion_Study_Guide.md)
Deep dive into Azure Route Server as the BGP control plane for third-party firewall/SD-WAN NVA service insertion. Covers effective-route and UDR interaction, hub/spoke peering requirements, dynamic route injection, same-VNet limitations, East-West and internet inspection, and detailed ExpressRoute and VPN Gateway integration including exact gateway termination points, branch-to-branch route exchange, hybrid route preference, inspection-bypass caveats, active-active VPN requirements, stateful symmetry, verification, and troubleshooting, with matching SVG and editable draw.io diagrams.

### [Azure Firewall Inspection Methods — Comprehensive Architecture and Operations Study Guide](09-05-26-12-41_Azure_Firewall_Inspection_Methods_Comprehensive_Study_Guide.md)
Exhaustive Azure firewall-inspection architecture guide covering customer-managed hub/spoke with Azure Firewall or third-party NGFWs, Virtual WAN secured hubs and integrated NVAs, Routing Intent, Route Server/BGP, Standard Load Balancer HA Ports, Gateway Load Balancer chaining, forced tunneling, WAF layering, Private Endpoint inspection, double inspection, routing symmetry, NAT/DNS, HA/failover, verification, and troubleshooting, with matching SVG and editable draw.io diagrams.

### [Azure Firewall in a Customer-Managed Hub VNet — Method 1 Deep Dive](09-05-26-18-55_Azure_Firewall_Customer_Managed_Hub_VNet_Method_1_Deep_Dive.md)
Complete Method 1 expansion covering customer-owned hub/spoke architecture, exact UDR and route-selection behavior, VNet peering and gateway-transit settings, symmetric spoke-to-spoke and hybrid routing, GatewaySubnet inspection routes, Internet egress and SNAT, NAT Gateway integration, inbound DNAT, firewall rule-processing order, Premium TLS/IDPS considerations, forced tunneling, DNS and Private Endpoint caveats, Azure CLI examples, verification workflows, common mistakes, and symptom-based troubleshooting, with four matching SVG and editable draw.io diagrams.

### [Azure ExpressRoute Global Reach — Comprehensive Study Guide](09-04-26-18-22_Azure_ExpressRoute_Global_Reach_Study_Guide.md)
Deep dive into ExpressRoute Global Reach as a Layer 3 WAN-transit service between on-premises networks connected by separate ExpressRoute circuits. Covers BGP and private-peering behavior, `/29` IPv4 and `/125` IPv6 connection addressing, Premium requirements for cross-geopolitical connections, same- and cross-subscription configuration, route and connection limits, throughput, failover, route-policy interaction with MPLS/SD-WAN/VPN paths, firewall and asymmetric-routing considerations, verification, and troubleshooting.

## AWS Networking

### [AWS ALB/NLB + Inline Firewall Endpoint — GWLB/GWLBE Deep Dive](09-06-26-16-42_AWS_ALB_NLB_Inline_Firewall_Endpoint_GWLBE_Deep_Dive.md)
Deep dive into pre-load-balancer and post-load-balancer firewall insertion with ALB/NLB, Gateway Load Balancer, and GWLBE. Covers IGW gateway-route-table steering, VPC more-specific subnet routes, exact ALB backend packet flow, NLB IP-target requirements, client-IP preservation limitations, GENEVE/UDP 6081, per-AZ route symmetry, provider/consumer deployment CLI, TLS placement, verification, common mistakes, and troubleshooting, with three matching SVG/editable draw.io diagrams.

### [Legacy AWS Transit Gateway + Direct NVA VPC Attachment — Deep Dive](09-06-26-16-41_Legacy_TGW_NVA_VPC_Attachment_Deep_Dive.md)
Deep dive into the pre-GWLB direct-appliance service-insertion pattern: PRE/POST Transit Gateway route tables, Inspection-VPC TGW attachment subnet routing directly to firewall ENIs, Appliance Mode and stateful symmetry, active/active and active/standby HA, source/destination check, east-west packet walks, Direct Connect transit-VIF/DXGW and Site-to-Site VPN enforcement, Internet egress variants, AWS CLI build/verification commands, bypass analysis, troubleshooting, and matching editable draw.io/SVG diagrams.

### [Caveats for Centralized Ingress Routing — ALB, NLB, GWLB/GWLBE, TGW, and Distributed Alternatives](09-06-26-16-23_Caveats_for_Centralized_Ingress_Routing.md)
Explains the symmetry caveats in centralized Internet ingress, including the Experian ALB case-study return-route matrix, why ALB proxying makes the original GWLBE recoverable from the destination ALB subnet, why NLB client-IP preservation is unsupported through TGW or between NLB and target through GWLBE, and why distributed/spoke ingress removes the centralized TGW return-AZ recovery problem while retaining its own placement constraints. Includes AWS case-study/documentation references and matching SVG/editable draw.io diagrams.

### [AWS Transit Gateway + Centralized GWLB/GWLBE Inspection VPC — Deep Dive](09-06-26-15-45_TGW_Centralized_GWLB_GWLBE_Inspection_VPC_Deep_Dive.md)
Detailed centralized third-party NGFW architecture using TGW, a dedicated Inspection VPC, zonal GWLBE, GWLB, and Appliance Mode. Covers pre-inspection versus post-inspection TGW route tables, exact Inspection-VPC subnet routes, east-west packet flow, centralized Internet egress and NAT return enforcement, Direct Connect Transit VIF/DXGW and Site-to-Site VPN inspection, stateful symmetry, HA/AZ behavior, AWS CLI configuration and verification, bypass risks, troubleshooting, and matching editable draw.io/SVG diagrams.

### [Distributed GWLBE with a Centralized Third-Party Firewall Fleet — Deep Dive](09-06-26-15-23_Distributed_GWLBE_Centralized_Third_Party_Firewall_Fleet_Deep_Dive.md)
Fine-grained distributed Gateway Load Balancer Endpoint architecture with a centralized third-party NGFW fleet. Covers exact per-subnet route-table enforcement for east-west VPC traffic, Internet north-south ingress, south-north egress through NAT Gateway, Direct Connect Transit VIF → Direct Connect Gateway → Transit Gateway routing, Site-to-Site VPN primary/backup behavior, TGW route priority, BGP, double-inspection choices, original-tuple/GENEVE packet flow, AWS CLI deployment and verification, failover, common mistakes, and symptom-based troubleshooting, with three detailed matching SVG/editable draw.io diagrams.

### [AWS Firewall Inspection and Service Insertion — Comprehensive Study Guide](09-06-26-15-03_AWS_Firewall_Inspection_Insertion_Comprehensive_Study_Guide.md)
Comprehensive AWS firewall-insertion guide covering AWS Network Firewall, third-party NGFW/NVAs behind Gateway Load Balancer, distributed GWLBE, centralized Transit Gateway inspection VPCs, Direct Connect transit-VIF/DXGW/TGW inspection, Internet ingress and egress, ALB/NLB placement, ELB sandwich and direct-NVA legacy designs, Cloud WAN Network Function Group service insertion, VPC Route Server/BGP active-standby patterns, NAT/source-IP behavior, appliance mode and symmetry, AWS CLI verification, failover, MTU, common mistakes, and symptom-based troubleshooting, with matching SVG and editable draw.io diagrams.

### [AWS VPC Traffic Mirroring — Missing Inbound Packets and Source-Side Policy](09-05-26-11-22_AWS_VPC_Traffic_Mirroring_Missing_Inbound_Packets_Study_Guide.md)
Explains why an analyzer can miss inbound packets in AWS VPC Traffic Mirroring, including the documented behavior that traffic dropped at the mirror source by inbound Security Group or Network ACL rules is not mirrored. Covers source/filter/target architecture, VXLAN/UDP 4789 transport, TLS misconceptions, the important nuance when a workload claims it received the exact packet, AWS CLI configuration patterns, verification, bandwidth/PPS limitations, and symptom-based troubleshooting, with matching SVG and editable draw.io packet-flow diagrams.

### [AWS NLB Hairpinning, Client-IP Preservation, and Proxy Protocol v2](09-05-26-10-38_AWS_NLB_Hairpinning_Client_IP_Preservation_PPv2.md)
Explains why an internal Network Load Balancer target calling the same NLB can fail when client-IP preservation is enabled. Covers AWS NAT loopback/hairpinning behavior, self-target packet flow, why routing changes do not solve the issue, disabling `preserve_client_ip.enabled`, using Proxy Protocol v2 to retain client identity, protocol/default caveats, CLI configuration, verification, common mistakes, and troubleshooting.

### [AWS Cloud WAN — Comprehensive Network Engineering Study Guide](09-05-26-09-57_AWS_Cloud_WAN_Comprehensive_Study_Guide.md)
Deep dive into AWS Cloud WAN as a policy-driven global Layer 3 WAN. Covers Global Networks, Core Networks, Core Network Edges, globally consistent segments, attachment policies, VPC/VPN/Connect/TGW/Direct Connect gateway attachments, native Direct Connect routing, service insertion and Network Function Groups, Routing Policy route filtering/summarization/BGP path control, packet flows, multi-account operation, CLI workflows, Route Analysis, CloudWatch monitoring, quotas, MTU, pricing, convergence, migration, common mistakes, and troubleshooting.

### [AWS PrivateLink, VPC Endpoints, and GWLB Firewall Inspection](09-04-26-16-18_AWS_PrivateLink_GWLB_Firewall_Inspection_Study_Guide.md)
Deep dive into AWS PrivateLink and VPC endpoint types, including interface endpoints, endpoint services, resource/service-network endpoints, and the distinction between gateway endpoints and PrivateLink. Covers Gateway Load Balancer Endpoints (GWLBE), route-table-based traffic steering, GENEVE-based appliance insertion, centralized and distributed firewall inspection, packet flows, security controls, limitations, and troubleshooting.

### [AWS DNS for Network Experts — Route 53 VPC Resolver](09-04-26-15-43_AWS_DNS_Route53_Resolver_Study_Guide.md)
Advanced AWS DNS guide covering AmazonProvidedDNS/VPC+2, Route 53 VPC Resolver, inbound and outbound Resolver endpoints, forwarding and delegation rules, private hosted zones, hybrid on-premises DNS, Route 53 Profiles, DNS Firewall, query logging, DNS over HTTPS, DNSSEC-related concepts, centralized multi-account DNS, high availability, troubleshooting, and Route 53 Global Resolver.

## BGP, MPLS, and Routing

### [BGP Optimal Route Reflection (ORR) — Comprehensive Study Guide](08-29-26-15-51_bgp_optimal_route_reflection_orr.md)
Explains RFC 9107 Optimal Route Reflection, why conventional route reflectors can cause suboptimal hot-potato routing, client-versus-RR IGP viewpoints, alternate IGP roots, Cisco IOS XR and Junos behavior, interaction with ADD-PATH, design considerations, verification, and troubleshooting.

### [BGP Clusters and Route Reflectors — Comprehensive Study Guide](08-29-26-15-14_bgp_clusters_study_guide.md)
Covers route-reflector clusters, RR clients and non-clients, cluster IDs, ORIGINATOR_ID, CLUSTER_LIST, loop prevention, path-selection implications, Cisco/Juniper/FRR configuration concepts, verification, and troubleshooting.

## GitHub, Git, and Network Automation

### [Network Automation Using GitHub](08-30-26-17-00_network_automation_using_github.md)
Practical GitOps/NetDevOps guide for using GitHub as the reviewed source of truth for network configuration. Covers pull-request workflows, GitHub Actions, private runners, secrets, validation pipelines, deployment approvals, Ansible/Nornir/Terraform/vendor APIs, Cisco IOS XE/IOS XR/NX-OS/Meraki/SD-WAN/Catalyst Center/NSO use cases, post-change validation, rollback, and production safety controls.

## Hands-On Labs

### [Runnable FRR BGP ORR-Behavior / ADD-PATH GNS3 Lab](labs/bgp-orr-frr-gns3-lab/README.md)
Hands-on lab instructions and assets for building the FRR/GNS3 topology. Covers Docker/FRR prerequisites, GNS3 API requirements, the RR/E1/E2/C1/C2 topology, OSPF metrics, standard route-reflection versus ADD-PATH scenarios, configuration behavior, validation, and automation details.
