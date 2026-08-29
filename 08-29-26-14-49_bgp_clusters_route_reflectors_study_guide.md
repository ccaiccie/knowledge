# BGP Clusters: Route Reflectors, Cluster IDs, and Hierarchical Design

> **Generated:** 2026-08-29 14:49 PDT  
> **Primary standard:** RFC 4456 — BGP Route Reflection  
> **Scope:** Route-reflector clusters, client/non-client rules, ORIGINATOR_ID, CLUSTER_LIST, redundancy, hierarchy, Cisco IOS XE/IOS XR, Junos, verification, and troubleshooting.

## URLs reviewed

- https://www.rfc-editor.org/rfc/rfc4456.html
- https://www.cisco.com/c/en-us/td/docs/routers/ios/config/17-x/ip-routing/b-ip-routing/m_irg-multicluster-id.html
- https://www.cisco.com/c/en/us/support/docs/ip/border-gateway-protocol-bgp/200153-BGP-Route-Reflection-and-Multiple-Cluste.html
- https://www.cisco.com/c/en/us/td/docs/iosxr/cisco8000/bgp/bgp-config-cisco8000/r-wrapper-bgp-routing-optimisation-and-convergence-techniques/c-bgp-route-reflectors.html
- https://www.juniper.net/documentation/us/en/software/junos/bgp/topics/topic-map/bgp-rr.html
- https://www.juniper.net/documentation/us/en/software/junos/cli-reference/topics/ref/statement/cluster-edit-protocols-bgp.html

## Overview

A **BGP cluster** is a control-plane grouping used by **BGP route reflection**. It is not an IP subnet, a forwarding domain, a VRF, or a separate autonomous system.

Ordinary Internal BGP (IBGP) does not readvertise a route learned from one IBGP peer to another IBGP peer. Therefore, without route reflection, routers needing full IBGP visibility normally require a logical full mesh.

For `N` routers, a full mesh requires:

```text
N x (N - 1) / 2
```

| Routers | IBGP sessions |
|---:|---:|
| 10 | 45 |
| 50 | 1,225 |
| 100 | 4,950 |

A **route reflector (RR)** relaxes this IBGP split-horizon rule for selected peers called **route-reflector clients**.

