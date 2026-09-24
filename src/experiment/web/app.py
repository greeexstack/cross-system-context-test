from __future__ import annotations

from pathlib import Path

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware

from .models import (
    EvaluationCreateRequest,
    EvaluationListItem,
    EvaluationResult,
    HealthResponse,
)
from .service import EvaluationService


PROJECT_ROOT = Path(__file__).resolve().parents[3]
FIXTURE_ROOT = PROJECT_ROOT / "fixtures_package"

service = EvaluationService(FIXTURE_ROOT)

app = FastAPI(
    title="Cross-System Context API",
    version="0.1.1",
    description=(
        "Product API over the validated Cross-System Context v0.2 "
        "controlled evaluation."
    ),
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.get("/health", response_model=HealthResponse)
def health() -> HealthResponse:
    return HealthResponse()


@app.get(
    "/v1/evaluations",
    response_model=list[EvaluationListItem],
)
def list_evaluations() -> list[EvaluationListItem]:
    return service.list_runs()


@app.post(
    "/v1/evaluations",
    response_model=EvaluationResult,
)
def create_evaluation(
    request: EvaluationCreateRequest,
) -> EvaluationResult:
    return service.run_v02()


@app.get(
    "/v1/evaluations/{run_id}",
    response_model=EvaluationResult,
)
def get_evaluation(run_id: str) -> EvaluationResult:
    result = service.get(run_id)

    if result is None:
        raise HTTPException(
            status_code=404,
            detail="Evaluation not found.",
        )

    return result


@app.get(
    "/v1/evaluations/{run_id}/cases/{pair_id}",
    response_model=dict,
)
def get_case(run_id: str, pair_id: str) -> dict:
    result = service.get(run_id)

    if result is None:
        raise HTTPException(
            status_code=404,
            detail="Evaluation not found.",
        )

    for case in result.cases:
        if case.pair_id == pair_id:
            return case.model_dump()

    raise HTTPException(
        status_code=404,
        detail="Case not found.",
    )
