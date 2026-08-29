# Pseudowires, VCCV, and BFD over VCCV — Junos Study Guide

> Generated: 2026-08-29 14:41 PDT  
> Focus: why VCCV exists, how BFD over VCCV validates pseudowire data-path liveliness, Junos support across Layer 2 circuits/L2VPN/VPLS, control-word implications, interoperability, verification, and troubleshooting.

## Supplied concept

> Pseudowires use VCCV as a pseudowire-specific Operations, Administration, and Maintenance (OAM) channel. BFD over VCCV can continuously monitor pseudowire data-path liveliness. Junos documents BFD for VCCV across LDP-based Layer 2 circuits, BGP-based Layer 2 VPNs, and LDP- or BGP-based VPLS depending on feature context. Control-word negotiation and VCCV channel type can matter for interoperability; a pseudowire can be signaled yet still fail OAM/data-plane expectations.

## Source URLs

- Juniper — BFD Support for VCCV for Layer 2 VPNs, Layer 2 Circuits, and VPLS: https://www.juniper.net/documentation/us/en/software/junos/vpn-l2/topics/concept/bfd-for-vccv.html
- Juniper — Configuring BFD for VCCV for Layer 2 VPNs, Layer 2 Circuits, and VPLS: https://www.juniper.net/documentation/us/en/software/junos/vpn-l2/topics/task/layer-two-vpns-bfd-for-vccv.html
- Juniper — Configuring BFD for VCCV for Layer 2 Circuits: https://www.juniper.net/documentation/us/en/software/junos/vpn-l2/topics/task/configuring-bfd-for-vccv-for-l2ckt.html
- Juniper — Example: Configuring BFD for VCCV for Layer 2 Circuits: https://www.juniper.net/documentation/us/en/software/junos/vpn-l2/topics/concept/example/example-l2ckt-vccv-bfd-sessions.html
- Juniper — MPLS Pseudowires Configuration: https://www.juniper.net/documentation/us/en/software/junos/mpls/topics/topic-map/mpls-pseudowires-configuration.html
- RFC 5085 — Pseudowire VCCV: https://www.rfc-editor.org/rfc/rfc5085.html
- RFC 5885 — BFD for VCCV: https://www.rfc-editor.org/rfc/rfc5885.html
- Junos OS Layer 2 VPNs and VPLS User Guide: https://www.juniper.net/documentation/us/en/software/junos/vpn-l2/vpn-l2.pdf

## Overview

A **pseudowire (PW)** emulates a Layer 2 service across a packet-switched network. From the customer edge it can look like an Ethernet wire, VLAN circuit, Frame Relay circuit, ATM circuit, or another point-to-point Layer 2 service. Inside an MPLS provider network, the service is commonly represented by a **pseudowire/VC label** carried inside a transport label stack.

The important operational distinction is that the control plane can successfully create the pseudowire while the data plane still has a defect. Label bindings may exist, LDP sessions may be established, BGP routes may be present, and a service may look "up" from a signaling perspective even though packets sent through the actual pseudowire are mishandled, black-holed, encapsulated incompatibly, or fail an OAM expectation.

That is why **Virtual Circuit Connectivity Verification (VCCV)** exists. RFC 5085 defines VCCV as a control channel associated with the pseudowire. It gives OAM traffic a way to follow or be associated with the pseudowire itself rather than merely testing generic IP reachability between provider edge routers.

**Bidirectional Forwarding Detection (BFD) over VCCV**, standardized in RFC 5885, places BFD in that pseudowire-specific OAM context. Instead of relying only on periodic manual ping, BFD can send frequent lightweight control packets and declare the PW path failed when expected BFD packets stop arriving.