![BGP route-reflector cluster](data:image/svg+xml;base64,PHN2ZyB4bWxucz0iaHR0cDovL3d3dy53My5vcmcvMjAwMC9zdmciIHdpZHRoPSIxMDAwIiBoZWlnaHQ9IjU2MCIgdmlld0JveD0iMCAwIDEwMDAgNTYwIj4KPHJlY3Qgd2lkdGg9IjEwMDAiIGhlaWdodD0iNTYwIiBmaWxsPSJ3aGl0ZSIvPgo8dGV4dCB4PSI1MDAiIHk9IjM4IiB0ZXh0LWFuY2hvcj0ibWlkZGxlIiBmb250LWZhbWlseT0iQXJpYWwiIGZvbnQtc2l6ZT0iMjYiIGZvbnQtd2VpZ2h0PSJib2xkIj5CR1AgUm91dGUtUmVmbGVjdG9yIENsdXN0ZXIgYW5kIExvb3AgUHJldmVudGlvbjwvdGV4dD4KPGVsbGlwc2UgY3g9IjUwMCIgY3k9IjMwMCIgcng9IjQxMCIgcnk9IjIwNSIgZmlsbD0iI2Y1ZjVmNSIgc3Ryb2tlPSIjMzMzIiBzdHJva2Utd2lkdGg9IjMiLz4KPHRleHQgeD0iMTY1IiB5PSIxMjUiIGZvbnQtZmFtaWx5PSJBcmlhbCIgZm9udC1zaXplPSIyMCIgZm9udC13ZWlnaHQ9ImJvbGQiPkNsdXN0ZXIgSUQgMTAuMjU1LjAuMTAwPC90ZXh0Pgo8Y2lyY2xlIGN4PSI1MDAiIGN5PSIxODUiIHI9IjU1IiBmaWxsPSJ3aGl0ZSIgc3Ryb2tlPSIjMTExIiBzdHJva2Utd2lkdGg9IjMiLz4KPHRleHQgeD0iNTAwIiB5PSIxODAiIHRleHQtYW5jaG9yPSJtaWRkbGUiIGZvbnQtZmFtaWx5PSJBcmlhbCIgZm9udC1zaXplPSIyMSIgZm9udC13ZWlnaHQ9ImJvbGQiPlJSMTwvdGV4dD4KPHRleHQgeD0iNTAwIiB5PSIyMDciIHRleHQtYW5jaG9yPSJtaWRkbGUiIGZvbnQtZmFtaWx5PSJBcmlhbCIgZm9udC1zaXplPSIxNiI+Um91dGUgUmVmbGVjdG9yPC90ZXh0Pgo8Y2lyY2xlIGN4PSIyNDUiIGN5PSIzNjUiIHI9IjUyIiBmaWxsPSJ3aGl0ZSIgc3Ryb2tlPSIjMTExIiBzdHJva2Utd2lkdGg9IjMiLz4KPHRleHQgeD0iMjQ1IiB5PSIzNzIiIHRleHQtYW5jaG9yPSJtaWRkbGUiIGZvbnQtZmFtaWx5PSJBcmlhbCIgZm9udC1zaXplPSIxOSI+Q2xpZW50IEE8L3RleHQ+CjxjaXJjbGUgY3g9IjUwMCIgY3k9IjQzNSIgcj0iNTIiIGZpbGw9IndoaXRlIiBzdHJva2U9IiMxMTEiIHN0cm9rZS13aWR0aD0iMyIvPgo8dGV4dCB4PSI1MDAiIHk9IjQ0MiIgdGV4dC1hbmNob3I9Im1pZGRsZSIgZm9udC1mYW1pbHk9IkFyaWFsIiBmb250LXNpemU9IjE5Ij5DbGllbnQgQjwvdGV4dD4KPGNpcmNsZSBjeD0iNzU1IiBjeT0iMzY1IiByPSI1MiIgZmlsbD0id2hpdGUiIHN0cm9rZT0iIzExMSIgc3Ryb2tlLXdpZHRoPSIzIi8+Cjx0ZXh0IHg9Ijc1NSIgeT0iMzcyIiB0ZXh0LWFuY2hvcj0ibWlkZGxlIiBmb250LWZhbWlseT0iQXJpYWwiIGZvbnQtc2l6ZT0iMTkiPkNsaWVudCBDPC90ZXh0Pgo8ZyBzdHJva2U9IiMzMzMiIHN0cm9rZS13aWR0aD0iNCI+PGxpbmUgeDE9IjQ2MCIgeTE9IjIyNSIgeDI9IjI4MCIgeTI9IjMyNSIvPjxsaW5lIHgxPSI1MDAiIHkxPSIyNDAiIHgyPSI1MDAiIHkyPSIzODMiLz48bGluZSB4MT0iNTQwIiB5MT0iMjI1IiB4Mj0iNzIwIiB5Mj0iMzI1Ii8+PC9nPgo8dGV4dCB4PSI1MDAiIHk9IjUyNSIgdGV4dC1hbmNob3I9Im1pZGRsZSIgZm9udC1mYW1pbHk9IkFyaWFsIiBmb250LXNpemU9IjE3Ij5SZWZsZWN0ZWQgcm91dGVzIGNhcnJ5IE9SSUdJTkFUT1JfSUQgYW5kIENMVVNURVJfTElTVCB0byBwcmV2ZW50IGNvbnRyb2wtcGxhbmUgbG9vcHMuPC90ZXh0Pgo8L3N2Zz4=)

**What this image shows:** RR1 and three RR clients in one cluster.

**What matters:** Clients do not require a full IBGP mesh with one another. RR1 is permitted to reflect eligible IBGP routes.

**What to verify:** Confirm each intended client has an established IBGP session to the RR, the neighbor is actually marked as an RR client on the RR, and the cluster ID is intentional and stable.

## Core terms

| Term | Meaning |
|---|---|
| **AS** | BGP autonomous system identified by an ASN. |
| **RR** | Route reflector; an IBGP speaker allowed to reflect certain IBGP-learned routes. |
| **Client** | IBGP neighbor configured as a route-reflector client on the RR. |
| **Non-client** | Ordinary IBGP neighbor of an RR. |
| **Cluster** | RR plus the clients associated with a reflection domain. |
| **Cluster ID** | 32-bit identifier used by RR loop prevention. |
| **ORIGINATOR_ID** | Router ID of the original IBGP speaker whose route was reflected. |
| **CLUSTER_LIST** | Sequence of cluster IDs traversed by a reflected route. |

