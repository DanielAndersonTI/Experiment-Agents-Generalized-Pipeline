from __future__ import annotations

import csv
import json
import re
from collections import Counter, defaultdict
from datetime import datetime, timezone
from pathlib import Path
from typing import Any
import xml.etree.ElementTree as ET


REPO_ROOT = Path(__file__).resolve().parent.parent
SYSTEMS_DIR = REPO_ROOT / "systems"
OUTPUT_ROOT = REPO_ROOT / "analysis-results" / "static-analysis"

IGNORED_DIR_NAMES = {
    ".git",
    ".github",
    ".gradle",
    ".idea",
    ".vscode",
    "build",
    "dist",
    "node_modules",
    "out",
    "target",
}

TYPE_DECLARATION_RE = re.compile(
    r"(?m)^\s*(?:public|protected|private|abstract|final|sealed|non-sealed|static|\s)*"
    r"\b(class|interface|enum|record|@interface)\s+([A-Za-z_]\w*)"
)

ANNOTATION_RE = re.compile(r"(?m)^\s*@([A-Za-z_][\w.]*)")
PACKAGE_RE = re.compile(r"(?m)^\s*package\s+([A-Za-z_][\w.]*)\s*;")
IMPORT_RE = re.compile(r"(?m)^\s*import\s+(static\s+)?([A-Za-z_][\w.*]*)\s*;")
MAIN_METHOD_RE = re.compile(r"\bpublic\s+static\s+void\s+main\s*\(")

METHOD_RE = re.compile(
    r"""(?mx)
    ^\s*
    (?:@[\w.]+\s*(?:\([^)]*\))?\s*)*
    (?:
      (?:public|protected|private|static|final|abstract|synchronized|native|strictfp|default|sealed|non-sealed)\s+
    )*
    (?:<[^>{};\n]+>\s*)?
    (?:[\w\[\].<>?,@]+\s+)+
    (?P<name>[A-Za-z_]\w*)
    \s*\([^;{}()]*\)
    (?:\s*throws\s+[^{;]+)?
    \s*\{
    """
)

CONSTRUCTOR_RE = re.compile(
    r"""(?mx)
    ^\s*
    (?:@[\w.]+\s*(?:\([^)]*\))?\s*)*
    (?:
      (?:public|protected|private)\s+
    )?
    (?P<name>[A-Z][A-Za-z0-9_]*)
    \s*\([^;{}()]*\)
    (?:\s*throws\s+[^{;]+)?
    \s*\{
    """
)

SIMPLE_CONTROLLER_ANNOTATIONS = {
    "Controller",
    "RestController",
    "Path",
    "WebServlet",
}
SIMPLE_SERVICE_ANNOTATIONS = {"Service"}
SIMPLE_REPOSITORY_ANNOTATIONS = {"Repository"}
SIMPLE_CONFIGURATION_ANNOTATIONS = {"Configuration"}
SIMPLE_DOMAIN_ANNOTATIONS = {"Entity", "Embeddable", "MappedSuperclass", "Document"}
SIMPLE_BOOT_ANNOTATIONS = {"SpringBootApplication", "ApplicationPath"}


def read_text(path: Path) -> str:
    for encoding in ("utf-8", "utf-8-sig", "latin-1"):
        try:
            return path.read_text(encoding=encoding)
        except UnicodeDecodeError:
            continue
    return path.read_text(encoding="utf-8", errors="replace")


def should_skip_dir(path: Path) -> bool:
    return any(part in IGNORED_DIR_NAMES for part in path.parts)


def iter_project_files(project_root: Path, pattern: str) -> list[Path]:
    files: list[Path] = []
    for candidate in project_root.rglob(pattern):
        if candidate.is_file() and not should_skip_dir(candidate):
            files.append(candidate)
    return sorted(files)


def strip_comments(text: str) -> str:
    comment_re = re.compile(r"//.*?$|/\*.*?\*/", re.MULTILINE | re.DOTALL)

    def replace(match: re.Match[str]) -> str:
        return "\n" * match.group(0).count("\n")

    return comment_re.sub(replace, text)


