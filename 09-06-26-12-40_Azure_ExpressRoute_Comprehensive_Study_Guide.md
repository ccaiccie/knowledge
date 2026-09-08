# Azure ExpressRoute — Comprehensive Routing, Multi-Circuit, Virtual WAN, and Route Server Study Guide

> **Scope:** Azure ExpressRoute architecture, circuit models and SKUs, BGP routing, Azure Private Peering and Microsoft Peering, multi-circuit/multi-site load balancing and failover, Virtual WAN integration, Azure Route Server integration, FastPath, Global Reach, configuration, verification, failure behavior, and troubleshooting.
>
> **Validated against current Microsoft documentation:** September 7, 2026.

## Source URLs

Primary Microsoft sources used for this guide:

- https://learn.microsoft.com/azure/expressroute/expressroute-introduction
- https://learn.microsoft.com/azure/expressroute/expressroute-circuit-peerings
- https://learn.microsoft.com/azure/expressroute/expressroute-connectivity-models
- https://learn.microsoft.com/azure/expressroute/expressroute-routing
- https://learn.microsoft.com/azure/expressroute/howto-circuit-cli
- https://learn.microsoft.com/azure/expressroute/howto-routing-cli
- https://learn.microsoft.com/azure/expressroute/expressroute-howto-linkvnet-cli
- https://learn.microsoft.com/azure/expressroute/how-to-routefilter-portal
- https://learn.microsoft.com/azure/expressroute/designing-for-disaster-recovery-with-expressroute-privatepeering
- https://learn.microsoft.com/azure/expressroute/metro
- https://learn.microsoft.com/azure/expressroute/expressroute-erdirect-about
- https://learn.microsoft.com/azure/expressroute/about-fastpath
- https://learn.microsoft.com/azure/expressroute/expressroute-global-reach
- https://learn.microsoft.com/azure/expressroute/expressroute-about-virtual-network-gateways
- https://learn.microsoft.com/azure/virtual-wan/virtual-wan-expressroute-about
- https://learn.microsoft.com/azure/virtual-wan/about-virtual-hub-routing
- https://learn.microsoft.com/azure/route-server/expressroute-vpn-support
- https://learn.microsoft.com/azure/route-server/quickstart-create-route-server-cli
- https://learn.microsoft.com/cli/azure/network/express-route
- https://learn.microsoft.com/cli/azure/network/express-route/peering
- https://learn.microsoft.com/cli/azure/network/express-route/peering/connection
- https://learn.microsoft.com/cli/azure/network/express-route/gateway
- https://learn.microsoft.com/cli/azure/network/express-route/gateway/connection
- https://learn.microsoft.com/cli/azure/network/vnet-gateway
- https://learn.microsoft.com/cli/azure/network/vpn-connection
- https://learn.microsoft.com/cli/azure/network/routeserver
- https://learn.microsoft.com/cli/azure/network/routeserver/peering

## Table of contents

