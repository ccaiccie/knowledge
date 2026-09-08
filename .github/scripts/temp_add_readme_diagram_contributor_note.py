from pathlib import Path

p = Path('README.md')
s = p.read_text()
needle = "A browsable index of the technical study guides and labs in this repository. Each entry links directly to the Markdown article and summarizes the major concepts it covers.\n\n"
insert = """A browsable index of the technical study guides and labs in this repository. Each entry links directly to the Markdown article and summarizes the major concepts it covers.\n\n## Contributing diagrams\n\nContributors are welcome to improve the diagrams in this repository. For any architecture, topology, routing, packet-flow, NAT, HA, tunnel, protocol, or service-insertion diagram, please treat the matching `.drawio` file under `images/` as the **source of truth**.\n\nWhen changing a diagram:\n\n- Update the corresponding editable `.drawio` file first.\n- Regenerate or update the matching `.svg` so it represents the same nodes, labels, arrows, sequence, and relationships as the `.drawio` source.\n- Do not modify only the rendered `.svg` while leaving the `.drawio` file stale.\n- Keep arrows fully visible, readable, and clear of nodes and labels; use explicit routing/waypoints where needed.\n- Preserve the existing relative paths used by the Markdown guides unless the diagram is intentionally being renamed.\n\nThis keeps every published diagram editable and prevents the rendered SVG and its source from drifting apart.\n\n"
if needle not in s:
    raise SystemExit('README introduction anchor not found')
s = s.replace(needle, insert, 1)
p.write_text(s)
