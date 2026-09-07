from pathlib import Path

p = Path('09-07-26-07-03_Palo_Alto_Networks_Firewalling_in_GCP_Deep_Dive.md')
text = p.read_text()
start = text.index('## 6.2 Model B — direct Internet egress through VM-Series')
end = text.index('## 6.3 Standard versus direct Internet egress', start)

replacement = r'''## 6.2 Model B — direct Internet egress through VM-Series

Google added NSI **direct Internet egress** on **August 20, 2026**. Google documents that, in this model, the network security appliance in the producer VPC inspects an outbound packet and sends the allowed packet **directly to the Internet through the appliance's external network interface**. The Internet response returns to the appliance, which then sends the response **directly to the consumer VM over GENEVE**, avoiding the standard-NSI hairpin back through the consumer VPC before Internet egress.

Google also states that enabling direct Internet egress does **not** require additional NSI producer resources, consumer resources, Cloud NAT, or a consumer default Internet route. The appliance itself must be configured for direct egress according to its vendor documentation.

Palo Alto Networks documents the corresponding VM-Series implementation as **GCP NSI Overlay Support**. Palo Alto describes this mode as enabling **direct packet egress** and **inner routing**, which lets PAN-OS use its own routing table to forward an inspected inner packet instead of always re-encapsulating the allowed outbound packet back to the consumer VPC first.

**Primary references:**

- Palo Alto Networks — Configure GCP NSI Overlay Support: https://docs.paloaltonetworks.com/vm-series/deployment/public-cloud/set-up-the-vm-series-firewall-on-google-cloud-platform/configure-gcp-nsi-overlay-support
- Google Cloud — NSI in-band integration overview / Direct Internet Egress: https://docs.cloud.google.com/network-security-integration/docs/in-band/in-band-integration-overview
- Google Cloud — NSI release notes, August 20, 2026: https://docs.cloud.google.com/network-security-integration/docs/release-notes

### 6.2.1 Palo Alto prerequisites and topology

Palo Alto documents these requirements for GCP NSI Overlay Support:

- **VM-Series** firewall;
- **PAN-OS 12.1.8 or later**;
- an already deployed Google Cloud NSI environment;
- `nic0` used for **Management**;
- `nic1` used for **Trust**;
- `nic2` used for **Untrust**;
- security endpoint placement and target consumer workloads must satisfy Google's documented regional-placement requirements;
- **autoscaling is currently not supported** for GCP NSI Overlay.

The topology difference is:

```text
Standard NSI
Consumer VM
  -> NSI / GENEVE
  -> VM-Series
  -> GENEVE reinjection to consumer VPC
  -> consumer Internet route / Cloud NAT
  -> Internet

GCP NSI Overlay / direct Internet egress
Consumer VM
  -> NSI / GENEVE
  -> VM-Series Trust (ethernet1/1)
  -> PAN-OS inner route lookup
  -> Trust-to-Untrust Security/NAT processing
  -> VM-Series Untrust (ethernet1/2)
  -> Internet
```

The producer firewall therefore becomes both the NSI inspection engine and the routed Internet egress/return point for the selected flow.

### 6.2.2 Configure Trust and Untrust interfaces on PAN-OS

Palo Alto's documented CLI example assigns intercepted workload traffic to `ethernet1/1` and direct Internet egress to `ethernet1/2`.

Trust:

```cli
set network interface ethernet ethernet1/1 layer3 dhcp-client enable yes
set network virtual-router default interface ethernet1/1
set zone Trust network layer3 ethernet1/1
```

Untrust:

```cli
set network interface ethernet ethernet1/2 layer3 dhcp-client enable yes
set network virtual-router default interface ethernet1/2
set zone Untrust network layer3 ethernet1/2
```

`ethernet1/1` receives the inner workload packet after GENEVE decapsulation. With NSI Overlay enabled, PAN-OS can perform an inner-packet route lookup and forward the packet out `ethernet1/2` instead of returning it to the consumer VPC.

### 6.2.3 Disable the Trust-interface default route

Palo Alto specifically instructs you to disable the default route learned on the application-facing dataplane interface:

```cli
set network interface ethernet1/1 layer3 config-type static no-default-route yes
```

Replace `ethernet1/1` if your Trust/application dataplane interface uses a different name.

**Why:** the Trust-facing interface should not install a competing default route that can send Internet-bound inner traffic back toward the Trust/inspection side. The desired direct-egress path is through Untrust.

Commit the interface/routing changes.

### 6.2.4 Configure NAT for east-west and Internet traffic

Palo Alto documents a **no-NAT** rule for Trust-to-Trust east-west traffic:

```cli
set rulebase nat rules no-nat-east-west from Trust to Trust
set rulebase nat rules no-nat-east-west source any destination any service any
```

For Internet-bound Trust-to-Untrust traffic, Palo Alto documents source NAT using the Untrust interface address:

```cli
set rulebase nat rules egress-nat from Trust to Untrust
set rulebase nat rules egress-nat source any destination any service any
set rulebase nat rules egress-nat source-translation dynamic-ip-and-port interface-address interface ethernet1/2
```

Commit the NAT changes.

Before PAN-OS SNAT, the inner packet still has the consumer workload's private source address. After the Trust-to-Untrust NAT rule, PAN-OS translates the source to the address associated with `ethernet1/2` and owns the Internet-leg NAT/session state.

```text
Before PAN-OS SNAT:
10.10.1.10:51514 -> 198.51.100.25:443

After PAN-OS SNAT:
UNTRUST_INTERFACE_ADDRESS:translated-port -> 198.51.100.25:443
```

Verify the actual translated source port from PAN-OS session/NAT state rather than assuming it.

### 6.2.5 Enable Palo Alto GCP NSI Overlay inspection

Palo Alto documents this feature-specific command:

```cli
request plugins vm_series gcp nsi inspect enable yes
```

Verify status:

```cli
show plugins vm_series gcp nsi status
```

Verify GENEVE encapsulation and decapsulation activity:

```cli
show counter global filter delta yes | match geneve
```

Palo Alto specifically recommends confirming that `geneve_encap` and `geneve_decap` counters increment while test traffic flows.

To disable the feature:

```cli
request plugins vm_series gcp nsi inspect enable no
```

Commit configuration changes where PAN-OS requires it.

### 6.2.6 PAN-OS Security policy is still required

NSI interception does not replace PAN-OS policy enforcement. After VM-Series decapsulates the packet, the inner flow must be permitted by the applicable PAN-OS **Security policy** and any attached App-ID/content-security profiles.

The logical Internet-egress policy relationship is normally:

```text
Source zone:       Trust
Destination zone:  Untrust
Source:            intended consumer workloads
Destination:       approved Internet destinations / any as required
Application:       explicitly allowed applications
Service:           application-default or required service policy
Action:            allow
Security profiles: attach as required
```

Palo Alto's NSI Overlay setup page focuses on interface, routing, NAT, and plugin requirements rather than prescribing one universal Security rule, so build the actual Security policy to your organization's requirements.

### 6.2.7 Forward packet flow after Overlay is enabled

Example:

```text
Consumer: 10.10.1.10:51514
Internet: 198.51.100.25:443
```

1. The consumer VM initiates the connection.
2. The consumer NSI firewall rule matches the new session and invokes `APPLY_SECURITY_PROFILE_GROUP`.
3. Google sends the packet to the producer service in GENEVE.
4. The producer ILB selects a healthy VM-Series backend.
5. VM-Series decapsulates the packet and sees the original inner tuple.
6. PAN-OS performs Security/App-ID/threat inspection.
7. NSI Overlay enables **inner routing**, so PAN-OS performs its route lookup for the inspected inner packet.
8. The Internet route selects Untrust (`ethernet1/2`).
9. The Trust-to-Untrust NAT rule source-NATs the connection using the `ethernet1/2` interface address.
10. VM-Series sends the packet directly to the Internet instead of GENEVE-reinjecting this allowed outbound packet back into the consumer VPC.

### 6.2.8 Return path — Internet response back to the consumer

1. The Internet server replies to the public source identity created by VM-Series Untrust/NAT state.
2. The response arrives on the VM-Series Untrust path.
3. PAN-OS performs existing-session lookup and reverse NAT.
4. PAN-OS applies stateful inspection to the response.
5. VM-Series uses metadata from the original NSI/GENEVE flow to construct the response GENEVE packet for the consumer.
6. Google documents that the appliance sends the Internet response **directly to the consumer VM using GENEVE**.
7. Google reinjects the decapsulated response to the original consumer workload.
8. The consumer receives the response without Cloud NAT or a consumer default Internet route participating in this inspected direct-egress flow.

This produces two producer/consumer boundary crossings:

```text
Hop 1  consumer -> producer   intercepted outbound flow
Hop 2  producer -> consumer   inspected Internet response over GENEVE
```

Google contrasts this with standard in-band NSI, which has four crossings because the allowed outbound packet is first reinjected to the consumer VPC for Internet egress and the response later traverses inspection again.

### 6.2.9 Google-side configuration: what changes and what does not

Once standard NSI producer/consumer resources are working, Google states that direct Internet egress does **not** require additional producer-VPC, consumer-VPC, or in-band NSI resource configuration solely to turn on direct egress. Configure the network appliance according to vendor documentation.

The NSI object chain remains:

```text
consumer firewall policy
 -> APPLY_SECURITY_PROFILE_GROUP
 -> security profile group
 -> custom-intercept profile
 -> intercept endpoint group
 -> deployment group
 -> zonal deployment
 -> internal passthrough ILB
 -> VM-Series
```

What changes is what VM-Series does **after inspection** of an allowed Internet-bound packet.

For selected direct-egress flows, Google documents that the consumer VPC does **not** require Cloud NAT or a consumer default Internet route.

### 6.2.10 Verification on VM-Series

```cli
show plugins vm_series gcp nsi status
show counter global filter delta yes | match geneve
show session all filter source 10.10.1.10 destination 198.51.100.25
show routing route
```

**Success criteria:**

- NSI Overlay reports enabled/healthy;
- `geneve_decap` increases when consumer traffic arrives;
- PAN-OS creates the expected session for the original inner flow;
- routing selects the Untrust Internet path;
- the egress NAT rule translates Trust-to-Untrust traffic;
- Internet response traffic returns to VM-Series;
- reverse NAT/session lookup succeeds;
- `geneve_encap` increases when responses are returned to the consumer;
- the consumer receives the response without depending on Cloud NAT.

### 6.2.11 Troubleshooting direct Internet egress

#### Outbound GENEVE reaches VM-Series but traffic does not leave Untrust

**Where:** PAN-OS interface/routing/NAT state.

**Check:**

```cli
show plugins vm_series gcp nsi status
show routing route
show session all filter source 10.10.1.10 destination 198.51.100.25
show counter global filter severity drop delta yes
```

**What failure means:** NSI delivered the packet, but PAN-OS likely lacks a usable inner route, Security policy, or Trust-to-Untrust NAT path.

#### Traffic exits the wrong interface

**Where:** PAN-OS virtual router and DHCP/default-route behavior.

**Check:** verify `ethernet1/1` has `no-default-route yes` and the Internet route resolves through Untrust.

#### Internet server receives traffic but response does not reach consumer

**Where:** PAN-OS NAT/session state and GENEVE response encapsulation.

**Check:** confirm the response reaches Untrust, matches the established PAN-OS session, reverse NAT succeeds, and `geneve_encap` increments when the return packet is sent toward the consumer.

#### GENEVE counters do not increment

**Where:** Palo Alto NSI plugin and Google NSI producer chain.

**Check:** `show plugins vm_series gcp nsi status`, producer ILB health, intercept deployment state, and consumer policy selection.

### 6.2.12 Limitations and design cautions

- Palo Alto requires **PAN-OS 12.1.8 or later** for GCP NSI Overlay Support.
- Palo Alto currently states that **autoscaling is not supported** for GCP NSI Overlay.
- Keep the documented `nic0` Management, `nic1` Trust, and `nic2` Untrust role mapping unless newer Palo Alto documentation explicitly supports another topology.
- Direct Internet egress changes the NAT owner: PAN-OS can own the Internet SNAT/session state instead of consumer Cloud NAT.
- Do not troubleshoot this model as though the allowed outbound packet must be reinjected into the consumer VPC; that is standard NSI, not Overlay direct egress.
- A working NSI control-plane chain does not prove PAN-OS has the correct inner route, Security policy, NAT policy, or Internet-facing Untrust connectivity.

**Source information:** Palo Alto Networks documents GCP NSI Overlay Support, its PAN-OS 12.1.8 requirement, three-interface role mapping, Trust default-route suppression, Trust-to-Trust no-NAT, Trust-to-Untrust interface-address SNAT, the `request plugins vm_series gcp nsi inspect enable yes` command, status/counter verification, and the current no-autoscaling limitation.

**Additional explanation:** Google's direct-egress feature supplies the interception/reinjection framework, while PAN-OS becomes responsible for inner-packet routing, Security/NAT policy, and the Internet-facing forwarding leg.

**Reasonable inference:** Operationally, direct Internet egress is a hybrid of transparent NSI insertion on the consumer-to-firewall leg and a conventional routed/NATed PAN-OS Internet edge on the firewall-to-Internet leg.

'''

p.write_text(text[:start] + replacement + text[end:])
