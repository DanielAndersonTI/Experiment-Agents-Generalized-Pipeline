"""Local DAVINCI Architect server using Python's standard library only."""

from __future__ import annotations

import json
import mimetypes
import struct
import textwrap
import traceback
import zlib
from datetime import datetime
from http import HTTPStatus
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from threading import Lock
from urllib.parse import urlparse

try:
    from Interface.utils.pipeline_runner import run_real_pipeline
except ModuleNotFoundError:
    from utils.pipeline_runner import run_real_pipeline


HOST = "127.0.0.1"
PORT = 8000
BASE_DIR = Path(__file__).resolve().parent
PROJECT_ROOT = BASE_DIR.parent
RESULTS_DIR = PROJECT_ROOT / "result"
STATIC_DIR = BASE_DIR / "static"
IMAGE_DIR = BASE_DIR / "img"
LOGO_PATH = IMAGE_DIR / "Logo-DAVINCI.png"
MAX_SYSTEMS = 10
LATEST_RUN: dict | None = None
PIPELINE_PROGRESS = {
    "active": False,
    "completed": 0,
    "total": 0,
    "current_system": "",
    "percent": 0,
}
PROGRESS_LOCK = Lock()
REQUIRED_SYSTEM_FIELDS = (
    "system_name",
    "architecture_target",
    "requirements",
    "reference_services",
    "reference_interactions",
)

# The second proposal comes from Agent 2 in C1/C2 and from Agent 2.1 in C4, so the
# report label follows the configuration sent by the interface. Runs restored from
# disk (no mode available) keep the default label used by C1/C2.
AGENT_B_LABELS = {
    "c1": "Agent B (Communication Specialist)",
    "c2": "Agent B (Communication Specialist)",
    "c4": "Agent B (Software Architect 2.1)",
}
DEFAULT_AGENT_B_LABEL = "Agent B (Communication Specialist)"


def _agent_b_label(system: dict) -> str:
    """Return the Agent B label for the configuration of one system."""
    mode = str(system.get("mode") or "").strip().lower()
    return AGENT_B_LABELS.get(mode, DEFAULT_AGENT_B_LABEL)


def _latest_persisted_proposals(system_name: str) -> dict[str, str]:
    """Return the newest saved agent proposals for one system, when available."""
    run_root = RESULTS_DIR / system_name.lower() / "result_generalized_fewshot"
    if not run_root.is_dir():
        return {}

    for run_dir in sorted(
        (path for path in run_root.glob("run_*") if path.is_dir()),
        key=lambda path: path.name,
        reverse=True,
    ):
        proposals = {}
        for result_key, filename in (
            ("agent_a", "proposta_a.csv"),
            ("agent_b", "proposta_b.csv"),
            ("consolidated", "consolidada.csv"),
            ("specification", "especificacao_arquitetural.yaml"),
        ):
            file_path = run_dir / filename
            if file_path.is_file():
                try:
                    proposals[result_key] = file_path.read_text(encoding="utf-8").strip()
                except OSError:
                    continue
        if proposals:
            return proposals
    return {}


def _persisted_report_run() -> dict | None:
    """Build the minimum report model from saved pipeline artifacts after a restart."""
    if not RESULTS_DIR.is_dir():
        return None

    proposals = []
    latest_timestamp = 0.0
    for system_dir in RESULTS_DIR.iterdir():
        if not system_dir.is_dir():
            continue
        saved_proposals = _latest_persisted_proposals(system_dir.name)
        if not saved_proposals:
            continue
        run_dirs = [path for path in (system_dir / "result_generalized_fewshot").glob("run_*") if path.is_dir()]
        if run_dirs:
            latest_timestamp = max(latest_timestamp, max(path.stat().st_mtime for path in run_dirs))
        proposals.append({"system": system_dir.name, **saved_proposals})

    if not proposals:
        return None
    generated_at = datetime.fromtimestamp(latest_timestamp).strftime("%Y-%m-%d %H:%M:%S") if latest_timestamp else "unknown"
    systems = [{"system_name": item["system"]} for item in proposals]
    return {
        "run_id": "persisted-results",
        "generated_at": generated_at,
        "systems": systems,
        "proposals": proposals,
        "service_metrics": [],
        "interaction_metrics": [],
        "best_results": [],
    }


