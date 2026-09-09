from pathlib import Path
p=Path('09-07-26_GCP_Firewall_Policy_Hierarchy_Goto_Next_NSI_Deep_Dive.md')
s=p.read_text()

# TOC entry
needle='- [22. Design guidance](#22-design-guidance)\n- [Sources](#sources)'
repl='- [22. Design guidance](#22-design-guidance)\n- [23. Reference — `gcloud compute network-firewall-policies rules create` parameters](#23-reference--gcloud-compute-network-firewall-policies-rules-create-parameters)\n  - [23.1 Rule identity and policy scope](#231-rule-identity-and-policy-scope)\n  - [23.2 Action and inspection behavior](#232-action-and-inspection-behavior)\n  - [23.3 Direction and Layer-4 matching](#233-direction-and-layer-4-matching)\n  - [23.4 Source match parameters](#234-source-match-parameters)\n  - [23.5 Destination match parameters](#235-destination-match-parameters)\n  - [23.6 Target-selection parameters](#236-target-selection-parameters)\n  - [23.7 Logging, enablement, and description](#237-logging-enablement-and-description)\n  - [23.8 Complete NSI example](#238-complete-nsi-example)\n  - [23.9 How to read a rule quickly](#239-how-to-read-a-rule-quickly)\n- [Sources](#sources)'
if needle not in s:
    raise SystemExit('TOC anchor not found')
s=s.replace(needle,repl,1)

# Pointer in section 10 after first network-firewall-policies rule example
needle2='Normal firewall rule evaluation stops when the interception rule matches.\n\n---\n\n# 11. Build an NSI interception rule in a hierarchical policy'
pointer='Normal firewall rule evaluation stops when the interception rule matches.\n\n> **Command reference:** For a parameter-by-parameter explanation of `gcloud compute network-firewall-policies rules create`—including source/destination selectors, network context, secure tags, targets, `apply_security_profile_group`, TLS inspection, logging, and global versus regional scope—see [Section 23](#23-reference--gcloud-compute-network-firewall-policies-rules-create-parameters).\n\n---\n\n# 11. Build an NSI interception rule in a hierarchical policy'
if needle2 not in s:
    raise SystemExit('Section 10 pointer anchor not found')
s=s.replace(needle2,pointer,1)

