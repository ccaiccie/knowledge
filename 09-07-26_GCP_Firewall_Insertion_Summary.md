# GCP Firewall Insertion Summary

## Purpose

This guide condenses the major Google Cloud firewall insertion methods into a single decision-oriented reference. The goal is to make it easy to distinguish **Google-managed firewalling**, **transparent VM-Series interception**, **route-based VM-Series service insertion**, **same-VPC versus inter-VPC steering**, **hybrid inspection**, and **Internet ingress/egress**.

## Core mental model

There are four primary buckets:

| Method | What selects traffic? | Where is the firewall? | Routing change required? | Best mental label |
|---|---|---|---:|---|
| **Cloud NGFW Enterprise** | Google firewall policy | Google-managed distributed service | No | **Google-native firewall** |
| **VM-Series + NSI** | Google firewall policy → security profile | Palo Alto VM-Series in producer VPC | No normal route steering | **Transparent service insertion** |
| **VM-Series + PBR + internal passthrough ILB** | Policy-Based Route | Palo Alto VM-Series behind ILB | Yes | **Selective routed insertion** |
| **VM-Series + static route + internal passthrough ILB** | Destination route | Palo Alto VM-Series behind ILB | Yes | **Destination-based routed insertion** |

A useful shorthand is:

```text
Cloud NGFW = Google-managed firewall
NSI        = policy-driven transparent interception
PBR        = selective routing
Static     = destination routing
ILB        = highly available firewall next hop
PAN-OS     = actual firewall session/security/NAT state on VM-Series
```

---

## 1. Cloud NGFW Enterprise

Use this when you want Google-managed firewalling and do not want to operate firewall VMs.

```text
VM
 |
 v
Google VPC fabric
 |
 v
Cloud NGFW policy / inspection
 |
 v
Destination
```

Key points:

- Google owns and operates the firewall service.
- You configure Google firewall policies and security resources rather than PAN-OS policy.
- Palo Alto Networks technology powers advanced threat prevention, but this is not a customer-managed VM-Series firewall.
- There is no routed service-chain hop through a firewall VM.

**Memorize:**

> Cloud NGFW Enterprise = Google-managed firewalling in the VPC fabric.

**Deep dive:** [Google Cloud NGFW Enterprise Firewall Endpoints — Deep Dive](09-07-26-07-05_GCP_Cloud_NGFW_Enterprise_Firewall_Endpoints_Deep_Dive.md)

---

## 2. VM-Series + Network Security Integration (NSI)

NSI is the main transparent VM-Series insertion model.

The key distinction is:

> **NSI is selected by firewall policy, not by normal routing.**

Packet flow:

```text
Workload
   |
   | normal VPC routing
   v
Google firewall policy
   |
   | APPLY_SECURITY_PROFILE_GROUP
   v
NSI
   |
   | GENEVE
   v
Internal passthrough ILB
   |
   v
VM-Series
   |
   | inspection verdict
   v
GENEVE reinjection
   |
   v
original GCP forwarding path
```

Key points:

- The consumer VPC does not need a route such as `10.0.0.0/8 -> firewall` merely to invoke inspection.
- Google firewall policy chooses the flow.
- NSI transports the original packet to VM-Series using GENEVE.
- PAN-OS performs stateful inspection of the inner flow.
- Allowed traffic is reinjected into the Google forwarding path.

**Memorize:**

> NSI = policy, not routing.

**Deep dive:** [Palo Alto Networks Firewalling in Google Cloud — Cloud NGFW Enterprise Integration vs VM-Series Service Insertion](09-07-26-07-03_Palo_Alto_Networks_Firewalling_in_GCP_Deep_Dive.md)

---

## 3. NSI Internet egress: two variants

### 3.1 Standard NSI Internet egress

VM-Series inspects the flow and gives it back to the consumer VPC.

```text
Consumer VM
   |
   v
NSI / GENEVE
   |
   v
VM-Series
   |
   v
reinject into consumer VPC
   |
   v
consumer routing / Cloud NAT
   |
   v
Internet
```

