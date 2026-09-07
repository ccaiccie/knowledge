# Palo Alto Networks Firewalling in Google Cloud — Cloud NGFW Enterprise Integration vs VM-Series Service Insertion

## Purpose

This guide separates three concepts that are easy to conflate:

1. **Google Cloud NGFW Enterprise** — a Google-managed firewall service whose advanced threat prevention is powered by Palo Alto Networks technology.
2. **Palo Alto Networks VM-Series on Google Cloud** — PAN-OS firewalls that you deploy and operate as Compute Engine virtual machines.
3. **Google Cloud Network Security Integration (NSI) with VM-Series** — Google-managed packet interception that can transparently deliver selected packets to VM-Series over **GENEVE (Generic Network Virtualization Encapsulation)** without changing the consumer VPC's normal routes.

> **Important correction:** Palo Alto Networks currently documents its standalone managed **Cloud NGFW** product family for AWS and Azure. Do not model a separate product called “Palo Alto Cloud NGFW for Google Cloud.” In GCP, the Palo Alto paths are Google Cloud NGFW Enterprise using Palo Alto threat-prevention technology, or customer-deployed Palo Alto products such as VM-Series.

---

## Source URLs

### Palo Alto Networks
- https://docs.paloaltonetworks.com/ngfw
- https://docs.paloaltonetworks.com/vm-series
- https://docs.paloaltonetworks.com/vm-series/deployment/public-cloud/set-up-the-vm-series-firewall-on-google-cloud-platform/securing-vpc-with-vm-on-gcp
- https://docs.paloaltonetworks.com/vm-series/deployment/public-cloud/set-up-the-vm-series-firewall-on-google-cloud-platform/deployment-models-for-vm-series-on-gcp
- https://docs.paloaltonetworks.com/vm-series/deployment/public-cloud/set-up-the-vm-series-firewall-on-google-cloud-platform/configuring-gcp-load-balancer
- https://docs.paloaltonetworks.com/vm-series/deployment/public-cloud/set-up-the-vm-series-firewall-on-google-cloud-platform/google-cloud-network-security-integration-nsi-with-vm-series-firewall
- https://docs.paloaltonetworks.com/vm-series/deployment/public-cloud/set-up-the-vm-series-firewall-on-google-cloud-platform/configure-gcp-nsi-overlay-support
- https://docs.paloaltonetworks.com/vm-series/deployment/public-cloud/set-up-the-vm-series-firewall-on-google-cloud-platform/deployment-models-for-vm-series-on-gcp/active-passive-model
- https://docs.paloaltonetworks.com/vm-series/getting-started/vm-series-on-google-performance-and-capacity/vm-series-on-google-cloud-platform-supported-gcp-instance-types

### Google Cloud
- https://cloud.google.com/security/products/firewall
- https://cloud.google.com/blog/products/identity-security/announcing-next-gen-firewall-enterprise-now-in-ga-next24
- https://docs.cloud.google.com/firewall/docs/about-intrusion-prevention
- https://docs.cloud.google.com/network-security-integration/docs/nsi-overview
- https://docs.cloud.google.com/network-security-integration/docs/understand-geneve
- https://docs.cloud.google.com/network-security-integration/docs/in-band/in-band-integration-overview
- https://docs.cloud.google.com/network-security-integration/docs/in-band/firewall-policies-overview
- https://docs.cloud.google.com/network-security-integration/docs/in-band/in-band-integration-tutorial
- https://docs.cloud.google.com/network-security-integration/docs/in-band/configure-intercept-deployments
- https://docs.cloud.google.com/network-security-integration/docs/in-band/configure-intercept-endpoint-groups
- https://docs.cloud.google.com/network-security-integration/docs/in-band/configure-endpoint-group-associations
- https://docs.cloud.google.com/network-security-integration/docs/in-band/configure-security-profiles
- https://docs.cloud.google.com/network-security-integration/docs/in-band/configure-security-profile-groups
- https://docs.cloud.google.com/network-security-integration/docs/in-band/configure-firewall-rules
- https://docs.cloud.google.com/network-security-integration/docs/in-band/configure-consumer-service
- https://docs.cloud.google.com/network-security-integration/docs/release-notes
- https://docs.cloud.google.com/vpc/docs/policy-based-routes
- https://docs.cloud.google.com/vpc/docs/use-policy-based-routes
- https://docs.cloud.google.com/sdk/gcloud/reference/network-connectivity/policy-based-routes/create
- https://docs.cloud.google.com/load-balancing/docs/internal/ilb-next-hop-overview
- https://docs.cloud.google.com/load-balancing/docs/internal/setting-up-ilb-next-hop
- https://cloud.google.com/blog/products/networking/policy-based-routing-network-patterns-for-virtual-appliances

---

# 1. Product boundary

![Product boundary](images/09-07-26-07-03_pan_gcp_product_boundary.svg)

[Editable draw.io](images/09-07-26-07-03_pan_gcp_product_boundary.drawio)

**What this image shows:** Google Cloud NGFW Enterprise, VM-Series, and NSI + VM-Series are related but distinct architectures.

**What matters:** Google owns the Cloud NGFW service; VM-Series is PAN-OS running on Compute Engine; NSI is the Google service-insertion fabric that can deliver traffic to VM-Series.

**What to verify:** Decide which control plane owns policy and where the firewall session state lives before designing routing.

## 1.1 Google Cloud NGFW Enterprise

**Source information:** Google describes Cloud NGFW as a distributed, stateful firewall embedded in the Google Cloud networking fabric. Its advanced intrusion-prevention capabilities are powered by Palo Alto Networks threat-prevention technology.

**Additional explanation:** This does not mean a PAN-OS VM is hidden in your project. You configure Google firewall policies, security profiles, firewall endpoints, and TLS inspection resources with Google APIs and IAM. Google operates the inspection data plane.

Use it when you want Google-managed lifecycle, native distributed L3/L4 enforcement, managed L7 threat prevention, and no customer-managed firewall fleet.

## 1.2 VM-Series on GCP

VM-Series is Palo Alto Networks' virtualized NGFW. It runs PAN-OS and exposes the familiar Palo Alto constructs: zones, virtual routers, Security policy, App-ID, NAT policy, logging, and licensed cloud-delivered security services. It can be centrally managed with Panorama and supported Strata management workflows.

Use VM-Series when you require PAN-OS policy semantics or operational consistency with Palo Alto firewalls elsewhere.

## 1.3 Correct product mapping

| Requirement | Correct design |
|---|---|
| Native Google distributed firewall with PAN threat prevention | Google Cloud NGFW Enterprise |
| PAN-OS firewall in GCP | VM-Series |
| Transparent interception into PAN-OS firewall VMs | VM-Series + NSI |
| Explicit routed service chain | VM-Series + internal passthrough NLB + PBR/custom routes |

---

# 2. VM-Series deployment models in GCP

Palo Alto documents multiple GCP architectures. Two are especially important for service insertion.

## 2.1 Modern model — VM-Series + Network Security Integration

NSI divides the design into a **producer** and a **consumer**.

The producer side contains the VM-Series inspection service: producer VPC, VM-Series instances, an internal passthrough Network Load Balancer (ILB), a global intercept deployment group, and one or more zonal intercept deployments that reference ILB forwarding rules.

The consumer side contains application workloads, an intercept endpoint group, endpoint-group association, custom-intercept security profile, security profile group, and a global network or hierarchical firewall policy rule using `apply_security_profile_group`.

## 2.2 Traditional model — internal passthrough LB + PBR/custom routes

Palo Alto's classic multi-interface architecture attaches VM-Series dataplane NICs to workload/trust/untrust networks. Internal passthrough Network Load Balancers front firewall interfaces, while custom static routes or **Policy-Based Routes (PBRs)** steer traffic to the load balancer.

Unlike NSI, this is a true **routed service chain**. Google sends the packet to a VM-Series dataplane interface as the next hop, PAN-OS makes a routing/security/NAT decision, and the packet re-enters the Google VPC data plane after the firewall forwards it.

---

# 3. NSI architecture and packet flow

![NSI packet flow](images/09-07-26-07-03_pan_gcp_nsi_packet_flow.svg)

[Editable draw.io](images/09-07-26-07-03_pan_gcp_nsi_packet_flow.drawio)

**What this image shows:** A consumer firewall policy selects a flow and resolves it through a custom-intercept profile and endpoint group to a producer-side ILB and VM-Series service.

**What matters:** The consumer VPC's normal route does not point to the firewall. NSI is invoked by firewall-policy action, not by an ordinary route next hop.

**What to verify:** endpoint group association, security profile group reference, zonal intercept deployment state, ILB health, GENEVE enablement on VM-Series, and successful reinjection.

## 3.1 GENEVE packet model

NSI in-band interception encapsulates the original packet in GENEVE and adds Google-specific metadata. Conceptually:

```text
Outer inspection transport
+----------------------------------------------------------+
| Outer IP | UDP | GENEVE | Google metadata | Inner packet|
+----------------------------------------------------------+

Inner packet example:
10.10.1.10:51514 -> 10.10.2.20:443 TCP
```

The VM-Series inspects the inner packet, not merely the GENEVE outer transport.

## 3.2 Enable GENEVE inspection on VM-Series

Palo Alto documents:

```cli
request plugins vm_series geneve-inspect enable yes
```

A reboot is required when enabling this feature. Bootstrap can also include:

```text
geneve-inspect=enable
```

Verify VM interface mapping with:

```cli
debug show vm-series interfaces all
```

---

# 4. End-to-end NSI build with gcloud

Example objects:

| Item | Example |
|---|---|
| Producer project | `pan-sec-prod` |
| Consumer project | `app-prod-1` |
| Region / zone | `us-central1` / `us-central1-a` |
| Producer VPC | `pan-inspection-vpc` |
| Consumer VPC | `app-vpc` |
| Deployment group | `pan-idg` |
| Zonal deployment | `pan-id-uscentral1a` |
| Endpoint group | `pan-ieg` |
| Security profile | `pan-custom-intercept` |
| Security profile group | `pan-spg` |
| Firewall policy | `pan-nsi-policy` |

