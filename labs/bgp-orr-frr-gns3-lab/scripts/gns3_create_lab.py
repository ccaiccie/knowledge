#!/usr/bin/env python3
"""Create the FRR BGP RR / ADD-PATH lab through the GNS3 v2 controller API.

The script intentionally creates Docker nodes directly rather than adding a
global GNS3 template.  It therefore leaves the user's template inventory
unchanged and puts each node's FRR configuration in its own environment.
"""

from __future__ import annotations

import argparse
import base64
import csv
import json
import ssl
import sys
from datetime import datetime, timezone
from pathlib import Path
from typing import Any
from urllib import error as urlerror
from urllib import request as urlrequest

LAB_DIR = Path(__file__).resolve().parents[1]
DEFAULT_IMAGE = "orr-frr:10.7.0"
DEFAULT_START_COMMAND = "/usr/local/bin/orr-lab-start"


class Gns3ApiError(RuntimeError):
    """Raised for an unexpected GNS3 controller response."""


class Gns3Client:
    def __init__(
        self,
        base_url: str,
        *,
        username: str | None,
        password: str | None,
        headers: list[str],
        verify_tls: bool,
    ) -> None:
        self.base_url = base_url.rstrip("/")
        self.headers: dict[str, str] = {"Accept": "application/json"}
        self.ssl_context = None if verify_tls else ssl._create_unverified_context()
        if username:
            credentials = f"{username}:{password or ''}".encode("utf-8")
            token = base64.b64encode(credentials).decode("ascii")
            self.headers["Authorization"] = f"Basic {token}"
        for header in headers:
            name, separator, value = header.partition(":")
            if not separator or not name.strip():
                raise ValueError(f"Invalid --header value {header!r}; use 'Name: Value'.")
            self.headers[name.strip()] = value.strip()

    def request(
        self,
        method: str,
        path: str,
        *,
        payload: dict[str, Any] | None = None,
        expected: tuple[int, ...] = (200,),
    ) -> Any:
        headers = dict(self.headers)
        data = None
        if payload is not None:
            data = json.dumps(payload).encode("utf-8")
            headers["Content-Type"] = "application/json"
        request = urlrequest.Request(
            f"{self.base_url}{path}", data=data, headers=headers, method=method
        )
        try:
            with urlrequest.urlopen(request, timeout=30, context=self.ssl_context) as response:
                status = response.status
                content = response.read()
        except urlerror.HTTPError as error:
            detail = error.read().decode("utf-8", errors="replace").strip().replace("\n", " ")
            raise Gns3ApiError(
                f"{method} {path} returned HTTP {error.code}: {detail[:1000]}"
            ) from error
        except urlerror.URLError as error:
            raise Gns3ApiError(f"{method} {path} could not reach {self.base_url}: {error.reason}") from error

        if status not in expected:
            detail = content.decode("utf-8", errors="replace").strip().replace("\n", " ")
            raise Gns3ApiError(f"{method} {path} returned HTTP {status}: {detail[:1000]}")
        if not content:
            return None
        return json.loads(content.decode("utf-8"))


def read_csv(filename: Path) -> list[dict[str, str]]:
    with filename.open(newline="", encoding="utf-8") as source:
        return list(csv.DictReader(source))


def load_config(node_name: str, scenario: str) -> str:
    scenario_file = LAB_DIR / "configs" / scenario / f"{node_name}.conf"
    common_file = LAB_DIR / "configs" / "common" / f"{node_name}.conf"
    chosen = scenario_file if scenario_file.exists() else common_file
    if not chosen.exists():
        raise FileNotFoundError(f"No configuration exists for {node_name}: {chosen}")
    return chosen.read_text(encoding="utf-8")


def encode_environment(config: str, daemons: str) -> str:
    config_b64 = base64.b64encode(config.encode("utf-8")).decode("ascii")
    daemons_b64 = base64.b64encode(daemons.encode("utf-8")).decode("ascii")
    return f"FRR_CONFIG_B64={config_b64}\nFRR_DAEMONS_B64={daemons_b64}"


