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

### [Azure Virtual WAN Secured Hub with Azure Firewall or Integrated NVA — Method 4 Study Guide](09-05-26-15-56_Azure_Virtual_WAN_Secured_Hub_Method_4_Study_Guide.md)
Deep dive into Virtual WAN secured hubs for centralized firewall inspection. Covers Azure Firewall versus supported hub-integrated NVAs, Routing Intent and Private/Internet traffic policies, route association/propagation, spoke-to-spoke and branch-to-spoke packet walks, inter-hub inspection, Internet egress/DNAT, Private Endpoint caveats, HA/asymmetry, verification, troubleshooting, and configuration steps, with matching SVG and editable draw.io diagrams.

### [Azure Virtual WAN Multi-Region Hubs — Deep Dive Expansion for Method 4](09-05-26-16-05_Azure_Virtual_WAN_Multi_Region_Hubs_Deep_Dive.md)
Detailed multi-region expansion covering the global Virtual WAN versus regional vHub model, automatic full-mesh hub-to-hub transit over Microsoft's backbone, regional route learning and propagation, West-to-East packet walks with and without inter-hub inspection, the one-VNet-to-one-vHub constraint, regional branch and ExpressRoute designs, per-hub Routing Intent, regional firewall placement, route symmetry, address overlap, and cross-region troubleshooting, with matching SVG and editable draw.io topology.

### [Azure Route Server + Third-Party NVA for Dynamic Service Insertion — Comprehensive Study Guide](09-05-26-13-55_Azure_Route_Server_Third_Party_NVA_Dynamic_Service_Insertion_Study_Guide.md)
Deep dive into Azure Route Server as the BGP control plane for third-party firewall/SD-WAN NVA service insertion. Covers effective-route and UDR interaction, hub/spoke peering requirements, dynamic route injection, same-VNet limitations, East-West and internet inspection, and detailed ExpressRoute and VPN Gateway integration including exact gateway termination points, branch-to-branch route exchange, hybrid route preference, inspection-bypass caveats, active-active VPN requirements, stateful symmetry, verification, and troubleshooting, with matching SVG and editable draw.io diagrams.

### [Azure Firewall Inspection Methods — Comprehensive Architecture and Operations Study Guide](09-05-26-12-41_Azure_Firewall_Inspection_Methods_Comprehensive_Study_Guide.md)
Exhaustive Azure firewall-inspection architecture guide covering customer-managed hub/spoke with Azure Firewall or third-party NGFWs, Virtual WAN secured hubs and integrated NVAs, Routing Intent, Route Server/BGP, Standard Load Balancer HA Ports, Gateway Load Balancer chaining, forced tunneling, WAF layering, Private Endpoint inspection, double inspection, routing symmetry, NAT/DNS, HA/failover, verification, and troubleshooting, with matching SVG and editable draw.io diagrams.

### [Azure ExpressRoute Global Reach — Comprehensive Study Guide](09-04-26-18-22_Azure_ExpressRoute_Global_Reach_Study_Guide.md)
Deep dive into ExpressRoute Global Reach as a Layer 3 WAN-transit service between on-premises networks connected by separate ExpressRoute circuits. Covers BGP and private-peering behavior, `/29` IPv4 and `/125` IPv6 connection addressing, Premium requirements for cross-geopolitical connections, same- and cross-subscription configuration, route and connection limits, throughput, failover, route-policy interaction with MPLS/SD-WAN/VPN paths, firewall and asymmetric-routing considerations, verification, and troubleshooting.

## AWS Networking

### [AWS VPC Traffic Mirroring — Missing Inbound Packets and Source-Side Policy](09-05-26-11-22_AWS_VPC_Traffic_Mirroring_Missing_Inbound_Packets_Study_Guide.md)
Explains why an analyzer can miss inbound packets in AWS VPC Traffic Mirroring, including the documented behavior that traffic dropped at the mirror source by inbound Security Group or Network ACL rules is not mirrored. Covers source/filter/target architecture, VXLAN/UDP 4789 transport, TLS misconceptions, the important nuance when a workload claims it received the exact packet, AWS CLI configuration patterns, verification, bandwidth/PPS limitations, and symptom-based troubleshooting, with matching SVG and editable draw.io packet-flow diagrams.

