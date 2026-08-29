# BGP Confederations — Comprehensive iBGP Scaling Study Guide

> **Generated:** 2026-08-29 14:29 PDT  
> **Topic:** Border Gateway Protocol (BGP) Confederations, member-AS behavior, iBGP scaling, control-plane behavior, path attributes, configuration, verification, and troubleshooting.

## Supplied and supporting URLs

- Cisco IOS XE — Configuring Internal BGP Features: https://www.cisco.com/c/en/us/td/docs/routers/ios-xe/ip-routing/b-ip-routing/m_irg-int-features-0.html
- Cisco IOS XR / Cisco 8000 — BGP Confederations: https://www.cisco.com/c/en/us/td/docs/iosxr/cisco8000/bgp/bgp-config-cisco8000/r-wrapper-core-bgp-configurations/r-bgp-confederations.html
- Cisco IOS XR — BGP Confederation Peerings: https://www.cisco.com/c/en/us/td/docs/iosxr/cisco8000/bgp/bgp-config-cisco8000/r-wrapper-core-bgp-configurations/c-bgp-confederation-peerings.html
- Juniper — BGP Confederations for iBGP Scaling: https://www.juniper.net/documentation/us/en/software/junos/bgp/topics/topic-map/bgp-confederations-for-scaling.html
- Juniper — `confederation` statement reference: https://www.juniper.net/documentation/us/en/software/junos/cli-reference/topics/ref/statement/confederation-edit-routing-options.html
- IETF RFC 5065 — Autonomous System Confederations for BGP: https://www.rfc-editor.org/rfc/rfc5065.html

## Overview

A **BGP confederation** divides one administrative BGP Autonomous System (AS) into multiple internal **member ASes**, often called **sub-ASes**. Routers inside a member AS use normal iBGP rules. Routers in different member ASes form **confederation eBGP** sessions. To peers outside the confederation, the entire structure appears as one AS.

The main goals are:

- reduce the operational impact of the iBGP full-mesh requirement;
- create internal policy and topology boundaries;
- retain one external AS identity;
- use eBGP-like loop prevention between internal member ASes without exposing those member AS numbers externally.

RFC 5065 defines BGP confederations as a standards-track mechanism intended to reduce the full-mesh scaling problem and improve policy administration.

## Architecture

```text
                    External peer / ISP
                         AS 64500
                            |
                     normal eBGP
                            |
                 +---------------------+
                 | Confederation 65000 |
                 +---------------------+
                    /       |       \
                   /        |        \
          Sub-AS 65001  Sub-AS 65002  Sub-AS 65003
             R1/R2          R3/R4          R5/R6
                  \        /  \        /
                   confed eBGP boundaries

Within each member AS: iBGP or route reflection
Between member ASes:    confederation eBGP
Outside the confed:     ordinary eBGP; outside sees AS 65000
```

**What this diagram shows:** One external confederation AS, 65000, divided into three member ASes.

**What matters:** Peering inside each member AS is iBGP. Peering between different member ASes is confederation eBGP. The outside world sees AS 65000, not 65001/65002/65003 as independent external ASes.

**What to verify:** Every router is configured with the correct member-AS number and every member-AS border session is identified as belonging to the same confederation. A mismatch can prevent adjacency formation or cause ordinary eBGP behavior where confederation behavior was intended.

## Why ordinary iBGP does not scale

Traditional iBGP requires a full mesh because a route learned from one iBGP peer is not normally advertised to another iBGP peer.

For `N` BGP speakers, the number of sessions is:

```text
N × (N - 1) / 2
```

Examples:

| Routers | Full-mesh iBGP sessions |
|---:|---:|
| 10 | 45 |
| 50 | 1,225 |
| 100 | 4,950 |
| 500 | 124,750 |

A confederation reduces the size of each iBGP domain by splitting the larger AS into member ASes. However, the **full-mesh rule still exists inside each member AS** unless route reflectors are also used.

## Confederation terminology

- **Confederation AS / Confederation Identifier** — the AS number presented to external peers.
- **Member AS / Sub-AS** — an internal AS used only as part of the confederation.
- **Confederation eBGP** — BGP peering between different member ASes of the same confederation.
- **AS_CONFED_SEQUENCE** — ordered sequence of member-AS numbers traversed inside the confederation.
- **AS_CONFED_SET** — unordered set historically used for aggregation. RFC 9774 deprecates AS_SET and AS_CONFED_SET, so modern designs should avoid depending on the latter.

## Control-plane behavior