## 4.1 Enable APIs

```cli
gcloud services enable compute.googleapis.com networksecurity.googleapis.com --project=pan-sec-prod
gcloud services enable compute.googleapis.com networksecurity.googleapis.com --project=app-prod-1
```

## 4.2 Create producer VPC

```cli
gcloud compute networks create pan-inspection-vpc \
  --project=pan-sec-prod \
  --subnet-mode=custom

gcloud compute networks subnets create pan-inspection-uscentral1 \
  --project=pan-sec-prod \
  --network=pan-inspection-vpc \
  --region=us-central1 \
  --range=10.250.10.0/24
```

Deploy supported VM-Series instances, license them, and configure the needed PAN-OS interfaces, zones, virtual router, Security policy, and management before putting them behind the producer ILB.

## 4.3 Build the producer internal passthrough Network Load Balancer

The producer-side load balancer is not just a backend service. For NSI in-band inspection, the complete chain is:

```text
NSI intercept deployment
        |
        v
regional internal forwarding rule
UDP/6081 on pan-inspection-vpc
        |
        v
regional INTERNAL backend service
protocol UDP
        |
        v
zonal VM-Series instance group(s)
        |
        v
VM-Series GENEVE inspection
```

The forwarding rule is especially important because **the zonal NSI intercept deployment references this forwarding rule directly**. Google sends intercepted traffic to the forwarding rule as GENEVE over UDP port `6081`.

### 4.3.1 Create the regional health check

The load balancer needs a health check that proves a VM-Series backend is available before Google selects it. This example uses TCP port `80`, matching Google's NSI in-band tutorial. The appliance must actually answer the configured health-check port; change the port if your VM-Series deployment uses a different supported health-monitoring method.

```cli
gcloud compute health-checks create tcp pan-nsi-hc \
  --project=pan-sec-prod \
  --region=us-central1 \
  --port=80
```

### 4.3.2 Create the regional UDP backend service

For NSI in-band GENEVE delivery, Google's documented producer backend service uses protocol `UDP` and load-balancing scheme `INTERNAL`.

```cli
gcloud compute backend-services create pan-nsi-ilb-bs \
  --project=pan-sec-prod \
  --region=us-central1 \
  --protocol=UDP \
  --health-checks=pan-nsi-hc \
  --health-checks-region=us-central1 \
  --load-balancing-scheme=INTERNAL
```

This corrects the earlier `UNSPECIFIED` example. The backend service is the regional load-balancing object that owns backend membership and health state; it is **not** the ILB frontend/VIP by itself.

### 4.3.3 Put the VM-Series appliances in an instance group

NSI's internal passthrough load balancer uses instance-group backends. If the VM-Series instances are already in a supported managed or unmanaged zonal instance group, reuse that group. For an unmanaged group, a simplified example is:

```cli
gcloud compute instance-groups unmanaged create pan-nsi-fw-ig-a \
  --project=pan-sec-prod \
  --zone=us-central1-a

gcloud compute instance-groups unmanaged add-instances pan-nsi-fw-ig-a \
  --project=pan-sec-prod \
  --zone=us-central1-a \
  --instances=pan-fw-a1
```

For production, add only interfaces/instances appropriate for the Palo Alto NSI architecture and use the vendor-supported HA or scaling model rather than treating the preceding single-instance example as an HA design.

### 4.3.4 Attach the instance group to the backend service

```cli
gcloud compute backend-services add-backend pan-nsi-ilb-bs \
  --project=pan-sec-prod \
  --region=us-central1 \
  --instance-group=pan-nsi-fw-ig-a \
  --instance-group-zone=us-central1-a
```

If you deploy inspection capacity in more than one zone, add the corresponding zonal instance groups as additional backends where the documented NSI/load-balancer design supports them.

### 4.3.5 Create the actual internal passthrough ILB frontend

Now create the **regional internal forwarding rule**. This creates the ILB frontend IP and maps UDP/6081 to `pan-nsi-ilb-bs`.

```cli
gcloud compute forwarding-rules create pan-nsi-ilb-fr \
  --project=pan-sec-prod \
  --backend-service=pan-nsi-ilb-bs \
  --region=us-central1 \
  --network=pan-inspection-vpc \
  --subnet=pan-inspection-uscentral1 \
  --ip-protocol=UDP \
  --load-balancing-scheme=INTERNAL \
  --ports=6081
```

At this point the forwarding rule is the actual ILB frontend used by NSI. Unless you explicitly reserve and specify an internal address, Google assigns an available frontend address from the selected subnet.

Retrieve it:

```cli
ILB_IP=$(gcloud compute forwarding-rules describe pan-nsi-ilb-fr \
  --project=pan-sec-prod \
  --region=us-central1 \
  --format='get(IPAddress)')

echo "$ILB_IP"
```

Also obtain the producer subnet gateway address:

```cli
GW_IP=$(gcloud compute networks subnets describe pan-inspection-uscentral1 \
  --project=pan-sec-prod \
  --region=us-central1 \
  --format='get(gatewayAddress)')

echo "$GW_IP"
```

### 4.3.6 Allow GENEVE and health-check traffic to the VM-Series backends

```cli
gcloud compute network-firewall-policies create pan-producer-fw-policy \
  --project=pan-sec-prod \
  --global

gcloud compute network-firewall-policies associations create \
  --project=pan-sec-prod \
  --name=pan-producer-fw-policy-assoc \
  --firewall-policy=pan-producer-fw-policy \
  --global-firewall-policy \
  --network=pan-inspection-vpc

gcloud compute network-firewall-policies rules create 100 \
  --project=pan-sec-prod \
  --firewall-policy=pan-producer-fw-policy \
  --global-firewall-policy \
  --action=allow \
  --direction=INGRESS \
  --layer4-configs=udp:6081 \
  --src-ip-ranges=${GW_IP}/32

gcloud compute network-firewall-policies rules create 101 \
  --project=pan-sec-prod \
  --firewall-policy=pan-producer-fw-policy \
  --global-firewall-policy \
  --action=allow \
  --direction=INGRESS \
  --layer4-configs=tcp:80 \
  --src-ip-ranges=35.191.0.0/16,130.211.0.0/22
```

These GCP firewall-policy rules only permit the transport to reach the producer appliances. PAN-OS still needs the correct interface mapping, GENEVE inspection state, Security policy, and vendor-required service configuration.

### 4.3.7 Verify the complete ILB, not only the backend service

```cli
gcloud compute backend-services describe pan-nsi-ilb-bs \
  --project=pan-sec-prod \
  --region=us-central1

gcloud compute backend-services get-health pan-nsi-ilb-bs \
  --project=pan-sec-prod \
  --region=us-central1

gcloud compute forwarding-rules describe pan-nsi-ilb-fr \
  --project=pan-sec-prod \
  --region=us-central1 \
  --format='yaml(name,IPAddress,IPProtocol,ports,backendService,loadBalancingScheme,network,subnetwork)'
```

**Success criteria:**

- intended instance group is attached and healthy;
- `IPProtocol` is UDP;
- port `6081` is present;
- `loadBalancingScheme` is `INTERNAL`;
- the forwarding rule points to `pan-nsi-ilb-bs` and has an internal IP.

## 4.4–4.7 Tie the producer service to the consumer VPC

![NSI producer-consumer object chain](images/09-07-26-07-03_nsi_producer_consumer_object_chain.svg)

[Editable draw.io](images/09-07-26-07-03_nsi_producer_consumer_object_chain.drawio)

**What this image shows:** The consumer-side policy objects ultimately point to a producer-side **intercept deployment group**. That global producer object owns one or more **zonal intercept deployments**, and each zonal deployment references the internal forwarding rule that fronts the VM-Series service.

**What matters:** The consumer never points directly to `pan-nsi-ilb-fr`. The stable cross-project contract is the **intercept deployment group**. The consumer creates its own **intercept endpoint group** as a pointer to that producer service, and an **endpoint-group association** binds that pointer to the actual consumer VPC.

**What to verify:**

```text
Consumer firewall rule
  -> security profile group
  -> custom-intercept profile
  -> intercept endpoint group (pan-ieg)
  -> producer intercept deployment group (pan-idg)
  -> selected zonal intercept deployment (pan-id-uscentral1a)
  -> producer forwarding rule (pan-nsi-ilb-fr)
  -> backend service
  -> healthy VM-Series
```

### 4.4 Create the producer intercept deployment group — the global service umbrella

The **intercept deployment group** is the producer's global logical representation of the inspection service. It has no data-plane IP of its own. It groups zonal deployments and gives consumers one stable producer object to reference.

```cli
gcloud network-security intercept-deployment-groups create pan-idg \
  --project=pan-sec-prod \
  --location=global \
  --network=projects/pan-sec-prod/global/networks/pan-inspection-vpc \
  --no-async
```

Conceptually:

```text
Producer project: pan-sec-prod
Producer VPC:     pan-inspection-vpc
Global NSI offer: pan-idg
Actual packet entry point: supplied by zonal intercept deployments
```

Verify:

```cli
gcloud network-security intercept-deployment-groups describe pan-idg \
  --project=pan-sec-prod \
  --location=global
```

### 4.5 Create the zonal intercept deployment — map one zone to one producer ILB frontend

```cli
gcloud network-security intercept-deployments create pan-id-uscentral1a \
  --project=pan-sec-prod \
  --location=us-central1-a \
  --forwarding-rule=pan-nsi-ilb-fr \
  --forwarding-rule-location=us-central1 \
  --intercept-deployment-group=projects/pan-sec-prod/locations/global/interceptDeploymentGroups/pan-idg \
  --no-async
```

This creates:

```text
pan-idg
  -> pan-id-uscentral1a
       -> pan-nsi-ilb-fr
            -> pan-nsi-ilb-bs
                 -> VM-Series backends
```

Verify:

