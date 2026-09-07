# Google Cloud Firewall Inspection and Service Insertion — Comprehensive Study Guide

> **Last reviewed:** 2026-09-06

## URLs reviewed

- https://docs.cloud.google.com/firewall/docs/about-firewalls
- https://docs.cloud.google.com/firewall/docs/about-firewall-endpoints
- https://docs.cloud.google.com/firewall/docs/manage-firewall-endpoints
- https://docs.cloud.google.com/firewall/docs/about-tls-inspection
- https://docs.cloud.google.com/network-security-integration/docs/nsi-overview
- https://docs.cloud.google.com/network-security-integration/docs/in-band/in-band-integration-tutorial
- https://docs.cloud.google.com/network-security-integration/docs/understand-geneve
- https://docs.cloud.google.com/network-security-integration/docs/out-of-band/out-of-band-integration-overview
- https://docs.cloud.google.com/vpc/docs/policy-based-routes
- https://docs.cloud.google.com/vpc/docs/use-policy-based-routes
- https://docs.cloud.google.com/load-balancing/docs/internal/ilb-next-hop-overview
- https://docs.cloud.google.com/load-balancing/docs/internal/setting-up-ilb-next-hop
- https://docs.cloud.google.com/network-connectivity/docs/network-connectivity-center
- https://docs.cloud.google.com/network-connectivity/docs/network-connectivity-center/concepts/connectivity-topologies
- https://docs.cloud.google.com/network-connectivity/docs/network-connectivity-center/how-to/creating-router-appliances
- https://docs.cloud.google.com/network-connectivity/docs/network-connectivity-center/how-to/connect-site-to-cloud
- https://docs.cloud.google.com/architecture/best-practices-vpc-design
- https://cloud.google.com/blog/products/networking/policy-based-routing-network-patterns-for-virtual-appliances

## Firewall insertion taxonomy

Google Cloud uses several different mechanisms rather than one universal gateway-load-balancer construct.

| # | Method | Steering point | Inline? | Best fit |
|---|---|---|---|---|
| 1 | Cloud NGFW distributed policy | Hierarchical/global/regional firewall policy | Yes, distributed | Broad stateful L3/L4 segmentation |
| 2 | Cloud NGFW Enterprise firewall endpoints | `apply_security_profile_group` + packet intercept | Yes | Native IPS, URL filtering, TLS inspection |
| 3 | Network Security Integration (NSI) in-band | Firewall policy + intercept endpoint | Yes | Transparent third-party inspection with GENEVE |
| 4 | Policy-Based Route (PBR) → internal passthrough NLB → NVA | Source/destination/protocol policy | Yes | Fine-grained service insertion, including hybrid ingress |
| 5 | Static route → internal passthrough NLB → NVA | Destination-prefix route | Yes | Default-route egress and transit firewall pools |
| 6 | Direct next-hop VM / multi-NIC firewall | Static route/topology | Yes | Traditional trust-zone bridge/router design |
| 7 | NCC Router Appliance + BGP | Dynamic BGP route exchange | Yes when routed through appliance | Hybrid/site-to-cloud/site-to-site transit |
| 8 | NCC Gateway + Security Service Edge (SSE) | NCC spoke-group/gateway topology | Yes for eligible paths | Cloud-delivered security service insertion |
| 9 | Load-balancer sandwich / proxy-fronted firewall | External/internal LB topology | Yes for application path | Published applications and proxy-centric security |
| 10 | Packet Mirroring / NSI out-of-band / Cloud IDS | Mirroring policy | **No** | Passive detection and analysis |

The critical distinction is whether GCP **enforces policy in the distributed fabric**, **intercepts packets transparently**, or **changes routing so an appliance becomes the next hop**.

---

## 1. Cloud NGFW distributed firewall policy

Cloud Next Generation Firewall (Cloud NGFW) provides stateful distributed enforcement through hierarchical, global, and regional firewall policies. The packet is filtered as part of Google Cloud's virtual networking path; it is not routed through a customer-owned firewall VM.

Use it for organization-wide segmentation, same-VPC east-west controls, north-south stateful filtering, and Standard-tier policy features such as supported FQDN/threat-intelligence objects. If the requirement is that a Palo Alto, Fortinet, Check Point, Cisco, or custom NVA must actually receive the packet, use one of the insertion methods below instead.

---

## 2. Cloud NGFW Enterprise firewall endpoint insertion

