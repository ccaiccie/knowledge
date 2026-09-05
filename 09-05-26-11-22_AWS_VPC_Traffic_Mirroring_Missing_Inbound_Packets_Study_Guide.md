# AWS VPC Traffic Mirroring: Why an Inbound Packet Can Be Missing from the Analyzer

## Exam scenario

> **Question:** An analyzer reports no inbound packet that the workload says it received. Which source-side fact can explain the absence?
>
> - All inbound traffic is mirrored before any VPC policy.
> - The NLB always converts VXLAN to TCP.
> - A Traffic Mirror session decrypts TLS automatically.
> - **Inbound traffic dropped by the source security group or network ACL is not mirrored.**

**Best answer:** **Inbound traffic dropped by the source Security Group (SG) or Network Access Control List (NACL) is not mirrored.**

This comes directly from AWS VPC Traffic Mirroring behavior: inbound traffic dropped at the mirror source because of **inbound security-group rules** or **inbound network-ACL rules** is not copied to the mirror target.

> **Important nuance:** If the workload truly received the **exact same packet**, then its inbound SG/NACL did not drop that exact packet. In a real troubleshooting case, investigate the Traffic Mirror filter, source ENI, session, target path, VXLAN handling, packet truncation, congestion, and whether the workload and analyzer are referring to the same flow and time window.

---

## Supplied and supporting URLs

- AWS — Traffic Mirror targets and source-side routing/security behavior: https://docs.aws.amazon.com/vpc/latest/mirroring/traffic-mirroring-targets.html
- AWS — How Traffic Mirroring works: https://docs.aws.amazon.com/vpc/latest/mirroring/traffic-mirroring-how-it-works.html
- AWS — Traffic Mirror filters: https://docs.aws.amazon.com/vpc/latest/mirroring/traffic-mirroring-filters.html
- AWS — Traffic Mirror packet format: https://docs.aws.amazon.com/vpc/latest/mirroring/traffic-mirroring-packet-formats.html
- AWS — Traffic Mirror source/target connectivity: https://docs.aws.amazon.com/vpc/latest/mirroring/traffic-mirroring-connection.html
- AWS — Traffic Mirroring limitations: https://docs.aws.amazon.com/vpc/latest/mirroring/traffic-mirroring-network-limitations.html
- AWS — Getting started: https://docs.aws.amazon.com/vpc/latest/mirroring/traffic-mirroring-getting-started.html
- AWS CLI v2 — `create-traffic-mirror-filter`: https://docs.aws.amazon.com/cli/latest/reference/ec2/create-traffic-mirror-filter.html
- AWS CLI v2 — `create-traffic-mirror-filter-rule`: https://docs.aws.amazon.com/cli/latest/reference/ec2/create-traffic-mirror-filter-rule.html
- AWS CLI v2 — `create-traffic-mirror-session`: https://docs.aws.amazon.com/cli/latest/reference/ec2/create-traffic-mirror-session.html

---

## 1. The key idea

**Source information:** AWS states that **inbound traffic dropped at the Traffic Mirror source because of inbound security-group rules or inbound network-ACL rules is not mirrored**. AWS also states that mirrored outbound traffic is not subject to the outbound security-group rules of the Traffic Mirror source.

**Additional explanation:** Traffic Mirroring is not an omniscient packet tap that sees every packet before all VPC policy. It copies traffic from an eligible source network interface, subject to documented source-side behavior and the Traffic Mirror filter/session configuration.

**Reasonable inference:** If a packet is rejected before it becomes eligible for mirroring at the source ENI, the analyzer cannot receive a copy of that packet from that mirror session.

---

## 2. Packet path and capture point

![AWS VPC Traffic Mirroring ingress capture path](images/09-05-26-11-22_aws_vpc_traffic_mirroring_ingress_capture_path.svg)

[Open the editable draw.io diagram](images/09-05-26-11-22_aws_vpc_traffic_mirroring_ingress_capture_path.drawio)

