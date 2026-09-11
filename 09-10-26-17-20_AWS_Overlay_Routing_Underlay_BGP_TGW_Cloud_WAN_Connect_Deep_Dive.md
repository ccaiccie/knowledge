# AWS Overlay Routing — Underlay, BGP, Transit Gateway Connect, Cloud WAN Connect, SD-WAN, ECMP, and Failure Domains

## Purpose

This guide explains **overlay routing in AWS as a routing architecture**, independently of firewall insertion.

> **The underlay provides endpoint reachability. The overlay provides logical routing between networks using tunnels and/or BGP.**

The clearest customer-visible AWS overlay-routing constructs are:

- **AWS Transit Gateway Connect** — GRE data plane plus BGP control plane.
- **AWS Cloud WAN Connect (GRE)** — GRE plus BGP toward a Cloud WAN core network edge.
- **AWS Cloud WAN Tunnel-less Connect** — native BGP without GRE.
- **Third-party SD-WAN overlays** that use VPC, Internet, VPN, MPLS, or Direct Connect as transport.

Firewall/service insertion is one **application** of overlay routing; it is not what defines overlay routing.

Companion guide: [AWS Overlay Networking with Transit Gateway Connect and Cloud WAN Connect — Service Insertion Deep Dive](09-10-26-17-10_AWS_Overlay_Networking_TGW_Cloud_WAN_Connect_Service_Insertion_Deep_Dive.md)

## Table of contents

