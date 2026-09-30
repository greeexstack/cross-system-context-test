const API_BASE =
  process.env.NEXT_PUBLIC_API_BASE_URL ?? "http://127.0.0.1:8000";

export type EvidenceItem = {
  evidence_id: string;
  channel: string;
  direction: string;
  occurred_at: string;
  subject: string;
  summary: string;
};

export type ReasoningSnapshot = {
  pair_id: string;
  phase: string;
  interpretation_class: string | null;
  support_level: string | null;
  decision_strength: string | null;
  identity_match: string | null;
  temporal_status: string | null;
  availability: string | null;
  reversion: string | null;
  recommended_focus: string | null;
  evidence_ids: string[];
  evidence: EvidenceItem[];
  evidence_valid: boolean;
  notes: string[];
};

export type CaseResult = {
  pair_id: string;
  split: string;
  passed: boolean;
  dimensions: Record<string, boolean>;
  base: ReasoningSnapshot;
  variant: ReasoningSnapshot;
};

export type EvaluationResult = {
  run_id: string;
  evaluation_version: string;
  source: string;
  status: string;
  started_at: string;
  completed_at: string;
  total_cases: number;
  passed_cases: number;
  dimensions: Record<
    string,
    {
      passed: number;
      total: number;
    }
  >;
  cases: CaseResult[];
};

export type UserEvaluationRequest = {
  name: string;
  objective: string;
  workflow: string;
  record_type: "opportunity" | "service_order";
  primary_context: string;
  additional_context: string;
};


export type UserEvaluationResult = {
  run_id: string;
  evaluation_version: "v0.2-user";
  source: "user-input";
  status: "completed";
  created_at: string;
  starred: boolean;
  deleted_at: string | null;

  name: string;
  objective: string;
  workflow: string;
  record_type: "opportunity" | "service_order";

  primary_context: string;
  additional_context: string;

  base: ReasoningSnapshot;
  variant: ReasoningSnapshot;

  interpretation_changed: boolean;
  support_changed: boolean;
  decision_strength_changed: boolean;

  assumptions: string[];
};

async function parseResponse<T>(response: Response): Promise<T> {
  if (response.status === 204) {
    return undefined as T;
  }

  if (!response.ok) {
    let detail = `Request failed (${response.status})`;

    try {
      const body = await response.json();

      if (body?.detail) {
        detail = body.detail;
      }
    } catch {
      // Keep the generic error.
    }

    throw new Error(detail);
  }

  return response.json();
}

export async function createEvaluation(): Promise<EvaluationResult> {
  const response = await fetch(`${API_BASE}/v1/evaluations`, {
    method: "POST",
    headers: {
      "Content-Type": "application/json",
    },
    body: JSON.stringify({
      evaluation_version: "v0.2",
      source: "frozen-fixtures",
    }),
  });

  return parseResponse<EvaluationResult>(response);
}

export async function createUserEvaluation(
  request: UserEvaluationRequest,
): Promise<UserEvaluationResult> {
  const response = await fetch(`${API_BASE}/v1/user-evaluations`, {
    method: "POST",
    headers: {
      "Content-Type": "application/json",
    },
    body: JSON.stringify(request),
  });

  return parseResponse<UserEvaluationResult>(response);
}

export async function getEvaluation(
  runId: string,
): Promise<EvaluationResult> {
  const response = await fetch(
    `${API_BASE}/v1/evaluations/${runId}`,
    {
      cache: "no-store",
    },
  );

  return parseResponse<EvaluationResult>(response);
}

export async function getUserEvaluation(
  runId: string,
): Promise<UserEvaluationResult> {
  const response = await fetch(
    `${API_BASE}/v1/user-evaluations/${runId}`,
    {
      cache: "no-store",
    },
  );

  return parseResponse<UserEvaluationResult>(response);
}
export async function getUserEvaluations(): Promise<UserEvaluationResult[]> {
  const response = await fetch(
    `${API_BASE}/v1/user-evaluations`,
    {
      cache: "no-store",
    },
  );

  return parseResponse<UserEvaluationResult[]>(response);
}
export async function deleteUserEvaluation(
  runId: string,
): Promise<void> {
  const response = await fetch(
    `${API_BASE}/v1/user-evaluations/${runId}`,
    {
      method: "DELETE",
    },
  );

  await parseResponse<void>(response);
}

export async function starUserEvaluation(
  runId: string,
): Promise<UserEvaluationResult> {
  const response = await fetch(
    `${API_BASE}/v1/user-evaluations/${runId}/star`,
    {
      method: "POST",
    },
  );

  return parseResponse<UserEvaluationResult>(response);
}

export async function unstarUserEvaluation(
  runId: string,
): Promise<UserEvaluationResult> {
  const response = await fetch(
    `${API_BASE}/v1/user-evaluations/${runId}/star`,
    {
      method: "DELETE",
    },
  );

  return parseResponse<UserEvaluationResult>(response);
}
export async function getCase(
  runId: string,
  pairId: string,
): Promise<CaseResult> {
  const response = await fetch(
    `${API_BASE}/v1/evaluations/${runId}/cases/${pairId}`,
    {
      cache: "no-store",
    },
  );

  return parseResponse<CaseResult>(response);
}