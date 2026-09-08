from pathlib import Path
p=Path('09-07-26_GCP_Shared_VPC_Centralized_Firewall_Insertion_Method_11_Deep_Dive.md')
s=p.read_text()
start='## 12.1 Router Appliance + BGP `gcloud` build\n'
end='\n---\n\n# 13. Selective inspection with VM tags\n'
a=s.index(start); b=s.index(end,a)
new='''## 12.1 Router Appliance + BGP `gcloud` build

Create the NCC hub, Router Appliance spoke, and Cloud Router in the Shared VPC **host project**:

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

For Router Appliance, the Cloud Router interfaces use **RFC1918 addresses from the appliance subnet**, not HA-VPN-style link-local addresses. Create a redundant interface pair in `firewall-subnet`:

```cli
gcloud compute routers add-interface shared-vpc-fw-cr \\
  --project=network-host-prod \\
  --region=us-central1 \\
  --interface-name=router-appliance-interface-0 \\
  --ip-address=10.100.10.5 \\
  --subnetwork=firewall-subnet

gcloud compute routers add-interface shared-vpc-fw-cr \\
  --project=network-host-prod \\
  --region=us-central1 \\
  --interface-name=router-appliance-interface-1 \\
  --ip-address=10.100.10.6 \\
  --subnetwork=firewall-subnet \\
  --redundant-interface=router-appliance-interface-0
```

Create BGP sessions to `fw-router-a`. The peer address is the appliance VM's **primary internal IP on nic0**, and the BGP peer explicitly identifies the Router Appliance VM and zone:

```cli
gcloud compute routers add-bgp-peer shared-vpc-fw-cr \\
  --project=network-host-prod \\
  --region=us-central1 \\
  --peer-name=fw-router-a-peer-0 \\
  --interface=router-appliance-interface-0 \\
  --peer-ip-address=10.100.10.20 \\
  --peer-asn=65010 \\
  --instance=fw-router-a \\
  --instance-zone=us-central1-a

gcloud compute routers add-bgp-peer shared-vpc-fw-cr \\
  --project=network-host-prod \\
  --region=us-central1 \\
  --peer-name=fw-router-a-peer-1 \\
  --interface=router-appliance-interface-1 \\
  --peer-ip-address=10.100.10.20 \\
  --peer-asn=65010 \\
  --instance=fw-router-a \\
  --instance-zone=us-central1-a
```

Create equivalent BGP peers for `fw-router-b`, using its primary internal IP `10.100.10.21`, its zone `us-central1-b`, and its configured private ASN, for example `65011`.

Verify the NCC spoke and Cloud Router BGP state:

```cli
gcloud network-connectivity spokes describe shared-vpc-fw-spoke \\
  --project=network-host-prod \\
  --region=us-central1

gcloud compute routers get-status shared-vpc-fw-cr \\
  --project=network-host-prod \\
  --region=us-central1
```

**Success criteria:** the Router Appliance spoke is active, the expected BGP peers are established, and the intended prefixes are learned and advertised through the appliances.

**Control-plane reminder:** Cloud Router exchanges routes; the Router Appliance VM forwards and inspects packets.

**Important:** the interface addresses, appliance addresses, and private ASNs above are examples. They must be replaced with values that match the actual appliance subnet and vendor BGP configuration.
'''
s=s[:a]+new+s[b:]
p.write_text(s)