def strip_string_literals(text: str) -> str:
    string_re = re.compile(r'"(?:\\.|[^"\\])*"|\'(?:\\.|[^\'\\])*\'', re.DOTALL)
    return string_re.sub('""', text)


def sanitize_java(text: str) -> str:
    return strip_string_literals(strip_comments(text))


def relative_to_repo(path: Path) -> str:
    return path.relative_to(REPO_ROOT).as_posix()


def detect_source_root(java_file: Path) -> tuple[str, str]:
    normalized = java_file.as_posix()
    match = re.search(r"(.*/src(?:/[^/]+)*/java)/", normalized)
    if not match:
        return (java_file.parent.as_posix(), "other-java")

    source_root = Path(match.group(1))
    relative_source_root = relative_to_repo(source_root)
    source_root_lower = relative_source_root.lower()

    if "/ui_tests/" in source_root_lower:
        return (relative_source_root, "ui-test")
    if source_root_lower.endswith("/src/main/java"):
        return (relative_source_root, "main")
    if source_root_lower.endswith("/src/test/java"):
        return (relative_source_root, "test")
    return (relative_source_root, "other-java")


def parse_package(text: str) -> str:
    match = PACKAGE_RE.search(text)
    return match.group(1) if match else "(default)"


def parse_imports(text: str) -> list[dict[str, Any]]:
    imports: list[dict[str, Any]] = []
    for is_static, target in IMPORT_RE.findall(text):
        imports.append(
            {
                "target": target.strip(),
                "is_static": bool(is_static.strip()) if is_static else False,
            }
        )
    return imports


def parse_annotations(text: str) -> list[str]:
    return [annotation.split(".")[-1] for annotation in ANNOTATION_RE.findall(text)]


def parse_primary_type(sanitized_text: str, file_stem: str) -> tuple[str, str]:
    matches = TYPE_DECLARATION_RE.findall(sanitized_text)
    if not matches:
        return ("unknown", file_stem)

    for kind, name in matches:
        if name == file_stem:
            return (kind, name)

    kind, name = matches[0]
    return (kind, name)


def count_methods(sanitized_text: str) -> tuple[int, int]:
    matches = list(METHOD_RE.finditer(sanitized_text))
    constructors = list(CONSTRUCTOR_RE.finditer(sanitized_text))

    method_count = len(matches) + len(constructors)
    public_method_count = 0

    for match in matches + constructors:
        signature = match.group(0)
        if re.search(r"\bpublic\b", signature):
            public_method_count += 1

    return (method_count, public_method_count)


def infer_role(package_name: str, annotations: list[str], source_set: str, type_name: str) -> str:
    package_lower = package_name.lower()
    annotation_set = set(annotations)

    if source_set in {"test", "ui-test"}:
        return "test"
    if annotation_set & SIMPLE_CONTROLLER_ANNOTATIONS:
        return "controller"
    if annotation_set & SIMPLE_SERVICE_ANNOTATIONS:
        return "service"
    if annotation_set & SIMPLE_REPOSITORY_ANNOTATIONS:
        return "repository"
    if annotation_set & SIMPLE_CONFIGURATION_ANNOTATIONS:
        return "configuration"
    if annotation_set & SIMPLE_DOMAIN_ANNOTATIONS:
        return "domain"
    if any(token in package_lower for token in (".controller", ".web", ".rest", ".servlet", ".api")):
        return "controller"
    if any(token in package_lower for token in (".service", ".application")):
        return "service"
    if any(token in package_lower for token in (".repository", ".dao")):
        return "repository"
    if any(token in package_lower for token in (".domain", ".model", ".entity")):
        return "domain"
    if any(token in package_lower for token in (".config", ".configuration")):
        return "configuration"
    if any(token in package_lower for token in (".event", ".listener")):
        return "event"
    if ".aspect" in package_lower:
        return "aspect"
    if any(token in package_lower for token in (".exception", ".error")):
        return "exception"
    if any(token in package_lower for token in (".persistence", ".jdbc", ".mongo")):
        return "persistence"
    if any(token in package_lower for token in (".util", ".helper")):
        return "utility"
    if any(token in package_lower for token in (".ui", ".view")):
        return "ui"
    if type_name.endswith("Application"):
        return "bootstrap"
    return "other"