```cli
gcloud network-security intercept-deployments describe pan-id-uscentral1a \
  --project=pan-sec-prod \
  --location=us-central1-a
```

### 4.6 Create the consumer intercept endpoint group — consumer-side pointer to the producer service

```cli
gcloud network-security intercept-endpoint-groups create pan-ieg \
  --project=app-prod-1 \
  --location=global \
  --intercept-deployment-group=projects/pan-sec-prod/locations/global/interceptDeploymentGroups/pan-idg \
  --no-async
```

Conceptually:

```text
CONSUMER                                   PRODUCER
pan-ieg  --------------------------------> pan-idg
(endpoint group)                           (deployment group)
```

### 4.7 Associate the endpoint group with the consumer VPC

```cli
gcloud network-security intercept-endpoint-group-associations create pan-ieg-app-vpc \
  --project=app-prod-1 \
  --location=global \
  --intercept-endpoint-group=projects/app-prod-1/locations/global/interceptEndpointGroups/pan-ieg \
  --network=app-vpc \
  --no-async
```

| Object | Question it answers |
|---|---|
| `pan-ieg` | Which producer inspection service do I want to consume? |
| `pan-ieg-app-vpc` | Which consumer VPC is bound to that service? |

After Step 4.7:

```text
app-vpc
  -> pan-ieg-app-vpc association
  -> pan-ieg endpoint group
  -> pan-idg deployment group
  -> pan-id-uscentral1a zonal deployment
  -> pan-nsi-ilb-fr
  -> pan-nsi-ilb-bs
  -> VM-Series
```

But **no workload flow is intercepted merely because these objects exist**. Steps 4.8–4.12 add the policy-selection layer.

## 4.8 Create custom-intercept security profile

```cli
gcloud network-security security-profiles custom-intercept create pan-custom-intercept \
  --organization=ORG_ID \
  --location=global \
  --billing-project=app-prod-1 \
  --intercept-endpoint-group=projects/app-prod-1/locations/global/interceptEndpointGroups/pan-ieg \
  --no-async
```

## 4.9 Create security profile group

```cli
gcloud network-security security-profile-groups create pan-spg \
  --organization=ORG_ID \
  --location=global \
  --custom-intercept-profile=pan-custom-intercept \
  --billing-project=app-prod-1 \
  --no-async
```

## 4.10 Create global network firewall policy

```cli
gcloud compute network-firewall-policies create pan-nsi-policy \
  --project=app-prod-1
```

## 4.11 Create interception rule

```cli
gcloud compute network-firewall-policies rules create 1000 \
  --project=app-prod-1 \
  --firewall-policy=pan-nsi-policy \
  --action=APPLY_SECURITY_PROFILE_GROUP \
  --security-profile-group=organizations/ORG_ID/locations/global/securityProfileGroups/pan-spg \
  --direction=INGRESS \
  --layer4-configs=tcp:443 \
  --src-ip-ranges=10.10.1.0/24 \
  --global-firewall-policy \
  --enable-logging
```

For egress rules, use destination matching instead of ingress source matching.

## 4.12 Associate firewall policy with VPC

```cli
gcloud compute network-firewall-policies associations list \
  --project=app-prod-1 \
  --firewall-policy=pan-nsi-policy
```

---

# 5. East-west packet flow with NSI

Example:

```text
Client: 10.10.1.10:51514
Server: 10.10.2.20:443
```

1. The client sends a SYN using the ordinary consumer VPC route.
2. The VPC firewall policy evaluates the new connection.
3. The matching rule invokes `APPLY_SECURITY_PROFILE_GROUP`.
4. The security profile group resolves to the custom-intercept profile.
5. The profile resolves to `pan-ieg`.
6. The endpoint group maps to producer deployment group `pan-idg`.
7. NSI selects the zonal intercept deployment.
8. The intercept deployment references the producer ILB forwarding rule.
9. The ILB chooses a healthy VM-Series backend.
10. GENEVE carries the original packet and metadata to VM-Series.
11. PAN-OS evaluates zones, Security policy, App-ID/content inspection, and enabled security subscriptions.
12. A deny verdict drops the packet; an allow verdict causes the appliance to re-encapsulate the unmodified original packet.
13. The appliance sends that GENEVE packet back by **Direct Server Return (DSR)**, bypassing the producer ILB on reinjection.
14. Google resumes the original consumer-network delivery toward `10.10.2.20`.

## 5.1 Return path — NSI firewall rules are stateful

A **separate reverse-direction `APPLY_SECURITY_PROFILE_GROUP` rule is not required for return packets that belong to an already tracked NSI session**. Google explicitly documents that intercept firewall rules are stateful: when a **new session** matches an intercept rule, all subsequent **ingress and egress** packets associated with that session are intercepted automatically and are encapsulated with the appropriate security-profile-group context.

![NSI stateful return traffic](images/09-07-26-08-06_pan_gcp_nsi_stateful_session_return.svg)

[Editable draw.io](images/09-07-26-08-06_pan_gcp_nsi_stateful_session_return.drawio)

**What this image shows:** The first SYN is selected by one directional NSI intercept rule. Once Google has created state for that connection, the reverse SYN-ACK and later packets are automatically intercepted as members of the same tracked session.

**What matters:** Rule direction determines which **new connections** enter NSI inspection. It does not require every packet direction of an already established connection to independently match a second `APPLY_SECURITY_PROFILE_GROUP` rule.

**What to verify:** Confirm the initiating packet matches the intended intercept rule; endpoint/deployment resources are healthy; VM-Series receives the GENEVE packet; and both traffic directions appear in the expected PAN-OS session.

For example, if this new connection is selected by an egress intercept rule:

```text
10.10.1.10:51514 -> 10.10.2.20:443
```

then the response:

```text
10.10.2.20:443 -> 10.10.1.10:51514
```

is recognized by Google as the reverse direction of the tracked NSI session and is automatically sent through the same inspection service. It does **not** need to independently match a newly created ingress interception rule simply to preserve stateful symmetry.

| Traffic case | Separate opposite-direction intercept rule required? |
|---|---|
| Return packet for a session that already matched NSI | **No** — automatically intercepted as part of the tracked session |
| Later packets in either direction of that same session | **No** — NSI session state preserves interception |
| Brand-new connection initiated from the opposite direction | **Yes**, if that independently initiated connection must be inspected |
| TCP non-SYN packet that is not part of a known active tracked session | Cannot establish a new intercepted TCP session; Google documents that matching partial TCP sessions are dropped |

### 5.2 New-session policy selection versus reverse-session state

This distinction is important when designing policy. A reverse-direction intercept rule is useful when the opposite endpoint is allowed to initiate **new** connections. It is not required merely because TCP has response packets traveling in the opposite direction.

Correct mental model:

```text
First packet of NEW connection
        |
        v
Directional firewall rule matches
APPLY_SECURITY_PROFILE_GROUP
        |
        v
Google creates tracked NSI session
        |
        +-------------------------------+
        |                               |
        v                               v
Forward packets                    Reverse packets
automatically intercepted          automatically intercepted
        |                               |
        +-------------> VM-Series <-----+
```

### 5.3 Partial TCP-session caveat

Google cautions that intercept rules cannot process arbitrary partial TCP sessions. Non-SYN TCP packets that match an intercept rule but do not belong to a known, tracked active connection are dropped. This is another indication that NSI interception is connection-state-aware rather than a stateless per-packet redirect mechanism.

**Source information:** Google states that intercept firewall rules are stateful and that all subsequent ingress and egress packets associated with a matching new session are intercepted automatically.

**Additional explanation:** PAN-OS remains stateful too. Because Google keeps both directions in the NSI inspection path, the VM-Series can inspect both halves of a connection in its PAN-OS session without you creating a second consumer-VPC route or duplicate reverse-direction intercept rule.

**Reasonable inference:** For an established intercepted connection with return-path problems, first validate the NSI endpoint/deployment state, GENEVE delivery/reinjection, and PAN-OS session before assuming the fix is another reverse-direction intercept rule.

---

# 6. NSI Internet egress — complete forward and return path

![NSI Internet egress forward and return paths](images/09-07-26-07-03_nsi_internet_egress_return_paths.svg)

[Editable draw.io](images/09-07-26-07-03_nsi_internet_egress_return_paths.drawio)

**What this image shows:** NSI has two materially different Internet-egress models: **standard in-band reinjection**, in which the consumer VPC still owns Internet routing/NAT, and **direct Internet egress**, in which the producer VM-Series sends allowed packets directly to the Internet and returns responses to the consumer over GENEVE.

**What matters:** In standard NSI, once the outbound connection has matched an intercept rule, return packets belonging to that same tracked connection are automatically intercepted by NSI. You do not need a separate ingress `APPLY_SECURITY_PROFILE_GROUP` rule merely for the response leg. In direct Internet egress the response lands on VM-Series itself and is GENEVE-reinjected to the consumer.

**What to verify:** identify which model your VM-Series deployment is actually configured for before troubleshooting routes, NAT, or interception state.

## 6.1 Model A — standard in-band reinjection with Cloud NAT or a workload external IP

Example original flow:

```text
Consumer VM:       10.10.1.10:51514
Internet server:   198.51.100.25:443
```

### 6.1.1 Forward path

1. `10.10.1.10` creates the TCP connection toward `198.51.100.25:443`.
2. The consumer VPC's **egress** firewall policy matches the **new session** and invokes `APPLY_SECURITY_PROFILE_GROUP`.
3. NSI resolves the security profile group → custom-intercept profile → `pan-ieg` → `pan-idg` → the zonal intercept deployment.
4. Google GENEVE-encapsulates the original packet and sends it to the producer internal passthrough ILB on UDP/6081.
5. The ILB selects a healthy VM-Series backend.
6. VM-Series decapsulates the packet and PAN-OS inspects the original tuple:

```text
10.10.1.10:51514 -> 198.51.100.25:443
```