**What this image shows:** An inbound packet encounters source-side VPC policy before the successful traffic path reaches the workload ENI. An allowed packet can be copied by the Traffic Mirror session and encapsulated toward the mirror target. A packet rejected by the source inbound SG/NACL is not mirrored.

**What matters:** The analyzer is not guaranteed to see traffic that VPC policy rejected at the source. Mirrored traffic travels separately to the mirror target and has its own routing, security, bandwidth, and decapsulation requirements.

**What to verify:** Confirm the exact source ENI, inbound SG and NACL decision, mirror-session state, filter rules, path to the target, and that the analyzer can process VXLAN on UDP 4789.

---

## 3. What VPC Traffic Mirroring actually does

A Traffic Mirror session ties together three things:

1. **Source** — an eligible Elastic Network Interface (ENI) whose traffic is being observed.
2. **Filter** — rules that decide which ingress and/or egress packets are copied.
3. **Target** — where the copies are sent, such as a monitoring ENI, a Network Load Balancer (NLB), or a Gateway Load Balancer endpoint (GWLBe).

For traffic that matches an accepted Traffic Mirror rule, AWS encapsulates the mirrored packet with **Virtual Extensible LAN (VXLAN)** and sends it toward the target.

### VXLAN transport

The analyzer does **not** simply receive the original frame as an ordinary unencapsulated TCP flow.

AWS documents that mirrored traffic is encapsulated in VXLAN. The Traffic Mirror target path must therefore support the mirrored encapsulation, and a target security group must allow **UDP port 4789** from the mirror source when applicable.

This makes the distractor “The NLB always converts VXLAN to TCP” incorrect. Traffic Mirroring uses VXLAN encapsulation; an NLB is not described by AWS as automatically converting mirrored VXLAN traffic into ordinary TCP.

---

## 4. Why the source SG/NACL answer is correct

Consider a client sending TCP/443 to an EC2 workload.

### Case A — packet is allowed

```text
Client
  |
  v
Inbound VPC policy allows packet
  |
  v
Workload ENI
  | \
  |  \-- mirrored copy --> VXLAN/UDP 4789 --> analyzer
  |
  v
Workload/application
```

The original packet can reach the workload and, if the Traffic Mirror filter accepts it, a copy can be sent to the target.

### Case B — source inbound policy drops packet

```text
Client
  |
  v
Inbound SG or NACL
  |
  +---- DROP
```

AWS explicitly documents that inbound traffic dropped at the Traffic Mirror source because of the source's **inbound SG** or **inbound NACL** is **not mirrored**. There is therefore no mirror copy for the analyzer to receive.

---

## 5. Security Group versus Network ACL

| Property | Security Group | Network ACL |
|---|---|---|
| Scope | ENI/resource association | Subnet |
| State model | Stateful | Stateless |
| Rule model | Allow rules | Allow and deny rules |
| Relevant here | Inbound SG can prevent traffic from being mirrored when it drops inbound traffic at the source | Inbound NACL can prevent traffic from being mirrored when it drops inbound traffic at the source |

The exam point is not asking whether the SG or NACL made the decision. It is testing whether you know that **source-side inbound policy can prevent a packet from appearing in the mirrored feed**.

---

## 6. The tricky wording: “the workload says it received it”

If the workload really received **that exact packet**, the same packet cannot simultaneously have been dropped by the workload's own inbound SG or inbound NACL.

### Exam interpretation

The documented source-side fact that explains why an inbound packet can be absent from Traffic Mirroring is:

> **Inbound traffic dropped by the source security group or NACL is not mirrored.**

### Real-world interpretation

If the application claims it received the exact packet, validate that both observations refer to the same traffic:

- Same source and destination IP addresses
- Same source and destination ports
- Same protocol
- Same timestamp/time zone
- Same ENI
- Same connection attempt
- Same Availability Zone/path
- Same direction
- Same packet, not merely the same application transaction