## Why route reflection is needed

Without an RR:

```text
R1 ---iBGP--- R2 ---iBGP--- R3
```

If R1 sends a route to R2, R2 does not ordinarily advertise that IBGP-learned route to R3. R1 and R3 therefore need their own IBGP relationship.

With an RR:

```text
Client-A
   |
   v
   RR
  /  \
 v    v
B      C
```

The RR can readvertise the route according to route-reflection rules.

## Reflection rules

The practical rules are:

| Route learned by RR from | Advertise to RR clients? | Advertise to IBGP non-clients? |
|---|---:|---:|
| EBGP peer | Yes | Yes |
| Locally originated | Yes | Yes |
| RR client | Yes | Yes |
| IBGP non-client | Yes | No, under normal IBGP rules |

Memory aid:

```text
Client -> RR -> client       allowed
Client -> RR -> non-client   allowed
Non-client -> RR -> client   allowed
Non-client -> RR -> non-client   not normally reflected
```

This distinction explains many multi-RR troubleshooting problems.

## Cluster ID

RFC 4456 defines a cluster identifier as a 4-byte value. Vendors commonly display it in dotted-decimal form, such as:

```text
10.255.0.100
```

A cluster ID is not:

- an ASN,
- a prefix,
- a next hop,
- a route distinguisher,
- a route target.

It is a route-reflection loop-prevention identifier.

Some implementations use the BGP router ID as an implicit/default cluster ID if an explicit value is not configured. Explicit IDs generally make troubleshooting and replacement planning easier.

## ORIGINATOR_ID

When an RR first reflects an IBGP route, it creates the optional non-transitive **ORIGINATOR_ID** attribute if one is not already present.

Example:

```text
Original client BGP router ID: 10.0.0.1
Prefix:                        203.0.113.0/24

After reflection:
ORIGINATOR_ID = 10.0.0.1
```

If that route later returns to the original speaker, the router sees its own BGP identifier as ORIGINATOR_ID and ignores the route.

## CLUSTER_LIST

Each RR adds its cluster identifier to **CLUSTER_LIST** when reflecting a route.

Example:

```text
Client A
   |
   v
RR1 cluster 100
   |
   v
RR2 cluster 200
```

After RR1:

```text
ORIGINATOR_ID = 10.0.0.1
CLUSTER_LIST  = 100
```

After RR2:

```text
ORIGINATOR_ID = 10.0.0.1
CLUSTER_LIST  = 200 100
```

If RR1 later receives the route and sees cluster `100` already in CLUSTER_LIST, it rejects the update.

The exact visual ordering used by show commands varies by implementation; the key concept is that the attribute records the reflection path through clusters.

## Route-selection effect

RFC 4456 also modifies BGP tie breaking for reflected routes. Two important details are:

- ORIGINATOR_ID is used where the originating BGP identifier matters.
- An otherwise comparable path with a **shorter CLUSTER_LIST** should be preferred before later tie breakers.

CLUSTER_LIST is not normally an early best-path criterion; higher-priority BGP attributes still win first.

## Control plane versus data plane

The RR does not need to forward the traffic for the prefixes it reflects.

Control plane:

```text
Edge -> RR -> Client
```

Possible data plane:

```text
Client -> P1 -> P2 -> Edge
```

This matters because the RR may choose the best path using **its own IGP perspective**, while the downstream client is somewhere else in the topology.

## Route-reflector path hiding

A conventional RR usually reflects its selected best path rather than every candidate.

```text
Edge-A ---\
           RR ---- Client-X
Edge-B ---/
```

If RR chooses Edge-A, Client-X might never learn Edge-B even if Edge-B would be better from Client-X's location.

This is **RR path hiding**.

Depending on vendor and design, mitigation can include:

- BGP Add-Path,
- Optimal Route Reflection (ORR),
- topologically diverse RRs,
- better RR placement,
- designs that preserve alternate-path visibility.

Route-reflector redundancy alone does not guarantee path diversity.

## Redundant route reflectors