Cloud NGFW Enterprise provides Layer 7 inspection through **zonal firewall endpoints**. Firewall policy rules can use `apply_security_profile_group` to select traffic for Google Cloud packet intercept. The workload's normal route does not need to point to a firewall VM.

![Cloud NGFW Enterprise packet-intercept architecture](images/09-06-26-18-58_gcp_cloud_ngfw_enterprise_packet_intercept.svg)

[Editable draw.io](images/09-06-26-18-58_gcp_cloud_ngfw_enterprise_packet_intercept.drawio)

**What this image shows:** policy-selected traffic is intercepted, inspected by a zonal Cloud NGFW Enterprise endpoint, and then allowed/reinjected or dropped.

**What matters:** endpoints and endpoint associations are zonal; the protected workload must be in a zone with the required association. Security profiles/security profile groups define advanced inspection.

**What to verify:** endpoint state, association state, winning firewall rule, workload zone, security profile group, TLS trust, MTU, and endpoint utilization.

### Packet flow

For `10.10.1.10:51514 -> 10.20.1.20:443`:

1. Client emits the packet.
2. Hierarchical/global firewall policy evaluates the flow.
3. A matching rule uses `apply_security_profile_group`.
4. Packet intercept diverts the selected flow to the zonal firewall endpoint.
5. If TLS inspection is configured, Cloud NGFW decrypts, inspects, and re-encrypts the connection.
6. IDS/IPS, URL filtering, malware inspection, or other enabled Enterprise services evaluate it.
7. Approved traffic is reinjected to the original destination; denied traffic is not forwarded.
8. Return traffic is handled by the stateful inspection service.

Google currently documents up to **10 Gbps without TLS inspection** and **2 Gbps with TLS inspection** per endpoint, with per-connection maxima of **1.25 Gbps without TLS** and **250 Mbps with TLS**. Overload can cause packet loss, so capacity is part of the architecture.

### Representative configuration

```cli
gcloud network-security firewall-endpoints create endpoint-ips \
  --organization=ORGANIZATION_ID \
  --zone=ZONE \
  --billing-project=PROJECT_ID
```

```cli
gcloud network-security firewall-endpoint-associations create endpoint-association-ips \
  --endpoint=organizations/ORGANIZATION_ID/locations/ZONE/firewallEndpoints/endpoint-ips \
  --network=VPC_NAME \
  --zone=ZONE \
  --project=PROJECT_ID
```

### Verification

```cli
gcloud network-security firewall-endpoints list \
  --organization=ORGANIZATION_ID \
  --location=ZONE
```

```cli
gcloud network-security firewall-endpoint-associations list \
  --project=PROJECT_ID \
  --location=ZONE
```

**Success:** endpoint and association are active and reference the expected zone/VPC. **Failure:** wrong zone, inactive association, wrong profile, TLS trust failure, MTU mismatch, or endpoint saturation.

---

## 3. Network Security Integration in-band third-party packet intercept

NSI adds a **producer-consumer** model for third-party inspection. A security team can operate appliances in a producer VPC while consumer VPCs select traffic for interception through firewall policy.

The producer side contains zonal deployments backed by an **internal passthrough Network Load Balancer** and network-appliance VMs. The consumer references the inspection service through endpoint resources and a security profile group.

![NSI in-band third-party service insertion](images/09-06-26-18-58_gcp_nsi_inband_third_party_insertion.svg)

[Editable draw.io](images/09-06-26-18-58_gcp_nsi_inband_third_party_insertion.drawio)

**What this image shows:** consumer policy selects traffic; GCP encapsulates it in GENEVE; a producer ILB distributes it to a third-party firewall; allowed traffic is reinjected.

**What matters:** this is transparent packet interception, not a workload route to the firewall ILB.

**What to verify:** consumer endpoint association, security profile group, producer deployment, ILB health, appliance GENEVE handling, and UDP/6081 reachability.

### Packet flow

1. Consumer packet matches an NSI firewall-policy rule.
2. The rule references a security profile group containing a custom intercept profile.
3. Google Cloud encapsulates the packet in **GENEVE**.
4. The producer ILB receives the encapsulated flow and hashes it to a healthy appliance.
5. The firewall decapsulates and inspects the original packet.
6. It drops the packet or reinjects it through the logical bidirectional GENEVE mechanism.
7. Google Cloud resumes delivery to the original endpoint.

Google-specific GENEVE metadata includes items such as network cookie, endpoint cookie, and profile ID. This is useful when centralized inspection must distinguish overlapping consumer networks.

