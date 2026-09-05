# Azure Route Server + Third-Party NVA for Dynamic Service Insertion — Comprehensive Study Guide

**Generated:** 2026-09-05  
**Updated:** 2026-09-05 — expanded with minute-detail route-propagation examples  
**Scope:** Azure Route Server (ARS), Border Gateway Protocol (BGP), third-party Network Virtual Appliances (NVAs), dynamic service insertion, route tables, effective routes, hub-and-spoke, internet/Hybrid/East-West flow paths, high availability, symmetry, verification, and troubleshooting.

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
- https://learn.microsoft.com/en-us/azure/architecture/example-scenario/firewalls/

---

## 1. The single most important concept

**Source information:** Azure Route Server is a managed **BGP control-plane** service. It exchanges routes with an NVA and causes eligible Azure workloads to receive those routes in their **effective routing tables**. It is not an inline router and it does not carry workload packets.

**Additional explanation:** The third-party firewall, SD-WAN appliance, router, or other NVA is the **data-plane next hop**. Route Server distributes the NVA's reachability information through Azure's software-defined networking (SDN) control plane.

> **The NVA does not edit the spoke's Azure Route Table resource.**  
> **It advertises a BGP route to Route Server. Route Server causes Azure to program that route into eligible VM/NIC effective routes.**

That distinction is the heart of dynamic service insertion.

![Control/data plane](images/09-05-26-13-55_ars_nva_control_data_plane.svg)

[Editable draw.io](images/09-05-26-13-55_ars_nva_control_data_plane.drawio)

**What this image shows:** BGP control-plane exchange terminates between the NVA and Route Server, while workload packets go directly to the NVA.

**What matters:** A healthy BGP session proves route exchange only. It does not prove the firewall is forwarding, inspecting, NATing, or preserving state correctly.

**What to verify:** BGP peering, ARS learned routes, VM NIC effective routes, Network Watcher next hop, and NVA dataplane/session state.

---

## 2. Three different "route tables" you must keep separate mentally

Azure networking becomes much clearer when these are treated as separate objects.

| Object | What it is | Who owns/updates it | Can the NVA update it by BGP? |
|---|---|---|---|
| **Azure Route Table resource** | ARM resource containing user-defined routes (UDRs) attached to a subnet | Administrator, Terraform, Bicep, ARM, Azure Virtual Network Manager, automation | **No** |
| **Azure Route Server BGP routing state** | Routes learned from NVA peers, gateways, and Azure connectivity | Route Server control plane | **Yes — routes are learned dynamically** |
| **VM NIC effective routes** | Final merged routing view used by the Azure virtual network dataplane for that NIC | Azure SDN combines system routes, BGP routes, UDRs, peering/gateway state | **Yes — NVA-learned BGP routes appear here** |

This means all of the following can be true at the same time:

```text
Subnet route-table resource:
  No custom routes

Route Server learned-routes:
  0.0.0.0/0 via NVA 10.0.2.4, AS_PATH 65001

Spoke VM NIC effective routes:
  0.0.0.0/0 -> VirtualAppliance 10.0.2.4, source BGP
```

The Azure Route Table resource can remain completely unchanged while the forwarding behavior of the VM changes dynamically.

---

## 3. Minute detail: exactly how an NVA route reaches a spoke VM

![Route propagation pipeline](images/09-05-26-13-55_ars_route_propagation_pipeline.svg)

[Editable draw.io](images/09-05-26-13-55_ars_route_propagation_pipeline.drawio)

**What this image shows:** The control-plane chain from NVA BGP UPDATE to the VM NIC effective route.

**What matters:** There is no step in which Route Server creates or modifies a `Microsoft.Network/routeTables/routes` object.

**What to verify:** The route must be visible first at the NVA, then at ARS, then at the VM NIC.

### Example topology

