# Azure Virtual WAN Security SaaS Provider — Method 6 Deep Dive

> **Scope:** Azure Virtual WAN + Azure Firewall Manager **Security Partner Provider** integration for Internet/SaaS inspection.  
> **Important naming note:** Microsoft uses **Security Partner Provider** / **Security as a Service (SECaaS)** for this model. It is **not the same** as a third-party firewall VM, an Integrated NVA, or a SaaS NGFW deployed directly into the Virtual WAN hub.

## URLs reviewed

### Primary Microsoft documentation

- https://learn.microsoft.com/en-us/azure/firewall-manager/trusted-security-partners
- https://learn.microsoft.com/en-us/azure/firewall-manager/deploy-trusted-security-partner
- https://learn.microsoft.com/en-us/azure/firewall-manager/overview
- https://learn.microsoft.com/en-us/azure/virtual-wan/third-party-integrations
- https://learn.microsoft.com/en-us/azure/virtual-wan/virtual-wan-about
- https://learn.microsoft.com/en-us/azure/networking/design-guide/virtual-wan
- https://learn.microsoft.com/en-us/azure/architecture/networking/architecture/hub-spoke-virtual-wan-architecture
- https://learn.microsoft.com/en-us/rest/api/virtualwan/supported-security-providers/supported-security-providers?view=rest-virtualwan-2025-05-01
- https://learn.microsoft.com/en-us/cli/azure/network/security-partner-provider?view=azure-cli-latest
- https://learn.microsoft.com/en-us/cli/azure/network/vwan?view=azure-cli-latest
- https://learn.microsoft.com/en-us/cli/azure/network/vhub?view=azure-cli-latest
- https://learn.microsoft.com/en-us/cli/azure/network/vhub/connection?view=azure-cli-latest
- https://learn.microsoft.com/en-us/cli/azure/network/vpn-gateway?view=azure-cli-latest

### Provider documentation

- https://help.zscaler.com/zia/integrating-microsoft-azure-virtual-wan
- https://help.zscaler.com/zia/about-partner-integrations

## Table of contents

