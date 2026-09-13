# NAT64 and NPTv6 — Concepts, Packet Flow, and Cisco / Palo Alto / Fortinet Implementation

## Purpose

This guide separates two IPv6 transition mechanisms that are often confused:

- **NAT64** translates between **IPv6 and IPv4**. Stateful NAT64 commonly lets IPv6-only clients reach IPv4-only services and usually works with **DNS64**.
- **NPTv6 (Network Prefix Translation for IPv6)** translates **IPv6 prefix to IPv6 prefix**. It is a **stateless, algorithmic, 1:1** translation defined by RFC 6296 and does **not** translate ports.

The most useful mental shortcut is:

> **NAT64 = change address family. NPTv6 = keep IPv6, change prefix.**

## URLs reviewed

- RFC 6052 — IPv4-Embedded IPv6 Address Format: https://www.rfc-editor.org/rfc/rfc6052.html
- RFC 6146 — Stateful NAT64: https://www.rfc-editor.org/rfc/rfc6146.html
- RFC 6296 — NPTv6: https://www.rfc-editor.org/rfc/rfc6296.html
- Cisco IOS XE 17.x Stateful NAT64: https://www.cisco.com/c/en/us/td/docs/routers/ios/config/17-x/ip-addressing/b-ip-addressing/m_iadnat-stateful-nat64.html
- Cisco IOS XE 17.x NPTv6: https://www.cisco.com/c/en/us/td/docs/routers/ios/config/17-x/ip-addressing/b-ip-addressing/m_iadnat-asr1k-nptv6.html
- Palo Alto NAT64: https://docs.paloaltonetworks.com/ngfw/networking/nat64
- Palo Alto IPv6-initiated NAT64: https://docs.paloaltonetworks.com/ngfw/networking/nat64/configure-nat64-for-ipv6-initiated-communication
- Palo Alto NPTv6: https://docs.paloaltonetworks.com/ngfw/networking/nptv6/how-nptv6-works
- Palo Alto Create NPTv6 Policy: https://docs.paloaltonetworks.com/ngfw/networking/nptv6/create-an-nptv6-policy
- Fortinet NAT64 and DNS64: https://docs.fortinet.com/document/fortigate/latest/administration-guide/443324/nat64-policy-and-dns64-dns-proxy
- Fortinet NPTv6 (FortiOS 7.6): https://docs.fortinet.com/document/fortigate/7.6.0/new-features/625228/nptv6-protocol-for-ipv6-address-translation

## Table of contents