def _report_run() -> dict | None:
    """Prefer persisted proposal CSVs, falling back to the in-memory run data."""
    if LATEST_RUN is None:
        return _persisted_report_run()

    report_run = {**LATEST_RUN}
    fallback_proposals = {item["system"]: item for item in LATEST_RUN.get("proposals", [])}
    proposals = []
    for system in LATEST_RUN.get("systems", []):
        system_name = system.get("system_name", "").strip()
        fallback = fallback_proposals.get(system_name, {})
        saved = _latest_persisted_proposals(system_name)
        proposals.append({
            "system": system_name,
            "agent_a": saved.get("agent_a") or fallback.get("agent_a") or "",
            "agent_b": saved.get("agent_b") or fallback.get("agent_b") or "",
            "consolidated": saved.get("consolidated") or fallback.get("consolidated") or "",
            "specification": saved.get("specification") or fallback.get("specification") or "",
        })
    report_run["proposals"] = proposals
    return report_run


def empty_system_definition() -> dict:
    """Return the browser model for a new system block."""
    return {
        "system_name": "",
        "architecture_target": "Microservices",
        "requirements": "",
        "reference_services": "",
        "reference_interactions": "",
    }


class VirtusRequestHandler(BaseHTTPRequestHandler):
    """Serve the prototype page and its initial JSON API."""

    server_version = "DAVINCIArchitectInterface/0.1"

    def do_GET(self) -> None:
        path = urlparse(self.path).path
        if path == "/":
            self._serve_index()
            return
        if path == "/api/report/pdf":
            self._serve_pdf_report()
            return
        if path == "/api/report/specification-pdf":
            self._serve_specification_pdf()
            return
        if path == "/api/pipeline/progress":
            with PROGRESS_LOCK:
                progress = dict(PIPELINE_PROGRESS)
            self._send_json(HTTPStatus.OK, progress)
            return
        if path.startswith("/static/"):
            relative_path = path.removeprefix("/static/")
            requested_path = (STATIC_DIR / relative_path).resolve()
            if STATIC_DIR not in requested_path.parents:
                self._send_json(
                    HTTPStatus.FORBIDDEN,
                    {"ok": False, "code": "forbidden_path", "message": "Static path is not allowed."},
                )
                return
            self._serve_static_file(requested_path)
            return
        if path.startswith("/img/"):
            relative_path = path.removeprefix("/img/")
            requested_path = (IMAGE_DIR / relative_path).resolve()
            if IMAGE_DIR not in requested_path.parents:
                self._send_json(
                    HTTPStatus.FORBIDDEN,
                    {"ok": False, "code": "forbidden_path", "message": "Image path is not allowed."},
                )
                return
            self._serve_static_file(requested_path)
            return
        self._send_json(
            HTTPStatus.NOT_FOUND,
            {"ok": False, "code": "not_found", "message": "Route not found."},
        )

    def _serve_pdf_report(self) -> None:
        report_run = _report_run()
        if report_run is None:
            self._send_json(
                HTTPStatus.NOT_FOUND,
                {"ok": False, "code": "report_unavailable", "message": "Run a successful pipeline execution before downloading a report."},
            )
            return
        try:
            content = build_pdf_report(report_run)
        except Exception:
            traceback.print_exc()
            self._send_json(
                HTTPStatus.INTERNAL_SERVER_ERROR,
                {"ok": False, "code": "report_generation_failed", "message": "The full report could not be generated."},
            )
            return
        self.send_response(HTTPStatus.OK)
        self.send_header("Content-Type", "application/pdf")
        self.send_header("Content-Disposition", "attachment; filename=virtus-architecture-report.pdf")
        self.send_header("Content-Length", str(len(content)))
        self.end_headers()
        self.wfile.write(content)

    def _serve_specification_pdf(self) -> None:
        report_run = _report_run()
        if report_run is None or not any(item.get("specification") for item in report_run.get("proposals", [])):
            self._send_json(
                HTTPStatus.NOT_FOUND,
                {"ok": False, "code": "specification_unavailable", "message": "Run a successful pipeline execution before downloading the specification."},
            )
            return
        content = build_pdf_specification(report_run)
        self.send_response(HTTPStatus.OK)
        self.send_header("Content-Type", "application/pdf")
        self.send_header("Content-Disposition", "attachment; filename=virtus-architectural-specification.pdf")
        self.send_header("Content-Length", str(len(content)))
        self.end_headers()
        self.wfile.write(content)

    def _serve_index(self) -> None:
        content = (STATIC_DIR / "index.html").read_text(encoding="utf-8")
        host = self.headers.get("Host", f"{HOST}:{PORT}")
        if any(character in host for character in "\r\n"):
            host = f"{HOST}:{PORT}"
        scheme = self.headers.get("X-Forwarded-Proto", "http").split(",", 1)[0].strip()
        if scheme not in {"http", "https"}:
            scheme = "http"
        base_url = f"{scheme}://{host}"
        content = content.replace("__BASE_URL__", base_url).encode("utf-8")
        self.send_response(HTTPStatus.OK)
        self.send_header("Content-Type", "text/html; charset=utf-8")
        self.send_header("Content-Length", str(len(content)))
        self.end_headers()
        self.wfile.write(content)

    def do_POST(self) -> None:
        path = urlparse(self.path).path
        if path == "/api/pipeline/run":
            self._run_pipeline()
            return
        if path != "/api/systems":
            self._send_json(
                HTTPStatus.NOT_FOUND,
                {"ok": False, "code": "not_found", "message": "Route not found."},
            )
            return

        payload = self._read_json_body()
        if payload is None:
            return
        current_count = payload.get("current_count", 0)
        if not isinstance(current_count, int) or isinstance(current_count, bool):
            self._send_json(
                HTTPStatus.BAD_REQUEST,
                {"ok": False, "code": "invalid_count", "message": "Current system count must be an integer."},
            )
            return
        if current_count >= MAX_SYSTEMS:
            self._send_json(
                HTTPStatus.BAD_REQUEST,
                {"ok": False, "code": "system_limit", "message": "A maximum of ten systems is supported."},
            )
            return
        self._send_json(
            HTTPStatus.OK,
            {"ok": True, "system": empty_system_definition(), "count": current_count + 1},
        )

    def _run_pipeline(self) -> None:
        global LATEST_RUN
        payload = self._read_json_body()
        if payload is None:
            return
        systems = payload.get("systems")
        if not isinstance(systems, list) or not 1 <= len(systems) <= MAX_SYSTEMS:
            self._send_json(
                HTTPStatus.BAD_REQUEST,
                {"ok": False, "code": "invalid_system_count", "message": "Submit between one and ten systems."},
            )
            return
        for index, system in enumerate(systems, start=1):
            if not isinstance(system, dict):
                self._send_json(
                    HTTPStatus.BAD_REQUEST,
                    {"ok": False, "code": "invalid_system", "message": f"System {index} must be an object."},
                )
                return
            missing = [
                field for field in REQUIRED_SYSTEM_FIELDS
                if not isinstance(system.get(field), str) or not system[field].strip()
            ]
            if missing:
                self._send_json(
                    HTTPStatus.BAD_REQUEST,
                    {"ok": False, "code": "missing_fields", "message": f"Complete all required fields for system {index}.", "fields": missing},
                )
                return
            if system["architecture_target"] != "Microservices":
                self._send_json(
                    HTTPStatus.BAD_REQUEST,
                    {"ok": False, "code": "unsupported_target", "message": "Only the Microservices target is supported."},
                )
                return

        run_id = datetime.now().strftime("%Y%m%d_%H%M%S_%f")
        generated_at = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        with PROGRESS_LOCK:
            PIPELINE_PROGRESS.update({
                "active": True,
                "completed": 0,
                "total": len(systems),
                "current_system": systems[0]["system_name"].strip(),
                "percent": 0,
            })
        service_metrics = []
        interaction_metrics = []
        best_results = []
        proposals = []
        errors = []
        warnings = []
        for index, system in enumerate(systems):
            pipeline_result = run_real_pipeline(system, tracer_run_id=run_id)
            if not pipeline_result.get("ok"):
                errors.append({"system": system.get("system_name", ""), "message": pipeline_result.get("error", "The pipeline failed.")})
            else:
                name = system["system_name"].strip()
                metrics = pipeline_result.get("metrics", {})
                results = pipeline_result.get("results", {})
                for key, label in (("proposta_a", "Proposal A"), ("proposta_b", "Proposal B"), ("consolidada", "Consolidated")):
                    metric = metrics.get(key)
                    if metric:
                        service_metrics.append({"system": name, "proposal": label, "precision": metric["precision"], "recall": metric["recall"], "f1_score": metric["f1_score"]})
                    interaction_metric = metrics.get(f"{key}_inter")
                    if interaction_metric:
                        interaction_metrics.append({"system": name, "proposal": label, "precision": interaction_metric["precision"], "recall": interaction_metric["recall"], "f1_score": interaction_metric["f1_score"]})
                service_candidates = [row for row in service_metrics if row["system"] == name]
                interaction_candidates = [row for row in interaction_metrics if row["system"] == name]
                best_service = max(service_candidates, key=lambda row: row["f1_score"]) if service_candidates else None
                best_interaction = max(interaction_candidates, key=lambda row: row["f1_score"]) if interaction_candidates else None
                best_results.append({
                    "system": name,
                    "best_services": f"{best_service['proposal']} (F1 {best_service['f1_score']:.4f})" if best_service else "-",
                    "best_interactions": f"{best_interaction['proposal']} (F1 {best_interaction['f1_score']:.4f})" if best_interaction else "-",
                })
                proposals.append({
                    "system": name,
                    "agent_a": results.get("proposta_a", ""),
                    "agent_b": results.get("proposta_b", ""),
                    "consolidated": results.get("consolidada", ""),
                    "specification": results.get("especificacao_yaml", ""),
                })
                if pipeline_result.get("warning"):
                    warnings.append({"system": name, "message": pipeline_result["warning"]})
            with PROGRESS_LOCK:
                completed = index + 1
                PIPELINE_PROGRESS.update({
                    "completed": completed,
                    "current_system": systems[index + 1]["system_name"].strip() if index + 1 < len(systems) else "Complete",
                    "percent": round(completed / len(systems) * 100),
                })

        # Real agent failures should be rendered on the results page with partial results when available.
        result = {
            "ok": not errors or bool(service_metrics or interaction_metrics),
            "run_id": run_id,
            "generated_at": generated_at,
            "systems": systems,
            "proposals": proposals,
            "service_metrics": service_metrics,
            "interaction_metrics": interaction_metrics,
            "best_results": best_results,
            "report_available": True,
            "errors": errors,
            "warnings": warnings,
        }
        LATEST_RUN = result
        with PROGRESS_LOCK:
            PIPELINE_PROGRESS["active"] = False
        self._send_json(HTTPStatus.OK, result)

    def do_DELETE(self) -> None:
        path = urlparse(self.path).path
        if not path.startswith("/api/systems/"):
            self._send_json(
                HTTPStatus.NOT_FOUND,
                {"ok": False, "code": "not_found", "message": "Route not found."},
            )
            return
        try:
            index = int(path.rsplit("/", 1)[-1])
        except ValueError:
            self._send_json(
                HTTPStatus.BAD_REQUEST,
                {"ok": False, "code": "invalid_index", "message": "System index must be an integer."},
            )
            return
        current_count = self.headers.get("X-System-Count")
        try:
            count = int(current_count) if current_count is not None else 0
        except ValueError:
            count = 0
        if count <= 1:
            self._send_json(
                HTTPStatus.BAD_REQUEST,
                {"ok": False, "code": "minimum_systems", "message": "At least one system must remain."},
            )
            return
        if index < 0 or index >= count:
            self._send_json(
                HTTPStatus.NOT_FOUND,
                {"ok": False, "code": "invalid_index", "message": "The requested system does not exist."},
            )
            return
        self._send_json(HTTPStatus.OK, {"ok": True, "removed_index": index, "count": count - 1})

    def _read_json_body(self) -> dict | None:
        try:
            content_length = int(self.headers.get("Content-Length", "0"))
            raw_body = self.rfile.read(content_length)
            payload = json.loads(raw_body.decode("utf-8")) if raw_body else {}
        except (ValueError, UnicodeDecodeError, json.JSONDecodeError):
            self._send_json(
                HTTPStatus.BAD_REQUEST,
                {"ok": False, "code": "invalid_json", "message": "Request body must contain valid JSON."},
            )
            return None
        if not isinstance(payload, dict):
            self._send_json(
                HTTPStatus.BAD_REQUEST,
                {"ok": False, "code": "invalid_payload", "message": "Request body must be a JSON object."},
            )
            return None
        return payload

    def _serve_static_file(self, file_path: Path) -> None:
        if not file_path.is_file():
            self._send_json(
                HTTPStatus.NOT_FOUND,
                {"ok": False, "code": "asset_not_found", "message": "Requested asset was not found."},
            )
            return
        content_type = mimetypes.guess_type(file_path.name)[0] or "application/octet-stream"
        content = file_path.read_bytes()
        self.send_response(HTTPStatus.OK)
        self.send_header("Content-Type", content_type)
        self.send_header("Content-Length", str(len(content)))
        self.end_headers()
        self.wfile.write(content)

    def _send_json(self, status: HTTPStatus, payload: dict) -> None:
        content = json.dumps(payload).encode("utf-8")
        self.send_response(status)
        self.send_header("Content-Type", "application/json; charset=utf-8")
        self.send_header("Content-Length", str(len(content)))
        self.end_headers()
        self.wfile.write(content)

    def log_message(self, format: str, *args: object) -> None:
        """Keep local output concise while retaining standard server logging."""
        print(f"{self.address_string()} - {format % args}")


