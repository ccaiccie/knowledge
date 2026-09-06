# Azure Front Door WAF and Application Gateway WAF — Method 9 Deep Dive

**Last validated:** 2026-09-06  
**Scope:** Layer-7 HTTP/HTTPS firewall inspection with Azure Front Door Web Application Firewall (WAF), Azure Application Gateway WAF v2, and a layered Azure Front Door → Application Gateway design.

> **Source information** = behavior explicitly documented by Microsoft.  
> **Additional explanation** = networking/security context added to make documented behavior operationally clear.  
> **Reasonable inference** = a design conclusion derived from documented behavior and identified as such.

---

## Supplied and supporting URLs

- https://github.com/ccaiccie/knowledge/blob/main/09-05-26-12-41_Azure_Firewall_Inspection_Methods_Comprehensive_Study_Guide.md#11-method-9--layer-7-web-firewall-inspection-with-azure-front-door-waf-and-application-gateway-waf
- https://learn.microsoft.com/en-us/azure/frontdoor/web-application-firewall
- https://learn.microsoft.com/en-us/azure/web-application-firewall/afds/afds-overview
- https://learn.microsoft.com/en-us/azure/web-application-firewall/afds/waf-front-door-drs
- https://learn.microsoft.com/en-us/azure/web-application-firewall/afds/waf-front-door-custom-rules
- https://learn.microsoft.com/en-us/azure/web-application-firewall/afds/waf-front-door-rate-limit
- https://learn.microsoft.com/en-us/azure/frontdoor/origin-security
- https://learn.microsoft.com/en-us/azure/frontdoor/private-link
- https://learn.microsoft.com/en-us/azure/frontdoor/how-to-enable-private-link-application-gateway
- https://learn.microsoft.com/en-us/azure/frontdoor/create-front-door-cli
- https://learn.microsoft.com/en-us/azure/application-gateway/quick-create-cli
- https://learn.microsoft.com/en-us/azure/web-application-firewall/ag/tutorial-restrict-web-traffic-cli
- https://learn.microsoft.com/en-us/azure/web-application-firewall/ag/application-gateway-crs-rulegroups-rules
- https://learn.microsoft.com/en-us/azure/architecture/example-scenario/gateway/firewall-application-gateway
- https://learn.microsoft.com/en-us/azure/architecture/example-scenario/gateway/application-gateway-before-azure-firewall
- https://learn.microsoft.com/en-us/azure/well-architected/service-guides/azure-front-door

---

# 1. What Method 9 actually is

Azure Front Door WAF and Application Gateway WAF are **reverse-proxy web firewalls**. They inspect HTTP/HTTPS requests that are explicitly published through them. They are not routed transit firewalls like Azure Firewall or a third-party next-generation firewall (NGFW)/network virtual appliance (NVA).

| Capability | Front Door WAF | Application Gateway WAF v2 | Azure Firewall / NGFW |
|---|---|---|---|
| Primary scope | Global HTTP/HTTPS ingress | Regional HTTP/HTTPS ingress | Routed L3/L4 and product-dependent L7 transit |
| Deployment location | Microsoft global edge | Customer VNet/subnet | VNet/vHub/appliance path |
| Traffic steering | DNS + endpoint + route | Frontend/listener + routing rule | UDR/BGP/routing intent/NAT |
| TLS termination | Yes | Yes | Product/design dependent |
| HTTP request inspection | Yes | Yes | Not equivalent |
| Generic east-west inspection | No | No | Yes |
| Generic Internet egress inspection | No | No | Yes |
| Arbitrary TCP/UDP publication | No | No | Yes/product-dependent |
| Path-based L7 routing | Yes | Yes | Not the same function |

**Source information:** Microsoft describes both Front Door WAF and Application Gateway WAF as Layer-7 web application protection services. Front Door is global and decentralized; Application Gateway is regional and VNet-integrated.

**Key design principle:** a WAF protects only traffic that reaches the WAF endpoint. If the origin remains directly reachable, clients can bypass WAF inspection. Origin lockdown is therefore part of the firewall design.

---

# 2. Three practical architectures

![Method 9 architecture variants](images/09-06-26-10-24_method9_architecture_variants.svg)

[Editable draw.io diagram](images/09-06-26-10-24_method9_architecture_variants.drawio)

**What this image shows**  
Three separate designs: Front Door WAF directly in front of an origin, Application Gateway WAF in a regional VNet, and a layered Front Door → Application Gateway design.

**What matters**  
These are reverse-proxy paths. DNS, Front Door routes, Application Gateway listeners/rules, and origin access restrictions place the WAF in the path. User-defined routes (UDRs) are not the insertion mechanism for the client-to-WAF leg.

