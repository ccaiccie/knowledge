# Azure Route Server + Third-Party NVA for Dynamic Service Insertion — Comprehensive Study Guide

**Generated:** 2026-09-05  
**Updated:** 2026-09-05 — expanded with NVA placement, peering, control-plane, and data-plane requirements  
**Scope:** Azure Route Server (ARS), Border Gateway Protocol (BGP), third-party Network Virtual Appliances (NVAs), dynamic service insertion, route tables, effective routes, hub-and-spoke, internet/hybrid/East-West flow paths, high availability, symmetry, verification, and troubleshooting.

## Supplied / supporting URLs

- https://learn.microsoft.com/en-us/azure/route-server/route-injection-in-spokes
- https://learn.microsoft.com/en-us/azure/route-server/configure-route-server
- https://learn.microsoft.com/en-us/azure/route-server/route-server-faq
- https://learn.microsoft.com/en-us/azure/route-server/troubleshoot-route-server
- https://learn.microsoft.com/en-us/azure/route-server/quickstart-create-route-server-cli
- https://learn.microsoft.com/en-us/azure/route-server/expressroute-vpn-support
- https://learn.microsoft.com/en-us/azure/route-server/hub-routing-preference
- https://learn.microsoft.com/en-us/azure/route-server/route-maps-about
- https://learn.microsoft.com/en-us/azure/route-server/route-maps-scenario-drop-inbound-routes
- https://learn.microsoft.com/en-us/azure/virtual-network/manage-route-table
- https://learn.microsoft.com/en-us/azure/virtual-network/virtual-network-manage-peering
- https://learn.microsoft.com/en-us/azure/architecture/networking/guide/network-virtual-appliance-high-availability
- https://learn.microsoft.com/en-us/azure/architecture/example-scenario/firewalls/

---

## 1. The single most important concept

**Source information:** Azure Route Server is a managed **BGP control-plane** service. It exchanges routes with an NVA and causes eligible Azure workloads to receive those routes in their **effective routing tables**. It is not an inline router and it does not carry workload packets.

**Additional explanation:** The third-party firewall, SD-WAN appliance, router, or other NVA is the **data-plane next hop**. Route Server distributes the NVA's reachability information through Azure's software-defined networking (SDN) control plane.

> **The NVA does not edit the spoke's Azure Route Table resource.**  
> **It advertises a BGP route to Route Server. Route Server causes Azure to program that route into eligible VM/NIC effective routes.**

![Control/data plane](images/09-05-26-13-55_ars_nva_control_data_plane.svg)

[Editable draw.io](images/09-05-26-13-55_ars_nva_control_data_plane.drawio)

**What this image shows:** BGP terminates between the NVA and Route Server, while workload packets go directly to the NVA.

**What matters:** BGP health and packet forwarding are separate things.

**What to verify:** BGP peering, ARS learned routes, VM NIC effective routes, Network Watcher next hop, and NVA dataplane/session state.

---

## 2. Three different "route tables" you must keep separate mentally

| Object | What it is | Who updates it | Can NVA BGP modify it? |
|---|---|---|---|
| **Azure Route Table resource** | ARM object containing user-defined routes (UDRs) | Administrator / IaC / automation | **No** |
| **Route Server BGP routing state** | Routes learned from NVA peers, gateways, and Azure connectivity | Route Server control plane | **Yes — learns dynamically** |
| **VM NIC effective routes** | Combined forwarding view used by Azure SDN | Azure combines system + BGP + UDR routes | **Yes — BGP routes appear here** |

Example:

```text
Azure Route Table resource attached to spoke subnet:
  No custom UDR entries

Route Server learned-routes:
  0.0.0.0/0 via NVA 10.0.2.4, AS_PATH 65001

Spoke VM NIC effective routes:
  0.0.0.0/0 -> VirtualAppliance 10.0.2.4, source BGP
```

The subnet's user-created Route Table resource can remain empty while workload forwarding changes dynamically.