def create_server(host: str = HOST, port: int = PORT) -> ThreadingHTTPServer:
    """Create the local threaded HTTP server."""
    return ThreadingHTTPServer((host, port), VirtusRequestHandler)


def build_pdf_report(run: dict) -> bytes:
    """Build a styled, complete final execution report without dependencies."""

    # DAVINCI Architect colors: navy titles, gold final-architecture details, pale blue panels.
    navy = (0.039, 0.118, 0.361)
    gold = (0.914, 0.769, 0.416)
    pale_blue = (0.925, 0.949, 0.988)
    light_gray = (0.949, 0.949, 0.949)
    entries = []

    def add(text="", style="body"):
        entries.append((text, style))

    def add_wrapped(label, value):
        add(label, "label")
        for line in textwrap.wrap(str(value or ""), width=88) or [""]:
            add(line, "body")

    add("DAVINCI Architect", "title")
    add("Multi-Agent Software Architect", "subtitle")
    add(f"Run ID / Test Number: {run.get('run_id', 'unknown')}", "metadata")
    add(f"Generated: {run.get('generated_at', datetime.now().strftime('%Y-%m-%d %H:%M:%S'))}", "metadata")
    add("", "body")
    proposals_by_system = {item["system"]: item for item in run.get("proposals", [])}

    for system in run.get("systems", []):
        name = system.get("system_name", "")
        add(f"SYSTEM: {name}", "system")
        add("SECTION 1 - INPUTS PROVIDED", "section")
        add_wrapped("System Requirements", system.get("requirements"))
        add_wrapped("Reference Services", system.get("reference_services"))
        add_wrapped("Reference Interactions", system.get("reference_interactions"))
        add("", "body")

        proposal_data = proposals_by_system.get(name, {})
        add("SECTION 2 - AGENT PROPOSALS", "section")
        add("Agent Proposals", "subsection")
        for proposal_name, subtitle, key in (
            ("Agent A", "Agent A (Software Architect)", "agent_a"),
            ("Agent B", _agent_b_label(system), "agent_b"),
        ):
            add(subtitle, "proposal")
            for csv_line in (proposal_data.get(key) or "").splitlines():
                add(csv_line, "agent_csv_header" if csv_line.startswith("Microservice,") else "agent_csv")
            add("", "body")

        add("SECTION 3 - FINAL ARCHITECTURE RECOMMENDED BY THE PIPELINE", "final_section")
        add("Final Architecture Recommended by the Pipeline", "final_title")
        add("This consolidated architecture is the implementation recommendation produced after considering the intermediate agent proposals.", "final_explanation")
        add("Consolidated Architecture CSV", "final_csv_label")
        for csv_line in (proposal_data.get("consolidated") or "").splitlines():
            add(csv_line, "final_csv_header" if csv_line.startswith("Microservice,") else "final_csv")
        add("", "body")

    add("SECTION 4 - EVALUATION METRICS", "section")
    add("Evaluation Metrics", "subsection")
    for line in textwrap.wrap("Precision, Recall, and F1-score are calculated by comparing the generated architectures with the reference services and interactions provided in the inputs. The quality of these metrics depends on how accurately the reference data represents the desired architecture.", width=88):
        add(line, "explanation")
    add("Services Metrics: System | Proposal | Precision | Recall | F1-Score", "table_header")
    for item in run.get("service_metrics", []):
        add(f"{item['system']} | {item['proposal']} | {item['precision']:.4f} | {item['recall']:.4f} | {item['f1_score']:.4f}", "table_row")
    add("Interactions Metrics: System | Proposal | Precision | Recall | F1-Score", "table_header")
    for item in run.get("interaction_metrics", []):
        add(f"{item['system']} | {item['proposal']} | {item['precision']:.4f} | {item['recall']:.4f} | {item['f1_score']:.4f}", "table_row")
    add("SECTION 5 - BEST RESULTS", "section")
    add("System | Best Services | Best Interactions", "table_header")
    for item in run.get("best_results", []):
        add(f"{item['system']} | {item['best_services']} | {item['best_interactions']}", "table_row")
    add("", "body")
    pages = [entries[index:index + 43] for index in range(0, len(entries), 43)] or [[("", "body")]]
    objects = [
        b"<< /Type /Catalog /Pages 2 0 R >>",
        b"PLACEHOLDER_PAGES",
        b"<< /Type /Font /Subtype /Type1 /BaseFont /Helvetica >>",
        b"<< /Type /Font /Subtype /Type1 /BaseFont /Helvetica-Bold >>",
    ]
    logo_width, logo_height, logo_data = _read_rgb_png(LOGO_PATH)
    compressed_logo = zlib.compress(logo_data)
    objects.append(
        f"<< /Type /XObject /Subtype /Image /Width {logo_width} /Height {logo_height} /ColorSpace /DeviceRGB /BitsPerComponent 8 /Filter /FlateDecode /Length {len(compressed_logo)} >>\nstream\n".encode()
        + compressed_logo
        + b"\nendstream"
    )
    page_numbers = []
    for page_entries in pages:
        page_number = len(objects) + 1
        content_number = page_number + 1
        page_numbers.append(page_number)
        objects.append(
            f"<< /Type /Page /Parent 2 0 R /MediaBox [0 0 612 792] /Resources << /Font << /F1 3 0 R /F2 4 0 R >> /XObject << /Im1 5 0 R >> >> /Contents {content_number} 0 R >>".encode()
        )
        content_lines = ["q", "1 1 1 rg", "0 0 612 792 re", "f", "Q"]
        if page_entries is pages[0]:
            content_lines.extend(["q", "72 0 0 72 480 690 cm", "/Im1 Do", "Q"])
        y = 760
        for text, style in page_entries:
            if style == "final_section":
                content_lines.extend([f"{pale_blue[0]} {pale_blue[1]} {pale_blue[2]} rg", f"45 {y - 10} 522 24 re", "f", f"{gold[0]} {gold[1]} {gold[2]} RG", "2 w", f"45 {y - 10} 522 24 re", "S"])
            elif style in {"final_title", "final_explanation", "final_csv_label", "final_csv_header", "final_csv"}:
                content_lines.extend([f"{pale_blue[0]} {pale_blue[1]} {pale_blue[2]} rg", f"45 {y - 10} 522 24 re", "f", f"{gold[0]} {gold[1]} {gold[2]} RG", "1 w", f"45 {y - 10} 522 24 re", "S"])
            elif style in {"table_header", "agent_csv_header"}:
                content_lines.extend([f"{light_gray[0]} {light_gray[1]} {light_gray[2]} rg", f"45 {y - 10} 522 17 re", "f"])

            if style in {"title", "final_title"}:
                font, size, color = ("F2", 18 if style == "title" else 15, navy)
            elif style == "subtitle":
                font, size, color = ("F1", 11, navy)
            elif style in {"section", "final_section", "subsection", "system"}:
                font, size, color = ("F2", 12 if style != "system" else 13, navy)
            elif style in {"proposal", "label", "table_header", "agent_csv_header", "final_csv_label", "final_csv_header"}:
                font, size, color = ("F2", 9, navy)
            elif style == "footer":
                font, size, color = ("F2", 8, navy)
            else:
                font, size, color = ("F1", 8, (0.12, 0.12, 0.12))
            safe_line = text.replace("\\", "\\\\").replace("(", "\\(").replace(")", "\\)")
            content_lines.extend([f"{color[0]} {color[1]} {color[2]} rg", "BT", f"/{font} {size} Tf", f"50 {y} Td", f"({safe_line[:112]}) Tj", "ET"])
            y -= 16 if style not in {"title", "section", "final_section", "final_title"} else 22
        if page_entries is pages[-1]:
            credit_lines = (
                ("Developed by Daniel Anderson", 150, 42),
                ("In partnership with Virtus UFCG", 178, 30),
                ("Contact: daniel.silva@virtus-cc.ufcg.edu.br", 145, 18),
                ("© 2026 DAVINCI Architect. All rights reserved.", 164, 6),
            )
            for credit, x, y_position in credit_lines:
                safe_credit = credit.replace("\\", "\\\\").replace("(", "\\(").replace(")", "\\)")
                content_lines.extend([f"{navy[0]} {navy[1]} {navy[2]} rg", "BT", "/F1 7 Tf", f"{x} {y_position} Td", f"({safe_credit}) Tj", "ET"])
        stream = "\n".join(content_lines).encode("latin-1", "replace")
        objects.append(b"<< /Length " + str(len(stream)).encode() + b" >>\nstream\n" + stream + b"\nendstream")
    kids = " ".join(f"{number} 0 R" for number in page_numbers)
    objects[1] = f"<< /Type /Pages /Kids [{kids}] /Count {len(page_numbers)} >>".encode()

    pdf = bytearray(b"%PDF-1.4\n%\xe2\xe3\xcf\xd3\n")
    offsets = [0]
    for number, obj in enumerate(objects, start=1):
        offsets.append(len(pdf))
        pdf.extend(f"{number} 0 obj\n".encode())
        pdf.extend(obj)
        pdf.extend(b"\nendobj\n")
    xref_offset = len(pdf)
    pdf.extend(f"xref\n0 {len(objects) + 1}\n".encode())
    pdf.extend(b"0000000000 65535 f \n")
    for offset in offsets[1:]:
        pdf.extend(f"{offset:010d} 00000 n \n".encode())
    pdf.extend(f"trailer\n<< /Size {len(objects) + 1} /Root 1 0 R >>\nstartxref\n{xref_offset}\n%%EOF\n".encode())
    return bytes(pdf)