7. If PAN-OS denies it, the connection stops there.
8. If PAN-OS allows it, the appliance re-encapsulates the **original packet** using the GENEVE metadata and sends it back using DSR. The producer ILB is not traversed on this reinjection leg.
9. Google restores the packet to the consumer VPC's normal forwarding path.
10. The consumer VPC then follows its ordinary Internet route.
11. If **Cloud NAT** is the Internet egress mechanism, Cloud NAT performs SNAT. Conceptually:

```text
Before Cloud NAT:
10.10.1.10:51514 -> 198.51.100.25:443

After Cloud NAT:
NAT_PUBLIC_IP:translated-source-port -> 198.51.100.25:443
```

The exact translated source port is implementation/runtime state and should not be fabricated in a design document.
12. The packet reaches the Internet server.

### 6.1.2 Return path — automatically intercepted as part of the existing NSI session

The Internet response does **not** need a second independent ingress intercept-rule match simply to return through VM-Series.

1. The server replies:

```text
198.51.100.25:443 -> NAT_PUBLIC_IP:translated-source-port
```

2. The response reaches the consumer's Internet edge.
3. If Cloud NAT was used, Cloud NAT performs reverse translation and restores the destination to the consumer VM's private tuple:

```text
198.51.100.25:443 -> 10.10.1.10:51514
```

4. Google recognizes the response as the reverse direction of the **existing tracked NSI connection** created when the outbound session first matched the egress intercept rule.
5. Because intercept firewall rules are stateful, NSI automatically intercepts this response packet. A separate ingress `APPLY_SECURITY_PROFILE_GROUP` rule is not required for the return traffic of this established session.
6. NSI GENEVE-encapsulates the response with the appropriate security-profile context and sends it to the producer VM-Series service.
7. VM-Series decapsulates the response and evaluates it against the existing PAN-OS session/security state.
8. If allowed, VM-Series re-encapsulates the response and reinjects it by DSR.
9. Google delivers the restored response to `10.10.1.10`.
10. The client TCP stack receives the response and the session continues.

The standard model still has **four logical consumer/producer boundary crossings** for a full bidirectional exchange, but the third crossing is triggered by the state of the already intercepted session—not by a requirement for a separately authored reverse-direction intercept rule:

```text
Hop 1  consumer -> producer   new outbound session inspection
Hop 2  producer -> consumer   outbound reinjection
Hop 3  consumer -> producer   automatic reverse-packet interception for tracked session
Hop 4  producer -> consumer   inbound response reinjection
```

### 6.1.3 Who owns state?

There are three relevant state domains to keep distinct:

- **Google NSI intercept-session state** — determines that subsequent ingress and egress packets belong to the connection selected for interception.
- **PAN-OS session state** — App-ID, Security policy, threat inspection, and PAN-OS connection/session processing.
- **Cloud NAT state** — the private-to-public source translation and reverse mapping, if Cloud NAT is used.

Do not treat those as one shared state table. PAN-OS is not performing Cloud NAT's translation merely because it inspected the packet first, and an additional reverse NSI rule is not what preserves interception for an already tracked NSI session.

### 6.1.4 Why the consumer default route still matters

In this standard NSI model, the appliance is an inspection service, not the final Internet next hop. After an allow verdict and GENEVE reinjection, the consumer VPC still needs a valid Internet path such as:

```text
consumer default route -> default internet gateway -> Cloud NAT / external IP -> Internet
```

If the consumer has no usable Internet path, NSI can inspect and reinject successfully and the flow can still fail after reinjection.

## 6.2 Model B — direct Internet egress through VM-Series

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

## 6.3 Standard versus direct Internet egress

| Characteristic | Standard NSI | Direct Internet egress |
|---|---|---|
| Allowed outbound packet returns to consumer before Internet | Yes | No |
| Consumer needs its own Internet route | Yes | Not for the inspected direct-egress flow |
| Consumer Cloud NAT required | If private workloads need it | No |
| VM-Series sends packet directly to Internet | No | Yes |
| Internet response first lands in consumer Internet path | Yes | No |
| Internet response first lands on producer firewall | No | Yes |
| Response inspected | **Yes — automatically as reverse traffic of the tracked NSI session** | Yes, directly on VM-Series |
| Separate ingress intercept rule required for response leg | **No** | No; response is already on VM-Series |
| Cross-VPC boundary crossings per bidirectional Internet exchange | Four logical hops | Two logical hops |

## 6.4 Verification for Internet egress

### Standard model

**Where:** consumer VPC, Cloud NAT, NSI, PAN-OS.

**Check:**

```cli
gcloud compute routes list --project=app-prod-1 \
  --filter='network:app-vpc'

gcloud compute routers nats list \
  --router=ROUTER_NAME \
  --region=us-central1 \
  --project=app-prod-1
```

Also verify PAN-OS sees both directions of the private inner flow.

**Success criteria:**

- outbound new session is inspected and reinjected;
- consumer route/NAT sends it to the Internet;
- response reverse-NATs back to the private VM;
- Google recognizes it as reverse traffic for the existing NSI session and automatically intercepts it;
- PAN-OS sees the response in the expected session and NSI reinjects it to the VM.

### Direct Internet egress

**Where:** producer VM-Series untrust/trust path and NSI.

Verify:

```cli
show session all filter source 10.10.1.10 destination 198.51.100.25
show routing route
show counter global filter severity drop delta yes
```

**Success criteria:** PAN-OS sees the outbound inner flow, routes/NATs it to untrust, receives the Internet response, associates it with the same logical session, and sends a GENEVE return packet to the consumer.

---

# 7. Traditional internal passthrough ILB + PBR/static-route architecture — full deep dive

![Traditional ILB/PBR east-west and Internet flows](images/09-07-26-07-03_traditional_ilb_pbr_east_west_internet.svg)

[Editable draw.io](images/09-07-26-07-03_traditional_ilb_pbr_east_west_internet.drawio)

![Traditional ILB/PBR hybrid Interconnect and HA VPN inspection](images/09-07-26-07-03_traditional_ilb_pbr_hybrid_interconnect_havpn.svg)

[Editable draw.io](images/09-07-26-07-03_traditional_ilb_pbr_hybrid_interconnect_havpn.drawio)

**What these images show:** The first diagram separates east-west service insertion from Internet north-south routing. The second shows how on-premises traffic arriving through **Cloud Interconnect** or **HA VPN** can be steered through a trust-side internal passthrough ILB and VM-Series fleet before reaching workloads, with the reverse direction also inspected.

**What matters:** In the traditional model, the firewall is a **real L3 forwarding hop**. Google PBR/static-route logic gets the packet to an ILB-backed firewall interface; PAN-OS then performs its own route lookup and forwards the packet out another dataplane interface. The packet re-enters Google VPC routing after leaving VM-Series.

**What to verify:** both forward and return steering, ILB health, symmetric hashing, PAN-OS route/NAT/security state, Cloud Router dynamic routes for on-prem prefixes, and PBR recursion exclusions.

## 7.1 Traditional model building blocks

A typical multi-interface VM-Series design contains:

| Component | Typical purpose |
|---|---|
| Untrust VPC/interface | Internet-facing path; external LB/external IP/Cloud NAT design depending architecture |
| Management VPC/interface | GUI/API/Panorama/Strata management |
| Trust VPC/interface | Workload/hub-facing routed inspection path |
| Internal passthrough ILB | Highly available next hop in front of firewall dataplane NICs |
| Backend service | Health and backend membership for VM-Series instances |
| PBR | Selective service insertion based on source, destination, protocol, and endpoint scope |
| Custom static route | Destination-prefix steering to a next-hop ILB |
| Cloud Router | BGP route exchange for Cloud Interconnect or HA VPN |
| PAN-OS virtual router | Routing decision after the firewall receives the packet |
| PAN-OS Security/NAT policies | Stateful inspection and optional translation |

Palo Alto recommends the trust interface as a backend of an internal passthrough Network Load Balancer for egress from trust/workload networks. Palo Alto also explicitly identifies custom routes as appropriate for **inter-VPC, VPC-to-on-premises, and VPC-to-Internet** steering and PBRs for **intra-VPC** inspection.

## 7.2 How an ILB next hop differs from a normal load-balanced application

When an internal passthrough Network Load Balancer is used as a **route next hop**, it is acting as a gateway-selection mechanism rather than as the final application VIP.

Important behavior:

- Google forwards the original packet to a selected backend VM without rewriting the packet's source/destination tuple merely because the ILB is the next hop.
- The backend VM is expected to route/forward the packet.
- All VPC-supported protocol traffic can be sent through a next-hop ILB; it is not limited to the forwarding rule's nominal TCP/UDP service ports in the way a normal application listener would be.
- The firewall VM therefore needs IP forwarding/routing behavior appropriate to the Palo Alto deployment.
- After VM-Series forwards the packet, Google performs a **new VPC route lookup** on the egressing dataplane interface.

That last point is the essence of **multi-stage routing**:

```text
Stage 1: source endpoint / hybrid attachment
         -> PBR or static route
         -> internal passthrough ILB
         -> selected VM-Series backend

Stage 2: VM-Series PAN-OS route/security/NAT decision
         -> firewall egress interface
         -> packet re-enters Google VPC routing
         -> final workload / hybrid path / Internet
```

## 7.3 PBR versus custom static route

### Use a PBR when

You need to match more than the destination prefix, for example:

- only source `10.10.1.0/24`;
- only TCP/443;
- only VMs with a particular network tag;
- traffic entering through Cloud Interconnect VLAN attachments in a particular region;
- subnet-to-subnet traffic where ordinary subnet routing would otherwise be preferred.

### Use a custom static route when

A destination prefix alone is enough to select the firewall service, such as:

```text
0.0.0.0/0      -> trust ILB for Internet egress
10.100.0.0/16  -> trust ILB for on-premises destinations
10.20.0.0/16   -> trust ILB for a remote workload network
```

For next-hop ILBs, the route and load balancer must satisfy Google's same-network/global-access requirements.

## 7.4 East-west inspection — subnet/VPC A to subnet/VPC B

