## 22. ExpressRoute + Route Server + NVA in detail

### 22.1 Where ExpressRoute actually terminates

**Source information:** An ExpressRoute circuit does **not** terminate on Azure Route Server and does **not** terminate on the third-party NVA. At the Microsoft edge, private peering is established with Microsoft Enterprise Edge (MSEE). The circuit is attached to the Azure virtual network through an **ExpressRoute virtual network gateway** deployed in the hub VNet's `GatewaySubnet`.

For the Route Server integration described here, the **ExpressRoute gateway and Azure Route Server must be in the same VNet**. The NVA establishes BGP to Route Server separately.

```text
On-premises CE/WAN
      |
      | ExpressRoute private peering
      v
Provider / Microsoft Enterprise Edge (MSEE)
      |
      v
ExpressRoute circuit
      |
      v
ExpressRoute virtual network gateway
in HUB GatewaySubnet
```

So the clean answer to **"where does ExpressRoute terminate?"** is:

> The ExpressRoute circuit's Azure VNet attachment terminates at the **ExpressRoute virtual network gateway in `GatewaySubnet`**. Route Server is the route-exchange control plane, and the NVA is the inspection/forwarding data plane.

![ExpressRoute termination and Route Server flow](images/09-05-26-13-55_ars_expressroute_termination_flow.svg)

[Editable draw.io](images/09-05-26-13-55_ars_expressroute_termination_flow.drawio)

**What this image shows:** The physical/logical ExpressRoute path ends at the ExpressRoute gateway, while Route Server exchanges routing information between the gateway and the NVA.

**What matters:** Do not configure the NVA as if it were the ExpressRoute circuit endpoint. Its job is to learn/advertise routes through Route Server and forward traffic only when Azure selects it as the next hop.

**What to verify:** ExpressRoute private peering/circuit state, ExpressRoute gateway connection, Route Server branch-to-branch setting, NVA BGP sessions, and effective routes on spokes.

### 22.2 Required placement

A common supported topology is:

```text
HUB VNet 10.0.0.0/16
 |
 |-- GatewaySubnet
 |     ExpressRoute Gateway
 |
 |-- RouteServerSubnet
 |     Azure Route Server
 |
 |-- NVA subnet
 |     Firewall / SD-WAN NVA
 |
 +-- peering --> Spoke-A
 +-- peering --> Spoke-B
```

For **ExpressRoute Gateway ↔ Route Server route exchange**, both managed services must be in the **same hub VNet**. The NVA can be in the hub or in a supported reachable peered-VNet design, but the simplest architecture places it in the same hub.

### 22.3 Three separate control-plane relationships

Keep these independent:

```text
1. On-premises ↔ MSEE / ExpressRoute
   BGP on ExpressRoute private peering

2. ExpressRoute Gateway ↔ Azure Route Server
   Azure-managed route exchange
   No manual ARS BGP peer object is created for the gateway

3. NVA ↔ Azure Route Server
   Customer-configured eBGP multihop
   NVA peers to both ARS IPs
```

By default Route Server does **not** propagate routes between the NVA and the ExpressRoute gateway. Enable **branch-to-branch**:

```cli
az network routeserver update \
  --name '<ROUTE_SERVER_NAME>' \
  --resource-group '<RESOURCE_GROUP>' \
  --allow-b2b-traffic true
```

After that, Route Server can share:

```text
ExpressRoute/on-prem prefixes -> NVA
NVA/SD-WAN prefixes           -> ExpressRoute Gateway
```

This is useful when the NVA has additional branch networks, an SD-WAN fabric, or security/service routes that must be reachable from ExpressRoute-connected sites.

### 22.4 Example route exchange

Assume:

```text
On-prem over ExpressRoute: 10.100.0.0/16
SD-WAN behind NVA:         10.200.0.0/16
Azure spoke:               10.20.0.0/16
```

Before branch-to-branch:

```text
NVA knows Azure routes from ARS, but does not automatically receive ER-gateway routes.
ER gateway knows its ExpressRoute/on-prem routes, but does not automatically receive NVA-learned branch routes.
```

After branch-to-branch:

```text
ExpressRoute Gateway -> ARS -> NVA
  10.100.0.0/16

NVA -> ARS -> ExpressRoute Gateway
  10.200.0.0/16
```

The ExpressRoute gateway can then advertise eligible NVA-originated prefixes toward on-premises through ExpressRoute.

### 22.5 Spoke -> on-premises flow when the NVA is intended to inspect

Suppose the spoke VM is `10.20.1.10` and on-premises destination is `10.100.10.10`.

The critical question is **which route wins on the spoke**.

A spoke can simultaneously have:

```text
10.100.0.0/16 -> ExpressRoute gateway path
0.0.0.0/0     -> NVA 10.0.2.4
```

Longest-prefix match picks `10.100.0.0/16`, so the packet can go directly toward ExpressRoute and **bypass the NVA**.

This is why an NVA-advertised default route alone is not sufficient to force inspection of known on-premises prefixes.

Microsoft documents techniques such as controlling gateway-route propagation in spoke route tables and using explicit UDR/service-insertion policy when hybrid traffic must be inspected. Route maps can also control Route Server route exchange, but Route Server route maps are currently Preview.

### 22.6 On-premises -> spoke flow

Without deliberate inspection steering, the natural path is:

```text
On-premises
 -> ExpressRoute circuit
 -> ExpressRoute Gateway
 -> Azure routing / peering
 -> Spoke VM
```

If the NVA must inspect that traffic, the **gateway-to-spoke direction must also be steered through the NVA**. Branch-to-branch merely gives the gateway and NVA knowledge of each other's routes; it does not automatically force the packet through the NVA.

![ExpressRoute inspection caveat](images/09-05-26-13-55_ars_expressroute_inspection_caveat.svg)

[Editable draw.io](images/09-05-26-13-55_ars_expressroute_inspection_caveat.drawio)

**What this image shows:** ExpressRoute can have a direct route to a spoke while Route Server simultaneously exchanges routes with the NVA.

**What matters:** **Route exchange is not service chaining.** The winning route must point to the NVA in both directions for a stateful firewall to inspect the session.

**What to verify:** Gateway-learned prefix specificity, spoke effective routes, any route-table propagation settings, Route Server hub routing preference, NVA routes, and Network Watcher Next Hop.

### 22.7 ExpressRoute versus NVA route preference

When Route Server learns the same prefix from ExpressRoute and an NVA/SD-WAN path, the default hub routing preference is **ExpressRoute**.

Available Route Server preferences are:

```text
ExpressRoute   (default)
VpnGateway
ASPath
```

Example:

```cli
az network routeserver update \
  --name '<ROUTE_SERVER_NAME>' \
  --resource-group '<RESOURCE_GROUP>' \
  --hub-routing-preference 'ASPath'
```

With `ASPath`, Route Server compares AS-path length regardless of whether the route came from ExpressRoute, VPN, or NVA. With `VpnGateway`, VPN Gateway and NVA routes are favored over ExpressRoute; if the same route is learned from VPN Gateway and NVA, the shorter AS path is used between those sources.

### 22.8 ExpressRoute AS-path nuance

Route Server preserves AS_PATH when it learns routes from the NVA. However, when ExpressRoute advertises NVA-originated routes to on-premises, Microsoft documents that private ASN information is removed and on-premises sees the Azure ExpressRoute ASN `12076` for the advertised prefix. Do not assume NVA private-AS prepends will remain visible end-to-end through ExpressRoute.

### 22.9 ExpressRoute design checklist

- ExpressRoute circuit and private peering operational.
- ExpressRoute virtual network gateway deployed in `GatewaySubnet`.
- ExpressRoute gateway and Route Server in the same hub VNet.
- NVA BGP established to both Route Server IPs.
- Branch-to-branch enabled if ER gateway and NVA must exchange routes.
- Hub routing preference selected intentionally.
- Spoke peering configured to consume the hub gateway/Route Server as required.
- Route specificity checked for every inspected on-prem prefix.
- Stateful forward and return paths both verified through the same compatible NVA state.
- `NO_ADVERTISE` or route maps used where route leakage must be prevented.
- Do not use ExpressRoute-to-ExpressRoute connectivity through Route Server; Microsoft directs that use case to ExpressRoute Global Reach.