**What to verify**  
DNS, certificate state, WAF policy association, origin/backend health, host-header/SNI behavior, and the absence of an unprotected direct-origin path.

## 2.1 Pattern A — Azure Front Door WAF only

Use Front Door when the application is public HTTP/HTTPS and you want globally distributed ingress, edge WAF, global health-based origin selection, acceleration, and—on Premium—Private Link to supported origins.

```text
Client
  -> Azure Front Door edge
  -> Front Door WAF
  -> Front Door route
  -> origin group
  -> selected origin
```

Best fits include multi-region web applications, public APIs, App Service, API Management, storage/static sites, Application Gateway origins, and supported services exposed through Private Link.

## 2.2 Pattern B — Application Gateway WAF v2 only

Use Application Gateway when you need a **regional, VNet-integrated reverse proxy** in front of private or public HTTP(S) backends.

```text
Client
  -> Application Gateway frontend
  -> listener
  -> WAF policy
  -> request-routing rule
  -> backend pool
  -> backend HTTP settings
  -> application
```

Good fits include VMs, VM scale sets, AKS, API Management, App Service, and other HTTP(S) services reachable from the Application Gateway subnet.

## 2.3 Pattern C — Front Door WAF → Application Gateway WAF

Use the layered design when you need both global edge functions and a regional reverse-proxy/security boundary.

Typical responsibility split:

- **Front Door:** global entry point, edge WAF, bot/rate controls, geo/IP rules, origin health/failover.
- **Application Gateway:** regional host/path routing, private backend integration, regional listener policy, optional application-specific second WAF layer.

Do not duplicate every WAF rule at both layers by default. Two identical WAFs increase false-positive and troubleshooting surfaces without automatically doubling security.

---

# 3. Azure Front Door WAF architecture and packet flow

Azure Front Door Standard/Premium is a global reverse proxy. A request enters a Microsoft edge location, matches a Front Door endpoint/domain and route, is evaluated by the associated WAF security policy, and—if allowed—is proxied to a selected healthy origin.

Important objects are:

1. **Profile** — parent Front Door resource and SKU.
2. **Endpoint** — Front Door-generated hostname and route container.
3. **Custom domain** — public application hostname such as `www.contoso.com`.
4. **Origin group** — health/load-balancing boundary.
5. **Origin** — concrete backend.
6. **Route** — maps domains/path patterns/protocols to an origin group.
7. **WAF policy** — custom and managed rules.
8. **Security policy** — associates the WAF policy with Front Door domains/endpoints.

![Front Door WAF packet flow](images/09-06-26-10-24_frontdoor_waf_packet_flow.svg)

[Editable draw.io diagram](images/09-06-26-10-24_frontdoor_waf_packet_flow.drawio)

**What this image shows**  
A client establishes TLS to Front Door, Front Door WAF inspects the HTTP request, and Front Door proxies allowed traffic to a healthy origin over a separate connection.

**What matters**  
Front Door terminates the client-side session and creates/reuses an origin-side session. The origin does not receive the original client TCP connection.

**What to verify**  
Endpoint/domain route match, certificate, WAF association, managed/custom rule state, origin health, origin host header, HTTPS port, Private Link approval if used, and origin lockdown.

## 3.1 Detailed request flow

Assume:

- Client: `198.51.100.25`
- Public URL: `https://www.contoso.com`
- Origin: `app.contoso.internal:443`

1. DNS resolves `www.contoso.com` to the Front Door custom domain/endpoint.
2. The client opens TCP/443 and TLS to a Front Door edge location.
3. Front Door terminates TLS and identifies the matching route/domain.
4. Custom WAF rules are evaluated according to policy priority.
5. Managed rules evaluate the HTTP request when configured.
6. If blocked, Front Door generates the response and **does not forward the request to the origin**.
7. If allowed, Front Door selects a healthy origin from the origin group.
8. Front Door opens or reuses an origin-side connection.
9. With end-to-end TLS, Front Door establishes a second TLS session to the origin.
10. Front Door forwards the HTTP request with documented proxy/forwarding context.
11. The origin responds to Front Door.
12. Front Door returns the response to the client over the client-side connection.

Conceptually:

```text
Client-side session:
198.51.100.25:ephemeral -> Front Door edge:443
TLS session #1 terminates at Front Door.

Origin-side session:
Front Door service -> origin:443
TLS session #2 terminates at the origin.
```

**Additional explanation:** because Front Door proxies the request, the origin-side transport source is Front Door infrastructure, not the original client. Use documented forwarding headers/log fields for client context, and do not trust arbitrary client-supplied forwarding headers from a path that can bypass Front Door.

---

# 4. Front Door WAF rule processing

## 4.1 Detection versus Prevention

Microsoft documents two core WAF modes:

- **Detection:** inspect and log matching requests without normal blocking enforcement.
- **Prevention:** enforce configured WAF actions.

A practical rollout is to start in Detection, collect representative traffic, tune narrow false-positive exclusions, and then move to Prevention.

## 4.2 Managed Default Rule Set (DRS)

Front Door WAF managed rules cover common web-attack classes such as:

- SQL injection.
- Cross-site scripting.
- Remote command execution.
- Local/remote file inclusion.
- Protocol anomalies and other exploit patterns.

For DRS 2.x, Microsoft documents anomaly scoring. Rule severities contribute to a cumulative score:

| Severity | Score contribution |
|---|---:|
| Critical | 5 |
| Error | 4 |
| Warning | 3 |
| Notice | 2 |

An anomaly score of 5 or greater is blocked in Prevention mode. A log entry whose action is only `Matched` can be a contributing event rather than the final block event.

## 4.3 Custom rules

Custom rules are evaluated before the managed rule set. This matters operationally: a broad custom `Allow` rule can short-circuit managed-rule inspection for matching requests.

Use custom rules for deliberate controls such as:

- IP ranges.
- Geography.
- Request headers.
- URI/path patterns.
- Rate limits.

Prefer narrowly scoped exceptions over broad Allow rules where the intent is only to eliminate a false positive.

## 4.4 Rate limiting

Front Door WAF supports rate-limit custom rules. Microsoft documents per-client/socket-IP thresholds over supported one-minute or five-minute windows. Because Front Door is distributed, operators should not assume a single centralized counter visible at every edge server at exactly the same instant.

---

# 5. Front Door origin lockdown

This is one of the most important parts of the design.

## 5.1 Preferred: Private Link with Front Door Premium

Front Door Premium supports Private Link to documented origin types, including Application Gateway and services exposed through internal load balancers.

The security effect is:

```text
Internet client
  -> public Front Door edge
  -> Microsoft private connectivity
  -> private origin
```

This prevents the normal application path from requiring a broadly reachable public origin.

## 5.2 Public origin: service tag plus Front Door profile ID

When Application Gateway is a public Front Door origin, Microsoft documents a layered restriction:

1. Allow the `AzureFrontDoor.Backend` service tag to the Application Gateway listener ports.
2. Deny general Internet access to those ports.
3. Use an Application Gateway WAF custom rule to verify `X-Azure-FDID` equals the expected Front Door profile identifier.

Why both?

- The service tag proves the traffic comes from Front Door infrastructure.
- `X-Azure-FDID` proves it came from **your intended Front Door profile**, not simply another customer's Front Door.

---

# 6. Front Door implementation example — Azure CLI

The commands below follow Microsoft's documented CLI object model. Replace names, IDs, origins, and probe paths for your environment.

## 6.1 Variables

```cli
RG="RG-WebEdge"
LOCATION="eastus"
AFD_PROFILE="afd-contoso-prod"
AFD_ENDPOINT="contoso-web"
ORIGIN_GROUP="og-web-prod"
WAF_POLICY="waf-afd-contoso-prod"
SEC_POLICY="afd-security-prod"
```

## 6.2 Create Front Door Premium

```cli
az group create \
  --name "$RG" \
  --location "$LOCATION"

az afd profile create \
  --profile-name "$AFD_PROFILE" \
  --resource-group "$RG" \
  --sku Premium_AzureFrontDoor
```

**Why Premium here:** the design uses capabilities such as managed WAF rules and Private Link origin connectivity. Verify current tier support for your exact feature set before deployment.

## 6.3 Create endpoint

```cli
az afd endpoint create \
  --resource-group "$RG" \
  --endpoint-name "$AFD_ENDPOINT" \
  --profile-name "$AFD_PROFILE" \
  --enabled-state Enabled
```

## 6.4 Create origin group

```cli
az afd origin-group create \
  --resource-group "$RG" \
  --origin-group-name "$ORIGIN_GROUP" \
  --profile-name "$AFD_PROFILE" \
  --probe-request-type GET \
  --probe-protocol Https \
  --probe-interval-in-seconds 60 \
  --probe-path /health \
  --sample-size 4 \
  --successful-samples-required 3 \
  --additional-latency-in-milliseconds 50
```

The health endpoint should be inexpensive, deterministic, and representative of application readiness.

## 6.5 Create WAF policy

```cli
az network front-door waf-policy create \
  --name "$WAF_POLICY" \
  --resource-group "$RG" \
  --sku Premium_AzureFrontDoor \
  --disabled false \
  --mode Prevention
```

## 6.6 Add managed rules

The Microsoft quickstart currently demonstrates these rule-set versions. For production, verify the newest supported version validated for your application.

