# Contributing

Thank you for helping improve this repository. Contributions that improve technical accuracy, clarity, diagrams, configuration examples, verification steps, and troubleshooting guidance are welcome.

## Diagram contribution requirements

For architecture, topology, routing, packet-flow, NAT, high-availability, tunnel, protocol, and service-insertion diagrams, the editable `.drawio` file under `images/` is the **source of truth**.

When changing a diagram:

1. Update the corresponding `.drawio` file first.
2. Regenerate or update the matching `.svg` from the same diagram.
3. Ensure the `.drawio` and `.svg` show the same nodes, labels, arrows, sequence numbers, packet paths, and relationships.
4. Do not modify only the rendered `.svg` while leaving the `.drawio` source stale.
5. Keep arrows fully visible and in front of background/container shapes.
6. Avoid arrows passing through nodes or overlapping labels. Use explicit waypoints, rounded/elbow connectors, and separate forward/return lanes when needed.
7. Make directionality and arrowheads unambiguous.
8. Preserve the existing relative file paths referenced by Markdown guides unless the diagram is intentionally being renamed; if renamed, update every Markdown reference.
9. Visually verify the final SVG before submitting the change.

For complex flows, prefer multiple focused diagrams over one overloaded diagram.

## Markdown and technical changes

When updating a study guide:

- Preserve existing source URLs and add authoritative sources for new technical claims.
- Prefer official vendor documentation for configuration syntax, limits, compatibility, and behavior.
- Do not invent commands, output, defaults, limits, routing behavior, NAT behavior, or unsupported combinations.
- Keep packet-flow descriptions explicit about interfaces/resources, route tables, next hops, policies, NAT points, state, and return-path symmetry.
- When reliable command output is known, include expected fields and success criteria; otherwise describe expected state rather than fabricating output.
- Keep related `.drawio` and `.svg` diagrams synchronized with any packet-flow or architecture changes.

## Before submitting

Please verify that:

- Markdown links resolve.
- Referenced images exist under `images/`.
- Every custom SVG diagram has a matching editable `.drawio` file.
- The SVG matches its `.drawio` source.
- Arrows, labels, and packet-flow direction are readable.
- Commands and configuration examples are source-supported.
- Existing content was not unintentionally removed.

The goal is to keep the repository technically useful while ensuring every published custom diagram remains editable for future contributors.
