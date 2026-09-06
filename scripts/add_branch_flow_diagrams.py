from pathlib import Path

p = Path('09-05-26-20-00_Azure_Virtual_WAN_Integrated_Third_Party_NGFW_Direct_Hub_Deep_Dive.md')
text = p.read_text(encoding='utf-8')
anchor = '''For a branch prefix `10.50.0.0/16` reaching Spoke A `10.10.0.0/16`:

'''
insert = '''For a branch prefix `10.50.0.0/16` reaching Spoke A `10.10.0.0/16`:

### Forward-path diagram

![Branch-to-spoke forward packet flow](images/09-05-26-20-00_branch_spoke_forward.svg)

[Editable draw.io source](images/09-05-26-20-00_branch_spoke_forward.drawio)

**What this image shows:** Only branch-to-Azure traffic. Blue arrows show the branch host entering the Virtual WAN VPN/ExpressRoute gateway, matching Private Traffic Routing Intent, crossing the Integrated NGFW, and reaching Spoke A.

**What matters:** The gateway is the branch entry point into the vHub routing fabric; the security insertion happens after the private-traffic classification and before the final spoke lookup.

**What to verify:** The branch advertises `10.50.0.0/16`, the vHub learns it through the expected gateway/connection, the NGFW sees the branch-to-Azure session, and the final route resolves `10.10.0.0/16` toward Spoke A.

### Return-path diagram

![Branch-to-spoke return packet flow](images/09-05-26-20-00_branch_spoke_return.svg)

[Editable draw.io source](images/09-05-26-20-00_branch_spoke_return.drawio)

**What this image shows:** Only Azure-to-branch reply traffic. Orange arrows show VM-A returning through the vHub, Routing Intent, existing NGFW state, and the VPN/ExpressRoute gateway toward the branch.

**What matters:** Stateful symmetry requires the return path to traverse compatible firewall state before the branch route is resolved toward the gateway.

**What to verify:** The return packet matches the existing NGFW session/state, the vHub resolves `10.50.0.0/16` toward the intended branch gateway/connection, and no alternate route creates asymmetric bypass.

'''
if anchor not in text:
    raise SystemExit('Branch section anchor not found')
text = text.replace(anchor, insert, 1)
p.write_text(text, encoding='utf-8')

rpath = Path('README.md')
r = rpath.read_text(encoding='utf-8')
old = 'independent forward/return SVG + editable draw.io packet-flow pairs for east-west, Internet egress, and Internet-inbound DNAT.'
new = 'independent forward/return SVG + editable draw.io packet-flow pairs for east-west, branch/ExpressRoute, Internet egress, and Internet-inbound DNAT.'
if old not in r:
    raise SystemExit('README summary anchor not found')
r = r.replace(old, new, 1)
rpath.write_text(r, encoding='utf-8')

for rel in [
    'images/09-05-26-20-00_branch_spoke_forward.svg',
    'images/09-05-26-20-00_branch_spoke_forward.drawio',
    'images/09-05-26-20-00_branch_spoke_return.svg',
    'images/09-05-26-20-00_branch_spoke_return.drawio',
]:
    if not Path(rel).exists():
        raise SystemExit('Missing ' + rel)
print('Branch forward/return diagrams validated.')
