"""Agente 5: estrutura a arquitetura consolidada como especificacao YAML."""

from __future__ import annotations

import csv
import json
from io import StringIO


def _yaml_string(value: str) -> str:
    return json.dumps(str(value or ""), ensure_ascii=False)


def gerar_especificacao_yaml(system_name: str, consolidated_csv: str) -> str:
    """Generate YAML exclusively from the consolidated architecture CSV."""
    rows = []
    reader = csv.reader(StringIO(consolidated_csv or ""))
    for row in reader:
        if len(row) < 3 or row[0].strip().lower() == "microservice":
            continue
        service = row[0].strip()
        responsibilities = [item.strip() for item in row[1].split(";") if item.strip()]
        dependencies = [item.strip() for item in row[2].split(";") if item.strip()]
        rows.append((service, responsibilities, dependencies))

    lines = [
        f"system: {_yaml_string(system_name)}",
        "services:",
    ]
    for service, responsibilities, dependencies in rows:
        lines.extend([
            f"  - name: {_yaml_string(service)}",
            "    responsibilities:",
        ])
        lines.extend(f"      - {_yaml_string(item)}" for item in responsibilities or [""])
        lines.append("    dependencies:")
        lines.extend(f"      - {_yaml_string(item)}" for item in dependencies or [""])
        lines.append("    suggested_endpoints:")
        lines.extend([
            f"      - {_yaml_string(f'/api/{service.lower().replace(' ', '-').replace('_', '-')}')}",
        ])

    lines.append("interactions:")
    seen = set()
    for service, _, dependencies in rows:
        for dependency in dependencies:
            pair = (service, dependency)
            if pair in seen:
                continue
            seen.add(pair)
            lines.extend([
                "  - from: " + _yaml_string(service),
                "    to: " + _yaml_string(dependency),
            ])
    return "\n".join(lines) + "\n"
