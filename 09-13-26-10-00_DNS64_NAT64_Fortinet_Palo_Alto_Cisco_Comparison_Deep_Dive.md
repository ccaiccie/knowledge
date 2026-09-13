# DNS64, NAT64, and NPTv6 Across Cisco, Palo Alto Networks, and Fortinet — Deep Dive

## Source URLs

### IETF
- RFC 6052 — IPv4-Embedded IPv6 Address Format: https://www.rfc-editor.org/rfc/rfc6052.html
- RFC 6146 — Stateful NAT64: https://www.rfc-editor.org/rfc/rfc6146.html
- RFC 6296 — NPTv6: https://www.rfc-editor.org/rfc/rfc6296.html

### Cisco
- Cisco IOS XE 17.x Stateful NAT64: https://www.cisco.com/c/en/us/td/docs/routers/ios/config/17-x/ip-addressing/b-ip-addressing/m_iadnat-stateful-nat64.html
- Cisco IOS XE 17.x NPTv6: https://www.cisco.com/c/en/us/td/docs/routers/ios/config/17-x/ip-addressing/b-ip-addressing/m_iadnat-asr1k-nptv6.html

### Palo Alto Networks
- NAT64: https://docs.paloaltonetworks.com/ngfw/networking/nat64
- IPv6-initiated NAT64: https://docs.paloaltonetworks.com/ngfw/networking/nat64/configure-nat64-for-ipv6-initiated-communication
- NPTv6: https://docs.paloaltonetworks.com/ngfw/networking/nptv6/how-nptv6-works
- Create NPTv6 Policy: https://docs.paloaltonetworks.com/ngfw/networking/nptv6/create-an-nptv6-policy
- PAN-OS 11.2 Configure CLI hierarchy: https://docs.paloaltonetworks.com/ngfw/pan-os-cli-quick-start/cli-command-hierarchy/pan-os-11-2-configure-cli-command-hierarchy
- PAN-OS 12.1 removed set commands: https://docs.paloaltonetworks.com/ngfw/pan-os-cli-quick-start/cli-changes/deleted-set-commands-12-1

### Fortinet
- NAT64 policy and DNS64: https://docs.fortinet.com/document/fortigate/latest/administration-guide/443324/nat64-policy-and-dns64-dns-proxy
- NAT66, NAT46, NAT64, and DNS64: https://docs.fortinet.com/document/fortigate/7.4.10/administration-guide/627219/nat66-nat46-nat64-and-dns64
- FortiOS 7.6 NPTv6: https://docs.fortinet.com/document/fortigate/7.6.0/new-features/625228/nptv6-protocol-for-ipv6-address-translation

## Table of Contents