---

## 3. Does the NVA have to be in the same VNet as Azure Route Server?

### Short answer

**No. The NVA does not inherently have to be in the same VNet as Azure Route Server.**

The most common and simplest design puts Route Server and the NVA in the same hub VNet, but Microsoft also documents topologies where Route Server and NVAs are in different **peered VNets**.

The real requirements are:

1. The NVA must be able to establish BGP to **both** Route Server BGP IP addresses.
2. The workload must have a valid Azure data-plane path to the NVA private IP used as the next hop.
3. The VNet peering configuration must allow the workload VNet to consume the remote Route Server where required.
4. Forwarded traffic must be allowed on peerings that carry NVA transit traffic.
5. Stateful return routing must be deliberately engineered.

### The common design: ARS and NVA in the same hub VNet

![Same-VNet NVA design](images/09-05-26-13-55_ars_same_vnet_nva_requirement.svg)

[Editable draw.io](images/09-05-26-13-55_ars_same_vnet_nva_requirement.drawio)

**What this image shows:** Route Server and the firewall/NVA are separate resources/subnets inside one hub VNet, with workload spokes peered to the hub.

**What matters:** This topology minimizes peering and reachability variables. The NVA can reach both Route Server IPs directly through VNet routing, while spoke workloads can reach the NVA through hub/spoke peering.

**What to verify:** Both NVA-to-ARS BGP sessions, spoke peering settings, forwarded traffic, and the spoke VM NIC effective routes.

Example:

```text
Hub VNet:               10.0.0.0/16
RouteServerSubnet:      10.0.1.0/26
Route Server BGP IPs:   10.0.1.4, 10.0.1.5
Route Server ASN:       65515
NVA subnet:             10.0.2.0/24
NVA:                    10.0.2.4, ASN 65001
Spoke VNet:             10.20.0.0/16
```

Control plane:

```text
NVA 10.0.2.4
   |\
   | \ eBGP multihop
   |  \
   v   v
ARS 10.0.1.4
ARS 10.0.1.5
```

Data plane:

```text
Spoke VM
   |
   | effective route says next hop = NVA
   v
NVA 10.0.2.4
   |
   v
Destination
```

Route Server is **not** in the data path.

### Supported alternative: NVA in a different peered VNet

![Peered-VNet NVA design](images/09-05-26-13-55_ars_peered_vnet_nva_supported.svg)

[Editable draw.io](images/09-05-26-13-55_ars_peered_vnet_nva_supported.drawio)

**What this image shows:** Route Server is in VNet A while the NVA is in VNet B, with peering providing IP reachability for BGP.

**What matters:** Successful BGP across the peering does not automatically prove that a third workload VNet can reach the NVA. **VNet peering is not automatically transitive.**

**What to verify:** Two separate paths:

```text
Control plane:
Route Server VNet <---- BGP over peering ----> NVA VNet

Data plane:
Workload VNet <---- valid Azure forwarding path ----> NVA VNet
```

### Why this distinction matters

This topology can exist:

```text
Spoke VNet  <---- peering ---->  RouteServer VNet
RouteServer VNet <---- peering ----> NVA VNet
```

But that does **not** automatically create generic transit:

```text
Spoke VNet  <---- automatic transit? ----> NVA VNet
```

It may be possible for the NVA to have perfect BGP adjacency with Route Server while the spoke packet cannot actually reach the NVA private IP that appears as its next hop.

Therefore:

> **Route propagation is not the same thing as packet transit.**

For a different-VNet NVA design, you must deliberately provide the workload-to-NVA data path, for example through direct peering or another supported transit design.

### What absolutely must be in the Route Server VNet?

- Azure Route Server itself.
- The dedicated `RouteServerSubnet`.
- For the standard Route Server + ExpressRoute/VPN gateway integration, the gateway participates from the Route Server hub design as documented by Microsoft.