```cli
az network front-door waf-policy managed-rules add \
  --policy-name "$WAF_POLICY" \
  --resource-group "$RG" \
  --type Microsoft_DefaultRuleSet \
  --action Block \
  --version 2.1

az network front-door waf-policy managed-rules add \
  --policy-name "$WAF_POLICY" \
  --resource-group "$RG" \
  --type Microsoft_BotManagerRuleSet \
  --version 1.0
```

## 6.7 Associate WAF with endpoint/domain

```cli
SUB_ID=$(az account show --query id -o tsv)

az afd security-policy create \
  --resource-group "$RG" \
  --profile-name "$AFD_PROFILE" \
  --security-policy-name "$SEC_POLICY" \
  --domains "/subscriptions/${SUB_ID}/resourceGroups/${RG}/providers/Microsoft.Cdn/profiles/${AFD_PROFILE}/afdEndpoints/${AFD_ENDPOINT}" \
  --waf-policy "/subscriptions/${SUB_ID}/resourceGroups/${RG}/providers/Microsoft.Network/frontdoorWebApplicationFirewallPolicies/${WAF_POLICY}"
```

A WAF policy that exists but is not associated with the domain/endpoint receiving requests performs no inspection for that path.

---

# 7. Application Gateway WAF v2 architecture and packet flow

Application Gateway is regional and VNet-integrated. It is deployed into a dedicated subnet and uses:

- Frontend IP configuration.
- Frontend ports.
- HTTP(S) listeners.
- Certificates.
- Request-routing rules/path maps.
- Backend pools.
- Backend HTTP settings.
- Health probes.
- WAF policy.

![Application Gateway WAF packet flow](images/09-06-26-10-24_appgateway_waf_packet_flow.svg)

[Editable draw.io diagram](images/09-06-26-10-24_appgateway_waf_packet_flow.drawio)

**What this image shows**  
A client reaches a public or private Application Gateway frontend. The listener accepts the request, WAF evaluates it, the routing rule selects the backend, and Application Gateway opens a separate backend connection.

**What matters**  
Application Gateway is not an inline transparent hop. The backend connection is a new connection originated by the gateway.

**What to verify**  
Frontend IP, listener/certificate, rule priority, WAF policy, backend pool, backend HTTP settings, host/SNI, probe health, NSG/UDR reachability, DNS, and backend certificate trust.

## 7.1 Detailed flow

Assume:

- Client: `198.51.100.25`
- Gateway public frontend: `203.0.113.20`
- Application Gateway subnet: `10.10.1.0/24`
- Backend: `10.10.20.10:443`

1. DNS resolves `www.contoso.com` to the gateway frontend.
2. Client opens TCP/443 and TLS to `203.0.113.20`.
3. The HTTPS listener matches frontend IP/port and host name.
4. Application Gateway terminates client TLS.
5. WAF evaluates the HTTP request.
6. If blocked, the request never reaches the backend.
7. If allowed, the routing rule selects a backend pool/path map.
8. Backend HTTP settings determine protocol, port, host-name behavior, timeout, affinity, and related backend connection parameters.
9. Application Gateway opens or reuses a backend connection to `10.10.20.10:443`.
10. The backend responds to Application Gateway.
11. Application Gateway returns the response to the client.

```text
Client-side connection:
198.51.100.25:ephemeral -> 203.0.113.20:443

Backend-side connection:
Application Gateway -> 10.10.20.10:443
```

## 7.2 Routing still matters on the backend side

A UDR does not insert Application Gateway into arbitrary client transit. However, once Application Gateway proxies toward a backend, normal VNet routing applies. NSGs, UDRs, VNet peering, DNS, Private Endpoints, and inserted firewalls can all affect the gateway-to-backend connection.

If an Azure Firewall or NVA sits between Application Gateway and the workload, preserve the stateful firewall's return-path symmetry.

---

# 8. Application Gateway implementation example — Azure CLI

## 8.1 Network and public IP

```cli
RG="RG-AppGateway"
LOCATION="eastus"
VNET="VNet-Web"
AG_SUBNET="AppGatewaySubnet"
BACKEND_SUBNET="BackendSubnet"
PIP="pip-appgw-prod"
APPGW="agw-contoso-prod"
WAF_POLICY="waf-agw-contoso-prod"

az group create \
  --name "$RG" \
  --location "$LOCATION"

az network vnet create \
  --resource-group "$RG" \
  --name "$VNET" \
  --address-prefix 10.10.0.0/16 \
  --subnet-name "$AG_SUBNET" \
  --subnet-prefix 10.10.1.0/24

az network vnet subnet create \
  --resource-group "$RG" \
  --vnet-name "$VNET" \
  --name "$BACKEND_SUBNET" \
  --address-prefixes 10.10.20.0/24

az network public-ip create \
  --resource-group "$RG" \
  --name "$PIP" \
  --allocation-method Static \
  --sku Standard
```