![Pseudowire and VCCV relationship](data:image/svg+xml;base64,PHN2ZyB4bWxucz0iaHR0cDovL3d3dy53My5vcmcvMjAwMC9zdmciIHdpZHRoPSIxMTAwIiBoZWlnaHQ9IjQyMCIgdmlld0JveD0iMCAwIDExMDAgNDIwIj4KPHJlY3Qgd2lkdGg9IjExMDAiIGhlaWdodD0iNDIwIiBmaWxsPSJ3aGl0ZSIvPgo8dGV4dCB4PSI1NTAiIHk9IjM4IiB0ZXh0LWFuY2hvcj0ibWlkZGxlIiBmb250LWZhbWlseT0iQXJpYWwiIGZvbnQtc2l6ZT0iMjYiIGZvbnQtd2VpZ2h0PSJib2xkIj5Qc2V1ZG93aXJlLCBWQ0NWLCBhbmQgQkZEIG92ZXIgVkNDVjwvdGV4dD4KPHJlY3QgeD0iNDAiIHk9IjE1MCIgd2lkdGg9IjE3MCIgaGVpZ2h0PSIxMDAiIHJ4PSIxMiIgZmlsbD0iI2VlZiIgc3Ryb2tlPSIjMzMzIi8+Cjx0ZXh0IHg9IjEyNSIgeT0iMTkwIiB0ZXh0LWFuY2hvcj0ibWlkZGxlIiBmb250LWZhbWlseT0iQXJpYWwiIGZvbnQtc2l6ZT0iMjAiPkNFMTwvdGV4dD48dGV4dCB4PSIxMjUiIHk9IjIyMCIgdGV4dC1hbmNob3I9Im1pZGRsZSIgZm9udC1mYW1pbHk9IkFyaWFsIiBmb250LXNpemU9IjE1Ij5DdXN0b21lciBFZGdlPC90ZXh0Pgo8cmVjdCB4PSIyNzAiIHk9IjEyNSIgd2lkdGg9IjE4MCIgaGVpZ2h0PSIxNTAiIHJ4PSIxMiIgZmlsbD0iI2VmZSIgc3Ryb2tlPSIjMzMzIi8+Cjx0ZXh0IHg9IjM2MCIgeT0iMTY1IiB0ZXh0LWFuY2hvcj0ibWlkZGxlIiBmb250LWZhbWlseT0iQXJpYWwiIGZvbnQtc2l6ZT0iMjAiPlBFMTwvdGV4dD48dGV4dCB4PSIzNjAiIHk9IjE5NSIgdGV4dC1hbmNob3I9Im1pZGRsZSIgZm9udC1mYW1pbHk9IkFyaWFsIiBmb250LXNpemU9IjE1Ij5QVyBpbmdyZXNzPC90ZXh0Pgo8cmVjdCB4PSI2NTAiIHk9IjEyNSIgd2lkdGg9IjE4MCIgaGVpZ2h0PSIxNTAiIHJ4PSIxMiIgZmlsbD0iI2VmZSIgc3Ryb2tlPSIjMzMzIi8+Cjx0ZXh0IHg9Ijc0MCIgeT0iMTY1IiB0ZXh0LWFuY2hvcj0ibWlkZGxlIiBmb250LWZhbWlseT0iQXJpYWwiIGZvbnQtc2l6ZT0iMjAiPlBFMjwvdGV4dD48dGV4dCB4PSI3NDAiIHk9IjE5NSIgdGV4dC1hbmNob3I9Im1pZGRsZSIgZm9udC1mYW1pbHk9IkFyaWFsIiBmb250LXNpemU9IjE1Ij5QVyBlZ3Jlc3M8L3RleHQ+CjxyZWN0IHg9Ijg5MCIgeT0iMTUwIiB3aWR0aD0iMTcwIiBoZWlnaHQ9IjEwMCIgcng9IjEyIiBmaWxsPSIjZWVmIiBzdHJva2U9IiMzMzMiLz4KPHRleHQgeD0iOTc1IiB5PSIxOTAiIHRleHQtYW5jaG9yPSJtaWRkbGUiIGZvbnQtZmFtaWx5PSJBcmlhbCIgZm9udC1zaXplPSIyMCI+Q0UyPC90ZXh0Pjx0ZXh0IHg9Ijk3NSIgeT0iMjIwIiB0ZXh0LWFuY2hvcj0ibWlkZGxlIiBmb250LWZhbWlseT0iQXJpYWwiIGZvbnQtc2l6ZT0iMTUiPkN1c3RvbWVyIEVkZ2U8L3RleHQ+CjxsaW5lIHgxPSIyMTAiIHkxPSIyMDAiIHgyPSIyNzAiIHkyPSIyMDAiIHN0cm9rZT0iIzMzMyIgc3Ryb2tlLXdpZHRoPSIzIi8+PGxpbmUgeDE9IjgzMCIgeTE9IjIwMCIgeDI9Ijg5MCIgeTI9IjIwMCIgc3Ryb2tlPSIjMzMzIiBzdHJva2Utd2lkdGg9IjMiLz4KPGxpbmUgeDE9IjQ1MCIgeTE9IjE4NSIgeDI9IjY1MCIgeTI9IjE4NSIgc3Ryb2tlPSIjMzMzIiBzdHJva2Utd2lkdGg9IjgiLz48dGV4dCB4PSI1NTAiIHk9IjE3MCIgdGV4dC1hbmNob3I9Im1pZGRsZSIgZm9udC1mYW1pbHk9IkFyaWFsIiBmb250LXNpemU9IjE2Ij5NUExTIHRyYW5zcG9ydCArIFBXIGxhYmVsPC90ZXh0Pgo8bGluZSB4MT0iNDUwIiB5MT0iMjM1IiB4Mj0iNjUwIiB5Mj0iMjM1IiBzdHJva2U9IiNhMDAiIHN0cm9rZS13aWR0aD0iNCIgc3Ryb2tlLWRhc2hhcnJheT0iMTAsOCIvPjx0ZXh0IHg9IjU1MCIgeT0iMjY1IiB0ZXh0LWFuY2hvcj0ibWlkZGxlIiBmb250LWZhbWlseT0iQXJpYWwiIGZvbnQtc2l6ZT0iMTYiIGZpbGw9IiNhMDAiPlZDQ1YgY29udHJvbCBjaGFubmVsIGNhcnJ5aW5nIEJGRCAvIHBpbmcgT0FNPC90ZXh0Pgo8dGV4dCB4PSI1NTAiIHk9IjMzMCIgdGV4dC1hbmNob3I9Im1pZGRsZSIgZm9udC1mYW1pbHk9IkFyaWFsIiBmb250LXNpemU9IjE3Ij5TaWduYWxpbmcgY2FuIGJlIGhlYWx0aHkgd2hpbGUgdGhlIFBXIGZvcndhcmRpbmcvT0FNIHBhdGggaXMgdW5oZWFsdGh5LjwvdGV4dD4KPHRleHQgeD0iNTUwIiB5PSIzNjAiIHRleHQtYW5jaG9yPSJtaWRkbGUiIGZvbnQtZmFtaWx5PSJBcmlhbCIgZm9udC1zaXplPSIxNSI+QkZEIG92ZXIgVkNDViB0ZXN0cyBwc2V1ZG93aXJlIGxpdmVsaW5lc3MgY29udGludW91c2x5LCBub3QgbWVyZWx5IHRoZSBQRS10by1QRSBJUCBwYXRoLjwvdGV4dD4KPC9zdmc+)