def build_pdf_specification(run: dict) -> bytes:
    """Build a standalone PDF containing only Agent 5 YAML specifications."""
    navy = (0.039, 0.118, 0.361)
    gold = (0.914, 0.769, 0.416)
    pale_blue = (0.925, 0.949, 0.988)
    entries = [("DAVINCI Architect", "title"), ("Architectural Specification", "subtitle")]
    entries.append((f"Run ID / Test Number: {run.get('run_id', 'unknown')}", "metadata"))
    entries.append((f"Generated: {run.get('generated_at', datetime.now().strftime('%Y-%m-%d %H:%M:%S'))}", "metadata"))
    for proposal in run.get("proposals", []):
        entries.append((f"SYSTEM: {proposal.get('system', '')}", "system"))
        for line in (proposal.get("specification", "") or "").splitlines():
            entries.append((line, "yaml"))
        entries.append(("", "body"))

    pages = [entries[index:index + 43] for index in range(0, len(entries), 43)] or [[("", "body")]]
    objects = [
        b"<< /Type /Catalog /Pages 2 0 R >>",
        b"PLACEHOLDER_PAGES",
        b"<< /Type /Font /Subtype /Type1 /BaseFont /Helvetica >>",
        b"<< /Type /Font /Subtype /Type1 /BaseFont /Helvetica-Bold >>",
    ]
    logo_width, logo_height, logo_data = _read_rgb_png(LOGO_PATH)
    compressed_logo = zlib.compress(logo_data)
    objects.append(
        f"<< /Type /XObject /Subtype /Image /Width {logo_width} /Height {logo_height} /ColorSpace /DeviceRGB /BitsPerComponent 8 /Filter /FlateDecode /Length {len(compressed_logo)} >>\nstream\n".encode()
        + compressed_logo + b"\nendstream"
    )
    page_numbers = []
    for page_entries in pages:
        page_number = len(objects) + 1
        page_numbers.append(page_number)
        content_number = page_number + 1
        objects.append(f"<< /Type /Page /Parent 2 0 R /MediaBox [0 0 612 792] /Resources << /Font << /F1 3 0 R /F2 4 0 R >> /XObject << /Im1 5 0 R >> >> /Contents {content_number} 0 R >>".encode())
        content_lines = ["q", "1 1 1 rg", "0 0 612 792 re", "f", "Q"]
        if page_entries is pages[0]:
            content_lines.extend(["q", "72 0 0 72 480 690 cm", "/Im1 Do", "Q"])
        y = 760
        for text, style in page_entries:
            if style == "system":
                content_lines.extend([f"{pale_blue[0]} {pale_blue[1]} {pale_blue[2]} rg", f"45 {y - 10} 522 24 re", "f", f"{gold[0]} {gold[1]} {gold[2]} RG", "2 w", f"45 {y - 10} 522 24 re", "S"])
            font, size, color = ("F2", 18, navy) if style == "title" else ("F2", 13, navy) if style == "system" else ("F1", 8, (0.12, 0.12, 0.12))
            if style == "subtitle":
                size = 11
            if style == "metadata":
                size, color = 8, navy
            safe_line = text.replace("\\", "\\\\").replace("(", "\\(").replace(")", "\\)")
            content_lines.extend([f"{color[0]} {color[1]} {color[2]} rg", "BT", f"/{font} {size} Tf", f"50 {y} Td", f"({safe_line[:112]}) Tj", "ET"])
            y -= 16 if style not in {"title", "system"} else 22
        stream = "\n".join(content_lines).encode("latin-1", "replace")
        objects.append(b"<< /Length " + str(len(stream)).encode() + b" >>\nstream\n" + stream + b"\nendstream")
    objects[1] = f"<< /Type /Pages /Kids [{' '.join(f'{number} 0 R' for number in page_numbers)}] /Count {len(page_numbers)} >>".encode()
    pdf = bytearray(b"%PDF-1.4\n%\xe2\xe3\xcf\xd3\n")
    offsets = [0]
    for number, obj in enumerate(objects, start=1):
        offsets.append(len(pdf))
        pdf.extend(f"{number} 0 obj\n".encode()); pdf.extend(obj); pdf.extend(b"\nendobj\n")
    xref_offset = len(pdf)
    pdf.extend(f"xref\n0 {len(objects) + 1}\n".encode()); pdf.extend(b"0000000000 65535 f \n")
    for offset in offsets[1:]:
        pdf.extend(f"{offset:010d} 00000 n \n".encode())
    pdf.extend(f"trailer\n<< /Size {len(objects) + 1} /Root 1 0 R >>\nstartxref\n{xref_offset}\n%%EOF\n".encode())
    return bytes(pdf)