Example:

```text
Workload A: 10.10.1.10
Workload B: 10.20.1.20
Firewall service: VM-Series fleet behind ILB-A / ILB-B
```

### Forward path

1. `10.10.1.10` emits traffic toward `10.20.1.20`.
2. A PBR or custom route associated with the source side selects the appropriate internal passthrough ILB as the next hop.
3. The ILB hashes the flow and selects a healthy VM-Series backend.
4. The packet arrives at the firewall-facing NIC **with the original source/destination tuple preserved**.
5. PAN-OS performs:
   - ingress zone determination;
   - session lookup/creation;
   - Security policy evaluation;
   - App-ID/threat inspection;
   - NAT policy if the design requires translation;
   - virtual-router route lookup.
6. PAN-OS forwards the packet out the interface toward the destination side.
7. The packet re-enters the Google VPC fabric.
8. The destination-side route lookup delivers it toward `10.20.1.20`.

### Return path

1. `10.20.1.20` replies to `10.10.1.10`.
2. The destination-side PBR/static-route design must steer that reverse packet to the firewall service rather than allowing a direct bypass.
3. A corresponding ILB selects an eligible VM-Series backend.
4. **Symmetric hashing** on modern internal passthrough ILB next-hop designs helps the reverse five-tuple select the same eligible backend because the hash is direction-independent.
5. PAN-OS finds the existing session, performs reverse NAT if any, and applies stateful inspection.
6. PAN-OS routes the packet toward side A.
7. Google delivers it to `10.10.1.10`.

### Critical symmetry point

Symmetric hashing helps only when the architecture is built correctly. Google documents additional requirements when two internal passthrough ILBs use the same multi-NIC backend firewall VMs:

- the load balancers need the same eligible backend set;
- health state must be consistent across the paired load balancers;
- failover configuration must align if used.

If the reverse PBR is missing entirely, symmetric hashing cannot save the session because the return packet never reaches the ILB/firewall service.

## 7.5 Intra-VPC east-west inspection

Palo Alto specifically identifies PBR as the mechanism for intra-VPC subnet-to-subnet inspection.

Example source-tagged PBR:

```cli
gcloud services enable networkconnectivity.googleapis.com \
  --project=SEC_PROJECT

gcloud network-connectivity policy-based-routes create pbr-app-to-db \
  --project=SEC_PROJECT \
  --network="projects/SEC_PROJECT/global/networks/trust-vpc" \
  --source-range=10.10.1.0/24 \
  --destination-range=10.10.2.0/24 \
  --ip-protocol=ALL \
  --protocol-version=IPv4 \
  --next-hop-ilb-ip=10.10.10.25 \
  --priority=500 \
  --tags=inspect-eastwest \
  --description="Inspect app to database traffic through VM-Series"
```

Create the opposite-direction steering as required for stateful inspection:

```cli
gcloud network-connectivity policy-based-routes create pbr-db-to-app \
  --project=SEC_PROJECT \
  --network="projects/SEC_PROJECT/global/networks/trust-vpc" \
  --source-range=10.10.2.0/24 \
  --destination-range=10.10.1.0/24 \
  --ip-protocol=ALL \
  --protocol-version=IPv4 \
  --next-hop-ilb-ip=10.10.10.25 \
  --priority=500 \
  --tags=inspect-eastwest \
  --description="Return-path inspection database to app"
```

**Important:** tags apply to VMs that emit the packet. Ensure the intended source VMs actually carry the tag and do not accidentally tag the firewall backends into the same steering rule.

## 7.6 Inter-VPC / hub-and-spoke east-west inspection

Palo Alto supports a trust/hub model where workload networks direct traffic toward an internal load balancer in the firewall/trust path.

Google supports exporting/importing certain custom static routes with next-hop internal passthrough ILBs over VPC Network Peering. In a peering-based hub design:

```text
Spoke A
  -> imported/custom route toward ILB/firewall service
  -> VM-Series
  -> hub/trust routing
  -> Spoke B
```

Return:

```text
Spoke B
  -> imported/custom route toward firewall service
  -> VM-Series existing session
  -> Spoke A
```

Do not assume generic VPC peering itself creates transit between arbitrary spokes. The inspection design must use supported exported/imported routes and topology constructs deliberately.

## 7.7 Internet egress — workload to Internet

Example:

```text
10.10.1.10 -> 198.51.100.25:443
```

### Forward path

1. Workload sends Internet-bound traffic.
2. A default static route (`0.0.0.0/0`) or a suitable PBR sends it to the **trust-side internal passthrough ILB**.
3. The ILB selects a healthy VM-Series backend.
4. VM-Series receives the original private source packet on trust.
5. PAN-OS Security/App-ID/Threat policy is evaluated.
6. PAN-OS virtual routing selects the untrust/Internet-facing path.
7. If PAN-OS is the Internet NAT device in this architecture, a source NAT rule translates the private source.
8. The packet leaves the untrust dataplane path and reaches the Internet by the configured GCP Internet-edge mechanism.

Palo Alto documents that for outbound Internet traffic the untrust side can use an external IP or a Cloud NAT design depending deployment model. For active/passive architectures, Palo Alto specifically calls for an **external passthrough load balancer** for both Internet inbound and outbound because of connection-tracking requirements.

### Return path

1. Internet server replies to the public source identity used by the firewall design.
2. The Google Internet-facing construct delivers the response to the VM-Series untrust path.
3. The response must return to the appropriate PAN-OS state owner.
4. PAN-OS performs reverse NAT, session lookup, and response inspection.
5. PAN-OS routes the restored private response out trust.
6. The packet re-enters the trust/workload VPC.
7. Google routing delivers it to `10.10.1.10`.

In this traditional design, **PAN-OS can own the Internet NAT state**, unlike standard NSI where consumer Cloud NAT may be the translator.

## 7.8 Internet ingress — Internet to published workload

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

## 7.9 On-premises inspection through Cloud Interconnect

Yes — **Cloud Interconnect is a supported and important traditional PBR service-insertion use case**.

### 7.9.1 Where is the PBR actually applied?

This is different from AWS or Azure and is the most important point to understand:

> **A Google Cloud Policy-Based Route is not attached to a subnet and it is not associated with a customer-managed route table.**

The PBR is created as a **global resource that belongs to one VPC network**. The `--network` parameter is the VPC attachment:

```cli
--network="projects/SEC_PROJECT/global/networks/trust-vpc"
```

After the PBR belongs to `trust-vpc`, the route's own **scope** determines which packet sources are eligible to use it.

Google supports three practical scope models:

| PBR scope | How configured | Which packet sources are eligible |
|---|---|---|
| Network-wide | Omit `--tags` and `--interconnect-attachment-region` | All applicable VMs, Cloud VPN tunnels, and Cloud Interconnect VLAN attachments in the VPC |
| Selected VM sources | `--tags=TAG` | Only packets emitted by VMs in the VPC that have the specified network tag |
| Cloud Interconnect ingress | `--interconnect-attachment-region=REGION` or `all` | Packets entering the VPC through Cloud Interconnect VLAN attachments in that region, or all regions |

There is therefore **no later step such as “associate this PBR with subnet 10.10.0.0/24.”** The source/destination filters identify packet characteristics, while the route scope identifies the VPC endpoints where the PBR is applicable.

Mental model:

```text
Policy-Based Route
        |
        +-- belongs to trust-vpc
        |      --network=trust-vpc
        |
        +-- scope decides WHERE it can be evaluated
        |      |
        |      +-- network-wide
        |      +-- tagged VMs
        |      +-- Interconnect VLAN attachments by region
        |
        +-- filter decides WHICH packets match
               source CIDR
               destination CIDR
               protocol
        |
        +-- action
               next-hop internal passthrough ILB
```

Google's PBR is a **global Network Connectivity Center/Network Connectivity API resource**, but its routing applicability is tied to the specified VPC and route scope. It does not create a separate user-visible per-subnet route table.

### 7.9.2 Inbound Cloud Interconnect traffic — how the PBR is scoped

Google PBRs can be installed specifically for **Cloud Interconnect VLAN attachments by region**. This lets the PBR intercept packets as they enter the VPC from on-premises before ordinary dynamic/subnet routing sends them directly to a workload.

Example:

```text
On-prem source:                 10.100.0.0/16
GCP workload:                   10.10.0.0/16
Trust ILB VIP:                  10.250.10.25
Interconnect attachment region: us-central1
VPC:                            trust-vpc
```

The PBR:

```cli
gcloud network-connectivity policy-based-routes create pbr-interconnect-to-apps \
  --project=SEC_PROJECT \
  --network="projects/SEC_PROJECT/global/networks/trust-vpc" \
  --source-range=10.100.0.0/16 \
  --destination-range=10.10.0.0/16 \
  --ip-protocol=ALL \
  --protocol-version=IPv4 \
  --next-hop-ilb-ip=10.250.10.25 \
  --priority=400 \
  --interconnect-attachment-region=us-central1 \
  --description="Inspect on-prem traffic arriving through us-central1 Interconnect attachments"
```

Read that command literally as:

```text
Create PBR pbr-interconnect-to-apps
        |
        +-- belongs to trust-vpc
        |
        +-- eligible ingress points:
        |      Cloud Interconnect VLAN attachments in us-central1
        |
        +-- if source      = 10.100.0.0/16
        +-- and destination = 10.10.0.0/16
        |
        +-- next hop = 10.250.10.25
                        internal passthrough ILB
                        -> VM-Series
```

You **do not** attach the PBR to the Cloud Router, VLAN attachment, subnet, or a route table after this command. `--interconnect-attachment-region=us-central1` is what makes the route applicable to packets entering through the qualifying VLAN attachments.

Google does not let you scope the route to one individual VLAN attachment. The documented granularity is the VLAN-attachment **region**, or `all` attachment regions.

Only VLAN attachments that meet Google's current PBR dataplane requirements can use policy-based routes; verify the current Cloud Interconnect dataplane version requirements before deployment.

