from pathlib import Path

p = Path('09-07-26-07-03_Palo_Alto_Networks_Firewalling_in_GCP_Deep_Dive.md')
s = p.read_text()

old = '''## 7.8 Internet ingress — Internet to published workload

The untrust side is different from the trust-side ILB next-hop mechanism.

Palo Alto notes that Google Cloud external load balancers deliver traffic to the VM's primary interface. VM-Series designs therefore require correct NIC ordering and often management-interface swap so the intended untrust dataplane interface is primary.

A conceptual inbound flow is:

```text
Internet client
 -> external passthrough / supported external LB
 -> VM-Series untrust
 -> PAN-OS DNAT/security inspection if used
 -> trust-side route
 -> application workload
```

Return:

```text
application workload
 -> trust-side route/PBR/ILB as required
 -> same logical VM-Series state owner
 -> reverse DNAT/SNAT
 -> external Internet path
 -> client
```

If the workload's return route points directly to another Internet gateway and bypasses the firewall that owns the NAT/session state, the connection can fail even though the inbound SYN reached the application.
'''

new = '''## 7.8 Internet ingress — Internet to published workload

The untrust side is different from the trust-side ILB next-hop mechanism. Palo Alto documents a concrete north-south design in which a **Google Cloud external passthrough Network Load Balancer** distributes Internet traffic to the VM-Series **untrust** interfaces, and PAN-OS then performs destination NAT (DNAT), Security/App-ID/Threat inspection, and routing toward the private application.

Palo Alto also documents that Google external load balancers deliver traffic to a VM's **primary interface**. In the traditional multi-interface VM-Series design, plan NIC ordering and the management-interface swap so the intended untrust dataplane interface is NIC0/primary and can receive the external load-balancer traffic.

For active/passive VM-Series HA, Palo Alto specifically requires an **external passthrough load balancer** for Internet inbound and outbound because that load-balancer type provides the connection-tracking behavior used by the HA design.

### 7.8.1 Concrete Internet-ingress example

Use the following documented-style example:

```text
Internet client:             203.0.113.50:51514
External LB forwarding VIP:  34.172.143.223:80
VM-Series untrust:            NIC0 / primary dataplane interface
Published application:        10.0.2.4:80
Trust VPC:                    private workload network
```

![GCP Internet ingress through VM-Series](images/09-08-26_pan_gcp_internet_ingress_ext_passthrough_lb.svg)

[Editable draw.io](images/09-08-26_pan_gcp_internet_ingress_ext_passthrough_lb.drawio)

**What this image shows:** Internet traffic enters through an external passthrough NLB forwarding-rule VIP, reaches the active VM-Series untrust interface, is inspected and DNATed by PAN-OS, and is then routed to the private workload. The dashed lower path is the stateful return flow.

**What matters:** the public forwarding-rule address is the address the client connects to and the address PAN-OS matches in the original-packet side of the DNAT rule. The external passthrough load balancer does not replace PAN-OS NAT or Security policy.

**What to verify:** the forwarding rule points to the VM-Series external backend service, the active firewall is healthy, the untrust interface is the load-balancer-facing primary dataplane NIC, PAN-OS DNAT matches the public VIP, the Security rule allows the translated flow, PAN-OS has a route to the private application, and the return flow comes back through the same logical state owner.

### 7.8.2 Create the private application

Palo Alto's active/passive tutorial uses a private application VM in the trust VPC. The documented example creates a VM without an external IP and records its internal address:

```cli
gcloud compute instances create my-app2 \\
  --network-interface subnet="panw-us-central1-trust",no-address \\
  --zone=us-central1-a \\
  --image-project=panw-gcp-team-testing \\
  --image=ubuntu-2004-lts-apache-ac \\
  --machine-type=f1-micro
```

The Palo Alto example shows the resulting application address as:

```text
INTERNAL_IP: 10.0.2.4
EXTERNAL_IP:
status: RUNNING
```

The important design point is that the application itself does **not** need a public IP. Internet publication is owned by the external load-balancer forwarding rule and the VM-Series DNAT policy.

### 7.8.3 Create an Internet-facing forwarding rule for the application

Assume the external passthrough load balancer backend service already exists and uses the VM-Series untrust interfaces as its backends. Palo Alto's documented active/passive onboarding example creates an additional forwarding rule for the application:

```cli
gcloud compute forwarding-rules create panw-vmseries-extlb-rule2 \\
  --load-balancing-scheme=EXTERNAL \\
  --region=us-central1 \\
  --ip-protocol=L3_DEFAULT \\
  --ports=ALL \\
  --backend-service=panw-vmseries-extlb
```

Retrieve the public forwarding-rule address:

```cli
gcloud compute forwarding-rules describe panw-vmseries-extlb-rule2 \\
  --region=us-central1 \\
  --format='get(IPAddress)'
```

Palo Alto's example output is:

```text
34.172.143.223
```

That address becomes the Internet-facing identity for the published application in this example.

**Success criteria:**

- the forwarding rule is regional and external;
- its backend service is the VM-Series external/untrust backend service;
- the intended active VM-Series backend is healthy;
- the public VIP is recorded for the PAN-OS NAT rule and client testing.

### 7.8.4 Configure PAN-OS DNAT and Security policy

Palo Alto documents the following GUI workflow on the active VM-Series firewall:

1. Go to **Policies > NAT > Add**.
2. In **Original Packet**, configure:
   - **Source Zone:** `untrust`
   - **Destination Zone:** `untrust`
   - **Service:** `service-http`
   - **Destination Address:** `34.172.143.223` — the external forwarding-rule VIP.
3. In **Translated Packet**, configure destination translation:
   - **Translated Type:** `Static IP`
   - **Translated Address:** `10.0.2.4` — the private application address.
4. Commit the NAT policy.
5. Create/verify the corresponding **Security policy** that permits the intended inbound application traffic and attaches the required App-ID/content-security profiles.
6. Commit the Security policy.

The NAT transformation is therefore:

```text
Before PAN-OS DNAT:
203.0.113.50:51514 -> 34.172.143.223:80

After PAN-OS DNAT:
203.0.113.50:51514 -> 10.0.2.4:80
```

The original client source address is preserved in the passthrough-NLB model, which is useful for PAN-OS policy and logging. PAN-OS owns the DNAT/session state that maps the public forwarding-rule address to the private application.

### 7.8.5 Forward packet walk — Internet client to private workload

1. The client sends a TCP SYN to `34.172.143.223:80`.
2. The Google Cloud external passthrough NLB forwarding rule matches the public VIP and protocol/port.
3. The external backend service selects the healthy VM-Series backend. In active/passive, the active firewall is the backend whose dataplane health check succeeds.
4. The packet reaches the VM-Series **untrust NIC0** with the original client source address preserved.
5. PAN-OS performs session setup, NAT policy lookup, Security policy lookup, App-ID/content inspection as configured, and routing.
6. The DNAT rule matches destination `34.172.143.223` and translates it to `10.0.2.4`.
7. PAN-OS routes the translated packet out the trust dataplane toward the application.
8. The packet re-enters the Google VPC dataplane on the trust side.
9. Normal trust-VPC routing delivers the packet to `10.0.2.4:80`.

The forward path is:

```text
203.0.113.50:51514
        |
        v
34.172.143.223:80
external passthrough NLB
        |
        v
VM-Series untrust NIC0
        |
        | PAN-OS DNAT
        | 34.172.143.223 -> 10.0.2.4
        v
VM-Series trust
        |
        v
10.0.2.4:80
```

### 7.8.6 Return packet walk — private workload back to Internet client

The response must return through the VM-Series stateful path. A typical traditional design uses the trust-side routing/PBR/internal-ILB mechanisms described in Sections 7.3 and 7.7 so workload Internet-bound traffic returns to VM-Series instead of bypassing it.

1. `10.0.2.4:80` sends the response toward `203.0.113.50:51514`.
2. The workload's effective route/steering sends the response toward the VM-Series trust-side service.
3. The same logical PAN-OS state owner receives the response.
4. PAN-OS finds the established session.
5. PAN-OS performs reverse DNAT, restoring the public source identity associated with the original inbound connection.
6. The response is inspected according to the existing stateful session.
7. PAN-OS routes the packet out untrust.
8. The external passthrough load-balancer/forwarding path returns the flow to the Internet client.

Conceptually:

```text
Before reverse NAT:
10.0.2.4:80 -> 203.0.113.50:51514

After PAN-OS reverse NAT:
34.172.143.223:80 -> 203.0.113.50:51514
```

If the application's return route sends the packet directly to another Internet path and bypasses VM-Series, PAN-OS never gets the response needed for reverse NAT/session processing. The inbound SYN can reach the application while the TCP connection still fails.

### 7.8.7 Test and verify the published application

Palo Alto's documented test is to access the application through the forwarding-rule address:

```text
http://34.172.143.223/
```

Verify the Google-side objects:

```cli
gcloud compute forwarding-rules describe panw-vmseries-extlb-rule2 \\
  --region=us-central1 \\
  --format='yaml(name,IPAddress,IPProtocol,allPorts,backendService,loadBalancingScheme)'
```

Verify the external backend service health using the actual backend-service name and region:

```cli
gcloud compute backend-services get-health panw-vmseries-extlb \\
  --region=us-central1
```

On PAN-OS, verify the session and dataplane state with the appropriate filters for the real client/application tuple, for example:

```cli
show session all filter destination 10.0.2.4
show routing route
show counter global filter severity drop delta yes
```

Also use **Monitor > Traffic** and confirm:

- source IP is the real Internet client for the passthrough-LB flow;
- destination/NAT fields show the expected public-to-private translation;
- the intended Security rule is hit;
- the session has traffic in both directions;
- the session end reason is normal rather than aged-out or policy-denied.

### 7.8.8 Active/passive HA behavior and caveats

Palo Alto's active/passive GCP model puts each firewall in an unmanaged instance group and uses load-balancer health checks to identify the active dataplane. The passive firewall does not normally pass the dataplane health check until it becomes active.

For this model:

- the external passthrough load balancer is required for Internet inbound/outbound because Palo Alto relies on its connection-tracking behavior;
- HA synchronization maintains PAN-OS configuration/state between the peers according to the supported Palo Alto HA design;
- after failover, the newly active firewall begins passing the dataplane health check and becomes eligible for traffic;
- do not assume that an arbitrary external proxy load balancer has the same client-IP preservation or failover semantics as the documented external passthrough design;
- the external forwarding rule places the packet on **untrust**; it does not replace PAN-OS DNAT, Security policy, routing, or return-path design.

**Source information:** Palo Alto Networks documents Internet inbound through external load balancers to VM-Series untrust interfaces, the primary-interface requirement, active/passive use of an external passthrough load balancer, application onboarding with an `L3_DEFAULT`/`ALL` forwarding rule, DNAT from forwarding-rule VIP `34.172.143.223` to private application `10.0.2.4`, and validation by accessing the public forwarding-rule address.

**Additional explanation:** The external passthrough NLB is the Internet-facing distribution/HA layer. PAN-OS remains the stateful firewall, NAT owner, routing decision point, and inspection engine.

**Reasonable inference:** Treat ingress as two coupled routing stages: Google chooses the VM-Series untrust backend first; after PAN-OS DNAT and inspection, the firewall's trust-side route plus normal VPC routing delivers the translated packet to the private application.
'''

