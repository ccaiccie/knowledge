# Azure Private Endpoint Inspection — Azure Firewall and ILB-Backed Third-Party NVA Deep Dive

## Purpose

This guide explains how to force Azure Private Endpoint (PE) traffic through a stateful inspection device. It covers two deployment patterns:

1. **Azure Firewall** in a classic hub-and-spoke topology.
2. **Standard Internal Load Balancer (ILB) with HA Ports in front of third-party NVAs**, where the ILB frontend IP is used as the UDR next hop and one NVA instance performs policy, inspection, state tracking, and SNAT for the flow.

The routing problem is the same in both designs: Private Endpoints install highly specific routes and, unless Private Endpoint network policies are enabled and the source has an appropriate UDR, traffic can bypass centralized inspection. The HA-NVA design adds load-balancer hashing, health probing, vendor HA behavior, SNAT/state ownership, and failure-domain considerations.

Examples use Azure SQL terminology where useful, but the networking principles apply to Private Link-enabled services generally. Service-specific ports, DNS zones, FQDN behavior, and subresources must be validated for the actual PaaS service.

## URLs reviewed

- https://learn.microsoft.com/en-us/azure/private-link/inspect-traffic-with-azure-firewall
- https://learn.microsoft.com/en-us/azure/private-link/tutorial-inspect-traffic-azure-firewall
- https://learn.microsoft.com/en-us/azure/private-link/disable-private-endpoint-network-policy
- https://learn.microsoft.com/en-us/azure/private-link/private-endpoint-overview
- https://learn.microsoft.com/en-us/azure/private-link/create-private-endpoint-cli
- https://learn.microsoft.com/en-us/cli/azure/network/private-endpoint?view=azure-cli-latest
- https://learn.microsoft.com/en-us/azure/private-link/secure-private-link
- https://learn.microsoft.com/en-us/azure/private-link/private-link-service-overview
- https://learn.microsoft.com/en-us/cli/azure/network/private-link-service?view=azure-cli-latest
- https://learn.microsoft.com/en-us/azure/firewall/snat-private-range
- https://learn.microsoft.com/en-us/azure/load-balancer/load-balancer-ha-ports-overview
- https://learn.microsoft.com/en-us/azure/load-balancer/components
- https://learn.microsoft.com/en-us/azure/load-balancer/quickstart-load-balancer-standard-internal-cli
- https://learn.microsoft.com/en-us/cli/azure/network/lb/rule?view=azure-cli-latest
- https://learn.microsoft.com/en-us/azure/architecture/example-scenario/firewalls/

## Table of contents

