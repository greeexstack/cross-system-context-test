from __future__ import annotations

from datetime import datetime
from typing import Literal

from pydantic import BaseModel, Field


ResultStatus = Literal["completed", "failed"]


class DimensionResult(BaseModel):
    passed: int
    total: int


class EvidenceItem(BaseModel):
    evidence_id: str
    channel: str
    direction: str
    occurred_at: datetime
    subject: str
    summary: str


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
    evidence: list[EvidenceItem] = Field(default_factory=list)
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


class UserEvaluationCreateRequest(BaseModel):
    name: str = Field(min_length=2, max_length=100)
    objective: str = Field(min_length=10, max_length=1000)
    workflow: str = Field(default="", max_length=100)

    record_type: Literal[
        "opportunity",
        "service_order",
    ] = "opportunity"

    primary_context: str = Field(
        min_length=10,
        max_length=4000,
    )

    additional_context: str = Field(
        min_length=1,
        max_length=4000,
    )
class IntegratedCustomer(BaseModel):
    id: str = Field(min_length=1)
    name: str = Field(min_length=1)
    email: str | None = None
    phone: str | None = None


class IntegratedPrimaryRecord(BaseModel):
    record_id: str = Field(min_length=1)
    record_type: Literal["opportunity"] = "opportunity"
    summary: str = Field(min_length=1, max_length=4000)

    customer: IntegratedCustomer

    stage: str = Field(min_length=1)
    value: float
    quote_sent_at: datetime | None = None
    last_crm_activity_at: datetime | None = None

class IntegratedCommunication(BaseModel):
    communication_id: str = Field(min_length=1)
    customer: IntegratedCustomer
    direction: Literal["inbound", "outbound"]
    occurred_at: datetime
    channel: str = Field(min_length=1)
    topic: str = Field(min_length=1)
    content: str = Field(min_length=1, max_length=10000)


class IntegratedSecondaryContext(BaseModel):
    source_status: Literal[
        "available",
        "unavailable",
    ] = "available"
    communications: list[IntegratedCommunication] = Field(
        default_factory=list
    )


class IntegratedEvaluationCreateRequest(BaseModel):
    name: str = Field(min_length=2, max_length=100)
    objective: str = Field(min_length=10, max_length=1000)

    primary: IntegratedPrimaryRecord
    secondary: IntegratedSecondaryContext

    evaluation_at: datetime | None = None

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


class UserEvaluationResult(BaseModel):
    run_id: str
    evaluation_version: Literal["v0.2-user"] = "v0.2-user"
    source: Literal["user-input"] = "user-input"
    status: Literal["completed"] = "completed"

    created_at: datetime

    name: str
    objective: str
    workflow: str
    record_type: Literal[
        "opportunity",
        "service_order",
    ]

    primary_context: str
    additional_context: str

    base: ReasoningSnapshot
    variant: ReasoningSnapshot

    interpretation_changed: bool
    support_changed: bool
    decision_strength_changed: bool

    assumptions: list[str] = Field(default_factory=list)

    starred: bool = False
    deleted_at: datetime | None = None
class IntegratedEvaluationResult(BaseModel):
    run_id: str
    evaluation_version: Literal["v0.2-integrated"] = "v0.2-integrated"
    source: Literal["integrated-input"] = "integrated-input"
    status: Literal["completed"] = "completed"

    created_at: datetime

    name: str
    objective: str

    primary: IntegratedPrimaryRecord
    secondary: IntegratedSecondaryContext

    base: ReasoningSnapshot
    variant: ReasoningSnapshot

    interpretation_changed: bool
    support_changed: bool
    decision_strength_changed: bool

    assumptions: list[str] = Field(default_factory=list)
class HealthResponse(BaseModel):
    status: Literal["ok"] = "ok"
    product_experiment: str = "v0.2"
    storage: Literal["sqlite"] = "sqlite"