## 8.2 Create WAF policy

Microsoft's documented CLI tutorial shows:

```cli
az network application-gateway waf-policy create \
  --name "$WAF_POLICY" \
  --resource-group "$RG" \
  --type OWASP \
  --version 3.2
```

Application Gateway WAF also supports newer Microsoft rule-set generations in supported configurations. Choose and validate the rule set/version deliberately for production.

## 8.3 Create WAF_v2 gateway

```cli
az network application-gateway create \
  --name "$APPGW" \
  --location "$LOCATION" \
  --resource-group "$RG" \
  --vnet-name "$VNET" \
  --subnet "$AG_SUBNET" \
  --capacity 2 \
  --sku WAF_v2 \
  --http-settings-cookie-based-affinity Disabled \
  --frontend-port 80 \
  --http-settings-port 80 \
  --http-settings-protocol Http \
  --public-ip-address "$PIP" \
  --waf-policy "$WAF_POLICY" \
  --priority 1
```

This is a bootstrap example. Production HTTPS normally adds an HTTPS listener, certificate, explicit backend pool, HTTPS backend settings if end-to-end TLS is required, and a custom health probe.

## 8.4 Listener example

```cli
az network application-gateway frontend-port create \
  --resource-group "$RG" \
  --gateway-name "$APPGW" \
  --name port-443 \
  --port 443

az network application-gateway listener create \
  --resource-group "$RG" \
  --gateway-name "$APPGW" \
  --name https-www \
  --frontend-port port-443 \
  --frontend-ip appGatewayFrontendIP \
  --host-names www.contoso.com \
  --ssl-cert www-contoso-cert
```

Before referencing a generated/default frontend object name, query it:

```cli
az network application-gateway frontend-ip list \
  --resource-group "$RG" \
  --gateway-name "$APPGW" \
  --output table
```

## 8.5 Routing rule example

```cli
az network application-gateway rule create \
  --resource-group "$RG" \
  --gateway-name "$APPGW" \
  --name rule-www \
  --priority 100 \
  --rule-type Basic \
  --http-listener https-www \
  --address-pool pool-web \
  --http-settings https-backend
```

---

# 9. Layered Front Door → Application Gateway design

![Front Door to Application Gateway layered flow](images/09-06-26-10-24_frontdoor_to_appgateway_layered_flow.svg)

[Editable draw.io diagram](images/09-06-26-10-24_frontdoor_to_appgateway_layered_flow.drawio)

**What this image shows**  
The request terminates first at Front Door, is WAF-inspected, then Front Door connects to Application Gateway. Application Gateway can apply a second deliberately scoped WAF policy and proxy the request to the backend.

**What matters**  
There can be three separate TLS/session legs: client → Front Door, Front Door → Application Gateway, Application Gateway → backend.

**What to verify**  
Front Door origin health, Private Link approval or public-origin lockdown, `AzureFrontDoor.Backend` NSG allowance when public, `X-Azure-FDID` validation, App Gateway listener/host-name match, both WAF associations, and backend health.

## 9.1 Public App Gateway origin

Use both of these controls:

- NSG/edge access restriction for `AzureFrontDoor.Backend`.
- WAF custom rule validating `X-Azure-FDID`.

This prevents ordinary Internet clients and unrelated Front Door profiles from directly using the Application Gateway origin.

## 9.2 Private Link App Gateway origin

Front Door Premium supports Application Gateway as a Private Link origin.

High-level order:

1. Build and validate Application Gateway first.
2. Configure the Application Gateway private connectivity required for the integration.
3. Add it as a Private Link origin in Front Door Premium.
4. Approve the private endpoint connection.
5. Wait for Front Door origin health to become healthy.
6. Attach the route/custom domain.
7. Enable/tune Front Door WAF.
8. Remove or restrict any alternate public origin path.

---

# 10. TLS design

## 10.1 Front Door only

```text
Client -> Front Door     TLS #1
Front Door -> origin     TLS #2
```

For end-to-end encryption, configure HTTPS on both legs. Origin hostname/certificate validation must match Front Door's origin settings.

## 10.2 Application Gateway only

```text
Client -> App Gateway    TLS #1
App Gateway -> backend   TLS #2
```

For backend HTTPS, Application Gateway must be able to validate the backend certificate and SNI/host-name behavior used by the backend HTTP settings.

## 10.3 Layered design

```text
Client -> Front Door                 TLS #1
Front Door -> Application Gateway    TLS #2
Application Gateway -> backend       TLS #3
```

Each handshake can fail independently. A useful troubleshooting question is: **which TLS leg failed?**

---

# 11. Combining WAF with Azure Firewall or an NGFW

WAF and routed network firewall inspection solve different problems and can be complementary.