def endpoint_adapter(link: dict[str, str], endpoint: str) -> int:
    """Return a Docker adapter index from the current or legacy CSV column.

    A GNS3 Docker node has one Ethernet port (port 0) on each adapter.  The
    `a_adapter`/`b_adapter` columns therefore identify both the GNS3 adapter
    and the Linux interface number (`ethN`).  Accepting the old `*_port`
    spelling makes an already-downloaded links.csv work with this fixed script.
    """

    for field in (f"{endpoint}_adapter", f"{endpoint}_port"):
        value = link.get(field)
        if value and value.strip():
            try:
                adapter = int(value)
            except ValueError as error:
                raise ValueError(f"{field} must be an integer, got {value!r}") from error
            if adapter < 0:
                raise ValueError(f"{field} must be zero or greater, got {adapter}")
            return adapter
    raise ValueError(
        f"Link {link.get('a', '?')!r}-{link.get('b', '?')!r} is missing "
        f"{endpoint}_adapter."
    )


def adapter_counts(links: list[dict[str, str]]) -> dict[str, int]:
    counts: dict[str, int] = {}
    for link in links:
        for endpoint in ("a", "b"):
            node = link[endpoint]
            needed = endpoint_adapter(link, endpoint) + 1
            counts[node] = max(counts.get(node, 0), needed)
    return counts


def build_plan(scenario: str, image: str, start_command: str) -> dict[str, Any]:
    nodes = read_csv(LAB_DIR / "nodes.csv")
    links = read_csv(LAB_DIR / "links.csv")
    daemons = (LAB_DIR / "docker" / "daemons").read_text(encoding="utf-8")
    adapters = adapter_counts(links)

    node_payloads: list[dict[str, Any]] = []
    for node in nodes:
        name = node["name"]
        node_payloads.append(
            {
                "name": name,
                "node_type": "docker",
                "x": int(node["x"]),
                "y": int(node["y"]),
                "console_type": "telnet",
                "properties": {
                    "image": image,
                    "adapters": adapters[name],
                    "start_command": start_command,
                    "environment": encode_environment(load_config(name, scenario), daemons),
                },
            }
        )
    return {"nodes": node_payloads, "links": links}


def create_project(client: Gns3Client, name: str) -> dict[str, Any]:
    return client.request(
        "POST",
        "/v2/projects",
        payload={
            "name": name,
            "auto_close": False,
            "auto_open": False,
            "auto_start": False,
            "show_interface_labels": True,
        },
        expected=(201,),
    )


def create_nodes(
    client: Gns3Client,
    project_id: str,
    node_payloads: list[dict[str, Any]],
    compute_id: str,
) -> dict[str, str]:
    node_ids: dict[str, str] = {}
    for payload in node_payloads:
        payload = {**payload, "compute_id": compute_id}
        node = client.request(
            "POST",
            f"/v2/projects/{project_id}/nodes",
            payload=payload,
            expected=(201,),
        )
        expected_ports = {
            (adapter_number, 0)
            for adapter_number in range(int(payload["properties"]["adapters"]))
        }
        actual_ports = {
            (int(port["adapter_number"]), int(port["port_number"]))
            for port in node.get("ports", [])
        }
        missing_ports = expected_ports - actual_ports
        if missing_ports:
            expected = ", ".join(f"{adapter}/0" for adapter, _ in sorted(expected_ports))
            actual = ", ".join(f"{adapter}/{port}" for adapter, port in sorted(actual_ports))
            raise Gns3ApiError(
                f"Node {payload['name']} did not expose the expected Docker ports "
                f"({expected}); GNS3 returned ({actual or 'none'})."
            )
        node_ids[payload["name"]] = node["node_id"]
        print(f"Created {payload['name']}: {node['node_id']}")
    return node_ids


def create_links(
    client: Gns3Client,
    project_id: str,
    links: list[dict[str, str]],
    node_ids: dict[str, str],
) -> None:
    for link in links:
        a_adapter = endpoint_adapter(link, "a")
        b_adapter = endpoint_adapter(link, "b")
        payload = {
            "nodes": [
                {
                    "node_id": node_ids[link["a"]],
                    "adapter_number": a_adapter,
                    "port_number": 0,
                    "label": {"text": link["label"]},
                },
                {
                    "node_id": node_ids[link["b"]],
                    "adapter_number": b_adapter,
                    "port_number": 0,
                },
            ]
        }
        client.request(
            "POST",
            f"/v2/projects/{project_id}/links",
            payload=payload,
            expected=(201,),
        )
        print(
            f"Linked {link['a']} adapter {a_adapter} (eth{a_adapter}) to "
            f"{link['b']} adapter {b_adapter} (eth{b_adapter})"
        )