- [1. Executive summary](#1-executive-summary)
  - [1.1 Current supported Security Partner Providers](#11-current-supported-security-partner-providers)
- [2. Architecture: what is actually inserted](#2-architecture-what-is-actually-inserted)
- [3. Do not confuse three Virtual WAN third-party integration models](#3-do-not-confuse-three-virtual-wan-third-party-integration-models)
- [4. Prerequisites and dependencies](#4-prerequisites-and-dependencies)
  - [4.1 Azure CLI prerequisites](#41-azure-cli-prerequisites)
- [5. Control plane: how the secured default route appears](#5-control-plane-how-the-secured-default-route-appears)
  - [5.1 Query the live provider list for your Virtual WAN](#51-query-the-live-provider-list-for-your-virtual-wan)
  - [5.2 Inspect VNet-connection effective routes](#52-inspect-vnet-connection-effective-routes)
- [6. VNet-to-Internet packet flow — minute detail](#6-vnet-to-internet-packet-flow--minute-detail)
- [7. Branch-to-Internet packet flow](#7-branch-to-internet-packet-flow)
- [8. Two-security-provider design: SECaaS for Internet, Azure Firewall for private traffic](#8-two-security-provider-design-secaas-for-internet-azure-firewall-for-private-traffic)
- [9. Routing Intent versus Security Partner Provider semantics](#9-routing-intent-versus-security-partner-provider-semantics)
- [10. Public IP ranges used internally](#10-public-ip-ranges-used-internally)
- [11. Configuration workflow](#11-configuration-workflow)
  - [11.1 Create the Standard Virtual WAN and vHub](#111-create-the-standard-virtual-wan-and-vhub)
  - [11.2 Deploy the required vHub S2S VPN Gateway](#112-deploy-the-required-vhub-s2s-vpn-gateway)
  - [11.3 Discover supported providers before creating the resource](#113-discover-supported-providers-before-creating-the-resource)
  - [11.4 Create the Security Partner Provider resource](#114-create-the-security-partner-provider-resource)
  - [11.5 Connect a spoke and enable Internet security](#115-connect-a-spoke-and-enable-internet-security)
  - [11.6 Complete provider-side onboarding](#116-complete-provider-side-onboarding)
- [12. Zscaler-specific current limitations to validate](#12-zscaler-specific-current-limitations-to-validate)
- [13. High availability, failure, and convergence](#13-high-availability-failure-and-convergence)
- [14. Verification checklist and Azure CLI](#14-verification-checklist-and-azure-cli)
- [15. Troubleshooting by symptom](#15-troubleshooting-by-symptom)
- [16. Common mistakes](#16-common-mistakes)
- [17. Official Microsoft architecture image](#17-official-microsoft-architecture-image)
- [18. Design decision table](#18-design-decision-table)
- [19. Recommended reference architecture](#19-recommended-reference-architecture)
- [20. Final takeaways](#20-final-takeaways)
- [Sources](#sources)

---

## 1. Executive summary

**Source information:** Azure Firewall Manager can connect a Virtual WAN secured hub to a supported third-party SECaaS provider for **VNet-to-Internet (V2I)** and **Branch-to-Internet (B2I)** filtering. Azure automates route management so selected hub connections can receive a secured default route without the normal requirement to build spoke-subnet UDRs for this service insertion.

The most important architectural fact is that the Security Partner Provider infrastructure is **not a firewall VM inside your subscription or VNet**. In this model, the security service remains provider-hosted and the Azure Virtual WAN hub reaches it through the hub's **Site-to-Site (S2S) VPN Gateway** over IPsec.

**Additional explanation:** Think of Method 6 as **route-based redirection to an external cloud security service**. Azure Virtual WAN supplies transit and route programming; the hub S2S VPN gateway supplies the service tunnel; the provider supplies the Internet/SaaS inspection and provider-side egress.

### 1.1 Current supported Security Partner Providers

As of the current Microsoft Firewall Manager documentation, the dedicated **Security Partner Provider** page and the current deployment guide identify:

| Provider | Current Method 6 status | Notes |
|---|---|---|
| **Zscaler** | **Currently documented as supported** | Current Firewall Manager concept and deployment pages list Zscaler. |
| Check Point | **Do not assume current deployment support** | Older generic Virtual WAN documentation and the current CLI enum still contain `Checkpoint`, but the current dedicated Firewall Manager deployment page does not list it. |
| iboss | **Do not assume current deployment support** | Older generic Virtual WAN documentation and the current CLI enum still contain `IBoss`, but the current dedicated Firewall Manager deployment page does not list it. |

This documentation mismatch is important:

- the current dedicated Firewall Manager page says **“The current supported security partner is Zscaler”**;
- the current Security Partner Provider deployment page lists **Zscaler** only;
- the older generic Virtual WAN third-party integration page still says **Check Point, iboss, and Zscaler**;
- the current Preview Azure CLI command still accepts `Checkpoint`, `IBoss`, and `ZScaler` as enum values.

**Deployment rule:** do not treat an old documentation table or CLI enum as proof that a provider can be deployed in your subscription/region. Query the live `supportedSecurityProviders` API for your specific Virtual WAN and confirm current provider documentation before production deployment.

Also keep this separate from **Virtual WAN SaaS solutions**. Microsoft currently identifies **Palo Alto Networks Cloud NGFW** as a SaaS solution deployed directly into the vHub model. That is **not Method 6** and does not use the external Firewall Manager Security Partner Provider/IPsec architecture described here.

---

## 2. Architecture: what is actually inserted

![Method 6 architecture](images/09-05-26-16-44_method6_architecture.svg)

[Editable draw.io diagram](images/09-05-26-16-44_method6_architecture.drawio)

**What this image shows:** Spoke VNets and branches converge on a Virtual WAN hub. Internet traffic is selected by the secured-hub configuration and forwarded to the provider through the vHub S2S VPN gateway.

**What matters:** SECaaS is **external to the vHub**. Microsoft explicitly states that Security Partner Providers connect through VPN Gateway tunnels and that deleting the VPN Gateway breaks those connections.

**What to verify:** Hub provisioned state, provider security connection, S2S tunnel state, VNet/branch Internet-security opt-in, secured `0.0.0.0/0` route behavior, and provider traffic logs.

### Layer and plane placement

| Area | Role in Method 6 |
|---|---|
| Layer 2 | No customer-controlled L2 insertion. Virtual WAN is routed transit. |
| Layer 3 | Service insertion is route-driven, primarily around `0.0.0.0/0` for Internet traffic. |
| Control plane | Firewall Manager / Virtual WAN programs secured routing; provider onboarding synchronizes hub information and tunnel configuration. |
| Data plane | Packet traverses vHub routing → S2S VPN Gateway → IPsec → provider service → Internet/SaaS. |
| Security policy plane | Internet security rules are configured in the provider's management plane. |
| Optional private firewall | Azure Firewall can inspect private traffic while SECaaS owns Internet traffic. |

---

## 3. Do not confuse three Virtual WAN third-party integration models

![Integration model comparison](images/09-05-26-16-44_method6_integration_model_comparison.svg)

[Editable draw.io diagram](images/09-05-26-16-44_method6_integration_model_comparison.drawio)

**What this image shows:** Microsoft documents Integrated NVAs, SaaS solutions deployed into the vHub, and Firewall Manager Security Partner Providers as distinct models.

**What matters:** Method 6 is specifically the **Firewall Manager Security Partner Provider** architecture. A product described as a “SaaS firewall” is not automatically using this integration model.

**What to verify:** Confirm the vendor's exact Virtual WAN integration class before carrying over routing, HA, licensing, NAT, scale, or traffic-class assumptions.

| Model | Where security runs | Attachment | Typical purpose |
|---|---|---|---|
| Firewall Manager Security Partner Provider | Provider-hosted SECaaS outside vHub | S2S IPsec VPN from vHub | VNet/Branch Internet and SaaS filtering |
| Virtual WAN SaaS solution | SaaS security solution deployed directly into vHub model | Native Virtual WAN SaaS integration | NGFW inspection; Microsoft currently cites Palo Alto Networks Cloud NGFW |
| Integrated NVA | Integrated appliance in Virtual WAN hub architecture | Microsoft/vendor integrated lifecycle | Connectivity and/or NGFW depending on vendor |

---

## 4. Prerequisites and dependencies

**Source information:** Microsoft's deployment procedure tells you to include a **VPN Gateway** when enabling Security Partner Providers. The partner integration depends on that gateway for its tunnels.

Minimum design dependencies:

1. Azure Virtual WAN with a compatible **Standard** virtual hub.
2. A Virtual WAN **S2S VPN Gateway** in the hub.
3. A currently supported Security Partner Provider for the specific Virtual WAN/region.
4. Provider subscription/entitlement and tenant.
5. Microsoft Entra credentials/information required by the provider integration workflow.
6. Successful provider discovery/synchronization of the Azure vHub.
7. Provider tunnel status **Connected**.
8. Firewall Manager security configuration selecting the provider for Internet traffic.
9. Explicit VNet and/or branch connection opt-in for secured Internet routing.
10. Provider-side policy that permits the desired traffic.

### Why the S2S VPN Gateway is mandatory

**Source information:** Security Partner Providers connect to the hub using VPN Gateway tunnels. Microsoft warns that deleting the gateway removes the provider connections.

**Additional explanation:** This is one of the easiest ways to distinguish Method 6 from a SaaS NGFW directly deployed into the Virtual WAN hub.

### 4.1 Azure CLI prerequisites

The vHub and VPN Gateway command families are supplied by the `virtual-wan` extension in current Azure CLI releases. The extension auto-installs when required, but for repeatable automation you can explicitly update it:

```cli
az version
az extension add --name virtual-wan --upgrade
az account show --output table
```

Recommended variables used below:

```cli
RG='RG-Network'
LOCATION='eastus'
VWAN='Corp-vWAN'
VHUB='Hub-East'
VHUB_PREFIX='10.250.0.0/24'
VPNGW='Hub-East-VPNGW'
SEC_PROVIDER_RESOURCE='secpartner-zscaler-east'
SPOKE_VNET='Spoke-App-East'
SPOKE_CONN='conn-spoke-app-east'
```

---

## 5. Control plane: how the secured default route appears

The key routing question is: **how does a spoke or branch learn that Internet traffic must go to SECaaS?**

Microsoft documents that:

- The security-partner deployment causes a `0.0.0.0/0` default-route relationship to be created toward the secured service path.
- Merely connecting the provider does **not** automatically mean every VNet/site receives that default route.
- You select which connections are secured/opted in.
- Microsoft specifically warns **not to manually advertise `0.0.0.0/0` over BGP from branches** just to force this behavior, because doing so can interfere with the security-provider deployment.

![Control-plane troubleshooting](images/09-05-26-16-44_method6_control_plane_troubleshooting.svg)

[Editable draw.io diagram](images/09-05-26-16-44_method6_control_plane_troubleshooting.drawio)

**What this image shows:** Provider onboarding, tunnel establishment, route distribution, and the observability points on both Azure and provider sides.

**What matters:** A healthy packet path is impossible if the control plane never distributes the secured default route.

**What to verify:** Azure security-connection state, VPN tunnel state, connection Internet-security setting, effective route behavior, provider hub synchronization, provider location/tunnel object, policy attachment, and provider logs.

### Simulated route example

The following is explanatory, not vendor command output:

```text
Workload: 10.10.1.10
Destination: 8.8.8.8

More-specific private route: no match
Default route: 0.0.0.0/0
Selected path: Virtual WAN secured Internet path
Service next hop: Security Partner Provider
Transport from vHub to provider: S2S VPN Gateway / IPsec
```

### 5.1 Query the live provider list for your Virtual WAN

The Virtual WAN REST API exposes `supportedSecurityProviders`. This is the best Azure-side deployment-time check when documentation and CLI enums disagree.

```cli
SUBSCRIPTION_ID=$(az account show --query id -o tsv)

az rest \
  --method get \
  --url "https://management.azure.com/subscriptions/${SUBSCRIPTION_ID}/resourceGroups/${RG}/providers/Microsoft.Network/virtualWans/${VWAN}/supportedSecurityProviders?api-version=2025-05-01" \
  --output jsonc
```

To display only provider names/types:

```cli
az rest \
  --method get \
  --url "https://management.azure.com/subscriptions/${SUBSCRIPTION_ID}/resourceGroups/${RG}/providers/Microsoft.Network/virtualWans/${VWAN}/supportedSecurityProviders?api-version=2025-05-01" \
  --query "supportedProviders[].{name:name,type:type,url:url}" \
  --output table
```

**What it tests:** providers Azure reports as supported for the specified Virtual WAN/API context.

**Success criteria:** the intended provider appears and is also supported by current provider/Microsoft deployment documentation for the target region/subscription.

**Failure indicator:** the provider is absent. Do not force creation merely because `az network security-partner-provider create --help` still accepts its name.

### 5.2 Inspect VNet-connection effective routes

After the provider is connected and Internet security is enabled on the spoke connection, inspect what the vHub is actually advertising/using for that connection:

```cli
SPOKE_CONN_ID=$(az network vhub connection show \
  --resource-group "$RG" \
  --vhub-name "$VHUB" \
  --name "$SPOKE_CONN" \
  --query id -o tsv)

az network vhub get-effective-routes \
  --resource-group "$RG" \
  --name "$VHUB" \
  --resource-type HubVirtualNetworkConnection \
  --resource-id "$SPOKE_CONN_ID" \
  --output table
```

**What it tests:** actual vHub forwarding state for the selected connection rather than intended configuration alone.

**Success criteria:** the secured default-route behavior expected for the provider-enabled connection is present. Validate the actual returned fields rather than relying on a fabricated fixed output sample.

---

## 6. VNet-to-Internet packet flow — minute detail

![VNet-to-Internet flow](images/09-05-26-16-44_method6_vnet_internet_packet_flow.svg)

[Editable draw.io diagram](images/09-05-26-16-44_method6_vnet_internet_packet_flow.drawio)

**What this image shows:** An Azure workload reaching a public destination through the external SECaaS provider.

**What matters:** The vHub does not host the SECaaS firewall in Method 6. It routes to the VPN gateway/provider tunnel after choosing the secured Internet path.

**What to verify:** Secured default route, lack of unintended bypass, tunnel status, provider logs, policy action, and return traffic.

### Packet walk

1. A workload, for example `10.10.1.10`, opens a connection to a public destination.
2. The workload/VNet route lookup uses the Virtual WAN-connected path for Internet traffic.
3. The vHub sees the Internet destination and uses the secured default path selected by Firewall Manager.
4. The vHub forwards the packet to its S2S VPN gateway.
5. The gateway encrypts the traffic into the IPsec service tunnel toward the provider.
6. The provider receives the packet and applies its Internet/SaaS security policy.
7. Depending on provider capability and licensing, inspection can include SWG policy, URL categorization, application controls, user-aware controls, threat inspection, and TLS inspection.
8. If allowed, the provider sends the connection toward the Internet/SaaS destination.
9. Return traffic reaches the provider service edge.
10. Provider state/routing returns the packet through the Azure service tunnel.
11. The S2S VPN gateway decapsulates it and returns it to vHub routing.
12. The vHub forwards it to the originating spoke VNet.

### NAT consideration

**Source information:** Microsoft documents the route/service integration but does not define one universal SECaaS public-source-NAT behavior for all partners.

**Reasonable inference:** The public source IP visible to the Internet is provider-specific. Do not assume it is an Azure Firewall public IP or the original workload IP. Validate provider egress/NAT behavior and test the observed public source address.

---

## 7. Branch-to-Internet packet flow

![Branch-to-Internet flow](images/09-05-26-16-44_method6_branch_internet_packet_flow.svg)

[Editable draw.io diagram](images/09-05-26-16-44_method6_branch_internet_packet_flow.drawio)

**What this image shows:** A branch uses Azure Virtual WAN as transit and sends non-bypassed Internet traffic from its regional hub to SECaaS.

**What matters:** Microsoft recommends direct/local breakout for key Microsoft 365 traffic rather than hairpinning those flows through an Azure secured hub.

**What to verify:** Branch routing, hub association, secured default route receipt, local M365 breakout policy, provider tunnel health, service-edge selection, and provider logs.

### Branch packet walk

1. Branch client initiates an Internet flow.
2. Branch SD-WAN/router sends non-locally-broken-out traffic to its Azure Virtual WAN connectivity path.
3. Traffic enters the regional vHub.
4. Secured Internet routing selects the Security Partner Provider.
5. vHub forwards to the S2S VPN gateway.
6. IPsec carries traffic to the provider cloud.
7. Provider applies security policy and egresses permitted traffic.
8. Return traffic follows provider state/routing back through the tunnel and vHub to the branch.

### Microsoft 365 handling

Microsoft's security-partner guidance recommends that globally distributed branches send key Microsoft 365 connectivity **directly and locally** to the Microsoft network before steering remaining Internet traffic through the Azure secured hub. The rationale is latency, performance, and the characteristics of encrypted Microsoft 365 connections.

---

## 8. Two-security-provider design: SECaaS for Internet, Azure Firewall for private traffic

![Dual-provider split](images/09-05-26-16-44_method6_dual_provider_split.svg)

[Editable draw.io diagram](images/09-05-26-16-44_method6_dual_provider_split.drawio)

**What this image shows:** The supported split in which the Security Partner Provider handles Internet/SaaS traffic while Azure Firewall handles private traffic.

**What matters:** This is a **traffic-class split**, not arbitrary per-prefix chaining between unrelated firewall products.

**What to verify:** Firewall Manager security configuration assigns Internet traffic to the trusted provider and private traffic to Azure Firewall.

| Flow | Typical inspection owner in this design |
|---|---|
| Spoke VNet → Internet | Security Partner Provider |
| Branch → Internet | Security Partner Provider |
| Spoke VNet → Spoke VNet | Azure Firewall |
| Branch → Spoke VNet | Azure Firewall |
| Spoke VNet → Branch | Azure Firewall |
| Internet ingress to private workload | Not the primary Security Partner Provider use case; design separately |

### Why this matters for east-west inspection

A Security Partner Provider is **not automatically a full east-west stateful firewall replacement**. Microsoft's Security Partner Provider scenarios are centered on Internet filtering. If the requirement is “all private VNet-to-VNet or branch-to-VNet traffic must traverse a third-party NGFW,” choose a security model that actually owns the private traffic class, such as Azure Firewall, an appropriate Virtual WAN NVA/SaaS security integration, or another documented service-insertion architecture.

---

## 9. Routing Intent versus Security Partner Provider semantics

Modern Virtual WAN Routing Intent exposes private and Internet traffic policies with a single security next hop for each class, but the exact supported next-hop model depends on the integration type.

**Additional explanation:** For Method 6, operationally focus on Firewall Manager's Security Partner Provider workflow and its automatic secured-Internet route distribution. Do not assume every feature documented for an in-hub NVA or SaaS NGFW applies one-for-one to the external SECaaS VPN model.

**CLI caution:** do not invent a Routing Intent next-hop value for a Security Partner Provider. The supported Method 6 deployment workflow is represented by the Security Partner Provider resource plus Firewall Manager security configuration. Use the specific provider/Firewall Manager workflow documented for the service.

---

## 10. Public IP ranges used internally

If your organization uses publicly routable-looking addresses internally in VNets or branches, Microsoft says to add them explicitly as **Private Traffic Prefixes** so they are not treated as Internet destinations.

Example:

```text
Corporate internal prefix: 198.51.100.0/24
Intent: private enterprise routing
Action: add to Private Traffic Prefixes
```

If Azure Firewall handles the private traffic class, also review its SNAT behavior for non-RFC1918 destinations because Azure Firewall normally treats such addresses differently from RFC1918 private space unless configured otherwise.

---

## 11. Configuration workflow

### 11.1 Create the Standard Virtual WAN and vHub

```cli
az network vwan create \
  --resource-group "$RG" \
  --name "$VWAN" \
  --location "$LOCATION" \
  --type Standard

az network vhub create \
  --resource-group "$RG" \
  --name "$VHUB" \
  --vwan "$VWAN" \
  --location "$LOCATION" \
  --address-prefix "$VHUB_PREFIX" \
  --sku Standard
```

Verify:

```cli
az network vwan show \
  --resource-group "$RG" \
  --name "$VWAN" \
  --output yaml

az network vhub show \
  --resource-group "$RG" \
  --name "$VHUB" \
  --output yaml
```

**Success criteria:** Standard vWAN, intended region/address prefix, and successful vHub provisioning.

### 11.2 Deploy the required vHub S2S VPN Gateway

Method 6 requires the vHub S2S VPN Gateway because the security partner builds service tunnels through it.

```cli
az network vpn-gateway create \
  --resource-group "$RG" \
  --name "$VPNGW" \
  --vhub "$VHUB" \
  --location "$LOCATION" \
  --scale-unit 2
```

Verify:

```cli
az network vpn-gateway show \
  --resource-group "$RG" \
  --name "$VPNGW" \
  --output yaml
```

**Important:** choose a scale unit based on current bandwidth/capacity requirements. The value `2` above is an example, not a universal recommendation.

### 11.3 Discover supported providers before creating the resource

```cli
SUBSCRIPTION_ID=$(az account show --query id -o tsv)

az rest \
  --method get \
  --url "https://management.azure.com/subscriptions/${SUBSCRIPTION_ID}/resourceGroups/${RG}/providers/Microsoft.Network/virtualWans/${VWAN}/supportedSecurityProviders?api-version=2025-05-01" \
  --query "supportedProviders[].{name:name,type:type,url:url}" \
  --output table
```

Do this **before** trusting the provider choices exposed by the CLI command itself.

### 11.4 Create the Security Partner Provider resource

The current Azure CLI has a dedicated command group:

```text
az network security-partner-provider
```

**CLI status warning:** this command group is currently **Preview**. Microsoft documents the accepted enum values as `Checkpoint`, `IBoss`, and `ZScaler`, but the current dedicated Firewall Manager documentation lists **Zscaler** as the current supported Security Partner Provider. Therefore, an accepted CLI enum value is not proof of current service availability.

For the currently documented Zscaler path:

```cli
az network security-partner-provider create \
  --resource-group "$RG" \
  --name "$SEC_PROVIDER_RESOURCE" \
  --location "$LOCATION" \
  --vhub "$VHUB" \
  --provider ZScaler
```

Inspect the resource:

```cli
az network security-partner-provider show \
  --resource-group "$RG" \
  --name "$SEC_PROVIDER_RESOURCE" \
  --output yaml
```

List all provider resources in the resource group:

```cli
az network security-partner-provider list \
  --resource-group "$RG" \
  --output table
```

You can also wait for Azure resource creation state:

```cli
az network security-partner-provider wait \
  --resource-group "$RG" \
  --name "$SEC_PROVIDER_RESOURCE" \
  --created
```

**What these commands do not complete:** provider-side tenant onboarding, service-principal authorization, tunnel/service-edge creation, and security policy remain part of the provider workflow.

### 11.5 Connect a spoke and enable Internet security

Virtual WAN uses a **vHub VNet connection**, not VNet peering to the managed hub.

```cli
SPOKE_VNET_ID=$(az network vnet show \
  --resource-group "$RG" \
  --name "$SPOKE_VNET" \
  --query id -o tsv)

az network vhub connection create \
  --resource-group "$RG" \
  --vhub-name "$VHUB" \
  --name "$SPOKE_CONN" \
  --remote-vnet "$SPOKE_VNET_ID" \
  --internet-security true
```

For an existing connection:

```cli
az network vhub connection update \
  --resource-group "$RG" \
  --vhub-name "$VHUB" \
  --name "$SPOKE_CONN" \
  --internet-security true
```

Verify:

```cli
az network vhub connection show \
  --resource-group "$RG" \
  --vhub-name "$VHUB" \
  --name "$SPOKE_CONN" \
  --query "{name:name,internetSecurity:enableInternetSecurity,remoteVnet:remoteVirtualNetwork.id,provisioningState:provisioningState}" \
  --output yaml
```

**Note:** branch/site secured-Internet selection must be validated against the current Firewall Manager/Virtual WAN configuration surface. Do not invent a branch CLI flag simply because VNet connections expose `--internet-security`.

### 11.6 Complete provider-side onboarding

Current Zscaler documentation describes a workflow that includes:

1. Open the Azure Virtual WAN partner integration in the Zscaler admin portal.
2. Supply Azure application/client credentials plus tenant and subscription information.
3. Test the Azure integration.
4. Sync/discover eligible Azure hubs.
5. Provision the provider location/tunnel configuration.
6. Wait for tunnel status to show connected in both Azure and the provider portal.
7. Configure the provider security policy and Internet egress behavior.

Microsoft states that the provider creates a VPN site on your behalf and that this provider-created VPN site does **not** appear in the Azure portal like a normal customer-created VPN site.

### Management warning

Once the secured default route is installed, assumptions about direct RDP/SSH can break. Microsoft recommends a deliberate management path such as Azure Bastion/private connectivity rather than creating a casual Internet-security bypass.

---

## 12. Zscaler-specific current limitations to validate

The following come from the cited Zscaler Azure Virtual WAN integration documentation and are **provider-specific**, not universal Virtual WAN limitations:

- Redundant tunnels are documented as unsupported; Zscaler describes one outbound tunnel from an Azure Virtual WAN hub to a Zscaler tenant.
- Azure Government is documented as unsupported for this integration.
- Zscaler documents no failover to a different Zscaler data center based on unavailability/load in this integration because redundant tunnels are not supported.
- Sublocations are not supported; Zscaler locations are used.
- The integration has provider-documented tenancy/cloud constraints that must be validated before multitenant or multi-subscription design.
- Zscaler recommends BGP rather than relying on static-route propagation in the documented Virtual WAN scenario.

> **Version caution:** Re-check vendor documentation before production deployment. Partner limits can change independently of Azure Virtual WAN.

---

## 13. High availability, failure, and convergence

End-to-end availability depends on every component in this chain:

```text
Spoke/branch
  → Virtual WAN connection and route programming
  → vHub routing
  → vHub S2S VPN Gateway
  → IPsec service tunnel
  → provider security edge
  → provider policy/egress
  → Internet/SaaS destination
```

| Failure | Likely effect | First checks |
|---|---|---|
| Provider tunnel down | Secured Internet traffic fails/blackholes according to design/provider behavior | Azure and provider tunnel state |
| Provider policy deny | Routing works but application fails | Provider logs/policy |
| VNet/branch not opted in | No expected secured default route | Hub security configuration/effective routes |
| Public-looking corporate prefix misclassified | Corporate flow sent toward Internet security | Private Traffic Prefixes |
| Azure Firewall private-policy issue | East-west/hybrid fails while Internet may still work | Azure Firewall policy/private traffic configuration |
| Manual branch `0/0` advertisement | Route conflicts or provider deployment problems | Branch BGP advertisements |
| Provider API credentials invalid | Hub sync/onboarding fails | Provider integration test and Entra permissions |

### Convergence

**Source information:** Microsoft documents automated routing and tunnel status but does not publish one universal failover time across all partner failure modes.

**Reasonable inference:** Recovery time depends on IPsec liveness, Azure route state, provider service-edge behavior, provider policy propagation, and application TCP/TLS retry. Test actual failure and recovery in pre-production rather than assuming BFD-like subsecond convergence.

---

## 14. Verification checklist and Azure CLI

### 14.1 Verify the Azure resources

```cli
az network vhub show \
  --resource-group "$RG" \
  --name "$VHUB" \
  --query "{name:name,location:location,provisioningState:provisioningState,virtualWan:virtualWan.id}" \
  --output yaml

az network vpn-gateway show \
  --resource-group "$RG" \
  --name "$VPNGW" \
  --output yaml

az network security-partner-provider show \
  --resource-group "$RG" \
  --name "$SEC_PROVIDER_RESOURCE" \
  --output yaml
```

**Success criteria:** Azure resources are provisioned, the provider resource points at the intended vHub, and the vHub VPN gateway exists.

### 14.2 Verify spoke Internet-security opt-in

```cli
az network vhub connection show \
  --resource-group "$RG" \
  --vhub-name "$VHUB" \
  --name "$SPOKE_CONN" \
  --output yaml
```

Check `enableInternetSecurity`/the current equivalent property returned by the API.

### 14.3 Verify vHub effective routing

```cli
SPOKE_CONN_ID=$(az network vhub connection show \
  --resource-group "$RG" \
  --vhub-name "$VHUB" \
  --name "$SPOKE_CONN" \
  --query id -o tsv)

az network vhub get-effective-routes \
  --resource-group "$RG" \
  --name "$VHUB" \
  --resource-type HubVirtualNetworkConnection \
  --resource-id "$SPOKE_CONN_ID" \
  --output table
```

### 14.4 Verify the workload NIC route view

If you know the VM NIC:

```cli
az network nic show-effective-route-table \
  --resource-group RG-App \
  --name NIC-App01 \
  --output table
```

**Success criteria:** the workload no longer follows an unintended direct Internet route for traffic that is supposed to use the secured provider path.

### 14.5 Verify one concrete public destination

```cli
az network watcher show-next-hop \
  --resource-group RG-App \
  --vm App01 \
  --nic NIC-App01 \
  --source-ip 10.10.1.10 \
  --dest-ip 8.8.8.8 \
  --output table
```

Treat this as one Azure-routing observation, not as proof that the provider inspected the session. Correlate with provider logs.

### 14.6 Provider and workload checks

Provider-side verify:

- Azure credential/API integration succeeds;
- correct vHub is discovered;
- provider location/tunnel object exists;
- tunnel is active;
- correct security policy is assigned;
- logs show the expected source/destination;
- policy action is expected;
- egress service edge/region is expected.

Workload tests:

```cli
nslookup example.com
curl -I https://example.com
```

Windows:

```cli
tracert 8.8.8.8
```

Linux:

```cli
traceroute 8.8.8.8
```

Traceroute through a cloud security service or encrypted tunnel can be incomplete. Correlate workload timestamp, destination, Azure route/tunnel state, provider logs, and observed public egress IP for definitive validation.

---

## 15. Troubleshooting by symptom

### VNet has Internet but provider sees no logs

**Where:** Spoke effective routes and vHub security configuration.  
**CLI:**

```cli
az network vhub connection show -g "$RG" --vhub-name "$VHUB" -n "$SPOKE_CONN" -o yaml
az network nic show-effective-route-table -g RG-App -n NIC-App01 -o table
```

**What it tests:** Whether the connection actually received the secured Internet path.  
**Success:** Internet traffic is on the intended secured path and the provider sees a matching session.  
**Failure means:** Bypass or incomplete security configuration.  
**Next action:** Correct Internet-security opt-in and check competing UDRs/routes.

### VNet loses Internet immediately after enabling Method 6

**Where:** provider resource, vHub VPN gateway, provider portal.  
**CLI:**

```cli
az network security-partner-provider show -g "$RG" -n "$SEC_PROVIDER_RESOURCE" -o yaml
az network vpn-gateway show -g "$RG" -n "$VPNGW" -o yaml
```

**Tests:** Whether the default route was installed before a working provider tunnel/policy existed.  
**Success:** Azure resources are healthy, the provider tunnel is Connected in Azure/provider observability, and provider policy permits the test flow.  
**Failure means:** Secured route exists but the service path is broken.  
**Next action:** Restore tunnel/provider policy or temporarily remove the affected connection from secured Internet routing while troubleshooting.

### Provider name is accepted by CLI but deployment fails

**Where:** provider discovery.  
**CLI:**

```cli
az network security-partner-provider create --help

az rest \
  --method get \
  --url "https://management.azure.com/subscriptions/${SUBSCRIPTION_ID}/resourceGroups/${RG}/providers/Microsoft.Network/virtualWans/${VWAN}/supportedSecurityProviders?api-version=2025-05-01" \
  --output jsonc
```

**What it tests:** whether you are relying on the broader CLI enum rather than current service availability.  
**Failure means:** the CLI schema and current deployable provider set differ.  
**Next action:** use the current dedicated Microsoft/provider documentation and live API response; do not force an unsupported provider.

### Branch cannot reach Internet but spokes can

**Where:** Branch routing, Virtual WAN connection, local SD-WAN policy.  
**Tests:** Whether the branch enters the same secured path and receives the intended default.  
**Success:** Non-bypassed branch Internet traffic reaches SECaaS.  
**Failure means:** Branch-specific routing or local-breakout issue.  
**Next action:** Compare branch route/connection state with a working spoke and verify no manually advertised `0.0.0.0/0` conflicts with the provider workflow.

### SaaS performance is poor

**Where:** Provider service-edge selection, vHub region, branch geography.  
**Tests:** Whether traffic hairpins through a distant hub/provider edge.  
**Success:** Regional vHub/provider edge is reasonably close.  
**Failure means:** Excess centralization latency.  
**Next action:** Re-evaluate regional hubs and direct breakout for performance-sensitive services such as Microsoft 365.

### Corporate public-address prefix goes to SECaaS

**Where:** **Private Traffic Prefixes**.  
**Tests:** Classification of non-RFC1918 internal space.  
**Success:** Enterprise public-looking prefix is explicitly private.  
**Failure means:** Destination is treated as Internet.  
**Next action:** Add the private prefix and review Azure Firewall SNAT if Azure Firewall owns private traffic.

### Provider integration will not sync the vHub

**Where:** Provider Azure Virtual WAN integration page.  
**Tests:** Entra application credentials and Azure Security Partner Provider configuration.  
**Success:** Credential/API test succeeds and hub is discovered.  
**Failure means:** Identity/permission or hub-provider setup problem.  
**Next action:** Revalidate application/client ID, secret/key, tenant ID, subscription ID, and Azure provider configuration.

### RDP/SSH breaks after secured routing is enabled

**Where:** Management-path design.  
**Tests:** Whether management depended on the old Internet return path.  
**Success:** Administration uses Bastion or deliberate private connectivity.  
**Failure means:** Secured `0/0` altered the management return path.  
**Next action:** Use a controlled management path instead of creating a casual inspection bypass.

---

## 16. Common mistakes

1. Treating SECaaS as a universal east-west firewall.
2. Assuming “SaaS solution” and “Security Partner Provider” are synonyms.
3. Omitting or deleting the vHub S2S VPN Gateway.
4. Manually injecting branch `0.0.0.0/0` to imitate the secured-provider route.
5. Forgetting to opt in the actual VNet/branch connections.
6. Failing to declare public-looking enterprise prefixes as private.
7. Hairpinning key Microsoft 365 branch traffic when direct/local breakout is recommended.
8. Assuming provider HA equals Azure Virtual WAN hub HA.
9. Assuming old partner logos/lists or CLI enums are still current.
10. Assuming the Internet-facing public source IP is an Azure Firewall public IP; SECaaS NAT/egress is provider-specific.
11. Treating Palo Alto Networks Cloud NGFW as the same integration class as Firewall Manager Security Partner Provider.

---

## 17. Official Microsoft architecture image

The Microsoft figure below is useful for understanding the intended division between Internet partner security and Azure/private paths. The artwork contains historical partner logos, so **do not treat the logos themselves as the current supported-provider list**.

![Microsoft Firewall Manager security partner scenarios](https://learn.microsoft.com/en-us/azure/firewall-manager/media/trusted-security-partners/all-scenarios.png)

**What this image shows:** A secured Virtual WAN hub with partner security used for Internet access and Azure controls used for other traffic classes.

**What matters:** It reinforces that Method 6 is primarily Internet/SaaS service insertion.

**What to verify:** Use current Microsoft documentation and the live supported-security-provider API rather than inferring support from the historical image.

Image source: https://learn.microsoft.com/en-us/azure/firewall-manager/media/trusted-security-partners/all-scenarios.png

---

## 18. Design decision table

| Requirement | Method 6 fit | Why |
|---|---|---|
| Secure Web Gateway for Azure workload egress | **Yes** | Core documented use case |
| Branch Internet inspection through cloud security | **Yes** | Core documented use case |
| User-aware SaaS controls | **Potentially** | Provider capability/licensing dependent |
| Avoid firewall VM lifecycle | **Yes** | Provider hosts SECaaS infrastructure |
| Full third-party VNet-to-VNet NGFW inspection | **Not by itself** | Needs a private-traffic-capable security model |
| Internet ingress DNAT | **Not the primary use case** | Use an ingress firewall/WAF/DNAT design |
| Centralize key Microsoft 365 branch flows | **Usually avoid** | Microsoft recommends local breakout for key M365 connectivity |
| Same behavior as Palo Alto Cloud NGFW in vHub | **No** | Different Virtual WAN integration class |
| Guaranteed partner tunnel redundancy | **Provider-specific** | Validate current vendor architecture |

---

## 19. Recommended reference architecture

```text
Branches + Azure Spokes
        |
        v
 Azure Virtual WAN regional vHub
        |
        +-- Internet traffic -----------------------------+
        |                                                 |
        |        vHub S2S VPN Gateway                     |
        |                 |                               |
        |               IPsec                             |
        |                 v                               |
        |          Security Partner SECaaS --------------> Internet/SaaS
        |
        +-- Private traffic --> Azure Firewall --> VNet/Branch/private destinations
```

This gives each security platform the traffic class most clearly supported by Microsoft's Security Partner Provider architecture: **SECaaS for Internet** and **Azure Firewall for private traffic**.

---

## 20. Final takeaways

- Method 6 is an **external SECaaS insertion** architecture, not firewall-VM placement.
- Virtual WAN supplies global/regional transit and route programming.
- The vHub **S2S VPN Gateway** supplies the provider IPsec service connection.
- Firewall Manager distributes the secured Internet default route to opted-in connections.
- The most important route is `0.0.0.0/0` for Internet traffic.
- Do not manually advertise a branch default merely to reproduce the integration.
- The design is strongest for **VNet-to-Internet** and **Branch-to-Internet** inspection.
- Pairing SECaaS for Internet with **Azure Firewall for private traffic** is a clean supported pattern.
- Microsoft recommends local breakout for key Microsoft 365 branch connectivity.
- Provider NAT, identity, inspection depth, HA, service-edge behavior, tenancy, licensing, and limits are provider-specific.
- Current dedicated Firewall Manager documentation identifies **Zscaler** as the supported Security Partner Provider.
- Older Microsoft pages and the current Preview CLI still expose Check Point/iboss names; validate the live API and current deployment documentation rather than assuming those are currently deployable.
- Palo Alto Networks Cloud NGFW is a **different Virtual WAN SaaS solution model**, not this external SECaaS Security Partner Provider design.

---

## Sources

### Microsoft

- https://learn.microsoft.com/en-us/azure/firewall-manager/trusted-security-partners
- https://learn.microsoft.com/en-us/azure/firewall-manager/deploy-trusted-security-partner
- https://learn.microsoft.com/en-us/azure/firewall-manager/overview
- https://learn.microsoft.com/en-us/azure/virtual-wan/third-party-integrations
- https://learn.microsoft.com/en-us/azure/virtual-wan/virtual-wan-about
- https://learn.microsoft.com/en-us/azure/networking/design-guide/virtual-wan
- https://learn.microsoft.com/en-us/azure/architecture/networking/architecture/hub-spoke-virtual-wan-architecture
- https://learn.microsoft.com/en-us/rest/api/virtualwan/supported-security-providers/supported-security-providers?view=rest-virtualwan-2025-05-01
- https://learn.microsoft.com/en-us/cli/azure/network/security-partner-provider?view=azure-cli-latest
- https://learn.microsoft.com/en-us/cli/azure/network/vwan?view=azure-cli-latest
- https://learn.microsoft.com/en-us/cli/azure/network/vhub?view=azure-cli-latest
- https://learn.microsoft.com/en-us/cli/azure/network/vhub/connection?view=azure-cli-latest
- https://learn.microsoft.com/en-us/cli/azure/network/vpn-gateway?view=azure-cli-latest

### Zscaler

- https://help.zscaler.com/zia/integrating-microsoft-azure-virtual-wan
- https://help.zscaler.com/zia/about-partner-integrations

### Official Microsoft image

- https://learn.microsoft.com/en-us/azure/firewall-manager/media/trusted-security-partners/all-scenarios.png
