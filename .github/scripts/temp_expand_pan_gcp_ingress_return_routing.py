from pathlib import Path

p = Path('09-07-26-07-03_Palo_Alto_Networks_Firewalling_in_GCP_Deep_Dive.md')
s = p.read_text()

old_toc = "    - [7.8.9 Can the same VM-Series fleet handle NSI and Internet ingress?](#789-can-the-same-vm-series-fleet-handle-nsi-and-internet-ingress)\n"
new_toc = old_toc + "    - [7.8.10 Ingress NAT and return routing — DNAT is required, SNAT is optional](#7810-ingress-nat-and-return-routing--dnat-is-required-snat-is-optional)\n"
if old_toc not in s:
    raise SystemExit('TOC anchor not found')
s = s.replace(old_toc, new_toc, 1)

marker = "**Reasonable inference:** Unless Palo Alto explicitly validates a combined NSI + Internet-ingress topology using a backend model that targets distinct dataplane NICs, use separate VM-Series fleets rather than assuming that a second ILB and a second NIC are sufficient.\n\n## 7.9 On-premises inspection through Cloud Interconnect"
insert = r'''**Reasonable inference:** Unless Palo Alto explicitly validates a combined NSI + Internet-ingress topology using a backend model that targets distinct dataplane NICs, use separate VM-Series fleets rather than assuming that a second ILB and a second NIC are sufficient.

### 7.8.10 Ingress NAT and return routing — DNAT is required, SNAT is optional

For the traditional Internet-ingress design, **PAN-OS does not need to source-NAT the inbound client merely to make the connection work**. The normal design is:

```text
Internet client
203.0.113.50:51514
        |
        v
External passthrough NLB
public VIP 34.172.143.223:443
        |
        v
VM-Series nic0 / Untrust
        |
        | PAN-OS DNAT
        | 34.172.143.223 -> 10.50.1.10
        v
VM-Series Trust
        |
        v
Application VPC
server 10.50.1.10:443
```

The external passthrough NLB preserves the original packet tuple when delivering it to the firewall backend. PAN-OS can therefore preserve the real Internet client source address and translate only the destination:

```text
Before PAN-OS DNAT:
203.0.113.50:51514 -> 34.172.143.223:443

After PAN-OS DNAT:
203.0.113.50:51514 -> 10.50.1.10:443
```

The application sees the real client IP:

```text
source      203.0.113.50
destination 10.50.1.10
```

That is desirable for application logging, PAN-OS policy visibility, and incident investigation.

#### Why SNAT is not mandatory

The return path can be made symmetric with **routing**, rather than by hiding the client behind the firewall's trust address.

Assume:

```text
Trust VPC:                 10.0.0.0/16
Trust-side ILB VIP:        10.0.1.100
Application VPC:           10.50.0.0/16
Application server:        10.50.1.10
Internet client:           203.0.113.50
Public forwarding-rule IP: 34.172.143.223
```

The application returns:

```text
10.50.1.10:443 -> 203.0.113.50:51514
```

Its VPC routing must steer that Internet-bound response back to the **trust-side internal passthrough NLB**, which selects the active VM-Series trust dataplane:

```text
Application VPC
0.0.0.0/0
    |
    v
Trust internal passthrough NLB
10.0.1.100
    |
    v
VM-Series Trust
    |
    | existing PAN-OS session
    | reverse DNAT
    v
VM-Series Untrust
    |
    v
Internet client
```

Palo Alto documents the trust interface as the backend of an internal passthrough Network Load Balancer and states that workload VPC routes should direct VPC-to-Internet traffic to that internal load balancer for inspection.

The important point is:

```text
DNAT publishes the private server.
Routing preserves the stateful return path.
SNAT is not inherently required for ingress symmetry.
```

#### Do not point the workload default route directly at one firewall NIC IP in the HA design

In an HA/load-balanced architecture, the workload VPC should normally steer traffic to the **trust-side internal passthrough NLB**, not directly to a specific firewall trust NIC address.

Preferred mental model:

```text
0.0.0.0/0
   -> trust ILB
   -> healthy/active VM-Series trust interface
```

rather than:

```text
0.0.0.0/0
   -> 10.0.1.10  # one specific firewall NIC
```

Using the ILB preserves the health-aware service abstraction and avoids hard-coding one appliance address as the return next hop.

Depending on the workload topology, the steering object can be a supported custom static route, an imported custom route in a VPC-peering hub/spoke design, or another Palo Alto-supported routing construct. The key requirement is that **the workload's Internet response must return to the VM-Series trust-side service before reaching the Internet**.

#### Full bidirectional packet walk without inbound SNAT

Forward direction:

```text
1. Client sends:
   203.0.113.50:51514 -> 34.172.143.223:443

2. External passthrough NLB selects active VM-Series untrust backend.

3. PAN-OS DNAT changes destination only:
   203.0.113.50:51514 -> 10.50.1.10:443

4. PAN-OS routes out Trust.

5. Google VPC routing delivers the packet to 10.50.1.10.
```

Return direction:

```text
1. Server replies:
   10.50.1.10:443 -> 203.0.113.50:51514

2. Application VPC 0.0.0.0/0 steering sends the response to the trust ILB.

3. The trust ILB selects the active/stateful VM-Series path.

4. PAN-OS finds the established session and reverses DNAT:
   34.172.143.223:443 -> 203.0.113.50:51514

5. PAN-OS forwards through Untrust.

6. Google sends the response toward the Internet client using the passthrough-LB/connection-tracking dataplane behavior.
```

Do not think of the external passthrough NLB as a reverse proxy on the return leg. Google documents passthrough NLBs as **direct server return (DSR)**: backend responses go directly toward the client, while the load balancer's connection-tracking and special routes handle the service semantics.

#### When would inbound SNAT be useful?

Inbound SNAT can be an intentional design choice when you **cannot guarantee the application's return route through VM-Series** or when you deliberately want the application to see the firewall as the source.

Example:

```text
Original Internet flow:
203.0.113.50 -> 34.172.143.223

PAN-OS DNAT + SNAT:
10.0.1.10 -> 10.50.1.10
```

Now the application naturally sends the reply to `10.0.1.10`, so symmetry is easier to force. The tradeoff is that the application no longer sees the original Internet client IP at Layer 3.

Use that only when the operational tradeoff is acceptable. For the documented Palo Alto ingress architecture, preserving the real client source IP is an explicit benefit of the active/passive model.

#### Separate public-services VPC design

A clean design is to keep Internet-facing applications in a dedicated workload VPC while the firewalls live in a security/trust hub VPC:

```text
                     SECURITY / TRUST VPC

Internet
   |
   v
External passthrough NLB
   |
   v
VM-Series nic0 / Untrust
   |
   | DNAT + Security inspection
   v
VM-Series Trust
   |
   +------------------------------+
                                  |
                                  v
                         APPLICATION VPC
                         10.50.0.0/16
                                  |
                                  v
                         Web 10.50.1.10
```

Return path:

```text
10.50.1.10
   |
   | 0.0.0.0/0 toward firewall service
   v
Trust internal passthrough NLB
   |
   v
VM-Series Trust
   |
   | existing session + reverse DNAT
   v
VM-Series Untrust
   |
   v
Internet client
```

For hub/spoke VPC peering, remember that the workload VPC cannot blindly reference an arbitrary ILB in another VPC. Use the supported custom-route export/import pattern described in Section 7.6, or another Palo Alto-supported workload-to-hub routing model. Route visibility and ILB next-hop usability are separate things to verify.

#### What to verify

**Google Cloud:**

```cli
gcloud compute forwarding-rules describe panw-vmseries-extlb-rule2 \
  --region=us-central1 \
  --format='yaml(name,IPAddress,IPProtocol,backendService,loadBalancingScheme)'

gcloud compute routes list \
  --filter='network:APPLICATION_VPC_NAME' \
  --format='table(name,destRange,priority,nextHopIlb,nextHopGateway,nextHopPeering)'
```

Verify that:

- the public forwarding rule reaches the external VM-Series backend service;
- the workload/application VPC has an effective Internet return route toward the trust-side firewall service;
- no more-specific route bypasses the firewall for the Internet client destination;
- the trust-side internal passthrough NLB is healthy and usable from the workload VPC topology.

**PAN-OS:**

```cli
show session all filter destination 10.50.1.10
show routing route
show counter global filter severity drop delta yes
```

Verify that:

- the forward session shows the original client IP;
- DNAT maps the public forwarding-rule IP to the private application;
- the return packet matches the existing session;
- reverse NAT restores the public service IP;
- no unintended source NAT rule hides the Internet client unless that behavior is deliberate.

**Source information:** Palo Alto documents external load-balanced Internet ingress to `nic0`/Untrust, preserving original client IP in the active/passive model, trust-side internal passthrough NLB use for workload VPC egress, and workload routes steering VPC-to-Internet traffic to that ILB. Google documents passthrough Network Load Balancers as preserving the original source/destination tuple and using direct-server-return behavior for backend responses.

**Additional explanation:** Inbound DNAT and workload-side return routing solve different problems. DNAT publishes the application; the trust-side route guarantees that the response returns through the stateful PAN-OS session owner.

**Reasonable inference:** When return steering is correct, inbound SNAT is an optional design choice rather than a requirement. Using routing for symmetry preserves the original client IP end to end through the firewall and into the application.

## 7.9 On-premises inspection through Cloud Interconnect'''

if marker not in s:
    raise SystemExit('Insertion marker not found')
s = s.replace(marker, insert, 1)
p.write_text(s)