## 11.1 Application Gateway before Azure Firewall

Microsoft Architecture Center documents Application Gateway → Azure Firewall Premium → backend as a valid design.

Flow:

1. Application Gateway terminates client TLS.
2. Application Gateway WAF inspects the HTTP request.
3. Allowed request is proxied toward the backend.
4. Routing sends the gateway-to-backend flow through Azure Firewall.
5. Azure Firewall applies network/IDPS policy according to the deployed feature set.
6. The return path must remain symmetric through the stateful firewall.

Use this when you need both HTTP-aware WAF enforcement and routed firewall controls on the regional backend leg.

## 11.2 Azure Firewall before Application Gateway

Microsoft documents this topology but highlights a client-IP consequence: after firewall NAT/SNAT, Application Gateway can see the firewall as the transport source rather than the true Internet client. Microsoft notes that Front Door can be placed before the firewall so the original client context is inserted into HTTP forwarding headers before traffic enters the VNet.

---

# 12. High availability and failover

## Front Door

Front Door is a managed global edge service, but application availability still depends on origin design:

- Use multiple origins/regions when required.
- Configure health probes correctly.
- Set priorities/weights for intended failover/load distribution.
- Ensure the active routes and WAF policies cover every failover path.

## Application Gateway WAF v2

Application Gateway v2 is managed and scalable within a region. For resilient application design:

- Use autoscaling or validated fixed capacity.
- Use multiple backend instances/zones where supported.
- Configure health probes that represent application readiness.
- For regional disaster recovery, deploy a second regional gateway and use a global service such as Front Door to steer between regions.

## Layered failure domains

With Front Door → Application Gateway:

1. Front Door edge must accept the request.
2. WAF must allow it.
3. Front Door must find a healthy Application Gateway origin.
4. Application Gateway listener/rule/WAF must accept it.
5. Application Gateway must find a healthy backend.
6. The backend application must respond.

A 502/503 therefore requires identifying **which layer generated the error**.

---

# 13. Verification commands and expected state

Exact CLI formatting can vary by Azure CLI version, so the success criteria below focus on reliable state/fields rather than fabricated output.

## 13.1 Front Door profile and endpoint

```cli
az afd profile show \
  --resource-group RG-WebEdge \
  --profile-name afd-contoso-prod \
  --output jsonc

az afd endpoint show \
  --resource-group RG-WebEdge \
  --profile-name afd-contoso-prod \
  --endpoint-name contoso-web \
  --output jsonc
```

**Where:** Front Door control plane.  
**What it tests:** Resource existence, SKU, administrative state.  
**Expected successful state:** Correct SKU and enabled endpoint with expected hostname.  
**Failure indicator:** Missing/disabled endpoint or wrong resource group/profile.  
**Next action:** Fix control-plane configuration before debugging the origin.

## 13.2 Front Door origins

```cli
az afd origin-group list \
  --resource-group RG-WebEdge \
  --profile-name afd-contoso-prod \
  --output table

az afd origin list \
  --resource-group RG-WebEdge \
  --profile-name afd-contoso-prod \
  --origin-group-name og-web-prod \
  --output jsonc
```

**Expected successful state:** Intended origin enabled; hostname, ports, host header, and Private Link properties match design.  
**Failure indicators:** Wrong host/port, disabled origin, pending/rejected private endpoint.  
**Next action:** Correct origin configuration and re-check health.

## 13.3 Front Door WAF policy

```cli
az network front-door waf-policy show \
  --resource-group RG-WebEdge \
  --name waf-afd-contoso-prod \
  --output jsonc
```

**Expected successful state:** Policy enabled, intended mode, intended managed/custom rules.  
**Failure indicator:** Policy in Detection when blocking was expected, disabled policy, missing rule set.  
**Next action:** Correct policy state.

## 13.4 WAF security-policy association

```cli
az afd security-policy list \
  --resource-group RG-WebEdge \
  --profile-name afd-contoso-prod \
  --output jsonc
```

**Expected successful state:** Intended endpoint/custom domain associated with the correct WAF resource ID.  
**Failure indicator:** WAF exists but does not cover the domain receiving traffic.  
**Next action:** Fix association.

## 13.5 Application Gateway state

```cli
az network application-gateway show \
  --resource-group RG-AppGateway \
  --name agw-contoso-prod \
  --output jsonc
```

**Expected successful state:** Successful provisioning, `WAF_v2`, correct WAF policy reference and expected frontend/listener/backend objects.  
**Failure indicator:** Failed provisioning or missing/wrong object references.  
**Next action:** Fix gateway configuration before testing traffic.

## 13.6 Listeners

```cli
az network application-gateway listener list \
  --resource-group RG-AppGateway \
  --gateway-name agw-contoso-prod \
  --output table
```