### Inside one member AS

Inside a member AS, normal iBGP behavior applies:

- iBGP-learned routes are not automatically re-advertised to other iBGP peers.
- An iBGP full mesh or route-reflector design is still required.
- LOCAL_PREF is meaningful and carried among internal peers.
- NEXT_HOP behavior follows normal iBGP rules unless explicitly changed.

### Between member ASes

A member-AS border router treats another member-AS border router as an external-type BGP peer, but the session is recognized as **inside the same confederation**.

This gives the design two useful properties:

1. eBGP-style AS-path loop prevention can be used between member ASes.
2. Confederation-aware attribute handling preserves the fact that all member ASes belong to one administrative routing domain.

Juniper explicitly documents that **NEXT_HOP, LOCAL_PREF, and MED**, attributes that normally have AS-local significance, can propagate throughout members of the same confederation.

## AS_PATH behavior and loop prevention

```text
Origin          Transit          Edge            External ISP
65001 --------> 65002 --------> 65003 --------> 64500
       confed           confed          normal
        eBGP             eBGP            eBGP

Inside the confederation:
  member-AS traversal is represented using confederation path segments.

At the external edge:
  confederation segments are removed and the outside peer sees AS 65000.
```

Conceptually, a path may appear inside the confederation as:

```text
(65001 65002 65003)
```

Vendor display syntax varies. Parentheses are commonly used to represent a confederation sequence.

Externally, the receiving AS should see the confederation identifier rather than the internal member-AS chain, for example:

```text
65000
```

rather than:

```text
65001 65002 65003
```

## Data-plane behavior

BGP confederations are fundamentally a **control-plane scaling mechanism**. They do not create a separate data-plane encapsulation.

Forwarding still depends on:

1. the selected BGP path;
2. the resolved BGP next hop;
3. the IGP/static/MPLS underlay reachability to that next hop;
4. the router's Routing Information Base (RIB);
5. the installed Forwarding Information Base (FIB).

This is a critical design point: a BGP session can be Established and a route can be valid in BGP while forwarding still fails because the next hop is unreachable.

## Packet and route flow example

Assume:

- Confederation AS: `65000`
- West member AS: `65001`
- Central member AS: `65002`
- East member AS: `65003`
- External ISP: `64500`
- Prefix originates in West: `10.10.10.0/24`

Route propagation:

```text
10.10.10.0/24
   |
   v
West member AS 65001
   |
   | confederation eBGP
   v
Central member AS 65002
   |
   | confederation eBGP
   v
East member AS 65003
   |
   | ordinary eBGP
   v
ISP AS 64500
```

Internally, member-AS traversal is tracked for loop prevention. Externally, the confederation is represented by AS 65000.

## Confederations versus route reflectors

| Characteristic | Full-mesh iBGP | Route Reflector | Confederation |
|---|---|---|---|
| Solves iBGP scale problem | No | Yes | Yes |
| Splits AS into member ASes | No | No | Yes |
| Uses cluster ID/originator ID | No | Yes | No |
| Uses confederation path segments | No | No | Yes |
| External peers see one AS | Yes | Yes | Yes |
| Internal policy boundaries | Limited | Moderate | Strong |
| Operational complexity | High at scale | Usually lowest | Higher |
| Common modern choice | No | Very common | More specialized |

A large provider can also combine the two:

```text
Confederation AS 65000
|
+-- Member AS 65001
|    +-- RR1
|    +-- RR2
|    +-- Clients
|
+-- Member AS 65002
|    +-- RR1
|    +-- RR2
|    +-- Clients
|
+-- Member AS 65003
     +-- RR1
     +-- RR2
     +-- Clients
```

This allows each member AS to scale internally with route reflectors while confederation eBGP connects the regions.

## Cisco IOS XE configuration

### Minimal building blocks

```cli
router bgp <MEMBER_AS>
 bgp confederation identifier <CONFEDERATION_AS>
 bgp confederation peers <PEER_MEMBER_AS> [<PEER_MEMBER_AS> ...]
```

Example for a router in member AS 65001:

```cli
router bgp 65001
 bgp confederation identifier 65000
 bgp confederation peers 65002
```

**Purpose of each command:**

- `router bgp 65001` — places this router in member AS 65001.
- `bgp confederation identifier 65000` — makes 65000 the AS presented outside the confederation.
- `bgp confederation peers 65002` — tells BGP that AS 65002 is another member of the same confederation.

A neighbor toward member AS 65002 would then use:

```cli
router bgp 65001
 neighbor 192.0.2.2 remote-as 65002
```

A neighbor inside the same member AS uses:

```cli
router bgp 65001
 neighbor 10.0.0.2 remote-as 65001
```

A normal external peer outside the confederation uses its real remote AS, for example:

```cli
router bgp 65001
 neighbor 203.0.113.1 remote-as 64500
```

The confederation identifier makes the organization appear externally as AS 65000.

### Complete illustrative Cisco topology

> The following is a **simulated lab configuration** assembled from documented command syntax. Interface addresses and route advertisements are placeholders for study use.

#### R1 — member AS 65001

```cli
router bgp 65001
 bgp log-neighbor-changes
 bgp confederation identifier 65000
 bgp confederation peers 65002
 neighbor 10.0.12.2 remote-as 65001
 neighbor 192.0.2.2 remote-as 65002
 address-family ipv4
  network 10.10.10.0 mask 255.255.255.0
  neighbor 10.0.12.2 activate
  neighbor 192.0.2.2 activate
 exit-address-family
```

#### R3 — member AS 65002

```cli
router bgp 65002
 bgp log-neighbor-changes
 bgp confederation identifier 65000
 bgp confederation peers 65001 65003
 neighbor 192.0.2.1 remote-as 65001
 neighbor 192.0.2.6 remote-as 65003
 address-family ipv4
  neighbor 192.0.2.1 activate
  neighbor 192.0.2.6 activate
 exit-address-family
```

#### R5 — member AS 65003 with external ISP

```cli
router bgp 65003
 bgp log-neighbor-changes
 bgp confederation identifier 65000
 bgp confederation peers 65002
 neighbor 192.0.2.5 remote-as 65002
 neighbor 203.0.113.1 remote-as 64500
 address-family ipv4
  neighbor 192.0.2.5 activate
  neighbor 203.0.113.1 activate
 exit-address-family
```

## Junos OS configuration concepts

Juniper documents that:

1. `autonomous-system` sets the local member-AS number;
2. the confederation statement identifies the main confederation AS;
3. all member ASes are listed as members;
4. BGP groups between member ASes are configured as external;
5. BGP groups within a member AS are internal.

Conceptual hierarchy:

```cli
routing-options {
    autonomous-system <MEMBER_AS>;
    confederation <CONFEDERATION_AS> members [ <MEMBER_AS_1> <MEMBER_AS_2> ... ];
}
```

Peer groups between member ASes are external BGP groups. Internal member-AS peers remain iBGP groups.

After configuration, Juniper instructs operators to verify with:

```cli
show routing-options
show protocols
commit
```

Operational verification includes:

```cli
show bgp neighbor
show bgp group
show bgp summary
```

## MED behavior in a confederation

Confederations can make MED handling especially important.

Cisco documents that:

```cli
bgp deterministic med
```

can be used to compare MED consistently among routes learned from peers in the same AS grouping.

Cisco also documents the interaction with:

```cli
bgp always-compare-med
```

When `bgp always-compare-med` is enabled, MED can be compared across paths that otherwise would not normally be comparable, including across member-AS boundaries. This is broader than deterministic MED.

The safe study distinction is:

- **deterministic MED** — makes ordering deterministic when comparing MEDs from the same neighboring AS;
- **always-compare-med** — broadens MED comparison across different neighboring ASes;
- confederation designs require careful testing because member-AS boundaries can affect which routes are considered comparable.

## NEXT_HOP behavior

Do not assume confederation eBGP behaves exactly like ordinary Internet eBGP.

Because the members are part of one confederation, vendors preserve internal-routing semantics for several attributes. Juniper explicitly calls out propagation of:

- `NEXT_HOP`
- `LOCAL_PREF`
- `MULTI_EXIT_DISC`

through member ASes.

Operational implication: always check actual next-hop reachability instead of assuming a confederation border changed it.

Verification:

```cli
show ip bgp <PREFIX>
show ip route <NEXT_HOP>
show ip cef <NEXT_HOP> detail
```

On Junos:

```cli
show route <PREFIX> detail
show route <NEXT_HOP>
show bgp neighbor
```

## LOCAL_PREF behavior

LOCAL_PREF is normally an intra-AS attribute. Within a confederation, it can retain its meaning across member-AS boundaries because the members are administratively part of the same logical AS.

That makes confederations attractive when a provider wants regional sub-AS boundaries but still wants consistent end-to-end policy based on LOCAL_PREF.

Example design:

```text
Preferred West exit     LOCAL_PREF 200
Normal Internet exit    LOCAL_PREF 100
Backup exit             LOCAL_PREF 50
```

A member-AS border can propagate the preferred path into other members without converting the policy into an external attribute such as MED.

## Failure behavior

A confederation does not inherently provide fast failure detection.

Failure detection still depends on:

- physical link signaling;
- BGP keepalive/hold timers;
- Bidirectional Forwarding Detection (BFD), if configured and supported;
- IGP convergence for next-hop reachability;
- recursive next-hop tracking;
- FIB programming.

Therefore:

```text
Link failure
   |
   v
Failure detection
   |
   v
BGP path invalidation / withdrawal
   |
   v
Best-path recalculation
   |
   v
RIB update
   |
   v
FIB update
   |
   v
Traffic converges
```

A confederation may change the propagation topology, but it does not eliminate the convergence chain.

## Verification workflow

### Cisco

```cli
show ip bgp summary
show ip bgp neighbors
show ip bgp <PREFIX>
show ip route <PREFIX>
show ip cef <PREFIX> detail
show running-config | section router bgp
```

Check the correct local member AS, confederation identifier, expected member ASes listed as confederation peers, Established sessions, external visibility of the confederation AS, and next-hop resolution.

### Junos

```cli
show bgp summary
show bgp neighbor
show bgp group
show route <PREFIX> detail
show routing-options
show protocols
```

Validate that peers are listed, `State` is `Established`, peer `Type` is correct, peer AS is correct, group `Local AS` and remote `AS` are correct, and `Down Peers` is zero.

## External verification

The strongest proof that the confederation is functioning correctly is to inspect a route from a router **outside** the confederation.

Expected:

```text
External peer sees: 65000
```

Unexpected:

```text
External peer sees: 65001 65002 65003
```

If internal member-AS values leak externally, review the confederation configuration and determine whether the session was actually configured as part of the confederation or as normal eBGP.

## Troubleshooting by symptom

### BGP adjacency does not establish between member ASes

Check:

```cli
show ip bgp summary
show ip bgp neighbors <NEIGHBOR_IP>
```

Possible causes:

- wrong remote AS;
- member AS omitted from `bgp confederation peers`;
- confederation identifier mismatch;
- ACL/firewall blocking TCP/179;
- update-source mismatch;
- missing route to loopback neighbor;
- TTL issue on multihop peering;
- authentication mismatch.

Juniper explicitly warns that peers will not establish if the two neighbors disagree about whether the adjacency belongs to a particular confederation.

### Route is in BGP but does not forward

Check:

```cli
show ip bgp <PREFIX>
show ip route <NEXT_HOP>
show ip cef <PREFIX> detail
```

Likely causes:

- unresolved BGP next hop;
- missing IGP route;
- recursive next-hop failure;
- route not installed due to administrative distance or RIB competition;
- policy suppressing the route;
- FIB programming issue.

### Wrong exit path chosen

Inspect:

```cli
show ip bgp <PREFIX>
```

Compare LOCAL_PREF, AS/confederation path, MED, origin, IGP metric to next hop, and route-map/policy results. Pay special attention to:

```cli
bgp deterministic med
bgp always-compare-med
```

### Internal member-AS values visible externally

Validate:

- `bgp confederation identifier` exists;
- member-AS peers are correctly declared;
- the external neighbor is actually outside the confederation;
- no route policy is unexpectedly rewriting AS_PATH.

### Routes do not propagate inside one member AS

Remember that the normal iBGP split-horizon rule still applies.

If three routers in member AS 65001 are only arranged as:

```text
R1 -- iBGP -- R2 -- iBGP -- R3
```

R2 does not simply re-advertise R1's iBGP-learned route to R3.

Solutions:

- full mesh the member AS; or
- use route reflectors inside the member AS.

## Common mistakes

1. Treating confederation eBGP as exactly identical to normal Internet eBGP.
2. Assuming confederations remove the need for iBGP full mesh inside each member AS.
3. Configuring member-AS border routers inconsistently.
4. Using the confederation AS as `remote-as` between member ASes instead of the actual member-AS number.
5. Forgetting underlay reachability.
6. Expecting external AS_PATH to contain member ASes.
7. Applying ordinary MED assumptions without checking MED comparison settings.
8. Assuming confederations automatically improve convergence speed.
9. Combining route reflectors and confederations without documenting loop-prevention boundaries.
10. Troubleshooting BGP without checking the RIB/FIB.

