# DNS64 and NAT64 Across Fortinet, Palo Alto Networks, and Cisco — Deep Dive

## Source URLs

- Fortinet FortiGate — NAT64 policy and DNS64 (DNS proxy)  
  https://docs.fortinet.com/document/fortigate/latest/administration-guide/443324/nat64-policy-and-dns64-dns-proxy
- Fortinet FortiGate — NAT66, NAT46, NAT64, and DNS64  
  https://docs.fortinet.com/document/fortigate/7.4.10/administration-guide/627219/nat66-nat46-nat64-and-dns64
- Palo Alto Networks — NAT64  
  https://docs.paloaltonetworks.com/ngfw/networking/nat64
- Palo Alto Networks — DNS64 Server  
  https://docs.paloaltonetworks.com/pan-os/10-1/pan-os-networking-admin/nat64/path-mtu-discovery
- Cisco IOS XE 17.x — Stateful NAT64  
  https://www.cisco.com/c/en/us/td/docs/routers/ios/config/17-x/ip-addressing/b-ip-addressing/m_iadnat-stateful-nat64.html

## Table of Contents

1. [Core mental model](#1-core-mental-model)
2. [Vendor comparison](#2-vendor-comparison)
3. [DNS64 packet flow](#3-dns64-packet-flow)
4. [FortiGate](#4-fortigate)
5. [Palo Alto Networks](#5-palo-alto-networks)
6. [Cisco IOS XE](#6-cisco-ios-xe)
7. [Operational caveats](#7-operational-caveats)
8. [Verification and troubleshooting](#8-verification-and-troubleshooting)
9. [Common mistakes](#9-common-mistakes)
10. [Sources](#10-sources)

---

## 1. Core mental model

**DNS64 and NAT64 are different functions.**

- **DNS64** is a DNS synthesis function. It creates an IPv6 AAAA response from an IPv4 A record when an IPv6-only client needs to reach an IPv4-only destination.
- **NAT64** is a packet-translation function. It translates the actual IPv6 flow into IPv4 and maintains the required state for the return traffic.

A common prefix is the RFC 6052 Well-Known Prefix:

```text
64:ff9b::/96
```

If DNS returns:

```text
A = 192.0.2.25
```

DNS64 can synthesize:

```text
AAAA = 64:ff9b::c000:219
```

The final 32 bits encode the IPv4 address.

![DNS64 and NAT64 control/data-plane flow](images/09-13-26-10-00_dns64_nat64_control_data_plane.svg)

[Editable draw.io source](images/09-13-26-10-00_dns64_nat64_control_data_plane.drawio)

**What this image shows:** DNS64 creates the destination IPv6 address before the application opens a connection. NAT64 translates the subsequent data packets.

**What matters:** a NAT64 device does not inherently need to be the DNS64 server. The two functions can be colocated or separated.

**What to verify:** the DNS64 prefix and the NAT64 translation prefix must match.

---

## 2. Vendor comparison

| Vendor / platform | NAT64 on device | DNS64 on device | Practical design |
|---|---:|---:|---|
| **Fortinet FortiGate / FortiOS** | Yes | **Yes** | One FortiGate can provide DNS64 plus NAT64 |
| **Palo Alto Networks NGFW / PAN-OS** | Yes | **No native DNS64 synthesis for this workflow** | Use a separate/third-party DNS64 solution |
| **Cisco IOS XE** | Yes | **No integrated DNS64 prerequisite replacement documented** | Cisco explicitly requires a separate working DNS64 installation for DNS-based NAT64 |

![Vendor placement comparison](images/09-13-26-10-00_dns64_nat64_vendor_placement.svg)

[Editable draw.io source](images/09-13-26-10-00_dns64_nat64_vendor_placement.drawio)

**What this image shows:** FortiGate can colocate DNS64 and NAT64, while Palo Alto and Cisco separate name synthesis from translation.

**What matters:** the external DNS64 server is not forwarding the user data through itself. It only synthesizes the AAAA record. The NAT64 device remains the data-plane translator.

**What to verify:** confirm the external DNS64 server uses the exact NAT64 prefix expected by the firewall/router.

---

## 3. DNS64 packet flow

Assume:

- IPv6-only client: `2001:db8:10::100`
- IPv4-only server: `192.0.2.25`
- NAT64 prefix: `64:ff9b::/96`

### 3.1 DNS stage

1. Client sends a DNS AAAA query for the target hostname.
2. The resolver/DNS64 function checks for an AAAA record.
3. If only an A record exists, DNS64 obtains `192.0.2.25`.
4. DNS64 synthesizes `64:ff9b::c000:219`.
5. The client believes it is connecting to an IPv6 destination.

### 3.2 Data-plane stage

Original IPv6 packet:

```text
Source:      2001:db8:10::100
Destination: 64:ff9b::c000:219
Protocol:    TCP/UDP/ICMP as supported
```

The NAT64 translator recognizes the configured prefix, extracts the embedded IPv4 address, creates/uses translation state, and forwards an IPv4 packet toward:

```text
Destination: 192.0.2.25
```

The return IPv4 packet matches the NAT64 session and is translated back to IPv6.

---

## 4. FortiGate

Fortinet documents native DNS64 on FortiGate in addition to NAT64.

### 4.1 DNS64 configuration

Fortinet documents:

```cli
config system dns64
    set status enable
    set dns64-prefix 64:ff9b::/96
    set always-synthesize-aaaa-record enable
end
```

The default `dns64-prefix` is documented as `64:ff9b::/96`.

FortiGate must also provide DNS service on the relevant IPv6-facing interface so that the client actually sends its DNS queries to the FortiGate.

### 4.2 Synthesis behavior

Fortinet documents two behaviors controlled by:

```cli
set always-synthesize-aaaa-record {enable | disable}
```

With the documented default enabled, DNS64 synthesis is performed according to that mode. If disabled, the DNS proxy first attempts to obtain a real AAAA record and synthesizes an address from the A record when an AAAA record is unavailable.

### 4.3 NAT64 data plane

Fortinet uses NAT64 policy processing to translate the IPv6 packet to IPv4.

Recent FortiOS architecture also uses a per-VDOM NAT46/NAT64 forwarding interface:

```text
naf.<vdom>
```

Fortinet documents that when NAT64 is used with central NAT, policy evaluation can occur in two stages:

```text
IPv6 policy:
srcintf -> naf

translation

IPv4 policy:
naf -> dstintf
```

That policy behavior is important because administrators must ensure the address matching is sufficiently constrained.

### 4.4 Design advantage

FortiGate can own:

```text
DNS64 synthesis
+
NAT64 translation
+
firewall policy
```

on one appliance.

That reduces the number of places where the NAT64 prefix must be synchronized.

---

## 5. Palo Alto Networks

PAN-OS supports NAT64 on the firewall.

Palo Alto documents stateful NAT64 for IPv6-initiated communication and states that a **third-party DNS64 server or other DNS64 solution** must be used when DNS is required for this workflow.

### 5.1 Architecture

```text
IPv6 Client
    |
    | DNS AAAA query
    v
External DNS64
    |
    | synthesized IPv6 destination
    v
IPv6 Client
    |
    | IPv6 packet
    v
Palo Alto NGFW
    |
    | NAT64
    v
IPv4 Server
```

### 5.2 Supported prefixes

Palo Alto documents support for RFC 6052-style IPv4-embedded IPv6 prefixes with these lengths:

```text
/32
/40
/48
/56
/64
/96
```

The prefix can be:

- the Well-Known Prefix `64:ff9b::/96`, or
- a Network-Specific Prefix (NSP).

### 5.3 Important exception

Palo Alto also supports **IPv4-initiated** access to IPv6 servers using static NAT64 mappings.

That use case does **not** require DNS64 because the client starts with an IPv4 destination and the firewall performs the static IPv4-to-IPv6 mapping.

So the statement "Palo Alto requires DNS64" is specifically about the common **IPv6-initiated, DNS-based NAT64 workflow**.

---

## 6. Cisco IOS XE

Cisco IOS XE supports Stateful NAT64.

Cisco's IOS XE 17.x documentation explicitly states:

```text
For DNS traffic to work, you must have a separate working installation of DNS64.
```

Therefore the typical design is:

```text
IPv6 Client
    |
    +---- DNS ----> Separate DNS64
    |
    +---- Data ---> Cisco IOS XE Stateful NAT64 ---> IPv4 Server
```

### 6.1 Data-plane role

IOS XE performs stateful IPv6/IPv4 translation using a configured NAT64 stateful prefix.

The router is therefore responsible for:

- recognizing the NAT64 prefix;
- translating IPv6 source/destination information to IPv4;
- creating translation state;
- forwarding the translated packet;
- translating the return flow back to IPv6.

### 6.2 Cisco restrictions

Cisco documents platform/release-specific restrictions for Stateful NAT64. Depending on platform and IOS XE release these can include:

- application issues where no required ALG exists;
- multicast restrictions;
- restrictions on IPv4 options and IPv6 extension headers;
- VRF-aware NAT64 support differences by platform/release;
- prefix and source-address restrictions to avoid translation loops.

Always check the exact platform's IOS XE configuration guide rather than assuming all IOS XE devices have identical NAT64 capabilities.

---

## 7. Operational caveats

### 7.1 DNS64 and NAT64 prefixes must agree

If DNS64 synthesizes:

```text
64:ff9b::/96
```

but NAT64 expects:

```text
2001:db8:64::/96
```

the translator will not recognize the synthesized destination as belonging to its NAT64 domain.

### 7.2 Real AAAA records

If a hostname already has a reachable native AAAA record, a DNS64 implementation can prefer the real IPv6 path rather than synthesizing one, depending on product configuration.

This is why FortiGate's `always-synthesize-aaaa-record` behavior matters operationally.

### 7.3 DNSSEC

DNS64 changes DNS answers by synthesizing AAAA data from A records. DNSSEC validation therefore requires careful architecture because synthesis and validation points interact.

Do not assume arbitrary end-to-end DNSSEC validation will work unchanged through a DNS64 design. Use the DNS64 implementation's documented DNSSEC guidance.

### 7.4 Literal IPv4 addresses

DNS64 helps only when the application performs DNS resolution.

If an IPv6-only application is hard-coded to connect to:

```text
192.0.2.25
```

DNS64 never participates.

The application or operating system needs another mechanism such as address synthesis at the host, application changes, or an explicit IPv6-mapped destination strategy appropriate to the environment.

### 7.5 Stateful symmetry

Stateful NAT64 maintains connection state. Return traffic must reach the same translation state or an HA mechanism that synchronizes that state if the platform supports it.

---

## 8. Verification and troubleshooting

### Symptom: AAAA lookup returns no usable address

**Where:** DNS64 service.

**What to test:**

```text
AAAA query for an IPv4-only destination
```

**Expected:** a synthesized AAAA record containing the configured NAT64 prefix.

**Failure meaning:** DNS64 is not enabled, the client is not using the DNS64 server, upstream DNS resolution failed, or synthesis policy prevented synthesis.

**Next action:** verify the resolver path and prefix configuration.

### Symptom: Synthesized AAAA exists but connection fails immediately

**Where:** NAT64 translator.

**What to test:** confirm the destination prefix received by the translator matches its configured NAT64 prefix.

**Expected:**

```text
DNS64 prefix == NAT64 translation prefix
```

**Failure meaning:** prefix mismatch or traffic bypassing the translator.

### Symptom: Forward packet translates but return traffic fails

**Where:** IPv4 routing and NAT64 session state.

**What to test:**

- IPv4 route toward the server;
- return route toward the translator;
- state/session table;
- HA symmetry;
- firewall/security policy.

**Failure meaning:** asymmetric path, missing route, policy denial, or lost translation state.

### FortiGate-specific checks

Verify:

- DNS service is enabled on the correct IPv6-facing interface;
- `config system dns64` is enabled;
- the configured DNS64 prefix matches NAT64;
- the NAT64 firewall policy is correct;
- if central NAT is used, both pre- and post-translation policy stages match intentionally.

### Palo Alto-specific checks

Verify:

- the external DNS64 server returns an address from the NAT64 prefix;
- the PAN-OS NAT64 rule uses that prefix;
- the traffic matches the correct security and NAT policy;
- the session table shows the translated flow.

### Cisco-specific checks

Verify:

- DNS is actually pointed at a working DNS64 implementation;
- the stateful NAT64 prefix matches the DNS64 synthesis prefix;
- the NAT64 mapping/state exists;
- IPv4 and IPv6 routing both lead through the translator.

---

## 9. Common mistakes

| Mistake | Correction |
|---|---|
| "NAT64 automatically performs DNS64." | They are separate functions. Some products colocate them; others do not. |
| "Palo Alto has NAT64, therefore it also answers DNS64 queries." | PAN-OS requires a separate/third-party DNS64 solution for the common IPv6-initiated DNS workflow. |
| "Cisco IOS XE NAT64 replaces the DNS64 server." | Cisco explicitly documents separate DNS64 as a prerequisite for DNS traffic. |
| "FortiGate always needs an external DNS64 appliance." | FortiGate has native DNS64 through its DNS proxy. |
| "DNS64 carries the application packets." | DNS64 only provides the synthesized DNS response. NAT64 carries/translates the data flow. |
| "Any IPv6 prefix can be used without coordination." | DNS64 and NAT64 must use compatible, matching translation prefixes. |
| "If DNS works, NAT64 must work." | DNS synthesis and packet translation are independent operational stages. |

---

## 10. Sources

1. Fortinet — NAT64 policy and DNS64 (DNS proxy)  
   https://docs.fortinet.com/document/fortigate/latest/administration-guide/443324/nat64-policy-and-dns64-dns-proxy

2. Fortinet — NAT66, NAT46, NAT64, and DNS64  
   https://docs.fortinet.com/document/fortigate/7.4.10/administration-guide/627219/nat66-nat46-nat64-and-dns64

3. Palo Alto Networks — NAT64  
   https://docs.paloaltonetworks.com/ngfw/networking/nat64

4. Palo Alto Networks — DNS64 Server  
   https://docs.paloaltonetworks.com/pan-os/10-1/pan-os-networking-admin/nat64/path-mtu-discovery

5. Cisco IOS XE 17.x — Stateful Network Address Translation 64  
   https://www.cisco.com/c/en/us/td/docs/routers/ios/config/17-x/ip-addressing/b-ip-addressing/m_iadnat-stateful-nat64.html