if old not in s:
    raise SystemExit('Expected Section 7.8 block not found')

s = s.replace(old, new, 1)

toc_old = '- [7.8 Internet ingress — Internet to published workload](#78-internet-ingress--internet-to-published-workload)\n'
toc_new = toc_old + '''  - [7.8.1 Concrete Internet-ingress example](#781-concrete-internet-ingress-example)\n  - [7.8.2 Create the private application](#782-create-the-private-application)\n  - [7.8.3 Create an Internet-facing forwarding rule for the application](#783-create-an-internet-facing-forwarding-rule-for-the-application)\n  - [7.8.4 Configure PAN-OS DNAT and Security policy](#784-configure-pan-os-dnat-and-security-policy)\n  - [7.8.5 Forward packet walk — Internet client to private workload](#785-forward-packet-walk--internet-client-to-private-workload)\n  - [7.8.6 Return packet walk — private workload back to Internet client](#786-return-packet-walk--private-workload-back-to-internet-client)\n  - [7.8.7 Test and verify the published application](#787-test-and-verify-the-published-application)\n  - [7.8.8 Active/passive HA behavior and caveats](#788-activepassive-ha-behavior-and-caveats)\n'''
if toc_old not in s:
    raise SystemExit('TOC Section 7.8 entry not found')
s = s.replace(toc_old, toc_new, 1)

p.write_text(s)