### 7.9.3 Inbound on-prem → GCP packet walk

1. On-prem router sends the packet across Dedicated or Partner Interconnect toward Google.
2. The packet enters `trust-vpc` through a VLAN attachment in `us-central1`.
3. Because `pbr-interconnect-to-apps` has `--interconnect-attachment-region=us-central1`, this PBR is applicable at that ingress point.
4. Google evaluates the PBR filter:

```text
source      10.100.0.0/16
             matches

destination 10.10.0.0/16
             matches

protocol    ALL
             matches
```

5. The PBR wins before ordinary destination routing and selects the internal passthrough ILB `10.250.10.25`.
6. The ILB selects a healthy VM-Series backend.
7. PAN-OS performs Security/App-ID/threat inspection and its own route lookup.
8. VM-Series forwards the packet toward the workload side.
9. The packet re-enters the Google VPC dataplane.
10. Normal VPC routing delivers it to the final workload in `10.10.0.0/16`.

So the forward path is:

```text
On-prem
   |
   v
Cloud Interconnect
VLAN attachment in us-central1
   |
   | PBR applies HERE because of
   | --interconnect-attachment-region=us-central1
   v
PBR filter match
   |
   v
Trust ILB 10.250.10.25
   |
   v
VM-Series
   |
   v
normal VPC routing
   |
   v
10.10.0.0/16 workload
```

### 7.9.4 Return GCP → on-prem — the Interconnect-scoped PBR does not apply to the workload VM

This is where designs commonly become confusing.

The inbound PBR is scoped to **Interconnect VLAN attachments**. A workload VM sending a return packet is a different packet source, so the `--interconnect-attachment-region` scope does not make that route automatically applicable to the workload VM.

For the workload-to-on-prem direction, use an appropriate return steering method. A clean PBR example is to tag the workload VMs that should send hybrid traffic through VM-Series.

Tag the workload:

```cli
gcloud compute instances add-tags app-vm-1 \
  --project=SEC_PROJECT \
  --zone=us-central1-a \
  --tags=inspect-hybrid
```

Then create the return-side PBR in the **same VPC**, scoped to that VM tag:

```cli
gcloud network-connectivity policy-based-routes create pbr-apps-to-onprem \
  --project=SEC_PROJECT \
  --network="projects/SEC_PROJECT/global/networks/trust-vpc" \
  --source-range=10.10.0.0/16 \
  --destination-range=10.100.0.0/16 \
  --ip-protocol=ALL \
  --protocol-version=IPv4 \
  --next-hop-ilb-ip=10.250.10.25 \
  --priority=400 \
  --tags=inspect-hybrid \
  --description="Inspect workload traffic returning to on-prem"
```

Again, there is no subnet/route-table association. The logic is:

```text
app-vm-1 has network tag inspect-hybrid
        |
        v
VM emits packet to 10.100.0.0/16
        |
        v
pbr-apps-to-onprem is applicable
because --tags=inspect-hybrid
        |
        v
PBR sends packet to trust ILB
        |
        v
VM-Series
        |
        v
Google performs normal routing after firewall
        |
        v
Cloud Router dynamic route
        |
        v
Interconnect VLAN attachment
        |
        v
On-prem
```

The two PBRs therefore solve **different source contexts**:

| Direction | Packet source | PBR scope |
|---|---|---|
| On-prem → GCP | Interconnect VLAN attachment | `--interconnect-attachment-region=us-central1` |
| GCP → on-prem | Workload VM | `--tags=inspect-hybrid` |

### 7.9.5 Return packet walk

1. Workload sends traffic to `10.100.0.0/16`.
2. Because the workload VM has the `inspect-hybrid` network tag, `pbr-apps-to-onprem` is applicable to packets it emits.
3. Source and destination ranges match.
4. PBR selects the trust ILB.
5. ILB sends the flow to the VM-Series service.
6. PAN-OS finds the existing session, inspects the response, and routes toward the on-prem prefix.
7. VM-Series emits the packet back into `trust-vpc`.
8. Section 7.11's firewall-bypass PBR prevents this post-inspection packet from being recursively sent to the ILB again.
9. Google resumes ordinary VPC routing.
10. The Cloud Router-learned dynamic route identifies the appropriate Interconnect path.
11. The packet exits through the selected VLAN attachment and reaches on-prem.

This separation is important:

```text
PBR scope:        Where can this PBR apply?
PBR filter:       Does this packet match source/destination/protocol?
PBR next hop:     Should it visit VM-Series first?
PAN-OS:           Is it allowed and which firewall egress path is used?
Cloud Router/BGP: After inspection, which hybrid path reaches on-prem?
```

### 7.9.6 Verification — prove scope instead of looking for a subnet association

Because there is no subnet attachment to inspect, verify the PBR object itself and the resource that provides its scope.

Describe the Interconnect ingress PBR:

```cli
gcloud network-connectivity policy-based-routes describe pbr-interconnect-to-apps \
  --project=SEC_PROJECT
```

Verify:

- `network` points to `trust-vpc`;
- source/destination ranges are correct;
- next-hop ILB IP is correct;
- priority is correct;
- Interconnect attachment region is `us-central1`.

Describe the workload return PBR:

```cli
gcloud network-connectivity policy-based-routes describe pbr-apps-to-onprem \
  --project=SEC_PROJECT
```

Verify that its VM scope contains `inspect-hybrid`.

Verify the workload actually has the tag:

```cli
gcloud compute instances describe app-vm-1 \
  --project=SEC_PROJECT \
  --zone=us-central1-a \
  --format='yaml(name,tags.items,networkInterfaces.networkIP)'
```

**Success criteria:** the workload shows `inspect-hybrid`, the return PBR references the same tag, and the PBR belongs to the expected VPC.

## 7.10 On-premises inspection through HA VPN

Yes — **HA VPN traffic can also be inspected using traditional PBR + ILB insertion**.

However, the scoping model differs from Cloud Interconnect.

Google documents that if a PBR has neither `--tags` nor `--interconnect-attachment-region`, the route is installed for **all applicable network endpoints**, including:

- VM instances;
- Cloud VPN tunnels;
- Cloud Interconnect attachments.

Therefore a network-wide PBR can match packets arriving through HA VPN and steer them to the ILB.

Conceptual inbound path:

```text
On-prem router
 -> IPsec / HA VPN tunnel
 -> Cloud Router
 -> packet enters VPC
 -> network-wide PBR matches on-prem source + workload destination
 -> trust ILB
 -> VM-Series
 -> workload
```

Return:

```text
workload
 -> workload PBR/static route
 -> trust ILB
 -> VM-Series
 -> VPC route lookup
 -> Cloud Router-selected HA VPN tunnel
 -> on-prem
```

### HA VPN PBR example

A route that deliberately applies network-wide might look like:

```cli
gcloud network-connectivity policy-based-routes create pbr-hybrid-to-apps \
  --project=SEC_PROJECT \
  --network="projects/SEC_PROJECT/global/networks/trust-vpc" \
  --source-range=10.100.0.0/16 \
  --destination-range=10.10.0.0/16 \
  --ip-protocol=ALL \
  --protocol-version=IPv4 \
  --next-hop-ilb-ip=10.250.10.25 \
  --priority=500 \
  --description="Inspect matching packets from VPN/Interconnect/network endpoints"
```

Because no VM tag or Interconnect-specific scope is supplied, understand the broad installation scope before deploying this in production.

## 7.11 Avoid PBR recursion through the firewall backends

This is one of the most important traditional-service-insertion design details.

If a network-wide PBR also applies to packets emitted by the VM-Series backend after inspection, the firewall can send a packet back into Google and have Google immediately steer it **back to the ILB/firewall again**, creating a loop.

### 7.11.1 Where is the bypass PBR applied?

Just like the inspection PBRs, the bypass PBR is **not attached to the firewall subnet or to a route table**.

The bypass PBR:

1. belongs to `trust-vpc` because of `--network`;
2. is scoped to VM instances carrying the `pan-fw` **network tag** because of `--tags=pan-fw`;
3. uses `--next-hop-other-routes=DEFAULT_ROUTING` so matching packets skip lower-priority PBRs and continue with normal Google VPC destination routing.

Therefore the effective association is:

```text
VM-Series VM
   |
   | network tag: pan-fw
   v
PBR pbr-pan-fw-bypass
   |
   | belongs to trust-vpc
   | --tags=pan-fw
   | priority 100
   | DEFAULT_ROUTING
   v
skip lower-priority interception PBRs
   |
   v
normal VPC routing
```

You do not apply it to `10.250.10.0/24`. You apply the **tag to the firewall VM**, and the PBR itself says that VMs with that tag are in scope.

### 7.11.2 First tag every VM-Series backend that must bypass interception

For example:

```cli
gcloud compute instances add-tags pan-fw-a1 \
  --project=SEC_PROJECT \
  --zone=us-central1-a \
  --tags=pan-fw
```

If there is another firewall backend:

```cli
gcloud compute instances add-tags pan-fw-b1 \
  --project=SEC_PROJECT \
  --zone=us-central1-b \
  --tags=pan-fw
```

The tag is a **GCP Compute Engine network tag** on the VM instance. It is not a PAN-OS tag, security tag, subnet tag, or firewall-policy tag.

Verify:

```cli
gcloud compute instances describe pan-fw-a1 \
  --project=SEC_PROJECT \
  --zone=us-central1-a \
  --format='yaml(name,tags.items,networkInterfaces.networkIP)'
```

Expected state includes:

```text
tags:
  items:
  - pan-fw
```

### 7.11.3 Create the higher-priority bypass PBR in the same VPC

```cli
gcloud network-connectivity policy-based-routes create pbr-pan-fw-bypass \
  --project=SEC_PROJECT \
  --network="projects/SEC_PROJECT/global/networks/trust-vpc" \
  --source-range=0.0.0.0/0 \
  --destination-range=0.0.0.0/0 \
  --ip-protocol=ALL \
  --protocol-version=IPv4 \
  --next-hop-other-routes=DEFAULT_ROUTING \
  --priority=100 \
  --tags=pan-fw \
  --description="Prevent VM-Series post-inspection traffic from re-entering interception PBRs"
```