```text
Hub VNet:                  10.0.0.0/16
RouteServerSubnet:         10.0.1.0/26
Route Server peer IP #1:   10.0.1.4
Route Server peer IP #2:   10.0.1.5
Route Server ASN:          65515
NVA subnet:                10.0.2.0/24
NVA-1:                     10.0.2.4
NVA ASN:                   65001
Spoke VNet:                10.20.0.0/16
Spoke workload subnet:     10.20.1.0/24
Spoke VM:                  10.20.1.10
```

Assume the NVA must become the internet egress firewall, so it originates:

```text
0.0.0.0/0
```

### Step 1 — The NVA creates/originates the route in its own routing process

How the default is originated is vendor-specific. Common mechanisms include a static default redistributed into BGP, a default-originate policy, or a vendor routing-policy construct.

Conceptual BGP information:

```text
NLRI:      0.0.0.0/0
NEXT_HOP:  NVA reachability / NVA next-hop semantics
AS_PATH:   65001
```

This is illustrative, not vendor CLI output.

### Step 2 — The NVA sends BGP UPDATEs to both Route Server instances

Azure Route Server exposes two managed BGP IPs for availability. Each NVA should peer with both.

Conceptually:

```text
NVA 10.0.2.4, ASN 65001
  |-- eBGP multihop --> 10.0.1.4, ASN 65515
  `-- eBGP multihop --> 10.0.1.5, ASN 65515
```

Microsoft recommends the NVA advertise a consistent route set over both peerings.

### Step 3 — Route Server accepts the BGP UPDATE

Route Server runs normal BGP acceptance/loop checks and any configured route-map policy.

Verify what ARS learned:

```cli
az network routeserver peering list-learned-routes \
  --name '<PEER_NAME>' \
  --resource-group '<RESOURCE_GROUP>' \
  --routeserver '<ROUTE_SERVER_NAME>' \
  -o table
```

A simulated result might conceptually look like:

```text
Network      NextHop     Origin   ASPath
-----------  ----------  -------  ------
0.0.0.0/0    10.0.2.4    EBgp     65001
```

**Simulated output — not copied from Microsoft or a vendor appliance.**

At this moment, the route is in Route Server's control-plane state. The spoke UDR table still has not been edited.

### Step 4 — Azure determines whether the spoke is eligible to consume the hub Route Server

For the common centralized hub-and-spoke model:

1. Hub and spoke VNets are peered.
2. The spoke peering is configured to **Use the remote virtual network's gateway or Route Server**.
3. Route Server is deployed in the hub.
4. The peering topology supports that remote Route Server usage.
5. The NVA is reachable as a valid next hop through the hub/peering topology.

If the NVA route is visible on Route Server but missing from the spoke NIC effective routes, this peering relationship is one of the first things to check.

### Step 5 — Azure SDN propagates the learned route into eligible workload forwarding state

This is the Azure-managed part.

The VM does **not** establish BGP with Route Server. The guest operating system does not need a BGP daemon. The NVA does not need Azure RBAC permission to modify spoke route-table resources.

Azure's virtual networking control plane programs eligible workloads so their NIC effective routing contains the learned BGP route.

### Step 6 — The VM NIC effective route view changes

Before the NVA advertises a default route, the spoke VM may have conceptually:

```text
10.20.0.0/16     VirtualNetwork / peering-related route
0.0.0.0/0        Internet                    [system]
```

After the NVA advertisement is propagated:

```text
10.20.0.0/16     VirtualNetwork / peering-related route
0.0.0.0/0        VirtualAppliance 10.0.2.4   [BGP]
0.0.0.0/0        Internet                    [system]
```

The user-created route-table resource can still have **zero UDR entries**.

![Before and after effective routes](images/09-05-26-13-55_ars_before_after_effective_routes.svg)

[Editable draw.io](images/09-05-26-13-55_ars_before_after_effective_routes.drawio)

**What this image shows:** What changes before and after ARS propagates the NVA route.

**What matters:** BGP changes effective forwarding state, not the route-table ARM object.

**What to verify:** Compare the subnet's configured route table with the VM NIC's effective routes.

### Step 7 — Azure performs route selection for each destination

For destination `8.8.8.8`, the matching candidates may be:

```text
0.0.0.0/0 -> Internet       [system]
0.0.0.0/0 -> 10.0.2.4      [BGP learned through ARS]
```

For equal prefix length in the normal Azure route-selection model, BGP is preferred over the ordinary system route, so the NVA path is selected.

### Step 8 — The packet goes directly from the workload to the NVA

```text
Spoke VM 10.20.1.10
        |
        | Azure effective route lookup
        | 0.0.0.0/0 -> 10.0.2.4
        v