**What this image shows:** The customer-facing Layer 2 service crosses an MPLS core as a pseudowire between PE1 and PE2. A separate conceptual line shows the VCCV control channel bound to that PW.

**What matters:** BFD over VCCV is not simply BFD between PE loopback addresses. The VCCV context associates the BFD session with a specific pseudowire, which is what makes it useful for detecting a failure in the PW forwarding path.

**What to verify:** Confirm that the PW is established, that both endpoints advertise or configure compatible VCCV capabilities, and that the BFD session is actually bound to the intended PW rather than assuming IP/MPLS underlay health proves the Layer 2 service is healthy.

## Core concepts

### Pseudowire

A pseudowire connects two attachment circuits across a packet network while preserving the behavior needed to emulate a Layer 2 service. In an MPLS deployment, customer traffic usually enters a PE, is classified into a service, receives a pseudowire label plus an outer transport label, traverses the core, and is decapsulated at the remote PE.

```text
Customer frame
  -> ingress AC/service classification
  -> optional control-word handling
  -> PW/VC label push
  -> transport label push
  -> MPLS core forwarding
  -> transport label removal
  -> PW label lookup
  -> optional control-word processing
  -> remote attachment circuit
```

The **pseudowire label** identifies the Layer 2 service at the egress PE. The **transport label** gets the packet across the provider core.