Key points:

- VM-Series is the inspection engine, not the final Internet router.
- Consumer VPC routing still decides Internet egress after reinjection.
- Cloud NAT can remain the SNAT owner.
- Return packets for an established intercepted session are automatically re-intercepted as part of NSI state.

**Memorize:**

> Standard NSI = inspect and give it back.

**Deep dive:** [Palo Alto Networks Firewalling in Google Cloud — Cloud NGFW Enterprise Integration vs VM-Series Service Insertion](09-07-26-07-03_Palo_Alto_Networks_Firewalling_in_GCP_Deep_Dive.md)

### 3.2 NSI direct Internet egress / Overlay

Here VM-Series becomes the actual Internet egress device for the selected flow.

```text
Consumer VM
   |
   v
NSI / GENEVE
   |
   v
VM-Series Trust
   |
   | PAN-OS route + Security + NAT
   v
VM-Series Untrust
   |
   v
Internet
```

Return:

```text
Internet
   |
   v
VM-Series Untrust
   |
   | reverse NAT / stateful inspection
   v
GENEVE
   |
   v
Consumer VM
```

Key points:

- VM-Series owns the Internet route/NAT for the selected flow.
- Consumer Cloud NAT is not required for that direct-egress flow.
- PAN-OS routing and NAT become part of the data path.

**Memorize:**

> NSI direct egress = VM-Series becomes the Internet router/NAT device.

**Deep dive:** [Palo Alto Networks Firewalling in Google Cloud — Cloud NGFW Enterprise Integration vs VM-Series Service Insertion](09-07-26-07-03_Palo_Alto_Networks_Firewalling_in_GCP_Deep_Dive.md)

---

## 4. Traditional VM-Series + internal passthrough ILB

This is explicit routed service insertion.

```text
Source
 |
 | PBR or static route
 v
Internal passthrough ILB
 |
 v
VM-Series
 |
 | PAN-OS routing/security/NAT
 v
Destination
```

The internal passthrough ILB acts as a **highly available next hop**, not as the final application VIP.

Important behavior:

- Google delivers the original packet to a selected firewall backend.
- The original source and destination tuple are preserved.
- PAN-OS performs session lookup, Security policy, App-ID, threat inspection, optional NAT, and routing.
- After VM-Series forwards the packet, it re-enters the Google VPC data plane and another route lookup occurs.

**Memorize:**

> Traditional VM-Series insertion = routed service chain through an ILB-backed firewall fleet.

**Deep dive:** [Palo Alto Networks Firewalling in Google Cloud — Cloud NGFW Enterprise Integration vs VM-Series Service Insertion](09-07-26-07-03_Palo_Alto_Networks_Firewalling_in_GCP_Deep_Dive.md)

---

## 5. PBR versus static route

This distinction removes a lot of confusion.

### PBR = selective steering

Use a Policy-Based Route when you care about more than just destination prefix.

Examples:

```text
source      = app subnet
destination = DB subnet
protocol    = TCP
tag         = inspect
             |
             v
firewall ILB
```

PBR can select based on:

- source prefix;
- destination prefix;
- protocol;
- VM network tags;
- Cloud Interconnect attachment region.

**Memorize:**

> PBR = selective routing.

**Deep dive:** [Google Cloud Policy-Based Routing (PBR) — Comprehensive Study Guide](09-05-26-08-12_GCP_Policy_Based_Routing_Study_Guide.md)

### Static route = destination steering

Use a static route when the destination prefix alone is sufficient.

Examples:

```text
10.20.0.0/16 -> VM-Series ILB
0.0.0.0/0    -> VM-Series ILB
```

**Memorize:**

> Static route = destination-based routing.

**Deep dive:** [Google Cloud Firewall Inspection and Service Insertion — Comprehensive Study Guide](09-06-26-18-58_GCP_Firewall_Inspection_Insertion_Comprehensive_Study_Guide.md)

---

## 6. Same-VPC east-west inspection