**Expected successful state:** Correct frontend, port, host name and certificate association.  
**Failure indicator:** Host/port mismatch.  
**Next action:** Correct listener/TLS configuration.

## 13.7 Routing rules

```cli
az network application-gateway rule list \
  --resource-group RG-AppGateway \
  --gateway-name agw-contoso-prod \
  --output jsonc
```

**Expected successful state:** Correct listener → backend pool → HTTP settings relationship and expected priority.  
**Failure indicator:** Wrong backend or rule priority/path selection.  
**Next action:** Correct rule mapping.

## 13.8 Backend health

Use the Application Gateway backend-health view/CLI for the deployed Azure CLI version.

**Expected successful state:** Backends used by the active rule show `Healthy`.  
**Failure indicators:** `Unhealthy` or `Unknown`, with probe/TLS/DNS/timeout/reachability detail.  
**Next action:** Fix the stated backend-health cause before tuning WAF rules.

---

# 14. Logging and observability

Enable diagnostic logs before production cutover.

## Front Door

Collect:

- Access logs.
- WAF logs.
- Relevant origin/health diagnostics.

Correlate:

- Client/forwarded client context.
- Host and URI.
- WAF rule ID/action.
- Tracking/correlation ID.
- Origin response status.
- Front Door response status.

## Application Gateway

Collect:

- Access logs.
- WAF/firewall logs.
- Backend health/performance information.

Correlate:

- Listener.
- Routing rule/backend pool.
- Frontend status code.
- Backend response status/time.
- WAF rule ID/action.
- Forwarded client context.

**Additional explanation:** do not treat every non-200 response as a WAF problem. A 403 can be WAF or application policy; a 502 commonly points to backend connectivity/TLS/health; a 404 can be listener/routing/application behavior.

---

# 15. Troubleshooting by symptom

## Symptom A — Malicious request reaches the application

**Where:** DNS, WAF association, alternate origin path.  
**Command/tool:** `dig`/`nslookup`, Front Door security-policy list, Application Gateway WAF association, origin access controls.  
**What it tests:** Whether the request actually traversed the WAF.  
**Expected state:** Public hostname resolves to the WAF path; direct origin path is blocked.  
**What failure means:** WAF may be configured correctly but bypassed.  
**Next action:** Close direct-origin access and correct DNS/policy association.

## Symptom B — Legitimate request gets 403 after Prevention is enabled

**Where:** WAF logs.  
**Command/tool:** Azure Monitor / Log Analytics.  
**What it tests:** Custom/managed rule match and final enforcement action.  
**Expected state:** Logs identify the request attribute/rule responsible.  
**What failure means:** The 403 may be application-generated rather than WAF-generated.  
**Next action:** Confirm source; if WAF, use the narrowest safe exclusion/override.

## Symptom C — Front Door returns 502/503

**Where:** Front Door origin health and origin TLS/network path.  
**Command/tool:** Origin list, health diagnostics, origin logs.  
**Expected state:** At least one enabled healthy origin.  
**What failure means:** Host header, DNS, TLS, port, Private Link approval, or application health can be wrong.  
**Next action:** Resolve origin health before adjusting WAF.

## Symptom D — Application Gateway backend unhealthy

**Where:** Backend-health view.  
**Command/tool:** Backend health, NSG/UDR, DNS, backend certificate.  
**Expected state:** Probe is healthy.  
**What failure means:** Wrong probe path/status, blocked network path, DNS failure, TLS trust/name failure, or backend down.  
**Next action:** Fix the precise backend-health reason.

## Symptom E — Direct App Gateway works but Front Door path fails

**Where:** Front Door → Application Gateway leg.  
**Command/tool:** Front Door origin config, App Gateway listener host names, NSG, `X-Azure-FDID`, Private Link status.  
**Expected state:** Correct host header/SNI and permitted Front Door source/profile.  
**What failure means:** App Gateway accepts direct clients but rejects Front Door's origin request.  
**Next action:** Align origin host header, certificate, listener, NSG, and profile-ID rule.

## Symptom F — Client IP appears as proxy/firewall IP

**Where:** Backend application and forwarding-header handling.  
**Command/tool:** HTTP headers and access logs.  
**Expected state:** Application trusts only known proxy hops and extracts the documented forwarded client context.  
**What failure means:** Application is using transport source IP or trusting unsafe user-provided forwarding headers.  
**Next action:** Configure trusted-proxy handling and close bypass paths.

## Symptom G — WAF logs show `Matched` but request was not blocked

**Where:** WAF logs and policy mode.  
**What it tests:** Detection/Prevention and cumulative anomaly score.  
**Expected state:** In Prevention, final action follows the configured rule/action/scoring behavior; in Detection, the request is logged rather than normally blocked.  
**Next action:** Find the final enforcement event, not just a contributing rule match.

