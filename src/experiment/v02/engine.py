from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime, timedelta, timezone
import re
from typing import Any, Iterable


@dataclass(frozen=True)
class IdentityResult:
    status: str
    matched_fields: tuple[str, ...] = ()


@dataclass(frozen=True)
class ReasoningResult:
    pair_id: str
    phase: str
    interpretation_class: str
    support_level: str
    decision_strength: str | None = None
    identity_match: str | None = None
    temporal_status: str | None = None
    availability: str | None = None
    reversion: str | None = None
    recommended_focus: str | None = None
    evidence_ids: tuple[str, ...] = ()
    evidence_valid: bool = True
    notes: tuple[str, ...] = ()


@dataclass(frozen=True)
class EngineConfig:
    stale_after_days: int = 30


class ContextReasoningEngine:
    """Generic v0.2 reasoning engine.

    The engine consumes only primary records and secondary observations.
    It never reads v0.2 ground truth and never branches on F01-F10 identifiers.
    """

    _FOLLOW_UP_RE = re.compile(r"\b(follow[- ]?up is due|follow-up due)\b", re.I)
    _PROPOSAL_RE = re.compile(r"\b(proposal|quote|quoted|commercial terms)\b", re.I)
    _NEGOTIATION_RE = re.compile(r"\bnegotiation\b", re.I)
    _SERVICE_RE = re.compile(r"\b(service|handoff|migration workshop|transition)\b", re.I)
    _NEXT_STEP_RE = re.compile(r"\bnext (?:step|handoff)|next follow-up|what the next", re.I)
    _SUPPORTING_RE = re.compile(r"\bapproved budget\b|within the approved budget|moving through procurement|confirmed the quoted amount", re.I)
    _RELEVANT_RE = re.compile(r"\bunder internal review\b|asked for a follow-up|schedule a review call|proposal is under internal review", re.I)
    _CONTRADICTORY_RE = re.compile(r"do not work for (?:them|us)|don't work|proposal to be revisited|requested that the proposal be revisited", re.I)
    _IRRELEVANT_RE = re.compile(r"\bseparate (?:project|service rollout|store rollout)|different project|no statement about the quoted opportunity", re.I)

    def __init__(self, config: EngineConfig | None = None) -> None:
        self.config = config or EngineConfig()

    def evaluate(self, case: dict[str, Any], *, phase: str) -> ReasoningResult:
        primary = case["primary"]
        secondary = case.get("variant_case") if phase == "variant" else case.get("base", {})
        primary_summary = primary.get("summary", "")
        primary_record_type = primary.get("record_type", "")

        interpretation = self._primary_interpretation(primary_summary, primary_record_type)
        strength = "moderate"
        notes: list[str] = []
        evidence_ids: list[str] = []
        identity_match: str | None = None
        temporal_status: str | None = None
        availability = secondary.get("secondary_source_status")
        reversion: str | None = None
        recommended_focus: str | None = None
        support = "primary_only"

        # No external source or explicit absence of observations never creates evidence.
        if availability == "unavailable":
            return ReasoningResult(
                pair_id=case["pair_id"], phase=phase, interpretation_class=interpretation,
                support_level="safe_fallback_primary_only", availability="unavailable", decision_strength=strength,
                evidence_ids=(), evidence_valid=True,
                notes=("secondary source unavailable; primary interpretation preserved",),
            )

        raw_evidence = secondary.get("secondary_evidence", [])
        if raw_evidence is None:
            return ReasoningResult(
                pair_id=case["pair_id"], phase=phase, interpretation_class=interpretation,
                support_level="safe_fallback_primary_only", availability="unavailable", decision_strength=strength,
                evidence_ids=(), evidence_valid=True,
                notes=("missing secondary observations treated as unavailable",),
            )
        if not raw_evidence:
            if phase == "variant" and case.get("base", {}).get("secondary_evidence"):
                base_state = self.evaluate(case, phase="base")
                return ReasoningResult(
                    pair_id=case["pair_id"], phase=phase, interpretation_class=base_state.interpretation_class,
                    support_level="primary_only", availability="available", decision_strength=strength,
                    reversion="toward_primary_only", evidence_ids=(), evidence_valid=True,
                    notes=("secondary evidence removed; interpretation reverts toward primary-only",),
                )
            return ReasoningResult(
                pair_id=case["pair_id"], phase=phase, interpretation_class=interpretation,
                support_level="no_secondary_evidence", availability="available", decision_strength=strength,
                evidence_ids=(), evidence_valid=True,
                notes=("secondary source available with no observed communication",),
            )

        identity = self._resolve_identity(primary, secondary)
        identity_match = identity.status

        # Only confidently attributed evidence may influence the business interpretation.
        if identity.status in {"no_match", "ambiguous_match"}:
            return ReasoningResult(
                pair_id=case["pair_id"], phase=phase, interpretation_class=interpretation,
                support_level="primary_only", identity_match=identity.status,
                availability="available", evidence_ids=(), evidence_valid=True,
                notes=("secondary evidence rejected because identity is not sufficiently certain",),
            )

        messages = list(self._resolve_evidence(raw_evidence))
        for msg in messages:
            evidence_ids.append(msg["communication_id"])

        # F07: freshness is derived from the observation timestamp, not from case labels.
        freshness = [self._temporal_status(msg["occurred_at"]) for msg in messages]
        temporal_status = "fresh" if any(status == "fresh" for status in freshness) else "clearly_stale" if freshness else None

        # Context-sensitive interpretation is based on evidence content, not family IDs.
        combined = " ".join(msg["summary"] for msg in messages)

        stale_only = bool(freshness) and all(status == "clearly_stale" for status in freshness)

        if self._CONTRADICTORY_RE.search(combined):
            contradiction_count = sum(1 for msg in messages if self._CONTRADICTORY_RE.search(msg["summary"]))
            if len(messages) > contradiction_count:
                support = "mixed_evidence"
            else:
                support = "weakened_by_secondary_context"
            strength = "weaker"
            notes.append("secondary evidence includes material conflict with the primary interpretation direction")
        elif self._IRRELEVANT_RE.search(combined):
            support = "primary_only"
            notes.append("secondary communication is about a different work item")
        elif self._SUPPORTING_RE.search(combined):
            support = "secondary_supported"
            strength = "stronger"
            notes.append("secondary evidence supports the existing interpretation without changing its class")
        elif self._RELEVANT_RE.search(combined) or self._FOLLOW_UP_RE.search(combined):
            if interpretation == "quote_followup_pending":
                support = "secondary_supported"
                strength = "stronger"
                notes.append("secondary evidence strengthens an interpretation that already indicates follow-up is due")
            else:
                interpretation = self._relevant_transition(interpretation)
                support = "supported_by_secondary_context"
                notes.append("secondary evidence is materially relevant to the primary situation")
        elif primary_record_type == "service_order" and self._NEXT_STEP_RE.search(combined):
            recommended_focus = "next_step_followup"
            support = "supported_by_secondary_context"
            notes.append("service completion context supports a next-step follow-up focus")
        else:
            notes.append("secondary evidence did not justify changing the primary interpretation")

        if stale_only:
            support = "temporal_context_rejected"
            notes.append("identity is valid but evidence is too old to be treated as current")

        if primary_record_type == "service_order" and self._NEXT_STEP_RE.search(combined):
            recommended_focus = "next_step_followup"
            if support == "primary_only":
                support = "supported_by_secondary_context"

        # Removing secondary evidence from a contextful base means the engine must fall back toward primary-only.
        if not raw_evidence and phase == "variant" and case.get("base", {}).get("secondary_evidence"):
            reversion = "toward_primary_only"
            support = "primary_only"
            strength = "moderate"

        return ReasoningResult(
            pair_id=case["pair_id"], phase=phase,
            interpretation_class=interpretation, support_level=support,
            decision_strength=strength, identity_match=identity_match,
            temporal_status=temporal_status, availability="available",
            reversion=reversion, recommended_focus=recommended_focus,
            evidence_ids=tuple(evidence_ids), evidence_valid=True,
            notes=tuple(notes),
        )

    def _primary_interpretation(self, summary: str, record_type: str) -> str:
        if record_type == "service_order" and self._SERVICE_RE.search(summary):
            return "service_completed_next_step_unrecorded"
        if self._NEGOTIATION_RE.search(summary):
            return "negotiation_open"
        if self._FOLLOW_UP_RE.search(summary):
            return "quote_followup_pending"
        if self._PROPOSAL_RE.search(summary):
            return "quote_pending_decision"
        return "primary_state_uncertain"

    @staticmethod
    def _relevant_transition(current: str) -> str:
        if current == "quote_pending_decision":
            return "quote_followup_pending"
        return current

    def _resolve_identity(self, primary: dict[str, Any], secondary: dict[str, Any]) -> IdentityResult:
        customer_id = self._primary_customer_id(primary["record_id"])
        identity = secondary.get("secondary_identity")
        raw_evidence = secondary.get("secondary_evidence") or []

        # Explicit identity records are authoritative for identity resolution.
        if identity is not None:
            primary_identity = self._lookup_customer(customer_id)
            return self._compare_identities(primary_identity, identity)

        observed_ids = set()
        for item in raw_evidence:
            if isinstance(item, str):
                comm = self._lookup_communication(item)
                if comm is not None and comm.get("customer_id") is not None:
                    observed_ids.add(comm["customer_id"])
        if not observed_ids:
            return IdentityResult("ambiguous_match")
        if observed_ids == {customer_id}:
            return IdentityResult("confident_match", ("customer_id",))
        return IdentityResult("no_match")

    def _primary_customer_id(self, opportunity_id: str) -> str:
        # The loader populates this lookup before evaluation.
        if hasattr(self, "_opportunities"):
            return self._opportunities[opportunity_id]["customer_id"]
        raise RuntimeError("engine indexes not initialized")

    def _lookup_customer(self, customer_id: str) -> dict[str, Any]:
        return self._customers[customer_id]

    def _lookup_communication(self, communication_id: str) -> dict[str, Any] | None:
        return self._communications.get(communication_id)

    def _compare_identities(self, primary: dict[str, Any], secondary: dict[str, Any]) -> IdentityResult:
        matches: list[str] = []
        for field in ("email", "phone", "name"):
            a = self._normalize(primary.get(field))
            b = self._normalize(secondary.get(field))
            if a and b and a == b:
                matches.append(field)

        strong_matches = [field for field in matches if field in {"email", "phone"}]
        if strong_matches:
            return IdentityResult("confident_match", tuple(strong_matches))
        if "name" in matches:
            return IdentityResult("ambiguous_match", ("name",))
        return IdentityResult("no_match")

    @staticmethod
    def _normalize(value: Any) -> str | None:
        if value is None:
            return None
        return re.sub(r"\s+", " ", str(value).strip().lower()) or None

    def _resolve_evidence(self, raw: Iterable[Any]) -> Iterable[dict[str, Any]]:
        for item in raw:
            if isinstance(item, str):
                comm = self._lookup_communication(item)
                if comm is not None:
                    yield comm
            elif isinstance(item, dict):
                comm = self._lookup_communication(item.get("communication_id"))
                if comm is not None:
                    if item.get("occurred_at"):
                        comm = {**comm, "occurred_at": item["occurred_at"]}
                    yield comm

    def _temporal_status(self, occurred_at: str) -> str:
        now = self._evaluation_at
        when = datetime.fromisoformat(occurred_at.replace("Z", "+00:00"))
        if when.tzinfo is None:
            when = when.replace(tzinfo=timezone.utc)
        age = now - when
        return "clearly_stale" if age > timedelta(days=self.config.stale_after_days) else "fresh"

    def initialize_indexes(self, customers: list[dict[str, Any]], opportunities: list[dict[str, Any]], communications: list[dict[str, Any]], evaluation_at: str) -> None:
        self._customers = {c["customer_id"]: c for c in customers}
        self._opportunities = {o["opportunity_id"]: o for o in opportunities}
        self._communications = {c["communication_id"]: c for c in communications}
        self._evaluation_at = datetime.fromisoformat(evaluation_at.replace("Z", "+00:00"))