If two subnets are in the same VPC, use PBR when you need to force traffic through VM-Series.

```text
10.10.1.0/24
     |
     | PBR
     v
ILB
 |
 v
VM-Series
 |
 v
10.10.2.0/24
```

Return traffic needs the corresponding steering path:

```text
10.10.2.0/24
     |
     | reverse PBR
     v
ILB
 |
 v
VM-Series
 |
 v
10.10.1.0/24
```

Why PBR?

Because normal subnet routing already knows how to reach the other subnet directly. PBR lets the firewall service override that direct path for the selected traffic.

**Memorize:**

> Same VPC = PBR.

**Deep dive:** [Google Cloud Policy-Based Routing (PBR) — Comprehensive Study Guide](09-05-26-08-12_GCP_Policy_Based_Routing_Study_Guide.md)

---

## 7. Inter-VPC inspection with VPC Network Peering

You do **not** need Network Connectivity Center for this specific design.

Architecture:

```text
Spoke A VPC
   |
   | VPC Peering
   v
Security / Hub VPC
   |
   | internal passthrough ILB
   v
VM-Series
   |
   | VPC Peering
   v
Spoke B VPC
```

Important fact:

> VPC Network Peering is non-transitive.

This means:

```text
A peers with Hub
B peers with Hub
```

does not mean:

```text
A automatically learns B
```

The common pattern is to export an **untagged custom static route** from the hub and import it into the spokes.

Example:

```text
10.0.0.0/8 -> firewall ILB
```

Spoke A imports the route. Traffic to a remote spoke destination such as `10.20.1.20` matches that aggregate and is sent to the hub firewall.

After VM-Series forwards the packet into the hub, the hub's more-specific directly learned peering subnet route toward Spoke B wins:

```text
10.20.0.0/16 via hub-to-spoke-b peering
```

That prevents the packet from looping back into the firewall route.

**Memorize:**

> Different VPCs with simple peering = exported static route through the firewall.

And:

> Peering is non-transitive; the firewall route creates the deliberate transit path.

**Deep dive:** [Google Cloud Firewall Inspection and Service Insertion — Comprehensive Study Guide](09-06-26-18-58_GCP_Firewall_Inspection_Insertion_Comprehensive_Study_Guide.md)

---

## 8. Where Network Connectivity Center fits

NCC is a different architecture, not a requirement for the peering design above.

Use NCC when you want a more scalable, dynamic routing fabric, especially with:

- BGP;
- Router Appliance spokes;
- many VPCs;
- hybrid connectivity;
- centralized route exchange;
- dynamic route propagation.

Conceptually:

```text
              NCC Hub
          /      |       \
       VPC      VPC    Router Appliance
                         |
                         v
                      VM-Series
                         |
                         BGP
```

**Memorize:**

> Peering design = static route exchange.

> NCC Router Appliance design = dynamic BGP route exchange.

**Deep dive:** [GCP Firewall Insertion with NCC Router Appliance + BGP — Deep Dive](09-07-26-09-03_GCP_NCC_Router_Appliance_BGP_Firewall_Insertion_Deep_Dive.md)

---

## 9. On-premises inspection through Cloud Interconnect

Cloud Interconnect traffic can be steered through VM-Series with PBR.

```text
On-prem
   |
   v
Cloud Interconnect
   |
   v
VLAN attachment
   |
   | PBR
   v
ILB
   |
   v
VM-Series
   |
   v
Workload
```

A PBR can be scoped to Cloud Interconnect VLAN attachments by region.

Important concept:

- The PBR belongs to the VPC.
- It is not attached to an AWS-style route table or a subnet.
- Scope determines where the route applies.

**Memorize:**

> Interconnect inbound = PBR can apply at the VLAN attachment ingress context.

**Deep dive:** [Google Cloud Policy-Based Routing (PBR) — Comprehensive Study Guide](09-05-26-08-12_GCP_Policy_Based_Routing_Study_Guide.md)

---