1. [Core mental model](#1-core-mental-model)
2. [NAT64 architecture and packet flow](#2-nat64-architecture-and-packet-flow)
3. [NPTv6 architecture and packet flow](#3-nptv6-architecture-and-packet-flow)
4. [Vendor comparison](#4-vendor-comparison)
5. [Cisco IOS XE implementation](#5-cisco-ios-xe-implementation)
6. [Palo Alto Networks implementation](#6-palo-alto-networks-implementation)
7. [FortiGate implementation](#7-fortigate-implementation)
8. [Routing, HA, and design implications](#8-routing-ha-and-design-implications)
9. [Verification and troubleshooting](#9-verification-and-troubleshooting)
10. [Common mistakes](#10-common-mistakes)
11. [Sources](#11-sources)

---

## 1. Core mental model

The simplest distinction is:

> **NAT64 changes the address family. NPTv6 keeps IPv6 and changes the prefix.**

| Property | NAT64 | NPTv6 |
|---|---|---|
| Address families | IPv6 ↔ IPv4 | IPv6 ↔ IPv6 |
| Primary use | IPv6-only clients reaching IPv4-only services | Prefix independence, renumbering, multihoming |
| Typical state | Stateful in common enterprise implementations | Stateless mapping |
| Port translation | Often yes with PAT/DIPP | No |
| DNS dependency | DNS64 commonly used for name-based IPv6→IPv4 access | None inherent |
| Address mapping | Can be many-to-one | Deterministic 1:1 |
| Security function | No | No |

### DNS64 versus NAT64

**DNS64** synthesizes an AAAA record from an IPv4 A record.

Example:

```text
A record:
server.example → 192.0.2.25

NAT64 prefix:
64:ff9b::/96

Synthesized AAAA:
server.example → 64:ff9b::c000:219
```

**NAT64** translates the subsequent packet flow.

![DNS64 and NAT64 control/data-plane flow](images/09-13-26-10-00_dns64_nat64_control_data_plane.svg)

[Editable draw.io source](images/09-13-26-10-00_dns64_nat64_control_data_plane.drawio)

**What this image shows:** DNS64 creates the synthetic IPv6 destination, while NAT64 performs the data-plane translation.

**What matters:** DNS64 and NAT64 can exist on different devices.

**What to verify:** both functions must use the same NAT64 prefix.

---

## 2. NAT64 architecture and packet flow

Assume:

```text
IPv6 client:       2001:db8:10::10
IPv4 server:       192.0.2.80:443
NAT64 prefix:      64:ff9b::/96
NAT64 IPv4 pool:   198.51.100.10
```

![NAT64 packet flow](images/13-09-26-09-54_nat64_packet_flow.svg)

[Editable draw.io source](images/13-09-26-09-54_nat64_packet_flow.drawio)

**What this image shows:** an IPv6-only client resolves an IPv4-only server through DNS64, sends to an IPv4-embedded IPv6 destination, and the translator emits an IPv4 flow.

**What matters:** `64:ff9b::c000:250` encodes IPv4 `192.0.2.80`; it is not an IPv6 address configured on the server.

**What to verify:** the NAT64 prefix routes to the translator, the IPv4 source pool is routable, and return traffic comes back through the translator.

### 2.1 Forward flow

```text
IPv6:
2001:db8:10::10:51500
    →
64:ff9b::c000:250:443
```

The translator identifies the embedded destination `192.0.2.80`, allocates an IPv4 source, and emits:

```text
IPv4:
198.51.100.10:40001
    →
192.0.2.80:443
```

### 2.2 Return flow

The IPv4 server replies to `198.51.100.10:40001`. The NAT64 device finds the existing state and translates the packet back to the original IPv6 client.

---

## 3. NPTv6 architecture and packet flow

NPTv6 translates one IPv6 prefix to another while staying entirely in IPv6.

![NPTv6 packet flow](images/13-09-26-09-54_nptv6_packet_flow.svg)

[Editable draw.io source](images/13-09-26-09-54_nptv6_packet_flow.drawio)

**What this image shows:** an inside IPv6 prefix is represented externally by another IPv6 prefix.

**What matters:** NPTv6 is deterministic and 1:1. It does not create PAT mappings.

**What to verify:** upstream routing sends the translated external prefix back to the NPTv6 device.

### 3.1 Checksum neutrality

RFC 6296 requires checksum-neutral translation. TCP and UDP checksums include IPv6 source/destination information in the pseudo-header, so NPTv6 must preserve the checksum contribution.

This means the result is **not always a simplistic textual prefix swap**; a compensating 16-bit adjustment can be involved.

### 3.2 Stateless mapping versus firewall state

NPTv6 itself does not require a per-flow NAT mapping table. A firewall performing NPTv6 can still keep normal security-session state.

---

## 4. Vendor comparison

| Capability | Cisco IOS XE | Palo Alto PAN-OS | FortiGate FortiOS |
|---|---|---|---|
| Stateful NAT64 | Yes | Yes | Yes |
| DNS64 on device | Separate DNS64 installation | External/third-party DNS64 for IPv6-initiated DNS workflow | Yes, documented DNS proxy/DNS64 |
| NAT64 PAT | `overload` | DIPP | IPv4 IP pool / policy NAT64 |
| NPTv6 | Yes; `nat66` CLI terminology | Yes; dedicated NPTv6 NAT type | FortiOS 7.6 adds documented partial RFC 6296 support |
| NPTv6 translation state | Stateless | Stateless | Stateless |
| Ports translated by NPTv6 | No | No | No |

![Vendor placement comparison](images/09-13-26-10-00_dns64_nat64_vendor_placement.svg)

[Editable draw.io source](images/09-13-26-10-00_dns64_nat64_vendor_placement.drawio)

---

## 5. Cisco IOS XE implementation

### 5.1 Cisco Stateful NAT64

Cisco IOS XE performs Stateful NAT64 and requires a separate working DNS64 installation for DNS-based use.

Example:

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

### 5.2 Cisco NAT64 verification

```cli
show nat64 translations
show nat64 pools
show nat64 prefix stateful global
show nat64 statistics
show nat64 timeouts
show ipv6 route 64:FF9B::/96
show ip route 198.51.100.10
```

**Success criteria:** translation entries appear after traffic starts, counters increment, and both IPv6 and IPv4 routing are correct.

### 5.3 Cisco NPTv6

Cisco uses **NAT66** CLI terminology for NPTv6.

```cli
interface GigabitEthernet0/0/0
 nat66 inside
!
interface GigabitEthernet0/0/1
 nat66 outside
!
nat66 prefix inside 2001:DB8:10::/48 outside 2001:DB8:200::/48
```

### 5.4 Cisco NPTv6 verification

```cli
show nat66 prefix
show nat66 statistics
show platform hardware qfp active feature nat66 datapath prefix
show platform hardware qfp active feature nat66 datapath statistics
```

---

## 6. Palo Alto Networks implementation

PAN-OS supports both stateful NAT64 and NPTv6. For the common IPv6-initiated NAT64 workflow, PAN-OS relies on an external DNS64 service.

> **Version note:** The `set` examples below use PAN-OS 11.2-style local firewall CLI syntax. Palo Alto documents direct `set rulebase nat ...` commands in PAN-OS 11.2, while PAN-OS 12.1 lists that command family among removed set commands. Validate the hierarchy on the target release before pasting.

### 6.1 Palo Alto NPTv6

Example:

```text
Internal ULA:       fd00:10:10::/64
Translated GUA:     2001:db8:100:10::/64
Internal host:      fd00:10:10::1234
External identity:  2001:db8:100:10::1234
```

![Palo Alto NPTv6 configuration](images/09-13-26-10-35_palo_alto_nptv6_configuration.svg)

[Editable draw.io](images/09-13-26-10-35_palo_alto_nptv6_configuration.drawio)

**What this image shows:** PAN-OS translates the IPv6 prefix while preserving the host/interface identity according to NPTv6 behavior.

**What matters:** NPTv6 is IPv6-to-IPv6 only and does not replace Security policy.

**What to verify:** the translated prefix routes back to the firewall and Security policy permits the flow.

#### 6.1.1 Address objects

```cli
configure

set address NPTV6-INSIDE ip-netmask fd00:10:10::/64
set address NPTV6-OUTSIDE ip-netmask 2001:db8:100:10::/64
```

#### 6.1.2 NPTv6 NAT rule

```cli
set rulebase nat rules NPTV6-OUT nat-type nptv6
set rulebase nat rules NPTV6-OUT from Trust-v6
set rulebase nat rules NPTV6-OUT to Untrust-v6
set rulebase nat rules NPTV6-OUT source NPTV6-INSIDE
set rulebase nat rules NPTV6-OUT destination any
set rulebase nat rules NPTV6-OUT service any
set rulebase nat rules NPTV6-OUT source-translation static-ip translated-address NPTV6-OUTSIDE
set rulebase nat rules NPTV6-OUT source-translation static-ip bi-directional yes
```

#### 6.1.3 NPTv6 Security policy

```cli
set rulebase security rules NPTV6-OUT-ALLOW from Trust-v6
set rulebase security rules NPTV6-OUT-ALLOW to Untrust-v6
set rulebase security rules NPTV6-OUT-ALLOW source NPTV6-INSIDE
set rulebase security rules NPTV6-OUT-ALLOW destination any
set rulebase security rules NPTV6-OUT-ALLOW application any
set rulebase security rules NPTV6-OUT-ALLOW service application-default
set rulebase security rules NPTV6-OUT-ALLOW action allow
```

#### 6.1.4 NPTv6 packet transformation

```text
Before:
SRC fd00:10:10::1234
DST 2001:db8:ffff::80

After:
SRC 2001:db8:100:10::1234
DST 2001:db8:ffff::80
```

Palo Alto documents NPTv6 prefixes from **/32 through /112** for the relevant policy fields. Beginning with PAN-OS 11.1.5, Palo Alto also documents source NPTv6 with dynamically assigned prefixes from DHCPv6, PPPoEv6, or cellular/5G interfaces.

NDP Proxy may be required when the translated prefix must be represented on-link.

### 6.2 Palo Alto NAT64

Example:

```text
IPv6 client:            2001:db8:10::100
NAT64 prefix:           64:ff9b::/96
IPv4-only server:       192.0.2.25
DNS64 synthesized AAAA: 64:ff9b::c000:219
IPv4 SNAT address:      203.0.113.10
```

![Palo Alto NAT64 configuration](images/09-13-26-10-35_palo_alto_nat64_configuration.svg)

[Editable draw.io](images/09-13-26-10-35_palo_alto_nat64_configuration.drawio)

**What this image shows:** external DNS64 creates the synthetic IPv6 destination and PAN-OS performs the stateful translation to IPv4.

**What matters:** PAN-OS extracts the embedded IPv4 destination from the NAT64 address for the IPv6-initiated workflow.

**What to verify:** DNS64 prefix, NAT64 match prefix, IPv4 SNAT, route lookup, and return path.

#### 6.2.1 Address objects

```cli
configure

set address IPV6-CLIENTS ip-netmask 2001:db8:10::/64
set address NAT64-PREFIX ip-netmask 64:ff9b::/96
set address NAT64-IPV4-SNAT ip-netmask 203.0.113.10/32
```

#### 6.2.2 NAT64 NAT rule

```cli
set rulebase nat rules NAT64-V6-OUT nat-type nat64
set rulebase nat rules NAT64-V6-OUT from Trust-v6
set rulebase nat rules NAT64-V6-OUT to Untrust-v4
set rulebase nat rules NAT64-V6-OUT source IPV6-CLIENTS
set rulebase nat rules NAT64-V6-OUT destination NAT64-PREFIX
set rulebase nat rules NAT64-V6-OUT service any
set rulebase nat rules NAT64-V6-OUT source-translation dynamic-ip-and-port translated-address NAT64-IPV4-SNAT
```

For this IPv6-initiated example there is intentionally no explicit destination-translation line; PAN-OS derives the IPv4 destination from the IPv4-embedded IPv6 destination.

#### 6.2.3 NAT64 Security policy

Palo Alto Security policy evaluates **pre-NAT source/destination addresses** while using the **post-NAT destination zone**.

```cli
set rulebase security rules NAT64-V6-OUT-ALLOW from Trust-v6
set rulebase security rules NAT64-V6-OUT-ALLOW to Untrust-v4
set rulebase security rules NAT64-V6-OUT-ALLOW source IPV6-CLIENTS
set rulebase security rules NAT64-V6-OUT-ALLOW destination NAT64-PREFIX
set rulebase security rules NAT64-V6-OUT-ALLOW application any
set rulebase security rules NAT64-V6-OUT-ALLOW service application-default
set rulebase security rules NAT64-V6-OUT-ALLOW action allow
```

#### 6.2.4 NAT64 packet transformation

```text
Before NAT64:
SRC 2001:db8:10::100
DST 64:ff9b::c000:219

After NAT64:
SRC 203.0.113.10
DST 192.0.2.25
```

#### 6.2.5 Commit and verify

```cli
commit
```

```cli
> set cli config-output-format set
> configure
# show rulebase nat
```

Session verification:

```cli
> show session all filter source 2001:db8:10::100
> show session id <session-id>
```

NPTv6-focused verification:

```cli
show session all filter source <ipv6-address>
show session all filter destination <ipv6-address>
show routing route
show neighbor interface all
```

Palo Alto also documents `test nptv6` for applicable checksum-neutral mapping validation scenarios.

---

## 7. FortiGate implementation

FortiGate can provide DNS64 and NAT64 on the same appliance, and FortiOS 7.6 adds documented NPTv6 support.

### 7.1 FortiGate DNS64

```cli
config system dns64
    set status enable
    set dns64-prefix 64:ff9b::/96
    set always-synthesize-aaaa-record enable
end
```

### 7.2 FortiGate DNS service

A documented DNS-proxy pattern includes:

```cli
config system dns-server
    edit "port10"
        set mode forward-only
    next
end
```

### 7.3 FortiGate NAT64 objects

```cli
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

Fortinet then uses an IPv4 IP pool and firewall policy with NAT64 enabled according to the deployment design.

With Central NAT, Fortinet documents two-stage policy evaluation around the NAT64 path, so pre- and post-translation matching must be designed carefully.

### 7.4 FortiGate NAT64 verification

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

Stop debug:

```cli
diagnose debug disable
```

### 7.5 FortiGate NPTv6

FortiOS 7.6.0 documents partial RFC 6296 support using an IPv6 IP pool of type `nptv6`.

```cli
config firewall ippool6
    edit "NPTV6-POOL"
        set type nptv6
        set internal-prefix 2001:db8:10::/64
        set external-prefix 2001:db8:200::/64
    next
end
```

That pool is referenced by the relevant IPv6 firewall policy.

### 7.6 FortiGate NPTv6 verification

```cli
show firewall ippool6
show firewall policy
diagnose sys session list
diagnose debug flow filter addr6 <ipv6-address>
diagnose debug flow show function-name enable
diagnose debug enable
diagnose debug flow trace start 20
```

---

## 8. Routing, HA, and design implications

### 8.1 NAT64 routing

The IPv6 realm must route the NAT64 prefix toward the translator. The IPv4 side must return traffic for the translated source pool/address through the NAT64 device.

### 8.2 NPTv6 routing

The translated external prefix must route back toward the NPTv6 device. Translation does not automatically advertise that prefix.

### 8.3 HA

- **NAT64:** session/binding state may need HA synchronization if failover must preserve sessions.
- **NPTv6:** the address mapping itself is algorithmic and stateless; firewall session state may still need synchronization.

### 8.4 MTU and PMTUD

Do not block ICMPv6 Packet Too Big messages or the relevant translated ICMP behavior. Some apparent application failures are really Path MTU Discovery failures.

### 8.5 NAT is not security

Neither NAT64 nor NPTv6 replaces Security policy, ACLs, or zone-policy enforcement.

---

## 9. Verification and troubleshooting

### Symptom: DNS name resolves but NAT64 connection fails

**Where:** DNS64, IPv6 routing, translator, IPv4 routing.

**Check:**
- synthesized AAAA prefix;
- route to NAT64 prefix;
- NAT64 rule/policy match;
- IPv4 source pool;
- return route;
- firewall state.

**Expected:** translation/session appears and translated IPv4 traffic leaves toward the server.

### Symptom: IPv4 server sees packets but IPv6 client receives no reply

Check:
1. return route to the translator;
2. NAT64 session/binding;
3. asymmetry;
4. firewall policy;
5. HA member receiving the return flow;
6. PMTUD/ICMP.

### Symptom: NPTv6 outbound works but inbound fails

Check:
1. route for the external translated prefix;
2. Security policy;
3. NDP Proxy where required;
4. correct inside/outside direction;
5. vendor mapping calculation/verification.

### Symptom: translated NPTv6 address is not the simple prefix + host bits expected

This can be correct because RFC 6296 checksum neutrality can require an adjustment. Validate with the vendor's NPTv6 diagnostic method rather than manually concatenating strings.

### Symptom: only some applications fail through NAT64

Investigate:
- hard-coded IPv4 literals;
- payloads containing IP addresses;
- ALG requirements;
- unsupported IPv4 options/IPv6 extension headers;
- IPsec/protocol limitations;
- PMTUD.

---

## 10. Common mistakes

1. Calling NPTv6 “NAT64 for IPv6.”
2. Assuming DNS64 translates packets.
3. Routing `64:ff9b::/96` toward the public Internet instead of toward the NAT64 translator.
4. Expecting dynamic NAT64 PAT to accept unsolicited IPv4-initiated traffic without a static binding.
5. Assuming NPTv6 translates ports.
6. Treating NAT64 or NPTv6 as a security policy.
7. Ignoring return routing for the translated NPTv6 prefix.
8. Assuming checksum-neutral NPTv6 is always a literal prefix swap.
9. Assuming “stateless NPTv6” means a firewall keeps no sessions.
10. Copying vendor commands across releases without validating exact platform/software support.

---

## 11. Sources

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
- https://docs.paloaltonetworks.com/ngfw/pan-os-cli-quick-start/cli-command-hierarchy/pan-os-11-2-configure-cli-command-hierarchy
- https://docs.paloaltonetworks.com/ngfw/pan-os-cli-quick-start/cli-changes/deleted-set-commands-12-1

### Fortinet
- https://docs.fortinet.com/document/fortigate/latest/administration-guide/443324/nat64-policy-and-dns64-dns-proxy
- https://docs.fortinet.com/document/fortigate/7.4.10/administration-guide/627219/nat66-nat46-nat64-and-dns64
- https://docs.fortinet.com/document/fortigate/7.6.0/new-features/625228/nptv6-protocol-for-ipv6-address-translation