Producer appliances must permit GENEVE from the documented subnet gateway source. The Google tutorial uses:

```cli
gcloud compute network-firewall-policies rules create 100 \
  --firewall-policy=producer-firewall-policy \
  --global-firewall-policy \
  --action=allow \
  --direction=INGRESS \
  --layer4-configs=udp:6081 \
  --src-ip-ranges=GATEWAY_IP/32
```

Use NSI in-band when the vendor supports this model and you want third-party inspection without rewriting consumer routes. Use PBR instead when you need explicit route-driven transit or the appliance/vendor is not integrated with NSI.

---

## 4. Policy-Based Route → internal passthrough NLB → firewall NVA

PBR is the strongest classic **fine-grained service-insertion** mechanism. It can classify on source range, destination range, and protocol, then send matching traffic to an internal passthrough NLB that fronts health-checked firewall VMs.

![PBR plus ILB plus NVA service insertion](images/09-06-26-18-58_gcp_pbr_ilb_nva_service_insertion.svg)

[Editable draw.io](images/09-06-26-18-58_gcp_pbr_ilb_nva_service_insertion.drawio)

**What this image shows:** hybrid traffic arriving from on-premises is selected by PBR, sent to an ILB-backed NVA pool, then returned to normal VPC routing after inspection.

**What matters:** PBR is evaluated before ordinary subnet/static/dynamic routes, after special routing paths. The firewall's second-stage route lookup must not send the packet back into the same intercept rule.

**What to verify:** PBR scope/priority, ILB global access when needed, backend IP forwarding, health checks, and the reverse-path design.

### Scope

Google documents PBR applicability to:

- all VM instances, Cloud Interconnect VLAN attachments, and Cloud VPN tunnels in the VPC;
- only tagged VM instances;
- VLAN attachments in a specific region.

This makes PBR especially valuable for **Cloud Interconnect ingress inspection**.

### Hybrid ingress example

For `10.100.100.10 on-prem -> 10.20.10.20 workload`:

1. Packet arrives on the Interconnect VLAN attachment.
2. PBR matches source `10.100.100.0/24` and destination `10.20.10.0/24`.
3. GCP sends it to the internal passthrough NLB instead of directly following the subnet route.
4. The ILB chooses a healthy firewall backend and preserves the original packet tuple.
5. Firewall inspects the packet and sends it back into the VPC fabric.
6. A new lookup follows the normal route to `10.20.10.0/24` because the appliance itself is not in the original intercept scope.
7. The return path must cross the same firewall state domain when stateful inspection requires symmetry.

Backend appliance VMs must have **IP forwarding enabled**. PBR priorities should be unique; equal-priority policy matches are not resolved by longest-prefix matching.

### Representative configuration and verification

```cli
gcloud network-connectivity policy-based-routes create PBR_NAME \
  --network=VPC_URI \
  --priority=1000 \
  --source-range=SOURCE_CIDR \
  --destination-range=DESTINATION_CIDR \
  --protocol-version=IPV4 \
  --next-hop-ilb-ip=ILB_VIP
```

```cli
gcloud network-connectivity policy-based-routes list
```

```cli
gcloud network-connectivity policy-based-routes describe PBR_NAME
```

**Success:** correct network, source/destination filters, priority, scope, and ILB next hop. **Failure:** wrong scope, wrong priority, appliance re-matching the same PBR and looping, or asymmetric return routing.

---

## 5. Static route → internal passthrough NLB → firewall pool

A custom static route can use an **internal passthrough Network Load Balancer as the next hop**. The ILB distributes traffic to health-checked appliance VMs.

This is best when the policy is fundamentally destination-based:

- `0.0.0.0/0` to an Internet egress firewall pool;
- remote private prefixes to a transit firewall;
- shared-service prefixes that must cross a firewall zone.

### Difference from PBR

Static routes match destination prefix and participate in ordinary route selection. PBR is evaluated earlier and can also classify by source and protocol. Use PBR for selective policy; use a static next-hop-ILB route for simple destination/default routing.

### Major limitation

Google explicitly documents that next-hop-ILB static routes **cannot override subnet routes**. Therefore a static route is not the tool for arbitrary same-VPC subnet-to-subnet interception. Use PBR or packet intercept for that.

### Internet egress packet flow