Read the command as:

```text
PBR pbr-pan-fw-bypass
        |
        +-- belongs to trust-vpc
        |
        +-- only applies to VMs tagged pan-fw
        |
        +-- matches any IPv4 source/destination/protocol
        |
        +-- priority 100
        |
        +-- action = DEFAULT_ROUTING
                |
                +-- ignore lower-priority PBRs
                +-- resume normal VPC destination routing
```

The lower numeric priority wins between matching PBRs. Therefore a priority `100` firewall bypass is evaluated before inspection PBRs at priority `400` or `500`.

### 7.11.4 Why this stops the loop

Assume the inbound Interconnect PBR sends this packet to VM-Series:

```text
10.100.1.10 -> 10.10.1.20
```

Forward inspection:

```text
Interconnect VLAN attachment
    |
    | pbr-interconnect-to-apps priority 400
    v
Trust ILB
    |
    v
VM-Series pan-fw-a1
```

PAN-OS allows the packet and emits it toward `10.10.1.20`.

At that moment this is a **new GCP routing decision for a packet emitted by the VM-Series VM**. Because that VM has tag `pan-fw`, the bypass PBR is applicable:

```text
VM-Series emits post-inspection packet
    |
    | source endpoint = VM tagged pan-fw
    v
pbr-pan-fw-bypass priority 100
    |
    | DEFAULT_ROUTING
    v
skip interception PBRs
    |
    v
normal subnet/dynamic/static route selection
    |
    v
10.10.1.20
```

Without the bypass, a broad network-wide PBR could match the packet after VM-Series emits it:

```text
VM-Series
   -> broad PBR
   -> ILB
   -> VM-Series
   -> broad PBR
   -> ILB
   -> loop
```

### 7.11.5 Why tagging the firewall is different from tagging the workload

The two tags have opposite purposes:

| Tag | Applied to | Purpose |
|---|---|---|
| `inspect-hybrid` | Application/workload VMs | Make their emitted traffic eligible for inspection PBRs |
| `pan-fw` | VM-Series firewall VMs | Make their post-inspection emitted traffic eligible for the high-priority `DEFAULT_ROUTING` bypass PBR |

Example evaluation for a workload return packet:

```text
app-vm-1 tag = inspect-hybrid
        |
        v
pbr-apps-to-onprem priority 400
        |
        v
Trust ILB -> VM-Series
        |
        v
pan-fw-a1 emits inspected packet
pan-fw-a1 tag = pan-fw
        |
        v
pbr-pan-fw-bypass priority 100
        |
        v
DEFAULT_ROUTING
        |
        v
Cloud Router dynamic route
        |
        v
Interconnect / HA VPN
```

There is no route-table association anywhere in this sequence. Applicability follows the **VPC + endpoint scope + packet filter** model.

### 7.11.6 Scope alternatives and design cautions

Typical techniques include:

1. Scope interception PBRs only to tagged workload VMs where possible.
2. Do not give firewall backend VMs the workload interception tag.
3. Tag firewall VMs separately with `pan-fw`.
4. Create a higher-priority `DEFAULT_ROUTING` PBR for `pan-fw` VMs.
5. Make source/destination match ranges precise enough to avoid unwanted matches.
6. Use network-wide PBR scope cautiously because Google explicitly warns that it can also apply to packets emitted by an internal passthrough ILB backend VM.

The bypass PBR is particularly valuable when the inspection rule must be network-wide, such as when it needs to apply to Cloud VPN tunnel traffic and cannot be limited with a VM tag.

### 7.11.7 Verify the bypass PBR

```cli
gcloud network-connectivity policy-based-routes describe pbr-pan-fw-bypass \
  --project=SEC_PROJECT
```

Verify:

- network is `trust-vpc`;
- VM scope/tag is `pan-fw`;
- priority is `100`;
- next-hop-other-routes is `DEFAULT_ROUTING`;
- source and destination cover the intended bypass traffic.

Also verify firewall instance tags:

```cli
gcloud compute instances describe pan-fw-a1 \
  --project=SEC_PROJECT \
  --zone=us-central1-a \
  --format='yaml(name,tags.items)'
```

**Success criteria:** the VM contains `pan-fw`, the bypass PBR contains the same tag, and all lower-priority interception PBRs have numerically larger priorities.

If the VM does not have the tag, the bypass PBR is not applicable to packets emitted by that VM even though the PBR exists in the same VPC.

## 7.12 Cloud Interconnect versus HA VPN for this inspection design

| Item | Cloud Interconnect | HA VPN |
|---|---|---|
| On-prem routing | BGP through Cloud Router | BGP through Cloud Router |
| Traffic can be inserted through PBR/ILB | Yes | Yes |
| PBR can be scoped specifically by hybrid attachment region | Yes, `--interconnect-attachment-region` | No equivalent tunnel-specific PBR scope |
| Network-wide PBR can affect it | Yes | Yes |
| Return path after firewall uses dynamic hybrid route | Yes | Yes |
| Need firewall-backend recursion protection | Yes | Yes |
| HA/failover controlled partly by | Interconnect redundancy + BGP | HA VPN tunnel redundancy + BGP |

## 7.13 Symmetric hashing and PAN-OS state

Google's internal passthrough Network Load Balancer provides **symmetric hashing** for modern next-hop designs. It calculates a direction-independent hash for a flow, helping both directions select the same eligible backend.

This is extremely useful for stateful NGFWs, but it is not a substitute for correct routing.

Success requires:

- forward traffic actually reaching an ILB next hop;
- return traffic also reaching the paired ILB/service path;
- compatible backend sets and health state;
- appropriate session-affinity configuration;
- PAN-OS state on the selected firewall.

SNAT is therefore **not inherently required merely to force path symmetry** in a correctly built modern ILB-next-hop design. Use NAT only when the addressing/Internet/security architecture requires it.

## 7.14 HA and failure behavior

### Active/active or scale-out fleet

Internal passthrough ILB health checks can remove unhealthy backends for new flow selection. Symmetric hashing helps maintain bidirectional backend affinity while the eligible set is stable.

If backend eligibility changes during a live session, a later packet can end up on a different firewall that does not own the session unless state is synchronized by the selected Palo Alto architecture.

### Active/passive VM-Series

Palo Alto's active/passive GCP model uses load-balancer health and firewall HA so production traffic is directed to the active peer. Palo Alto specifically requires an **external passthrough load balancer** for active/passive Internet inbound/outbound because that load balancer supports the needed connection tracking.

For hybrid/east-west trust paths, verify:

- active peer is healthy in the internal backend service;
- passive peer is not unintentionally selected for production traffic;
- HA state synchronization is healthy;
- both firewalls have consistent routing/security/NAT configuration.

## 7.15 Traditional design verification

### Verify PBR objects

```cli
gcloud network-connectivity policy-based-routes list \
  --project=SEC_PROJECT

gcloud network-connectivity policy-based-routes describe pbr-interconnect-to-apps \
  --project=SEC_PROJECT
```

**Verify:** source range, destination range, protocol, priority, endpoint scope, next-hop ILB IP.

### Verify ILB health

```cli
gcloud compute backend-services get-health TRUST_BACKEND_SERVICE \
  --region=us-central1 \
  --project=SEC_PROJECT
```

**Success:** intended VM-Series backends are healthy.

### Verify forwarding rule/global access

```cli
gcloud compute forwarding-rules describe TRUST_ILB_FORWARDING_RULE \
  --region=us-central1 \
  --project=SEC_PROJECT
```

For PBR use across regions, Google recommends enabling global access on the next-hop internal passthrough ILB.

### Verify Cloud Router routes

```cli
gcloud compute routers get-status HYBRID_ROUTER \
  --region=us-central1 \
  --project=SEC_PROJECT
```

**Verify:** on-prem prefixes are learned and expected advertisements are being sent.

### Verify PAN-OS

```cli
show session all filter source 10.100.1.10 destination 10.10.1.20
show routing route
show counter global filter severity drop delta yes
show interface all
```

Also inspect **Monitor > Traffic** and **Monitor > Threat**.

## 7.16 Troubleshooting traditional ILB/PBR by symptom

### Workload sends traffic directly and bypasses firewall

**Where:** PBR/static route selection.

**Check:** PBR scope/tag, source/destination match, route priority, next-hop ILB validity.

**Likely cause:** workload is not in PBR scope or a different routing path is winning.

### Forward path works but return traffic bypasses firewall

**Where:** destination-side/workload return steering.

**Check:** reverse PBR/static route and ILB backend symmetry.

**Failure meaning:** the state owner never sees the return packet.

### Packet loops repeatedly through VM-Series

**Where:** PBR scope on firewall backend VMs.

**Check:** whether post-inspection firewall egress traffic matches the same network-wide PBR.

**Next action:** apply a firewall-tag bypass PBR or refine interception match/scope.

### Interconnect traffic bypasses inspection

**Where:** PBR attachment scope.

**Check:** `--interconnect-attachment-region`, source/destination ranges, and next-hop ILB global access.

### HA VPN traffic bypasses inspection

**Where:** PBR installation scope.

**Check:** whether the PBR is network-wide. A VM-tag-scoped PBR does not mean “apply to VPN tunnels.”

### Cloud Router knows on-prem prefix but firewall cannot forward to it

**Where:** PAN-OS virtual router and firewall interface topology.

**Check:** firewall route table and next-hop path after the packet leaves VM-Series. Google Cloud's VPC/Cloud Router route knowledge does not automatically populate PAN-OS with an equivalent route unless your design/configuration provides it.

### ILB has healthy backends but stateful sessions still fail intermittently

**Where:** eligible backend symmetry/session affinity/HA state.

**Check:** paired ILBs use the same eligible backend set, health is consistent, session affinity isn't incompatible with symmetric hashing, and PAN-OS HA/session synchronization is functioning if required.