## 10. Return traffic to Cloud Interconnect

The inbound PBR and return PBR often need different scopes because the packet source context changes.

Forward:

```text
Interconnect attachment
   |
   | Interconnect-scoped PBR
   v
VM-Series
   |
   v
Workload
```

Return:

```text
Workload VM
   |
   | VM-tag or appropriate workload PBR
   v
ILB
   |
   v
VM-Series
   |
   v
Cloud Router
   |
   v
Interconnect
   |
   v
On-prem
```

**Memorize:**

> Forward and return directions can have different PBR scopes because they originate from different GCP endpoint types.

**Deep dive:** [Google Cloud Policy-Based Routing (PBR) — Comprehensive Study Guide](09-05-26-08-12_GCP_Policy_Based_Routing_Study_Guide.md)

---

## 11. HA VPN inspection

The overall concept is similar to Interconnect, but PBR scoping differs.

```text
On-prem
 |
 v
HA VPN
 |
 v
VPC
 |
 | network-wide PBR
 v
ILB
 |
 v
VM-Series
 |
 v
Workload
```

Key distinction:

- Interconnect supports attachment-region-aware PBR scoping.
- HA VPN typically relies on broader VPC PBR applicability.

**Memorize:**

> Interconnect can have attachment-region-specific PBR scope; HA VPN generally uses broader VPC scope.

**Deep dive:** [Google Cloud Policy-Based Routing (PBR) — Comprehensive Study Guide](09-05-26-08-12_GCP_Policy_Based_Routing_Study_Guide.md)

---

## 12. Traditional Internet egress through VM-Series

```text
Workload
 |
 | default route / PBR
 v
Trust ILB
 |
 v
VM-Series Trust
 |
 | Security
 | routing
 | SNAT
 v
VM-Series Untrust
 |
 v
Internet
```

In this model PAN-OS can own Internet NAT state.

This differs from standard NSI, where the packet is normally reinjected into the consumer VPC and Cloud NAT can remain the translator.

**Memorize:**

> Traditional routed model = PAN-OS can be the actual Internet gateway/NAT device.

**Deep dive:** [Palo Alto Networks Firewalling in Google Cloud — Cloud NGFW Enterprise Integration vs VM-Series Service Insertion](09-07-26-07-03_Palo_Alto_Networks_Firewalling_in_GCP_Deep_Dive.md)

---

## 13. Internet ingress through VM-Series

Typical pattern:

```text
Internet
 |
 v
External passthrough / supported external LB
 |
 v
VM-Series Untrust
 |
 | DNAT / Security
 v
Trust
 |
 v
Application
```

Return:

```text
Application
 |
 v
VM-Series
 |
 | reverse NAT / existing session
 v
Internet
```

The important principle is state symmetry:

> Return traffic must come back through the firewall that owns the relevant state/NAT relationship.

**Deep dive:** [Palo Alto Networks Firewalling in Google Cloud — Cloud NGFW Enterprise Integration vs VM-Series Service Insertion](09-07-26-07-03_Palo_Alto_Networks_Firewalling_in_GCP_Deep_Dive.md)

---

## 14. PBR recursion and firewall bypass

A broad PBR can accidentally catch packets emitted by the firewall after inspection.

Bad path:

```text
VM-Series
 |
 | same PBR again
 v
ILB
 |
 v
VM-Series
 |
 v
loop
```

Typical solution:

```text
firewall VM tag = pan-fw
```

Create a higher-priority PBR for firewall VMs that uses normal routing instead of interception:

```text
pan-fw tagged VM
     |
     v
DEFAULT_ROUTING
```

Then:

```text
VM-Series
 |
 | firewall bypass PBR
 v
normal GCP routing
```

**Memorize:**

> Workloads get steering PBRs; firewall VMs get bypass PBRs.

**Deep dive:** [Google Cloud Policy-Based Routing (PBR) — Comprehensive Study Guide](09-05-26-08-12_GCP_Policy_Based_Routing_Study_Guide.md)

---

