"""Best-effort execution observability for the CrewAI pipeline."""

from __future__ import annotations

import contextvars
import functools
import json
import threading
import time
from datetime import datetime, timezone
from pathlib import Path

try:
    from crewai.events import (
        LLMCallCompletedEvent,
        LLMCallFailedEvent,
        LLMCallStartedEvent,
        crewai_event_bus,
    )
except Exception:  # pragma: no cover - keeps the experiment usable without CrewAI events
    LLMCallCompletedEvent = LLMCallFailedEvent = LLMCallStartedEvent = None
    crewai_event_bus = None

_CURRENT_TRACKER: contextvars.ContextVar["ExecutionTracker | None"] = contextvars.ContextVar(
    "davinci_execution_tracker", default=None
)

# C4 (Agent 1 + Agent 2.1) uses two agents whose CrewAI role is the same
# ("Software Architect"), so the role alone cannot separate them in the
# per-agent cost report. The pipeline may therefore label the calls of one
# agent explicitly; the label lives in a ContextVar, following the same
# pattern already used for the tracker itself.
_CURRENT_AGENT_LABEL: contextvars.ContextVar["str | None"] = contextvars.ContextVar(
    "davinci_agent_label", default=None
)


def set_agent_label(label: str):
    """Label the LLM calls executed next; returns a token for reset_agent_label."""
    return _CURRENT_AGENT_LABEL.set(label)


def reset_agent_label(token) -> None:
    """Remove a label created by set_agent_label (best effort, never raises)."""
    try:
        _CURRENT_AGENT_LABEL.reset(token)
    except Exception:
        pass


_REGISTER_LOCK = threading.Lock()
_REGISTERED = False


def _now() -> datetime:
    return datetime.now(timezone.utc)


def _iso(value: datetime) -> str:
    return value.isoformat(timespec="milliseconds")


def _provider(model: str | None) -> str | None:
    if not model:
        return None
    return model.split("/", 1)[0] if "/" in model else None


def _agent_name(role: str | None) -> str:
    normalized = (role or "unknown").lower()
    for marker, name in (
        ("software architect", "agent_1"),
        ("communication", "agent_2"),
        ("validator", "agent_3"),
        ("refiner", "agent_4"),
    ):
        if marker in normalized:
            return name
    return role or "unknown"


def _usage_value(usage: dict | None, *names: str) -> int | None:
    if not isinstance(usage, dict):
        return None
    for name in names:
        value = usage.get(name)
        if isinstance(value, int) and not isinstance(value, bool):
            return value
    return None


