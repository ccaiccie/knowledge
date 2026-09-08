from pathlib import Path
p=Path('09-08-26_AWS_Direct_Connect_Transit_VIF_Deep_Dive.md')
s=p.read_text()
old='- [11. Multiple Direct Connect circuits and failover](#11-multiple-direct-connect-circuits-and-failover)\n'
new='''- [11. Multiple Direct Connect circuits and failover](#11-multiple-direct-connect-circuits-and-failover)\n  - [11.1 Predictable multi-Region design goals](#111-predictable-multi-region-design-goals)\n  - [11.2 Recommended regional-primary / remote-backup design](#112-recommended-regional-primary--remote-backup-design)\n  - [11.3 AWS-to-on-premises path selection](#113-aws-to-on-premises-path-selection)\n  - [11.4 On-premises-to-AWS path selection](#114-on-premises-to-aws-path-selection)\n  - [11.5 Failure behavior and policy matrix](#115-failure-behavior-and-policy-matrix)\n  - [11.6 Firewall interception and inspection with DXGW + TGW](#116-firewall-interception-and-inspection-with-dxgw--tgw)\n  - [11.7 TGW route-table design for mandatory inspection](#117-tgw-route-table-design-for-mandatory-inspection)\n  - [11.8 Forward and return packet walk through the firewall](#118-forward-and-return-packet-walk-through-the-firewall)\n  - [11.9 AWS Network Firewall network-function attachment alternative](#119-aws-network-firewall-network-function-attachment-alternative)\n'''
if old not in s: raise SystemExit('TOC marker not found')
s=s.replace(old,new,1)
marker='\n---\n\n# 12. AWS CLI build example\n'
if marker not in s: raise SystemExit('section marker not found')
insert=r'''

## 11.1 Predictable multi-Region design goals

When you have Direct Connect connections in different AWS Regions, the first design decision is whether you want **active/active ECMP** or **regional-primary / remote-backup**. Do not leave this accidental.

For stateful firewalls and deterministic troubleshooting, a regional-primary model is usually easier to reason about:

```text
East AWS/on-prem traffic
  primary = DX-East
  backup  = DX-West

West AWS/on-prem traffic
  primary = DX-West
  backup  = DX-East
```

AWS Direct Connect evaluates private/transit VIF paths using longest-prefix match first, then Direct Connect local preference, then AS_PATH, then MED. AWS explicitly recommends its Direct Connect local-preference BGP communities for active/passive path control and does not recommend relying on MED as the primary mechanism.

The important supported communities for **routes you advertise from on-premises toward AWS** are:

```text
7224:7300 = High Direct Connect local preference
7224:7200 = Medium
7224:7100 = Low
```

These influence the **AWS-to-on-premises return path** for the advertised prefix.

![Multi-Region Direct Connect deterministic routing](images/09-08-26_aws_dx_multi_region_deterministic_routing.svg)

[Editable draw.io](images/09-08-26_aws_dx_multi_region_deterministic_routing.drawio)

**What this image shows:** two Direct Connect locations in different Regions, one global DXGW, separate regional TGWs, and explicit preference policy for east and west traffic.

**What matters:** AWS-side path preference and customer-router path preference are independent decisions. Configure both directions deliberately.

**What to verify:** the same prefix is not accidentally receiving equal attributes on every VIF unless ECMP is intentional; customer routers prefer the intended regional DX for AWS prefixes; AWS sees the intended high/low Direct Connect community on on-premises prefixes.

---

## 11.2 Recommended regional-primary / remote-backup design

Example:

```text
DX-East location / transit VIF-E
DX-West location / transit VIF-W
DXGW = global
TGW-East = us-east-1
TGW-West = us-west-2

East VPCs:
10.10.0.0/16
10.20.0.0/16

West VPCs:
10.30.0.0/16
10.40.0.0/16

On-prem East site:
192.168.10.0/24

On-prem West site:
192.168.20.0/24
```

A predictable policy is:

| Prefix | Primary DX | Backup DX | AWS return-path community on primary | AWS return-path community on backup |
|---|---|---|---|---|
| `192.168.10.0/24` East on-prem | DX-East | DX-West | `7224:7300` | `7224:7100` |
| `192.168.20.0/24` West on-prem | DX-West | DX-East | `7224:7300` | `7224:7100` |

On the customer side, configure BGP import policy so AWS prefixes learned from the local DX receive a higher **customer LOCAL_PREF** than the remote DX. For example:

```text
Routes learned from DX-East at East WAN edge:
LOCAL_PREF 200

Same AWS routes learned from DX-West at East WAN edge:
LOCAL_PREF 100
```

That customer LOCAL_PREF is your own BGP policy and is different from AWS Direct Connect community `7224:7300` / `7224:7100`.

Mental model:

```text
AWS DX community
= tells AWS which DX to use toward on-prem

Customer LOCAL_PREF
= tells your WAN which DX to use toward AWS
```

Do not rely only on the geographic "home Region" preference. AWS does have Region-affinity behavior when no Direct Connect local-preference community is applied, but explicit policy is easier to audit and survives architectural changes more predictably.

---

## 11.3 AWS-to-on-premises path selection

For prefixes advertised by your routers over multiple private/transit VIFs, AWS evaluates:

1. longest prefix length;
2. Direct Connect local preference;
3. AS_PATH length;
4. MED when the higher-priority attributes are equal.

For active/passive connectivity with equal prefix lengths, use the Direct Connect local-preference communities.

Example for East on-premises prefix `192.168.10.0/24`:

```text
DX-East advertisement:
192.168.10.0/24 community 7224:7300

DX-West advertisement:
192.168.10.0/24 community 7224:7100
```

AWS prefers DX-East while it is available. If the DX-East BGP route disappears, DX-West remains as the backup.

If you advertise identical prefixes with identical attributes across multiple transit VIFs, AWS can use ECMP. That is useful for active/active designs but is intentionally avoided in this regional-primary example.

---

## 11.4 On-premises-to-AWS path selection

The reverse decision happens in your customer routing domain.

The DXGW can advertise the same allowed AWS prefix over both transit VIFs. Your routers therefore need a deterministic import policy.

Example:

```text
10.10.0.0/16 learned from DX-East
  -> customer LOCAL_PREF 200

10.10.0.0/16 learned from DX-West
  -> customer LOCAL_PREF 100
```

For West prefixes, reverse the preference.

This avoids a common mistake: configuring AWS-side Direct Connect communities correctly but leaving the customer routers with equal preference, producing a different forward path than return path.

For stateful inspection, that asymmetry can cause session failure even when BGP itself is healthy.

---

## 11.5 Failure behavior and policy matrix

| Failure | Expected result in regional-primary design | What changes |
|---|---|---|
| Primary transit VIF BGP down | Backup DX wins | BGP route withdrawal removes primary path |
| Primary physical DX down | All VIFs on that circuit fail | Backup circuit/VIF becomes usable |
| One regional TGW unavailable | That Region's TGW destinations are unavailable unless another supported inter-Region architecture exists | DX alone does not replace TGW reachability |
| Primary firewall path unhealthy | Depends on firewall/GWLB/Network Firewall health and TGW inspection routing | BGP path can remain healthy while inspection fails |
| Equal BGP attributes accidentally configured | ECMP can occur | Flows may use multiple DX paths |

Do not treat Direct Connect BGP health as firewall health. Route availability, firewall health, and state synchronization are separate failure domains.

---

## 11.6 Firewall interception and inspection with DXGW + TGW

A transit VIF does **not** inspect traffic. It only provides BGP connectivity into the DXGW/TGW routing domain.

Firewall insertion is performed by **Transit Gateway route-table steering** (or by a TGW network-function attachment), not by the transit VIF itself.

A classic centralized inspection design is:

```text
On-prem
  -> Direct Connect
  -> transit VIF
  -> DXGW attachment into TGW
  -> PRE-INSPECTION TGW route table
  -> Inspection VPC attachment
  -> firewall
  -> POST-INSPECTION TGW route table
  -> destination VPC
```

Return:

```text
Destination VPC
  -> spoke TGW route table
  -> Inspection VPC
  -> same stateful inspection path
  -> POST-INSPECTION TGW route table
  -> DXGW attachment
  -> transit VIF
  -> on-prem
```

![Direct Connect TGW firewall inspection](images/09-08-26_aws_dx_tgw_firewall_inspection.svg)

[Editable draw.io](images/09-08-26_aws_dx_tgw_firewall_inspection.drawio)

**What this image shows:** separate PRE and POST TGW route domains forcing DX-originated and VPC-originated traffic through an Inspection VPC.

**What matters:** for an inspected prefix, the DXGW attachment route table must point to the inspection attachment rather than directly to the workload VPC. Likewise, the spoke return route table must point on-premises prefixes to the inspection attachment, not directly to DXGW.

**What to verify:** appliance mode is enabled on the Inspection VPC attachment, forward and return TGW route tables both select inspection, and the post-inspection route table contains the actual workload and DXGW destinations.

AWS supports centralized inspection with either **AWS Network Firewall** or **Gateway Load Balancer plus third-party appliances** in an inspection VPC. For stateful appliances, enable Transit Gateway **appliance mode** on the inspection VPC attachment so TGW preserves the same Availability Zone for the lifetime of a flow.

---

## 11.7 TGW route-table design for mandatory inspection

Use three logical TGW route domains:

### DX PRE-INSPECTION route table

**Associated attachment:** DXGW attachment.

Example routes:

```text
10.10.0.0/16 -> Inspection VPC attachment
10.20.0.0/16 -> Inspection VPC attachment
10.30.0.0/16 -> Inspection VPC attachment
10.40.0.0/16 -> Inspection VPC attachment
```

Do **not** propagate spoke VPC routes directly into this route table if doing so would create a more-specific bypass route around inspection.

### Spoke PRE-INSPECTION route table

**Associated attachments:** workload VPC attachments.

Example:

```text
192.168.0.0/16 -> Inspection VPC attachment
```

You can also steer east-west VPC prefixes to inspection here when required.

### POST-INSPECTION route table

**Associated attachment:** Inspection VPC attachment.

Example:

```text
10.10.0.0/16 -> VPC-A attachment
10.20.0.0/16 -> VPC-B attachment
10.30.0.0/16 -> VPC-C attachment
10.40.0.0/16 -> VPC-D attachment
192.168.0.0/16 -> DXGW attachment
```

This table is allowed to know the real destinations because traffic has already passed through the firewall.

The core invariant is:

```text
PRE route tables
= point TO inspection

POST route table
= point TO final destination
```

That is the same PRE/POST mental model used in other TGW service-insertion architectures.

---

## 11.8 Forward and return packet walk through the firewall

Assume:

```text
On-prem host: 192.168.10.25
AWS workload: 10.10.1.10
```

Forward:

1. Customer router chooses the preferred Direct Connect path for `10.10.1.10`.
2. Packet crosses the transit VIF and DXGW.
3. Packet enters TGW on the DXGW attachment.
4. TGW uses the route table associated with the DXGW attachment.
5. `10.10.0.0/16` points to the Inspection VPC attachment.
6. TGW sends the flow into the Inspection VPC.
7. The inspection VPC route tables/GWLB/AWS Network Firewall endpoint path delivers it to the stateful firewall.
8. The firewall allows the session.
9. Traffic returns to TGW from the Inspection VPC attachment.
10. TGW now uses the POST-INSPECTION route table associated with the Inspection VPC attachment.
11. `10.10.0.0/16` points to VPC-A.
12. VPC-A receives the packet.

Return:

1. VPC-A subnet route sends `192.168.10.25` toward TGW.
2. TGW uses the route table associated with VPC-A.
3. `192.168.0.0/16` points to the Inspection VPC attachment.
4. Appliance mode keeps the flow on the same inspection-AZ path for the lifetime of the session.
5. Firewall sees the reverse direction of the existing stateful session.
6. Traffic returns to TGW from the Inspection VPC attachment.
7. POST-INSPECTION route table selects `192.168.0.0/16 -> DXGW attachment`.
8. DXGW selects the preferred transit VIF according to Direct Connect BGP policy.
9. Packet returns to on-premises.

If step 3 on the return path instead says:

```text
192.168.0.0/16 -> DXGW attachment
```

then the return packet bypasses the firewall. That is an asymmetric stateful design.

---

## 11.9 AWS Network Firewall network-function attachment alternative

AWS Transit Gateway also supports a **network function attachment** for AWS Network Firewall. This lets TGW connect directly to AWS Network Firewall without requiring you to build a traditional inspection VPC attachment for the TGW-facing service-insertion hop.

For this attachment type, TGW routes traffic to the firewall using **static TGW routes**.

Example documented CLI pattern:

```cli
aws ec2 create-transit-gateway-route \
  --transit-gateway-route-table-id tgw-rtb-PREINSPECTION \
  --destination-cidr-block 10.10.0.0/16 \
  --transit-gateway-attachment-id tgw-attach-NETWORK-FUNCTION
```

The route target is the Network Firewall network-function attachment.

Use this model when you want AWS-managed TGW-to-Network-Firewall attachment semantics. Use an Inspection VPC + GWLB when you need third-party NGFW appliances or more customized service chains.

For either model, the Direct Connect path-selection rules remain separate from firewall insertion:

```text
BGP / transit VIF / DXGW
= choose hybrid path

TGW route tables / network-function attachment
= choose inspection path
```
'''
s=s.replace(marker,insert+marker,1)
p.write_text(s)