NVA 10.0.2.4
        |
        | security policy / NAT / routing
        v
Internet
```

Route Server is not in the packet path.

---

## 4. Exact example: the Route Table blade is empty, but traffic still goes to the firewall

Imagine the spoke subnet is associated with an Azure Route Table resource named:

```text
rt-spoke-app
```

In the Azure portal:

**Route tables** → **rt-spoke-app** → **Routes**

You might see no custom routes at all.

That tells you only that there are no administrator-created UDR rows in that ARM resource.

Now inspect:

**Virtual machine** → **Networking** → **Network interface** → **Effective routes**

The same VM can show a BGP route similar to:

```text
Source   Address Prefix   Next Hop Type       Next Hop IP
-------  ---------------  ------------------  -----------
BGP      0.0.0.0/0        Virtual appliance   10.0.2.4
Default  0.0.0.0/0        Internet            -
```

Conceptually, the BGP route is winning even though the route-table resource is empty.

CLI verification:

```cli
az network nic show-effective-route-table \
  --resource-group '<RESOURCE_GROUP>' \
  --name '<SPOKE_VM_NIC>' \
  -o table
```

This is one of the most important Route Server troubleshooting commands because it shows the merged result actually presented to the Azure dataplane for the NIC.

---

## 5. How UDRs, BGP routes, and system routes interact

![Effective route selection](images/09-05-26-13-55_ars_effective_route_selection_example.svg)

[Editable draw.io](images/09-05-26-13-55_ars_effective_route_selection_example.drawio)

**What this image shows:** System routes, ARS/BGP routes, and UDRs all contribute candidates to the effective route decision.

**What matters:** First compare prefix length. Then, for equal prefixes, apply Azure route-source precedence and special-case behavior.

**What to verify:** Use Network Watcher **Next hop** for one exact destination.

### Example candidate routes

System routes:

```text
10.20.0.0/16      -> Virtual network
0.0.0.0/0         -> Internet
```

NVA routes learned through ARS:

```text
0.0.0.0/0         -> NVA-1 10.0.2.4
10.100.0.0/16     -> NVA-1 10.0.2.4
```

Optional UDRs:

```text
203.0.113.0/24    -> Internet
10.100.10.0/24    -> NVA-2 10.0.2.5
```

Now evaluate several destinations.

### Destination `8.8.8.8`

Matches:

```text
0.0.0.0/0 system Internet
0.0.0.0/0 BGP NVA-1
```

Normal result: BGP `0/0` toward NVA-1 wins over the ordinary system default.

### Destination `10.100.50.25`

Matches:

```text
10.100.0.0/16 BGP -> NVA-1
0.0.0.0/0 BGP -> NVA-1
```

Longest-prefix match selects `/16`.

### Destination `10.100.10.50`

Matches:

```text
10.100.10.0/24 UDR -> NVA-2
10.100.0.0/16 BGP -> NVA-1
0.0.0.0/0 BGP -> NVA-1
```

Longest-prefix match selects the `/24` UDR, so NVA-2 wins.

### Destination `203.0.113.25`

Matches:

```text
203.0.113.0/24 UDR -> Internet
0.0.0.0/0 BGP -> NVA-1
```

The `/24` UDR is more specific, so it can serve as an explicit bypass exception.

### Why this is useful

You can build a mostly dynamic ARS/BGP design and retain small UDR route tables only for specific exceptions.

---

## 6. Why Route Server does not eliminate every UDR

Microsoft explicitly documents a major limitation: Route Server BGP cannot force traffic **between subnets in the same VNet** through an NVA because Azure system routing for that VNet traffic is preferred in that case.

Therefore:

- **Spoke A VNet → Spoke B VNet:** ARS/BGP can be an effective service-insertion method.
- **Subnet A → Subnet B inside the same VNet:** use UDRs or a supported load-balancing/service architecture if forced inspection is required.

This is why designs that claim "Route Server replaces all UDRs" are incomplete.

---

## 7. East-West service insertion between separate spoke VNets

![East-West service insertion](images/09-05-26-13-55_ars_nva_east_west_service_insertion.svg)

[Editable draw.io](images/09-05-26-13-55_ars_nva_east_west_service_insertion.drawio)

Example:

```text
Spoke A: 10.10.0.0/16
Spoke B: 10.20.0.0/16
NVA-1:   10.0.2.4
NVA-2:   10.0.2.5
```

The NVA may advertise a private inspection summary or selected spoke destination routes into Route Server.

### Forward direction: Spoke A → Spoke B

1. VM-A sends to `10.20.1.10`.
2. Azure checks VM-A NIC effective routes.
3. The winning NVA-learned route selects the firewall next hop.
4. Packet travels directly to the NVA.
5. NVA applies policy/session state.
6. NVA route lookup points toward Spoke B.
7. Packet reaches VM-B.

### Return direction: Spoke B → Spoke A

The destination VM performs a separate route lookup for the return packet. That route must also steer the flow through the inspection design.

Stateful symmetry must be considered separately from simple IP reachability.

---

## 8. Internet egress with an NVA-advertised default route

![Internet egress](images/09-05-26-13-55_ars_nva_internet_egress.svg)

[Editable draw.io](images/09-05-26-13-55_ars_nva_internet_egress.drawio)

The NVA advertises:

```text
0.0.0.0/0
```

Route Server learns and distributes it into eligible VM effective routes.

### Outbound path

```text
Spoke VM
  -> effective route 0/0 points to NVA
  -> NVA inspection
  -> SNAT if required by vendor/HA architecture
  -> internet