### VCCV

**VCCV = Virtual Circuit Connectivity Verification.** RFC 5085 defines a control channel associated with a pseudowire and the OAM functions used over that channel. Two dimensions matter:

- **Control Channel (CC) type** — how the OAM packet is carried/identified in relation to the pseudowire.
- **Connectivity Verification (CV) type** — the verification mechanism carried, such as LSP Ping or BFD.

The exact valid combinations depend on pseudowire signaling, encapsulation, and implementation support.

### BFD over VCCV

RFC 5885 defines BFD CV types for VCCV. Operationally:

- BFD is primarily a **pseudowire fault-detection mechanism**.
- It continuously monitors the PW data path.
- A single BFD session is associated with a pseudowire.
- RFC 5885 specifies **asynchronous mode** for this use.
- Both endpoints participate symmetrically.
- Dynamically signaled PWs must have compatible advertised/received VCCV and BFD capabilities before a BFD CV type can be selected.

RFC 5885 supports BFD with IP/UDP headers and BFD carried using PW-ACH (Pseudowire Associated Channel Header) without IP/UDP headers. This matters because some modes depend on associated-channel/control-word processing.

## Control plane versus data plane

The pseudowire control plane creates the service relationship and distributes the information required to identify the PW. Depending on the service, Junos can use LDP, BGP signaling, or a combination of BGP autodiscovery and LDP signaling.

Control-plane success can prove that the remote PE is reachable by the signaling protocol, that a PW FEC was advertised, that a label binding was exchanged, or that a BGP L2VPN route was accepted. It does **not** prove that every packet sent through the actual pseudowire is processed correctly.

The data plane can still fail because of MPLS forwarding defects, wrong PW labels, attachment-circuit mismatches, MTU problems, control-word mismatch, unsupported/mismatched VCCV CC/CV types, or platform-specific OAM requirements.

This is the reason **"the pseudowire is signaled up" is not equivalent to "the pseudowire is healthy."**

## Junos support model

Juniper documents BFD for VCCV in these service contexts:

| Service | Signaling context | BFD for VCCV |
|---|---|---|
| Layer 2 circuit | LDP-based | Supported |
| Layer 2 VPN | BGP-based | Supported |
| VPLS | LDP-based or BGP-based | Supported |

Juniper also documents a **distributed BFD for VCCV model** on current supported hardware, with periodic packet processing moved to PIC concentrators such as DPC, FPC, and MPC. This improves scale/performance and can allow BFD for VCCV sessions to remain across graceful restarts.

### Distributed BFD loopback prerequisite

Juniper explicitly requires MPLS family on the loopback for distributed BFD for VCCV:

```cli
set interfaces lo0 unit 0 family mpls
```

### ACX control-word requirement

Juniper explicitly notes that on ACX Series routers, BFD sessions over VCCV require the **control word**, and it must also be configured on the peer so control-word negotiation can occur.

Relevant hierarchy differs by service:

```text
VPLS:
[edit routing-instances <RI> protocols vpls]

Layer 2 VPN:
[edit routing-instances <RI> protocols l2vpn]

Layer 2 circuit:
[edit protocols l2circuit neighbor <PEER> interface <INTERFACE>]
```

## Pseudowire control word

The **Pseudowire Control Word (CW)** is a four-byte field that can appear between the PW label and customer payload for applicable pseudowire types.

```text
Without CW:
[Transport Label][PW Label][Customer L2 Payload]

With CW:
[Transport Label][PW Label][Control Word][Customer L2 Payload]
```

A control-word mismatch can create a particularly confusing failure where signaling succeeds but packet interpretation differs between the PEs. Depending on feature/platform, customer forwarding, OAM, or both can fail.

A possible operational pattern is:

```text
LDP/BGP signaling:          UP
PW label bindings:          Present
Transport LSP:              UP
PW service status:          Established/Up
BFD over VCCV:              Down / never establishes
Customer forwarding:        May work, fail, or fail only for specific traffic/OAM
```

Do not stop troubleshooting just because the signaling state is Up.

## VCCV CC types and interoperability