A common design dual-homes clients to two RRs:

```text
RR1       RR2
 \       /
  \     /
   Client
```

This protects the BGP control plane from a single RR failure.

However, two RRs can still select and advertise the same path, so RR redundancy is not the same thing as multipath.

### Should two redundant RRs use the same cluster ID?

Do not treat this as an unconditional rule.

RFC 4456 allows multiple RRs in one cluster, and shared cluster IDs can be used so an RR recognizes that a route has already traversed that cluster.

However, vendor topology guidance introduces important nuances. Juniper specifically documents designs where a redundant RR must use a **different cluster ID** to accept/reflect routes toward other clusters rather than discarding them as same-cluster routes.

Choose the cluster-ID strategy after answering:

- Are the RRs serving the same client set?
- Do the RRs peer with each other?
- Are they clients of an upper-tier RR?
- Must RR2 accept a route already reflected by RR1?
- Are they one logical cluster or intentionally separate reflection domains?

## Multiple clusters

For larger networks, clients can be divided into several clusters.

```text
Cluster A -> RR-A
Cluster B -> RR-B
Cluster C -> RR-C
```

RRs then need an intentional inter-cluster route-distribution topology.

A simple option is to full-mesh the RRs. This scales much better than full-meshing every BGP speaker, but at very large scale the RR mesh can itself become large.

## Hierarchical route reflection

A lower-tier RR can be a client of an upper-tier RR:

```text
             RR-Core
            /   |   \
         RR-A  RR-B  RR-C
          |     |     |
       clients clients clients
```

Juniper documents this as a “cluster of clusters” approach.

Advantages:

- smaller RR-to-RR mesh,
- geographic hierarchy,
- easier scaling of large ASes.

Tradeoffs:

- more control-plane hops,
- more path-hiding risk,
- longer CLUSTER_LIST values,
- more complex policy,
- harder troubleshooting.

Client relationships are directional. A lower-tier RR can be a client of an upper-tier RR; that does not mean they should be mutual clients.

## Cisco IOS XE configuration

Representative pattern:

```cli
router bgp 65000
 bgp router-id 10.255.0.11
 bgp cluster-id 10.255.0.100
 neighbor 10.255.0.21 remote-as 65000
 neighbor 10.255.0.21 update-source Loopback0
 address-family ipv4
  neighbor 10.255.0.21 activate
  neighbor 10.255.0.21 route-reflector-client
 exit-address-family
```

Important commands:

`bgp cluster-id 10.255.0.100`

- Sets an explicit cluster ID.

`neighbor ... route-reflector-client`

- Makes that neighbor an RR client for the applicable address family.

`update-source Loopback0`

- Uses a stable loopback as the BGP session source.
- Requires IGP/static reachability to the remote loopback.

Client side:

```cli
router bgp 65000
 bgp router-id 10.255.0.21
 neighbor 10.255.0.11 remote-as 65000
 neighbor 10.255.0.11 update-source Loopback0
 address-family ipv4
  neighbor 10.255.0.11 activate
 exit-address-family
```

The client does not configure itself as a client; that designation is configured on the RR.

## Cisco multiple cluster IDs

Cisco IOS XE supports multiple cluster IDs on applicable releases, including per-neighbor cluster IDs.

Cisco documents syntax such as:

```cli
router bgp 6500
 neighbor 2001:DB8:1::1 cluster-id 0.0.0.6
```

Cisco also documents client-to-client reflection controls on supporting software, for example:

```cli
router bgp 65000
 no bgp client-to-client reflection all
```

Disabling client-to-client reflection changes route-distribution requirements and can require clients to obtain routes through another topology. It should be an intentional design decision.

## Cisco IOS XR configuration

Representative IOS XR structure:

```cli
router bgp 65000
 bgp router-id 10.255.0.11
 bgp cluster-id 10.255.0.100
 neighbor 10.255.0.21
  remote-as 65000
  update-source Loopback0
  address-family ipv4 unicast
   route-reflector-client
  !
 !
!
```

Verify syntax against the exact IOS XR release/platform because hierarchy and supported options can vary.

## Junos OS configuration

Junos enables route reflection using a `cluster` statement in an internal BGP group:

```cli
set routing-options router-id 10.255.0.11
set routing-options autonomous-system 65000
set protocols bgp group RR-CLIENTS type internal
set protocols bgp group RR-CLIENTS local-address 10.255.0.11
set protocols bgp group RR-CLIENTS cluster 10.255.0.100
set protocols bgp group RR-CLIENTS neighbor 10.255.0.21
set protocols bgp group RR-CLIENTS neighbor 10.255.0.22
```

Juniper documents the cluster identifier as a 4-byte number.

Juniper also warns that adding/changing route-reflection cluster configuration in some VPN/BGP scenarios can reset BGP sessions sharing the AS. Treat cluster changes as potentially disruptive.

Some Juniper devices/features may require an Advanced BGP Feature license. Check the exact platform and release.

## Next-hop behavior

Route reflection does not inherently mean next-hop-self.

A reflected route may keep the original BGP next hop. The client therefore needs underlay/IGP reachability to that next hop.

Classic failure pattern:

```text
BGP update received:       yes
Prefix visible in BGP:     yes
Next hop resolvable:       no
Route active/installed:    no
Forwarding works:          no
```

Always troubleshoot next-hop resolution before assuming cluster logic is broken.

## Failure behavior

### Single RR failure

With one RR, clients lose their route-reflection source when the RR/session fails.

With dual RRs, a client can continue using the surviving session, assuming the second RR has equivalent route visibility.

Convergence depends on:

- failure detection,
- BGP timers/BFD where supported,
- route visibility on the surviving RR,
- best-path recalculation,
- RIB/FIB programming,
- next-hop reachability.

### Hierarchical RR failure

An upper-tier RR can become a major control-plane failure domain. Large designs typically make upper tiers redundant and validate route propagation after each single failure.

## Verification: Cisco IOS / IOS XE

Check sessions:

```cli
show ip bgp summary
```

Inspect a reflected route:

```cli
show ip bgp 203.0.113.0/24
```

Look for:

- Originator/ORIGINATOR_ID,
- Cluster list,
- next hop,
- local preference,
- AS path,
- best-path status.

Check configuration:

```cli
show running-config | section router bgp
```

Check next-hop resolution:

```cli
show ip route <BGP_NEXT_HOP>
show ip cef <BGP_NEXT_HOP>
```

## Verification: IOS XR

Common checks:

```cli
show bgp ipv4 unicast summary
show bgp ipv4 unicast 203.0.113.0/24 detail
show running-config router bgp
```

## Verification: Junos

Neighbor state:

```cli
show bgp summary
show bgp neighbor <NEIGHBOR_IP>
```

Route detail:

```cli
show route 203.0.113.0/24 detail
```

What the RR advertises:

```cli
show route advertising-protocol bgp <NEIGHBOR_IP> 203.0.113.0/24 detail
```

What it received:

```cli
show route receive-protocol bgp <NEIGHBOR_IP> 203.0.113.0/24 detail
```

Juniper documents `Cluster list` and `Originator ID` in detailed output for reflected routes.

## Troubleshooting by symptom

### Client receives no routes

Check:

1. BGP session established?
2. Correct ASN?
3. Address family active?
4. Neighbor actually configured as an RR client?
5. RR itself has the route?
6. Export policy allowing it?
7. Client-to-client reflection disabled?
8. Local cluster ID already in CLUSTER_LIST?
9. ORIGINATOR_ID equal to receiver's own BGP ID?

### One cluster cannot learn another cluster's routes

Check:

1. Are RRs peered?
2. Client/non-client direction correct?
3. Is the source route from a client or non-client?
4. Does CLUSTER_LIST already contain the receiving RR's cluster?
5. Are redundant RRs using a cluster-ID scheme that suppresses needed propagation?
6. Is an upper-tier RR missing?
7. Is inter-tier policy filtering the route?

### Route exists on RR but not client

Cisco:

```cli
show ip bgp <PREFIX>
show ip bgp neighbors <CLIENT_IP> advertised-routes
```

Junos:

```cli
show route <PREFIX> detail
show route advertising-protocol bgp <CLIENT_IP> <PREFIX> detail
```

### Route received but inactive

Check the next hop and competing routes.

### Route disappears after adding a second RR

Inspect CLUSTER_LIST first. If the same cluster ID appears where the second RR expects to accept the route, loop prevention may be doing exactly what it was designed to do.