A load balancer, proxy, NAT function, retry, or multiple backend interfaces can make two observations look like the same packet when they are not.

---

## 7. Traffic Mirror filters can also make packets disappear

A Traffic Mirror filter is separate from an SG or NACL.

**Source information:** AWS evaluates Traffic Mirror filter rules in ascending rule-number order, and the first matching rule determines whether the traffic is mirrored. If you create a filter without rules, no traffic is mirrored.

Example:

```text
Rule 10: reject TCP/22
Rule 20: accept all other IPv4 TCP
```

SSH packets match rule 10 and are not copied, even if the workload itself is allowed to receive them.

Ingress and egress are also distinct directions. If you configure only ingress rules, that does not automatically mirror egress traffic.

---

## 8. TLS is not automatically decrypted

The distractor “A Traffic Mirror session decrypts TLS automatically” is false.

Traffic Mirroring copies packet data; it does not automatically terminate or decrypt Transport Layer Security (TLS). If the original payload is encrypted, the mirrored copy remains encrypted unless a separate security product performs decryption under an appropriate architecture and policy.

So if the analyzer sees a TCP/443 flow but cannot read HTTP contents, that is not evidence that mirroring failed.

---

## 9. Mirror-target requirements

A mirror target can be:

- A network interface
- A Network Load Balancer
- A Gateway Load Balancer endpoint

AWS recommends an NLB or GWLBe when high availability is required.

Verify:

- The mirrored path is routable.
- Security controls on the target path allow the mirrored traffic.
- UDP/4789 is allowed where required.
- The monitoring appliance understands VXLAN.
- The appliance has sufficient throughput and packets-per-second capacity.
- The analyzer is looking at the correct interface and VXLAN-decapsulated traffic.

---

## 10. CLI configuration example

The following is a **configuration pattern** using placeholders. Replace every placeholder with an actual resource identifier or value from your environment.

### Step 1 — create a Traffic Mirror filter

Run from a host with AWS CLI v2 credentials authorized for EC2 Traffic Mirroring APIs.

```cli
aws ec2 create-traffic-mirror-filter \
  --description "Inbound TCP mirror filter"
```

Record the returned `<TRAFFIC_MIRROR_FILTER_ID>`.

### Step 2 — add an ingress accept rule

```cli
aws ec2 create-traffic-mirror-filter-rule \
  --traffic-mirror-filter-id <TRAFFIC_MIRROR_FILTER_ID> \
  --traffic-direction ingress \
  --rule-number 100 \
  --rule-action accept \
  --protocol 6 \
  --source-cidr-block 0.0.0.0/0 \
  --destination-cidr-block 0.0.0.0/0 \
  --description "Mirror inbound IPv4 TCP"
```

Placeholders:

- `<TRAFFIC_MIRROR_FILTER_ID>` — ID beginning with `tmf-`
- Protocol `6` — TCP

### Step 3 — create the Traffic Mirror session

```cli
aws ec2 create-traffic-mirror-session \
  --network-interface-id <SOURCE_ENI_ID> \
  --traffic-mirror-target-id <TRAFFIC_MIRROR_TARGET_ID> \
  --traffic-mirror-filter-id <TRAFFIC_MIRROR_FILTER_ID> \
  --session-number 1 \
  --description "Inbound workload inspection"
```

Placeholders:

- `<SOURCE_ENI_ID>` — ENI being mirrored
- `<TRAFFIC_MIRROR_TARGET_ID>` — target ID beginning with `tmt-`
- `<TRAFFIC_MIRROR_FILTER_ID>` — filter ID beginning with `tmf-`

**Expected behavior:** Only traffic matching accepted filter rules is copied. Source-side inbound traffic that AWS drops because of the source inbound SG or inbound NACL is not mirrored.

---

## 11. Verification workflow