RFC 5085 defines multiple VCCV Control Channel types so OAM can be carried in different pseudowire encapsulation environments. The practical consequences are:

1. Both ends require a compatible way to recognize the VCCV packet.
2. Some CC modes are tied closely to PWE3 control-word / PW-ACH handling.
3. Other modes rely on label TTL behavior.
4. Vendor/platform support can be a subset of the RFC possibilities.

Juniper's multisegment pseudowire documentation illustrates context-specific support. It states that Junos supports **VCCV Type 1 and Type 3** for the documented MS-PW OAM feature, while **Type 2 is not supported**. It also states Type 3 functions whether or not CW is enabled for the described case, whereas Type 1 end-to-end verification requires CW.

Therefore, never reduce VCCV interoperability to a single yes/no feature bit. Determine the **service, platform, release, CC type, CV type, and CW behavior** on each endpoint.

## BFD CV types

RFC 5885 defines four BFD CV bit values:

| Encapsulation | Fault detection only | Fault detection + status signaling |
|---|---:|---:|
| BFD with IP/UDP headers | `0x04` | `0x08` |
| BFD using PW-ACH, no IP/UDP headers | `0x10` | `0x20` |

The important rule is that both peers must select a **mutually supported** BFD CV type. For dynamically established PWs, RFC 5885 says only BFD CV types both advertised and received are eligible.

## Normal customer packet flow

1. PE1 receives a frame on the attachment circuit.
2. It classifies the interface/VLAN into the correct Layer 2 service.
3. It optionally inserts a control word.
4. It pushes the PW/VC label.
5. It pushes the outer MPLS transport label.
6. P routers forward using the transport label.
7. PE2 receives the packet and resolves the PW label.
8. PE2 handles/removes the CW if present and expected.
9. PE2 forwards the reconstructed frame on the remote attachment circuit.

## BFD-over-VCCV packet flow

1. The endpoint has an established PW and VCCV capability context.
2. A BFD session is associated with that PW.
3. BFD control packets are sent over the selected VCCV control channel.
4. The receiving PE identifies the packet as VCCV/OAM using the selected CC behavior.
5. The PW demultiplexer, such as the PW label, supplies context for the BFD session.
6. The BFD state machine processes the control packets.
7. If expected packets stop arriving within the negotiated detection interval, BFD declares the PW path down.

That is materially different from ordinary BFD between PE loopbacks. Generic PE-to-PE BFD can show the routed/MPLS underlay is alive while the specific pseudowire service is still broken.

## Junos configuration scopes

### LDP-based Layer 2 circuit

Junos places L2 circuit OAM under the service's neighbor/interface:

```text
[edit protocols l2circuit neighbor <PEER_IP> interface <INTERFACE_NAME> oam]
```

A source-supported skeleton is:

```cli
protocols {
    l2circuit {
        neighbor <PEER_IP> {
            interface <INTERFACE_NAME> {
                virtual-circuit-id <VC_ID>;
                oam {
                    bfd-liveness-detection;
                }
            }
        }
    }
}
```

The L2VPN `control-channel` hierarchy does not apply to Layer 2 circuits.

### BGP-based Layer 2 VPN

Juniper documents OAM under:

```text
[edit routing-instances <RI_NAME> protocols l2vpn]
```

with a structure that includes:

```cli
oam {
    bfd-liveness-detection;
    ping-interval <VALUE>;
    ping-multiplier <VALUE>;
}
```

### VPLS

Juniper documents VPLS OAM under the VPLS routing instance and, where applicable, the neighbor:

```text
[edit routing-instances <RI_NAME> protocols vpls]
[edit routing-instances <RI_NAME> protocols vpls neighbor <PEER_ADDRESS>]
```

## Verification workflow

### 1. Attachment circuit

Verify physical/logical interface state, VLAN/CCC encapsulation, service delimiter, and MTU.

### 2. Underlay

Verify PE loopback reachability and MPLS transport state using the protocols appropriate to the network (IGP, LDP, RSVP, SR-MPLS, etc.).

### 3. PW signaling and VCCV capabilities

Juniper recommends:

```cli
show ldp database extensive
```

Use it to inspect LDP state and VCCV control-channel information where applicable.

