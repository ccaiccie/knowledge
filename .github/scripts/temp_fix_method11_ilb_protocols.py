from pathlib import Path
p=Path('09-07-26_GCP_Shared_VPC_Centralized_Firewall_Insertion_Method_11_Deep_Dive.md')
s=p.read_text()
old='''gcloud compute backend-services create fw-ilb-be \\
  --project=network-host-prod \\
  --region=us-central1 \\
  --load-balancing-scheme=INTERNAL \\
  --protocol=TCP \\
'''
new='''gcloud compute backend-services create fw-ilb-be \\
  --project=network-host-prod \\
  --region=us-central1 \\
  --load-balancing-scheme=INTERNAL \\
  --protocol=UNSPECIFIED \\
'''
if old not in s:
    raise SystemExit('backend service block not found')
s=s.replace(old,new,1)
old2='''  --ip-protocol=TCP \\
  --ports=ALL \\
  --allow-global-access \\
'''
new2='''  --ip-protocol=L3_DEFAULT \\
  --ports=ALL \\
  --allow-global-access \\
'''
if old2 not in s:
    raise SystemExit('forwarding rule protocol block not found')
s=s.replace(old2,new2,1)
anchor='''gcloud compute backend-services get-health fw-ilb-be \\
  --project=network-host-prod \\
  --region=us-central1
```
'''
insert='''gcloud compute backend-services get-health fw-ilb-be \\
  --project=network-host-prod \\
  --region=us-central1
```

### Why this PBR firewall ILB uses `L3_DEFAULT` + `ALL`

For this **PBR -> internal passthrough NLB -> firewall/NVA** design, the forwarding rule is intentionally configured with:

```text
Forwarding rule protocol: L3_DEFAULT
Ports:                    ALL
Backend service protocol: UNSPECIFIED
```

That combination makes the firewall service explicitly multi-protocol. For IPv4 internal passthrough Network Load Balancers, Google documents `L3_DEFAULT` as supporting TCP, UDP, ICMP, SCTP, ESP, AH, GRE, and other supported L3 protocols. `L3_DEFAULT` requires `ALL` ports, and the corresponding backend service protocol is `UNSPECIFIED`.

The TCP health check above does **not** limit inspected traffic to TCP. It only determines whether each firewall backend is healthy enough to receive data-plane flows.

> **Do not copy this forwarding rule unchanged into the static-route design in Section 7.2.** Google documents that an internal passthrough NLB whose forwarding rule uses `L3_DEFAULT` **cannot be the next hop of a static route**. If such a static route is created, traffic is silently dropped.

'''
if anchor not in s:
    raise SystemExit('health anchor not found')
s=s.replace(anchor,insert,1)
anchor2='''## 7.2 Static-route egress `gcloud` build
'''
insert2='''## 7.2 Static-route egress `gcloud` build

> **Protocol behavior is different from the PBR example in Section 5.4.** Do **not** use an `L3_DEFAULT` forwarding rule when an internal passthrough NLB is the next hop of a **static route**. Google documents that `L3_DEFAULT` forwarding rules cannot be static-route next hops; traffic is silently dropped. Use a supported TCP or UDP forwarding-rule configuration for the static-route next-hop ILB. For modern next-hop ILB routes, Google Cloud forwards supported VPC protocol traffic on all ports to the appliance backends regardless of the forwarding rule's protocol/port configuration. In other words, the TCP/UDP forwarding-rule setting is a next-hop compatibility requirement here, not a statement that the firewall only receives that one protocol.

```text
PBR -> ILB -> firewall:
  L3_DEFAULT + ALL
  backend protocol UNSPECIFIED

Static route -> ILB -> firewall:
  TCP or UDP forwarding rule as supported next-hop configuration
  NOT L3_DEFAULT
  next-hop behavior still forwards supported VPC protocols/all ports
```

'''
if anchor2 not in s:
    raise SystemExit('section 7.2 anchor not found')
s=s.replace(anchor2,insert2,1)
p.write_text(s)