### Check 1 — confirm the source ENI

```cli
aws ec2 describe-traffic-mirror-sessions
```

Verify that the session references the ENI attached to the workload you are troubleshooting.

**Success:** The expected source ENI, filter, and target are present.

**Failure means:** You may be mirroring a different interface or stale session.

**Next action:** Correct the session's source or create the session on the right ENI.

### Check 2 — inspect filter rules

```cli
aws ec2 describe-traffic-mirror-filters
```

Verify direction, rule order, action, protocol, CIDRs, and port ranges.

**Success:** The missing flow matches an `accept` rule before any matching `reject` rule.

**Failure means:** The mirror filter itself is excluding the traffic.

### Check 3 — inspect source SGs and NACLs

For the source ENI and subnet, verify the inbound path is permitted. If VPC Flow Logs are enabled, correlate the flow by timestamp and 5-tuple. Flow Logs can help distinguish accepted versus rejected IP traffic and complement packet mirroring.

### Check 4 — validate target transport

```text
UDP destination port: 4789
Encapsulation: VXLAN
```

Ensure the analyzer is decoding or decapsulating the mirror stream rather than expecting raw TCP/UDP payloads.

---

## 12. Other documented reasons mirrored packets may be absent

AWS documents Traffic Mirroring limitations where mirrored traffic can be dropped when instance bandwidth or packet-per-second limits are exceeded. Production traffic receives priority during congestion.

Other practical checks include:

- Traffic Mirror filter excludes the flow.
- Wrong ENI is configured as the source.
- Wrong traffic direction is configured.
- The mirror target is unreachable.
- Target security policy blocks UDP/4789.
- Analyzer cannot parse VXLAN.
- Packet-length configuration truncates mirrored packets.
- Bandwidth/PPS limits cause mirrored packets to be dropped.
- Analyzer and workload timestamps are not synchronized.
- Multiple ENIs or load-balanced backends cause correlation with the wrong path.

---

## 13. Troubleshooting by symptom

### Symptom: workload receives traffic but analyzer sees nothing

**Where to check:** Traffic Mirror session, filter, source ENI, target path.

**What it tests:** Whether the specific workload flow is eligible and whether its copy can reach the analyzer.

**Expected success:** Correct ENI + matching accept filter + working target path.

**If it fails:** Do not assume the SG/NACL dropped the exact packet if the workload demonstrably received it. Check filter/session/path mismatch first.

**Next action:** Correlate the 5-tuple and timestamp, then inspect the configured source ENI and filter.

### Symptom: VPC Flow Logs show REJECT and analyzer sees nothing

**Where to check:** Source SG/NACL and Flow Log record.

**What it tests:** Whether VPC policy rejected the inbound traffic.

**Expected result:** A source-side inbound rejection is consistent with AWS documentation that such traffic is not mirrored.

**Next action:** Identify the rule responsible; do not troubleshoot analyzer VXLAN decapsulation for a packet that never became mirrorable.

### Symptom: analyzer sees UDP/4789 but not the original TCP flow

**Where to check:** Analyzer software.

**What it tests:** Whether the analyzer is decoding VXLAN.

**Expected success:** VXLAN is decapsulated and the original mirrored frame is visible inside it.

**Failure means:** The transport copy reached the target, but the analyzer is not presenting the inner packet properly.

### Symptom: only some packets are missing under load

**Where to check:** EC2 bandwidth/PPS metrics and mirror-target capacity.

**What it tests:** Whether mirror traffic is being dropped due to resource limits.

**Next action:** Correlate packet loss with load and review AWS Traffic Mirroring bandwidth/PPS limitations.

---

## 14. Common mistakes