1. Workload sends to an Internet IP.
2. Custom `0.0.0.0/0` points to the internal passthrough NLB.
3. ILB selects a healthy firewall backend.
4. Firewall applies policy and, if it is the egress identity, performs SNAT.
5. Firewall forwards toward the default Internet gateway.
6. Return traffic must reach the same state/NAT domain.

Representative route:

```cli
gcloud compute routes create default-via-firewall-ilb \
  --network=VPC_NAME \
  --destination-range=0.0.0.0/0 \
  --next-hop-ilb=ILB_FORWARDING_RULE \
  --next-hop-ilb-region=REGION \
  --priority=900
```

Verify:

```cli
gcloud compute routes describe default-via-firewall-ilb
```

```cli
gcloud compute forwarding-rules describe ILB_FORWARDING_RULE --region=REGION
```

```cli
gcloud compute backend-services get-health BACKEND_SERVICE --region=REGION
```

Google cautions against routing Google APIs/services through next-hop VMs or next-hop internal passthrough NLBs; follow current documented Google-service routing guidance for those destinations.

---

## 6. Direct next-hop VM / multi-NIC firewall between VPCs

This is the traditional trust-zone model. A firewall VM has multiple NICs, for example an outside NIC in an untrusted/transit VPC and an inside NIC in a protected VPC. Google architecture guidance describes a stateful Layer 7 firewall bridging/routing between VPC networks.

Typical path:

```text
Internet / On-prem
       |
Outside / transit VPC
       |
Firewall outside NIC
       |
policy + NAT + session state
       |
Firewall inside NIC
       |
Trusted workload VPC
```

Use this when explicit topology matters, the vendor firewall owns routing/NAT/VPN functions, or a legacy design already depends on multi-NIC trust zones. The tradeoffs are VM-scale chokepoints, more complex HA, and the need to engineer every forward and reverse route.

A direct next-hop VM can be used, but production designs often prefer an ILB-backed firewall pool because the ILB provides health-checked next-hop distribution.

---

## 7. Network Connectivity Center Router Appliance + BGP

NCC supports third-party **Router Appliance** VMs as spokes. The appliance forms BGP sessions with Cloud Router and can be a router, SD-WAN edge, or firewall/router combination.

This is a **dynamic-routing insertion pattern**: BGP makes selected prefixes reachable through the NVA. Cloud Router is control plane only; the appliance VM is the data-plane hop.

### Good use cases

- site-to-cloud connectivity through a firewall/SD-WAN edge;
- site-to-site transit through GCP;
- dynamic route learning and advertisement;
- architectures where route policy should be controlled with BGP rather than many static/PBR objects.

Google documents TCP/179 reachability and RFC1918 addressing for the Router Appliance peering relationship.

### Packet path

1. On-premises advertises a prefix toward the NVA.
2. NVA exchanges routes with Cloud Router/NCC.
3. GCP installs/selects a path through the appliance.
4. Workload packet traverses the NVA.
5. Firewall policy/session inspection occurs.
6. NVA forwards to the remote site.
7. Reverse advertisements must force the return flow through the same stateful path.

Verify:

```cli
gcloud network-connectivity spokes list
```

```cli
gcloud compute routers get-status CLOUD_ROUTER_NAME --region=REGION
```

**Success:** BGP peers are established and the expected prefixes are learned/advertised. **Failure:** idle/active BGP state, missing routes, or a more-preferred bypass path.

---

## 8. NCC Gateway + Security Service Edge

NCC Gateway spokes can integrate with third-party **Security Service Edge (SSE)** services. This is different from operating firewall VMs inside your own VPC.

Current NCC topology documentation states that SSE inspection is available for traffic routed between an **NCC Gateway spoke in the gateways spoke group** and spokes in the **prod, non-prod, or services** groups.

Use it when you want cloud-delivered security, workforce/hybrid access enforcement, and an NCC hub as the connectivity fabric. Do not assume every Interconnect/VPN/Router-Appliance flow is automatically inspected; validate the actual spoke-group path and current provider support.

---

## 9. Load-balancer sandwich / proxy-fronted firewall

For published applications, a firewall or reverse-proxy appliance tier can sit between an external frontend and protected backend services:

```text
Internet
  |
External LB / public VIP
  |
Firewall / security proxy tier
  |
Internal LB / application service
  |
Backends
```

This is useful when the appliance is intentionally proxying or terminating the application flow. It is not the same as transparent PBR/NSI insertion because the proxy can create new transport sessions and alter source-IP, port, TLS, health-check, and return-path behavior.

