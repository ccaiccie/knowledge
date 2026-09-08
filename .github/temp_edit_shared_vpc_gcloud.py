from pathlib import Path

p = Path('09-07-26_GCP_Shared_VPC_Centralized_Firewall_Insertion_Method_11_Deep_Dive.md')
s = p.read_text()


def insert_before(next_heading: str, block: str, key: str):
    global s
    if key in s:
        return
    marker = f'\n---\n\n{next_heading}\n'
    if marker not in s:
        raise SystemExit(f'Marker not found: {next_heading}')
    s = s.replace(marker, '\n' + block + marker, 1)

# TOC
s = s.replace(
    '- [3. Architecture and ownership model](#3-architecture-and-ownership-model)\n',
    '- [3. Architecture and ownership model](#3-architecture-and-ownership-model)\n'
    '  - [3.1 Shared VPC foundation gcloud build](#31-shared-vpc-foundation-gcloud-build)\n',
)
s = s.replace(
    '  - [5.4 Representative PBR configuration](#54-representative-pbr-configuration)\n',
    '  - [5.4 Firewall ILB + PBR gcloud build](#54-firewall-ilb--pbr-gcloud-build)\n',
)
s = s.replace(
    '  - [6.1 Hybrid ingress packet flow](#61-hybrid-ingress-packet-flow)\n',
    '  - [6.1 Hybrid ingress packet flow](#61-hybrid-ingress-packet-flow)\n'
    '  - [6.2 Interconnect-scoped PBR gcloud build](#62-interconnect-scoped-pbr-gcloud-build)\n',
)
s = s.replace(
    '  - [7.1 Where SNAT belongs](#71-where-snat-belongs)\n',
    '  - [7.1 Where SNAT belongs](#71-where-snat-belongs)\n'
    '  - [7.2 Static-route egress gcloud build](#72-static-route-egress-gcloud-build)\n',
)
s = s.replace(
    '- [10. Shared VPC + Cloud NGFW Enterprise](#10-shared-vpc--cloud-ngfw-enterprise)\n',
    '- [10. Shared VPC + Cloud NGFW Enterprise](#10-shared-vpc--cloud-ngfw-enterprise)\n'
    '  - [10.1 Cloud NGFW Enterprise gcloud build](#101-cloud-ngfw-enterprise-gcloud-build)\n',
)
s = s.replace(
    '- [11. Shared VPC + NSI in-band](#11-shared-vpc--nsi-in-band)\n',
    '- [11. Shared VPC + NSI in-band](#11-shared-vpc--nsi-in-band)\n'
    '  - [11.1 NSI consumer gcloud build](#111-nsi-consumer-gcloud-build)\n',
)
s = s.replace(
    '- [12. Shared VPC + NCC Router Appliance](#12-shared-vpc--ncc-router-appliance)\n',
    '- [12. Shared VPC + NCC Router Appliance](#12-shared-vpc--ncc-router-appliance)\n'
    '  - [12.1 Router Appliance + BGP gcloud build](#121-router-appliance--bgp-gcloud-build)\n',
)

insert_before(
    '# 4. Why Shared VPC is useful for centralized firewall insertion',
    '''## 3.1 Shared VPC foundation `gcloud` build

Create the host VPC and subnets:

```cli
gcloud compute networks create prod-shared-vpc \\
  --project=network-host-prod \\
  --subnet-mode=custom

gcloud compute networks subnets create app-subnet \\
  --project=network-host-prod \\
  --network=prod-shared-vpc \\
  --region=us-central1 \\
  --range=10.10.0.0/16

gcloud compute networks subnets create db-subnet \\
  --project=network-host-prod \\
  --network=prod-shared-vpc \\
  --region=us-central1 \\
  --range=10.20.0.0/16

gcloud compute networks subnets create firewall-subnet \\
  --project=network-host-prod \\
  --network=prod-shared-vpc \\
  --region=us-central1 \\
  --range=10.100.10.0/24
```

Enable Shared VPC and attach service projects:

```cli
gcloud compute shared-vpc enable network-host-prod

gcloud compute shared-vpc associated-projects add app-prod-a \\
  --host-project=network-host-prod

gcloud compute shared-vpc associated-projects add db-prod-b \\
  --host-project=network-host-prod
```

Grant subnet-use permission to workload service accounts:

```cli
gcloud compute networks subnets add-iam-policy-binding app-subnet \\
  --project=network-host-prod \\
  --region=us-central1 \\
  --member='serviceAccount:APP_WORKLOAD_SA@app-prod-a.iam.gserviceaccount.com' \\
  --role='roles/compute.networkUser'

gcloud compute networks subnets add-iam-policy-binding db-subnet \\
  --project=network-host-prod \\
  --region=us-central1 \\
  --member='serviceAccount:DB_WORKLOAD_SA@db-prod-b.iam.gserviceaccount.com' \\
  --role='roles/compute.networkUser'
```

Verify:

```cli
gcloud compute shared-vpc get-host-project app-prod-a
gcloud compute shared-vpc get-host-project db-prod-b
gcloud compute shared-vpc list-associated-resources network-host-prod
```

**Success:** the expected host is returned and both service projects are attached.
''',
    '## 3.1 Shared VPC foundation `gcloud` build',
)