### 4. Layer 2 circuit state

```cli
show l2circuit connections
```

Confirm the expected neighbor/interface/VC is established without mismatch reasons.

### 5. BFD session

```cli
show bfd session extensive
```

Check BFD state, peer/session parameters, negotiated timers, and diagnostics. If the PW is established but BFD is down, focus on VCCV compatibility, CW behavior, platform prerequisites, timer support, and forwarding/OAM treatment.

### 6. Control-word expectations

Check both endpoints for:

- one side using CW and the other not;
- a selected VCCV mode that requires CW;
- ACX BFD-over-VCCV without CW on both peers;
- multi-vendor endpoints advertising different CC/CV combinations.

### 7. MTU and actual forwarding

MPLS labels and a control word add overhead. A service can be signaled perfectly yet fail for larger customer frames when an intermediate MTU is insufficient.

## Troubleshooting by symptom

### PW signaling Up, BFD Down

Likely categories:

- incompatible VCCV CC/CV type;
- control-word mismatch or missing required CW;
- unsupported service/platform/release combination;
- missing `family mpls` on `lo0.0` for distributed BFD;
- too-aggressive BFD timers;
- actual PW data-plane defect.

Checks:

```cli
show ldp database extensive
show bfd session extensive
show l2circuit connections
```

For BGP-signaled L2VPN/VPLS, inspect the relevant service routes and connection state too.

### BFD Up, customer traffic fails

BFD proves the BFD/VCCV path is alive, not every customer forwarding property. Check VLAN/tagging, Ethernet encapsulation, MTU, VPLS MAC learning, filters/policers, service delimiter, and attachment-circuit state.

### Customer traffic works, VCCV/BFD fails

This strongly suggests an OAM interoperability/configuration problem. Compare CC types, CV types, PW-ACH/CW handling, platform restrictions, hierarchy placement, and explicit-vs-default feature configuration.

### Same-vendor works, multi-vendor fails

Compare:

1. PW type/service encapsulation.
2. Signaling FEC/model.
3. CW enable/disable/default behavior.
4. Advertised VCCV CC types.
5. Advertised BFD CV types.
6. BFD timer ranges and mode.
7. MTU.
8. Platform/release implementation limits.

## Multisegment pseudowire notes

A **multisegment PW (MS-PW)** stitches multiple single-segment PWs through switching PEs (S-PEs). Juniper documents OAM capabilities including end-to-end MPLS ping, partial verification, traceroute, VCCV, and BFD.

Important Junos-specific notes:

- VCCV Type 1 and Type 3 are supported for the documented MS-PW OAM feature.
- VCCV Type 2 is not supported in that context.
- Type 3 can operate whether or not CW is enabled for the described MS-PW case.
- Type 1 end-to-end verification requires CW.
- PW-label TTL manipulation can make a VCCV packet emerge at an intermediate S-PE for partial connectivity verification.

This is why statements such as "VCCV always requires a control word" are too broad.

## Interoperability checklist

| Item | PE1 | PE2 | Requirement |
|---|---|---|---|
| PW type / encapsulation |  |  | Must be compatible |
| Signaling/FEC |  |  | Must be compatible |
| Control word | enabled/disabled/default | enabled/disabled/default | Frequently critical |
| VCCV CC types |  |  | At least one common type |
| BFD CV types |  |  | At least one common BFD type |
| BFD mode | asynchronous | asynchronous | Required by RFC 5885 usage |
| BFD timers |  |  | Negotiable and platform-supported |
| MTU |  |  | Sufficient end-to-end |
| Platform/release |  |  | Feature supported on both ends |

## Common mistakes

1. **Assuming LDP adjacency equals PW health.**
2. **Assuming a PW Up state proves OAM compatibility.**
3. **Ignoring the control word.**
4. **Configuring OAM at the wrong Junos hierarchy.**
5. **Forgetting `family mpls` on `lo0.0` for distributed BFD for VCCV.**
6. **Using overly aggressive BFD timers without checking scale/support.**
7. **Assuming vendors that both say "VCCV" necessarily support the same CC/CV combination.**
8. **Ignoring MTU overhead.**
9. **Troubleshooting BFD before confirming PW signaling.**
10. **Assuming VCCV type support is universal across all service contexts.**