The **NVA itself does not universally have to be in that VNet**.

### Recommended design for learning and straightforward production deployments

Start with:

```text
                        HUB VNET
             +---------------------------+
             | RouteServerSubnet         |
             | Azure Route Server        |
             |                           |
             | NVA subnet                |
             | FW-1          FW-2        |
             +---------------------------+
                  /                 \
                 / VNet peering      \ VNet peering
                /                     \
       +----------------+      +----------------+
       | Spoke A        |      | Spoke B        |
       | 10.10.0.0/16   |      | 10.20.0.0/16   |
       +----------------+      +----------------+
```

This keeps the mental model clean:

```text
NVA ⇄ Route Server       = BGP control plane
Route Server → Spokes    = Azure route propagation
Spoke → NVA              = data plane
NVA → destination        = inspected forwarding
```

---

## 4. Peering requirements for a spoke to consume the hub Route Server

The spoke does **not** form BGP directly with Route Server.

For a common centralized hub-and-spoke design:

### Hub-to-spoke peering

Configure the hub side so the peering permits the routing/transit behavior required by the NVA design, including **forwarded traffic** where the firewall forwards packets across the peering.

### Spoke-to-hub peering

Enable the option conceptually shown in Azure as:

**Use the remote virtual network's gateway or Route Server**.

This is the key peering relationship that lets the spoke consume the Route Server in the remote hub.

### What the spoke VM does not need

The workload VM:

- does not run BGP,
- does not peer to Route Server,
- does not peer to the NVA,
- does not need a guest static route pointing at Route Server,
- does not need RBAC permission to Route Server.

Azure SDN supplies the effective route to the VM NIC.

---

## 5. Minute detail: exactly how an NVA route reaches a spoke VM

![Route propagation pipeline](images/09-05-26-13-55_ars_route_propagation_pipeline.svg)

[Editable draw.io](images/09-05-26-13-55_ars_route_propagation_pipeline.drawio)

Assume:

```text
Hub VNet:                  10.0.0.0/16
RouteServerSubnet:         10.0.1.0/26
Route Server peer #1:      10.0.1.4
Route Server peer #2:      10.0.1.5
Route Server ASN:          65515
NVA:                       10.0.2.4, ASN 65001
Spoke VNet:                10.20.0.0/16
Spoke VM:                  10.20.1.10
NVA advertisement:         0.0.0.0/0
```

### Step 1 — NVA originates the route

Conceptually:

```text
NLRI:      0.0.0.0/0
AS_PATH:   65001
NEXT_HOP:  NVA reachability
```

The exact default-originate or redistribution mechanism is vendor-specific.

### Step 2 — NVA advertises it to both Route Server instances

```text
NVA 10.0.2.4, ASN 65001
  |-- BGP --> ARS IP #1, ASN 65515
  `-- BGP --> ARS IP #2, ASN 65515
```

### Step 3 — Route Server learns the route

Verify:

```cli
az network routeserver peering list-learned-routes \
  --name '<PEER_NAME>' \
  --resource-group '<RESOURCE_GROUP>' \
  --routeserver '<ROUTE_SERVER_NAME>' \
  -o table
```

Conceptual result:

```text
Network      NextHop     Origin   ASPath
-----------  ----------  -------  ------
0.0.0.0/0    10.0.2.4    EBgp     65001
```

**Simulated output for explanation only.**

### Step 4 — Azure checks spoke eligibility

Azure evaluates VNet peering and remote Route Server usage.

If ARS learned the route but the spoke NIC does not show it, inspect the spoke/hub peering before troubleshooting the firewall dataplane.

### Step 5 — Azure SDN programs the spoke NIC effective route

The NVA does not modify a UDR resource. The effective route can become:

```text
0.0.0.0/0 -> VirtualAppliance 10.0.2.4   [BGP]
```

### Step 6 — Azure evaluates the destination

For `8.8.8.8`, candidate routes might be:

```text
0.0.0.0/0 -> Internet       [system]
0.0.0.0/0 -> 10.0.2.4      [BGP]
```

The BGP route normally wins over the ordinary system default for the same prefix length.

### Step 7 — Packet goes directly to the NVA

```text
10.20.1.10 -> 8.8.8.8