start = '## 5.4 Representative PBR configuration\n'
end = '\n---\n\n# 6. Shared VPC + Cloud Interconnect or HA VPN ingress\n'
if start in s:
    a = s.index(start)
    b = s.index(end, a)
    replacement = '''## 5.4 Firewall ILB + PBR `gcloud` build

Assume `fw-a` and `fw-b` already exist with IP forwarding enabled.

```cli
gcloud compute instance-groups unmanaged create fw-ig-a --project=network-host-prod --zone=us-central1-a
gcloud compute instance-groups unmanaged add-instances fw-ig-a --project=network-host-prod --zone=us-central1-a --instances=fw-a

gcloud compute instance-groups unmanaged create fw-ig-b --project=network-host-prod --zone=us-central1-b
gcloud compute instance-groups unmanaged add-instances fw-ig-b --project=network-host-prod --zone=us-central1-b --instances=fw-b
```

Create health check, backend service, and forwarding rule:

```cli
gcloud compute health-checks create tcp fw-hc \\
  --project=network-host-prod \\
  --region=us-central1 \\
  --port=HEALTH_CHECK_PORT

gcloud compute backend-services create fw-ilb-be \\
  --project=network-host-prod \\
  --region=us-central1 \\
  --load-balancing-scheme=INTERNAL \\
  --protocol=TCP \\
  --network=prod-shared-vpc \\
  --health-checks=fw-hc \\
  --health-checks-region=us-central1

gcloud compute backend-services add-backend fw-ilb-be \\
  --project=network-host-prod \\
  --region=us-central1 \\
  --instance-group=fw-ig-a \\
  --instance-group-zone=us-central1-a

gcloud compute backend-services add-backend fw-ilb-be \\
  --project=network-host-prod \\
  --region=us-central1 \\
  --instance-group=fw-ig-b \\
  --instance-group-zone=us-central1-b

gcloud compute addresses create fw-ilb-vip \\
  --project=network-host-prod \\
  --region=us-central1 \\
  --subnet=firewall-subnet \\
  --addresses=10.100.10.10

gcloud compute forwarding-rules create fw-ilb-fr \\
  --project=network-host-prod \\
  --region=us-central1 \\
  --load-balancing-scheme=INTERNAL \\
  --network=prod-shared-vpc \\
  --subnet=firewall-subnet \\
  --address=10.100.10.10 \\
  --ip-protocol=TCP \\
  --ports=ALL \\
  --allow-global-access \\
  --backend-service=fw-ilb-be \\
  --backend-service-region=us-central1
```

Verify health before steering traffic:

```cli
gcloud compute backend-services get-health fw-ilb-be \\
  --project=network-host-prod \\
  --region=us-central1
```

Create the PBR:

```cli
gcloud network-connectivity policy-based-routes create app-to-db-inspection \\
  --project=network-host-prod \\
  --network='projects/network-host-prod/global/networks/prod-shared-vpc' \\
  --priority=1000 \\
  --source-range=10.10.0.0/16 \\
  --destination-range=10.20.0.0/16 \\
  --ip-protocol=ALL \\
  --protocol-version=IPV4 \\
  --next-hop-ilb-ip=10.100.10.10
```

For workload-tag-only steering, create a separate PBR and add:

```cli
--tags=inspect-app
```

Verify:

```cli
gcloud network-connectivity policy-based-routes describe app-to-db-inspection \\
  --project=network-host-prod
```

**Critical:** firewall-originated post-inspection packets must not re-match the same insertion PBR.
'''
    s = s[:a] + replacement + s[b:]