### [AWS NLB Hairpinning, Client-IP Preservation, and Proxy Protocol v2](09-05-26-10-38_AWS_NLB_Hairpinning_Client_IP_Preservation_PPv2.md)
Explains why an internal Network Load Balancer target calling the same NLB can fail when client-IP preservation is enabled. Covers AWS NAT loopback/hairpinning behavior, self-target packet flow, why routing changes do not solve the issue, disabling `preserve_client_ip.enabled`, using Proxy Protocol v2 to retain client identity, protocol/default caveats, CLI configuration, verification, common mistakes, and symptom-based troubleshooting.

### [AWS Cloud WAN — Comprehensive Network Engineering Study Guide](09-05-26-09-57_AWS_Cloud_WAN_Comprehensive_Study_Guide.md)
Deep dive into AWS Cloud WAN as a policy-driven global Layer 3 WAN. Covers Global Networks, Core Networks, Core Network Edges, globally consistent segments, attachment policies, VPC/VPN/Connect/TGW/Direct Connect gateway attachments, native Direct Connect routing, service insertion and Network Function Groups, Routing Policy route filtering/summarization/BGP path control, packet flows, multi-account operation, CLI workflows, Route Analysis, CloudWatch monitoring, quotas, MTU, pricing, convergence, migration, common mistakes, and symptom-based troubleshooting.

### [AWS PrivateLink, VPC Endpoints, and GWLB Firewall Inspection](09-04-26-16-18_AWS_PrivateLink_GWLB_Firewall_Inspection_Study_Guide.md)
Deep dive into AWS PrivateLink and VPC endpoint types, including interface endpoints, endpoint services, resource/service-network endpoints, and the distinction between gateway endpoints and PrivateLink. Covers Gateway Load Balancer Endpoints (GWLBE), route-table-based traffic steering, GENEVE-based appliance insertion, centralized and distributed firewall inspection, packet flows, security controls, limitations, and troubleshooting.

### [AWS DNS for Network Experts — Route 53 VPC Resolver](09-04-26-15-43_AWS_DNS_Route53_Resolver_Network_Expert_Study_Guide.md)
Advanced AWS DNS guide covering AmazonProvidedDNS/VPC+2, Route 53 VPC Resolver, inbound and outbound Resolver endpoints, forwarding and delegation rules, private hosted zones, hybrid on-premises DNS, Route 53 Profiles, DNS Firewall, query logging, DNS over HTTPS, DNSSEC-related concepts, centralized multi-account DNS, high availability, troubleshooting, and Route 53 Global Resolver.

## BGP, MPLS, and Routing

### [BGP Optimal Route Reflection (ORR) — Comprehensive Study Guide](08-29-26-15-51_bgp_optimal_route_reflection_orr.md)
Explains RFC 9107 Optimal Route Reflection, why conventional route reflectors can cause suboptimal hot-potato routing, client-versus-RR IGP viewpoints, alternate IGP roots, client-specific route selection, Cisco IOS XR and Junos behavior, interaction with ADD-PATH, design considerations, verification, and troubleshooting.

### [BGP Clusters and Route Reflectors — Comprehensive Study Guide](08-29-26-15-14_bgp_clusters_study_guide.md)
Covers route-reflector clusters, RR clients and non-clients, cluster IDs, ORIGINATOR_ID, CLUSTER_LIST, loop prevention, redundant route reflectors, hierarchical reflection, path-selection implications, Cisco/Juniper/FRR configuration concepts, verification, and troubleshooting.

### [BGP Clusters: Route Reflectors, Cluster IDs, and Hierarchical Design — GitHub Edition](08-29-26-14-55_bgp_clusters_route_reflectors_github_fixed.md)
GitHub-rendering-corrected route-reflector guide covering RFC 4456 reflection rules, cluster IDs, ORIGINATOR_ID, CLUSTER_LIST, client/non-client behavior, loop prevention, redundant RR design, and operational verification with repository-hosted images.

### [BGP Clusters: Route Reflectors, Cluster IDs, and Hierarchical Design](08-29-26-14-49_bgp_clusters_route_reflectors_study_guide.md)
Detailed introduction to BGP route-reflector clusters, iBGP scaling, client/non-client advertisement rules, cluster IDs, ORIGINATOR_ID, CLUSTER_LIST, redundancy, hierarchy, Cisco IOS XE/IOS XR and Junos considerations, verification, and troubleshooting.