**Cloud Armor note:** Cloud Armor is a WAF/DDoS policy service on supported Google Cloud load balancers. It is valuable application protection, but it is not a generic routed L3/L4 firewall insertion mechanism.

---

## 10. Packet Mirroring / NSI out-of-band / Cloud IDS — not inline

Packet Mirroring creates a **copy** of traffic. NSI out-of-band can use firewall-policy mirroring rules to deliver GENEVE-encapsulated copies to collector appliances. Cloud IDS is similarly a detection-oriented service.

The original packet does **not** traverse the collector. Therefore, if the requirement is "malicious traffic must be blocked before delivery," choose an inline method: Cloud NGFW Enterprise, NSI in-band, PBR/ILB/NVA, static-route/ILB/NVA, or a routed firewall topology.

---

# Method selection by traffic direction

## Same-VPC east-west

Prefer Cloud NGFW distributed policy for L3/L4 segmentation, Cloud NGFW Enterprise for native L7 inspection, NSI in-band for third-party transparent inspection, or PBR→ILB→NVA for explicit third-party steering. Static routes cannot override ordinary subnet routes for arbitrary same-VPC subnet traffic.

## Multi-VPC east-west

Use NSI producer/consumer insertion, Cloud NGFW Enterprise endpoint associations, a transit VPC with ILB-backed firewalls, or NCC Router Appliance when BGP-driven transit is the design requirement.

## Internet egress

Common patterns are native Cloud NGFW, default static route to an ILB-backed firewall pool, selective PBR, a multi-NIC egress firewall that performs SNAT, or NCC Gateway/SSE where supported. Decide explicitly **where SNAT occurs** and make the reverse path return through the state owner.

## Internet ingress

Options include external Application Load Balancer + Cloud Armor for HTTP(S) WAF, Cloud NGFW Enterprise, NSI in-band, or an explicit public-facing/multi-NIC firewall/load-balancer sandwich. DNAT designs must preserve a symmetric return path for reverse NAT and session state.

## Cloud Interconnect ingress

PBR is especially useful because it can apply to regional VLAN attachments. Traffic can arrive from on-premises, match source/destination criteria, be sent to the firewall ILB, and then re-enter normal VPC routing after inspection. Choose NCC Router Appliance instead when the firewall must participate directly in BGP transit.

## Cloud VPN ingress

PBR can apply to VPN traffic in its documented route scope. NCC Router Appliance is appropriate when the inspection device is also the dynamic routing edge. Verify the exact tunnel/spoke model before assuming fine-grained per-tunnel behavior.

---

# Stateful symmetry, NAT, and HA

For every stateful firewall design, draw both directions:

```text
Forward: source -> steering point -> firewall -> destination
Return:  destination -> steering point -> same state domain -> source
```

Verify: route/PBR/policy decision in each direction, load-balancer hashing behavior, vendor state synchronization, SNAT/DNAT location, competing more-specific routes, and failure behavior.

The internal passthrough NLB is not an application proxy; routing, filtering, proxying, and NAT are the NVA's responsibility. It can provide health-checked backend selection, but it does **not** guarantee that unrelated firewall nodes share session state.

Cloud NGFW firewall endpoints and NSI deployments are zonal constructs, so a multi-zone application requires matching deployment/association planning. Router Appliance HA should use redundant appliances/BGP sessions and validate route withdrawal, convergence, and transient asymmetry.

---

# Common mistakes

1. Calling Packet Mirroring inline inspection.
2. Trying to override a same-VPC subnet route with a static next-hop-ILB route.
3. Forgetting IP forwarding on firewall VM backends.
4. Treating Cloud Router as a packet-forwarding hop.
5. Assuming the ILB automatically solves state synchronization.
6. Forgetting the PBR second-stage lookup and creating a loop.
7. Sending Google APIs/services through next-hop appliances contrary to current Google guidance.
8. Ignoring Cloud NGFW firewall-endpoint zones.
9. Ignoring MTU and GENEVE encapsulation overhead.
10. Assuming NCC SSE inspection applies to every spoke combination.

---

# Troubleshooting by symptom

## Traffic bypasses the firewall

```cli
gcloud network-connectivity policy-based-routes list
```

```cli
gcloud compute routes list --filter='network:VPC_NAME'
```

**Tests:** installed steering objects, scope, priority, and competing routes. **Failure means:** wrong PBR filter/scope, direct subnet route winning in a static-route design, wrong policy association, or a bypass route. **Next:** describe the exact route/PBR and trace both directions separately.