## When to use a confederation

A confederation is reasonable when:

- the AS is extremely large;
- the organization wants strong internal BGP policy boundaries;
- regions or operational domains should behave like separate ASes internally;
- a single external AS identity is required;
- the engineering team understands confederation-specific path behavior.

A route-reflector-only design is usually simpler when the main problem is just iBGP session scale.

## Confederation + route reflector design guidance

A scalable provider design often uses route reflectors within each member AS and confederation eBGP only at member-AS borders.

This separates two problems:

- **Route reflectors** solve peer-mesh scaling inside a member AS.
- **Confederations** create policy and loop-prevention boundaries between member ASes.

## Comparison with eBGP everywhere

A confederation differs from an enterprise that simply assigns a different normal AS to every region:

- member ASes are intentionally hidden externally;
- selected AS-local attributes can traverse member-AS boundaries;
- confederation path segments are understood as internal structure;
- the design is standardized to represent multiple internal ASes as one external AS.

This makes confederation a middle ground between one giant iBGP domain and many independent eBGP ASes.

## Exam memory aids

- **Confederation identifier = what the outside world sees.**
- **Member AS = what the router uses internally.**
- **Same member AS = iBGP.**
- **Different member AS, same confederation = confederation eBGP.**
- **Outside confederation = normal eBGP.**
- **Full mesh still exists inside each member AS unless route reflection is used.**
- **Confederation path information is used internally for loop prevention and removed before external advertisement.**
- **Confederation is a control-plane scaling/policy mechanism, not a new data-plane tunnel.**

## Configuration summary

### Cisco IOS XE core syntax

```cli
router bgp <MEMBER_AS>
 bgp confederation identifier <CONFEDERATION_AS>
 bgp confederation peers <MEMBER_AS_1> [<MEMBER_AS_2> ...]
 neighbor <PEER_IP> remote-as <REMOTE_MEMBER_AS>
```

### Cisco verification

```cli
show ip bgp summary
show ip bgp neighbors
show ip bgp <PREFIX>
show ip route <PREFIX>
show ip cef <PREFIX> detail
```

### Junos conceptual routing-options hierarchy

```cli
routing-options {
    autonomous-system <MEMBER_AS>;
    confederation <CONFEDERATION_AS> members [ <MEMBER_AS_1> <MEMBER_AS_2> ... ];
}
```

### Junos verification

```cli
show bgp neighbor
show bgp group
show bgp summary
show routing-options
show protocols
```

## Key takeaways

A BGP confederation is not merely "iBGP with several AS numbers." It is a deliberate hierarchical BGP architecture in which:

- a single logical AS is partitioned into member ASes;
- iBGP remains within each member;
- confederation eBGP joins the members;
- confederation path information prevents internal loops;
- internal member-AS structure is hidden from ordinary external peers;
- LOCAL_PREF, MED, NEXT_HOP, and policy behavior need to be understood in confederation context;
- route reflectors can be used inside each member AS;
- the data plane still depends on ordinary next-hop resolution, RIB, and FIB behavior.

## Sources

1. Cisco IOS XE — Configuring Internal BGP Features  
   https://www.cisco.com/c/en/us/td/docs/routers/ios-xe/ip-routing/b-ip-routing/m_irg-int-features-0.html

2. Cisco IOS XR / Cisco 8000 — BGP Confederations  
   https://www.cisco.com/c/en/us/td/docs/iosxr/cisco8000/bgp/bgp-config-cisco8000/r-wrapper-core-bgp-configurations/r-bgp-confederations.html

3. Cisco IOS XR — BGP Confederation Peerings  
   https://www.cisco.com/c/en/us/td/docs/iosxr/cisco8000/bgp/bgp-config-cisco8000/r-wrapper-core-bgp-configurations/c-bgp-confederation-peerings.html

4. Juniper Networks — BGP Confederations for iBGP Scaling  
   https://www.juniper.net/documentation/us/en/software/junos/bgp/topics/topic-map/bgp-confederations-for-scaling.html

5. Juniper Networks — `confederation` statement  
   https://www.juniper.net/documentation/us/en/software/junos/cli-reference/topics/ref/statement/confederation-edit-routing-options.html

6. IETF RFC 5065 — Autonomous System Confederations for BGP  
   https://www.rfc-editor.org/rfc/rfc5065.html

7. IETF RFC 9774 — Deprecation of AS_SET and AS_CONFED_SET in BGP  
   https://www.rfc-editor.org/rfc/rfc9774.html
