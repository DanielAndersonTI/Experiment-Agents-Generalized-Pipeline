"""Convert flexible interface text into pipeline input structures."""

from __future__ import annotations

import re


def _tokens(text: str) -> list[str]:
    return [token.strip() for token in re.split(r"[,;|\n]+", text or "") if token.strip()]


def parse_reference_services(text: str) -> list:
    """Parse service names separated by lines, commas, semicolons, or pipes."""
    result = []
    seen = set()
    for service in _tokens(text):
        if service not in seen:
            result.append(service)
            seen.add(service)
    return result


def parse_reference_interactions(text: str) -> set:
    """Parse undirected, sorted interaction pairs from flexible text."""
    interactions = set()
    for group in re.split(r"[;|\n]+", text or ""):
        group = group.strip()
        if not group:
            continue
        comma_parts = [part.strip() for part in group.split(",") if part.strip()]
        if any(re.search(r"<->|->", item) for item in comma_parts):
            for item in comma_parts:
                arrow_parts = re.split(r"\s*(?:<->|->)\s*", item, maxsplit=1)
                if len(arrow_parts) == 2:
                    left, right = (part.strip() for part in arrow_parts)
                    if left and right and left != right:
                        interactions.add(tuple(sorted((left, right))))
            continue
        for index in range(0, len(comma_parts) - 1, 2):
            left, right = comma_parts[index:index + 2]
            if left != right:
                interactions.add(tuple(sorted((left, right))))
    return interactions


def parse_name_map(text: str) -> dict:
    """Parse alias-to-canonical mappings separated by lines, semicolons, or pipes."""
    result = {}
    for item in re.split(r"[;|\n]+", text or ""):
        item = item.strip()
        if not item:
            continue
        parts = re.split(r"\s*(?:->|,)\s*", item, maxsplit=1)
        if len(parts) == 2:
            alias, canonical = (part.strip() for part in parts)
            if alias and canonical:
                result[alias] = canonical
    return result