def infer_entrypoint_reasons(type_name: str, annotations: list[str], sanitized_text: str) -> list[str]:
    reasons: list[str] = []
    annotation_set = set(annotations)

    if MAIN_METHOD_RE.search(sanitized_text):
        reasons.append("main-method")
    if annotation_set & SIMPLE_BOOT_ANNOTATIONS:
        reasons.append("application-bootstrap")
    if annotation_set & SIMPLE_CONTROLLER_ANNOTATIONS:
        reasons.append("http-entrypoint")
    if type_name.endswith("Application") and "application-bootstrap" not in reasons:
        reasons.append("application-class")

    return reasons


def import_to_package(import_target: str) -> str:
    if import_target.endswith(".*"):
        return import_target[:-2]
    if "." not in import_target:
        return "(default)"
    return import_target.rsplit(".", 1)[0]


def is_internal_import(import_target: str, known_types: set[str], known_packages: set[str]) -> bool:
    if import_target.endswith(".*"):
        package_name = import_target[:-2]
        return any(
            known_package == package_name or known_package.startswith(package_name + ".")
            for known_package in known_packages
        )

    if import_target in known_types:
        return True

    package_name = import_to_package(import_target)
    return package_name in known_packages


def external_dependency_root(import_target: str) -> str:
    package_name = import_to_package(import_target)
    parts = [part for part in package_name.split(".") if part]
    if not parts:
        return "(default)"

    if parts[0] in {"java", "javax", "jakarta"}:
        return ".".join(parts[: min(2, len(parts))])

    return ".".join(parts[: min(3, len(parts))])


def find_project_roots() -> list[Path]:
    if not SYSTEMS_DIR.exists():
        raise FileNotFoundError(f"Could not find systems directory at {SYSTEMS_DIR}")

    return sorted(path for path in SYSTEMS_DIR.iterdir() if path.is_dir())


def discover_build_files(project_root: Path) -> list[Path]:
    build_files: list[Path] = []
    for candidate in iter_project_files(project_root, "pom.xml"):
        build_files.append(candidate)
    for candidate in iter_project_files(project_root, "build.gradle"):
        build_files.append(candidate)
    for candidate in iter_project_files(project_root, "build.gradle.kts"):
        build_files.append(candidate)
    return sorted(set(build_files))


def detect_java_version_from_gradle(text: str) -> str | None:
    patterns = [
        r"JavaLanguageVersion\.of\((\d+)\)",
        r"sourceCompatibility\s*=\s*['\"]?([\d.]+)",
        r"targetCompatibility\s*=\s*['\"]?([\d.]+)",
        r"VERSION_(\d+)\b",
    ]
    for pattern in patterns:
        match = re.search(pattern, text)
        if match:
            return match.group(1)
    return None


def parse_gradle_module(build_file: Path, project_root: Path) -> dict[str, Any]:
    text = read_text(build_file)
    plugins = re.findall(r"id\s*[\(\s]['\"]([^'\"]+)['\"]", text)

    java_version = detect_java_version_from_gradle(text)
    module_path = build_file.parent.relative_to(project_root).as_posix() or "."

    return {
        "module_path": module_path,
        "build_tool": "gradle",
        "build_file": relative_to_repo(build_file),
        "artifact_id": build_file.parent.name,
        "packaging": "war" if "war" in plugins else "jar",
        "java_version": java_version or "",
        "plugins": sorted(set(plugins)),
        "declared_submodules": [],
    }


def xml_namespace(root: ET.Element) -> dict[str, str]:
    if root.tag.startswith("{"):
        return {"m": root.tag.split("}", 1)[0][1:]}
    return {}


def namespaced(tag: str, namespace: dict[str, str]) -> str:
    if not namespace:
        return tag
    return f"m:{tag}"


def find_text(element: ET.Element, path: str, namespace: dict[str, str]) -> str:
    value = element.findtext(path, namespaces=namespace)
    return value.strip() if value else ""