Do not randomly change cluster IDs; diagram the intended reflection graph first.

### Suboptimal exit

Possible RR path hiding. Compare:

1. all candidate paths received by RR,
2. RR's selected best path,
3. path actually advertised to client,
4. what client would choose with full visibility.

Consider Add-Path/ORR/topologically diverse RRs where supported and justified.

## Common mistakes

- Treating cluster ID like an ASN.
- Assuming cluster IDs affect packet forwarding.
- Forgetting next-hop reachability.
- Assuming every redundant RR pair must use one shared cluster ID.
- Assuming two RRs automatically provide path diversity.
- Making hierarchical RRs mutual clients without understanding reflection direction.
- Disabling client-to-client reflection without providing another path.
- Ignoring path hiding.
- Changing cluster IDs without understanding session-reset/route-churn impact.

## Design recommendations

1. Use stable loopbacks for IBGP.
2. Use a resilient IGP/underlay.
3. Use at least two RRs for important client populations.
4. Document cluster IDs and RR client relationships.
5. Keep reflection topology simple enough to trace.
6. Validate every required prefix propagation direction.
7. Use hierarchy only when scale justifies it.
8. Account for path hiding.
9. Inspect ORIGINATOR_ID and CLUSTER_LIST during troubleshooting.
10. Test RR failures and inter-RR failures.
11. Verify software-specific shared-vs-unique cluster-ID behavior.
12. Treat RR design as a control-plane architecture, not a forwarding topology.

## Memory aids

```text
AS_PATH       -> inter-AS loop prevention
ORIGINATOR_ID -> prevents route returning to original IBGP speaker
CLUSTER_LIST  -> prevents route re-entering an RR cluster
```

```text
Cluster = route-reflection control-plane domain
Cluster != forwarding domain
```

```text
More hierarchy = fewer sessions
but potentially more path hiding and complexity
```

## Key takeaways

- BGP route-reflector clusters scale IBGP by relaxing normal IBGP split-horizon behavior.
- ORIGINATOR_ID identifies the original IBGP speaker.
- CLUSTER_LIST records RR clusters traversed and provides loop prevention.
- Cluster IDs are 32-bit control-plane values.
- Client and non-client advertisement rules are intentionally different.
- RRs do not need to be in the data path.
- Redundant RRs improve availability but do not automatically expose multiple paths.
- Hierarchical route reflection scales large designs at the cost of additional complexity.
- Cluster-ID strategy must match the actual vendor implementation and RR topology.
- When troubleshooting, inspect session state, route-reflector-client status, ORIGINATOR_ID, CLUSTER_LIST, policy, and next-hop resolution.

## Sources

- RFC 4456 — https://www.rfc-editor.org/rfc/rfc4456.html
- Cisco IOS XE BGP Multiple Cluster IDs — https://www.cisco.com/c/en-us/td/docs/routers/ios/config/17-x/ip-routing/b-ip-routing/m_irg-multicluster-id.html
- Cisco Route Reflection and Multiple Cluster IDs — https://www.cisco.com/c/en/us/support/docs/ip/border-gateway-protocol-bgp/200153-BGP-Route-Reflection-and-Multiple-Cluste.html
- Cisco IOS XR Route Reflectors — https://www.cisco.com/c/en/us/td/docs/iosxr/cisco8000/bgp/bgp-config-cisco8000/r-wrapper-bgp-routing-optimisation-and-convergence-techniques/c-bgp-route-reflectors.html
- Juniper BGP Route Reflectors — https://www.juniper.net/documentation/us/en/software/junos/bgp/topics/topic-map/bgp-rr.html
- Juniper `cluster` statement — https://www.juniper.net/documentation/us/en/software/junos/cli-reference/topics/ref/statement/cluster-edit-protocols-bgp.html

## Accuracy notes

**Source information:** RFC 4456 definitions and loop-prevention behavior; Cisco and Juniper configuration and documented platform behavior.

**Additional explanation:** Session-scaling examples, traffic/control-plane separation, design recommendations, and troubleshooting workflow.

**Reasonable inference:** Discussions of operational complexity and path-hiding exposure are engineering consequences of the documented route-reflection model, not claims of identical behavior on every software release.