1. [Overlay routing mental model](#1-overlay-routing-mental-model)
2. [Underlay versus overlay](#2-underlay-versus-overlay)
3. [Control plane versus data plane](#3-control-plane-versus-data-plane)
4. [Transit Gateway Connect architecture](#4-transit-gateway-connect-architecture)
5. [Connect peer addressing](#5-connect-peer-addressing)
6. [What AWS advertises to the appliance](#6-what-aws-advertises-to-the-appliance)
7. [What the appliance advertises to AWS](#7-what-the-appliance-advertises-to-aws)
8. [TGW association versus propagation](#8-tgw-association-versus-propagation)
9. [Route selection and preference](#9-route-selection-and-preference)
10. [ECMP](#10-ecmp)
11. [Direct Connect as underlay](#11-direct-connect-as-underlay)
12. [VPN versus Connect](#12-vpn-versus-connect)
13. [Cloud WAN Connect](#13-cloud-wan-connect)
14. [Tunnel-less Connect](#14-tunnel-less-connect)
15. [SD-WAN overlay routing](#15-sd-wan-overlay-routing)
16. [Route recursion](#16-route-recursion)
17. [MTU](#17-mtu)
18. [Failure domains and convergence](#18-failure-domains-and-convergence)
19. [Leaks, loops, blackholes, and bypass](#19-leaks-loops-blackholes-and-bypass)
20. [Overlay routing versus service insertion](#20-overlay-routing-versus-service-insertion)
21. [Verification](#21-verification)
22. [AWS CLI](#22-aws-cli)
23. [Exam takeaways](#23-exam-takeaways)
24. [References](#24-references)

---

## 1. Overlay routing mental model

Traditional data-center networking often teaches:

~~~text
IP underlay
   |
VXLAN
   |
EVPN
   |
tenant overlay routes
~~~

A Transit Gateway Connect design is conceptually:

~~~text
VPC / Direct Connect underlay
         |
        GRE
         |
        BGP
         |
TGW Connect <-> SD-WAN/NVA logical routes
~~~

Cloud WAN Tunnel-less Connect removes GRE:

~~~text
VPC underlay
    |
native BGP
    |
Cloud WAN Connect
~~~

The customer-visible routing relationship is logical even though AWS hides the physical fabric underneath VPC, TGW, and Cloud WAN.

---

## 2. Underlay versus overlay

![AWS overlay routing control and data plane](images/09-10-26-17-20_aws_overlay_routing_control_data_plane.svg)

[Editable draw.io source](images/09-10-26-17-20_aws_overlay_routing_control_data_plane.drawio)

### Underlay

The underlay answers:

> Can the routing/tunnel endpoints reach one another?

Examples:

- VPC route-table reachability;
- AWS backbone connectivity;
- Direct Connect;
- Internet transport;
- Cloud WAN transport VPC attachment.

### Overlay

The overlay answers:

> Which prefixes are reachable through which logical peer?

Example:

~~~text
UNDERLAY

NVA outer IP 10.0.1.10
      |
      | VPC/TGW transport reachability
      v
TGW GRE outer IP 10.255.0.1


OVERLAY

169.254.100.x <---- BGP ----> 169.254.100.x

Learned/advertised routes:
10.10.0.0/16
10.20.0.0/16
172.16.0.0/12
~~~

The overlay can fail while the underlay remains healthy.

---

## 3. Control plane versus data plane

For Transit Gateway Connect:

~~~text
CONTROL PLANE = BGP
DATA PLANE    = GRE
UNDERLAY      = VPC or Direct Connect transport attachment
~~~

BGP exchanges reachability. GRE carries the customer packet.

This creates separate troubleshooting layers:

1. Underlay reachability.
2. GRE operation.
3. BGP state.
4. AWS route installation.
5. TGW route-table selection.
6. Actual data-plane forwarding.

A BGP session being Established does not prove that the customer packet is flowing.

---

## 4. Transit Gateway Connect architecture

~~~text
                       Transit Gateway
                  +----------------------+
Spoke VPC ------->| TGW route table      |
                  |                      |
                  | Connect attachment   |
                  +----------+-----------+
                             |
                            GRE
                             |
                         BGP x 2
                             |
                  +----------v-----------+
                  | SD-WAN / NVA         |
                  +----------+-----------+
                             |
                       transport path
                             |
                   VPC or Direct Connect
~~~

The hierarchy is:

~~~text
TGW
 |
 +-- Transport attachment
 |      +-- VPC or Direct Connect
 |
 +-- Connect attachment
        +-- Connect peer
              +-- one GRE tunnel
              +-- two BGP sessions
~~~

The two BGP sessions provide routing-plane redundancy for the Connect peer.

---

## 5. Connect peer addressing

A TGW Connect peer contains different address roles.

### GRE outer addresses

Appliance side:

~~~text
10.0.1.10
~~~

TGW side, taken from a TGW CIDR block:

~~~text
10.255.0.1
~~~

### BGP inside addresses

For IPv4, AWS requires a /29 from 169.254.0.0/16, excluding reserved ranges.

Conceptually:

~~~text
OUTER
10.0.1.10 <======== GRE ========> 10.255.0.1

INNER CONTROL PLANE
169.254.100.x <====== BGP ======> 169.254.100.x
~~~

These inside addresses are control-plane addresses, not workload prefixes.

---

## 6. What AWS advertises to the appliance

A subtle but important TGW rule:

> **Routes in the TGW route table associated with the Connect attachment are advertised to the third-party appliance through BGP.**

Example:

~~~text
TGW-RT-CONNECT

10.10.0.0/16 -> Spoke-A
10.20.0.0/16 -> Spoke-B
172.16.0.0/12 -> DXGW

             |
             | BGP advertisements
             v

SD-WAN appliance learns:
10.10.0.0/16
10.20.0.0/16
172.16.0.0/12
~~~

This means the associated TGW route table is both:

- a forwarding context for traffic entering from Connect; and
- a source of routes AWS advertises toward the Connect appliance.

---

## 7. What the appliance advertises to AWS

The appliance can advertise remote prefixes such as:

~~~text
192.168.10.0/24  Branch 1
192.168.20.0/24  Branch 2
172.20.0.0/16    Data center
0.0.0.0/0        Optional default
~~~

TGW learns them through BGP and the Connect attachment.

AWS documents Connect routes as dynamically propagated; static routes are not supported on the Connect attachment.

Example:

~~~text
NVA advertises 192.168.10.0/24
        |
        v
TGW Connect
        |
        | propagation enabled/default behavior
        v
TGW-RT-SPOKES

192.168.10.0/24 -> Connect attachment
~~~

---

## 8. TGW association versus propagation

### Association

An attachment is associated with one TGW route table.

That route table is consulted when a packet **enters TGW from that attachment**.

~~~text
Spoke-A packet
   |
   v
Spoke-A attachment
   |
   v
Spoke-A associated TGW RT
   |
   v
selected next attachment
~~~

### Propagation

An attachment can propagate its learned routes into TGW route tables.

~~~text
Connect learns branch routes
      |
      +--> TGW-RT-PROD
      +--> TGW-RT-SHARED
      +--> TGW-RT-BRANCH
~~~

This lets you control which routing domains can use the overlay.

A route learned by Connect does not need to be visible in every TGW route table.

---

## 9. Route selection and preference

Route selection starts with **longest-prefix match**.

Example:

~~~text
192.168.0.0/16  -> Connect
192.168.10.0/24 -> VPN
~~~

Traffic to 192.168.10.25 follows the /24 VPN route.

### Static versus propagated

For the same destination prefix, AWS TGW prefers a static route over a propagated route.

~~~text
10.20.0.0/16 -> Connect       propagated
10.20.0.0/16 -> Inspection    static
~~~

The static route wins.

This is useful for deterministic routing, but it also means a perfectly healthy BGP route can be hidden by a static route.

### Do not assume router-only BGP logic

AWS transit constructs have route-type and attachment-type preference behavior in addition to BGP attributes.

Troubleshoot in this order:

1. longest prefix;
2. static versus propagated;
3. attachment-type priority;
4. BGP attributes;
5. ECMP eligibility.

---

## 10. ECMP

TGW Connect can use ECMP between eligible:

- Connect peers on the same Connect attachment;
- Connect peers across Connect attachments on the same TGW.

AWS requires compatible/matching route attributes such as AS-PATH and ASN characteristics for all paths to participate.

### Important distinction

~~~text
Connect Peer A
   |
   +-- BGP session 1
   +-- BGP session 2
~~~

This is **one GRE peer/data path with two redundant BGP sessions**.

It is not two data-plane ECMP paths.

For ECMP data paths you need multiple Connect peers:

~~~text
Connect Peer A -> GRE path A
Connect Peer B -> GRE path B
~~~

---

## 11. Direct Connect as underlay

Direct Connect can carry the transport while Connect supplies the overlay.

~~~text
Remote site / SD-WAN
        |
Direct Connect
        |
DXGW / TGW transport
        |
TGW Connect
        |
GRE + BGP
        |
SD-WAN / NVA
~~~

Think:

~~~text
Direct Connect = underlay transport
GRE            = overlay encapsulation
BGP            = overlay routing control plane
~~~

The Direct Connect circuit can remain healthy while overlay routes move between Connect peers.

That is one of the biggest advantages of separating the underlay from the logical routing plane.

---

## 12. VPN versus Connect

| Property | Site-to-Site VPN | TGW Connect |
|---|---|---|
| Encapsulation | IPsec | GRE |
| Encryption | Yes | No |
| BGP | Supported | Required |
| Primary purpose | Secure hybrid connectivity | SD-WAN/NVA connectivity |
| Typical peer | Customer gateway | Third-party appliance |

GRE is not encryption.

A vendor SD-WAN system can separately encrypt traffic even when TGW Connect itself uses GRE.

---

## 13. Cloud WAN Connect

Cloud WAN Connect uses an existing **VPC attachment as the transport attachment**.

GRE mode:

~~~text
Third-party appliance
       |
      GRE
       |
     BGP x 2
       |
Cloud WAN Core Network Edge
       |
Cloud WAN segments
~~~

Cloud WAN adds global segmentation and core-network policy, so route behavior is not identical to TGW route-table association/propagation.

---

## 14. Tunnel-less Connect

Cloud WAN Tunnel-less Connect removes GRE and uses native BGP.

~~~text
Third-party appliance
       |
    native BGP
       |
Cloud WAN Core Network Edge
~~~

What disappears:

- GRE tunnel configuration;
- GRE overhead;
- GRE-specific MTU reduction.

What remains:

- BGP;
- VPC transport reachability;
- VPC routes to the core-network-edge BGP address;
- Cloud WAN segment/policy design.

AWS recommends placing the third-party appliance in the same subnet as the transport VPC attachment where practical. Tunnel-less Connect also supports MP-BGP for IPv4 and IPv6.

---

## 15. SD-WAN overlay routing

A vendor SD-WAN may already have its own overlay above several transports:

~~~text
                    SD-WAN overlay
                   /             \
              Branch A          Branch B
              /  |  \           /  |  \
        Internet MPLS 5G   Internet MPLS 5G
~~~

AWS may then be one hub/site in that SD-WAN fabric:

~~~text
Branches
   |
vendor SD-WAN overlay
   |
AWS SD-WAN appliance
   |
TGW Connect
   |
AWS VPCs
~~~

This can create nested encapsulation:

~~~text
application packet
   |
SD-WAN/IPsec encapsulation
   |
provider transport
   |
GRE Connect encapsulation
   |
AWS transit routing
~~~

That is why MTU analysis must be end-to-end.

---

## 16. Route recursion

Overlay routes eventually depend on underlay reachability.

Conceptually:

~~~text
Overlay:
10.40.0.0/16 -> BGP peer

BGP peer:
169.254.100.x -> GRE interface

GRE destination:
10.255.0.1

Underlay:
10.255.0.1 -> TGW transport path
~~~

If the GRE outer endpoint loses underlay reachability, the logical overlay is no longer usable.

Tunnel-less Connect removes the GRE recursion layer but still depends on VPC reachability to the BGP peer.

---

## 17. MTU

TGW Connect GRE adds at least:

~~~text
20 bytes IPv4 outer header
 4 bytes GRE header
--------------------------
24 bytes
~~~

AWS gives the standard example:

~~~text
external MTU = 1500
GRE MTU      = 1476
~~~

Nested SD-WAN or IPsec encapsulation can reduce the practical payload further.

Common symptoms:

- large packets fail while small ones work;
- TCP handshake succeeds but data transfer stalls;
- retransmissions increase;
- PMTUD fails.

---

## 18. Failure domains and convergence

![AWS overlay routing failure and route selection](images/09-10-26-17-20_aws_overlay_route_selection_failover.svg)

[Editable draw.io source](images/09-10-26-17-20_aws_overlay_route_selection_failover.drawio)

Treat these as separate failure domains.

### Underlay

- Direct Connect circuit;
- VPC attachment;
- ENI/instance;
- Internet/private transport.

### Tunnel

- GRE outer reachability;
- wrong GRE addresses;
- encapsulation;
- MTU.

### BGP

- neighbor loss;
- ASN mismatch;
- route filtering;
- route withdrawal.

### AWS routing

- wrong TGW route-table association;
- propagation missing;
- static route wins;
- more-specific route wins.

### SD-WAN/application policy

- vendor path selection;
- application steering;
- security policy.

A typical convergence chain is:

~~~text
underlay failure
  ->
GRE loss
  ->
BGP withdrawal
  ->
TGW removes route
  ->
alternate route/peer wins
  ->
traffic moves
~~~

Total convergence is the sum of these stages, not simply the BGP timer.

---

## 19. Leaks, loops, blackholes, and bypass

### Route leak

An appliance unintentionally advertises 0.0.0.0/0 into a widely propagated TGW routing domain.

Result: many VPCs may suddenly prefer the appliance.

### Blackhole

BGP remains up and advertises 10.50.0.0/16, but the appliance has no valid forwarding path beyond itself.

### Loop

~~~text
TGW -> Connect -> NVA -> TGW -> Connect -> NVA
~~~

This occurs when the post-NVA lookup resolves the same destination back through the overlay.

### Bypass

~~~text
10.50.0.0/16 -> Connect
10.50.20.0/24 -> direct VPC
~~~

Traffic for the /24 bypasses Connect due to longest-prefix match.

---

## 20. Overlay routing versus service insertion

Pure routing use case:

~~~text
AWS VPC
  |
 TGW
  |
Connect
  |
SD-WAN router
  |
Branch
~~~

The appliance is simply a router.

Security/service-insertion use case:

~~~text
Spoke
  |
TGW route
  |
Connect
  |
Security NVA
  |
post-inspection path
  |
Destination
~~~

Therefore:

> **Overlay routing is the foundation. Service insertion is one use of that routing foundation.**

The companion security article focuses on that second case.

---

## 21. Verification

Always prove the layers in order.

### 1. Underlay

Verify:

- transport attachment state;
- VPC routes;
- ENI reachability;
- Direct Connect if used.

### 2. GRE

Verify:

- outer endpoints;
- tunnel counters;
- MTU.

### 3. BGP

Verify:

- both sessions where expected;
- received prefixes;
- advertised prefixes;
- AS-PATH;
- next hop;
- route policy.

### 4. AWS route installation

Do not stop at the appliance BGP table.

Verify the route actually appears in TGW or Cloud WAN.

### 5. Effective route choice

Ask:

- Which route table is consulted?
- Which exact prefix wins?
- Is it static or propagated?
- Is another route more specific?
- Is ECMP actually active?

### 6. Data plane

Use:

- VPC Flow Logs;
- Transit Gateway Flow Logs;
- appliance packet capture;
- SD-WAN telemetry;
- application tests.

---

## 22. AWS CLI

### Connect attachments

~~~bash
aws ec2 describe-transit-gateway-connects --output table
~~~

### Connect peers

~~~bash
aws ec2 describe-transit-gateway-connect-peers --output json
~~~

### TGW associations

~~~bash
aws ec2 get-transit-gateway-route-table-associations \
  --transit-gateway-route-table-id tgw-rtb-EXAMPLE \
  --output table
~~~

### TGW propagations

~~~bash
aws ec2 get-transit-gateway-route-table-propagations \
  --transit-gateway-route-table-id tgw-rtb-EXAMPLE \
  --output table
~~~

### Effective TGW routes

~~~bash
aws ec2 search-transit-gateway-routes \
  --transit-gateway-route-table-id tgw-rtb-EXAMPLE \
  --filters Name=state,Values=active \
  --output table
~~~

The final command is often decisive because it shows the route AWS is actually prepared to use.

---

## 23. Exam takeaways

Memorize:

~~~text
TGW Connect
  transport = VPC or Direct Connect attachment
  data plane = GRE
  control plane = BGP
  static routes on Connect = not supported
  eBGP multihop TTL = 2
~~~

~~~text
One Connect peer
  = one GRE data path
  + two BGP sessions for control-plane redundancy
~~~

~~~text
TGW route-table association
  = lookup context for traffic entering from attachment
  + for Connect, routes advertised toward the appliance

TGW propagation
  = learned attachment routes installed into selected TGW route tables
~~~

~~~text
Cloud WAN Tunnel-less Connect
  = no GRE
  = native BGP
  = VPC remains transport
  = MP-BGP IPv4/IPv6 supported
~~~

The most useful operational rule is:

> **Never troubleshoot an overlay as one network. Prove the underlay, tunnel, BGP, AWS route installation, route-table selection, and data plane independently.**

---

## 24. References

Official AWS documentation:

- Transit Gateway Connect attachments and peers: https://docs.aws.amazon.com/vpc/latest/tgw/tgw-connect.html
- How Transit Gateway works and routing: https://docs.aws.amazon.com/vpc/latest/tgw/how-transit-gateways-work.html
- Transit Gateway route propagation: https://docs.aws.amazon.com/vpc/latest/tgw/enable-tgw-route-propagation.html
- VPC route priority and longest-prefix match: https://docs.aws.amazon.com/vpc/latest/userguide/route-tables-priority.html
- Cloud WAN Connect and Tunnel-less Connect: https://docs.aws.amazon.com/network-manager/latest/cloudwan/cloudwan-connect-attachment.html
- Direct Connect with Transit Gateway: https://docs.aws.amazon.com/directconnect/latest/UserGuide/direct-connect-transit-gateways.html

Related knowledgebase guides:

- [AWS Overlay Networking with Transit Gateway Connect and Cloud WAN Connect — Service Insertion Deep Dive](09-10-26-17-10_AWS_Overlay_Networking_TGW_Cloud_WAN_Connect_Service_Insertion_Deep_Dive.md)
- [AWS Firewall Insertion Summary](09-07-26_AWS_Firewall_Insertion_Summary.md)
- [AWS Cloud WAN Service Insertion — Deep Dive](09-06-26-17-01_AWS_Cloud_WAN_Service_Insertion_Deep_Dive.md)
- [AWS Direct Connect Transit VIF — Deep Dive](09-08-26_AWS_Direct_Connect_Transit_VIF_Deep_Dive.md)