## ILB selected but appliance gets no packets

```cli
gcloud compute backend-services get-health BACKEND_SERVICE --region=REGION
```

**Success:** intended NVA backends are healthy. **Failure means:** health-check firewall, wrong probe port, interface binding, or appliance failure. Verify IP forwarding and interface counters next.

## Firewall receives traffic but destination does not

Check firewall policy/NAT/session table, NVA routing table, IP forwarding, and the VPC's second-stage route after the packet exits the appliance. A common cause is a route loop or the packet matching the same insertion rule again.

## TCP handshake starts but return fails

Trace the destination-to-source path independently. Look for reverse-path bypass, return traffic hashing to a non-state-sharing peer, or an alternate BGP/static route.

## NSI in-band appliance sees nothing

Verify the winning consumer firewall rule, security profile group/custom intercept profile, endpoint/deployment association, producer ILB health, and GENEVE UDP/6081 reachability.

## Cloud NGFW Enterprise L7 inspection fails

Verify active endpoint/association, workload zone, security profile, TLS CA trust where required, VPC MTU compatibility, and endpoint capacity metrics.

## Router Appliance BGP is up but firewall is bypassed

```cli
gcloud compute routers get-status CLOUD_ROUTER_NAME --region=REGION
```

Check whether another direct/static/dynamic route is more preferred, or whether only one direction is being advertised through the NVA.

---

# Recommended decision sequence

1. Need only distributed stateful filtering? **Cloud NGFW policy**.
2. Need Google-managed L7/IPS/URL/TLS? **Cloud NGFW Enterprise firewall endpoints**.
3. Need transparent third-party inspection without route changes? **NSI in-band**.
4. Need selective source/destination/protocol steering? **PBR → internal passthrough NLB → NVA**.
5. Need default/destination-prefix steering? **Static route → internal passthrough NLB → NVA**.
6. Need explicit trust-zone VPC separation and firewall-owned routing/NAT? **Multi-NIC/direct NVA**.
7. Need dynamic hybrid BGP transit through firewall/SD-WAN? **NCC Router Appliance**.
8. Need cloud-delivered SSE integrated with NCC? **NCC Gateway/SSE**.
9. Need passive detection only? **NSI out-of-band / Packet Mirroring / Cloud IDS**.

---

# Sources

- https://docs.cloud.google.com/firewall/docs/about-firewalls
- https://docs.cloud.google.com/firewall/docs/about-firewall-endpoints
- https://docs.cloud.google.com/firewall/docs/manage-firewall-endpoints
- https://docs.cloud.google.com/firewall/docs/about-tls-inspection
- https://docs.cloud.google.com/network-security-integration/docs/nsi-overview
- https://docs.cloud.google.com/network-security-integration/docs/in-band/in-band-integration-tutorial
- https://docs.cloud.google.com/network-security-integration/docs/understand-geneve
- https://docs.cloud.google.com/network-security-integration/docs/out-of-band/out-of-band-integration-overview
- https://docs.cloud.google.com/vpc/docs/policy-based-routes
- https://docs.cloud.google.com/vpc/docs/use-policy-based-routes
- https://docs.cloud.google.com/load-balancing/docs/internal/ilb-next-hop-overview
- https://docs.cloud.google.com/load-balancing/docs/internal/setting-up-ilb-next-hop
- https://docs.cloud.google.com/network-connectivity/docs/network-connectivity-center
- https://docs.cloud.google.com/network-connectivity/docs/network-connectivity-center/concepts/connectivity-topologies
- https://docs.cloud.google.com/network-connectivity/docs/network-connectivity-center/how-to/creating-router-appliances
- https://docs.cloud.google.com/network-connectivity/docs/network-connectivity-center/how-to/connect-site-to-cloud
- https://docs.cloud.google.com/architecture/best-practices-vpc-design
- https://cloud.google.com/blog/products/networking/policy-based-routing-network-patterns-for-virtual-appliances

## Information classification

- **Source information:** documented product behavior, routing constraints, endpoint capacity/MTU, PBR scopes, GENEVE use, NCC/SSE eligibility, and CLI patterns from the sources above.
- **Additional explanation:** packet walks, state/symmetry reasoning, NAT implications, design comparison, and operational guidance.
- **Reasonable inference:** vendor-specific HA/session-state behavior varies and must be validated against the current vendor deployment guide; this guide does not assume cross-node state synchronization unless documented by the vendor.
