from __future__ import annotations

import os
from pathlib import Path

from fastapi import Depends, FastAPI, HTTPException, Request
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
from .d1_storage import D1UserEvaluationStore
from .service import EvaluationService


PROJECT_ROOT = Path(__file__).resolve().parents[3]
FIXTURE_ROOT = Path(__file__).resolve().parents[2] / "fixtures_package"

def _local_user_storage_path() -> str | None:
    configured = os.environ.get("CROSS_SYSTEM_USER_STORAGE_PATH")
    if configured is not None:
        return configured

    try:
        import js  # type: ignore  # noqa: F401
    except ModuleNotFoundError:
        return str(PROJECT_ROOT / ".runtime" / "user_evaluations.sqlite3")

    return None


USER_STORAGE_PATH = _local_user_storage_path()

service = EvaluationService(
    FIXTURE_ROOT,
    user_storage_path=USER_STORAGE_PATH,
)


def worker_env(request: Request):
    return request.scope.get("env")

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
async def create_user_evaluation(
    request: UserEvaluationCreateRequest,
    env=Depends(worker_env),
) -> UserEvaluationResult:
    if env is None:
        return service.run_user_evaluation(request)

    store = D1UserEvaluationStore(env.cross_system_context_prod)
    return await service.run_user_evaluation_d1(request, store)

@app.get(
    "/v1/user-evaluations",
    response_model=list[UserEvaluationResult],
)
async def list_user_evaluations(
    env=Depends(worker_env),
) -> list[UserEvaluationResult]:
    if env is None:
        return service.list_user_evaluations()

    store = D1UserEvaluationStore(env.cross_system_context_prod)
    return await service.list_user_evaluations_d1(store)

@app.delete(
    "/v1/user-evaluations/{run_id}",
    status_code=204,
)
async def delete_user_evaluation(
    run_id: str,
    env=Depends(worker_env),
) -> None:
    if env is None:
        deleted = service.delete_user_evaluation(run_id)
    else:
        store = D1UserEvaluationStore(env.cross_system_context_prod)
        deleted = await service.delete_user_evaluation_d1(run_id, store)

    if not deleted:
        raise HTTPException(
            status_code=404,
            detail="User evaluation not found.",
        )

@app.post(
    "/v1/user-evaluations/{run_id}/star",
    response_model=UserEvaluationResult,
)
async def star_user_evaluation(
    run_id: str,
    env=Depends(worker_env),
) -> UserEvaluationResult:
    if env is None:
        result = service.set_user_evaluation_starred(run_id, True)
    else:
        store = D1UserEvaluationStore(env.cross_system_context_prod)
        result = await service.set_user_evaluation_starred_d1(run_id, True, store)

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
async def unstar_user_evaluation(
    run_id: str,
    env=Depends(worker_env),
) -> UserEvaluationResult:
    if env is None:
        result = service.set_user_evaluation_starred(run_id, False)
    else:
        store = D1UserEvaluationStore(env.cross_system_context_prod)
        result = await service.set_user_evaluation_starred_d1(run_id, False, store)

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
async def get_user_evaluation(
    run_id: str,
    env=Depends(worker_env),
) -> UserEvaluationResult:
    if env is None:
        result = service.get_user(run_id)
    else:
        store = D1UserEvaluationStore(env.cross_system_context_prod)
        result = await service.get_user_d1(run_id, store)

    if result is None:
        raise HTTPException(
            status_code=404,
            detail="User evaluation not found.",
        )

    return result