| Mistake | Why it is wrong |
|---|---|
| Assuming Traffic Mirroring sees packets before all VPC policy | AWS explicitly documents that source-side inbound SG/NACL drops are not mirrored. |
| Assuming an NLB converts VXLAN to TCP | Traffic Mirroring uses VXLAN encapsulation; the analyzer must handle the mirror transport correctly. |
| Expecting TLS decryption | Traffic Mirroring copies traffic; it does not automatically decrypt TLS. |
| Creating a filter but no rules | By default, no traffic is mirrored until filter rules permit it. |
| Mirroring ingress and expecting egress too | Directions have separate filter rules. |
| Ignoring mirror-target security/routing | The copied VXLAN traffic has to reach the target successfully. |
| Treating “workload received it” as proof the analyzer must see it | Filter, ENI, direction, path, target, capacity, and correlation errors can still explain a missing copy. |

---

## 15. Exam memory aid

```text
Inbound packet
   |
   v
Source-side VPC policy
   |
   +-- DROP by inbound SG/NACL --> NOT MIRRORED
   |
   v
Eligible source ENI traffic
   |
   v
Traffic Mirror filter
   |
   +-- reject/no match --> NOT MIRRORED
   |
   v
VXLAN copy --> target --> analyzer
```

Remember three distractor killers:

- **VPC policy:** rejected source-side inbound traffic does not appear in Traffic Mirroring.
- **VXLAN:** mirrored traffic is VXLAN-encapsulated; NLB does not “convert VXLAN to TCP.”
- **TLS:** Traffic Mirroring does not automatically decrypt TLS.

---

## 16. Source information, additional explanation, and inference

### Source information

Confirmed by AWS documentation:

- Traffic Mirroring copies traffic from source ENIs to mirror targets.
- Matching mirrored packets are VXLAN encapsulated.
- Target-side handling must permit/process VXLAN, commonly UDP/4789.
- Inbound traffic dropped at the source because of inbound SG or inbound NACL rules is not mirrored.
- Mirrored outbound traffic is not subject to the source's outbound SG rules.
- Traffic Mirror filters determine what traffic is copied.
- Empty/no matching accept rules result in traffic not being mirrored.
- Mirrored packets can be dropped due to bandwidth/PPS limitations.

### Additional explanation

Separate the troubleshooting problem into four questions:

1. **Was the original packet allowed to reach the workload?**
2. **Was the packet eligible under the Traffic Mirror filter?**
3. **Was the copied VXLAN packet successfully delivered to the target?**
4. **Could the analyzer decode and display the inner mirrored packet?**

### Reasonable inference

If the application truly received the exact flow but the analyzer did not, the investigation moves away from an SG/NACL drop of that exact packet and toward source/interface selection, mirror filters, target delivery, capacity, decapsulation, or event correlation.

---

## Sources

1. AWS VPC Traffic Mirror targets and routing/security behavior — https://docs.aws.amazon.com/vpc/latest/mirroring/traffic-mirroring-targets.html
2. AWS — How Traffic Mirroring works — https://docs.aws.amazon.com/vpc/latest/mirroring/traffic-mirroring-how-it-works.html
3. AWS — Traffic Mirror filters — https://docs.aws.amazon.com/vpc/latest/mirroring/traffic-mirroring-filters.html
4. AWS — Traffic Mirror packet format — https://docs.aws.amazon.com/vpc/latest/mirroring/traffic-mirroring-packet-formats.html
5. AWS — Traffic Mirror connectivity — https://docs.aws.amazon.com/vpc/latest/mirroring/traffic-mirroring-connection.html
6. AWS — Traffic Mirroring limitations — https://docs.aws.amazon.com/vpc/latest/mirroring/traffic-mirroring-network-limitations.html
7. AWS CLI v2 command references — https://docs.aws.amazon.com/cli/latest/reference/ec2/create-traffic-mirror-filter.html ; https://docs.aws.amazon.com/cli/latest/reference/ec2/create-traffic-mirror-filter-rule.html ; https://docs.aws.amazon.com/cli/latest/reference/ec2/create-traffic-mirror-session.html