def start_nodes(client: Gns3Client, project_id: str, node_ids: dict[str, str]) -> None:
    for name, node_id in node_ids.items():
        client.request(
            "POST",
            f"/v2/projects/{project_id}/nodes/{node_id}/start",
            expected=(200, 201, 202, 204),
        )
        print(f"Started {name}")


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--server",
        default="http://127.0.0.1:3080",
        help="GNS3 controller URL (default: %(default)s)",
    )
    parser.add_argument(
        "--scenario",
        choices=("standard", "addpath"),
        default="standard",
        help="standard exposes RR path hiding; addpath exposes both exit paths to clients",
    )
    parser.add_argument(
        "--project-name",
        help="Project name. The default includes the scenario and a UTC timestamp.",
    )
    parser.add_argument(
        "--compute-id",
        default="local",
        help="GNS3 compute ID hosting Docker nodes (default: %(default)s)",
    )
    parser.add_argument(
        "--image",
        default=DEFAULT_IMAGE,
        help="Docker image built by scripts/build-image.sh (default: %(default)s)",
    )
    parser.add_argument(
        "--start-command",
        default=DEFAULT_START_COMMAND,
        help="Command supplied to each Docker node (default: %(default)s)",
    )
    parser.add_argument("--username", help="Optional HTTP basic-auth username")
    parser.add_argument("--password", help="Optional HTTP basic-auth password")
    parser.add_argument(
        "--header",
        action="append",
        default=[],
        help="Additional HTTP header, repeatable; for example 'Authorization: Bearer TOKEN'",
    )
    parser.add_argument("--insecure", action="store_true", help="Disable TLS certificate verification")
    parser.add_argument("--no-start", action="store_true", help="Create the project but do not start nodes")
    parser.add_argument("--dry-run", action="store_true", help="Print the sanitized build plan and exit")
    parser.add_argument(
        "--manifest",
        type=Path,
        help="Where to write created project and node identifiers",
    )
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    plan = build_plan(args.scenario, args.image, args.start_command)

    if args.dry_run:
        print(
            json.dumps(
                {
                    "scenario": args.scenario,
                    "nodes": [
                        {
                            "name": node["name"],
                            "node_type": node["node_type"],
                            "x": node["x"],
                            "y": node["y"],
                            "image": node["properties"]["image"],
                            "adapters": node["properties"]["adapters"],
                        }
                        for node in plan["nodes"]
                    ],
                    "links": plan["links"],
                },
                indent=2,
            )
        )
        return 0

    client = Gns3Client(
        args.server,
        username=args.username,
        password=args.password,
        headers=args.header,
        verify_tls=not args.insecure,
    )
    client.request("GET", "/v2/version", expected=(200,))

    timestamp = datetime.now(timezone.utc).strftime("%Y%m%d-%H%M%S")
    project_name = args.project_name or f"BGP-ORR-FRR-{args.scenario}-{timestamp}"
    project = create_project(client, project_name)
    project_id = project["project_id"]
    print(f"Created project {project_name}: {project_id}")

    try:
        node_ids = create_nodes(client, project_id, plan["nodes"], args.compute_id)
        create_links(client, project_id, plan["links"], node_ids)
        if not args.no_start:
            start_nodes(client, project_id, node_ids)
    except Exception:
        print(
            f"Creation stopped. The partial project remains in GNS3 as {project_id}; "
            "inspect or remove it in the GNS3 UI.",
            file=sys.stderr,
        )
        raise

    manifest = {
        "project_id": project_id,
        "project_name": project_name,
        "server": args.server,
        "scenario": args.scenario,
        "image": args.image,
        "node_ids": node_ids,
        "created_utc": datetime.now(timezone.utc).isoformat(),
    }
    output = args.manifest or LAB_DIR / f"gns3-manifest-{project_id}.json"
    output.write_text(json.dumps(manifest, indent=2) + "\n", encoding="utf-8")
    print(f"Manifest: {output}")
    print("Wait for OSPF and iBGP to converge, then follow README.md verification steps.")
    return 0


if __name__ == "__main__":
    try:
        raise SystemExit(main())
    except (FileNotFoundError, ValueError, OSError, Gns3ApiError) as error:
        print(f"ERROR: {error}", file=sys.stderr)
        raise SystemExit(1)
