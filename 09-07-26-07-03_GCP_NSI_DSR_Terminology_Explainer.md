# Google Cloud NSI and DSR — Terminology Explainer

This short companion to the Palo Alto Networks firewalling in GCP guide defines two terms that appear repeatedly in the Network Security Integration packet-flow sections.

Related guide: [Palo Alto Networks Firewalling in Google Cloud — Cloud NGFW Enterprise Integration vs VM-Series Service Insertion](09-07-26-07-03_Palo_Alto_Networks_Firewalling_in_GCP_Deep_Dive.md)

## NSI — Network Security Integration

**NSI** stands for **Network Security Integration**. It is a Google Cloud service that lets a VPC send selected traffic to third-party network security appliance VMs, such as Palo Alto Networks VM-Series, without changing the consumer VPC's ordinary routes merely to insert the appliance.

Google Cloud NSI supports two broad integration models:

- **In-band integration** — selected packets are intercepted and sent to the security appliance. The appliance can allow or drop the traffic before it reaches the original destination.
- **Out-of-band integration** — a copy of traffic is sent to an analysis appliance while the original traffic continues independently.

The VM-Series design in the main guide uses **NSI in-band integration**.

### What NSI does in the packet path

For an in-band flow, think of NSI as the Google-managed service-insertion fabric between a **consumer VPC** and a **producer VPC**:

```text
Consumer workload
    |
    | ordinary packet
    v
Google firewall-policy selection
    |
    | APPLY_SECURITY_PROFILE_GROUP
    v
NSI
    |
    | GENEVE / UDP 6081
    v
Producer internal passthrough ILB
    |
    v
VM-Series
    |
    | allow or drop
    v
NSI reinjection for allowed traffic
    |
    v
Original consumer forwarding path
```

The consumer firewall policy decides which traffic is intercepted. NSI then uses the endpoint/deployment object chain to locate the correct producer service and zonal deployment.

The important distinction is:

```text
NSI is not the firewall.
NSI is not the ILB.
NSI is not PAN-OS.

NSI is the Google-managed interception, encapsulation,
service-selection, and reinjection mechanism that connects them.
```

### NSI producer and consumer roles

**Producer:** owns the inspection service, including the VM-Series appliances, internal passthrough Network Load Balancer, intercept deployment group, and zonal intercept deployments.

**Consumer:** owns the workloads and selects the producer service through an intercept endpoint group, endpoint-group association, custom-intercept security profile, security profile group, and firewall-policy rule.

Conceptually:

```text
CONSUMER                                           PRODUCER

Workload
  |
Firewall policy
  |
Security profile group
  |
Custom-intercept profile
  |
Intercept endpoint group  --------------------->  Intercept deployment group
                                                     |
                                                     v
                                              Zonal intercept deployment
                                                     |
                                                     v
                                              Internal forwarding rule
                                                     |
                                                     v
                                              VM-Series appliances
```

## DSR — Direct Server Return

**DSR** stands for **Direct Server Return**.

In traditional load-balancing terminology, DSR means that a selected backend returns traffic directly toward the client rather than sending the response back through the load balancer first.

Google Cloud NSI uses the same idea for **packet reinjection**.

### Why DSR matters in NSI

The inspection-delivery path is:

```text
Consumer
  -> NSI
  -> producer internal passthrough ILB
  -> VM-Series
```

The ILB is needed on this leg because Google must select a healthy inspection backend.

After PAN-OS permits the packet, VM-Series does **not** send that allowed packet back to the ILB. Instead, the appliance re-encapsulates the packet in GENEVE using the required NSI metadata and sends it directly back toward Google's NSI consumer-side reinjection path.

```text
VM-Series
  -> DSR
  -> Google NSI reinjection
  -> consumer VPC forwarding
```

Not:

```text
VM-Series
  -> producer ILB
  -> NSI
  -> consumer
```

### Forward versus reinjection path

```text
INSPECTION DELIVERY

Consumer packet
    |
    v
NSI
    |
    v
Producer ILB
    |
    v
VM-Series


ALLOW / REINJECTION

VM-Series
    |
    | GENEVE packet using NSI metadata
    | DSR — bypass producer ILB
    v
Google NSI
    |
    v
Original consumer forwarding path
```

### What remains unchanged

For standard in-band reinjection, the appliance re-encapsulates the **original packet**. Google documents that the appliance preserves the original packet's IP addresses, protocol, and ports while using the GENEVE metadata required for reinjection.

So, for example, if VM-Series receives this inner packet:

```text
10.10.1.10:51514 -> 198.51.100.25:443
```

an allow verdict does not mean the appliance changes that inner tuple merely because DSR is used. The packet is re-encapsulated and returned to NSI for continued delivery according to the selected deployment model.

## NSI + DSR together

The easiest mental model is:

```text
NSI = the Google-managed traffic interception and reinjection framework.

DSR = the way the producer appliance returns an allowed
      GENEVE packet directly into that reinjection framework
      without hairpinning through the producer ILB.
```

Or, as one packet walk:

```text
1. Workload emits packet.
2. Google firewall policy selects the packet for NSI.
3. NSI encapsulates it with GENEVE.
4. Producer ILB selects a healthy VM-Series backend.
5. PAN-OS inspects the original packet.
6. PAN-OS allows it.
7. VM-Series re-encapsulates the original packet.
8. VM-Series uses DSR to return it directly toward NSI.
9. NSI reinjects it into the consumer's original forwarding path.
```

## Sources

- https://docs.cloud.google.com/network-security-integration/docs/nsi-overview
- https://docs.cloud.google.com/network-security-integration/docs/in-band/in-band-integration-overview
- https://docs.cloud.google.com/network-security-integration/docs/understand-geneve