## 15. Symmetric hashing

Internal passthrough ILB next-hop designs can use symmetric hashing so forward and reverse tuples are more likely to select the same eligible firewall backend.

But symmetric hashing does not fix incorrect routing.

You still need:

- both directions to reach the firewall service;
- compatible backend sets;
- consistent health state;
- valid PAN-OS session ownership.

**Memorize:**

> Symmetric hashing helps backend symmetry; it does not repair asymmetric routing.

**Deep dive:** [Palo Alto Networks Firewalling in Google Cloud — Cloud NGFW Enterprise Integration vs VM-Series Service Insertion](09-07-26-07-03_Palo_Alto_Networks_Firewalling_in_GCP_Deep_Dive.md)

---

## 16. One-page cheat sheet

```text
GOOGLE-MANAGED FIREWALL
Cloud NGFW Enterprise
= Google policy
= no firewall VMs

TRANSPARENT PAN FIREWALL
VM-Series + NSI
= firewall policy selects traffic
= GENEVE
= no normal route steering

SAME VPC
VM-Series + PBR
= selective service insertion

DIFFERENT VPCs WITH PEERING
VM-Series + ILB + exported static route
= no NCC required
= peering is non-transitive

LARGE / DYNAMIC MULTI-VPC
NCC + Router Appliance + BGP
= dynamic route exchange

ON-PREM INTERCONNECT
PBR scoped to Interconnect attachment region
-> ILB
-> VM-Series

HA VPN
network-wide or broadly scoped PBR
-> ILB
-> VM-Series

TRADITIONAL INTERNET EGRESS
default route / PBR
-> Trust ILB
-> VM-Series
-> SNAT
-> Internet

NSI STANDARD INTERNET
NSI
-> VM-Series
-> reinject
-> consumer Cloud NAT / Internet route

NSI DIRECT EGRESS
NSI
-> VM-Series
-> PAN-OS route / NAT
-> Internet
```

---

## 17. Decision tree

```text
Do you want Google-managed firewalling?
        |
       YES
        |
        v
Cloud NGFW Enterprise

Do you specifically want PAN-OS / VM-Series?
        |
       YES
        |
        v
Do you want transparent insertion
without changing workload routing?
        |
       YES
        |
        v
NSI

Do you need a routed VM-Series service chain?
        |
       YES
        |
        v
Same VPC?
   |
  YES -> PBR

Different VPCs, simple peering topology?
   |
  YES -> VPC Peering + exported static route + ILB

Large / dynamic / BGP topology?
   |
  YES -> NCC + Router Appliance + BGP

Hybrid traffic?
   |
   +-> Interconnect -> PBR with attachment-region scope
   |
   +-> HA VPN -> broader VPC PBR scope
```

---

## 18. Final mnemonic

```text
NSI     = Policy
PBR     = Selective routing
Static  = Destination routing
Peering = Simple multi-VPC
NCC     = Dynamic scalable multi-VPC
ILB     = HA firewall next hop
PAN-OS  = Inspection + session + optional NAT
```

If those seven associations are clear, most GCP firewall-insertion scenarios become a matter of deriving the correct path rather than memorizing every implementation detail.

---

## Sources

- https://github.com/ccaiccie/knowledge/blob/main/09-07-26-07-03_Palo_Alto_Networks_Firewalling_in_GCP_Deep_Dive.md
- https://docs.cloud.google.com/network-security-integration/docs/nsi-overview
- https://docs.cloud.google.com/network-security-integration/docs/in-band/in-band-integration-overview
- https://docs.cloud.google.com/vpc/docs/policy-based-routes
- https://docs.cloud.google.com/vpc/docs/vpc-peering
- https://docs.cloud.google.com/load-balancing/docs/internal/ilb-next-hop-overview
- https://cloud.google.com/network-connectivity/docs/network-connectivity-center/concepts/overview
- https://docs.paloaltonetworks.com/vm-series/deployment/public-cloud/set-up-the-vm-series-firewall-on-google-cloud-platform