```

### Return path

```text
Internet response
  -> NVA public/SNAT path
  -> correct state/NAT entry
  -> spoke destination
```

### Important NVA self-route issue

Microsoft documents a subtle case: if the NVA advertises `0.0.0.0/0`, Route Server can program that default for VMs in the VNet, including the NVA itself. This can cause the appliance to resolve its own internet-bound traffic back toward itself.

The documented remediation is to use a suitable UDR on the NVA subnet to override the learned default for the NVA's required management/egress path.

This is a perfect example of BGP effective routes and UDRs intentionally coexisting.

---

## 9. Dynamic withdrawal and failover: why BGP changes operations

Suppose the spoke currently has:

```text
0.0.0.0/0 -> NVA-1  [BGP]
```

If NVA-1 withdraws that route or the BGP session fails:

1. Route Server removes the learned path.
2. Azure recomputes effective routes for affected workloads.
3. If NVA-2 advertises an equal or backup path, that path can become active.
4. If no firewall default remains, another applicable route can become the winner, depending on the design.

Contrast that with a static UDR:

```text
0.0.0.0/0 -> 10.0.2.4
```

A static UDR does not magically rewrite itself because the firewall's BGP session failed. It remains configured until an operator or automation system changes it, or until a load-balancer architecture provides a stable next hop.

This is one of the biggest operational advantages of dynamic service insertion: **the route lifecycle can follow BGP reachability instead of requiring per-spoke route-table API changes.**

---

## 10. Active/active versus active/standby NVAs

![HA and failover](images/09-05-26-13-55_ars_nva_ha_failover.svg)

[Editable draw.io](images/09-05-26-13-55_ars_nva_ha_failover.drawio)

### Active/active

Both NVAs advertise the same prefix with equally preferred BGP attributes.

Possible result:

```text
0.0.0.0/0 -> NVA-1
0.0.0.0/0 -> NVA-2
```

Azure can use equal-cost multipath (ECMP) for flows.

For a stateful firewall, this is not automatically safe. You must validate:

- vendor HA architecture,
- session synchronization,
- SNAT design,
- whether both directions of a flow land on compatible state,
- whether the vendor explicitly supports the Route Server topology.

### Active/standby

A common model is to advertise the same prefix with different AS_PATH lengths.

Conceptually:

```text
NVA-1: 0.0.0.0/0   AS_PATH 65001
NVA-2: 0.0.0.0/0   AS_PATH 65002 65002 65002
```

The shorter path is preferred. The standby path remains available after withdrawal/failure of the primary path.

Microsoft documents Route Server default keepalive/hold timers of 60/180 seconds, although BGP can negotiate lower values with a peer. Aggressive timers should be validated carefully.

---

## 11. Hybrid route exchange with ExpressRoute or VPN

![Hybrid branch-to-branch](images/09-05-26-13-55_ars_nva_hybrid_branch_to_branch.svg)

[Editable draw.io](images/09-05-26-13-55_ars_nva_hybrid_branch_to_branch.drawio)

Route Server can sit in the same hub as:

- ExpressRoute gateway,
- VPN gateway,
- SD-WAN NVA,
- firewall NVA.

However, NVA ↔ gateway route exchange is not automatically enabled in every design. Microsoft documents **branch-to-branch** route exchange for this purpose.

Enable it:

```cli
az network routeserver update \
  --name '<ROUTE_SERVER_NAME>' \
  --resource-group '<RESOURCE_GROUP>' \
  --allow-b2b-traffic true
