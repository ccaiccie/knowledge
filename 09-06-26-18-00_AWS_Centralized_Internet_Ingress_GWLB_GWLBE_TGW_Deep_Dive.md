# AWS Centralized Internet Ingress with GWLB, GWLBE, and Transit Gateway — Deep Dive

> **Scope:** Internet-originated traffic entering a centralized Ingress VPC, traversing a third-party NGFW fleet behind AWS Gateway Load Balancer (GWLB), and then reaching private application VPCs through AWS Transit Gateway (TGW). This guide treats Internet ingress as a separate architecture from east-west inspection because the forward flow begins at an Internet Gateway (IGW)/public load balancer while the backend/return flow reaches the ingress VPC through TGW.
>
> **Source information** = behavior documented by AWS.  
> **Additional explanation** = packet/routing explanation derived from documented AWS behavior.  
> **Reasonable inference** = a design conclusion that follows from documented behavior but is not itself an AWS guarantee.

---

## Reference links

These are the most useful AWS references for this design:

1. [AWS Networking Blog — Design your firewall deployment for Internet ingress traffic flows](https://aws.amazon.com/blogs/networking-and-content-delivery/design-your-firewall-deployment-for-internet-ingress-traffic-flows/)
2. [AWS Networking Blog — Experian: Centralized internet ingress using AWS Gateway Load Balancer and AWS Transit Gateway](https://aws.amazon.com/blogs/networking-and-content-delivery/experian-centralized-internet-ingress-using-aws-gateway-load-balancer-and-aws-transit-gateway/)
3. [AWS Networking Blog — Centralized inspection architecture with AWS Gateway Load Balancer and AWS Transit Gateway](https://aws.amazon.com/blogs/networking-and-content-delivery/centralized-inspection-architecture-with-aws-gateway-load-balancer-and-aws-transit-gateway/)
4. [AWS Networking Blog — Introducing AWS Gateway Load Balancer: Supported architecture patterns](https://aws.amazon.com/blogs/networking-and-content-delivery/introducing-aws-gateway-load-balancer-supported-architecture-patterns/)
5. [AWS Networking Blog — VPC routing enhancements and GWLB deployment patterns](https://aws.amazon.com/blogs/networking-and-content-delivery/vpc-routing-enhancements-and-gwlb-deployment-patterns/)
6. [AWS ELB documentation — Target groups for Application Load Balancers](https://docs.aws.amazon.com/elasticloadbalancing/latest/application/load-balancer-target-groups.html)
7. [AWS ELB documentation — X-Forwarded headers for Application Load Balancers](https://docs.aws.amazon.com/elasticloadbalancing/latest/application/x-forwarded-headers.html)
8. [AWS Transit Gateway documentation — How Transit Gateway works / Appliance Mode](https://docs.aws.amazon.com/vpc/latest/tgw/how-transit-gateways-work.html)

---

# 1. Why Internet ingress must be designed separately from east-west inspection

The centralized east-west pattern normally looks like:

```text
Spoke A
  ↓
TGW
  ↓
Inspection VPC attachment
  ↓
GWLBE → GWLB → NGFW
  ↓
TGW
  ↓
Spoke B
```

Both directions of the inspected flow reach the Inspection VPC from **TGW**. TGW Appliance Mode is designed to preserve the AZ selected for the inspection VPC attachment for the lifetime of the flow.

Centralized Internet ingress is different:

```text
Internet
  ↓
IGW
  ↓
Internet-facing ALB/NLB or ingress proxy
  ↓
GWLBE → GWLB → NGFW
  ↓
TGW
  ↓
Private application VPC
```

The forward application flow originates from a public ingress tier in the Ingress VPC, while return traffic arrives back from the application through TGW. Therefore the return-routing design must deliberately send the packet to the correct zonal GWLBE before it reaches the public ingress tier.

AWS discusses centralized GWLB ingress as a distinct deployment model in [Design your firewall deployment for Internet ingress traffic flows](https://aws.amazon.com/blogs/networking-and-content-delivery/design-your-firewall-deployment-for-internet-ingress-traffic-flows/).

A particularly useful production example is [Experian: Centralized internet ingress using AWS Gateway Load Balancer and AWS Transit Gateway](https://aws.amazon.com/blogs/networking-and-content-delivery/experian-centralized-internet-ingress-using-aws-gateway-load-balancer-and-aws-transit-gateway/). AWS documents public ALBs in centralized ingress VPCs, ALB subnets steering application traffic to same-AZ GWLBE endpoints, and private backend targets reached through TGW.

---

# 2. Recommended architecture — public ALB → GWLBE → GWLB/NGFW → TGW → private backend

![Centralized Internet ingress architecture](images/09-06-26-18-00_centralized_ingress_alb_gwlbe_tgw.svg)

[Editable draw.io source](images/09-06-26-18-00_centralized_ingress_alb_gwlbe_tgw.drawio)

**What this image shows:** An internet-facing ALB terminates the public client connection in a dedicated Ingress VPC. The ALB then opens a backend flow to an IP target in a private application VPC. The ALB subnet route sends that backend flow through the local GWLBE/GWLB/NGFW service chain before TGW delivers it to the target VPC. Return traffic arrives from TGW into a dedicated TGW attachment subnet and is routed back through the same-AZ GWLBE before the ALB receives it.

**What matters:** The NGFW in this placement inspects the **ALB-to-backend** flow. It does not see the original Internet client's source address as the Layer-3 source of that backend TCP connection. ALB preserves client information at Layer 7 with `X-Forwarded-For`; see [ALB X-Forwarded headers](https://docs.aws.amazon.com/elasticloadbalancing/latest/application/x-forwarded-headers.html).

**What to verify:** ALB subnet, GWLBE subnet, and TGW attachment subnet must each use the intended route table. AZ-a traffic should stay on the AZ-a path unless the design deliberately allows otherwise.

## 2.1 Example addressing

### Ingress VPC — `10.254.0.0/16`

| Function | AZ-a | AZ-b |
|---|---|---|
| Public ALB subnet | `10.254.10.0/27` | `10.254.10.32/27` |
| GWLBE subnet | `10.254.100.0/28` | `10.254.100.16/28` |
| TGW attachment subnet | `10.254.200.0/27` | `10.254.200.32/27` |

### App VPC A — `10.10.0.0/16`

- Backend subnet: `10.10.10.0/24`
- Example target: `10.10.10.50:443`

### App VPC B — `10.20.0.0/16`

- Backend subnet: `10.20.10.0/24`

The CIDRs are examples, not AWS requirements.

---

# 3. ALB fundamentally changes the connection model

An Application Load Balancer is a Layer-7 reverse proxy. It terminates the public TCP/TLS connection and creates a separate connection to the selected backend target.

Public side:

```text
198.51.100.25:53000 → ALB-public-address:443
```

Backend side, conceptually:

```text
ALB-node-private-IP:ephemeral → 10.10.10.50:443
```

Therefore:

- The NGFW placed **after** ALB sees the ALB node as the Layer-3 source.
- The backend sees the ALB as the connection source.
- The original client address is normally available in `X-Forwarded-For` for HTTP/HTTPS.
- Host/path rules on the ALB determine which target group receives the request.

AWS documents ALB IP target groups at [Target groups for Application Load Balancers](https://docs.aws.amazon.com/elasticloadbalancing/latest/application/load-balancer-target-groups.html). IP targets are important here because the backend can be located in another VPC reachable over TGW rather than being an instance target in the ALB's own VPC.

### When this is a good fit

Use ALB-first centralized ingress when:

- Applications are HTTP/HTTPS.
- You want TLS termination and optional AWS WAF at ALB.
- Host/path routing is useful for sharing a centralized ingress tier.
- Private backends live in many VPCs.
- Firewall inspection of the ALB-to-backend flow satisfies policy.

### When this may not fit

If the NGFW must see the **true Internet client IP in the inner Layer-3/4 flow**, placing an ALB before the NGFW changes that visibility. Consider a transparent ingress-routing pattern, NLB-based architecture, vendor proxy design, or another supported pattern instead.

---

# 4. Forward packet flow in fine-grained detail

Assume:

```text
Internet client    198.51.100.25
DNS                 app1.example.com
ALB listener        HTTPS/443
Backend             10.10.10.50:443
App VPC             10.10.0.0/16
```

## 4.1 Client → internet-facing ALB

1. Public DNS resolves `app1.example.com` to the internet-facing ALB.
2. Client sends `198.51.100.25:53000 → ALB:443`.
3. The Ingress VPC's Internet Gateway provides public reachability to ALB nodes.
4. ALB terminates the client TCP/TLS session.
5. ALB evaluates listener rules, for example Host=`app1.example.com`.
6. The selected target group contains private IP target `10.10.10.50:443`.
7. ALB chooses a healthy target and creates a new backend connection.

## 4.2 ALB subnet → same-AZ GWLBE

Example AZ-a route table:

```text
RT-Ingress-ALB-a
Destination        Target
10.254.0.0/16      local
10.10.0.0/16       vpce-gwlb-a
10.20.0.0/16       vpce-gwlb-a
0.0.0.0/0          igw-ingress
```

The route:

```text
10.10.0.0/16 → vpce-gwlb-a
```

forces the ALB-generated backend connection into inspection before TGW.

This is the same design principle described in the [Experian centralized ingress case study](https://aws.amazon.com/blogs/networking-and-content-delivery/experian-centralized-internet-ingress-using-aws-gateway-load-balancer-and-aws-transit-gateway/): traffic from ALB subnets is sent to the GWLBE in the same AZ.

## 4.3 GWLBE → GWLB → NGFW

8. `GWLBE-a` invokes the GWLB endpoint service.
9. GWLB selects a healthy firewall target.
10. GWLB encapsulates the backend packet using GENEVE/UDP 6081.
11. The third-party NGFW inspects the inner ALB-to-backend flow.
12. If allowed, the appliance returns the packet to GWLB.
13. GWLB returns the allowed packet through the same endpoint service context to `GWLBE-a`.

GWLB architecture behavior is described in [Introducing AWS Gateway Load Balancer: Supported architecture patterns](https://aws.amazon.com/blogs/networking-and-content-delivery/introducing-aws-gateway-load-balancer-supported-architecture-patterns/).

## 4.4 GWLBE subnet → TGW

Example route table:

```text
RT-Ingress-GWLBE-a
Destination        Target
10.254.0.0/16      local
10.10.0.0/16       tgw-1
10.20.0.0/16       tgw-1
```

The packet now enters the Ingress VPC TGW attachment.

## 4.5 TGW → App VPC

The TGW route table associated with the Ingress VPC attachment should contain the **post-inspection** application routes:

```text
TGW-RT-INGRESS
Destination        Target
10.10.0.0/16       att-App-A
10.20.0.0/16       att-App-B
```

This route table should not send the packet back to an inspection attachment, because inspection has already happened in the Ingress VPC.

14. TGW selects `att-App-A`.
15. Packet enters App VPC A.
16. App VPC local routing reaches `10.10.10.50:443`.
17. The application processes the request.

---

# 5. Return packet flow — the critical symmetry problem

The return flow is the part that makes this architecture different from east-west inspection.

Conceptually:

```text
10.10.10.50:443
  ↓
App VPC route → TGW
  ↓
TGW → Ingress VPC attachment
  ↓
Ingress TGW attachment subnet route
  ↓
same-AZ GWLBE
  ↓
GWLB → NGFW
  ↓
GWLBE
  ↓
ALB node
  ↓
ALB sends response on original public client connection
  ↓
IGW → Internet client
```

## 5.1 Application subnet route

The backend's route table needs a route to the ALB/Ingress VPC address space through TGW. A summary route can be used when appropriate:

```text
RT-App-A
Destination        Target
10.10.0.0/16       local
10.254.0.0/16      tgw-1
```

The application does **not** return directly to the Internet. It returns to the ALB endpoint of its backend connection.

## 5.2 TGW post-backend route

The TGW route table associated with App VPC A needs the Ingress VPC prefix:

```text
TGW-RT-APPS
Destination        Target
10.254.0.0/16      att-Ingress
```

The return packet is delivered to the Ingress VPC TGW attachment.

## 5.3 Ingress VPC TGW attachment-subnet route table

This is the key return enforcement point.

Example AZ-a:

```text
RT-Ingress-TGW-a
Destination        Target
10.254.10.0/27     vpce-gwlb-a
10.254.0.0/16      local
```

Because `10.254.10.0/27` is more specific than the VPC's `10.254.0.0/16 local` route, the return packet destined for the ALB subnet is sent through `GWLBE-a` instead of directly to the ALB.

That is analogous to the VPC routing-enhancement technique documented in [VPC routing enhancements and GWLB deployment patterns](https://aws.amazon.com/blogs/networking-and-content-delivery/vpc-routing-enhancements-and-gwlb-deployment-patterns/).

## 5.4 GWLBE return to ALB

After the reverse flow is inspected and returned by GWLBE, the GWLBE subnet route uses the Ingress VPC local route to reach the ALB subnet:

```text
RT-Ingress-GWLBE-a
Destination        Target
10.254.0.0/16      local
10.10.0.0/16       tgw-1
10.20.0.0/16       tgw-1
```

ALB receives the backend response and maps it to the original client-side connection.

The final Internet response is then sent by ALB through IGW to `198.51.100.25`.

---

# 6. Appliance Mode — why the answer is not simply “enable it”

For centralized east-west service insertion, TGW Appliance Mode is a major symmetry mechanism. See [AWS Transit Gateway — Appliance Mode](https://docs.aws.amazon.com/vpc/latest/tgw/how-transit-gateways-work.html).

For the centralized **Ingress VPC** pattern, however, do not blindly copy the east-west setting.

The [Experian AWS reference](https://aws.amazon.com/blogs/networking-and-content-delivery/experian-centralized-internet-ingress-using-aws-gateway-load-balancer-and-aws-transit-gateway/) explains that their Ingress VPC TGW attachment has Appliance Mode disabled and uses subnet route tables to direct returning traffic through the appropriate GWLBE. AWS specifically distinguishes Appliance Mode's east-west purpose from ingress/egress VPC behavior.

The design principle is therefore:

```text
East-west Inspection VPC:
TGW attachment Appliance Mode is normally required for stateful AZ symmetry.

Centralized Ingress VPC:
Do not assume Appliance Mode is the symmetry solution.
Engineer the return route at the TGW attachment subnet so the response traverses the required GWLBE before reaching the public ingress tier.
```

Always validate the exact vendor design, because firewall session handling, GWLB cross-zone behavior, and multi-AZ routing choices affect the outcome.

---

# 7. Why the same-AZ GWLBE matters

Suppose the ALB backend connection was created from an ALB node in AZ-a and sent through `GWLBE-a`.

Forward:

```text
ALB node AZ-a
  → RT-Ingress-ALB-a
  → GWLBE-a
  → GWLB/NGFW state
  → TGW
  → App A
```

The clean return path is:

```text
App A
  → TGW
  → Ingress TGW attachment AZ-a
  → RT-Ingress-TGW-a
  → GWLBE-a
  → GWLB/NGFW reverse state
  → ALB node AZ-a
```

If the return path enters another AZ and invokes `GWLBE-b`, a stateful firewall may see a different service-chain context depending on GWLB/vendor behavior. Build and test explicit AZ-locality rather than assuming AWS will reconstruct application state across arbitrary AZ changes.

---

# 8. Where an NLB fits

A centralized NLB can be used instead of ALB when Layer-4 behavior is required. However, client-IP preservation, target type, protocol, cross-zone behavior, and whether the target is reached across TGW materially change the packet model.

Do not simply replace “ALB” with “NLB” in the diagrams without checking:

- `ip` versus `instance` targets.
- `preserve_client_ip.enabled` behavior.
- Proxy Protocol v2 if client metadata is required.
- Cross-zone load balancing.
- Whether the backend is reachable from the NLB node through TGW.
- Firewall policy expectations for source addresses.

AWS's high-level centralized ingress design article discusses ALB/NLB options here: [Design your firewall deployment for Internet ingress traffic flows](https://aws.amazon.com/blogs/networking-and-content-delivery/design-your-firewall-deployment-for-internet-ingress-traffic-flows/).

---

# 9. Transparent ingress routing in the application VPC is a different architecture

Another documented GWLB ingress approach is to keep the internet-facing load balancer in the **application VPC** and use an IGW edge-associated route table to steer inbound traffic to a local GWLBE.

Conceptually:

```text
Internet
  ↓
IGW ingress route table
  ↓ destination subnet CIDR → GWLBE
GWLBE → central GWLB/NGFW
  ↓
public ALB/NLB/workload subnet
```

This is the **distributed ingress** pattern, not the centralized Ingress-VPC + TGW pattern.

AWS explains this transparent GWLB model in [Design your firewall deployment for Internet ingress traffic flows](https://aws.amazon.com/blogs/networking-and-content-delivery/design-your-firewall-deployment-for-internet-ingress-traffic-flows/).

In that transparent pattern, the GWLBE can inspect the original client-side 5-tuple before the public load balancer. In the centralized ALB-first pattern, the NGFW after ALB sees the ALB-created backend connection instead.

That difference is fundamental when selecting an architecture.

---

# 10. ELB/firewall sandwich — another separate architecture

An ELB/firewall sandwich inserts firewall appliances as an explicit routed or proxy tier between public and private load-balancing layers.

Conceptually:

```text
Internet
  ↓
Public NLB/ALB
  ↓
Firewall appliance tier
  ↓
Private ALB/NLB/backend
```

Some firewall products support forwarding to DNS names or operate as explicit proxies, allowing the firewall to terminate or re-originate connections toward private application load balancers.

This is different from GWLB transparent insertion because:

- The appliance may participate directly in Layer-3/Layer-4 or proxy routing.
- NAT may occur on the firewall.
- Client/source preservation behavior is vendor-specific.
- HA and scale are handled differently from GWLB.

AWS includes an ELB sandwich centralized ingress alternative in [Design your firewall deployment for Internet ingress traffic flows](https://aws.amazon.com/blogs/networking-and-content-delivery/design-your-firewall-deployment-for-internet-ingress-traffic-flows/).

---

# 11. Route-table summary for the centralized ALB ingress model

## Ingress VPC — ALB subnet AZ-a

```text
10.254.0.0/16  → local
10.10.0.0/16   → vpce-gwlb-a
10.20.0.0/16   → vpce-gwlb-a
0.0.0.0/0      → igw-ingress
```

## Ingress VPC — GWLBE subnet AZ-a

```text
10.254.0.0/16  → local
10.10.0.0/16   → tgw-1
10.20.0.0/16   → tgw-1
```

## TGW route table associated with Ingress VPC

```text
10.10.0.0/16   → att-App-A
10.20.0.0/16   → att-App-B
```

## App VPC A subnet

```text
10.10.0.0/16   → local
10.254.0.0/16  → tgw-1
```

## TGW route table associated with App VPCs

```text
10.254.0.0/16  → att-Ingress
```

## Ingress VPC — TGW attachment subnet AZ-a

```text
10.254.0.0/16  → local
10.254.10.0/27 → vpce-gwlb-a   # more-specific return enforcement
```

The `10.254.10.0/27 → GWLBE-a` route is the critical return-side steering route.

---

# 12. Verification

## 12.1 Verify ALB target group uses intended private IPs

```cli
aws elbv2 describe-target-health \
  --target-group-arn <target-group-arn> \
  --output table
```

**Expected:** IP targets in the private application CIDRs are healthy.

**Failure:** Target is unhealthy/unreachable.

**Next action:** Verify TGW routes, application security groups/NACLs, target listener, and health-check path.

## 12.2 Verify ALB subnet routes

```cli
aws ec2 describe-route-tables \
  --route-table-ids <rtb-ingress-alb-a> \
  --output json
```

**Expected:** each private application CIDR points to the same-AZ GWLBE.

**Failure:** Application CIDR points directly to TGW or uses local/default routing.

**Consequence:** Backend traffic can bypass the NGFW.

## 12.3 Verify GWLBE subnet routes

```cli
aws ec2 describe-route-tables \
  --route-table-ids <rtb-ingress-gwlbe-a> \
  --output json
```

**Expected:** App VPC CIDRs point to TGW and Ingress VPC CIDR remains local.

## 12.4 Verify TGW return route

```cli
aws ec2 search-transit-gateway-routes \
  --transit-gateway-route-table-id <tgw-rtb-apps> \
  --filters Name=route-search.exact-match,Values=10.254.0.0/16 \
  --output json
```

**Expected:** destination `10.254.0.0/16` points to `att-Ingress`.

## 12.5 Verify TGW attachment-subnet return enforcement

```cli
aws ec2 describe-route-tables \
  --route-table-ids <rtb-ingress-tgw-a> \
  --output json
```

**Expected:** public ALB subnet `10.254.10.0/27` points to `vpce-gwlb-a`.

If only the broad VPC `local` route exists, return backend traffic can reach the ALB without traversing the firewall.

## 12.6 Verify GWLBE and GWLB targets

```cli
aws ec2 describe-vpc-endpoints \
  --vpc-endpoint-ids <vpce-gwlb-a> \
  --output json
```

```cli
aws elbv2 describe-target-health \
  --target-group-arn <gwlb-target-group-arn> \
  --output table
```

**Expected:** GWLBE is `available` and the intended firewall targets are healthy.

---

# 13. Troubleshooting by symptom

## Symptom: ALB receives the client connection but backend target is never reached

**Where:** ALB subnet route table.  
**What to test:** Application CIDR → same-AZ GWLBE.  
**Expected:** `10.10.0.0/16 → vpce-gwlb-a`.  
**Failure means:** Traffic may bypass inspection or have no route to the target.  
**Next action:** Verify GWLBE state and GWLBE subnet → TGW route.

## Symptom: Firewall sees the backend SYN but not SYN/ACK

**Where:** TGW return routing and Ingress TGW attachment subnet.  
**Expected:** App VPC → TGW → `att-Ingress`, then ALB subnet CIDR → same GWLBE.  
**Failure means:** Return traffic is bypassing or entering the wrong service chain.  
**Next action:** Verify TGW route-table association and the more-specific ALB-subnet route on the TGW attachment subnet.

## Symptom: Firewall logs show ALB addresses instead of Internet client addresses

**Meaning:** Expected for ALB-first insertion. ALB terminates the client connection and opens a backend connection.  
**Next action:** Use `X-Forwarded-For`/application logging or select a transparent pre-ALB inspection architecture if the NGFW must see original L3/L4 client identity.

## Symptom: Return traffic reaches ALB without hitting firewall

**Where:** Ingress VPC TGW attachment subnet route table.  
**Expected:** ALB subnet prefix → GWLBE.  
**Failure means:** VPC `local` routing wins because no more-specific route exists.  
**Next action:** Add the intended more-specific return route.

## Symptom: Works in one AZ but fails in another

**Where:** Per-AZ ALB/GWLBE/TGW attachment route associations.  
**Expected:** AZ-a uses GWLBE-a; AZ-b uses GWLBE-b, with equivalent route tables.  
**Failure means:** Cross-AZ return steering or missing endpoint/route is likely.  
**Next action:** Compare subnet associations and endpoint availability AZ by AZ.

---

# 14. Architecture selection matrix

| Requirement | Best-fit starting pattern |
|---|---|
| HTTP/HTTPS, centralized host/path routing, private multi-VPC backends | Centralized public ALB → GWLBE → TGW |
| Firewall must see original Internet client L3/L4 tuple before ELB | Distributed IGW ingress routing → GWLBE → public ELB |
| Layer-4 centralized ingress | NLB-based centralized ingress, validate client-IP and target behavior carefully |
| Firewall must act as explicit proxy/NAT tier | Vendor-supported ELB/firewall sandwich |
| East-west VPC inspection | TGW → centralized Inspection VPC with Appliance Mode |
| Internet egress | Centralized egress VPC / Inspection VPC with NAT after inspection |

---

# 15. Common mistakes

1. **Treating Internet ingress as east-west with an IGW bolted on.** The forwarding origins and symmetry mechanisms differ.
2. **Assuming Appliance Mode alone solves ingress symmetry.** The return-side VPC subnet route is a core part of centralized ingress.
3. **Forgetting that ALB creates a new backend connection.** The firewall after ALB sees ALB source IP, not the Internet client's L3 source.
4. **Sending ALB backend traffic directly to TGW.** That bypasses GWLB inspection.
5. **Letting TGW-return traffic use only the VPC local route to the ALB subnet.** That bypasses inspection on the reverse direction.
6. **Mixing AZs without understanding session implications.** Keep ALB/GWLBE/TGW return routing AZ-aware.
7. **Using NLB assumptions for ALB or vice versa.** Client-IP preservation and proxy behavior are different.
8. **Assuming a centralized ingress pattern preserves the original 5-tuple through ALB.** It does not; use transparent pre-ELB insertion if that is required.

---

# Sources

- [AWS Networking Blog — Design your firewall deployment for Internet ingress traffic flows](https://aws.amazon.com/blogs/networking-and-content-delivery/design-your-firewall-deployment-for-internet-ingress-traffic-flows/)
- [AWS Networking Blog — Experian: Centralized internet ingress using AWS Gateway Load Balancer and AWS Transit Gateway](https://aws.amazon.com/blogs/networking-and-content-delivery/experian-centralized-internet-ingress-using-aws-gateway-load-balancer-and-aws-transit-gateway/)
- [AWS Networking Blog — Centralized inspection architecture with AWS Gateway Load Balancer and AWS Transit Gateway](https://aws.amazon.com/blogs/networking-and-content-delivery/centralized-inspection-architecture-with-aws-gateway-load-balancer-and-aws-transit-gateway/)
- [AWS Networking Blog — Introducing AWS Gateway Load Balancer: Supported architecture patterns](https://aws.amazon.com/blogs/networking-and-content-delivery/introducing-aws-gateway-load-balancer-supported-architecture-patterns/)
- [AWS Networking Blog — VPC routing enhancements and GWLB deployment patterns](https://aws.amazon.com/blogs/networking-and-content-delivery/vpc-routing-enhancements-and-gwlb-deployment-patterns/)
- [AWS ELB documentation — Target groups for Application Load Balancers](https://docs.aws.amazon.com/elasticloadbalancing/latest/application/load-balancer-target-groups.html)
- [AWS ELB documentation — X-Forwarded headers for Application Load Balancers](https://docs.aws.amazon.com/elasticloadbalancing/latest/application/x-forwarded-headers.html)
- [AWS Transit Gateway documentation — How Transit Gateway works / Appliance Mode](https://docs.aws.amazon.com/vpc/latest/tgw/how-transit-gateways-work.html)