## Exam-focused mental model

When a question says:

> "The pseudowire is established, but BFD over VCCV does not come up."

Think:

```text
PW signaling established?
  -> yes
Compatible VCCV CC type?
  -> check
Compatible BFD CV type?
  -> check
Control word required/negotiated?
  -> check
Platform/release prerequisites met?
  -> check
MPLS/PW data path really working?
  -> check
BFD timer/scale valid?
  -> check
```

The key distinction is **control-plane establishment versus PW-specific OAM/data-plane liveliness**.

## Configuration summary

```cli
set interfaces lo0 unit 0 family mpls
```

```text
Layer 2 circuit OAM:
[edit protocols l2circuit neighbor <PEER_IP> interface <INTERFACE_NAME> oam]

Layer 2 VPN OAM:
[edit routing-instances <RI_NAME> protocols l2vpn oam]

VPLS OAM:
[edit routing-instances <RI_NAME> protocols vpls oam]
```

Key checks:

```cli
show l2circuit connections
show ldp database extensive
show bfd session extensive
```

## Key takeaways

- **VCCV is the pseudowire-specific OAM framework/control channel.**
- **BFD over VCCV continuously tests PW liveliness** and is designed to detect PW data-plane failure.
- **A signaled PW is not necessarily a healthy PW.** Signaling state and OAM/data-plane state are different.
- **Control-word negotiation can be decisive**, especially in platform-specific cases such as Juniper's ACX guidance.
- **Junos documents BFD for VCCV across LDP L2 circuits, BGP L2VPN, and LDP/BGP VPLS**, subject to platform/release support.
- **Current distributed Junos BFD for VCCV requires MPLS family on `lo0.0`.**
- **Interoperability requires matching actual VCCV CC/CV capabilities**, not merely enabling a similarly named feature on both vendors.

## Sources

1. Juniper Networks — BFD Support for VCCV for Layer 2 VPNs, Layer 2 Circuits, and VPLS  
   https://www.juniper.net/documentation/us/en/software/junos/vpn-l2/topics/concept/bfd-for-vccv.html
2. Juniper Networks — Configuring BFD for VCCV for Layer 2 VPNs, Layer 2 Circuits, and VPLS  
   https://www.juniper.net/documentation/us/en/software/junos/vpn-l2/topics/task/layer-two-vpns-bfd-for-vccv.html
3. Juniper Networks — Configuring BFD for VCCV for Layer 2 Circuits  
   https://www.juniper.net/documentation/us/en/software/junos/vpn-l2/topics/task/configuring-bfd-for-vccv-for-l2ckt.html
4. Juniper Networks — Example: Configuring BFD for VCCV for Layer 2 Circuits  
   https://www.juniper.net/documentation/us/en/software/junos/vpn-l2/topics/concept/example/example-l2ckt-vccv-bfd-sessions.html
5. Juniper Networks — MPLS Pseudowires Configuration  
   https://www.juniper.net/documentation/us/en/software/junos/mpls/topics/topic-map/mpls-pseudowires-configuration.html
6. Juniper Networks — Junos OS Layer 2 VPNs and VPLS User Guide  
   https://www.juniper.net/documentation/us/en/software/junos/vpn-l2/vpn-l2.pdf
7. IETF RFC 5085 — Pseudowire VCCV  
   https://www.rfc-editor.org/rfc/rfc5085.html
8. IETF RFC 5885 — BFD for VCCV  
   https://www.rfc-editor.org/rfc/rfc5885.html

### Accuracy notes

- **Source information:** Junos service support, distributed BFD behavior, `family mpls` prerequisite, ACX control-word requirement, configuration hierarchy, and verification commands are from the cited Juniper documentation.
- **Standards information:** VCCV architecture and BFD CV behavior are based on RFC 5085 and RFC 5885.
- **Additional explanation:** Packet-flow descriptions, troubleshooting ordering, interoperability matrix, and the embedded SVG diagram are instructional synthesis from the cited standards/vendor behavior.
- **Platform caution:** Confirm the exact router, line card, and Junos release in Juniper Feature Explorer before production deployment or aggressive BFD timer selection.