- [1. What makes Private Endpoint inspection special](#1-what-makes-private-endpoint-inspection-special)
- [2. Common routing requirement for Azure Firewall and NVA designs](#2-common-routing-requirement-for-azure-firewall-and-nva-designs)
- [3. Enable Private Endpoint network policies](#3-enable-private-endpoint-network-policies)
- [Part I — Azure Firewall](#part-i--azure-firewall)
  - [4. Azure Firewall architecture](#4-azure-firewall-architecture)
  - [5. Azure Firewall forward and return path](#5-azure-firewall-forward-and-return-path)
- [Part II — Standard ILB → NVA(s) → Private Endpoint](#part-ii--standard-ilb---nvas---private-endpoint)
  - [6. Is this supported conceptually?](#6-is-this-supported-conceptually)
  - [6.1 The missing detail: there is no direct ILB-to-Private-Endpoint link](#61-the-missing-detail-there-is-no-direct-ilb-to-private-endpoint-link)
  - [6.2 What actually links the traffic path together](#62-what-actually-links-the-traffic-path-together)
  - [6.3 Create and identify the Private Endpoint](#63-create-and-identify-the-private-endpoint)
  - [6.4 Route the Private Endpoint prefix to the ILB](#64-route-the-private-endpoint-prefix-to-the-ilb)
  - [6.5 Why the UDR is on the source subnet, not the Private Endpoint object](#65-why-the-udr-is-on-the-source-subnet-not-the-private-endpoint-object)
  - [6.6 Complete object-to-object relationship](#66-complete-object-to-object-relationship)
  - [7. ILB/NVA architecture diagram](#7-ilbnva-architecture-diagram)
  - [8. Exact ILB/NVA forward packet flow](#8-exact-ilbnva-forward-packet-flow)
  - [9. Exact ILB/NVA return packet flow](#9-exact-ilbnva-return-packet-flow)
  - [10. HA behavior: what ILB does and does not provide](#10-ha-behavior-what-ilb-does-and-does-not-provide)
  - [11. Azure CLI — create the ILB and NVA service insertion layer](#11-azure-cli--create-the-ilb-and-nva-service-insertion-layer)
    - [11.8 Can I link the ILB directly to a PaaS Private Endpoint without a UDR?](#118-can-i-link-the-ilb-directly-to-a-paas-private-endpoint-without-a-udr)
    - [11.9 Why Private Link Service looks similar but is a different architecture](#119-why-private-link-service-looks-similar-but-is-a-different-architecture)
  - [12. Create workload UDR to the ILB frontend](#12-create-workload-udr-to-the-ilb-frontend)
  - [13. Verify the source NIC effective route](#13-verify-the-source-nic-effective-route)
  - [14. Verify ILB rule and health configuration](#14-verify-ilb-rule-and-health-configuration)
  - [15. NVA routing requirements](#15-nva-routing-requirements)
  - [16. NAT policy on the NVA](#16-nat-policy-on-the-nva)
  - [17. Flow symmetry and HA Ports](#17-flow-symmetry-and-ha-ports)
  - [18. Important Azure Load Balancer constraints](#18-important-azure-load-balancer-constraints)
  - [19. DNS path remains unchanged](#19-dns-path-remains-unchanged)
  - [20. Peering requirements](#20-peering-requirements)
  - [21. Failure scenarios](#21-failure-scenarios)
  - [22. Troubleshooting by symptom](#22-troubleshooting-by-symptom)
  - [23. Azure Firewall vs ILB/NVA comparison](#23-azure-firewall-vs-ilbnva-comparison)
  - [24. Common mistakes](#24-common-mistakes)
  - [25. Recommended production design sequence](#25-recommended-production-design-sequence)
  - [26. Source information, additional explanation, and inference](#26-source-information-additional-explanation-and-inference)
- [Sources](#sources)

---

## 1. What makes Private Endpoint inspection special

A Private Endpoint is an Azure-managed network interface placed in a customer subnet. The NIC receives a private IP. Client DNS resolution maps the normal PaaS hostname to that private address, and the packet is delivered through the Private Link data plane to the service.

The important behavior is route specificity. A Private Endpoint installs a highly specific route for its address. A generic UDR such as:

```text
0.0.0.0/0 -> VirtualAppliance -> firewall/NVA
```

is not, by itself, sufficient to override a more-specific PE route. Microsoft documents that Private Endpoint network policies must be enabled when you want UDR/NSG policy enforcement for Private Endpoints, and the inspection UDR must be sufficiently specific relative to the VNet address space that contains the PE.

### Source information

Microsoft states that Private Endpoint traffic can be inspected by **Azure Firewall or a third-party network virtual appliance**. Microsoft also recommends SNAT when traffic is inspected on the way to a Private Endpoint because SNAT gives the destination side an unambiguous return destination through the stateful inspection device.

### Additional explanation

The Private Endpoint is not a normal dual-homed router or VM that you control. You cannot assume that attaching a route table to some other subnet forces the PE return path through the same firewall instance. If a stateful firewall receives only the forward direction, the session fails. SNAT solves that by making the inspection device the apparent source of the PE-facing flow.

---

## 2. Common routing requirement for Azure Firewall and NVA designs

Assume:

| Resource | Example |
|---|---|
| Workload VNet | `10.10.0.0/16` |
| Client subnet | `10.10.1.0/24` |
| Client VM | `10.10.1.4` |
| Hub VNet | `10.0.0.0/16` |
| Azure Firewall private IP | `10.0.1.4` |
| ILB frontend IP | `10.0.2.10` |
| NVA subnet | `10.0.3.0/24` |
| NVA-1 | `10.0.3.4` |
| NVA-2 | `10.0.3.5` |
| PE VNet | `10.20.0.0/16` |
| PE subnet | `10.20.1.0/24` |
| PE IP | `10.20.1.4` |

A useful source-subnet route is:

```text
10.20.0.0/16 -> VirtualAppliance -> inspection next hop
```

where `inspection next hop` is either:

```text
Azure Firewall design: 10.0.1.4
ILB/NVA design:         10.0.2.10
```

A `/24` or `/32` can be used when you need narrower steering. A dedicated PE subnet/VNet is operationally useful because it lets you aggregate many endpoints behind a small number of UDRs.

### Why `0.0.0.0/0` is not enough

The Private Endpoint route is more specific. Longest-prefix match wins. Microsoft documents that when PE network policy support for UDRs is enabled, the custom route prefix must be **equal to or more specific than the address-space prefix of the VNet in which the PE is deployed**. For a PE in a `10.20.0.0/16` VNet, examples such as `10.20.0.0/16`, `10.20.1.0/24`, or `10.20.1.4/32` can participate in overriding the PE route; `0.0.0.0/0` cannot.

---

## 3. Enable Private Endpoint network policies

```cli
RG=rg-pe-inspection
PE_VNET=vnet-pe
PE_SUBNET=snet-private-endpoints

az network vnet subnet update \
  --resource-group "$RG" \
  --vnet-name "$PE_VNET" \
  --name "$PE_SUBNET" \
  --disable-private-endpoint-network-policies false
```

Verify:

```cli
az network vnet subnet show \
  --resource-group "$RG" \
  --vnet-name "$PE_VNET" \
  --name "$PE_SUBNET" \
  --query '{Subnet:name,Prefix:addressPrefix,PENetworkPolicies:privateEndpointNetworkPolicies}' \
  --output table
```

**Success criteria:** `privateEndpointNetworkPolicies` reports an enabled state.

**Failure indicator:** it remains disabled. Fix this before troubleshooting firewall policy because the traffic can bypass the UDR inspection design.

> Current Private Link documentation also allows enabling only UDR policy or only NSG policy. For this inspection design, at minimum the PE subnet must permit **UDR policy enforcement**.

---

# Part I — Azure Firewall

## 4. Azure Firewall architecture

![Azure Firewall Private Endpoint inspection](images/09-06-26-12-37_private_endpoint_inspection_architecture.svg)

[Editable draw.io source](images/09-06-26-12-37_private_endpoint_inspection_architecture.drawio)

**What this image shows**  
The workload sends PE traffic to Azure Firewall. The firewall evaluates policy, performs SNAT when an application rule is used, and forwards to the PE.

**What matters**  
DNS must return the PE address, the client subnet must have a PE-specific UDR, Private Endpoint network policies must be enabled, and the firewall must perform stateful inspection/SNAT.

**What to verify**  
Client effective routes, PE subnet policy state, firewall logs, and DNS resolution.

## 5. Azure Firewall forward and return path

Assume:

```text
Client:   10.10.1.4:53000
PE:       10.20.1.4:1433
Firewall: 10.0.1.4
```

Forward:

1. DNS resolves the PaaS hostname to `10.20.1.4`.
2. Client sends `10.10.1.4:53000 -> 10.20.1.4:1433`.
3. Client-subnet UDR matches `10.20.0.0/16` and sends the packet to `10.0.1.4`.
4. Azure Firewall evaluates network/application policy.
5. Application rules SNAT the session.
6. Azure Firewall forwards the translated flow to `10.20.1.4`.
7. Private Link carries the connection to the service.

Return:

1. Service response returns through the PE.
2. Because the forward flow was SNATed, the reply is addressed to the firewall-side translated source.
3. Azure Firewall receives the reply and matches session state.
4. Reverse NAT restores the original client destination.
5. The firewall forwards the packet to `10.10.1.4`.

For Azure SQL, application-rule FQDN inspection is aligned with SQL proxy-mode behavior on TCP/1433. Redirect mode can introduce additional ports/destinations and should be designed separately.

---

# Part II — Standard ILB -> NVA(s) -> Private Endpoint

## 6. Is this supported conceptually?

Yes. Microsoft documents both of these building blocks:

- Private Endpoint inspection can use a **third-party NVA**.
- An **internal Standard Load Balancer with HA Ports** can be used to provide high availability and scale for NVAs.

Microsoft's Azure Architecture Center also documents UDRs that use an internal load balancer frontend IP as the next hop to reach an NVA tier.

The combination therefore looks like this:

```text
Client subnet UDR
   |
   | destination = PE address space
   v
Standard Internal Load Balancer frontend IP
   |
   | HA Ports + per-flow hashing + health probe
   +------> NVA-1
   |
   +------> NVA-2
              |
              | inspect + SNAT
              v
        Private Endpoint
              |
              v
        Azure Private Link
              |
              v
          Azure PaaS
```

The ILB does **not** inspect traffic. It is the highly available next-hop abstraction. The selected NVA owns firewall policy, state, optional TLS inspection, logging, and NAT.

## 6.1 The missing detail: there is no direct ILB-to-Private-Endpoint link

This is the most important correction to the mental model.

There is **no Azure object property** such as:

```text
PrivateEndpoint.gatewayLoadBalancer = ILB
```

and there is no CLI command such as:

```text
az network private-endpoint attach-load-balancer ...
```

The ILB is not attached to the Private Endpoint. The ILB becomes part of the path because a **UDR on the traffic source's subnet** tells Azure that destinations covering the PE IP must use the ILB frontend IP as the `VirtualAppliance` next hop.

![How ILB routing reaches a Private Endpoint](images/09-06-26-12-37_ilb_to_private_endpoint_routing_relationship.svg)

[Editable draw.io source](images/09-06-26-12-37_ilb_to_private_endpoint_routing_relationship.drawio)

**What this image shows:** The Private Endpoint retains its real IP `10.20.1.4`. The workload does not address the ILB. The workload addresses `10.20.1.4`; Azure's route lookup selects the ILB VIP `10.0.2.10` as the next hop. The ILB selects an NVA, and the NVA forwards the original destination toward the PE after inspection/SNAT.

**What matters:** The destination IP remains the PE IP throughout the steering decision. The ILB frontend is a **next-hop address**, not a replacement destination and not a DNAT address.

**What to verify:** DNS returns the PE IP, the client effective route for that PE prefix points to `10.0.2.10`, the selected NVA receives a packet whose destination is still the PE IP, and the NVA has a direct routed path from itself to the PE VNet.

## 6.2 What actually links the traffic path together

The complete relationship is:

```text
1. Private Endpoint object
      creates/owns PE NIC + private IP 10.20.1.4

2. Private DNS
      service FQDN -> 10.20.1.4

3. PE subnet network policy
      allows UDR policy to override PE routing behavior

4. Workload subnet route table
      10.20.0.0/16 -> VirtualAppliance -> 10.0.2.10

5. Internal Standard Load Balancer
      frontend 10.0.2.10 -> HA Ports backend pool -> healthy NVA

6. Selected NVA
      receives original destination 10.20.1.4
      inspects
      SNATs
      routes toward PE VNet

7. Private Endpoint
      receives flow addressed to 10.20.1.4
      hands it through Private Link to PaaS
```

That is the "link." It is a **routing/service-insertion chain**, not an Azure resource attachment between the ILB and PE.

## 6.3 Create and identify the Private Endpoint

The following generic Azure CLI structure is current and documented. The exact `--group-id` depends on the target service.

First identify the target resource and supported Private Link group IDs. For a service that exposes Private Link resources:

```cli
TARGET_RESOURCE_ID=<resource-id-of-paas-service>

az network private-link-resource list \
  --id "$TARGET_RESOURCE_ID" \
  --output table
```

Then create the PE in the dedicated PE subnet:

```cli
RG=rg-pe-inspection
PE_VNET=vnet-pe
PE_SUBNET=snet-private-endpoints
PE_NAME=pe-app-service
PE_CONNECTION=pe-app-service-connection
GROUP_ID=<service-specific-group-id>

az network private-endpoint create \
  --resource-group "$RG" \
  --name "$PE_NAME" \
  --vnet-name "$PE_VNET" \
  --subnet "$PE_SUBNET" \
  --private-connection-resource-id "$TARGET_RESOURCE_ID" \
  --group-id "$GROUP_ID" \
  --connection-name "$PE_CONNECTION"
```

To inspect the PE object and its NIC reference:

```cli
az network private-endpoint show \
  --resource-group "$RG" \
  --name "$PE_NAME" \
  --query '{name:name,state:provisioningState,nics:networkInterfaces[].id,connections:privateLinkServiceConnections[].privateLinkServiceConnectionState.status}' \
  --output json
```

Get the PE NIC ID and actual private IP:

```cli
PE_NIC_ID=$(az network private-endpoint show \
  --resource-group "$RG" \
  --name "$PE_NAME" \
  --query 'networkInterfaces[0].id' \
  --output tsv)

PE_NIC_NAME=${PE_NIC_ID##*/}

PE_IP=$(az network nic show \
  --ids "$PE_NIC_ID" \
  --query 'ipConfigurations[0].privateIPAddress' \
  --output tsv)

echo "$PE_IP"
```

For the examples in this guide, assume the result is:

```text
10.20.1.4
```

That is the address the application will connect to after Private DNS resolution. You do **not** replace it with `10.0.2.10`.

## 6.4 Route the Private Endpoint prefix to the ILB

Assume:

```text
PE VNet      = 10.20.0.0/16
PE subnet    = 10.20.1.0/24
PE IP        = 10.20.1.4
ILB frontend = 10.0.2.10
```

The workload subnet route can be aggregated at the PE VNet level:

```cli
APP_RT=rt-app-pe-via-nva

az network route-table create \
  --resource-group "$RG" \
  --name "$APP_RT" \
  --location "$LOCATION"

az network route-table route create \
  --resource-group "$RG" \
  --route-table-name "$APP_RT" \
  --name pe-vnet-via-ilb \
  --address-prefix 10.20.0.0/16 \
  --next-hop-type VirtualAppliance \
  --next-hop-ip-address 10.0.2.10

az network vnet subnet update \
  --resource-group "$RG" \
  --vnet-name vnet-app \
  --name snet-app \
  --route-table "$APP_RT"
```

Or scope the steering to only one PE:

```cli
az network route-table route create \
  --resource-group "$RG" \
  --route-table-name "$APP_RT" \
  --name single-pe-via-ilb \
  --address-prefix 10.20.1.4/32 \
  --next-hop-type VirtualAppliance \
  --next-hop-ip-address 10.0.2.10
```

The choice is operational:

| UDR prefix | Effect |
|---|---|
| `10.20.0.0/16` | Steer destinations in the whole dedicated PE VNet through the NVA service |
| `10.20.1.0/24` | Steer the dedicated PE subnet |
| `10.20.1.4/32` | Steer only one PE IP |
| `0.0.0.0/0` | Too broad to override the PE route by itself |

The prefix must follow Microsoft's PE UDR precedence requirements and must not be broader than the PE VNet address-space prefix when the goal is to override the PE route.

## 6.5 Why the UDR is on the source subnet, not the Private Endpoint object

A common misunderstanding is to look for a route-table property on the PE NIC that says "send inbound PE traffic through the ILB." That is not how this pattern works.

The route decision that inserts the firewall occurs **before the packet reaches the PE**, on the source side:

```text
Client 10.10.1.4
  |
  | destination = 10.20.1.4
  v
Azure source-NIC route lookup
  |
  | UDR says next hop = 10.0.2.10
  v
ILB -> NVA
  |
  | destination is still 10.20.1.4
  v
Private Endpoint
```

The PE subnet's network-policy setting matters because it permits the platform to honor UDR policy for traffic destined to PE addresses. It does **not** make the PE point to the ILB.

## 6.6 Complete object-to-object relationship

Use this as the configuration checklist:

```text
PaaS resource
  ^
  | privateLinkServiceConnection
  |
Private Endpoint pe-app-service
  |
  +-- NIC -> 10.20.1.4
  |
  +-- placed in vnet-pe/snet-private-endpoints
              |
              +-- PE network policies enabled for UDR

Private DNS zone
  service FQDN -> 10.20.1.4

vnet-app/snet-app
  |
  +-- route table rt-app-pe-via-nva
        |
        +-- 10.20.0.0/16
            nextHopType = VirtualAppliance
            nextHopIp   = 10.0.2.10

10.0.2.10
  = Standard ILB frontend
      |
      +-- HA Ports rule
      +-- backend pool
          +-- NVA-1
          +-- NVA-2

Selected NVA
  |
  +-- policy/inspection
  +-- SNAT
  +-- route 10.20.0.0/16 toward PE VNet
  v
10.20.1.4 Private Endpoint
```

There is therefore **one actual Azure Private Link attachment**: the **Private Endpoint to the PaaS/private-link resource**. The ILB/NVA relationship to that PE is only routing and forwarding.

---

## 7. ILB/NVA architecture diagram

![ILB NVA Private Endpoint architecture](images/09-06-26-12-37_private_endpoint_ilb_nva_architecture.svg)

[Editable draw.io source](images/09-06-26-12-37_private_endpoint_ilb_nva_architecture.drawio)

**What this image shows**  
A workload UDR points at the internal Standard Load Balancer frontend `10.0.2.10`. The HA Ports rule hashes each incoming flow to a healthy NVA. The selected NVA inspects and SNATs the connection before sending it to the Private Endpoint.

**What matters**  
The UDR next hop is the **ILB frontend**, not an individual firewall VM. SNAT makes the return flow target the NVA/session owner rather than the original workload address.

**What to verify**  
ILB SKU, frontend IP, HA Ports rule, health probes, backend membership, NIC IP forwarding, NVA policy, SNAT, and the effective source route to the PE.

---

## 8. Exact ILB/NVA forward packet flow

Assume this connection:

```text
Client socket:       10.10.1.4:53000
Private Endpoint:    10.20.1.4:443
ILB frontend:        10.0.2.10
Selected NVA:        NVA-1 / 10.0.3.4
```

### Step 1 — client route lookup

The client sends:

```text
SRC 10.10.1.4:53000
DST 10.20.1.4:443
```

The effective route table contains:

```text
10.20.0.0/16 -> VirtualAppliance -> 10.0.2.10
```

The packet is therefore steered toward the ILB frontend.

### Step 2 — ILB HA Ports selection

The Standard ILB receives the flow on frontend `10.0.2.10`.

HA Ports is configured with:

```text
Protocol:      All
Frontend port: 0
Backend port:  0
```

Azure Load Balancer selects a healthy backend per flow using connection properties including source IP, source port, destination IP, destination port, and protocol.

Example decision:

```text
10.10.1.4:53000 -> 10.20.1.4:443/TCP
                         |
                         +--> NVA-1 selected
```

A different flow may be sent to NVA-2.

### Step 3 — selected NVA receives transit traffic

The NVA NIC must have Azure IP forwarding enabled, and the NVA operating system/application must actually forward transit packets.

NVA-1 receives the flow, performs policy lookup, state creation, optional application/security inspection, and then SNAT.

Conceptually:

```text
Before NVA SNAT
SRC 10.10.1.4:53000
DST 10.20.1.4:443

After NVA SNAT
SRC 10.0.3.4:<translated-port>
DST 10.20.1.4:443
```

The exact translated source IP may be a dedicated egress/data-plane IP, loopback, or vendor-specific interface address. Use the vendor-supported HA design; do not assume every appliance should SNAT to its Azure NIC primary IP.

### Step 4 — NVA routes toward the PE

The NVA must have a valid route to `10.20.0.0/16` that does **not** send the packet back to its own ILB frontend.

This matters because Azure Load Balancer documents that outbound traffic from a backend VM to the frontend of the same internal load balancer is not a supported normal hairpin path.

The NVA should forward directly toward the PE VNet over hub-to-PE connectivity, subject to the vendor topology and Azure VNet routes.

### Step 5 — Private Endpoint receives the packet

The PE sees the translated NVA source and forwards the flow through Private Link to the PaaS service.

---

## 9. Exact ILB/NVA return packet flow

The return direction is where SNAT becomes essential.

### With NVA SNAT

The service/PE sees the connection as coming from the selected NVA.

The response is therefore conceptually:

```text
SRC 10.20.1.4:443
DST 10.0.3.4:<translated-port>
```

Return sequence:

1. PaaS sends the response through Private Link to the PE.
2. PE-side routing sends the reply toward the translated NVA source.
3. NVA-1 receives the packet because NVA-1 owns that NAT/session entry.
4. NVA-1 performs reverse SNAT.
5. The packet becomes:

```text
SRC 10.20.1.4:443
DST 10.10.1.4:53000
```

6. NVA-1 forwards the restored reply to the workload VNet.
7. The client receives a symmetric stateful session.

### Without SNAT

The destination can see the original client address:

```text
SRC 10.10.1.4
DST 10.20.1.4
```

The reply can then be routed directly toward `10.10.1.4`, bypassing the selected NVA/ILB path. The firewall would see only one direction and stateful inspection would fail or behave unpredictably.

This is why SNAT is the preferred PE-inspection design unless the NVA vendor documents another supported symmetry mechanism. Current Microsoft documentation also notes that some NVA scenarios can remove the SNAT requirement through the `disableSnatOnPL` mechanism; treat that as an advanced NVA-specific design and validate vendor support rather than assuming it applies universally.

---

## 10. HA behavior: what ILB does and does not provide

### What ILB HA Ports provides

- Per-flow distribution across healthy NVA backend instances.
- Health-probe-based removal of unhealthy instances.
- Active/active and some active/passive NVA patterns, depending on vendor support.
- A stable frontend next-hop IP for UDRs.

### What ILB does not automatically provide

- Firewall session-state synchronization between NVA-1 and NVA-2.
- Vendor policy synchronization.
- NAT-state synchronization.
- Guaranteed preservation of an existing stateful session if its NVA dies.
- NVA control-plane failover logic.

If NVA-1 fails after a session is established, ILB can stop sending **new** flows to it after health detection. Whether an existing connection survives depends on the appliance vendor's stateful HA mechanism. If NVA-2 does not possess NVA-1's session and NAT state, that session normally has to reconnect.

### Vendor validation checklist

Confirm with the NVA vendor:

- whether Standard ILB HA Ports is supported;
- whether Floating IP/direct-server-return behavior is required;
- which NIC/interface should be placed in the backend pool;
- whether one-arm or two-arm topology is supported;
- whether SNAT is required and to what address;
- whether the vendor supports the Private Link `disableSnatOnPL` design;
- how session synchronization works;
- health-probe port/path requirements;
- whether asymmetric return traffic is tolerated;
- whether the appliance supports active/active or active/passive behind ILB;
- whether multiple frontend IPs or multiple HA Ports rules are supported.

---

## 11. Azure CLI — create the ILB and NVA service insertion layer

The following commands create the Azure-side load-balancer constructs. They do **not** configure vendor firewall policy, HA clustering, NAT, or interface roles inside the NVA operating system.

### 11.1 Variables

```cli
RG=rg-pe-inspection
LOCATION=eastus2
HUB_VNET=vnet-hub
NVA_SUBNET=snet-nva
NVA_SUBNET_PREFIX=10.0.3.0/24

ILB=ilb-nva
ILB_FRONTEND=fe-nva
ILB_IP=10.0.2.10
ILB_BACKEND=be-nvas
ILB_PROBE=probe-nva
ILB_RULE=ha-ports-nva

NVA1_NIC=nic-nva1
NVA2_NIC=nic-nva2
```

### 11.2 Create NVA subnet if it does not already exist

```cli
az network vnet subnet create \
  --resource-group "$RG" \
  --vnet-name "$HUB_VNET" \
  --name "$NVA_SUBNET" \
  --address-prefixes "$NVA_SUBNET_PREFIX"
```

### 11.3 Create Standard internal Load Balancer

```cli
az network lb create \
  --resource-group "$RG" \
  --name "$ILB" \
  --location "$LOCATION" \
  --sku Standard \
  --vnet-name "$HUB_VNET" \
  --subnet "$NVA_SUBNET" \
  --frontend-ip-name "$ILB_FRONTEND" \
  --private-ip-address "$ILB_IP" \
  --backend-pool-name "$ILB_BACKEND"
```

Verify:

```cli
az network lb show \
  --resource-group "$RG" \
  --name "$ILB" \
  --query '{sku:sku.name,frontend:frontendIPConfigurations[0].privateIPAddress,backendPools:backendAddressPools[].name}' \
  --output json
```

**Expected state:** SKU `Standard`, frontend `10.0.2.10`, backend pool present.

### 11.4 Create an NVA health probe

Use a port that the appliance vendor explicitly documents for health checking. Example only:

```cli
az network lb probe create \
  --resource-group "$RG" \
  --lb-name "$ILB" \
  --name "$ILB_PROBE" \
  --protocol tcp \
  --port 9000
```

Do **not** blindly use TCP/9000 in production. The appliance must actually answer the configured probe in the intended health state.

### 11.5 Create the HA Ports rule

Microsoft documents HA Ports using protocol `All` and frontend/backend port `0`.

```cli
az network lb rule create \
  --resource-group "$RG" \
  --lb-name "$ILB" \
  --name "$ILB_RULE" \
  --protocol All \
  --frontend-port 0 \
  --backend-port 0 \
  --frontend-ip-name "$ILB_FRONTEND" \
  --backend-pool-name "$ILB_BACKEND" \
  --probe-name "$ILB_PROBE"
```

If your vendor requires Floating IP, use the vendor-supported rule form and validate it against current CLI help:

```cli
az network lb rule create --help
```

Do not enable Floating IP merely because an NVA is involved; Microsoft supports both floating and nonfloating HA Ports configurations, and the correct choice is architecture/vendor-specific.

### 11.6 Enable Azure NIC IP forwarding

```cli
az network nic update \
  --resource-group "$RG" \
  --name "$NVA1_NIC" \
  --ip-forwarding true

az network nic update \
  --resource-group "$RG" \
  --name "$NVA2_NIC" \
  --ip-forwarding true
```

Verify:

```cli
az network nic show \
  --resource-group "$RG" \
  --name "$NVA1_NIC" \
  --query '{nic:name,ipForwarding:enableIPForwarding,privateIPs:ipConfigurations[].privateIPAddress}' \
  --output json
```

**Success criteria:** `enableIPForwarding` is `true`.

### 11.7 Add NVA NICs to the ILB backend pool

The exact command depends on whether the backend pool is NIC-based or IP-based. For a NIC-based pool, update the relevant NIC IP configuration.

First inspect the IP configuration names:

```cli
az network nic ip-config list \
  --resource-group "$RG" \
  --nic-name "$NVA1_NIC" \
  --output table
```

Then associate the vendor-designated data-plane IP configuration with the backend pool using the current Azure CLI syntax for your deployment. Verify afterward with:

```cli
az network lb address-pool show \
  --resource-group "$RG" \
  --lb-name "$ILB" \
  --name "$ILB_BACKEND" \
  --output json
```

Because firewall vendors differ in NIC count, IP configuration, floating-IP requirements, and one-arm/two-arm architecture, this guide intentionally does not invent a universal NIC-association command that could place the wrong interface in the pool.

### 11.8 Can I link the ILB directly to a PaaS Private Endpoint without a UDR?

**No. Not for the Private Endpoint inspection design in this guide.**

For an Azure PaaS Private Endpoint such as Azure SQL, Storage, Key Vault, App Service, or another service exposed through Private Link, there is no property on the PE that accepts an Internal Load Balancer frontend as an inspection hop. There is also no ILB property that says "forward this frontend to that existing PaaS Private Endpoint."

If you omit the UDR or another supported route-steering mechanism, the normal path is conceptually:

```text
Client
  |
  | DNS resolves service FQDN -> 10.20.1.4
  v
Azure route lookup
  |
  | Private Endpoint / InterfaceEndpoint route
  v
Private Endpoint 10.20.1.4
  |
  v
Private Link -> PaaS
```

The ILB/NVA tier is **not in that path** simply because it exists in the hub.

The Standard ILB only becomes the NVA abstraction for this design when Azure is told to use the ILB frontend as the next hop for the PE destination prefix. In a classic VNet hub-and-spoke architecture, that is normally accomplished with the UDR described in sections 6.4 and 12.

Therefore, these two statements are both true:

```text
PE is linked to PaaS through Private Link.
ILB is linked to NVA backends through the Load Balancer backend pool/HA Ports rule.
```

But this statement is false for PaaS PE inspection:

```text
PE is linked directly to ILB.
```

### If you do not want to manage UDRs

You need a different service-insertion architecture rather than a hidden ILB-to-PE association. For example, in **Azure Virtual WAN**, a secured virtual hub with Azure Firewall can use Virtual WAN security/routing controls to steer private traffic without you manually placing a traditional UDR on every spoke subnet. That is a different architecture from this classic ILB-backed NVA pattern.

Microsoft's current Private Endpoint inspection guidance still describes route steering when an NVA or Azure Firewall must intercept traffic destined to a PE. In a traditional hub-and-spoke topology, there is no automatic ILB interception mechanism for an existing Azure PaaS Private Endpoint.

### 11.9 Why Private Link Service looks similar but is a different architecture

Azure **Private Link Service (PLS)** is the source of much of the confusion because PLS really does reference an **internal Standard Load Balancer frontend**.

A provider-owned application can look like this:

```text
Consumer VNet
  |
  | Private Endpoint
  v
Private Link
  |
  v
Private Link Service
  |
  | references Standard ILB frontend
  v
Internal Standard Load Balancer
  |
  v
Provider application backends
```

That is a valid no-UDR Private Link pattern for **publishing your own service**.

The provider creates a Private Link Service against an ILB frontend, conceptually:

```cli
az network private-link-service create \
  --resource-group <PROVIDER_RG> \
  --name <PLS_NAME> \
  --vnet-name <PROVIDER_VNET> \
  --subnet <PLS_NAT_SUBNET> \
  --lb-name <PROVIDER_ILB> \
  --lb-frontend-ip-configs <ILB_FRONTEND_NAME>
```

A consumer then creates a Private Endpoint **to that Private Link Service**.

That does **not** let you take this existing relationship:

```text
Private Endpoint -> Azure SQL / Storage / Key Vault / other Azure PaaS
```

and insert your NVA ILB in the middle as:

```text
Private Endpoint -> ILB -> NVA -> existing Azure PaaS Private Endpoint
```

Those are different Private Link roles:

| Design | What the Private Endpoint connects to | Is ILB directly referenced? |
|---|---|---|
| Azure PaaS Private Endpoint | Azure PaaS Private Link resource/subresource | **No** |
| Customer Private Link Service | Customer-created Private Link Service | **Yes, by the PLS on the provider side** |
| ILB-backed NVA inspection of PaaS PE | Existing PaaS PE remains destination; NVA inserted by routing | **No direct PE↔ILB link** |

So if your goal is specifically **inspect traffic destined to an Azure PaaS Private Endpoint through third-party NVAs behind an ILB**, the ILB architecture requires traffic steering. If your goal is instead **publish an application behind an ILB privately to consumers**, Private Link Service is the correct no-UDR construct.

---

## 12. Create workload UDR to the ILB frontend

```cli
APP_VNET=vnet-app
APP_SUBNET=snet-app
APP_RT=rt-app-pe-via-nva
PE_PREFIX=10.20.0.0/16

az network route-table create \
  --resource-group "$RG" \
  --name "$APP_RT" \
  --location "$LOCATION"

az network route-table route create \
  --resource-group "$RG" \
  --route-table-name "$APP_RT" \
  --name pe-via-ilb-nva \
  --address-prefix "$PE_PREFIX" \
  --next-hop-type VirtualAppliance \
  --next-hop-ip-address "$ILB_IP"

az network vnet subnet update \
  --resource-group "$RG" \
  --vnet-name "$APP_VNET" \
  --name "$APP_SUBNET" \
  --route-table "$APP_RT"
```

Configured route verification:

```cli
az network route-table route list \
  --resource-group "$RG" \
  --route-table-name "$APP_RT" \
  --output table
```

Illustrative expected shape:

```text
Name            AddressPrefix   NextHopType       NextHopIpAddress
--------------  --------------  ----------------  ----------------
pe-via-ilb-nva  10.20.0.0/16    VirtualAppliance  10.0.2.10
```

---

## 13. Verify the source NIC effective route

```cli
CLIENT_NIC=<client-vm-nic-name>

az network nic show-effective-route-table \
  --resource-group "$RG" \
  --name "$CLIENT_NIC" \
  --output table
```

**What it tests:** the actual route Azure installed for the workload NIC.

**Success criteria:** the PE VNet/subnet or `/32` prefix resolves to `VirtualAppliance` and next-hop IP `10.0.2.10`.

**Failure indicators:**

- a more-specific `InterfaceEndpoint` route is still winning;
- route table is attached to the wrong subnet;
- destination prefix is too broad;
- PE network policies are disabled;
- UDR points directly to an NVA instead of the intended ILB VIP.

For one concrete destination, also use Network Watcher Next Hop:

```cli
az network watcher show-next-hop \
  --resource-group "$RG" \
  --vm <client-vm-name> \
  --nic "$CLIENT_NIC" \
  --source-ip 10.10.1.4 \
  --dest-ip 10.20.1.4 \
  --output table
```

The expected selected next hop is the virtual-appliance path associated with the ILB next-hop design, not a direct PE route.

---

## 14. Verify ILB rule and health configuration

```cli
az network lb rule show \
  --resource-group "$RG" \
  --lb-name "$ILB" \
  --name "$ILB_RULE" \
  --output json
```

Important fields:

```text
protocol            = All
frontendPort        = 0
backendPort         = 0
frontendIP config   = fe-nva
backend pool        = be-nvas
probe               = probe-nva
```

Probe configuration:

```cli
az network lb probe show \
  --resource-group "$RG" \
  --lb-name "$ILB" \
  --name "$ILB_PROBE" \
  --output json
```

**Success criteria:** probe settings match the vendor's supported health endpoint and NVA instances are healthy.

**Failure means:** ILB may have no usable backend or may steer new flows away from an unhealthy appliance.

---

## 15. NVA routing requirements

The NVA needs three logical routing outcomes:

1. **From the client side:** accept transit traffic delivered by the ILB.
2. **Toward the PE:** route `10.20.0.0/16` toward the PE VNet, not back to the ILB VIP.
3. **Toward the workload:** after reverse NAT, route `10.10.0.0/16` back toward the workload spoke.

A generic conceptual NVA table is:

```text
10.10.0.0/16 -> Azure VNet path toward workload spoke
10.20.0.0/16 -> Azure VNet path toward PE spoke
0.0.0.0/0    -> vendor/enterprise-defined default path
```

The exact appliance CLI must come from the firewall vendor because route table names, zones, VRFs, next-hop rules, and HA semantics differ.

---

## 16. NAT policy on the NVA

The PE-inspection flow should normally be SNATed on the selected firewall instance or on a vendor-supported shared egress identity.

Conceptual rule:

```text
Source zone:       workload/transit
Source prefix:     10.10.0.0/16
Destination:       10.20.0.0/16 or PE objects
Service:           required PaaS ports
Action:            allow/inspect
Source NAT:        vendor-supported NVA egress identity
Destination NAT:   none
```

Do not DNAT the PE destination. The client must still address the real PE IP/FQDN. The firewall is inserted in the transit path; it is not replacing the Private Endpoint.

### Why a shared SNAT address may matter

Some active/active firewall products can synchronize NAT state or use a shared/floating identity. Others use node-local SNAT addresses. Either can work if the vendor supports it, but the failure behavior differs.

If NVA-1 SNATs to a node-local address and dies, existing sessions tied to that NAT state may fail. A shared stateful cluster can provide better continuity if supported.

---

## 17. Flow symmetry and HA Ports

Azure Load Balancer documentation describes HA Ports flow symmetry for supported NVA configurations behind one internal Standard Load Balancer. This does **not** replace NVA SNAT for Private Endpoint inspection.

There are two different symmetry problems:

### Problem A — ILB backend selection symmetry

For traffic that traverses the ILB in both directions in a supported topology, Azure can maintain a consistent backend mapping for the flow.

### Problem B — Private Endpoint return-path symmetry

The PE-side destination must still return through the same stateful inspection path. SNAT makes the return destination the firewall/session owner and is therefore the safer Private Endpoint design.

Do not confuse "HA Ports supports flow symmetry" with "Private Endpoint SNAT is unnecessary." They solve different parts of the path.

---

## 18. Important Azure Load Balancer constraints

### Standard SKU only

HA Ports is available on **internal Standard Load Balancer**.

### Per-flow load balancing

The ILB hashes each flow. It does not send every packet round-robin independently.

### Health probes affect backend eligibility

A failed probe removes an NVA from new-flow selection until it becomes healthy again.

### Backend-to-own-frontend hairpin limitation

Azure documents that outbound traffic from a backend VM to the frontend of its own internal load balancer fails. Design the NVA's PE-facing routing so it does not send the packet back into the same ILB frontend.

### IP fragmentation

Microsoft documents limitations around IP fragmentation with Load Balancer rules. Validate MTU/MSS behavior for overlays, VPNs, TLS inspection, or encapsulating NVA products.

### TCP idle timeout with UDR + HA Ports

Microsoft documents that TCP idle timeout is not supported for internal Load Balancer HA Ports when a UDR is used to forward traffic to the ILB. Account for application keepalives and vendor behavior.

---

## 19. DNS path remains unchanged

The inspection device is not the Private Endpoint DNS authority.

The client should resolve the normal service hostname, for example:

```text
myserver.database.windows.net
```

through the appropriate private DNS chain to the PE address, for example:

```text
myserver.privatelink.database.windows.net -> 10.20.1.4
```

Verify:

```cli
nslookup myserver.database.windows.net
```

or:

```cli
dig myserver.database.windows.net
```

If DNS returns a public address, you are not testing the PE inspection path.

---

## 20. Peering requirements

A common topology is:

```text
Workload spoke <-> Hub/NVA VNet <-> PE spoke
```

VNet peering is non-transitive by itself. The NVA is the routed transit point.

For this customer-managed NVA hub model, create both peering directions and allow forwarded traffic. Example for workload ↔ hub:

```cli
HUB_VNET_ID=$(az network vnet show -g "$RG" -n vnet-hub --query id -o tsv)
APP_VNET_ID=$(az network vnet show -g "$RG" -n vnet-app --query id -o tsv)
PE_VNET_ID=$(az network vnet show -g "$RG" -n vnet-pe --query id -o tsv)

az network vnet peering create \
  --resource-group "$RG" \
  --vnet-name vnet-app \
  --name app-to-hub \
  --remote-vnet "$HUB_VNET_ID" \
  --allow-vnet-access \
  --allow-forwarded-traffic

az network vnet peering create \
  --resource-group "$RG" \
  --vnet-name vnet-hub \
  --name hub-to-app \
  --remote-vnet "$APP_VNET_ID" \
  --allow-vnet-access \
  --allow-forwarded-traffic
```

And hub ↔ PE VNet:

```cli
az network vnet peering create \
  --resource-group "$RG" \
  --vnet-name vnet-hub \
  --name hub-to-pe \
  --remote-vnet "$PE_VNET_ID" \
  --allow-vnet-access \
  --allow-forwarded-traffic

az network vnet peering create \
  --resource-group "$RG" \
  --vnet-name vnet-pe \
  --name pe-to-hub \
  --remote-vnet "$HUB_VNET_ID" \
  --allow-vnet-access \
  --allow-forwarded-traffic
```

Unlike the Azure Route Server/gateway-transit pattern, these peerings do not inherently require `--allow-gateway-transit`/`--use-remote-gateways` merely to pass NVA-forwarded traffic. Those flags are used when the spoke must consume a remote VNet gateway/Route Server function.

Do not add a direct workload-to-PE peering path unless you deliberately control it; an alternate direct path can undermine centralized inspection.

---

## 21. Failure scenarios

### NVA-1 health probe fails before a new session

Expected behavior:

1. ILB marks NVA-1 unhealthy after the configured probe behavior.
2. New flows are sent to healthy backends such as NVA-2.
3. NVA-2 creates new firewall/NAT state.

### NVA-1 dies during an existing session

Possible outcomes depend on vendor HA:

- **No state sync:** existing session fails and client reconnects.
- **State/NAT sync:** NVA-2 may continue the flow if the vendor architecture supports takeover.
- **Shared/floating identity:** continuity depends on vendor implementation and Azure LB compatibility.

Do not claim zero-loss failover merely because ILB health probes are configured.

### Both NVAs unhealthy

No healthy backend exists. New flows fail. The UDR still points to the ILB VIP, so Azure does not automatically bypass inspection unless you build a separate fail-open routing mechanism.

### SNAT not configured

Symptoms commonly include:

- SYN reaches the NVA and PE;
- application times out;
- NVA sees only outbound direction;
- return path bypasses the appliance;
- session table remains incomplete.

### PE network policies disabled

The client effective route can still prefer the PE-specific route, bypassing the ILB/NVA.

---

## 22. Troubleshooting by symptom

### Symptom: NVA logs show nothing

**Where:** client NIC effective routes.  
**Command:**

```cli
az network nic show-effective-route-table -g "$RG" -n "$CLIENT_NIC" -o table
```

**What it tests:** whether the client sends PE traffic to the ILB VIP.

**Expected:** PE prefix -> `VirtualAppliance` -> `10.0.2.10`.

**Failure means:** route specificity, subnet association, or PE policy problem.

**Next action:** correct routing before debugging the NVA.

### Symptom: DNS resolves PE correctly, but effective route still uses InterfaceEndpoint/direct PE

**Where:** PE subnet policy plus workload effective routes.

**Commands:**

```cli
az network vnet subnet show \
  -g "$RG" \
  --vnet-name "$PE_VNET" \
  -n "$PE_SUBNET" \
  --query privateEndpointNetworkPolicies \
  -o tsv

az network route-table route list \
  -g "$RG" \
  --route-table-name "$APP_RT" \
  -o table
```

**What it tests:** whether the PE subnet permits UDR enforcement and whether the UDR is sufficiently specific.

**Failure means:** network policies are still disabled or the UDR prefix is too broad.

**Next action:** enable PE UDR policy and use the PE VNet/subnet or PE `/32` prefix.

### Symptom: ILB receives flows but one NVA never gets traffic

**Where:** ILB backend pool and health probes.  
**Commands:**

```cli
az network lb address-pool show -g "$RG" --lb-name "$ILB" -n "$ILB_BACKEND" -o json
az network lb probe show -g "$RG" --lb-name "$ILB" -n "$ILB_PROBE" -o json
```

**What it tests:** membership and health configuration.

**Failure means:** wrong NIC/IP configuration, probe service down, NSG blocking probe, or vendor probe mismatch.

### Symptom: NVA receives forward traffic but client times out

**Where:** NVA session/NAT table and return routing.

**What it tests:** state symmetry.

**Expected:** a SNAT entry exists, response hits the same logical firewall state, reverse NAT occurs.

**Failure means:** no SNAT, wrong PE-facing route, state-sync issue, or vendor HA mismatch.

### Symptom: NVA sends traffic back to ILB frontend and it disappears

**Where:** NVA route table.

**Cause:** backend-to-own-frontend hairpin design.

**Next action:** give the NVA a direct routed path toward the PE VNet instead of sending the post-inspection leg back to its own ILB VIP.

### Symptom: PE connection works when firewall is bypassed but fails through NVA

Check in order:

1. DNS resolves the service FQDN to the PE IP;
2. PE connection state is approved;
3. PE subnet UDR policy is enabled;
4. client effective route selects the ILB VIP;
5. ILB HA Ports rule exists;
6. health probe is correct;
7. correct NVA interface is in the backend pool;
8. backend NIC IP forwarding is enabled;
9. NVA transit forwarding works;
10. NVA security policy permits the flow;
11. NVA SNAT is present unless using a specifically supported no-SNAT Private Link design;
12. NVA PE-facing route does not hairpin to ILB;
13. PaaS-specific ports and connection mode are correct.

---

## 23. Azure Firewall vs ILB/NVA comparison

| Area | Azure Firewall | ILB + third-party NVA |
|---|---|---|
| Managed HA | Azure-managed | ILB plus vendor HA design |
| UDR next hop | Firewall private IP | ILB frontend IP |
| Direct resource attachment to PE | **None** — routing inserts firewall | **None** — routing inserts ILB/NVA |
| Scale/failover | Service-managed | Health probe + backend pool + vendor clustering |
| SNAT for PE flow | Application rules always SNAT | Must normally be designed/configured in NVA |
| FQDN policy | Native firewall features | Vendor-specific |
| TLS inspection | Premium feature where supported | Vendor-specific |
| Session synchronization | Managed service behavior | Vendor-specific |
| CLI for Azure plumbing | Azure Firewall CLI | Azure LB + NIC + route CLI |
| Firewall policy CLI | Azure-native | Vendor CLI/API/Terraform/etc. |
| Operational complexity | Lower | Higher but more vendor flexibility |

---

## 24. Common mistakes

- Assuming the ILB must be attached or associated directly with the Private Endpoint object.
- Assuming Private Link Service can be used to insert an ILB/NVA in front of an already-existing Azure PaaS Private Endpoint.
- DNATing the PE address to the ILB VIP; the destination should remain the real PE IP.
- Putting a route on the wrong subnet and expecting the PE object itself to discover the ILB.
- Assuming Private Endpoint inspection requires Azure Firewall; third-party NVAs are valid.
- Assuming an NVA VM alone is highly available without an HA mechanism.
- Pointing the UDR directly at one NVA when the intended design is an ILB-backed NVA pool.
- Using Basic Load Balancer instead of Standard ILB.
- Creating a normal port-specific LB rule instead of HA Ports when the design requires all transit ports/protocols.
- Using an arbitrary health-probe port that the appliance does not support.
- Forgetting Azure NIC IP forwarding.
- Forgetting OS/appliance forwarding even though Azure NIC IP forwarding is enabled.
- Omitting SNAT on the PE-facing leg without a vendor-supported alternative.
- Assuming HA Ports removes the need for firewall session-state synchronization.
- Hairpinning an NVA backend back into its own ILB frontend.
- Leaving Private Endpoint network policies disabled.
- Relying on `0.0.0.0/0` alone to capture PE traffic.
- Debugging routing while DNS still returns the public PaaS address.
- Creating an alternate direct spoke-to-PE path that bypasses inspection.

---

## 25. Recommended production design sequence

1. Put Private Endpoints in a dedicated subnet or VNet.
2. Create the PE against the intended PaaS subresource and record its actual private IP.
3. Configure Private DNS so applications resolve the service name to that PE IP.
4. Enable Private Endpoint network policies for UDR support.
5. Build hub-to-workload and hub-to-PE connectivity with forwarded traffic allowed where required.
6. Deploy two or more vendor-supported NVA instances.
7. Enable IP forwarding on the NVA data-plane NICs.
8. Create an internal **Standard** Load Balancer.
9. Put the vendor-designated NVA interface/IP configuration in the backend pool.
10. Create a vendor-supported health probe.
11. Create an HA Ports rule (`All`, `0`, `0`).
12. Configure the NVA routing table so PE-facing traffic exits toward the PE VNet, not back into the ILB VIP.
13. Configure security policy and SNAT, unless the vendor explicitly supports an alternate Private Link symmetry design.
14. Add **source-subnet** UDRs for the PE VNet/subnet or `/32`, with next hop equal to the ILB frontend IP.
15. Validate the client effective route for the PE IP.
16. Establish a test connection and verify that the NVA sees the destination as the **real PE IP**, not the ILB IP.
17. Verify the NVA's translated source and PE-facing route.
18. Verify the return packet hits the same logical firewall state and reverse NAT occurs.
19. Fail one NVA and measure new-flow behavior and existing-flow behavior separately.
20. Document whether the vendor provides state/NAT synchronization and what sessions are expected to survive failover.

---

## 26. Source information, additional explanation, and inference

### Source information

Microsoft documentation directly supports the following:

- Private Endpoint traffic can be inspected by Azure Firewall or a third-party NVA.
- Private Endpoint network policies must be enabled to use UDR/NSG enforcement for PEs.
- A generic default route does not automatically override a PE-specific route.
- When UDR policy is enabled, the overriding UDR must meet the documented prefix-specificity requirements relative to the PE VNet address space.
- SNAT is recommended for inspected Private Endpoint traffic, subject to documented advanced NVA exceptions.
- Azure Firewall application rules always SNAT.
- A Private Endpoint is created against a target resource/subresource and owns a private NIC/IP in the selected subnet.
- A Private Link Service can reference an internal Standard Load Balancer frontend when publishing a customer-owned provider service; that is distinct from inspecting an existing Azure PaaS Private Endpoint.
- Internal Standard Load Balancer supports HA Ports for NVA high availability/scale.
- HA Ports uses protocol `All` and port `0`.
- Load Balancer uses per-flow selection and health probes.
- Azure Architecture Center documents UDR-to-ILB-frontend patterns for NVA service insertion.
- Outbound flow from an ILB backend VM to that same ILB frontend is a platform limitation.

### Additional explanation

There is no direct ILB-to-PaaS-PE resource association. The packet walks in this guide combine the documented primitives into the actual PE inspection design:

```text
DNS -> PE IP
source-subnet UDR -> ILB VIP
ILB -> selected NVA
NVA inspection/SNAT -> real PE IP
Private Link -> service
return -> SNAT/session owner -> reverse NAT -> client
```

Private Link Service is a separate provider-publishing model:

```text
Consumer PE -> Private Link Service -> provider ILB -> provider backends
```

It is not an interception mechanism for an already-existing PaaS PE.

### Reasonable inference

The exact firewall-side SNAT address, session replication mechanics, zone names, VRFs, route-table identifiers, and failover behavior are vendor-specific. They must not be assumed from Azure ILB behavior alone.

---

## Sources

- Microsoft Learn — Azure Firewall scenarios to inspect traffic destined to a private endpoint: https://learn.microsoft.com/en-us/azure/private-link/inspect-traffic-with-azure-firewall
- Microsoft Learn — Tutorial: Inspect private endpoint traffic with Azure Firewall: https://learn.microsoft.com/en-us/azure/private-link/tutorial-inspect-traffic-azure-firewall
- Microsoft Learn — Manage network policies for private endpoints: https://learn.microsoft.com/en-us/azure/private-link/disable-private-endpoint-network-policy
- Microsoft Learn — What is a private endpoint?: https://learn.microsoft.com/en-us/azure/private-link/private-endpoint-overview
- Microsoft Learn — Create a private endpoint with Azure CLI: https://learn.microsoft.com/en-us/azure/private-link/create-private-endpoint-cli
- Microsoft Learn — `az network private-endpoint`: https://learn.microsoft.com/en-us/cli/azure/network/private-endpoint?view=azure-cli-latest
- Microsoft Learn — Private Link Service overview: https://learn.microsoft.com/en-us/azure/private-link/private-link-service-overview
- Microsoft Learn — `az network private-link-service`: https://learn.microsoft.com/en-us/cli/azure/network/private-link-service?view=azure-cli-latest
- Microsoft Learn — Secure your Azure Private Link deployment: https://learn.microsoft.com/en-us/azure/private-link/secure-private-link
- Microsoft Learn — Azure Firewall SNAT private IP address ranges: https://learn.microsoft.com/en-us/azure/firewall/snat-private-range
- Microsoft Learn — High availability ports overview: https://learn.microsoft.com/en-us/azure/load-balancer/load-balancer-ha-ports-overview
- Microsoft Learn — Azure Load Balancer components: https://learn.microsoft.com/en-us/azure/load-balancer/components
- Microsoft Learn — Create an internal Standard Load Balancer with Azure CLI: https://learn.microsoft.com/en-us/azure/load-balancer/quickstart-load-balancer-standard-internal-cli
- Microsoft Learn — `az network lb rule`: https://learn.microsoft.com/en-us/cli/azure/network/lb/rule?view=azure-cli-latest
- Azure Architecture Center — Deploy highly available NVAs: https://learn.microsoft.com/en-us/azure/architecture/example-scenario/firewalls/