---

# 8. Inbound Internet and interface constraints

Palo Alto documents that Google Cloud external load balancers deliver traffic to a VM's primary interface. VM-Series designs therefore commonly require careful NIC ordering and, in some load-balanced architectures, a management-interface swap.

Palo Alto documents:

```cli
set system setting mgmt-interface-swap enable yes
request restart system
```

Verify after reboot:

```cli
debug show vm-series interfaces all
```

Do not enable the swap on a one-interface firewall; Palo Alto warns this can cause maintenance-mode behavior.

---

# 9. HA and scaling

## Active/passive

Palo Alto's GCP active/passive model uses load balancers and health checks so only the active firewall receives production dataplane traffic. The pair synchronizes configuration/state and is intended to preserve sessions during failover.

Use it when session continuity and deterministic HA matter more than horizontal scale.

## Autoscale

Autoscaling VM-Series is appropriate when inspection throughput changes materially and a horizontally scalable firewall fleet is preferred. Panorama-driven templates and lifecycle automation are commonly used.

## NSI zonal coverage

An intercept deployment is **zonal**. Build the producer service in every required zone and confirm the backing ILB has healthy inspection capacity in those zones.

Palo Alto's NSI overlay documentation currently notes that autoscaling is not supported for that overlay mode; verify current vendor release notes before designing elastic direct-egress NSI capacity.

---

# 10. NAT behavior

## NSI standard reinjection

- PAN-OS SNAT is not automatically required.
- Consumer Cloud NAT can remain the Internet translation point.
- Outbound inspected traffic is reinjected to the consumer before Internet routing.
- Return traffic is reverse-NATed in the consumer path and is **automatically intercepted again because it belongs to the existing tracked NSI session**.

## NSI direct Internet egress

- VM-Series becomes the Internet-facing routed inspection point for selected flows.
- PAN-OS can own the routing/NAT needed by the direct-egress appliance architecture.
- Consumer Cloud NAT/default Internet routing is not required for those direct-egress inspected flows.

## Traditional routed VM-Series

A classic route-based VM-Series deployment can perform normal PAN-OS source NAT and destination NAT because the firewall is a real forwarding hop.

---

# 11. Verification

## NSI control plane

```cli
gcloud network-security intercept-deployment-groups list \
  --project=pan-sec-prod \
  --location=global

gcloud network-security intercept-deployments list \
  --project=pan-sec-prod \
  --location=-

gcloud network-security intercept-endpoint-groups list \
  --project=app-prod-1 \
  --location=global
```

## Producer ILB health

```cli
gcloud compute backend-services get-health pan-nsi-ilb-bs \
  --project=pan-sec-prod \
  --region=us-central1
```

## Consumer firewall policy

```cli
gcloud compute network-firewall-policies rules list \
  --project=app-prod-1 \
  --firewall-policy=pan-nsi-policy \
  --global-firewall-policy
```

## VM-Series

```cli
show session all filter source 10.10.1.10 destination 10.10.2.20
show counter global filter severity drop delta yes
show routing route
show interface all
```

Also inspect **Monitor > Traffic**, **Monitor > Threat**, plugin state, and HA state.

Exact output varies by PAN-OS/plugin release, so success should be judged by the expected inner source/destination/application and intended policy verdict rather than by fabricated sample output.

---

# 12. Troubleshooting by symptom

## Policy matches but no traffic appears on VM-Series

**Where:** consumer firewall policy and NSI resource chain.

**Check:** rule → security profile group → custom-intercept profile → endpoint group → deployment group → zonal deployment.

## Deployment is active but packets do not pass

```cli
gcloud compute backend-services get-health pan-nsi-ilb-bs \
  --region=us-central1 \
  --project=pan-sec-prod
```

Check health check, VM-Series interface mapping, HA state, backend registration, and producer UDP/6081 reachability.

## VM-Series sees GENEVE but not inner sessions

```cli
request plugins vm_series geneve-inspect enable yes
```

Verify required reboot and interface/plugin state.

## Standard NSI Internet outbound works but responses do not reach the VM

**Check in order:**

1. consumer Cloud NAT/external-IP return path;
2. reverse NAT back to the private consumer VM;
3. Google NSI state for the already intercepted connection;
4. automatic reverse-packet interception to the producer VM-Series service;
5. PAN-OS response session state;
6. GENEVE DSR reinjection.

A missing standalone ingress `APPLY_SECURITY_PROFILE_GROUP` rule is **not** normally the explanation for return packets that already belong to the tracked outbound NSI session.

## Direct Internet egress sends outbound traffic but receives no usable response

**Check:** PAN-OS untrust return route/NAT state, Security policy, response session lookup, and GENEVE response reinjection metadata.

## Traditional ILB/PBR design has one-way sessions

**Check:** reverse PBR/custom route, paired ILB eligible backends, symmetric hashing requirements, and PAN-OS state owner.

---

# 13. Common mistakes

1. Calling Google Cloud NGFW Enterprise a Palo Alto-managed firewall.
2. Assuming a standalone product named “Palo Alto Cloud NGFW for Google Cloud” exists because Palo Alto has Cloud NGFW for AWS/Azure.
3. Adding a route next hop to VM-Series in an NSI consumer VPC; standard NSI selection is firewall-policy driven.
4. Forgetting GENEVE inspection enablement on VM-Series.
5. Associating the producer VPC itself as the consumer endpoint-group network.
6. Ignoring zonal intercept-deployment coverage.
7. Treating an unhealthy ILB backend as a firewall-policy problem.
8. Assuming standard NSI Internet responses bypass inspection.
9. **Assuming return packets for an established NSI session need a second ingress `APPLY_SECURITY_PROFILE_GROUP` rule.** They are automatically intercepted as part of the tracked session; the opposite-direction rule is for independently initiated new connections.
10. Confusing standard NSI Cloud NAT state with PAN-OS NAT state.
11. Assuming direct Internet egress still requires consumer Cloud NAT.
12. Expecting a forward-only PBR to provide stateful symmetry in the traditional routed model.
13. Applying a broad PBR to VM-Series backend traffic and creating recursive service insertion.
14. Assuming an Interconnect-region-scoped PBR also means the same thing for HA VPN tunnels.
15. Assuming Cloud Router's dynamic route automatically exists inside the PAN-OS virtual router.
16. Ignoring GCP primary-interface/load-balancer constraints for Internet ingress.

---

# 14. Design decision matrix

| Requirement | Google Cloud NGFW Enterprise | VM-Series + NSI | VM-Series + ILB/PBR |
|---|---:|---:|---:|
| Google-managed firewall lifecycle | Yes | No | No |
| PAN-OS policy | No | Yes | Yes |
| App-ID / PAN-OS subscriptions | No PAN-OS control plane | Yes | Yes |
| No route changes for service insertion | Yes | Yes | No |
| Explicit firewall L3 hop | No | Standard: no; direct egress: firewall routes Internet leg | Yes |
| Google firewall policy selects inspection | Yes | Yes | Optional/No |
| GENEVE inspection | Google-managed internal path | Yes | Not required |
| Customer controls firewall VMs | No | Yes | Yes |
| Consumer Cloud NAT can remain Internet NAT | N/A/design-specific | Yes in standard model | Not normally if PAN-OS owns routed Internet NAT |
| Direct appliance Internet egress | No PAN-OS appliance | Yes, supported direct-egress model | Yes |
| PBR/static route required | No | No for standard NSI selection | Yes |
| Cloud Interconnect/HA VPN route-based insertion | Not this model | Firewall-policy interception | Yes |
| Best fit | Native GCP security | PAN-OS with transparent insertion | Explicit routed service chain and traditional PAN-OS topology |

---

# Sources

- https://docs.paloaltonetworks.com/vm-series
- https://docs.paloaltonetworks.com/vm-series/deployment/public-cloud/set-up-the-vm-series-firewall-on-google-cloud-platform/securing-vpc-with-vm-on-gcp
- https://docs.paloaltonetworks.com/vm-series/deployment/public-cloud/set-up-the-vm-series-firewall-on-google-cloud-platform/deployment-models-for-vm-series-on-gcp
- https://docs.paloaltonetworks.com/vm-series/deployment/public-cloud/set-up-the-vm-series-firewall-on-google-cloud-platform/google-cloud-network-security-integration-nsi-with-vm-series-firewall
- https://docs.paloaltonetworks.com/vm-series/deployment/public-cloud/set-up-the-vm-series-firewall-on-google-cloud-platform/configure-gcp-nsi-overlay-support
- https://docs.paloaltonetworks.com/vm-series/deployment/public-cloud/set-up-the-vm-series-firewall-on-google-cloud-platform/configuring-gcp-load-balancer
- https://cloud.google.com/security/products/firewall
- https://docs.cloud.google.com/network-security-integration/docs/nsi-overview
- https://docs.cloud.google.com/network-security-integration/docs/understand-geneve
- https://docs.cloud.google.com/network-security-integration/docs/in-band/in-band-integration-overview
- https://docs.cloud.google.com/network-security-integration/docs/in-band/firewall-policies-overview
- https://docs.cloud.google.com/network-security-integration/docs/in-band/in-band-integration-tutorial
- https://docs.cloud.google.com/network-security-integration/docs/in-band/configure-consumer-service
- https://docs.cloud.google.com/network-security-integration/docs/in-band/configure-firewall-rules
- https://docs.cloud.google.com/network-security-integration/docs/release-notes
- https://docs.cloud.google.com/vpc/docs/policy-based-routes
- https://docs.cloud.google.com/vpc/docs/use-policy-based-routes
- https://docs.cloud.google.com/sdk/gcloud/reference/network-connectivity/policy-based-routes/create
- https://docs.cloud.google.com/load-balancing/docs/internal/ilb-next-hop-overview
- https://docs.cloud.google.com/load-balancing/docs/internal/setting-up-ilb-next-hop
- https://cloud.google.com/blog/products/networking/policy-based-routing-network-patterns-for-virtual-appliances
