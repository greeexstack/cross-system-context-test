from __future__ import annotations

from datetime import datetime
from typing import Literal

from pydantic import BaseModel, Field


ResultStatus = Literal["completed", "failed"]


class DimensionResult(BaseModel):
    passed: int
    total: int


class ReasoningSnapshot(BaseModel):
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
    evidence_ids: list[str] = Field(default_factory=list)
    evidence_valid: bool
    notes: list[str] = Field(default_factory=list)


class CaseResult(BaseModel):
    pair_id: str
    split: str
    passed: bool
    dimensions: dict[str, bool]
    base: ReasoningSnapshot
    variant: ReasoningSnapshot


class EvaluationCreateRequest(BaseModel):
    evaluation_version: Literal["v0.2"] = "v0.2"
    source: Literal["frozen-fixtures"] = "frozen-fixtures"


class EvaluationResult(BaseModel):
    run_id: str
    evaluation_version: str
    source: str
    status: ResultStatus
    started_at: datetime
    completed_at: datetime
    total_cases: int
    passed_cases: int
    dimensions: dict[str, DimensionResult]
    cases: list[CaseResult]


class EvaluationListItem(BaseModel):
    run_id: str
    evaluation_version: str
    source: str
    status: ResultStatus
    started_at: datetime
    completed_at: datetime
    total_cases: int
    passed_cases: int


class HealthResponse(BaseModel):
    status: Literal["ok"] = "ok"
    product_experiment: str = "v0.2"
    storage: Literal["memory"] = "memory"