- [1. What ExpressRoute actually is](#1-what-expressroute-actually-is)
  - [1.1 Redundancy inside one circuit](#11-redundancy-inside-one-circuit)
- [2. ExpressRoute connectivity models and types](#2-expressroute-connectivity-models-and-types)
  - [2.1 Connectivity models](#21-connectivity-models)
  - [2.2 Circuit SKU](#22-circuit-sku)
  - [2.3 Billing family](#23-billing-family)
  - [2.4 Provider circuit versus ExpressRoute Direct](#24-provider-circuit-versus-expressroute-direct)
  - [2.5 ExpressRoute Metro](#25-expressroute-metro)
  - [2.6 ExpressRoute Global Reach](#26-expressroute-global-reach)
    - [2.6.1 What Global Reach actually connects](#261-what-global-reach-actually-connects)
    - [2.6.2 Control plane and BGP route exchange](#262-control-plane-and-bgp-route-exchange)
    - [2.6.3 Exact packet flow](#263-exact-packet-flow)
    - [2.6.4 Prerequisites and SKU/geography rules](#264-prerequisites-and-skugeography-rules)
    - [2.6.5 Azure CLI configuration](#265-azure-cli-configuration)
    - [2.6.6 Cross-subscription circuit connection](#266-cross-subscription-circuit-connection)
    - [2.6.7 Three or more circuits and non-transitivity](#267-three-or-more-circuits-and-non-transitivity)
    - [2.6.8 Bandwidth, route scale, and failure behavior](#268-bandwidth-route-scale-and-failure-behavior)
    - [2.6.9 Global Reach versus Route Server and Virtual WAN](#269-global-reach-versus-route-server-and-virtual-wan)
    - [2.6.10 Security and firewall implications](#2610-security-and-firewall-implications)
- [3. Private Peering, Microsoft Peering, and legacy Public Peering](#3-private-peering-microsoft-peering-and-legacy-public-peering)
  - [3.1 Azure Private Peering](#31-azure-private-peering)
  - [3.2 Microsoft Peering](#32-microsoft-peering)
  - [3.3 Azure CLI — Microsoft Peering](#33-azure-cli--microsoft-peering)
  - [3.4 Azure CLI — route filter for Microsoft Peering](#34-azure-cli--route-filter-for-microsoft-peering)
- [4. BGP mechanics you must understand](#4-bgp-mechanics-you-must-understand)
- [5. ExpressRoute to a customer-managed VNet](#5-expressroute-to-a-customer-managed-vnet)
  - [5.1 Control plane](#51-control-plane)
  - [5.2 Data plane](#52-data-plane)
  - [5.3 Azure CLI — create the ExpressRoute VNet gateway](#53-azure-cli--create-the-expressroute-vnet-gateway)
  - [5.4 Azure CLI — connect the VNet gateway to the circuit](#54-azure-cli--connect-the-vnet-gateway-to-the-circuit)
  - [5.5 Azure CLI — cross-subscription authorization](#55-azure-cli--cross-subscription-authorization)
  - [5.6 FastPath](#56-fastpath)
- [6. Multi-location, multi-circuit design](#6-multi-location-multi-circuit-design)
  - [6.1 Active/active ECMP](#61-activeactive-ecmp)
  - [6.2 Active/standby](#62-activestandby)
  - [6.3 Azure CLI — attach two circuits and set connection weights](#63-azure-cli--attach-two-circuits-and-set-connection-weights)
  - [6.4 Failure sequence and capacity](#64-failure-sequence-and-capacity)
- [7. ExpressRoute with Azure Virtual WAN](#7-expressroute-with-azure-virtual-wan)
  - [7.1 vHub route-table model](#71-vhub-route-table-model)
  - [7.2 Azure CLI — vWAN ExpressRoute gateway and connection](#72-azure-cli--vwan-expressroute-gateway-and-connection)
- [8. ExpressRoute with Azure Route Server and SD-WAN](#8-expressroute-with-azure-route-server-and-sd-wan)
  - [8.1 Branch-to-branch route exchange](#81-branch-to-branch-route-exchange)
  - [8.2 Azure CLI — Route Server integration](#82-azure-cli--route-server-integration)
  - [8.3 Vendor integration models](#83-vendor-integration-models)
- [9. Packet-flow examples](#9-packet-flow-examples)
- [10. Azure CLI — provider circuit and Private Peering](#10-azure-cli--provider-circuit-and-private-peering)
- [11. Azure CLI — Global Reach](#11-azure-cli--global-reach)
- [12. Azure CLI — hub/spoke gateway transit](#12-azure-cli--hubspoke-gateway-transit)
- [13. Multi-circuit BGP policy examples](#13-multi-circuit-bgp-policy-examples)
- [14. Connection weight versus AS-path prepending](#14-connection-weight-versus-as-path-prepending)
- [15. Security and firewall insertion](#15-security-and-firewall-insertion)
- [16. High-availability hierarchy](#16-high-availability-hierarchy)
- [17. Verification checklist](#17-verification-checklist)
  - [17.1 Circuit and peering](#171-circuit-and-peering)
  - [17.2 Traditional VNet gateway connection](#172-traditional-vnet-gateway-connection)
  - [17.3 Gateway resiliency and route information](#173-gateway-resiliency-and-route-information)
  - [17.4 Virtual WAN](#174-virtual-wan)
  - [17.5 Route Server](#175-route-server)
  - [17.6 Global Reach](#176-global-reach)
- [18. Troubleshooting by symptom](#18-troubleshooting-by-symptom)
- [19. Common mistakes](#19-common-mistakes)
- [20. Design recommendations](#20-design-recommendations)
- [21. Decision table](#21-decision-table)
- [22. Final mental model](#22-final-mental-model)
- [Sources](#sources)

---

## 1. What ExpressRoute actually is

**Source information:** Azure ExpressRoute provides private Layer-3 connectivity from a customer network to Microsoft through a connectivity provider, exchange, or ExpressRoute Direct. Dynamic route exchange uses external Border Gateway Protocol (**eBGP**). Microsoft uses autonomous system (**AS**) 12076 on ExpressRoute Private and Microsoft peerings.

ExpressRoute has three different layers that are often incorrectly collapsed into one concept:

1. **Physical/provider connectivity** — how your router reaches the Microsoft Enterprise Edge (**MSEE**) routers at an ExpressRoute peering location.
2. **ExpressRoute circuit** — a logical Azure resource with a service key and purchased bandwidth.
3. **Peering/routing domain** — BGP routing carried over the circuit:
   - **Azure Private Peering** for private VNet connectivity.
   - **Microsoft Peering** for supported Microsoft public services.

A circuit is therefore not equivalent to one cable and is not equivalent to one BGP neighbor.

### 1.1 Redundancy inside one circuit

Every ExpressRoute peering is designed around **two independent BGP sessions**, one to each MSEE. Microsoft requires both sessions for the availability design/SLA requirements.

For IPv4 Private Peering, allocate either one `/29` split into two `/30`s or two independent `/30`s.

| Link | Subnet | Customer/PE | Microsoft MSEE |
|---|---|---:|---:|
| Primary | `192.168.100.128/30` | `192.168.100.129` | `192.168.100.130` |
| Secondary | `192.168.100.132/30` | `192.168.100.133` | `192.168.100.134` |

Microsoft does **not** rely on HSRP or VRRP between your routers and MSEE. High availability is BGP-based.

![ExpressRoute circuit anatomy](images/09-06-26-12-40_expressroute_circuit_anatomy.svg)

[Download/edit the matching draw.io source](images/09-06-26-12-40_expressroute_circuit_anatomy.drawio)

**What this image shows:** One circuit with redundant primary/secondary provider paths to two MSEEs and separate Private/Microsoft peering routing domains.

**What matters:** One circuit protects against a single MSEE/link failure but both paths still share the same ExpressRoute peering-location failure domain unless you use Metro or a separate geographically diverse circuit.

**What to verify:** Both BGP sessions are established, provider provisioning state is `Provisioned`, and the intended peering is enabled.

---

## 2. ExpressRoute connectivity models and types

### 2.1 Connectivity models

| Model | What it is | Typical use |
|---|---|---|
| Cloud/Ethernet exchange | Virtual cross-connect through an exchange provider | Colocation customers |
| Point-to-point Ethernet | Dedicated Ethernet into an ER peering location | Simple private WAN extension |
| Any-to-any IP VPN | Provider-managed L3 WAN such as MPLS/IP-VPN | Existing carrier WAN integration |
| ExpressRoute Direct | Customer/provider routers connect directly to Microsoft dual ports | High scale, physical isolation, many logical circuits |

To see provider, peering-location, and bandwidth combinations:

```cli
az network express-route list-service-providers --output table
```

### 2.2 Circuit SKU

| SKU | Reach | Key purpose |
|---|---|---|
| **Local** | Local designated Azure region(s) for the peering location | Localized, cost-conscious designs |
| **Standard** | Regions within the geopolitical area | Normal enterprise deployments |
| **Premium** | Global Azure reach plus higher limits | Multinational/global designs |

### 2.3 Billing family

Provider circuits use a billing family such as `MeteredData` or `UnlimitedData` where supported. This affects billing, not BGP route selection.

Microsoft documents that moving from `MeteredData` to `UnlimitedData` is supported, while reversing from Unlimited to Metered is not generally available through the normal workflow. Local circuits use Unlimited Data.

### 2.4 Provider circuit versus ExpressRoute Direct

A provider-backed circuit is created with a provider and peering location. ExpressRoute Direct instead uses a Microsoft-facing ExpressRoute Port resource, and logical circuits reference that port.

Current core CLI exposes both the port resource and the circuit association:

```cli
az network express-route port list --output table
```

```cli
az network express-route create \
  --resource-group RG-Network \
  --name ER-Direct-Circuit-01 \
  --location <azure-resource-location> \
  --express-route-port <express-route-port-name-or-id> \
  --bandwidth 10Gbps \
  --sku-tier Premium \
  --sku-family UnlimitedData
```

**Important:** Do not copy a bandwidth value blindly. It must be valid for the selected Direct resource/circuit configuration.

### 2.5 ExpressRoute Metro

ExpressRoute Metro dual-homes a circuit across **two distinct ExpressRoute peering locations in the same metro**. It reduces the single-peering-location failure domain.

Microsoft's current Metro documentation still directs you to create the circuit using a Metro-supported provider/peering-location combination. Discover the currently offered provider/location combinations first:

```cli
az network express-route list-service-providers --output json
```

Do not invent a Metro location string; use a value returned by Azure for the selected provider.

### 2.6 ExpressRoute Global Reach

**Source information:** ExpressRoute Global Reach links ExpressRoute circuits so that the **on-premises networks behind those circuits can communicate directly over Microsoft's global network**. It is primarily an on-premises-to-on-premises transit feature. It does not require traffic to enter an Azure VNet merely to move between the sites.

A simple mental model is:

```text
Without Global Reach

Site A / LA                    Site B / Dallas
10.10.0.0/16                  10.20.0.0/16
     |                              |
     v                              v
ER Circuit A                    ER Circuit B
     |                              |
     +----> Azure VNets      Azure VNets <----+

No automatic Site A <-> Site B transit
```

With Global Reach:

```text
Site A / LA                    Site B / Dallas
10.10.0.0/16                  10.20.0.0/16
     |                              |
     v                              v
ER Circuit A ==== Global Reach ==== ER Circuit B
               Microsoft backbone
```

The important distinction is:

```text
ExpressRoute Private Peering
    = on-premises <-> Azure private routing domain

ExpressRoute Global Reach
    = on-premises <-> on-premises transit between ER circuits
```

#### 2.6.1 What Global Reach actually connects

Global Reach is represented as an **ExpressRoute circuit connection under Azure Private Peering**. It is not a VNet peering, it is not a Route Server adjacency, and it is not a connection between two ExpressRoute VNet gateways.

Conceptually:

```text
ER Circuit A
  |
  +-- AzurePrivatePeering
          |
          | ExpressRouteCircuitConnection
          | Global Reach
          |
  +-- AzurePrivatePeering
ER Circuit B
```

This means the Global Reach relationship exists at the ExpressRoute circuit/private-peering layer.

You do **not** need the following merely for the basic circuit-to-circuit Global Reach data path:

- Azure Route Server;
- VNet peering;
- a VNet ExpressRoute gateway acting as the transit router;
- a Virtual WAN hub;
- UDRs in an Azure VNet.

Those features can exist in the wider architecture, but they are not what creates the Global Reach circuit relationship.

#### 2.6.2 Control plane and BGP route exchange

Assume:

```text
LA site
  ASN: 65010
  Prefix: 10.10.0.0/16

Dallas site
  ASN: 65020
  Prefix: 10.20.0.0/16
```

LA advertises `10.10.0.0/16` over the Private Peering of Circuit A. Dallas advertises `10.20.0.0/16` over the Private Peering of Circuit B.

After Global Reach is established, the remote on-premises prefixes can be exchanged through the connected circuit relationship, subject to ExpressRoute routing rules and your CE/provider routing policies.

Conceptually:

```text
LA CE
  advertises 10.10.0.0/16
      |
      v
Circuit A Private Peering
      |
      | Global Reach
      v
Circuit B Private Peering
      |
      v
Dallas CE learns 10.10.0.0/16
```

and the reverse direction:

```text
Dallas CE
  advertises 10.20.0.0/16
      |
      v
Circuit B Private Peering
      |
      | Global Reach
      v
Circuit A Private Peering
      |
      v
LA CE learns 10.20.0.0/16
```

**What to verify:** Do not stop at the Azure resource state. On both customer/provider routers, verify that the remote site prefixes are actually present, accepted by policy, and installed in the forwarding table.

#### 2.6.3 Exact packet flow

For this packet:

```text
Source:      10.10.10.25
Destination: 10.20.20.25
```

a representative path is:

```text
10.10.10.25
   |
   v
LA LAN/router
   |
   | route to 10.20.0.0/16 learned through ER
   v
LA CE/provider edge
   |
   | ExpressRoute Private Peering
   v
MSEE / Microsoft edge
   |
   | Global Reach
   | Microsoft backbone
   v
MSEE / Microsoft edge
   |
   | ExpressRoute Private Peering
   v
Dallas CE/provider edge
   |
   v
10.20.20.25
```

The packet does **not** need to traverse:

```text
ER VNet gateway -> Azure VNet -> another ER VNet gateway
```

merely to reach the other on-premises site.

The return flow is the same logical path in reverse, subject to your BGP policy:

```text
10.20.20.25
  -> Dallas ER Circuit B
  -> Global Reach
  -> ER Circuit A
  -> LA
  -> 10.10.10.25
```

#### 2.6.4 Prerequisites and SKU/geography rules

Before creating Global Reach, validate all of the following:

1. Both circuits are provisioned and operational.
2. **Azure Private Peering** is configured on both circuits.
3. The selected ExpressRoute peering locations support Global Reach.
4. Address spaces advertised by the two sites do not create unintended overlap/ambiguity.
5. A dedicated `/29` is available for the Global Reach circuit connection.
6. Customer/provider route policies allow the remote site prefixes.
7. Circuit capacity is sufficient for both Azure-bound traffic and site-to-site traffic.

**SKU/geography:** Microsoft's current Global Reach documentation states that when connecting circuits in **different geopolitical regions**, both circuits must use the **Premium SKU**.

For circuits within the same supported geopolitical region, Premium is not required merely because Global Reach is used; use the SKU that satisfies reach/limit requirements and is supported for the topology.

Global Reach availability is location-dependent. Always validate the current supported-location list before committing to a design.

#### 2.6.5 Azure CLI configuration

Assume:

```text
Circuit A: ER-LA-01
Circuit B: ER-DAL-01
Resource group: RG-Network
Global Reach prefix: 10.254.0.0/29
```

First verify Private Peering on both circuits:

```cli
az network express-route peering show \
  --resource-group RG-Network \
  --circuit-name ER-LA-01 \
  --name AzurePrivatePeering \
  --query '{state:state,provisioning:provisioningState,id:id}' \
  --output json
```

```cli
az network express-route peering show \
  --resource-group RG-Network \
  --circuit-name ER-DAL-01 \
  --name AzurePrivatePeering \
  --query '{state:state,provisioning:provisioningState,id:id}' \
  --output json
```

Retrieve Circuit B's resource ID:

```cli
ER_DAL_ID=$(az network express-route show \
  --resource-group RG-Network \
  --name ER-DAL-01 \
  --query id \
  --output tsv)
```

Create the Global Reach connection from Circuit A's Private Peering:

```cli
az network express-route peering connection create \
  --resource-group RG-Network \
  --circuit-name ER-LA-01 \
  --peering-name AzurePrivatePeering \
  --name GR-LA-to-DAL \
  --peer-circuit "$ER_DAL_ID" \
  --address-prefix 10.254.0.0/29
```

Microsoft's current CLI defines `--address-prefix` as a **`/29` IP address space used to carve out customer addresses for the circuit connection**. Treat it as dedicated Global Reach connection addressing; do not reuse a LAN, VNet, Private Peering `/30`, VPN pool, or overlapping enterprise prefix.

Wait for the connection resource to reach `Succeeded`:

```cli
az network express-route peering connection wait \
  --resource-group RG-Network \
  --circuit-name ER-LA-01 \
  --peering-name AzurePrivatePeering \
  --name GR-LA-to-DAL \
  --created
```

Show the connection:

```cli
az network express-route peering connection show \
  --resource-group RG-Network \
  --circuit-name ER-LA-01 \
  --peering-name AzurePrivatePeering \
  --name GR-LA-to-DAL \
  --output json
```

List every Global Reach connection under the private peering:

```cli
az network express-route peering connection list \
  --resource-group RG-Network \
  --circuit-name ER-LA-01 \
  --peering-name AzurePrivatePeering \
  --output table
```

**Success criteria:**

- Global Reach connection provisioning succeeds;
- the peer circuit reference is correct;
- the `/29` is the intended dedicated connection prefix;
- remote site prefixes are visible on the CE routers;
- bidirectional test traffic follows the expected ExpressRoute paths.

**Failure indicators:**

- Global Reach resource is failed/disconnected;
- peer circuit ID is wrong;
- Private Peering is not operational on one side;
- `/29` overlaps another network;
- remote prefixes are filtered by CE/provider policy;
- sites advertise overlapping prefixes;
- location/SKU combination is unsupported.

#### 2.6.6 Cross-subscription circuit connection

If the peer circuit is in another subscription, the Global Reach CLI supports an **authorization key**.

Microsoft's current command reference exposes:

```text
--authorization-key
```

and defines it as the authorization key used when the peer circuit is in another subscription.

The conceptual workflow is:

```text
Circuit owner in Subscription B
     |
     | grants/creates authorization for the peer circuit relationship
     v
Authorization key
     |
     v
Subscription A creates Global Reach connection
     using --authorization-key
```

When implementing this, use the current Microsoft authorization procedure for the exact ownership model rather than copying a same-subscription command and assuming access is implicit.

#### 2.6.7 Three or more circuits and non-transitivity

Do not design Global Reach as though it were a generic transitive routing mesh.

If you configure:

```text
Circuit A <-> Circuit B
Circuit B <-> Circuit C
```

do **not** assume that this automatically means:

```text
Circuit A <-> Circuit C
```

For a full three-circuit mesh, explicitly create the required pairwise relationships:

```text
A <-> B
A <-> C
B <-> C
```

The number of pairwise relationships grows quickly as circuit count increases. This is one reason Virtual WAN can become operationally cleaner when the problem evolves from a few ER-attached sites into a large multi-connection global transit fabric.

#### 2.6.8 Bandwidth, route scale, and failure behavior

**Bandwidth:** Global Reach does not create new bandwidth. Site-to-Azure and site-to-site traffic share the capacity of the involved ExpressRoute circuits.

Example:

```text
Circuit B capacity:            5 Gbps
Existing Azure traffic:        3 Gbps
New Global Reach traffic:      3 Gbps
                               ------
Total offered load:            6 Gbps
Available circuit capacity:    5 Gbps
```

The result is congestion even though Global Reach itself is configured correctly.

If Circuit A is 10 Gbps and Circuit B is 5 Gbps, the smaller circuit can become the bottleneck for traffic traversing the pair.

**Route scale:** Enabling Global Reach means customer routers can receive remote on-premises prefixes in addition to Azure prefixes. Check both ExpressRoute route limits and the CE's own `maximum-prefix`/FIB capacity.

**Failure behavior:** One ExpressRoute circuit already contains redundant primary and secondary BGP sessions. A single peering-link failure can therefore leave the circuit operational through the surviving session.

But if the **entire circuit or peering location** becomes unavailable, the Global Reach path through that circuit is lost unless you have another independently designed circuit/path.

For mission-critical site-to-site use, combine Global Reach with proper circuit diversity:

- diverse peering locations;
- diverse provider/local-loop infrastructure where possible;
- redundant CE routers;
- BGP policy for alternate paths;
- tested failover capacity.

#### 2.6.9 Global Reach versus Route Server and Virtual WAN

These three features solve different problems.

| Feature | Primary purpose | Packet forwarding role |
|---|---|---|
| **Global Reach** | On-premises site-to-site transit between ExpressRoute circuits | Microsoft backbone carries the site-to-site packets |
| **Azure Route Server** | BGP route exchange between NVAs and supported Azure gateways in a VNet | ARS is control plane only; it does not forward packets |
| **Virtual WAN** | Managed multi-connection transit among VNets, VPN, ExpressRoute, SD-WAN, and security services | vHub routing fabric provides managed transit |

Do not use this incorrect mental model:

```text
ER Circuit A -> Route Server -> ER Circuit B
```

Route Server is not the ER circuit-to-circuit WAN transit feature.

Use Global Reach when the requirement is primarily:

```text
Datacenter A <---- Microsoft backbone ----> Datacenter B
```

Use Virtual WAN when the requirement becomes broader:

```text
ExpressRoute + VPN + SD-WAN + VNets + multiple regions + routing segmentation/security insertion
```

#### 2.6.10 Security and firewall implications

Global Reach provides private backbone transit; it does **not** automatically insert Azure Firewall or a third-party NVA into the circuit-to-circuit path.

The natural Global Reach path is:

```text
Site A
 -> Circuit A
 -> Global Reach / Microsoft backbone
 -> Circuit B
 -> Site B
```

not:

```text
Site A
 -> Circuit A
 -> Azure Firewall
 -> Global Reach
 -> Circuit B
 -> Site B
```

If you need site-to-site traffic inspection, deliberately place stateful security in a path that the routing architecture actually traverses. Options can include on-premises firewalls at each CE edge or a broader Azure transit/security design such as Virtual WAN secured hub, depending on requirements.

**Stateful symmetry:** If inspection/NAT exists at either end, ensure the return route does not bypass the state owner. Global Reach can provide reachability while an asymmetric security design still breaks the application session.

**Fast mental model:**

```text
Global Reach = connect ER-attached sites
              over Microsoft's backbone

It is NOT:
- VNet peering
- Azure Firewall insertion
- Route Server transit
- automatic SD-WAN policy
```

---

## 3. Private Peering, Microsoft Peering, and legacy Public Peering

New ExpressRoute designs use **Azure Private Peering** and **Microsoft Peering**. The old Azure Public Peering routing domain is legacy/deprecated for new design work.

### 3.1 Azure Private Peering

Use Private Peering for Azure resources reached by private IP, including VMs, internal load balancers, NVAs, and Private Endpoints.

Typical path:

```text
On-premises
  -> CE/PE router
  -> ExpressRoute Private Peering
  -> MSEE
  -> Microsoft backbone
  -> ER VNet gateway / eligible FastPath
  -> Azure VNet private IP
```

No NAT is inherently required.

### 3.2 Microsoft Peering

Use Microsoft Peering for supported Microsoft public service endpoints over ExpressRoute.

Typical requirements include:

- redundant BGP sessions;
- peering-link IP addressing;
- public prefixes registered to you/your ASN or an appropriate customer ASN;
- public source address before entering Microsoft Peering, commonly via SNAT;
- route filters selecting the Microsoft BGP communities you want to receive.

Microsoft Peering is **not general Internet transit**.

### 3.3 Azure CLI — Microsoft Peering

Example only; use public prefixes that are actually registered/validated for your organization.

```cli
az network express-route peering create \
  --resource-group RG-Network \
  --circuit-name ER-LA-01 \
  --peering-type MicrosoftPeering \
  --peer-asn 65010 \
  --vlan-id 300 \
  --primary-peer-subnet 192.0.2.0/30 \
  --secondary-peer-subnet 192.0.2.4/30 \
  --advertised-public-prefixes 203.0.113.0/24
```

If the public prefixes are registered to a different customer ASN, review the current `--customer-asn` option and Microsoft routing requirements before applying it.

Verify:

```cli
az network express-route peering show \
  --resource-group RG-Network \
  --circuit-name ER-LA-01 \
  --name MicrosoftPeering \
  --query '{state:state,peerASN:peerASN,vlan:vlanId,advertised:advertisedPublicPrefixes}' \
  --output json
```

### 3.4 Azure CLI — route filter for Microsoft Peering

For circuits configured on or after August 1, 2017, Microsoft documents that Microsoft Peering does not advertise service routes until an appropriate route filter is attached.

List current service communities:

```cli
az network route-filter rule list-service-communities --output table
```

Create a route filter:

```cli
az network route-filter create \
  --resource-group RG-Network \
  --name RF-MicrosoftServices \
  --location westus
```

Add the allowed community values. The value below is only an example from Microsoft documentation; select the communities that correspond to the services you require:

```cli
az network route-filter rule create \
  --resource-group RG-Network \
  --filter-name RF-MicrosoftServices \
  --name Allow-Selected-Microsoft-Services \
  --access Allow \
  --communities 12076:5040
```

Attach the route filter to Microsoft Peering:

```cli
az network express-route peering update \
  --resource-group RG-Network \
  --circuit-name ER-LA-01 \
  --name MicrosoftPeering \
  --route-filter RF-MicrosoftServices
```

Verify the attachment:

```cli
az network express-route peering show \
  -g RG-Network \
  --circuit-name ER-LA-01 \
  -n MicrosoftPeering \
  --query '{state:state,routeFilter:routeFilter.id}' \
  -o json
```

---

## 4. BGP mechanics you must understand

### 4.1 ASNs

- Microsoft ExpressRoute ASN: **12076**
- Azure Route Server ASN: **65515**
- Customer ASN can be 16-bit or 32-bit subject to reserved ASN restrictions.

### 4.2 Prefix limits

Current documented Private Peering limits include up to 4,000 IPv4 prefixes normally and up to 10,000 with ExpressRoute Premium. Microsoft Peering has a much smaller advertised-prefix limit. Always verify current limits before a large migration.

Exceeding prefix limits can cause BGP session failure. Aggregate deliberately.

### 4.3 Default route

A default `0.0.0.0/0` can be advertised through **Private Peering** to force Azure workload Internet traffic toward on-premises. That does not make ExpressRoute Microsoft Peering a general Internet path.

### 4.4 BGP communities

Microsoft tags routes with regional/service communities. Do not assume arbitrary customer communities sent to Microsoft are honored as a generic inbound traffic-engineering control.

### 4.5 Longest prefix wins first

If one circuit advertises `10.10.0.0/16` and another advertises `10.10.10.0/24`, traffic to `10.10.10.25` follows the `/24` before AS-path or connection-weight comparisons for equal prefixes are relevant.

---

## 5. ExpressRoute to a customer-managed VNet

The conventional non-vWAN design has:

1. ExpressRoute circuit + Private Peering.
2. ExpressRoute virtual network gateway in `GatewaySubnet`.
3. Azure connection object between the VNet gateway and circuit.
4. Optional hub/spoke peering with gateway transit.

### 5.1 Control plane

The ExpressRoute VNet gateway exchanges routes between the ExpressRoute circuit and Azure VNet routing.

### 5.2 Data plane

Without FastPath:

```text
VM
 -> VNet routing
 -> ExpressRoute VNet gateway
 -> Microsoft backbone
 -> MSEE
 -> provider/customer edge
 -> on-premises
```

### 5.3 Azure CLI — create the ExpressRoute VNet gateway

Assume:

```text
VNet:       VNet-Hub
Address:    10.0.0.0/16
GatewaySubnet: 10.0.255.0/27
Gateway:    ERGW-Hub
SKU:        ErGw2AZ
```

Create the required subnet:

```cli
az network vnet subnet create \
  --resource-group RG-Hub \
  --vnet-name VNet-Hub \
  --name GatewaySubnet \
  --address-prefixes 10.0.255.0/27
```

Create the public IP resource used by the gateway control plane:

```cli
az network public-ip create \
  --resource-group RG-Hub \
  --name ERGW-Hub-PIP \
  --sku Standard \
  --allocation-method Static
```

Create the ExpressRoute VNet gateway:

```cli
az network vnet-gateway create \
  --resource-group RG-Hub \
  --name ERGW-Hub \
  --vnet VNet-Hub \
  --gateway-type ExpressRoute \
  --sku ErGw2AZ \
  --public-ip-address ERGW-Hub-PIP
```

Verify:

```cli
az network vnet-gateway show \
  --resource-group RG-Hub \
  --name ERGW-Hub \
  --query '{name:name,type:gatewayType,sku:sku.name,state:provisioningState}' \
  --output table
```

**Success criteria:** gateway type `ExpressRoute`, expected SKU, provisioning state `Succeeded`.

### 5.4 Azure CLI — connect the VNet gateway to the circuit

Same subscription:

```cli
az network vpn-connection create \
  --resource-group RG-Hub \
  --name Conn-ER-LA-01 \
  --vnet-gateway1 ERGW-Hub \
  --express-route-circuit2 /subscriptions/<SUBSCRIPTION_ID>/resourceGroups/RG-Network/providers/Microsoft.Network/expressRouteCircuits/ER-LA-01
```

Despite the command group name `vpn-connection`, the destination argument `--express-route-circuit2` creates an ExpressRoute-type connection.

Verify:

```cli
az network vpn-connection show \
  --resource-group RG-Hub \
  --name Conn-ER-LA-01 \
  --query '{type:connectionType,state:connectionStatus,weight:routingWeight,fastPath:expressRouteGatewayBypass}' \
  --output json
```

### 5.5 Azure CLI — cross-subscription authorization

The circuit owner creates an authorization:

```cli
az network express-route auth create \
  --resource-group RG-Network \
  --circuit-name ER-LA-01 \
  --name Auth-Spoke-Subscription
```

Retrieve the authorization key:

```cli
AUTH_KEY=$(az network express-route auth show \
  -g RG-Network \
  --circuit-name ER-LA-01 \
  -n Auth-Spoke-Subscription \
  --query authorizationKey \
  -o tsv)
```

The circuit user creates the connection using that authorization:

```cli
az network vpn-connection create \
  --resource-group RG-Hub \
  --name Conn-Shared-ER \
  --vnet-gateway1 ERGW-Hub \
  --express-route-circuit2 /subscriptions/<CIRCUIT_SUBSCRIPTION>/resourceGroups/RG-Network/providers/Microsoft.Network/expressRouteCircuits/ER-LA-01 \
  --authorization-key "$AUTH_KEY"
```

Verify authorization use state:

```cli
az network express-route auth show \
  -g RG-Network \
  --circuit-name ER-LA-01 \
  -n Auth-Spoke-Subscription \
  -o json
```

### 5.6 FastPath

FastPath keeps the gateway for the control plane while eligible data traffic bypasses the gateway data plane.

Enable FastPath on a new traditional VNet connection where the gateway/SKU and feature combination supports it:

```cli
az network vpn-connection create \
  --resource-group RG-Hub \
  --name Conn-ER-FastPath \
  --vnet-gateway1 ERGW-Hub \
  --express-route-circuit2 /subscriptions/<SUB_ID>/resourceGroups/RG-Network/providers/Microsoft.Network/expressRouteCircuits/ER-LA-01 \
  --express-route-gateway-bypass true
```

Or update an existing connection:

```cli
az network vpn-connection update \
  --resource-group RG-Hub \
  --name Conn-ER-LA-01 \
  --express-route-gateway-bypass true
```

Do not enable this blindly. FastPath support depends on gateway SKU and feature/topology.

---

## 6. Multi-location, multi-circuit design

Assume:

- Site A / LA: `10.10.0.0/16`
- Site B / Dallas: `10.20.0.0/16`
- Circuit 1: west peering location
- Circuit 2: central/east peering location
- Azure VNet: `10.50.0.0/16`
- Customer ASN: `65010`

![Two circuits and BGP path control](images/09-06-26-12-40_expressroute_multi_circuit_bgp.svg)

[Download/edit the matching draw.io source](images/09-06-26-12-40_expressroute_multi_circuit_bgp.drawio)

### 6.1 Active/active ECMP

For equal-cost behavior, advertise the same prefix on both circuits with equivalent policy. Azure can ECMP identical routes across multiple eligible ExpressRoute circuits.

Do not expect per-packet round robin. ECMP is flow-oriented.

### 6.2 Active/standby

For Azure -> on-premises path preference, use AS-path prepending toward Microsoft:

```text
Circuit 1: 10.10.0.0/16 AS_PATH 65010
Circuit 2: 10.10.0.0/16 AS_PATH 65010 65010 65010
```

For on-premises -> Azure preference, use your own BGP `LOCAL_PREF` internally:

```text
Circuit 1 learned Azure routes -> LOCAL_PREF 200
Circuit 2 learned Azure routes -> LOCAL_PREF 100
```

### 6.3 Azure CLI — attach two circuits and set connection weights

A traditional VNet gateway can have separate connection objects to multiple circuits.

```cli
az network vpn-connection create \
  -g RG-Hub \
  -n Conn-ER-West \
  --vnet-gateway1 ERGW-Hub \
  --express-route-circuit2 /subscriptions/<SUB_ID>/resourceGroups/RG-Network/providers/Microsoft.Network/expressRouteCircuits/ER-West
```

```cli
az network vpn-connection create \
  -g RG-Hub \
  -n Conn-ER-East \
  --vnet-gateway1 ERGW-Hub \
  --express-route-circuit2 /subscriptions/<SUB_ID>/resourceGroups/RG-Network/providers/Microsoft.Network/expressRouteCircuits/ER-East
```

Azure CLI exposes routing weight on the connection. Microsoft documents a range of 0–32000, with higher weight preferred when the same destination prefix is learned through multiple ExpressRoute connections to the VNet gateway.

```cli
az network vpn-connection update \
  -g RG-Hub \
  -n Conn-ER-West \
  --routing-weight 200

az network vpn-connection update \
  -g RG-Hub \
  -n Conn-ER-East \
  --routing-weight 100
```

**Important:** Connection weight influences the Azure-side selection layer. It does not replace customer-side `LOCAL_PREF`, AS-path design, or longest-prefix match.

### 6.4 Failure sequence and capacity

When Circuit 1 fails:

1. physical/BGP failure is detected;
2. BGP routes are withdrawn;
3. alternate circuit route becomes active;
4. Azure/customer FIBs converge;
5. new flows use Circuit 2;
6. existing stateful sessions may survive or reset depending on middleboxes/application timers.

BFD can improve detection, but do not assume subsecond end-to-end convergence. Microsoft documents scenarios where failover can take considerably longer.

A 5-Gbps backup circuit cannot carry 8 Gbps simply because the primary failed. Size the surviving path for business-critical failure load.

---

## 7. ExpressRoute with Azure Virtual WAN

Virtual WAN changes the Azure-side termination model. Instead of a customer-managed `GatewaySubnet`, create an ExpressRoute gateway in the managed virtual hub.

![ExpressRoute with Virtual WAN](images/09-06-26-12-40_expressroute_vwan_integration.svg)

[Download/edit the matching draw.io source](images/09-06-26-12-40_expressroute_vwan_integration.drawio)

### 7.1 vHub route-table model

Each connection has:

- **association** — which vHub route table is used to look up traffic arriving on that connection;
- **propagation** — which route tables learn prefixes from that connection.

This replaces much of the traditional hub VNet/gateway-transit plumbing.

### 7.2 Azure CLI — vWAN ExpressRoute gateway and connection

Create the vWAN ExpressRoute gateway:

```cli
az network express-route gateway create \
  --name ERGW-vHub-West \
  --resource-group RG-vWAN \
  --virtual-hub vHub-West \
  --min-val 5
```

Get the Private Peering resource ID:

```cli
ER_PEERING_ID=$(az network express-route peering show \
  -g RG-Network \
  --circuit-name ER-LA-01 \
  -n AzurePrivatePeering \
  --query id -o tsv)
```

Create the connection:

```cli
az network express-route gateway connection create \
  --resource-group RG-vWAN \
  --gateway-name ERGW-vHub-West \
  --name Conn-ER-LA-01 \
  --peering "$ER_PEERING_ID"
```

For segmented routing, specify the actual vHub route-table IDs:

```cli
az network express-route gateway connection create \
  --resource-group RG-vWAN \
  --gateway-name ERGW-vHub-West \
  --name Conn-ER-Segmented \
  --peering "$ER_PEERING_ID" \
  --associated-route-table <VHUB_ROUTE_TABLE_ID> \
  --propagated-route-tables <VHUB_ROUTE_TABLE_ID> \
  --labels Default \
  --routing-weight 100
```

Verify:

```cli
az network express-route gateway connection show \
  -g RG-vWAN \
  --gateway-name ERGW-vHub-West \
  -n Conn-ER-LA-01 \
  -o json
```

---

## 8. ExpressRoute with Azure Route Server and SD-WAN

Azure Route Server (**ARS**) is a managed BGP control plane inside a customer-managed VNet. It is not a packet-forwarding appliance.

![ExpressRoute, Route Server, and SD-WAN branch-to-branch](images/09-06-26-13-15_expressroute_sdwan_branch_to_branch.svg)

[Download/edit the matching draw.io source](images/09-06-26-13-15_expressroute_sdwan_branch_to_branch.drawio)

### 8.1 Branch-to-branch route exchange

When enabled, ARS can exchange routes between BGP-speaking NVAs and VNet gateways such as ExpressRoute/VPN gateways in supported designs.

Representative data path:

```text
Branch A
 -> ExpressRoute
 -> ER VNet gateway
 -> Azure VNet forwarding
 -> SD-WAN NVA
 -> SD-WAN overlay
 -> Branch B
```

ARS is absent from the packet path.

### 8.2 Azure CLI — Route Server integration

Create the required subnet:

```cli
az network vnet subnet create \
  -g RG-Hub \
  --vnet-name VNet-Hub \
  -n RouteServerSubnet \
  --address-prefixes 10.0.1.0/27
```

Create the Standard public IP:

```cli
az network public-ip create \
  -g RG-Hub \
  -n RouteServerIP \
  --sku Standard \
  --version IPv4
```

Create ARS:

```cli
SUBNET_ID=$(az network vnet subnet show \
  -g RG-Hub \
  --vnet-name VNet-Hub \
  -n RouteServerSubnet \
  --query id -o tsv)

az network routeserver create \
  -g RG-Hub \
  -n ARS-Hub \
  --hosted-subnet "$SUBNET_ID" \
  --public-ip-address RouteServerIP
```

Peer an NVA:

```cli
az network routeserver peering create \
  -g RG-Hub \
  --routeserver ARS-Hub \
  -n SDWAN-NVA \
  --peer-asn 65050 \
  --peer-ip 10.0.2.4
```

Enable branch-to-branch route exchange when required:

```cli
az network routeserver update \
  -g RG-Hub \
  -n ARS-Hub \
  --allow-b2b-traffic true
```

Verify ARS endpoints and state:

```cli
az network routeserver show \
  -g RG-Hub \
  -n ARS-Hub \
  --query '{asn:virtualRouterAsn,peerIPs:virtualRouterIps,allowB2B:allowBranchToBranchTraffic,preference:hubRoutingPreference}' \
  -o json
```

Verify learned/advertised routes:

```cli
az network routeserver peering list-learned-routes \
  -g RG-Hub \
  --routeserver ARS-Hub \
  -n SDWAN-NVA \
  -o table
```

```cli
az network routeserver peering list-advertised-routes \
  -g RG-Hub \
  --routeserver ARS-Hub \
  -n SDWAN-NVA \
  -o table
```

### 8.3 Vendor integration models

Three common models exist:

1. **Customer-managed hub + ARS + BGP-capable NVA** — broad vendor flexibility.
2. **Integrated NVA in Virtual WAN** — Azure-managed vHub route exchange with supported vendor integrations.
3. **NVA in a regular VNet connected to vWAN** — more customer control but more lifecycle/routing responsibility.

Vendor examples include Fortinet FortiGate, Palo Alto Prisma SD-WAN/VM-Series architectures, and Cisco Catalyst SD-WAN/C8000V. Do not assume all vendors use the same Azure attachment or HA model.

ARS is not ExpressRoute-circuit-to-circuit transit. Use Global Reach for that requirement.

---

## 9. Packet-flow examples

### 9.1 On-premises to Azure through traditional ExpressRoute

```text
Source:      10.10.10.25:53000
Destination: 10.50.20.10:443
```

1. Enterprise routing selects an Azure prefix learned from ExpressRoute.
2. Customer BGP policy selects Circuit 1 or Circuit 2.
3. Packet traverses provider handoff/private-peering VLAN to MSEE.
4. Microsoft backbone delivers toward the Azure region.
5. ER gateway or eligible FastPath delivers into the VNet.
6. Azure routing delivers to `10.50.20.10`.
7. Return path uses the route to `10.10.0.0/16` learned through Private Peering.

No NAT is inherently required for Private Peering.

### 9.2 Azure to on-premises with equal circuits

If Azure sees identical prefixes with equivalent attributes, it can use eligible equal-cost ExpressRoute paths.

### 9.3 Azure to on-premises with AS prepend

```text
10.10.0.0/16 via Circuit 1: AS_PATH 65010
10.10.0.0/16 via Circuit 2: AS_PATH 65010 65010 65010
```

Circuit 1 is preferred while both paths are available.

---

## 10. Azure CLI — provider circuit and Private Peering

Discover providers and peering locations:

```cli
az network express-route list-service-providers --output table
```

Create a provider circuit:

```cli
az network express-route create \
  --name ER-LA-01 \
  --resource-group RG-Network \
  --location westus \
  --provider "Equinix" \
  --peering-location "Silicon Valley" \
  --bandwidth 1000 \
  --sku-tier Standard \
  --sku-family MeteredData
```

> **Billing warning:** Microsoft bills the circuit once the service key is issued. Create it when the provider is ready to provision.

Retrieve the service key and states:

```cli
az network express-route show \
  -g RG-Network \
  -n ER-LA-01 \
  --query '{serviceKey:serviceKey,providerState:serviceProviderProvisioningState,circuitState:circuitProvisioningState,provisioning:provisioningState}' \
  -o table
```

Create Azure Private Peering:

```cli
az network express-route peering create \
  -g RG-Network \
  --circuit-name ER-LA-01 \
  --peering-type AzurePrivatePeering \
  --peer-asn 65010 \
  --vlan-id 200 \
  --primary-peer-subnet 192.168.100.128/30 \
  --secondary-peer-subnet 192.168.100.132/30
```

Verify:

```cli
az network express-route peering show \
  -g RG-Network \
  --circuit-name ER-LA-01 \
  -n AzurePrivatePeering \
  --query '{state:state,azureASN:azureASN,peerASN:peerASN,vlan:vlanId,primary:primaryPeerAddressPrefix,secondary:secondaryPeerAddressPrefix}' \
  -o json
```

Current CLI exposes `az network express-route peering get-stats`, but Microsoft marks that command **Preview**. Do not build production automation that assumes Preview behavior is stable without validating the CLI/API version.

---

## 11. Azure CLI — Global Reach

Global Reach creates an ExpressRoute circuit connection under Azure Private Peering.

Assume:

- Circuit 1: `ER-LA-01`
- Circuit 2: `ER-DAL-01`
- Global Reach interconnect prefix: `10.254.0.0/29`

Create the circuit-to-circuit connection:

```cli
az network express-route peering connection create \
  --resource-group RG-Network \
  --circuit-name ER-LA-01 \
  --peering-name AzurePrivatePeering \
  --name GR-LA-to-DAL \
  --peer-circuit /subscriptions/<SUB_ID>/resourceGroups/RG-Network/providers/Microsoft.Network/expressRouteCircuits/ER-DAL-01 \
  --address-prefix 10.254.0.0/29
```

Verify:

```cli
az network express-route peering connection show \
  -g RG-Network \
  --circuit-name ER-LA-01 \
  --peering-name AzurePrivatePeering \
  -n GR-LA-to-DAL \
  -o json
```

List all Global Reach connections under the peering:

```cli
az network express-route peering connection list \
  -g RG-Network \
  --circuit-name ER-LA-01 \
  --peering-name AzurePrivatePeering \
  -o table
```

For cross-subscription/cross-tenant circuit ownership, use the current authorization workflow documented for the applicable Global Reach topology instead of assuming the same-subscription command is sufficient.

---

## 12. Azure CLI — hub/spoke gateway transit

If the ExpressRoute gateway is in a customer-managed hub VNet, spoke VNets consume it through normal VNet peering gateway transit.

Hub -> spoke:

```cli
SPOKE_ID=$(az network vnet show \
  -g RG-Spoke \
  -n VNet-SpokeA \
  --query id -o tsv)

az network vnet peering create \
  -g RG-Hub \
  --vnet-name VNet-Hub \
  -n Hub-to-SpokeA \
  --remote-vnet "$SPOKE_ID" \
  --allow-vnet-access \
  --allow-forwarded-traffic \
  --allow-gateway-transit
```

Spoke -> hub:

```cli
HUB_ID=$(az network vnet show \
  -g RG-Hub \
  -n VNet-Hub \
  --query id -o tsv)

az network vnet peering create \
  -g RG-Spoke \
  --vnet-name VNet-SpokeA \
  -n SpokeA-to-Hub \
  --remote-vnet "$HUB_ID" \
  --allow-vnet-access \
  --allow-forwarded-traffic \
  --use-remote-gateways
```

**Control-plane meaning:**

- hub `--allow-gateway-transit` allows the hub gateway to be consumed across peering;
- spoke `--use-remote-gateways` tells the spoke to use the remote hub gateway;
- `--allow-forwarded-traffic` permits forwarded traffic crossing the peering and is relevant when traffic is forwarded by gateways/NVAs.

Verify spoke effective routes:

```cli
az network nic show-effective-route-table \
  -g RG-Spoke \
  -n <SPOKE_VM_NIC> \
  -o table
```

**Success criteria:** expected on-premises prefixes appear with a virtual-network-gateway learned path.

---

## 13. Multi-circuit BGP policy examples

### Equal-active

```text
To Azure:
  advertise the same on-premises aggregate equally on both circuits

From Azure:
  use the same LOCAL_PREF internally for Azure routes learned via both circuits
```

### Primary/backup

```text
To Azure:
  Circuit 1: normal AS path
  Circuit 2: prepend customer ASN

From Azure:
  Circuit 1-learned Azure routes: LOCAL_PREF 200
  Circuit 2-learned Azure routes: LOCAL_PREF 100
```

### Per-site primary

```text
10.10.0.0/16: prefer Circuit 1, Circuit 2 backup
10.20.0.0/16: prefer Circuit 2, Circuit 1 backup
```

This often balances latency, bandwidth use, and deterministic failover better than global all-path ECMP.

---

## 14. Connection weight versus AS-path prepending

Keep the layers separate:

- **Longest-prefix match** selects the most-specific route.
- **AS-path prepending** changes the BGP path Microsoft sees for on-premises prefixes.
- **Azure connection/routing weight** influences Azure choice among connection objects where supported.
- **LOCAL_PREF** is your enterprise-side BGP policy.

Do not configure conflicting preferences at every layer without documenting which one should win.

---

## 15. Security and firewall insertion

ExpressRoute is private connectivity; it is **not a firewall** and does not automatically provide payload encryption.

Inspection options include:

- Azure Firewall or NVA in a customer-managed hub;
- Virtual WAN Routing Intent/security provider designs;
- on-premises firewalls before CE routers;
- IPsec overlays when required/supported;
- UDR/BGP-based service insertion.

### Stateful symmetry

If Azure -> Site A traverses Firewall A/Circuit 1, make the return path predictable enough that the same stateful security context sees the reverse flow. ECMP across independent firewalls without state sharing can break sessions.

---

## 16. High-availability hierarchy

### Level 1 — one circuit, two BGP sessions

Protects against one MSEE/link failure but not the entire peering location.

### Level 2 — ExpressRoute Metro

Dual peering locations inside the metro reduce the local failure domain.

### Level 3 — two circuits in different peering locations

Best for broader DR. Prefer diverse carrier/local-loop paths and customer-edge infrastructure.

### Level 4 — alternate technology

For some Private Peering workloads, a site-to-site VPN can provide emergency backup. Verify actual route preference and application behavior instead of assuming coexistence equals automatic failover.

---

## 17. Verification checklist

### 17.1 Circuit and peering

```cli
az network express-route show \
  -g RG-Network \
  -n ER-LA-01 \
  --query '{providerState:serviceProviderProvisioningState,circuitState:circuitProvisioningState,provisioning:provisioningState,sku:sku.name,serviceKey:serviceKey}' \
  -o json
```

Success indicators:

- `serviceProviderProvisioningState = Provisioned`
- `circuitProvisioningState = Enabled`
- Azure resource `provisioningState = Succeeded`

Peering:

```cli
az network express-route peering show \
  -g RG-Network \
  --circuit-name ER-LA-01 \
  -n AzurePrivatePeering \
  -o json
```

### 17.2 Traditional VNet gateway connection

```cli
az network vpn-connection show \
  -g RG-Hub \
  -n Conn-ER-LA-01 \
  --query '{type:connectionType,status:connectionStatus,weight:routingWeight,fastPath:expressRouteGatewayBypass,provisioning:provisioningState}' \
  -o json
```

Expected: ExpressRoute connection type, successful provisioning, connected/healthy status as applicable.

### 17.3 Gateway resiliency and route information

Current Azure CLI includes GA resiliency commands for ExpressRoute VNet gateways.

Retrieve the resiliency assessment:

```cli
az network vnet-gateway get-resiliency-information \
  --resource-group RG-Hub \
  --virtual-network-gateway-name ERGW-Hub \
  --attempt-refresh true \
  --output json
```

Retrieve route-set/resiliency information:

```cli
az network vnet-gateway get-routes-information \
  --resource-group RG-Hub \
  --virtual-network-gateway-name ERGW-Hub \
  --attempt-refresh true \
  --output json
```

**What to inspect:** current resiliency state/recommendations and route-set information reported by Azure. Do not hard-code exact JSON fields in automation until you confirm the API/CLI version used in your environment.

### 17.4 Virtual WAN

```cli
az network express-route gateway connection show \
  -g RG-vWAN \
  --gateway-name ERGW-vHub-West \
  -n Conn-ER-LA-01 \
  -o json
```

Verify the intended peering, route-table association, propagation, and routing weight.

### 17.5 Route Server

```cli
az network routeserver peering list-learned-routes \
  -g RG-Hub \
  --routeserver ARS-Hub \
  -n SDWAN-NVA \
  -o table
```

```cli
az network routeserver peering list-advertised-routes \
  -g RG-Hub \
  --routeserver ARS-Hub \
  -n SDWAN-NVA \
  -o table
```

### 17.6 Global Reach

```cli
az network express-route peering connection list \
  -g RG-Network \
  --circuit-name ER-LA-01 \
  --peering-name AzurePrivatePeering \
  -o table
```

Then verify the actual on-premises BGP route table on both sides. Azure resource state alone does not prove the desired site-to-site route is installed on the CE routers.

---

## 18. Troubleshooting by symptom

### Symptom: one of two BGP sessions is down

**Where:** CE/provider edge and ExpressRoute peering.

**Check:** primary/secondary `/30`, VLAN ID, ASN, Layer-2 cross-connect, MD5 key if used, provider provisioning.

**Success:** both sessions established.

### Symptom: circuit exists but BGP never comes up

First verify provider provisioning:

```cli
az network express-route show \
  -g RG-Network \
  -n ER-LA-01 \
  --query '{provider:serviceProviderProvisioningState,circuit:circuitProvisioningState}' \
  -o table
```

If provider state is not `Provisioned`, fix provisioning before debugging BGP policy.

### Symptom: BGP is established but Azure cannot reach on-premises

Check customer advertisements, prefix limits, AS-loop prevention, more-specific routes, and whether a UDR/NVA is overriding gateway-propagated routes.

### Symptom: VNet is not receiving ExpressRoute routes

For a traditional hub/spoke design:

1. Verify `Conn-ER-*` exists and is healthy.
2. Verify hub peering has `allowGatewayTransit`.
3. Verify spoke peering has `useRemoteGateways`.
4. Check the spoke VM NIC effective route table.

```cli
az network nic show-effective-route-table \
  -g RG-Spoke \
  -n <NIC_NAME> \
  -o table
```

### Symptom: Azure sends traffic through the wrong circuit

Check, in order:

1. prefix specificity;
2. AS-path difference for the on-premises destination;
3. Azure connection routing weight;
4. whether both circuits are actually linked to the same VNet/vHub routing domain.

### Symptom: Site A exits through Site B unexpectedly

Inspect customer `LOCAL_PREF`, AS path, IGP cost to BGP next hop, more-specific routes, and route-reflector policy.

### Symptom: Microsoft Peering is up but no Microsoft service routes are learned

Check whether a route filter is attached:

```cli
az network express-route peering show \
  -g RG-Network \
  --circuit-name ER-LA-01 \
  -n MicrosoftPeering \
  --query '{state:state,routeFilter:routeFilter.id}' \
  -o json
```

Then inspect the route-filter rule/community list.

### Symptom: FastPath was enabled but traffic does not behave as expected

Verify:

```cli
az network vpn-connection show \
  -g RG-Hub \
  -n Conn-ER-LA-01 \
  --query expressRouteGatewayBypass \
  -o tsv
```

Then confirm that the selected gateway SKU and resource type support FastPath for the exact feature/path. FastPath eligibility is not universal.

### Symptom: failover takes too long

Measure separately:

1. physical failure detection;
2. BFD/BGP-down;
3. route withdrawal;
4. alternate BGP best-path selection;
5. FIB update;
6. remote-site convergence;
7. firewall/NAT state behavior;
8. application retry.

### Symptom: Route Server NVA learns VNet routes but not ER routes

Check that ER gateway and ARS are in the same supported VNet topology, branch-to-branch is enabled when required, NVA peers with both ARS IPs, and you are not expecting unsupported ER-circuit-to-ER-circuit transit.

### Symptom: vWAN spoke cannot reach on-premises

Check ER gateway connection, route-table association, propagation labels/tables, VNet connection route-table association, and Routing Intent/security policy if present.

### Symptom: Global Reach resource exists but sites cannot communicate

Check:

- both circuits have Private Peering operational;
- Global Reach connection state;
- interconnect address prefix correctness;
- CE BGP advertisements and filters on both sites;
- route overlap;
- firewall policy between sites.

---

## 19. Common mistakes

1. Calling the two BGP sessions inside one circuit “two circuits.”
2. Assuming one circuit is disaster-proof because it has two MSEEs.
3. Confusing Local/Standard/Premium with different physical technologies.
4. Treating ExpressRoute Direct as one giant circuit rather than dedicated ports hosting logical circuits.
5. Configuring AS-path prepending toward Azure but forgetting customer-side `LOCAL_PREF`.
6. Expecting per-packet ECMP.
7. Under-sizing the surviving circuit for failover load.
8. Using Route Server for ER circuit-to-circuit transit instead of Global Reach.
9. Confusing vWAN route association with propagation.
10. Putting a stateful firewall in one direction while allowing the reverse path to bypass it.
11. Advertising excessive host routes instead of summarizing.
12. Confusing Azure resource region with ExpressRoute peering location.
13. Creating Microsoft Peering but forgetting the route filter.
14. Assuming a VNet gateway is automatically connected to a circuit once both resources exist; a connection object is required.
15. Assuming hub/spoke gateway transit is automatic; `allow-gateway-transit` and `use-remote-gateways` are explicit peering properties.
16. Assuming FastPath removes the ExpressRoute gateway from the architecture; the gateway remains the control-plane component.

---

## 20. Design recommendations

### Small enterprise / one geography

- One provider circuit may be acceptable for noncritical workloads.
- Bring up both BGP sessions.
- Consider VPN backup.

### Mission-critical regional enterprise

- Use geographically/operationally diverse circuits or Metro where appropriate.
- Prefer independent carrier/local-loop paths.
- Explicitly choose active/active or primary/backup.
- Size each surviving path for failure load.
- Test failover.

### Large multi-region enterprise

- Align circuits to major on-premises regions.
- Prefer nearest circuit under normal operation.
- Advertise backup routes through remote circuits.
- Use Virtual WAN when managed multi-region transit and route-table segmentation are desired.
- Use Global Reach for site-to-site transit between ER-attached locations.

### NVA/SD-WAN-heavy hub

- Customer-managed hub VNet + ExpressRoute gateway + ARS is a strong general pattern.
- Peer each NVA with both ARS instances.
- Enable branch-to-branch only with a deliberate transit requirement.
- Verify no route re-advertisement loop or inspection bypass is introduced.

---

## 21. Decision table

| Requirement | Best-fit feature |
|---|---|
| Private connection from premises to Azure VNets | ExpressRoute Private Peering |
| Reach supported Microsoft public services over ER | Microsoft Peering + route filter |
| Dedicated Microsoft-facing ports | ExpressRoute Direct |
| Localized Azure reach | Local SKU |
| Geopolitical-area Azure reach | Standard SKU |
| Global Azure reach/higher limits | Premium SKU |
| Two peering locations in one metro | ExpressRoute Metro |
| On-premises site-to-site transit between ER circuits | Global Reach |
| Managed global Azure hub routing | Virtual WAN + vHub ER gateway |
| Dynamic NVA + ER/VPN gateway route exchange | Azure Route Server |
| Reduced ER VNet gateway data-plane hop | FastPath |
| Cross-subscription circuit sharing | ExpressRoute circuit authorization |
| Spoke consumes hub ER gateway | VNet peering gateway transit |

---

## 22. Final mental model

```text
Physical/provider access
        ↓
ExpressRoute circuit
        ↓
Two redundant BGP sessions per peering
        ↓
Private Peering or Microsoft Peering
        ↓
Azure-side termination
  ├─ VNet ExpressRoute gateway
  └─ Virtual WAN ExpressRoute gateway
        ↓
Azure route distribution
        ↓
Workload
```

For a **traditional customer-managed VNet** remember the extra Azure object that is easy to miss:

```text
ExpressRoute circuit
      |
      | Azure Private Peering
      v
ExpressRoute VNet gateway
      ^
      |
      | az network vpn-connection ... --express-route-circuit2
      |
VNet / spokes using gateway transit
```

For multiple circuits, answer two questions separately:

1. **How does Azure choose the route toward on-premises?**
2. **How does on-premises choose the route toward Azure?**

Then test what happens when either path disappears.

---

## Sources

- Microsoft, **Azure ExpressRoute overview**: https://learn.microsoft.com/azure/expressroute/expressroute-introduction
- Microsoft, **ExpressRoute circuits and peering**: https://learn.microsoft.com/azure/expressroute/expressroute-circuit-peerings
- Microsoft, **ExpressRoute connectivity models**: https://learn.microsoft.com/azure/expressroute/expressroute-connectivity-models
- Microsoft, **ExpressRoute routing requirements**: https://learn.microsoft.com/azure/expressroute/expressroute-routing
- Microsoft, **Create/modify circuit with Azure CLI**: https://learn.microsoft.com/azure/expressroute/howto-circuit-cli
- Microsoft, **Create/modify peering with Azure CLI**: https://learn.microsoft.com/azure/expressroute/howto-routing-cli
- Microsoft, **Link a VNet to an ExpressRoute circuit with Azure CLI**: https://learn.microsoft.com/azure/expressroute/expressroute-howto-linkvnet-cli
- Microsoft, **Configure route filters for Microsoft Peering**: https://learn.microsoft.com/azure/expressroute/how-to-routefilter-portal
- Microsoft, **Designing for disaster recovery**: https://learn.microsoft.com/azure/expressroute/designing-for-disaster-recovery-with-expressroute-privatepeering
- Microsoft, **ExpressRoute Metro**: https://learn.microsoft.com/azure/expressroute/metro
- Microsoft, **ExpressRoute Direct**: https://learn.microsoft.com/azure/expressroute/expressroute-erdirect-about
- Microsoft, **ExpressRoute FastPath**: https://learn.microsoft.com/azure/expressroute/about-fastpath
- Microsoft, **ExpressRoute Global Reach**: https://learn.microsoft.com/azure/expressroute/expressroute-global-reach
- Microsoft, **ExpressRoute VNet gateways**: https://learn.microsoft.com/azure/expressroute/expressroute-about-virtual-network-gateways
- Microsoft, **ExpressRoute in Virtual WAN**: https://learn.microsoft.com/azure/virtual-wan/virtual-wan-expressroute-about
- Microsoft, **Virtual hub routing**: https://learn.microsoft.com/azure/virtual-wan/about-virtual-hub-routing
- Microsoft, **Route Server support for ExpressRoute/VPN**: https://learn.microsoft.com/azure/route-server/expressroute-vpn-support
- Microsoft, **Route Server CLI quickstart**: https://learn.microsoft.com/azure/route-server/quickstart-create-route-server-cli
- Microsoft, **Azure CLI — ExpressRoute**: https://learn.microsoft.com/cli/azure/network/express-route
- Microsoft, **Azure CLI — ExpressRoute Peering**: https://learn.microsoft.com/cli/azure/network/express-route/peering
- Microsoft, **Azure CLI — ExpressRoute peering connections / Global Reach**: https://learn.microsoft.com/cli/azure/network/express-route/peering/connection
- Microsoft, **Azure CLI — Virtual WAN ExpressRoute gateway**: https://learn.microsoft.com/cli/azure/network/express-route/gateway
- Microsoft, **Azure CLI — Virtual WAN ExpressRoute connection**: https://learn.microsoft.com/cli/azure/network/express-route/gateway/connection
- Microsoft, **Azure CLI — VNet gateway**: https://learn.microsoft.com/cli/azure/network/vnet-gateway
- Microsoft, **Azure CLI — VPN/ExpressRoute connection object**: https://learn.microsoft.com/cli/azure/network/vpn-connection
- Microsoft, **Azure CLI — Route Server**: https://learn.microsoft.com/cli/azure/network/routeserver
- Microsoft, **Azure CLI — Route Server peering**: https://learn.microsoft.com/cli/azure/network/routeserver/peering

---

## Information-quality labels used in this guide

- **Source information** — behavior stated directly in Microsoft documentation.
- **Additional explanation** — networking explanation following documented Azure/BGP/IP behavior.
- **Reasonable inference** — architecture conclusion derived from documented behavior; not presented as a Microsoft product guarantee.