```

Then verify which prefixes are being learned and propagated in both directions.

### Routing preference

Route Server supports hub routing preference settings such as:

- **ExpressRoute** — default preference behavior,
- **VPN**,
- **ASPath**.

Example:

```cli
az network routeserver update \
  --name '<ROUTE_SERVER_NAME>' \
  --resource-group '<RESOURCE_GROUP>' \
  --hub-routing-preference 'ASPath'
```

This matters when the same destination is reachable through ExpressRoute, VPN, or SD-WAN/NVA paths.

---

## 12. Route maps and BGP policy

**Source information:** Azure Route Server route maps are currently a **Preview** feature.

Inbound route maps act as Route Server learns routes. Outbound route maps act as Route Server advertises routes.

Common uses:

- Drop unwanted prefixes.
- Aggregate routes.
- Modify AS_PATH.
- Add or manipulate BGP communities.
- Control which routes move between NVA/gateway domains.

If an inbound route map drops a prefix, Route Server can stop accepting/propagating it even though the NVA continues to advertise it.

Microsoft also documents the BGP `NO_ADVERTISE` community:

```text
65535:65282
```

Use policy carefully to avoid route leaks and inspection bypass.

---

## 13. Route Server deployment requirements that affect this design

Important items from current Microsoft documentation include:

- Dedicated subnet named `RouteServerSubnet`.
- Minimum subnet size currently documented as `/26`.
- Do not associate a UDR with `RouteServerSubnet`.
- Do not associate an NSG with `RouteServerSubnet`.
- Route Server ASN is `65515`.
- NVA must use a different supported ASN.
- NVA must support eBGP multihop because the peer is in another subnet.
- Peer the NVA with both Route Server instance IPs.

Retrieve Route Server details:

```cli
az network routeserver show \
  --name '<ROUTE_SERVER_NAME>' \
  --resource-group '<RESOURCE_GROUP>'
```

Typical output contains:

```text
virtualRouterAsn: 65515
virtualRouterIps:
  - <ARS_IP_1>
  - <ARS_IP_2>