def _read_rgb_png(path: Path) -> tuple[int, int, bytes]:
    """Decode the project's RGB PNG into scanlines suitable for a PDF image."""
    raw = path.read_bytes()
    if raw[:8] != b"\x89PNG\r\n\x1a\n":
        raise ValueError("The DAVINCI logo must be a PNG image.")
    position = 8
    width = height = bit_depth = color_type = None
    compressed = bytearray()
    while position < len(raw):
        length = struct.unpack(">I", raw[position:position + 4])[0]
        chunk_type = raw[position + 4:position + 8]
        chunk = raw[position + 8:position + 8 + length]
        position += 12 + length
        if chunk_type == b"IHDR":
            width, height, bit_depth, color_type, _, _, _ = struct.unpack(">IIBBBBB", chunk)
        elif chunk_type == b"IDAT":
            compressed.extend(chunk)
        elif chunk_type == b"IEND":
            break
    if (width, height, bit_depth, color_type) != (width, height, 8, 2):
        raise ValueError("The DAVINCI logo must be an 8-bit RGB PNG image.")
    decoded = zlib.decompress(compressed)
    row_size = width * 3
    rows = []
    offset = 0
    previous = bytearray(row_size)
    for _ in range(height):
        filter_type = decoded[offset]
        current = bytearray(decoded[offset + 1:offset + 1 + row_size])
        offset += row_size + 1
        for index in range(row_size):
            left = current[index - 3] if index >= 3 else 0
            above = previous[index]
            upper_left = previous[index - 3] if index >= 3 else 0
            if filter_type == 1:
                current[index] = (current[index] + left) & 255
            elif filter_type == 2:
                current[index] = (current[index] + above) & 255
            elif filter_type == 3:
                current[index] = (current[index] + ((left + above) // 2)) & 255
            elif filter_type == 4:
                estimate = left + above - upper_left
                distances = (abs(estimate - left), abs(estimate - above), abs(estimate - upper_left))
                current[index] = (current[index] + (left, above, upper_left)[distances.index(min(distances))]) & 255
            elif filter_type != 0:
                raise ValueError("Unsupported PNG filter in the DAVINCI logo.")
        rows.append(current)
        previous = current
    return width, height, b"".join(rows)


def main() -> None:
    server = create_server()
    print(f"DAVINCI Architect running at http://{HOST}:{PORT}")
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        print("\nStopping DAVINCI Architect.")
    finally:
        server.server_close()


if __name__ == "__main__":
    main()