1. [NAT64 vs NPTv6](#1-nat64-vs-nptv6)
2. [NAT64 architecture](#2-nat64-architecture)
3. [DNS64 and IPv4-embedded IPv6 addresses](#3-dns64-and-ipv4-embedded-ipv6-addresses)
4. [NAT64 packet flow](#4-nat64-packet-flow)
5. [NPTv6 architecture](#5-nptv6-architecture)
6. [NPTv6 packet flow and checksum neutrality](#6-nptv6-packet-flow-and-checksum-neutrality)
7. [Cisco implementation](#7-cisco-implementation)
8. [Palo Alto implementation](#8-palo-alto-implementation)
9. [Fortinet implementation](#9-fortinet-implementation)
10. [Vendor comparison](#10-vendor-comparison)
11. [Routing, policy, HA, and design implications](#11-routing-policy-ha-and-design-implications)
12. [Verification and troubleshooting](#12-verification-and-troubleshooting)
13. [Common mistakes](#13-common-mistakes)
14. [Sources](#14-sources)

---

## 1. NAT64 vs NPTv6

| Property | NAT64 | NPTv6 |
|---|---|---|
| Address families | IPv6 ↔ IPv4 | IPv6 ↔ IPv6 |
| Primary use | IPv6-only ↔ IPv4-only interoperability | Provider-prefix independence / multihoming / renumbering |
| Typical state | Stateful for common enterprise implementations | Stateless by design |
| Port translation | Often yes with PAT/DIPP | No |
| DNS dependency | DNS64 commonly required for name-based IPv6→IPv4 access | None inherent |
| Address mapping | Can be many IPv6 clients to one/few IPv4 addresses | Algorithmic 1:1 |
| Transport checksum handling | Translator converts IPv4/IPv6 headers and applicable ICMP | Checksum-neutral algorithm avoids transport-header rewrite |
| Security function? | No; NAT and security policy are separate concerns | No; NPTv6 itself is not a firewall |
| Key RFCs | 6052, 6146, 6147 | 6296 |

### Source information

RFC 6146 defines stateful NAT64 as IPv6-to-IPv4 protocol/address translation with per-flow/binding state. RFC 6296 defines NPTv6 as stateless, transport-agnostic, two-way and algorithmic.

### Additional explanation

NAT64 solves **protocol coexistence**. NPTv6 solves **IPv6 prefix independence**. If both sides already speak IPv6, NAT64 is the wrong mental model.

---

## 2. NAT64 architecture

![NAT64 packet flow](images/13-09-26-09-54_nat64_packet_flow.svg)

[Editable draw.io source](images/13-09-26-09-54_nat64_packet_flow.drawio)

**What this image shows:** an IPv6-only client resolves an IPv4-only server through DNS64, sends to an IPv4-embedded IPv6 destination, and the NAT64 device creates an IPv4 flow.

**What matters:** the destination `64:ff9b::c000:250` is not a real IPv6 interface on the server. It encodes IPv4 address `192.0.2.80`. The NAT64 device owns the translation boundary.

**What to verify:** route the NAT64 prefix toward the translator; ensure DNS64 uses the same prefix; verify the IPv4 source pool/PAT address is routable on the IPv4 side.

RFC 6052 reserves `64:ff9b::/96` as the **Well-Known Prefix (WKP)**. Network-Specific Prefixes (NSPs) can also be used where implementations support them.

---

## 3. DNS64 and IPv4-embedded IPv6 addresses

An IPv6-only application asks DNS for an AAAA record. If the destination only has an A record, DNS64 can synthesize an AAAA record by embedding the 32-bit IPv4 address into an IPv6 prefix.

Example:

```text
A record:
server.example → 192.0.2.80

Using 64:ff9b::/96:

192.0.2.80
= C0 00 02 50
= c000:0250

Synthetic AAAA:
server.example → 64:ff9b::c000:250
```

The client therefore remains IPv6-only. It sends an IPv6 packet to the synthetic address, and routing must deliver that prefix to the NAT64 translator.

### Important distinction

**DNS64 does not translate packets.** It synthesizes DNS answers. **NAT64 translates packets.**

Hard-coded IPv4 literals and applications that carry IP addresses inside payloads may need special handling or an Application-Level Gateway (ALG). Vendor support varies.

---

## 4. NAT64 packet flow

Assume:

```text
IPv6 client:       2001:db8:10::10
IPv4 server:       192.0.2.80:443
NAT64 prefix:      64:ff9b::/96
NAT64 IPv4 pool:   198.51.100.10
```

### Forward flow

1. Client asks DNS64 for `server.example`.
2. DNS64 receives/obtains A=`192.0.2.80` and returns synthesized AAAA=`64:ff9b::c000:250`.
3. Client sends:
   ```text
   IPv6 src 2001:db8:10::10:51500
   IPv6 dst 64:ff9b::c000:250:443
   ```
4. IPv6 routing delivers `64:ff9b::/96` to the NAT64 device.
5. Stateful NAT64 identifies the embedded IPv4 destination `192.0.2.80`.
6. The translator allocates an IPv4 source address/port, for example:
   ```text
   2001:db8:10::10:51500  ↔  198.51.100.10:40001
   ```
7. It emits:
   ```text
   IPv4 src 198.51.100.10:40001
   IPv4 dst 192.0.2.80:443
   ```

### Return flow

1. Server returns to `198.51.100.10:40001`.
2. NAT64 finds the existing binding/session.
3. Source `192.0.2.80` is represented to the IPv6 client as `64:ff9b::c000:250`.
4. Destination becomes `2001:db8:10::10:51500`.
5. The return packet is emitted as IPv6.

### Stateful implication

Dynamic PAT normally means unsolicited IPv4 initiation cannot work without a static binding or previously created state. This is fundamentally different from NPTv6.

---

## 5. NPTv6 architecture

![NPTv6 packet flow](images/13-09-26-09-54_nptv6_packet_flow.svg)

[Editable draw.io source](images/13-09-26-09-54_nptv6_packet_flow.drawio)

**What this image shows:** an internal IPv6 prefix is algorithmically represented by a different external IPv6 prefix.

**What matters:** NPTv6 does not create a many-to-one port mapping. Every translated address has a deterministic counterpart.

**What to verify:** both prefixes and routing must be valid; upstream routers must route the external prefix toward the NPTv6 translator; security policy is still required separately on firewalls.

---

## 6. NPTv6 packet flow and checksum neutrality

RFC 6296 deliberately avoids classic NAPT44 behavior. The translator changes IPv6 address bits while preserving a checksum-neutral relationship.

### Why checksum neutrality matters

TCP and UDP checksums include an IPv6 pseudo-header containing source and destination addresses. Blindly changing an IPv6 prefix would change that pseudo-header and invalidate the transport checksum.

NPTv6 calculates an adjustment so the resulting IPv6 address produces the same Internet checksum contribution. Therefore the translator generally does not need to edit TCP/UDP headers.

### Consequence

Do **not** assume that NPTv6 always means “replace only the visible prefix and leave every remaining bit literally untouched.” The checksum-neutral algorithm may make a compensating 16-bit adjustment. Fortinet's 7.6 documentation illustrates this explicitly.

### Why NPTv6 can load-share

Because the mapping is stateless and algorithmic, two translators configured with the same inside/outside prefixes can produce the same mapping independently. There is no NAT binding table that must be synchronized merely to know the translated address.

A stateful firewall using NPTv6 can still maintain **firewall session state**. “NPTv6 is stateless” refers to the translation algorithm itself.

---

## 7. Cisco implementation

### 7.1 Cisco Stateful NAT64

Cisco IOS XE 17.x documents Stateful NAT64 with `nat64 enable`, a stateful prefix, IPv4 pools, static/dynamic mappings, and PAT.

A documented basic PAT pattern is:

```cli
ipv6 unicast-routing
!
interface GigabitEthernet0/0/0
 description IPv6-facing
 ipv6 enable
 ipv6 address 2001:DB8:10::1/64
 nat64 enable
!
interface GigabitEthernet0/0/1
 description IPv4-facing
 ip address 198.51.100.1 255.255.255.0
 nat64 enable
!
ipv6 access-list NAT64-V6
 permit ipv6 2001:DB8:10::/64 any
!
nat64 prefix stateful 64:FF9B::/96
nat64 v4 pool V4POOL 198.51.100.10 198.51.100.10
nat64 v6v4 list NAT64-V6 pool V4POOL overload
```

The exact addressing above is a documentation-style lab example; adapt interface names and routable pool addresses to the platform.

Cisco documents that a NAT Virtual Interface (NVI) is created for stateful NAT64 processing and that relevant traffic must route to it.

#### Cisco NAT64 verification

```cli
show nat64 translations
show nat64 pools
show nat64 prefix stateful global
show nat64 statistics
show nat64 timeouts
show ipv6 route 64:FF9B::/96
show ip route 198.51.100.10
```

**Success criteria:** a translation appears after traffic starts; prefix and pool are present; packet counters increment; routes resolve toward the correct NAT64 processing path.

**Failure indicators:** no binding, no match on the IPv6 ACL, stateful prefix not enabled/routed, pool exhaustion, or missing return route.

#### Cisco documented caveats

Cisco's IOS XE 17.x NAT64 guide calls out restrictions including multicast not being supported, unsupported IPv4 options / several IPv6 extension-header cases, and the need for DNS64 for DNS-based use. It also notes that NAT44 and stateful NAT64 are not supported on the same interface in the described implementation.

### 7.2 Cisco NPTv6

Cisco exposes NPTv6 using **NAT66** CLI terminology:

```cli
interface GigabitEthernet0/0/0
 nat66 inside
!
interface GigabitEthernet0/0/1
 nat66 outside
!
nat66 prefix inside 2001:DB8:10::/48 outside 2001:DB8:200::/48
```

For VRF-aware designs the documented syntax can append `vrf <vrf-name>`.

#### Cisco NPTv6 verification

```cli
show nat66 prefix
show nat66 statistics
show platform hardware qfp active feature nat66 datapath prefix
show platform hardware qfp active feature nat66 datapath statistics
```

Cisco's own example output identifies configured inside/outside prefixes and packet counters in each direction.

#### Cisco NPTv6 restrictions

The IOS XE 17.x NPTv6 chapter lists multicast, firewall integration in that feature context, HSL, and syslog as unsupported. Platform/software support must be checked in Cisco Feature Navigator because the chapter warns that availability varies by platform and release.

---

## 8. Palo Alto implementation

### 8.1 Palo Alto NAT64

Palo Alto Networks documents **stateful NAT64** for IPv6-initiated communication and static binding / optional port translation for IPv4-initiated communication. PAN-OS does **not** support stateless NAT64 according to the current NAT64 overview.

For IPv6-initiated communication:

1. Enable IPv6 firewalling and IPv6 on the required Layer 3 interfaces.
2. Configure a third-party DNS64 service or another DNS64 solution.
3. Create Security policy allowing the intended traffic.
4. Go to **Policies → NAT** and create a NAT64 rule.
5. Match the IPv6 source zone/network and the NAT64 destination prefix.
6. Configure source translation to an IPv4 address or Dynamic IP and Port (DIPP) as documented for the design.
7. Configure destination translation based on the IPv4-embedded IPv6 destination.
8. Commit and test with traffic.

Palo Alto supports WKP or supported Network-Specific Prefix lengths and can use multiple NAT64 prefixes, with each NAT64 rule using one prefix.

### Palo Alto NAT64 dataplane behavior to remember

- Security policy remains separate from the NAT rule.
- Route lookup and policy/NAT matching must lead traffic to the correct zones/interfaces.
- DIPP creates state; return traffic must match the session.
- DNS64 must synthesize using the same prefix expected by the NAT64 rule.
- Palo Alto documents TCP/UDP/ICMP translation according to RFC 6146 and best-effort behavior for some other protocols.

### 8.2 Palo Alto NPTv6

GUI prerequisites:

1. **Device → Setup → Session**: enable **IPv6 Firewalling**.
2. **Network → Interfaces → Ethernet → IPv6**: enable IPv6 and configure the Layer 3 address.
3. Create Security policy rules; Palo Alto explicitly states NPTv6 itself does not provide security.
4. Go to **Policies → NAT → Add**.
5. On **General**, set **NAT Type = NPTv6**.
6. On **Original Packet**, set source/destination zones and the original IPv6 prefix.
7. On **Translated Packet**, use **Static IP** for normal source prefix translation, or supported dynamic-prefix behavior where applicable.
8. Optionally enable **Bi-directional** translation.
9. Configure NDP Proxy where the translated prefix must be represented on-link.
10. Commit.

Current documentation permits NPTv6 prefix lengths from **/32 through /112** for the policy fields it describes.

Beginning with **PAN-OS 11.1.5**, Palo Alto documents source NPTv6 using dynamically assigned IPv6 prefixes from DHCPv6, PPPoEv6, or cellular/5G interfaces.

### Palo Alto NPTv6 verification

Useful checks include:

```cli
show session all filter source <ipv6-address>
show session all filter destination <ipv6-address>
show routing route
show neighbor interface all
```

Palo Alto also documents the `test nptv6` CLI for calculating/validating a checksum-neutral mapped address in applicable destination-NAT scenarios.

**Success criteria:** traffic logs show the expected Security rule, session details show translated addressing, the external prefix is routed back to the firewall, and NDP is correct if the external mapping is on-link.

---

## 9. Fortinet implementation

### 9.1 FortiGate NAT64 + DNS64

FortiGate can provide both NAT64 policy handling and DNS64/DNS proxy functions.

Fortinet's current administration example uses:

```cli
config system dns-server
    edit "port10"
        set mode forward-only
    next
end

config firewall vip6
    edit "vip6"
        set extip 64:ff9b::-64:ff9b::ffff:ffff
        set embedded-ipv4-address enable
    next
end

config firewall address6
    edit "internal-net6"
        set ip6 2001:db8:1::/48
    next
end
```

The design then uses an IPv4 IP pool enabled for NAT64 and a firewall policy with NAT64 enabled so the FortiGate translates the embedded IPv4 destination and allocates the IPv4 source address.

A key Fortinet-specific caveat is **central NAT**: Fortinet documents two-stage policy evaluation around the NAT64 driver and warns administrators to configure source/destination address matching carefully to avoid unintended policy hits.

### FortiGate NAT64 verification

```cli
get router info6 routing-table all
get router info routing-table all
diagnose sys session filter clear
diagnose sys session list
diagnose debug flow filter clear
diagnose debug flow show function-name enable
diagnose debug enable
diagnose debug flow trace start 20
```

Use `diagnose debug disable` and stop/reset debug after collection.

**Verify:** IPv6 policy match, NAT64 VIP match, source pool allocation, IPv4 egress route, and matching return session.

### 9.2 FortiGate NPTv6

Fortinet added documented **partial RFC 6296 NPTv6 support in FortiOS 7.6.0**.

The new IPv6 IP-pool type is:

```cli
config firewall ippool6
    edit "NPTV6-POOL"
        set type nptv6
        set internal-prefix 2001:db8:10::/64
        set external-prefix 2001:db8:200::/64
    next
end
```

That pool is then referenced by an IPv6 firewall policy according to Fortinet's NPTv6 policy example.

Fortinet emphasizes that the translation changes the network/prefix representation while maintaining a deterministic 1:1 mapping and checksum neutrality. Its documentation also shows that checksum compensation can modify a 16-bit word, which is an excellent reminder that NPTv6 is not necessarily a naive text substitution.

### FortiGate NPTv6 verification

Inspect the policy, sessions, and packet flow:

```cli
show firewall ippool6
show firewall policy
diagnose sys session list
diagnose debug flow filter addr6 <ipv6-address>
diagnose debug flow show function-name enable
diagnose debug enable
diagnose debug flow trace start 20
```

**Success criteria:** the correct policy uses the NPTv6 pool, outbound packets carry the expected external representation, inbound traffic is algorithmically mapped back, and upstream routing sends the external prefix toward the FortiGate.

---

## 10. Vendor comparison

| Capability | Cisco IOS XE | Palo Alto PAN-OS | FortiGate FortiOS |
|---|---|---|---|
| Stateful NAT64 | Yes | Yes | Yes |
| Stateless NAT64 | Cisco documents it separately on supported IOS XE platforms | PAN-OS overview says no | Product/version dependent; current FortiGate docs focus heavily on policy/CGNAT variants |
| DNS64 | Separate DNS64 installation in Cisco stateful NAT64 prerequisite | Third-party/other DNS64 solution for IPv6-initiated NAT64 | FortiGate DNS proxy can provide DNS64 in documented design |
| NAT64 PAT | `nat64 ... overload` | DIPP | IPv4 IP pool / policy NAT64 |
| NPTv6 | Yes; CLI uses `nat66` terminology | Yes, dedicated NPTv6 NAT type | FortiOS 7.6.0 adds partial RFC 6296 support |
| NPTv6 state | Stateless translation | Stateless algorithm; firewall sessions still stateful | Stateless translation; firewall sessions still stateful |
| NPTv6 ports | Not translated | Not translated | Not translated |
| Dynamic WAN prefix NPTv6 | Platform/release-specific | PAN-OS 11.1.5+ documented | Check exact FortiOS release behavior |
| Security policy separate | Router feature / ZBF context is separate | Yes | Yes, via firewall policy |

---

## 11. Routing, policy, HA, and design implications

### NAT64 routing

The IPv6 realm must route the NAT64 prefix toward the translator. The IPv4 side must route the selected IPv4 pool/interface addresses correctly. Failure in either direction creates classic one-way behavior.

### NPTv6 routing

The external prefix must be reachable through the NPTv6 device. NPTv6 does not magically advertise that prefix to an ISP. BGP/static routing and provider authorization still matter.

### HA

- **NAT64:** stateful translations/sessions may need HA synchronization if failover is expected to preserve sessions.
- **NPTv6:** the translation algorithm requires no per-flow mapping state, so multiple translators can compute the same address mapping. A firewall may still need to synchronize security session state for hitless failover.

### NAT is not security

Neither NAT64 nor NPTv6 should be treated as a substitute for Security policy, ACLs, or zone firewall policy.

### MTU / PMTUD

Address-family translation can affect packet sizing and ICMP behavior. Ensure ICMPv6 Packet Too Big and relevant translated ICMP behavior are not accidentally blocked. Symptoms that look like application failures can actually be Path MTU Discovery (PMTUD) failures.

---

## 12. Verification and troubleshooting

### Symptom: DNS name resolves but connection fails through NAT64

**Where:** DNS64, IPv6 route table, translator, IPv4 route table.

**Tool:** `dig AAAA`, route lookup, NAT64 translation/session table.

**What it tests:** whether the synthesized AAAA uses the correct prefix and reaches the translator.

**Expected:** AAAA embeds the intended A record; NAT64 state appears; translated IPv4 SYN leaves toward the server.

**Failure means:** prefix mismatch, missing route, NAT rule mismatch, pool issue, Security policy deny, or no IPv4 return route.

**Next action:** compare the DNS64 synthesis prefix byte-for-byte with the NAT64 rule/prefix.

### Symptom: IPv4 server sees packets but IPv6 client never receives return traffic

Check:

1. server default gateway / route to NAT64 IPv4 pool,
2. NAT64 session/binding,
3. asymmetric routing,
4. firewall state,
5. ICMP/PMTUD,
6. HA member receiving the return flow.

### Symptom: NPTv6 outbound works but inbound cannot reach the internal host

Check:

1. upstream route for the **external translated prefix**,
2. firewall Security policy,
3. NDP Proxy if the prefix is expected on-link,
4. correct inside/outside direction,
5. deterministic mapping with vendor test/verification command.

### Symptom: translated IPv6 address is not the literal prefix + original host bits expected

This can be normal under RFC 6296 checksum neutrality. Validate with the vendor's NPTv6 calculation/diagnostic method instead of manually concatenating strings.

### Symptom: only some applications fail through NAT64

Look for:

- application payloads containing literal IP addresses,
- protocols needing an ALG,
- unsupported extension headers/options,
- IPsec/protocol limitations,
- hard-coded IPv4 literals that bypass DNS64,
- PMTUD/ICMP filtering.

---

## 13. Common mistakes

1. **Calling NPTv6 “NAT64 for IPv6.”** NAT64 is cross-family; NPTv6 is IPv6-to-IPv6.
2. **Assuming DNS64 is the translator.** DNS64 synthesizes AAAA; NAT64 rewrites packet headers.
3. **Routing `64:ff9b::/96` to the Internet.** It should be routed to the NAT64 translator in the IPv6 domain.
4. **Expecting dynamic NAT64 PAT to accept unsolicited IPv4 connections.** Without static binding/state, it normally cannot.
5. **Assuming NPTv6 translates ports.** It does not.
6. **Assuming NPTv6 automatically provides firewall security.** It does not.
7. **Ignoring the external-prefix route in NPTv6.** Return traffic must find the translator.
8. **Ignoring checksum-neutral adjustment.** The mapped address may not be a simplistic prefix swap.
9. **Assuming “stateless NPTv6” means a firewall keeps no sessions.** Translation state and firewall session state are different concepts.
10. **Skipping platform/release validation.** Cisco and Fortinet support details vary materially by hardware/software release.

---

## 14. Sources

### IETF

- https://www.rfc-editor.org/rfc/rfc6052.html
- https://www.rfc-editor.org/rfc/rfc6146.html
- https://www.rfc-editor.org/rfc/rfc6296.html

### Cisco

- https://www.cisco.com/c/en/us/td/docs/routers/ios/config/17-x/ip-addressing/b-ip-addressing/m_iadnat-stateful-nat64.html
- https://www.cisco.com/c/en/us/td/docs/routers/ios/config/17-x/ip-addressing/b-ip-addressing/m_iadnat-asr1k-nptv6.html

### Palo Alto Networks

- https://docs.paloaltonetworks.com/ngfw/networking/nat64
- https://docs.paloaltonetworks.com/ngfw/networking/nat64/configure-nat64-for-ipv6-initiated-communication
- https://docs.paloaltonetworks.com/ngfw/networking/nptv6/how-nptv6-works
- https://docs.paloaltonetworks.com/ngfw/networking/nptv6/create-an-nptv6-policy

### Fortinet

- https://docs.fortinet.com/document/fortigate/latest/administration-guide/443324/nat64-policy-and-dns64-dns-proxy
- https://docs.fortinet.com/document/fortigate/7.6.0/new-features/625228/nptv6-protocol-for-ipv6-address-translation

---

## Final study mnemonic

```text
NAT64:
IPv6 client ──IPv6──> NAT64 ──IPv4──> IPv4 server
          DNS64 usually creates the IPv6 destination

NPTv6:
IPv6 host ──inside IPv6 prefix──> NPTv6 ──outside IPv6 prefix──> IPv6 network
          same address family, deterministic 1:1, no port translation
```