```

---

## 14. Current scale considerations

Use the current Azure Route Server FAQ as the source of truth for deployment limits. At the time of this update, Microsoft documents values including:

| Item | Current documented value |
|---|---:|
| BGP peers per Route Server | 16 |
| Routes accepted from one BGP peer | 4,000 |
| Supported VNets | 500 |
| VMs across VNet + peered VNets | 50,000 |
| Total on-prem + Azure VNet prefixes | 10,000 |

Validate these again before production design because service limits can change.

---

## 15. Full verification chain — prove each control-plane stage

Do not jump directly to packet capture. Prove the route hop by hop.

### Check 1 — Did the NVA originate the route?

On the NVA, verify:

- BGP peer state to both Route Server IPs,
- local BGP RIB,
- neighbor advertised-routes,
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

If the route is missing here, do not troubleshoot the spoke yet. Fix the NVA/ARS control plane first.

### Check 3 — What is Route Server advertising back to the NVA?

```cli
az network routeserver peering list-advertised-routes \
  -g '<RESOURCE_GROUP>' \
  --routeserver '<ROUTE_SERVER_NAME>' \
  -n '<PEER_NAME>' \
  -o table
```

Use this to prove the NVA is receiving the Azure/spoke prefixes it needs for return forwarding.

### Check 4 — Is the spoke configured to use the remote Route Server?

For the ordinary centralized hub model, inspect the **spoke → hub** VNet peering and confirm **Use the remote virtual network's gateway or Route Server** is enabled as required by the topology.

### Check 5 — Did the route reach the VM NIC?

```cli
az network nic show-effective-route-table \
  -g '<RESOURCE_GROUP>' \
  -n '<NIC_NAME>' \
  -o table
```

This is the decisive check for route injection.

### Check 6 — Which route wins for one exact destination?

Use Azure Network Watcher **Next hop**.

The portal workflow is:

1. Open **Network Watcher**.
2. Select **Next hop**.
3. Select source VM and NIC.
4. Enter source and destination IPs.
5. Run the test.

This answers the practical question:

> For this exact packet destination, which next hop will Azure use?

### Check 7 — Does the NVA actually receive and forward the packet?

Now verify dataplane state:

- packet capture on NVA ingress,
- firewall policy hit counter,
- session table,
- NAT translation,
- route lookup/FIB,
- packet capture on NVA egress,
- HA/session synchronization state.

If the packet reaches the NVA, Route Server has already done its control-plane job.

---

## 16. Symptom-based troubleshooting

### Symptom: BGP is up, but the spoke VM does not show the NVA route

Check in this order:

1. `list-learned-routes` on Route Server.
2. Spoke ↔ hub peering state.
3. Remote gateway/Route Server peering option.
4. Route-map filtering.
5. Whether the route is valid and accepted.
6. VM NIC effective routes.
7. Competing more-specific routes.

### Symptom: The Route Table blade is empty, so I think Route Server failed

That conclusion is incorrect. The route-table blade shows UDR configuration, not all effective routing state.

Check the VM NIC **Effective routes** instead.

### Symptom: Route Server learned `0/0`, but internet traffic still does not work

Check:

- whether the VM NIC actually received `0/0`,
- whether that BGP route is the winner,
- NVA IP forwarding,
- NVA egress route,
- SNAT,
- firewall policy,
- return path.

### Symptom: Traffic reaches the firewall in one direction only

Compare the **destination-side** NIC effective routes. Routing is evaluated independently in each direction.

Also verify active/active session symmetry and NAT.

### Symptom: Same-VNet subnet-to-subnet traffic bypasses the firewall

Expected if you are relying only on Route Server/BGP. Use a UDR or supported load-balancer architecture for forced same-VNet inspection.

### Symptom: NVA loses internet connectivity after advertising `0/0`

Microsoft specifically documents this condition. The NVA can receive the very default route it originated through Route Server's programming behavior.

Use a suitable UDR on the NVA subnet to preserve the appliance's intended management/egress path.

### Symptom: ExpressRoute takes precedence over the firewall/SD-WAN path

Check:

- Route Server hub routing preference,
- prefix specificity,
- AS_PATH,
- branch-to-branch configuration,
- route maps and communities.

### Symptom: Route Server peer drops after a large update

Check route scale. Microsoft currently documents 4,000 routes accepted from a single BGP peer. Summarize or filter where necessary.

---

## 17. Operational comparison: static UDR service insertion vs ARS/BGP service insertion

| Characteristic | Static UDR | ARS/BGP dynamic insertion |
|---|---|---|
| Route stored in Azure Route Table resource | Yes | No |
| Route appears in NIC effective routes | Yes | Yes |
| Requires BGP on NVA | No | Yes |
| Route can withdraw when BGP path disappears | No | Yes |
| Per-spoke route-table maintenance | Often | Reduced in suitable topologies |
| Same-VNet forced inspection | Strong fit | BGP alone not sufficient |
| HA next-hop change | Usually automation/LB/API needed | Can follow BGP path changes |
| Policy exceptions | UDR-specific | Can mix UDRs with BGP/route maps |
| Stateful symmetry still required | Yes | Yes |

---

## 18. Short packet walk-throughs

### Internet packet

```text
VM 10.20.1.10 -> 8.8.8.8