def parse_pom_module(build_file: Path, project_root: Path) -> dict[str, Any]:
    root = ET.fromstring(build_file.read_bytes())
    namespace = xml_namespace(root)

    properties_element = root.find(namespaced("properties", namespace), namespaces=namespace)
    properties: dict[str, str] = {}
    if properties_element is not None:
        for child in list(properties_element):
            key = child.tag.split("}", 1)[-1]
            properties[key] = (child.text or "").strip()

    declared_modules = [
        (module.text or "").strip()
        for module in root.findall(f"./{namespaced('modules', namespace)}/{namespaced('module', namespace)}", namespace)
        if (module.text or "").strip()
    ]

    java_version = (
        properties.get("java.version")
        or properties.get("java.release")
        or properties.get("maven.compiler.release")
        or properties.get("maven.compiler.source")
        or properties.get("maven.compiler.target")
    )

    artifact_id = find_text(root, namespaced("artifactId", namespace), namespace)
    packaging = find_text(root, namespaced("packaging", namespace), namespace) or "jar"
    module_path = build_file.parent.relative_to(project_root).as_posix() or "."

    return {
        "module_path": module_path,
        "build_tool": "maven",
        "build_file": relative_to_repo(build_file),
        "artifact_id": artifact_id or build_file.parent.name,
        "packaging": packaging,
        "java_version": java_version or "",
        "plugins": [],
        "declared_submodules": declared_modules,
    }


def parse_build_modules(project_root: Path) -> list[dict[str, Any]]:
    modules: list[dict[str, Any]] = []
    for build_file in discover_build_files(project_root):
        try:
            if build_file.name == "pom.xml":
                modules.append(parse_pom_module(build_file, project_root))
            else:
                modules.append(parse_gradle_module(build_file, project_root))
        except ET.ParseError as exc:
            modules.append(
                {
                    "module_path": build_file.parent.relative_to(project_root).as_posix() or ".",
                    "build_tool": "maven" if build_file.name == "pom.xml" else "gradle",
                    "build_file": relative_to_repo(build_file),
                    "artifact_id": build_file.parent.name,
                    "packaging": "",
                    "java_version": "",
                    "plugins": [],
                    "declared_submodules": [],
                    "parse_error": str(exc),
                }
            )
    return sorted(modules, key=lambda module: (module["module_path"], module["build_tool"]))


def map_file_to_module(java_file: Path, module_roots: dict[Path, dict[str, Any]], project_root: Path) -> str:
    best_match = project_root
    best_module_path = "."

    for module_root, module_data in module_roots.items():
        try:
            java_file.relative_to(module_root)
        except ValueError:
            continue

        if len(module_root.parts) > len(best_match.parts):
            best_match = module_root
            best_module_path = module_data["module_path"]

    return best_module_path