Spoke VM
   |
   | Azure effective route: 0/0 -> 10.0.2.4
   v
NVA
   |
   | inspect / NAT / route
   v
Internet
```

---

## 6. Before and after route injection

![Before and after effective routes](images/09-05-26-13-55_ars_before_after_effective_routes.svg)

[Editable draw.io](images/09-05-26-13-55_ars_before_after_effective_routes.drawio)

Before the NVA advertises `0/0`:

```text
0.0.0.0/0 -> Internet [system]
```

After ARS propagates the NVA route:

```text
0.0.0.0/0 -> 10.0.2.4 [BGP]
0.0.0.0/0 -> Internet  [system]
```

The Azure Route Table resource attached to the subnet can still have **zero UDR entries**.

Verify on the workload NIC:

```cli
az network nic show-effective-route-table \
  --resource-group '<RESOURCE_GROUP>' \
  --name '<NIC_NAME>' \
  -o table
```

---

## 7. How system routes, BGP routes, and UDRs interact

![Effective route selection](images/09-05-26-13-55_ars_effective_route_selection_example.svg)

[Editable draw.io](images/09-05-26-13-55_ars_effective_route_selection_example.drawio)

Azure first uses **longest-prefix match**. For equal prefixes, route source precedence and documented special cases determine the winner.

Example:

```text
System:
0.0.0.0/0 -> Internet

BGP via ARS:
0.0.0.0/0 -> NVA-1 10.0.2.4
10.100.0.0/16 -> NVA-1 10.0.2.4

UDR:
10.100.10.0/24 -> NVA-2 10.0.2.5
203.0.113.0/24 -> Internet
```

Results:

```text
8.8.8.8       -> BGP 0/0 -> NVA-1
10.100.50.25  -> BGP /16 -> NVA-1
10.100.10.50  -> UDR /24 -> NVA-2
203.0.113.25  -> UDR /24 -> Internet
```

This allows a mostly dynamic ARS/BGP design with narrowly scoped UDR exceptions.

---

## 8. Why Route Server does not eliminate every UDR

Microsoft documents an important limitation: BGP through Route Server cannot force traffic between subnets in the **same VNet** through an NVA in the normal case because Azure VNet system routing applies.

Therefore:

- **Spoke A VNet → Spoke B VNet:** ARS/BGP can be a strong service-insertion mechanism.
- **Subnet A → Subnet B in the same VNet:** use UDRs or another supported service-insertion architecture when forced inspection is required.

---

## 9. East-West service insertion between separate spokes

![East-West service insertion](images/09-05-26-13-55_ars_nva_east_west_service_insertion.svg)

[Editable draw.io](images/09-05-26-13-55_ars_nva_east_west_service_insertion.drawio)

Example:

```text
Spoke A: 10.10.0.0/16
Spoke B: 10.20.0.0/16
NVA-1:   10.0.2.4
NVA-2:   10.0.2.5
```

Forward path:

1. VM-A sends to `10.20.1.10`.
2. Azure evaluates VM-A effective routes.
3. NVA-learned route wins.
4. Packet goes directly to the NVA.
5. NVA applies security/session policy.
6. NVA forwards toward Spoke B.

Return path:

1. VM-B performs its own route lookup for `10.10.1.10`.
2. Its effective route must also steer the flow through the intended inspection tier.
3. The firewall must see a compatible stateful return path.

---

## 10. Internet egress with an NVA-advertised default

![Internet egress](images/09-05-26-13-55_ars_nva_internet_egress.svg)

[Editable draw.io](images/09-05-26-13-55_ars_nva_internet_egress.drawio)

NVA advertises:

```text
0.0.0.0/0
```

Outbound:

```text
Spoke VM
 -> BGP 0/0 points to NVA
 -> NVA inspection
 -> SNAT if required
 -> internet