# Append reference before Sources
anchor='---\n\n# Sources\n'
section=r'''---

# 23. Reference — `gcloud compute network-firewall-policies rules create` parameters

This section is a practical reference for the **network firewall policy** rule command used throughout this guide:

```cli
gcloud compute network-firewall-policies rules create PRIORITY \
  --firewall-policy=FIREWALL_POLICY \
  --action=ACTION \
  --layer4-configs=LAYER4_CONFIGS \
  [additional match, target, logging, inspection, and scope flags]
```

Use this section whenever an earlier example shows only the flags required for that specific flow. The command can express much richer source, destination, workload-target, and inspection matching than the short NSI examples above.

Google Cloud CLI reference:

- https://cloud.google.com/sdk/gcloud/reference/compute/network-firewall-policies/rules/create

## 23.1 Rule identity and policy scope

| Parameter | What it controls | Practical meaning |
|---|---|---|
| `PRIORITY` | Rule order inside the policy | Lower numeric priority is evaluated before higher numeric priority. Priority applies only **inside this policy**; it does not override firewall-policy hierarchy. |
| `--firewall-policy=NAME` | Parent network firewall policy | Selects the global or regional network firewall policy that receives the rule. |
| `--project=PROJECT_ID` | Project context | Selects the project containing the network firewall policy. |
| `--global-firewall-policy` | Global policy scope | Tells `gcloud` that the referenced policy is a global network firewall policy. This is the normal network-policy scope used for NSI interception rules. |
| `--firewall-policy-region=REGION` | Regional policy scope | Tells `gcloud` that the referenced policy is regional. Do not combine it with `--global-firewall-policy`. Regional network firewall policies do not support the same NSI `apply_security_profile_group` interception action described in this guide. |

Mental model:

```text
WHERE DOES THE RULE LIVE?

--firewall-policy
--project
--global-firewall-policy
or
--firewall-policy-region
```

## 23.2 Action and inspection behavior

The action answers: **what happens after all match conditions for this rule are satisfied?**

| Parameter/value | Meaning |
|---|---|
| `--action=ALLOW` | Permit the connection and terminate normal firewall-policy evaluation for that connection. |
| `--action=DENY` | Drop the connection and terminate normal firewall-policy evaluation. |
| `--action=GOTO_NEXT` | Exit the current policy and continue to the next applicable firewall-policy evaluation stage. It does **not** mean evaluate the next rule in this same policy. |
| `--action=APPLY_SECURITY_PROFILE_GROUP` | Stop normal firewall-rule evaluation and hand the connection to the referenced security profile group for supported security inspection/NSI processing. |
| `--security-profile-group=SECURITY_PROFILE_GROUP` | Inspection policy reference | Required when the action is `APPLY_SECURITY_PROFILE_GROUP`; identifies the Security Profile Group that contains the security/intercept profile used for inspection. |
| `--tls-inspect` | Enable TLS inspection for this inspected rule | Requests TLS inspection for matching traffic when the required TLS inspection configuration is present. |
| `--no-tls-inspect` | Do not request TLS inspection | Leaves TLS inspection disabled for this rule. |

For NSI, read these flags together:

```text
MATCH
  -> --action=APPLY_SECURITY_PROFILE_GROUP
  -> --security-profile-group=...
  -> optional --tls-inspect
  -> NSI/security inspection owns the connection decision
```

## 23.3 Direction and Layer-4 matching

| Parameter | What it controls | Example |
|---|---|---|
| `--direction=INGRESS` | Traffic entering the protected target | Internet/VPC source toward a VM or supported target. |
| `--direction=EGRESS` | Traffic leaving the protected target | VM/workload toward another VPC, on-premises, or Internet destination. |
| `--layer4-configs=all` | All IP protocols/ports | Match all Layer-4 traffic. |
| `--layer4-configs=tcp` | All TCP destination ports | Match any TCP connection. |
| `--layer4-configs=tcp:443` | TCP destination port 443 | Typical HTTPS match. |
| `--layer4-configs=tcp:80,tcp:443` | Multiple protocol/port entries | Match HTTP and HTTPS. |

If direction is omitted, verify the current CLI default before relying on it; production rules should normally state `--direction` explicitly so the intended packet orientation is obvious during review.

## 23.4 Source match parameters

Source selectors answer **who/what originated the packet?** Availability and valid combinations depend on rule direction and policy capabilities.

| Parameter | Meaning | Typical use |
|---|---|---|
| `--src-ip-ranges=CIDR[,CIDR...]` | Match packet source IP against CIDR ranges | Branch networks, management ranges, application subnets, Internet ranges. |
| `--src-address-groups=ADDRESS_GROUP[...]` | Match source against reusable Network Security Address Groups | Replace long repeated CIDR lists with centrally managed address objects. |
| `--src-fqdns=FQDN[...]` | Match supported source FQDN criteria | Specialized ingress matching where supported. |
| `--src-region-codes=REGION_CODE[...]` | Match source geolocation/region code | Geographic ingress policy. |
| `--src-threat-intelligence=LIST[...]` | Match source against supported Google threat-intelligence lists | Block or inspect known malicious/suspicious source populations. |
| `--src-secure-tags=TAG_VALUE[...]` | Match source workloads carrying secure tags | Identity-oriented workload-to-workload policy independent of fixed IP addresses. |
| `--src-network-context=CONTEXT` | Match source by network context | Examples include `INTERNET`, `NON_INTERNET`, `VPC_NETWORKS`, and `INTRA_VPC` where supported. |
| `--src-networks=NETWORK_URL[...]` | Match traffic originating from specified VPC network resources | Used with the VPC-network source context to distinguish network identity from source CIDR. |

Important distinction:

```text
--src-ip-ranges
= WHO by IP prefix

--src-secure-tags
= WHO by workload tag identity

--src-networks
= WHO by VPC network resource

--src-network-context
= WHO by broad network context such as INTERNET
```

## 23.5 Destination match parameters

Destination selectors answer **where is the packet going?**

| Parameter | Meaning | Typical use |
|---|---|---|
| `--dest-ip-ranges=CIDR[,CIDR...]` | Match destination IP against CIDR ranges | East-west VPC prefixes, on-premises prefixes, controlled Internet ranges. |
| `--dest-address-groups=ADDRESS_GROUP[...]` | Match destination against reusable Address Groups | Central object-based destination policy. |
| `--dest-fqdns=FQDN[...]` | Match supported destination FQDNs | Egress policy for application/service names instead of static IP lists. |
| `--dest-region-codes=REGION_CODE[...]` | Match destination geolocation/region code | Geographic egress restrictions/inspection. |
| `--dest-threat-intelligence=LIST[...]` | Match destination against supported Google threat-intelligence lists | Deny or inspect suspicious/malicious destinations. |
| `--dest-network-context=CONTEXT` | Match destination by network context | Particularly useful for `INTERNET` versus non-Internet egress classification. |

A useful NSI Internet-egress pattern is conceptually:

```cli
--direction=EGRESS \
--dest-network-context=INTERNET \
--action=APPLY_SECURITY_PROFILE_GROUP
```

That expresses **Internet-bound egress** without manually maintaining `0.0.0.0/0` plus exception logic as the only classification mechanism.

## 23.6 Target-selection parameters

Target selectors are different from source/destination packet fields. They answer **which protected workload or load-balancer resource does this firewall rule apply to?**

| Parameter | Meaning |
|---|---|
| `--target-secure-tags=TAG_VALUE[...]` | Apply the rule only to targets carrying specified secure tags. |
| `--target-service-accounts=SERVICE_ACCOUNT[...]` | Apply the rule to VM targets using specified service accounts. |
| `--target-type=INSTANCES` | Target VM instances. This is the normal/default workload model. |
| `--target-type=INTERNAL_MANAGED_LB` | Target supported internal managed load-balancer resources instead of VM instances. |
| `--target-forwarding-rules=FORWARDING_RULE[...]` | With an internal-managed-LB target type, narrow the rule to specified forwarding rules. |

Mnemonic:

```text
SOURCE match
= WHO SENT IT?

DESTINATION match
= WHERE IS IT GOING?

TARGET selector
= WHICH PROTECTED RESOURCE DOES THIS RULE APPLY TO?
```

## 23.7 Logging, enablement, and description

| Parameter | Meaning |
|---|---|
| `--enable-logging` | Enable firewall rule logging for matching connections. Strongly recommended while validating hierarchy and NSI interception. |
| `--no-enable-logging` | Disable rule logging. |
| `--disabled` | Create or leave the rule disabled so it has no enforcement effect. Useful for staging. |
| `--no-disabled` | Rule is enabled. |
| `--description="TEXT"` | Administrative explanation of why the rule exists. Use this to document ownership, traffic class, and intended inspection behavior. |

For complex policies, a useful description convention is:

```text
<owner> | <traffic class> | <action> | <change/ticket>
```

Example:

```cli
--description="NetSec | prod Internet egress | NSI inspection | CHG-12345"
```

## 23.8 Complete NSI example

The following example shows how several flag groups combine. Replace all resource identifiers with values from your environment and verify that each match type is supported for the policy/action combination you intend to use.

```cli
gcloud compute network-firewall-policies rules create 100 \
  --project=app-prod-1 \
  --firewall-policy=pan-nsi-policy \
  --global-firewall-policy \
  --direction=EGRESS \
  --dest-network-context=INTERNET \
  --layer4-configs=tcp \
  --target-secure-tags=tagValues/123456789 \
  --action=APPLY_SECURITY_PROFILE_GROUP \
  --security-profile-group=organizations/ORG_ID/locations/global/securityProfileGroups/pan-nsi-spg \
  --tls-inspect \
  --enable-logging \
  --description="Inspect tagged production workload Internet egress through NSI"
```

Read it literally:

```text
RULE PRIORITY 100

WHERE?
  project app-prod-1
  global network firewall policy pan-nsi-policy

WHICH DIRECTION?
  EGRESS

WHAT TRAFFIC?
  destination network context = INTERNET
  protocol = TCP

WHICH TARGETS?
  workloads carrying secure tag tagValues/123456789

WHAT ACTION?
  APPLY_SECURITY_PROFILE_GROUP
  security profile group = pan-nsi-spg
  TLS inspection requested
  logging enabled
```

## 23.9 How to read a rule quickly

When reviewing a long command, reduce it to six questions:

```text
1. WHERE?
   --firewall-policy
   --project
   --global-firewall-policy / --firewall-policy-region

2. WHEN?
   PRIORITY

3. WHICH DIRECTION?
   --direction

4. WHAT TRAFFIC?
   --src-*
   --dest-*
   --layer4-configs

5. WHICH PROTECTED TARGET?
   --target-*

6. WHAT HAPPENS?
   --action
   --security-profile-group
   --tls-inspect
   --enable-logging
```

That produces the shortest useful mental model for this entire command:

```text
WHERE + PRIORITY + DIRECTION + MATCH + TARGET
                  -> ACTION
```

Do not assume every source/destination selector can be combined with every action, direction, policy scope, or target type. Google continues to add capabilities to Cloud NGFW, so validate unusual combinations against the current CLI reference and the relevant feature documentation before deployment.

'''
if anchor not in s:
    raise SystemExit('Sources anchor not found')
s=s.replace(anchor,section+anchor,1)

# Add network-firewall-policies CLI source if absent
src='- Google Cloud SDK — `gcloud compute network-firewall-policies rules create`: https://cloud.google.com/sdk/gcloud/reference/compute/network-firewall-policies/rules/create\n'
if src not in s:
    s=s.rstrip()+"\n"+src

p.write_text(s)