### [BGP Confederations — Comprehensive iBGP Scaling Study Guide](08-29-26-14-29-bgp-confederations-comprehensive-study-guide.md)
Explains BGP confederation architecture, member/sub-AS design, confederation eBGP versus iBGP, AS_CONFED_SEQUENCE behavior, external AS visibility, LOCAL_PREF/MED/NEXT_HOP handling, loop prevention, scaling tradeoffs, Cisco and Juniper implementation concepts, verification, and troubleshooting.

### [Pseudowires, VCCV, and BFD over VCCV — Junos Study Guide](08-29-26-14-41-pseudowire-vccv-bfd-junos-study-guide.md)
Covers MPLS pseudowires, Virtual Circuit Connectivity Verification (VCCV), BFD over VCCV, pseudowire OAM, control-channel and connectivity-verification types, control-word implications, LDP/BGP-signaled Layer 2 services, VPLS/L2VPN use cases, interoperability, data-plane validation, Junos configuration concepts, verification, and troubleshooting.

## GitHub, Git, and Network Automation

### [Network Automation Using GitHub](08-30-26-17-00_network_automation_using_github.md)
Practical GitOps/NetDevOps guide for using GitHub as the reviewed source of truth for network configuration. Covers pull-request workflows, GitHub Actions, private runners, secrets, validation pipelines, deployment approvals, Ansible/Nornir/Terraform/vendor APIs, Cisco IOS XE/IOS XR/NX-OS/Meraki/SD-WAN/Catalyst Center/NSO use cases, post-change validation, rollback, and production safety controls.

### [Git vs `gh`: Git Commands and GitHub CLI Study Guide](08-30-26-13-32_git-vs-gh-github-cli-study-guide.md)
Explains the difference between Git and GitHub CLI (`gh`), showing which tool manages local version-control history versus GitHub-specific services. Covers repositories, branches, commits, fetch/pull/push, pull requests, issues, Actions, releases, authentication, projects, and GitHub API operations.

### [Git Commands for the GitHub Foundations Exam](08-30-26-12-54_git_commands_github_foundations_exam.md)
Exam-focused Git command reference covering the working tree, staging area, commits, branches, remotes, clone/init, add/commit, fetch/pull/push, merge/rebase, switch/checkout, configuration, status/diff/log, undo and recovery operations, and the distinction between Git commands and GitHub features.

### [GitHub Projects vs Projects (classic)](08-30-26-10-00_github-projects-vs-projects-classic.md)
Compares the current GitHub Projects platform with retired Projects (classic). Covers items, custom fields, table/board/roadmap views, iterations, filtering/grouping, charts, workflows, templates, cross-repository planning, migration history, API direction, and why current Projects should be used for new work.

### [InnerSource Development Terminology Study Guide](08-30-26-09-59_innersource-development-terminology.md)
Introduces InnerSource as open-source-style collaboration inside a private organization. Covers host teams, guest teams, contributors, trusted committers, discoverability, contribution guidelines, governance, cross-team collaboration, repository practices, and how InnerSource differs from traditional closed-source and public open-source development.

### [GitHub Branch Protection and Rulesets Guide](08-30-26-09-41_github-branch-protection-guide.md)
Covers GitHub repository rulesets and classic branch protection, including required pull requests and approvals, status checks, conversation resolution, signed commits, linear history, force-push/deletion protection, bypass permissions, merge queues, deployment gates, rule layering, and recommended controls for GitOps/network-automation repositories.

## Hands-On Labs

### [FRR BGP ORR-Behavior / ADD-PATH Lab for GNS3 — Study Guide](08-30-26-01-49_BGP_ORR_FRR_GNS3_Lab.md)
Explains and documents a five-router FRRouting/GNS3 lab that demonstrates conventional route-reflector path hiding and uses BGP ADD-PATH to reproduce the client-appropriate path-selection outcome that ORR is designed to provide. Includes OSPF underlay costs, equal-attribute BGP paths, topology diagrams, prerequisites, expected behavior, validation, and automation details.

### [Runnable FRR BGP ORR-Behavior / ADD-PATH GNS3 Lab](labs/bgp-orr-frr-gns3-lab/README.md)
Hands-on lab instructions and assets for building the FRR/GNS3 topology. Covers Docker/FRR prerequisites, GNS3 API requirements, the RR/E1/E2/C1/C2 topology, OSPF metrics, standard route-reflection versus ADD-PATH scenarios, configuration behavior, validation, and the boundary between native ORR and the lab's ADD-PATH emulation.