insert_before(
    '# 7. Shared VPC + Internet egress',
    '''## 6.2 Interconnect-scoped PBR `gcloud` build

```cli
gcloud network-connectivity policy-based-routes create onprem-to-db-inspection \\
  --project=network-host-prod \\
  --network='projects/network-host-prod/global/networks/prod-shared-vpc' \\
  --priority=900 \\
  --source-range=10.200.0.0/16 \\
  --destination-range=10.20.0.0/16 \\
  --ip-protocol=ALL \\
  --protocol-version=IPV4 \\
  --next-hop-ilb-ip=10.100.10.10 \\
  --interconnect-attachment-region=us-central1
```

Use `--interconnect-attachment-region=all` to cover every VLAN attachment region in the VPC.

```cli
gcloud network-connectivity policy-based-routes describe onprem-to-db-inspection \\
  --project=network-host-prod
```

If neither `--tags` nor `--interconnect-attachment-region` is set, a matching PBR can apply broadly to VMs, Cloud VPN tunnels, and eligible Interconnect attachments in the VPC.
''',
    '## 6.2 Interconnect-scoped PBR `gcloud` build',
)

insert_before(
    '# 8. Where should the firewalls live?',
    '''## 7.2 Static-route egress `gcloud` build

```cli
gcloud compute routes create default-via-fw-ilb \\
  --project=network-host-prod \\
  --network=prod-shared-vpc \\
  --destination-range=0.0.0.0/0 \\
  --next-hop-ilb=10.100.10.10 \\
  --priority=800
```

Verify:

```cli
gcloud compute routes describe default-via-fw-ilb --project=network-host-prod
gcloud compute routes list --project=network-host-prod --filter='network:prod-shared-vpc'
```

Use this for destination-prefix steering such as Internet egress; it does not replace PBR for arbitrary same-VPC subnet interception.
''',
    '## 7.2 Static-route egress `gcloud` build',
)

insert_before(
    '# 11. Shared VPC + NSI in-band',
    '''## 10.1 Cloud NGFW Enterprise `gcloud` build

Create and associate a zonal firewall endpoint:

```cli
gcloud network-security firewall-endpoints create endpoint-ips \\
  --organization=ORGANIZATION_ID \\
  --zone=us-central1-a \\
  --billing-project=network-host-prod

gcloud network-security firewall-endpoint-associations create endpoint-association-ips \\
  --endpoint=organizations/ORGANIZATION_ID/locations/us-central1-a/firewallEndpoints/endpoint-ips \\
  --network=prod-shared-vpc \\
  --zone=us-central1-a \\
  --project=network-host-prod
```

Create the global network firewall policy and inspection rule:

```cli
gcloud compute network-firewall-policies create shared-vpc-enterprise-policy \\
  --project=network-host-prod \\
  --global

gcloud compute network-firewall-policies rules create 100 \\
  --project=network-host-prod \\
  --firewall-policy=shared-vpc-enterprise-policy \\
  --global-firewall-policy \\
  --direction=INGRESS \\
  --action=APPLY_SECURITY_PROFILE_GROUP \\
  --src-ip-ranges=10.10.0.0/16 \\
  --dest-ip-ranges=10.20.0.0/16 \\
  --layer4-configs=tcp:443 \\
  --security-profile-group=SECURITY_PROFILE_GROUP_RESOURCE \\
  --enable-logging

gcloud compute network-firewall-policies associations create \\
  --project=network-host-prod \\
  --firewall-policy=shared-vpc-enterprise-policy \\
  --network=prod-shared-vpc \\
  --name=shared-vpc-enterprise-association \\
  --global-firewall-policy
```

When required by the interception design:

```cli
gcloud compute networks update prod-shared-vpc \\
  --project=network-host-prod \\
  --network-firewall-policy-enforcement-order=BEFORE_CLASSIC_FIREWALL
```

Firewall endpoints and endpoint associations are zonal; repeat coverage for each protected workload zone.
''',
    '## 10.1 Cloud NGFW Enterprise `gcloud` build',
)