def analyze_project(project_root: Path) -> dict[str, Any]:
    modules = parse_build_modules(project_root)
    module_roots = {
        (project_root / module["module_path"]).resolve() if module["module_path"] != "." else project_root.resolve(): module
        for module in modules
    }

    java_files = iter_project_files(project_root, "*.java")
    source_roots: set[str] = set()
    raw_records: list[dict[str, Any]] = []
    known_packages: set[str] = set()
    known_types: set[str] = set()
    role_counter: Counter[str] = Counter()

    for java_file in java_files:
        source_root, source_set = detect_source_root(java_file)
        source_roots.add(source_root)

        if java_file.name in {"package-info.java", "module-info.java"}:
            continue

        text = read_text(java_file)
        sanitized_text = sanitize_java(text)
        package_name = parse_package(text)
        annotations = parse_annotations(text)
        type_kind, type_name = parse_primary_type(sanitized_text, java_file.stem)
        method_count, public_method_count = count_methods(sanitized_text)
        role = infer_role(package_name, annotations, source_set, type_name)
        entrypoint_reasons = infer_entrypoint_reasons(type_name, annotations, sanitized_text)
        module_path = map_file_to_module(java_file.resolve(), module_roots, project_root.resolve())
        effective_line_count = sum(1 for line in strip_comments(text).splitlines() if line.strip())

        record = {
            "project": project_root.name,
            "module": module_path,
            "source_set": source_set,
            "source_root": source_root,
            "file": relative_to_repo(java_file),
            "package": package_name,
            "type_name": type_name,
            "type_kind": type_kind,
            "role": role,
            "annotations": annotations,
            "imports": parse_imports(text),
            "line_count": len(text.splitlines()),
            "effective_line_count": effective_line_count,
            "method_count": method_count,
            "public_method_count": public_method_count,
            "entrypoint_reasons": entrypoint_reasons,
            "has_main_method": "main-method" in entrypoint_reasons,
            "is_entrypoint": bool(entrypoint_reasons),
        }
        raw_records.append(record)

        fqcn = type_name if package_name == "(default)" else f"{package_name}.{type_name}"
        known_types.add(fqcn)
        known_packages.add(package_name)
        role_counter[role] += 1

    package_edges: Counter[tuple[str, str, str]] = Counter()
    external_roots: Counter[str] = Counter()
    package_metrics: dict[str, dict[str, Any]] = defaultdict(
        lambda: {
            "package": "",
            "class_count": 0,
            "method_count": 0,
            "public_method_count": 0,
            "incoming_internal_dependencies": 0,
            "outgoing_internal_dependencies": 0,
            "roles": Counter(),
        }
    )

    class_rows: list[dict[str, Any]] = []
    entrypoints: list[dict[str, Any]] = []

    for record in raw_records:
        internal_import_count = 0
        external_import_count = 0

        package_metrics[record["package"]]["package"] = record["package"]
        package_metrics[record["package"]]["class_count"] += 1
        package_metrics[record["package"]]["method_count"] += record["method_count"]
        package_metrics[record["package"]]["public_method_count"] += record["public_method_count"]
        package_metrics[record["package"]]["roles"][record["role"]] += 1

        for imported in record["imports"]:
            target = imported["target"]
            target_package = import_to_package(target)
            category = "internal" if is_internal_import(target, known_types, known_packages) else "external"

            if category == "internal":
                internal_import_count += 1
            else:
                external_import_count += 1
                external_roots[external_dependency_root(target)] += 1

            if target_package != record["package"]:
                package_edges[(record["package"], target_package, category)] += 1

        row = {
            "project": record["project"],
            "module": record["module"],
            "source_set": record["source_set"],
            "source_root": record["source_root"],
            "file": record["file"],
            "package": record["package"],
            "type_name": record["type_name"],
            "type_kind": record["type_kind"],
            "role": record["role"],
            "line_count": record["line_count"],
            "effective_line_count": record["effective_line_count"],
            "method_count": record["method_count"],
            "public_method_count": record["public_method_count"],
            "import_count": len(record["imports"]),
            "internal_import_count": internal_import_count,
            "external_import_count": external_import_count,
            "has_main_method": record["has_main_method"],
            "is_entrypoint": record["is_entrypoint"],
            "entrypoint_reasons": "|".join(record["entrypoint_reasons"]),
            "annotations": "|".join(record["annotations"]),
        }
        class_rows.append(row)

        if record["is_entrypoint"]:
            entrypoints.append(
                {
                    "project": record["project"],
                    "module": record["module"],
                    "package": record["package"],
                    "type_name": record["type_name"],
                    "file": record["file"],
                    "entrypoint_reasons": "|".join(record["entrypoint_reasons"]),
                }
            )

    dependency_rows: list[dict[str, Any]] = []
    for (source_package, target_package, category), count in sorted(
        package_edges.items(),
        key=lambda item: (-item[1], item[0][0], item[0][1], item[0][2]),
    ):
        dependency_rows.append(
            {
                "project": project_root.name,
                "source_package": source_package,
                "target_package": target_package,
                "category": category,
                "count": count,
            }
        )

        if category == "internal":
            package_metrics[source_package]["outgoing_internal_dependencies"] += count
            package_metrics[target_package]["incoming_internal_dependencies"] += count

    package_rows: list[dict[str, Any]] = []
    for package_name, metrics in sorted(package_metrics.items()):
        package_rows.append(
            {
                "project": project_root.name,
                "package": package_name,
                "class_count": metrics["class_count"],
                "method_count": metrics["method_count"],
                "public_method_count": metrics["public_method_count"],
                "incoming_internal_dependencies": metrics["incoming_internal_dependencies"],
                "outgoing_internal_dependencies": metrics["outgoing_internal_dependencies"],
                "roles": "|".join(
                    f"{role}:{count}" for role, count in sorted(metrics["roles"].items())
                ),
            }
        )

    main_classes = sum(1 for row in class_rows if row["source_set"] == "main")
    test_classes = sum(1 for row in class_rows if row["source_set"] == "test")
    ui_test_classes = sum(1 for row in class_rows if row["source_set"] == "ui-test")
    internal_dependency_edges = [row for row in dependency_rows if row["category"] == "internal"]
    external_dependency_edges = [row for row in dependency_rows if row["category"] == "external"]

    package_roots = Counter()
    for package_name in known_packages:
        if package_name == "(default)":
            continue
        package_parts = package_name.split(".")
        package_roots[".".join(package_parts[: min(3, len(package_parts))])] += 1

    summary = {
        "project": project_root.name,
        "project_path": relative_to_repo(project_root),
        "generated_at_utc": datetime.now(timezone.utc).isoformat(),
        "methodology": {
            "type": "source-static-analysis",
            "notes": [
                "Analise estatica baseada em codigo-fonte Java, estrutura de build e imports.",
                "Nao depende de compilacao local, pois o ambiente atual nao possui java/maven no PATH.",
            ],
        },
        "build_tools": sorted({module["build_tool"] for module in modules}),
        "counts": {
            "build_files": len(modules),
            "source_roots": len(source_roots),
            "java_files": len(java_files),
            "analyzed_type_files": len(class_rows),
            "packages": len(known_packages),
            "classes": len(class_rows),
            "entrypoints": len(entrypoints),
            "main_classes": main_classes,
            "test_classes": test_classes,
            "ui_test_classes": ui_test_classes,
            "internal_package_dependencies": len(internal_dependency_edges),
            "external_package_dependencies": len(external_dependency_edges),
        },
        "role_counts": dict(sorted(role_counter.items())),
        "source_roots": sorted(source_roots),
        "package_roots": [
            {"package_root": package_root, "package_count": count}
            for package_root, count in package_roots.most_common(10)
        ],
        "top_internal_dependencies": [
            row for row in internal_dependency_edges[:25]
        ],
        "top_external_dependency_roots": [
            {"dependency_root": dependency_root, "count": count}
            for dependency_root, count in external_roots.most_common(20)
        ],
    }

    return {
        "summary": summary,
        "modules": modules,
        "classes": class_rows,
        "package_dependencies": dependency_rows,
        "package_metrics": package_rows,
        "entrypoints": sorted(entrypoints, key=lambda row: (row["module"], row["package"], row["type_name"])),
    }