---

## 23. VPN Gateway + Route Server + NVA in detail

### 23.1 Where the VPN terminates

The Site-to-Site (S2S) IPsec/IKE tunnel terminates on the **Azure VPN Gateway** deployed in the hub VNet's `GatewaySubnet`.

It does not terminate on Route Server.

```text
On-premises VPN device
      |
      | IPsec/IKE S2S tunnel
      v
Azure VPN Gateway public IP(s)
      |
      | GatewaySubnet
      v
Hub VNet
```

With active-active VPN Gateway, both gateway instances have public IPs and can establish tunnels to the on-premises VPN device.

### 23.2 Special Route Server requirements for VPN Gateway

Microsoft documents two specific requirements for Azure VPN Gateway to work with Azure Route Server:

```text
VPN Gateway mode: Active-active
VPN Gateway ASN:  65515
```

The VPN Gateway must be in the **same VNet** as Route Server for this managed route-exchange integration.

Important nuance:

> BGP does **not** have to be enabled on the Azure VPN Gateway merely for VPN Gateway ↔ Route Server communication.

If the S2S VPN itself uses BGP, the VPN Gateway learns on-premises prefixes dynamically. If BGP is not enabled on the S2S connection, the gateway learns remote prefixes from the **Local Network Gateway address-space definitions**. In either case, Route Server can advertise gateway-learned routes when branch-to-branch is enabled.

![VPN Gateway Route Server NVA flow](images/09-05-26-13-55_ars_vpn_gateway_flow.svg)

[Editable draw.io](images/09-05-26-13-55_ars_vpn_gateway_flow.drawio)

**What this image shows:** The IPsec tunnel ends on VPN Gateway, while Route Server exchanges VPN-gateway routes with the NVA and propagates eligible paths to spokes.

**What matters:** The NVA's BGP session is with Route Server, not with Azure VPN Gateway. The VPN Gateway ↔ Route Server relationship is Azure-managed.

**What to verify:** Active-active mode, ASN 65515, S2S tunnel state, branch-to-branch, NVA BGP, and spoke effective routes.

### 23.3 Control-plane sequence with BGP-enabled S2S VPN

Example:

```text
On-premises: 10.50.0.0/16
On-prem BGP ASN: 65050
Azure VPN Gateway ASN: 65515
NVA ASN: 65001
Spoke: 10.20.0.0/16
```

The route-learning sequence is:

```text
On-prem router
  -> BGP across IPsec tunnel
Azure VPN Gateway
  -> managed route exchange
Azure Route Server
  -> eBGP
NVA
```

In the opposite direction, NVA-originated branch/service prefixes can flow:

```text
NVA
  -> BGP
Route Server
  -> managed route exchange
VPN Gateway
  -> BGP across S2S tunnel
On-premises
```

### 23.4 Control-plane sequence without BGP on the S2S VPN

The Route Server integration still works, but the source of the on-premises routes changes:

```text
Local Network Gateway configured address spaces
  -> Azure VPN Gateway routing state
  -> Route Server
  -> NVA / eligible Azure routing
```

Topology changes on-premises are not dynamically learned in this mode; you must update the Local Network Gateway address-space configuration when prefixes change.

### 23.5 Branch-to-branch is still required

Without branch-to-branch:

```text
NVA <-> Route Server              works
VPN Gateway <-> Route Server      works
NVA routes <-> VPN Gateway routes are NOT propagated to each other
```

Enable it:

```cli
az network routeserver update \
  --name '<ROUTE_SERVER_NAME>' \
  --resource-group '<RESOURCE_GROUP>' \
  --allow-b2b-traffic true
```

After enabling it, the NVA can learn VPN-connected prefixes and the VPN Gateway can learn eligible NVA-originated prefixes through Route Server.

### 23.6 Spoke -> VPN-connected on-premises flow

Assume:

```text
Spoke VM: 10.20.1.10
On-prem:  10.50.10.10
```

