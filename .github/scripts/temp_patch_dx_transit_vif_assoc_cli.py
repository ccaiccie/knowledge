from pathlib import Path
p=Path('09-08-26_AWS_Direct_Connect_Transit_VIF_Deep_Dive.md')
s=p.read_text()
old='''For same-account ownership, use the Direct Connect gateway association API/CLI with the TGW ID and allowed prefixes.\n\nConceptual intent:\n\n```text\nDXGW: corp-dxgw\nTGW:  tgw-0123456789abcdef0\nAllowed AWS prefix: 10.0.0.0/8\n```\n\nAcross accounts, AWS uses an association proposal workflow: the TGW owner creates the proposal and the DXGW owner accepts it.\n'''
new='''For same-account ownership, create the association directly and include the TGW allowed prefixes:\n\n```cli\naws directconnect create-direct-connect-gateway-association \\\n  --direct-connect-gateway-id DXGW_ID \\\n  --gateway-id tgw-0123456789abcdef0 \\\n  --add-allowed-prefixes-to-direct-connect-gateway cidr=10.0.0.0/8\n```\n\n**What this does:** it associates the TGW with the DXGW and tells the DXGW to advertise `10.0.0.0/8` toward on-premises for this TGW association. It does **not** create `10.0.0.0/8` as a TGW forwarding route; TGW still needs routes to the actual destination attachments.\n\nAcross accounts, AWS uses an association proposal workflow: the TGW owner creates the proposal and the DXGW owner accepts it.\n'''
if old not in s: raise SystemExit('target block not found')
p.write_text(s.replace(old,new,1))