insert_before(
    '# 12. Shared VPC + NCC Router Appliance',
    '''## 11.1 NSI consumer `gcloud` build

Assume the producer already exposes an intercept endpoint group.

```cli
gcloud network-security security-profiles custom-intercept create shared-vpc-nsi-profile \\
  --organization=ORGANIZATION_ID \\
  --location=global \\
  --billing-project=network-host-prod \\
  --intercept-endpoint-group=projects/ENDPOINT_GROUP_PROJECT_ID/locations/global/interceptEndpointGroups/ENDPOINT_GROUP_ID

gcloud network-security security-profile-groups create shared-vpc-nsi-spg \\
  --organization=ORGANIZATION_ID \\
  --location=global \\
  --billing-project=network-host-prod \\
  --custom-intercept-profile=shared-vpc-nsi-profile

gcloud compute network-firewall-policies create shared-vpc-nsi-policy \\
  --project=network-host-prod \\
  --global

gcloud compute network-firewall-policies rules create 100 \\
  --project=network-host-prod \\
  --firewall-policy=shared-vpc-nsi-policy \\
  --global-firewall-policy \\
  --action=APPLY_SECURITY_PROFILE_GROUP \\
  --security-profile-group=organizations/ORGANIZATION_ID/locations/global/securityProfileGroups/shared-vpc-nsi-spg \\
  --direction=INGRESS \\
  --src-ip-ranges=10.10.0.0/16 \\
  --dest-ip-ranges=10.20.0.0/16 \\
  --layer4-configs=tcp:443 \\
  --enable-logging

gcloud compute network-firewall-policies associations create \\
  --project=network-host-prod \\
  --firewall-policy=shared-vpc-nsi-policy \\
  --network=prod-shared-vpc \\
  --name=shared-vpc-nsi-association \\
  --global-firewall-policy
```

Verify effective policy:

```cli
gcloud compute networks get-effective-firewalls prod-shared-vpc \\
  --project=network-host-prod
```
''',
    '## 11.1 NSI consumer `gcloud` build',
)

insert_before(
    '# 13. Selective inspection with VM tags',
    '''## 12.1 Router Appliance + BGP `gcloud` build

Create NCC hub, Router Appliance spoke, and Cloud Router in the Shared VPC host project:

```cli
gcloud network-connectivity hubs create shared-vpc-security-hub \\
  --project=network-host-prod

gcloud network-connectivity spokes linked-router-appliances create shared-vpc-fw-spoke \\
  --project=network-host-prod \\
  --hub=shared-vpc-security-hub \\
  --region=us-central1 \\
  --router-appliance=instance='https://www.googleapis.com/compute/v1/projects/network-host-prod/zones/us-central1-a/instances/fw-router-a',ip=10.100.10.20 \\
  --router-appliance=instance='https://www.googleapis.com/compute/v1/projects/network-host-prod/zones/us-central1-b/instances/fw-router-b',ip=10.100.10.21

gcloud compute routers create shared-vpc-fw-cr \\
  --project=network-host-prod \\
  --network=prod-shared-vpc \\
  --region=us-central1 \\
  --asn=64514
```

Representative first BGP peer; use design-specific link-local IPs and ASNs and repeat for the second appliance:

```cli
gcloud compute routers add-interface shared-vpc-fw-cr \\
  --project=network-host-prod \\
  --region=us-central1 \\
  --interface-name=to-fw-a \\
  --ip-address=169.254.10.1 \\
  --mask-length=30

gcloud compute routers add-bgp-peer shared-vpc-fw-cr \\
  --project=network-host-prod \\
  --region=us-central1 \\
  --peer-name=fw-a \\
  --interface=to-fw-a \\
  --peer-ip-address=169.254.10.2 \\
  --peer-asn=65010
```

Verify:

```cli
gcloud network-connectivity spokes describe shared-vpc-fw-spoke --project=network-host-prod --region=us-central1
gcloud compute routers get-status shared-vpc-fw-cr --project=network-host-prod --region=us-central1
```

Cloud Router is the BGP control plane; the Router Appliance VM is the forwarding data plane.
''',
    '## 12.1 Router Appliance + BGP `gcloud` build',
)

p.write_text(s)