If the spoke learns a specific VPN-gateway route:

```text
10.50.0.0/16 -> VPN Gateway
```

and the NVA advertises only:

```text
0.0.0.0/0 -> NVA
```

then `/16` wins over `/0`, and the packet can bypass the NVA.

Therefore, just as with ExpressRoute, **route sharing through Route Server does not automatically force VPN traffic through a firewall NVA**.

If inspection is mandatory, control route propagation/UDRs or otherwise ensure the NVA path is the selected route in both directions.

### 23.7 VPN-connected on-premises -> spoke flow

The natural path is:

```text
On-premises
 -> IPsec tunnel
 -> Azure VPN Gateway
 -> Azure routing
 -> Spoke
```

For firewall inspection, the VPN-gateway-to-spoke routing decision must select the NVA as the next hop before delivery to the spoke. Verify the return direction separately because stateful appliances require compatible symmetry.

### 23.8 Active-active impact

Active-active VPN Gateway means both Azure gateway instances can establish S2S tunnels. Your on-premises VPN device must be prepared for both gateway public IPs/tunnels if you want the full active-active design.

This gateway redundancy is separate from NVA redundancy:

```text
VPN Gateway HA  = tunnel/gateway availability
NVA HA          = firewall/session/inspection availability
Route Server HA = managed route-control-plane availability
```

All three failure domains should be tested independently.

### 23.9 If ExpressRoute and VPN coexist

When the same prefix exists through ExpressRoute and VPN, Route Server's default preference is **ExpressRoute**. You can change the hub routing preference to `VpnGateway` or `ASPath` where the design calls for it.

Remember that `VpnGateway` preference groups VPN Gateway and NVA routes ahead of ExpressRoute; it does not inherently distinguish VPN Gateway from NVA. When the same route is learned from VPN and NVA under that preference, shortest AS path is used between those choices.

### 23.10 VPN Gateway design checklist

- Route-based S2S VPN architecture for advanced/BGP designs.
- Azure VPN Gateway deployed in hub `GatewaySubnet`.
- VPN Gateway and Route Server in the same VNet.
- **Active-active** enabled.
- VPN Gateway ASN set to **65515** for Route Server integration.
- On-premises device configured for both active-active tunnels where required.
- BGP enabled on the S2S connection if dynamic on-prem route exchange is desired; otherwise maintain Local Network Gateway prefixes manually.
- NVA peers to both Route Server BGP IPs.
- Branch-to-branch enabled for VPN Gateway ↔ NVA route exchange.
- Spoke effective routes checked for more-specific VPN prefixes that might bypass an NVA default.
- Hub routing preference intentionally configured when VPN, ExpressRoute, and NVA paths coexist.
- Forward and return traffic tested through the stateful NVA.

### 23.11 ExpressRoute versus VPN Gateway summary

| Item | ExpressRoute | Azure VPN Gateway |
|---|---|---|
| Azure VNet termination | ExpressRoute VNet Gateway in `GatewaySubnet` | VPN Gateway in `GatewaySubnet` |
| Underlay | Private provider/Microsoft connectivity | IPsec/IKE over IP connectivity |
| Same VNet as Route Server for gateway integration | Yes | Yes |
| Manual BGP peer to Route Server | No | No |
| NVA manually peers to Route Server | Yes | Yes |
| Branch-to-branch needed for NVA↔gateway route exchange | Yes | Yes |
| Special gateway mode required by Route Server | Normal supported ER gateway design | **Active-active** |
| Gateway ASN requirement for ARS | Azure-managed behavior | **65515** |
| BGP required on WAN connection | ExpressRoute private peering uses BGP | Optional for S2S; recommended when dynamic route learning is desired |
| Default ARS preference when same prefix also exists elsewhere | **ExpressRoute** | Lower than ExpressRoute by default |
| Route exchange automatically forces firewall inspection | **No** | **No** |

The most important hybrid-routing takeaway is:

> **Route Server makes the ExpressRoute/VPN gateway and the NVA aware of each other's routes. It does not automatically put the NVA inline. Packet inspection still depends on which route wins at every forwarding point in both directions.**