def ensure_parent(path: Path) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)


def write_json(path: Path, payload: Any) -> None:
    ensure_parent(path)
    path.write_text(json.dumps(payload, indent=2, ensure_ascii=False), encoding="utf-8")


def write_csv(path: Path, rows: list[dict[str, Any]], fieldnames: list[str]) -> None:
    ensure_parent(path)
    with path.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=fieldnames)
        writer.writeheader()
        for row in rows:
            normalized_row = {}
            for field in fieldnames:
                value = row.get(field, "")
                if isinstance(value, list):
                    normalized_row[field] = "|".join(str(item) for item in value)
                else:
                    normalized_row[field] = value
            writer.writerow(normalized_row)


def write_project_outputs(project_data: dict[str, Any]) -> None:
    project_name = project_data["summary"]["project"]
    project_output_dir = OUTPUT_ROOT / project_name
    project_output_dir.mkdir(parents=True, exist_ok=True)

    write_json(project_output_dir / "summary.json", project_data["summary"])

    write_csv(
        project_output_dir / "modules.csv",
        project_data["modules"],
        [
            "module_path",
            "build_tool",
            "build_file",
            "artifact_id",
            "packaging",
            "java_version",
            "plugins",
            "declared_submodules",
            "parse_error",
        ],
    )
    write_csv(
        project_output_dir / "classes.csv",
        project_data["classes"],
        [
            "project",
            "module",
            "source_set",
            "source_root",
            "file",
            "package",
            "type_name",
            "type_kind",
            "role",
            "line_count",
            "effective_line_count",
            "method_count",
            "public_method_count",
            "import_count",
            "internal_import_count",
            "external_import_count",
            "has_main_method",
            "is_entrypoint",
            "entrypoint_reasons",
            "annotations",
        ],
    )
    write_csv(
        project_output_dir / "package_dependencies.csv",
        project_data["package_dependencies"],
        [
            "project",
            "source_package",
            "target_package",
            "category",
            "count",
        ],
    )
    write_csv(
        project_output_dir / "package_metrics.csv",
        project_data["package_metrics"],
        [
            "project",
            "package",
            "class_count",
            "method_count",
            "public_method_count",
            "incoming_internal_dependencies",
            "outgoing_internal_dependencies",
            "roles",
        ],
    )
    write_csv(
        project_output_dir / "entrypoints.csv",
        project_data["entrypoints"],
        [
            "project",
            "module",
            "package",
            "type_name",
            "file",
            "entrypoint_reasons",
        ],
    )


