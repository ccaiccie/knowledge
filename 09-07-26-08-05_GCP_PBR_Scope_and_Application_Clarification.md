# GCP Policy-Based Routes — Where They Apply and How to Scope Them

This note clarifies Sections 7.9 and 7.11 of the Palo Alto Networks Firewalling in Google Cloud guide.

## Core concept

A Google Cloud **Policy-Based Route (PBR)** is **not attached to a subnet or route table**. It is a global route resource associated with a single VPC by the `--network` argument.

There is no later `associate`, `attach`, or `apply-to-subnet` command.

The route's applicability is determined when you create it:

| PBR scope | Applies to |
|---|---|
| No `--tags` and no `--interconnect-attachment-region` | All applicable VM instances, Cloud VPN tunnels, and Cloud Interconnect VLAN attachments in the VPC |
| `--tags=TAG` | Only VM instances in the VPC that have the specified network tag |
| `--interconnect-attachment-region=REGION` | Cloud Interconnect VLAN attachments in that region; `all` covers all attachment regions |

You cannot target one specific Cloud VPN tunnel, and you cannot target one specific VLAN attachment.

## 7.9 — Cloud Interconnect inbound inspection

Example:

```cli
gcloud network-connectivity policy-based-routes create pbr-interconnect-to-apps \
  --project=SEC_PROJECT \
  --network="projects/SEC_PROJECT/global/networks/trust-vpc" \
  --source-range=10.100.0.0/16 \
  --destination-range=10.10.0.0/16 \
  --ip-protocol=ALL \
  --protocol-version=IPv4 \
  --next-hop-ilb-ip=10.250.10.25 \
  --priority=400 \
  --interconnect-attachment-region=us-central1
```

Interpretation:

```text
--network=.../trust-vpc
  -> the PBR belongs to trust-vpc

--interconnect-attachment-region=us-central1
  -> evaluate this PBR for matching packets entering trust-vpc
     through Interconnect VLAN attachments in us-central1
```

Packet path:

```text
On-prem
 -> Interconnect
 -> VLAN attachment in us-central1
 -> PBR evaluation in trust-vpc
 -> next-hop ILB 10.250.10.25
 -> VM-Series
 -> workload
```

The return direction from workload to on-prem is a different applicability context. If workload-originated packets must also be inspected, create a VM-scoped PBR, commonly using a network tag:

```cli
gcloud compute instances add-tags app-vm-1 \
  --project=SEC_PROJECT \
  --zone=us-central1-a \
  --tags=inspect-hybrid

gcloud network-connectivity policy-based-routes create pbr-apps-to-onprem \
  --project=SEC_PROJECT \
  --network="projects/SEC_PROJECT/global/networks/trust-vpc" \
  --source-range=10.10.0.0/16 \
  --destination-range=10.100.0.0/16 \
  --ip-protocol=ALL \
  --protocol-version=IPv4 \
  --next-hop-ilb-ip=10.250.10.25 \
  --priority=400 \
  --tags=inspect-hybrid
```

So the two directions are deliberately scoped differently:

```text
On-prem -> GCP:  Interconnect attachment scope
GCP -> On-prem:  workload VM tag scope
```

## HA VPN

A PBR cannot target one specific Cloud VPN tunnel. To include matching traffic from Cloud VPN tunnels, create a PBR without VM tags and without Interconnect-specific scope:

```cli
gcloud network-connectivity policy-based-routes create pbr-hybrid-to-apps \
  --project=SEC_PROJECT \
  --network="projects/SEC_PROJECT/global/networks/trust-vpc" \
  --source-range=10.100.0.0/16 \
  --destination-range=10.10.0.0/16 \
  --ip-protocol=ALL \
  --protocol-version=IPv4 \
  --next-hop-ilb-ip=10.250.10.25 \
  --priority=500
```

Because no scope selector is supplied, this route can apply to matching packets from VM instances, Cloud VPN tunnels, and Interconnect VLAN attachments in `trust-vpc`.

## 7.11 — Recursion bypass for VM-Series

If a broad service-insertion PBR also applies to packets emitted by the firewall after inspection, the firewall can be sent back to the ILB again.

Tag the firewall VMs:

```cli
gcloud compute instances add-tags pan-fw-a1 \
  --project=SEC_PROJECT \
  --zone=us-central1-a \
  --tags=pan-fw
```

Create a higher-priority bypass PBR in the same VPC:

```cli
gcloud network-connectivity policy-based-routes create pbr-pan-fw-bypass \
  --project=SEC_PROJECT \
  --network="projects/SEC_PROJECT/global/networks/trust-vpc" \
  --source-range=0.0.0.0/0 \
  --destination-range=0.0.0.0/0 \
  --ip-protocol=ALL \
  --protocol-version=IPv4 \
  --next-hop-other-routes=DEFAULT_ROUTING \
  --priority=100 \
  --tags=pan-fw
```

Meaning:

```text
--network=trust-vpc
  -> the bypass PBR belongs to trust-vpc

--tags=pan-fw
  -> only packets emitted by tagged firewall VMs are eligible

--priority=100
  -> evaluated before lower-priority service-insertion PBRs

--next-hop-other-routes=DEFAULT_ROUTING
  -> stop evaluating other PBRs and resume normal destination-based routing
```

Result:

```text
VM-Series emits inspected packet
 -> pbr-pan-fw-bypass matches
 -> DEFAULT_ROUTING
 -> skip lower-priority inspection PBRs
 -> normal subnet/static/dynamic route selection
 -> workload or Cloud Router/Interconnect/HA VPN
```

## What you do not configure

```text
No subnet association
No route-table association
No NIC route-table association
No Cloud Router attachment of the PBR
No separate "apply PBR" command
```

Cloud Router supplies dynamic hybrid route information; it does not own the PBR.

## Sources

- https://docs.cloud.google.com/vpc/docs/policy-based-routes
- https://docs.cloud.google.com/vpc/docs/use-policy-based-routes
- https://docs.cloud.google.com/sdk/gcloud/reference/network-connectivity/policy-based-routes/create
- https://docs.cloud.google.com/vpc/docs/routes
