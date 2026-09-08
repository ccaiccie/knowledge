from pathlib import Path

p = Path('09-07-26-07-03_Palo_Alto_Networks_Firewalling_in_GCP_Deep_Dive.md')
s = p.read_text()

old_toc = '  - [7.8 Internet ingress — Internet to published workload](#78-internet-ingress--internet-to-published-workload)\n'
new_toc = old_toc + '    - [7.8.9 Can the same VM-Series fleet handle NSI and Internet ingress?](#789-can-the-same-vm-series-fleet-handle-nsi-and-internet-ingress)\n'
if old_toc in s and '7.8.9 Can the same VM-Series fleet handle NSI and Internet ingress?' not in s:
    s = s.replace(old_toc, new_toc, 1)

marker = '\n## 7.9 On-premises inspection through Cloud Interconnect\n'
section = r'''
### 7.8.9 Can the same VM-Series fleet handle NSI and Internet ingress?

This is where the **primary-interface (`nic0`) constraint** becomes critical.

For Palo Alto's traditional Google Cloud Internet-ingress model, Palo Alto documents that Google external load balancers deliver traffic to the VM's **primary interface**. The supported VM-Series pattern therefore places the **Untrust dataplane on `nic0`** by using the management-interface swap model:

```text
Traditional Internet ingress

Internet
   |
   v
External passthrough NLB
   |
   v
VM-Series nic0
   |
   v
PAN-OS Untrust
   |
   | DNAT + Security policy
   v
Trust / private application
```

For passthrough load balancers that use **instance-group backends**, Google documents that load-balanced traffic is delivered to the backend VM's `nic0` interface. A second ordinary instance-group-backed ILB does **not** let you simply say "send this service to `nic2`."

That means this naive combined design is not valid:

```text
nic0 = Untrust
nic1 = Management
nic2 = NSI/inspection

External LB -> nic0       valid for classic ingress
NSI ILB     -> nic2       not achievable merely by adding a second
                         instance-group-backed passthrough LB
```

The problem is not the number of load balancers. The problem is **which VM interface each load balancer can actually target**.

#### Why this collides with NSI

Standard NSI producer delivery also uses an **internal passthrough Network Load Balancer** in front of the inspection appliances. If that producer backend is built with an instance group, the same `nic0` delivery rule applies.

So a shared fleet can create a role collision:

```text
                         SAME VM-SERIES INSTANCE

External passthrough NLB --------> nic0
                                      |
                                      +--> expected PAN-OS Untrust

NSI producer internal ILB --------> nic0
                                      |
                                      +--> would also arrive on nic0
```

You cannot solve that by assigning another logical PAN-OS interface to `nic2` unless the Google backend type and Palo Alto deployment model explicitly support targeting that non-primary NIC.

#### Google NEG exception — useful, but do not assume Palo Alto support

Google now documents that passthrough Network Load Balancers can also use zonal Network Endpoint Groups (NEGs) with `GCE_VM_IP` endpoints. This backend model can target a non-`nic0` interface in supported multi-NIC designs, unlike ordinary instance-group backends.

That changes the Google Cloud capability boundary, but it does **not** by itself prove that Palo Alto supports a combined VM-Series topology where:

```text
External LB -> nic0 / Untrust
NSI producer ILB -> non-nic0 / NSI dataplane
```

Treat that as a **version- and vendor-support question**, not as a generic architecture pattern. Verify the exact PAN-OS release, VM-Series plugin, NSI mode, backend type, NIC mapping, health-check model, and HA design in Palo Alto documentation before deploying it.

#### Safe design recommendation

Unless Palo Alto explicitly documents the combined topology you intend to use, the safer design is to separate the roles:

```text
Fleet A — traditional Internet ingress

External passthrough NLB
        |
        v
nic0 / PAN-OS Untrust
        |
        | DNAT + Security policy
        v
private workloads
```

and:

```text
Fleet B — NSI inspection

Consumer firewall policy
        |
        v
NSI producer internal passthrough NLB
        |
        v
VM-Series NIC layout required by the
current Palo Alto NSI deployment model
        |
        v
GENEVE inspection / reinjection
```

This avoids coupling two different insertion mechanisms to one primary interface and makes health checks, NAT ownership, session symmetry, upgrades, and failure domains easier to reason about.

#### Mental model

```text
External LB VIP
= public application publication
= Internet-facing
= reaches VM-Series primary/untrust path
= PAN-OS owns DNAT/session state

NSI producer ILB VIP
= internal interception transport endpoint
= not the application VIP
= carries NSI-delivered traffic to the appliance service
```

**Source information:** Palo Alto states that Google external load balancers distribute traffic to the VM-Series primary interface and therefore documents `nic0` on the Untrust VPC with management-interface swap for traditional load-balanced deployments. Google documents that instance-group-backed internal and regional external passthrough Network Load Balancers deliver load-balanced traffic through the backend VM's `nic0`; Google also documents zonal `GCE_VM_IP` NEG backends as the mechanism for targeting non-`nic0` interfaces in supported multi-NIC designs.

**Additional explanation:** Two different load balancer objects do not create two independently selectable VM interfaces when both use instance-group backends. The backend type and NIC mapping determine the actual receive interface.

**Reasonable inference:** Unless Palo Alto explicitly validates a combined NSI + Internet-ingress topology using a backend model that targets distinct dataplane NICs, use separate VM-Series fleets rather than assuming that a second ILB and a second NIC are sufficient.
'''

if marker not in s:
    raise SystemExit('section 7.9 marker not found')
if '### 7.8.9 Can the same VM-Series fleet handle NSI and Internet ingress?' not in s:
    s = s.replace(marker, '\n' + section + marker, 1)

p.write_text(s)
