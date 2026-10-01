from __future__ import annotations

import os
from pathlib import Path

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware

from .models import (
    EvaluationCreateRequest,
    EvaluationListItem,
    EvaluationResult,
    HealthResponse,
    IntegratedEvaluationCreateRequest,
    IntegratedEvaluationResult,
    UserEvaluationCreateRequest,
    UserEvaluationResult,
)
from .service import EvaluationService


PROJECT_ROOT = Path(__file__).resolve().parents[3]
FIXTURE_ROOT = PROJECT_ROOT / "fixtures_package"

USER_STORAGE_PATH = os.environ.get(
    "CROSS_SYSTEM_USER_STORAGE_PATH",
    str(PROJECT_ROOT / ".runtime" / "user_evaluations.sqlite3"),
)

service = EvaluationService(
    FIXTURE_ROOT,
    user_storage_path=USER_STORAGE_PATH,
)

app = FastAPI(
    title="Cross-System Context API",
    version="0.1.2",
    description=(
        "Product API over the validated Cross-System Context "
        "evaluation engine."
    ),
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:3000",
        "http://127.0.0.1:3000",
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.get(
    "/health",
    response_model=HealthResponse,
)
def health() -> HealthResponse:
    return HealthResponse()


# ---------------------------------------------------------------------------
# Frozen research benchmark
# ---------------------------------------------------------------------------

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
def get_case(
    run_id: str,
    pair_id: str,
) -> dict:
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
# ---------------------------------------------------------------------------
# Structured integration evaluation
# ---------------------------------------------------------------------------

@app.post(
    "/v1/integrated-evaluations",
    response_model=IntegratedEvaluationResult,
)
def create_integrated_evaluation(
    request: IntegratedEvaluationCreateRequest,
) -> IntegratedEvaluationResult:
    return service.run_integrated_evaluation(request)

# ---------------------------------------------------------------------------
# User evaluation
# ---------------------------------------------------------------------------

@app.post(
    "/v1/user-evaluations",
    response_model=UserEvaluationResult,
)
def create_user_evaluation(
    request: UserEvaluationCreateRequest,
) -> UserEvaluationResult:
    return service.run_user_evaluation(request)


@app.get(
    "/v1/user-evaluations",
    response_model=list[UserEvaluationResult],
)
def list_user_evaluations() -> list[UserEvaluationResult]:
    return service.list_user_evaluations()

@app.delete(
    "/v1/user-evaluations/{run_id}",
    status_code=204,
)
def delete_user_evaluation(
    run_id: str,
) -> None:
    deleted = service.delete_user_evaluation(run_id)

    if not deleted:
        raise HTTPException(
            status_code=404,
            detail="User evaluation not found.",
        )


@app.post(
    "/v1/user-evaluations/{run_id}/star",
    response_model=UserEvaluationResult,
)
def star_user_evaluation(
    run_id: str,
) -> UserEvaluationResult:
    result = service.set_user_evaluation_starred(
        run_id,
        True,
    )

    if result is None:
        raise HTTPException(
            status_code=404,
            detail="User evaluation not found.",
        )

    return result


@app.delete(
    "/v1/user-evaluations/{run_id}/star",
    response_model=UserEvaluationResult,
)
def unstar_user_evaluation(
    run_id: str,
) -> UserEvaluationResult:
    result = service.set_user_evaluation_starred(
        run_id,
        False,
    )

    if result is None:
        raise HTTPException(
            status_code=404,
            detail="User evaluation not found.",
        )

    return result
@app.get(
    "/v1/user-evaluations/{run_id}",
    response_model=UserEvaluationResult,
)
def get_user_evaluation(
    run_id: str,
) -> UserEvaluationResult:
    result = service.get_user(run_id)

    if result is None:
        raise HTTPException(
            status_code=404,
            detail="User evaluation not found.",
        )

    return result