---

# 16. Common mistakes

1. **Treating WAF as a replacement for Azure Firewall.** WAF protects published HTTP/HTTPS, not arbitrary routed traffic.
2. **Leaving the origin directly reachable.** This creates a WAF bypass.
3. **Creating a WAF policy but not associating it with the active Front Door domain/endpoint.**
4. **Running Detection and expecting blocking.**
5. **Adding a broad custom Allow rule that bypasses managed rules.**
6. **Disabling an entire rule group to fix one false positive.** Use narrow exclusions.
7. **Ignoring host header and SNI.** Reverse proxies establish new backend TLS sessions.
8. **Treating every 502 as a WAF block.** It is frequently backend TLS/health/reachability.
9. **Assuming the original client remains the transport source at the backend.**
10. **Duplicating identical WAF policies at Front Door and App Gateway without a defined purpose.**
11. **Forgetting Private Link endpoint approval.**
12. **Applying a UDR and assuming that inserts Application Gateway.** The client must target the listener.

---

# 17. Decision matrix

| Requirement | Recommended starting point | Why |
|---|---|---|
| Global public multi-region web app | Front Door Premium + WAF | Global edge, WAF, health/failover, Private Link support |
| Single-region private/internal web app | Application Gateway WAF v2 | VNet-integrated regional reverse proxy/private frontend |
| Public regional web app | Application Gateway WAF v2 | Direct regional ingress with WAF/L7 routing |
| Global edge plus regional L7 routing | Front Door → Application Gateway | Separate global and regional responsibilities |
| Arbitrary TCP/UDP east-west inspection | Azure Firewall/NGFW | Routed firewall requirement |
| Internet egress inspection | Azure Firewall/NGFW/SECaaS | WAF is not generic egress inspection |
| HTTP WAF plus regional network firewall | App Gateway WAF → Azure Firewall/NGFW → backend | WAF for web attacks, firewall for routed controls |
| Hide origin from Internet | Front Door Premium + Private Link | Removes general public origin path |

---

# 18. Recommended production solution

For a modern Internet-facing Azure application that needs global reach and strong origin isolation, a strong default is:

```text
Internet client
  -> Azure Front Door Premium custom domain
  -> Front Door WAF
  -> Prevention mode after tuning
  -> Private Link to supported regional origin when possible
  -> Application Gateway WAF v2 only when regional reverse-proxy/WAF functions are required
  -> private application backends
```

Use Front Door alone when Application Gateway adds no needed regional function. Add Application Gateway when you need regional listener/path routing, private backend integration, regional application boundaries, or a deliberately different second WAF control plane.

If Application Gateway must be a public Front Door origin, lock it down with the documented `AzureFrontDoor.Backend` service tag and `X-Azure-FDID` validation so ordinary Internet clients and unrelated Front Door profiles cannot bypass your intended edge entry point.

---

# 19. Sources

- https://github.com/ccaiccie/knowledge/blob/main/09-05-26-12-41_Azure_Firewall_Inspection_Methods_Comprehensive_Study_Guide.md#11-method-9--layer-7-web-firewall-inspection-with-azure-front-door-waf-and-application-gateway-waf
- https://learn.microsoft.com/en-us/azure/frontdoor/web-application-firewall
- https://learn.microsoft.com/en-us/azure/web-application-firewall/afds/afds-overview
- https://learn.microsoft.com/en-us/azure/web-application-firewall/afds/waf-front-door-drs
- https://learn.microsoft.com/en-us/azure/web-application-firewall/afds/waf-front-door-custom-rules
- https://learn.microsoft.com/en-us/azure/web-application-firewall/afds/waf-front-door-rate-limit
- https://learn.microsoft.com/en-us/azure/frontdoor/origin-security
- https://learn.microsoft.com/en-us/azure/frontdoor/private-link
- https://learn.microsoft.com/en-us/azure/frontdoor/how-to-enable-private-link-application-gateway
- https://learn.microsoft.com/en-us/azure/frontdoor/create-front-door-cli
- https://learn.microsoft.com/en-us/azure/application-gateway/quick-create-cli
- https://learn.microsoft.com/en-us/azure/web-application-firewall/ag/tutorial-restrict-web-traffic-cli
- https://learn.microsoft.com/en-us/azure/web-application-firewall/ag/application-gateway-crs-rulegroups-rules
- https://learn.microsoft.com/en-us/azure/architecture/example-scenario/gateway/firewall-application-gateway
- https://learn.microsoft.com/en-us/azure/architecture/example-scenario/gateway/application-gateway-before-azure-firewall
- https://learn.microsoft.com/en-us/azure/well-architected/service-guides/azure-front-door