def write_index(all_projects: list[dict[str, Any]]) -> None:
    OUTPUT_ROOT.mkdir(parents=True, exist_ok=True)

    summary_rows = []
    for project_data in all_projects:
        summary = project_data["summary"]
        counts = summary["counts"]
        summary_rows.append(
            {
                "project": summary["project"],
                "project_path": summary["project_path"],
                "build_tools": "|".join(summary["build_tools"]),
                "build_files": counts["build_files"],
                "source_roots": counts["source_roots"],
                "java_files": counts["java_files"],
                "analyzed_type_files": counts["analyzed_type_files"],
                "packages": counts["packages"],
                "classes": counts["classes"],
                "entrypoints": counts["entrypoints"],
                "main_classes": counts["main_classes"],
                "test_classes": counts["test_classes"],
                "ui_test_classes": counts["ui_test_classes"],
                "internal_package_dependencies": counts["internal_package_dependencies"],
                "external_package_dependencies": counts["external_package_dependencies"],
            }
        )

    write_json(
        OUTPUT_ROOT / "index.json",
        {
            "generated_at_utc": datetime.now(timezone.utc).isoformat(),
            "projects_analyzed": [project["summary"]["project"] for project in all_projects],
            "project_count": len(all_projects),
            "projects": [project["summary"] for project in all_projects],
        },
    )
    write_csv(
        OUTPUT_ROOT / "project_summaries.csv",
        summary_rows,
        [
            "project",
            "project_path",
            "build_tools",
            "build_files",
            "source_roots",
            "java_files",
            "analyzed_type_files",
            "packages",
            "classes",
            "entrypoints",
            "main_classes",
            "test_classes",
            "ui_test_classes",
            "internal_package_dependencies",
            "external_package_dependencies",
        ],
    )
    write_json(
        OUTPUT_ROOT / "manifest.json",
        {
            "output_root": relative_to_repo(OUTPUT_ROOT),
            "artifacts_per_project": [
                "summary.json",
                "modules.csv",
                "classes.csv",
                "package_dependencies.csv",
                "package_metrics.csv",
                "entrypoints.csv",
            ],
            "consolidated_artifacts": ["index.json", "project_summaries.csv", "manifest.json"],
        },
    )


def main() -> None:
    projects = find_project_roots()
    all_projects: list[dict[str, Any]] = []

    for project_root in projects:
        project_data = analyze_project(project_root)
        write_project_outputs(project_data)
        all_projects.append(project_data)

    write_index(all_projects)

    print(f"Analise estatica concluida para {len(all_projects)} projetos.")
    print(f"Resultados gravados em: {relative_to_repo(OUTPUT_ROOT)}")


if __name__ == "__main__":
    main()