```

Return:

```text
Internet
 -> NVA public/SNAT path
 -> session/NAT lookup
 -> spoke workload
```

### NVA self-route caveat

Microsoft documents a subtle case where an NVA advertising `0.0.0.0/0` can itself receive that learned default in effective routing. A suitable UDR on the NVA subnet may be required to preserve the NVA's intended management or internet egress path.

---

## 11. Dynamic withdrawal and failover

Suppose:

```text
0.0.0.0/0 -> NVA-1 [BGP]
```

If NVA-1 withdraws the route or its BGP session fails:

1. Route Server removes that learned path.
2. Azure recomputes affected effective routes.
3. Another NVA path may become active.
4. If no firewall route remains, another applicable route may win depending on the design.

Compare with a static UDR:

```text
0.0.0.0/0 -> 10.0.2.4
```

The static UDR does not rewrite itself simply because the NVA failed.

---

## 12. Active/active and active/standby NVAs

![HA and failover](images/09-05-26-13-55_ars_nva_ha_failover.svg)

[Editable draw.io](images/09-05-26-13-55_ars_nva_ha_failover.drawio)

### Active/active

Both NVAs advertise equal paths:

```text
0.0.0.0/0 -> NVA-1
0.0.0.0/0 -> NVA-2
```

Azure can use ECMP across flows.

For stateful firewalls validate:

- session synchronization,
- vendor-supported cluster behavior,
- SNAT,
- return-path symmetry,
- failover behavior.

### Active/standby

A common policy is a shorter AS_PATH on the active NVA and prepending on standby.

Conceptual example:

```text
NVA-1: 0.0.0.0/0 AS_PATH 65001
NVA-2: 0.0.0.0/0 AS_PATH 65002 65002 65002
```

Route Server default keepalive/hold timers are documented as 60/180 seconds; peers can negotiate lower values. Test convergence rather than assuming BGP session loss equals instant application recovery.

---

## 13. Hybrid route exchange with ExpressRoute or VPN

![Hybrid branch-to-branch](images/09-05-26-13-55_ars_nva_hybrid_branch_to_branch.svg)

[Editable draw.io](images/09-05-26-13-55_ars_nva_hybrid_branch_to_branch.drawio)

For NVA ↔ ExpressRoute/VPN gateway route exchange, enable branch-to-branch when required:

```cli
az network routeserver update \
  --name '<ROUTE_SERVER_NAME>' \
  --resource-group '<RESOURCE_GROUP>' \
  --allow-b2b-traffic true
```

Route Server hub routing preference can influence equal destinations learned via ExpressRoute, VPN, or NVA/SD-WAN paths.

Example:

```cli
az network routeserver update \
  --name '<ROUTE_SERVER_NAME>' \
  --resource-group '<RESOURCE_GROUP>' \
  --hub-routing-preference 'ASPath'