class ExecutionTracker:
    """Collects LLM events for one execution and never raises to the pipeline."""

    def __init__(self, execution_id: str):
        self.execution_id = execution_id
        self.started_at = _now()
        self._started_calls: dict[str, tuple[float, object]] = {}
        self._calls: list[dict] = []
        self._token = None

    def start(self) -> None:
        try:
            self._token = _CURRENT_TRACKER.set(self)
        except Exception:
            self._token = None

    def finish(self, run_dir: Path) -> None:
        try:
            finished_at = _now()
            metadata = self._metadata(finished_at)
            (run_dir / "execution_metadata.json").write_text(
                json.dumps(metadata, indent=2, ensure_ascii=False), encoding="utf-8"
            )
        except Exception:
            pass
        finally:
            try:
                if self._token is not None:
                    _CURRENT_TRACKER.reset(self._token)
            except Exception:
                pass

    def _record_started(self, event: object) -> None:
        try:
            call_id = str(event.call_id)
            self._started_calls[call_id] = (time.perf_counter(), event)
        except Exception:
            pass

    def _record_finished(self, event: object, failed: bool = False) -> None:
        try:
            call_id = str(event.call_id)
            started = self._started_calls.pop(call_id, None)
            started_clock = started[0] if started else time.perf_counter()
            source = started[1] if started else event
            duration_ms = round((time.perf_counter() - started_clock) * 1000, 3)
            usage = getattr(event, "usage", None)
            model = getattr(event, "model", None) or getattr(source, "model", None)
            agent_role = getattr(event, "agent_role", None) or getattr(source, "agent_role", None)
            agent = _CURRENT_AGENT_LABEL.get() or _agent_name(agent_role)
            prompt_tokens = _usage_value(usage, "prompt_tokens", "input_tokens")
            completion_tokens = _usage_value(usage, "completion_tokens", "output_tokens")
            total_tokens = _usage_value(usage, "total_tokens")
            if total_tokens is None and prompt_tokens is not None and completion_tokens is not None:
                total_tokens = prompt_tokens + completion_tokens
            self._calls.append({
                "agent": agent,
                "model": model,
                "provider": _provider(model),
                "started_at": _iso(getattr(source, "timestamp", _now())),
                "finished_at": _iso(getattr(event, "timestamp", _now())),
                "duration_ms": duration_ms,
                "prompt_tokens": prompt_tokens,
                "completion_tokens": completion_tokens,
                "total_tokens": total_tokens,
                "status": "failed" if failed else "completed",
            })
        except Exception:
            pass

    def _metadata(self, finished_at: datetime) -> dict:
        agents = {}
        for call in self._calls:
            summary = agents.setdefault(call["agent"], {"calls": 0, "prompt_tokens": 0, "completion_tokens": 0, "total_tokens": 0, "duration_ms": 0.0})
            summary["calls"] += 1
            summary["duration_ms"] = round(summary["duration_ms"] + call["duration_ms"], 3)
            for key in ("prompt_tokens", "completion_tokens", "total_tokens"):
                if call[key] is not None:
                    summary[key] += call[key]

        totals = {"prompt_tokens": 0, "completion_tokens": 0, "total_tokens": 0}
        for call in self._calls:
            for key in totals:
                if call[key] is not None:
                    totals[key] += call[key]
        return {
            "execution_id": self.execution_id,
            "execution": {
                "started_at": _iso(self.started_at),
                "finished_at": _iso(finished_at),
                "duration_ms": round((finished_at - self.started_at).total_seconds() * 1000, 3),
            },
            "llm_usage": {"total_calls": len(self._calls), **totals},
            "agents": agents,
            "calls": self._calls,
        }


def _on_started(_source: object, event: object) -> None:
    try:
        tracker = _CURRENT_TRACKER.get()
        if tracker:
            tracker._record_started(event)
    except Exception:
        pass


def _on_completed(_source: object, event: object) -> None:
    try:
        tracker = _CURRENT_TRACKER.get()
        if tracker:
            tracker._record_finished(event)
    except Exception:
        pass


def _on_failed(_source: object, event: object) -> None:
    try:
        tracker = _CURRENT_TRACKER.get()
        if tracker:
            tracker._record_finished(event, failed=True)
    except Exception:
        pass


def register_event_handlers() -> None:
    global _REGISTERED
    if _REGISTERED or crewai_event_bus is None:
        return
    with _REGISTER_LOCK:
        if _REGISTERED:
            return
        try:
            crewai_event_bus.on(LLMCallStartedEvent)(_on_started)
            crewai_event_bus.on(LLMCallCompletedEvent)(_on_completed)
            crewai_event_bus.on(LLMCallFailedEvent)(_on_failed)
            _REGISTERED = True
        except Exception:
            pass


register_event_handlers()


def track_execution(function):
    """Decorate one pipeline execution while preserving its existing behavior."""
    @functools.wraps(function)
    def wrapped(llm, system_name, config, timestamp, example, *extra_args, **extra_kwargs):
        # C0-C3 call the decorated executor with five positional arguments; C4
        # adds the second few-shot (example_b) as a sixth one. The wrapper
        # forwards whatever it receives so it stays configuration-agnostic.
        tracker = None
        try:
            tracker = ExecutionTracker(timestamp)
            tracker.start()
        except Exception:
            tracker = None
        results_root = function.__globals__.get("RESULTS_ROOT", Path("result"))
        tracer_run_id = config.get("tracer_run_id", timestamp)
        run_dir = Path(results_root) / f"results-tracer-{tracer_run_id}" / config["name"].lower()
        run_dir.mkdir(parents=True, exist_ok=True)
        try:
            return function(llm, system_name, config, timestamp, example, *extra_args, **extra_kwargs)
        finally:
            if tracker is not None:
                try:
                    tracker.finish(run_dir)
                except Exception:
                    pass
    return wrapped