1. Guest sends packet to Azure virtual NIC.
2. Azure SDN evaluates effective routes.
3. BGP 0/0 learned from NVA beats ordinary system 0/0.
4. Azure sends packet directly to 10.0.2.4.
5. NVA inspects/NATs/routes.
6. Packet exits toward internet.
7. Return traffic must return through compatible NVA state.
```

### Private branch packet

```text
VM 10.20.1.10 -> 10.100.50.10

1. NVA advertised 10.100.0.0/16 to ARS.
2. ARS propagated that route to the spoke effective table.
3. /16 is more specific than any default route.
4. Azure sends packet to NVA.
5. NVA forwards toward SD-WAN/VPN/ER path according to its own routing.
```

### UDR exception packet

```text
VM 10.20.1.10 -> 203.0.113.25

BGP: 0.0.0.0/0 -> NVA
UDR: 203.0.113.0/24 -> Internet

Result:
/24 wins by longest-prefix match, so the explicit UDR exception bypasses the NVA default.
```

---

## 19. Final mental model

When someone asks, **"How does the NVA update the spoke route table?"**, the precise answer is:

> It usually **does not update the Azure Route Table resource at all**. The NVA sends BGP advertisements to Azure Route Server. Route Server learns those routes and Azure's SDN control plane propagates eligible routes into the **effective routing tables of VM NICs** in the hub and peered spokes. Azure then merges those BGP routes with system routes and any UDRs, performs longest-prefix and route-source selection, and sends traffic directly to the NVA when the NVA route wins.

The easiest way to prove this experimentally is:

1. Leave the spoke Route Table resource empty.
2. Advertise `0.0.0.0/0` from the NVA to Route Server.
3. Verify ARS learned the route.
4. Verify the spoke VM NIC now shows a BGP default to the NVA.
5. Run Network Watcher Next Hop for `8.8.8.8`.
6. Withdraw the NVA default.
7. Watch the BGP route disappear from the VM NIC effective routes without any UDR object being edited.

That lab exposes the complete mechanism better than almost any static diagram.

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
- https://learn.microsoft.com/en-us/azure/architecture/example-scenario/firewalls/

### Source classification

**Source information:** Microsoft Learn / Azure Architecture Center statements about Route Server route injection, effective routes, BGP behavior, peering requirements, route maps, limits, and troubleshooting.

**Additional explanation:** The step-by-step packet/routing walk-throughs, comparison tables, and operational sequencing connect those documented behaviors into a network-engineering mental model.

**Reasonable inference:** Design recommendations such as using BGP for route lifecycle reduction and UDRs as an exception layer are explicitly framed as architecture guidance rather than undocumented Azure behavior.