```

---

## 14. Route maps and BGP policy

Azure Route Server route maps are currently documented as **Preview**.

Use cases include:

- dropping unwanted prefixes,
- aggregation,
- AS_PATH manipulation,
- BGP community policy,
- controlling propagation between NVA and gateway domains.

Microsoft also documents `NO_ADVERTISE`:

```text
65535:65282
```

Treat preview features according to current Azure preview terms.

---

## 15. Route Server and NVA requirements checklist

### Azure Route Server

- Dedicated subnet named `RouteServerSubnet`.
- Minimum subnet size currently documented as `/26`.
- Do not attach a UDR to `RouteServerSubnet`.
- Do not attach an NSG to `RouteServerSubnet`.
- Route Server uses ASN `65515`.
- Route Server exposes two managed BGP IP addresses.

### NVA

- BGP support.
- A supported ASN different from `65515`.
- Reachability to both Route Server BGP IPs.
- eBGP multihop where required.
- BGP sessions to **both** Route Server instances.
- Consistent route advertisement to both peers.
- IP forwarding enabled.
- Vendor routing and firewall dataplane configured.
- HA/session design appropriate for stateful traffic.

### Spoke VNet

- VNet peering to the Route Server VNet.
- Remote gateway/Route Server usage enabled as required.
- Forwarded traffic enabled where NVA transit needs it.
- Valid data-plane reachability to the NVA next hop.

### Workload VM

Nothing special inside the guest is required for ARS route injection.

---

## 16. Current scale considerations

Use the current Microsoft Route Server FAQ as the source of truth. At this update, Microsoft documents values including:

| Item | Current documented value |
|---|---:|
| BGP peers per Route Server | 16 |
| Routes accepted from one BGP peer | 4,000 |
| Supported VNets | 500 |
| VMs across VNet + peered VNets | 50,000 |
| Total on-prem + Azure VNet prefixes | 10,000 |

Re-check these before production deployment because limits can change.

---

## 17. Verification chain — prove every stage

### Check 1 — Did the NVA advertise the prefix?

On the NVA verify:

- both BGP neighbors,
- local BGP RIB,
- advertised routes,
- route policy,
- AS_PATH and communities.

### Check 2 — Did Route Server learn it?

```cli
az network routeserver peering list-learned-routes \
  -g '<RESOURCE_GROUP>' \
  --routeserver '<ROUTE_SERVER_NAME>' \
  -n '<PEER_NAME>' \
  -o table
```

### Check 3 — What is Route Server advertising to the NVA?

```cli
az network routeserver peering list-advertised-routes \
  -g '<RESOURCE_GROUP>' \
  --routeserver '<ROUTE_SERVER_NAME>' \
  -n '<PEER_NAME>' \
  -o table
```

### Check 4 — Is the spoke consuming the hub Route Server?

Inspect spoke → hub peering and confirm remote Route Server/gateway usage.

### Check 5 — Did the route reach the workload NIC?

```cli
az network nic show-effective-route-table \
  -g '<RESOURCE_GROUP>' \
  -n '<NIC_NAME>' \
  -o table
```

### Check 6 — Which route wins for one exact destination?

Use Azure Network Watcher **Next hop**.

### Check 7 — Does the packet reach the NVA?

Check:

- packet capture,
- policy hit counters,
- session table,
- NAT translation,
- NVA RIB/FIB,
- HA/session state.

---

## 18. Symptom-based troubleshooting

### BGP is up, but spoke VM does not show NVA route

Check:

1. ARS learned-routes.
2. Spoke/hub peering.
3. Remote Route Server usage.
4. Route-map filtering.
5. VM NIC effective routes.
6. More-specific competing routes.

### NVA is in another VNet; BGP works but packets never arrive

This strongly suggests a **data-plane reachability** issue rather than Route Server itself.

Check:

- Is the workload VNet directly peered to the NVA VNet or otherwise provided valid transit?
- Are you incorrectly assuming VNet peering is transitive?
- Does Network Watcher Next Hop return the NVA private IP?
- Can Azure actually resolve that next hop through the configured topology?
- Is forwarded traffic allowed?

### Route Table blade is empty

Expected in a pure ARS/BGP design. Check the VM NIC **Effective routes**, not only the UDR resource.

### Same-VNet subnet-to-subnet traffic bypasses NVA

Expected when relying on BGP alone. Use UDRs or another supported service-insertion architecture.

### NVA loses internet after advertising `0/0`

Check whether the NVA itself received the learned default and use an appropriate NVA-subnet UDR to preserve management/egress routing if required.

### ExpressRoute bypasses firewall/SD-WAN path

Check hub routing preference, prefix length, AS_PATH, branch-to-branch, route maps, and communities.

---

## 19. Static UDR versus ARS/BGP service insertion

| Characteristic | Static UDR | ARS/BGP dynamic insertion |
|---|---|---|
| Route stored in Azure Route Table resource | Yes | No |
| Appears in NIC effective routes | Yes | Yes |
| Requires BGP on NVA | No | Yes |
| Can withdraw dynamically | No | Yes |
| Per-spoke route maintenance | Often | Reduced in suitable designs |
| Same-VNet forced inspection | Strong fit | BGP alone insufficient |
| NVA may live in another VNet | Yes, with valid next-hop design | Yes in supported peered designs, with both BGP and data-path reachability |
| Stateful symmetry required | Yes | Yes |

---

## 20. Final mental model

When someone asks, **"Does the NVA need to be in the hub VNet?"**, the precise answer is:

> **No.** The common design puts the NVA and Route Server in the same hub because it is simpler. The actual requirement is that the NVA can establish BGP to both Route Server IPs and that workloads receiving the NVA route have a valid Azure packet path to the NVA next hop. Microsoft documents peered-VNet NVA designs, but VNet peering is not automatically transitive, so route propagation and workload packet reachability must be validated separately.

When someone asks, **"How does the NVA update the spoke route table?"**, the precise answer is:

> It normally does **not** update the Azure Route Table resource. The NVA advertises BGP prefixes to Azure Route Server. Route Server learns them and Azure SDN propagates eligible routes into the effective routing tables of workloads in the hub and peered spokes. Azure then selects among system, BGP, and UDR routes and forwards directly to the NVA when the NVA route wins.

### Recommended lab

1. Put ARS and one NVA in the same hub VNet.
2. Peer a spoke VNet to the hub.
3. Enable the spoke to use the remote Route Server.
4. Establish NVA BGP to both ARS IPs.
5. Advertise `0.0.0.0/0` from the NVA.
6. Confirm ARS learned it.
7. Confirm the spoke VM NIC receives a BGP default to the NVA.
8. Confirm Network Watcher Next Hop points to the NVA.
9. Withdraw the route and observe it disappear.
10. Only after that works, move the NVA to a separate peered VNet and deliberately solve both BGP reachability and workload-to-NVA data-plane reachability.

---

## Sources

- https://learn.microsoft.com/en-us/azure/route-server/route-injection-in-spokes
- https://learn.microsoft.com/en-us/azure/route-server/configure-route-server
- https://learn.microsoft.com/en-us/azure/route-server/route-server-faq
- https://learn.microsoft.com/en-us/azure/route-server/troubleshoot-route-server
- https://learn.microsoft.com/en-us/azure/route-server/quickstart-create-route-server-cli
- https://learn.microsoft.com/en-us/azure/route-server/expressroute-vpn-support
- https://learn.microsoft.com/en-us/azure/route-server/hub-routing-preference
- https://learn.microsoft.com/en-us/azure/route-server/route-maps-about
- https://learn.microsoft.com/en-us/azure/route-server/route-maps-scenario-drop-inbound-routes
- https://learn.microsoft.com/en-us/azure/virtual-network/manage-route-table
- https://learn.microsoft.com/en-us/azure/virtual-network/virtual-network-manage-peering
- https://learn.microsoft.com/en-us/azure/architecture/networking/guide/network-virtual-appliance-high-availability
- https://learn.microsoft.com/en-us/azure/architecture/example-scenario/firewalls/

### Source classification

**Source information:** Microsoft Learn / Azure Architecture Center statements about Route Server, route injection, peering, BGP behavior, route maps, limits, effective routes, and documented NVA architectures.

**Additional explanation:** The route propagation walkthroughs, placement comparisons, packet-flow explanations, and troubleshooting sequences connect those documented behaviors into an operational network-engineering model.

**Reasonable inference:** Recommendations such as beginning with the same-VNet hub architecture before adopting a multi-VNet NVA design are architecture guidance, not claims of undocumented Azure behavior.
