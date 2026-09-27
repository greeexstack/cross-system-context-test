"use client";

import Link from "next/link";
import { useEffect, useMemo, useState } from "react";
import {
  getEvaluation,
  type EvaluationResult,
} from "@/lib/api";

type EvaluationMeta = {
  name?: string;
  objective?: string;
  workflow?: string;
};

export default function EvaluationResultPage({
  params,
}: {
  params: Promise<{ run_id: string }>;
}) {
  const [runId, setRunId] = useState("");
  const [result, setResult] = useState<EvaluationResult | null>(null);
  const [meta, setMeta] = useState<EvaluationMeta>({});
  const [error, setError] = useState("");

  useEffect(() => {
    params.then(({ run_id }) => {
      setRunId(run_id);

      const saved = window.sessionStorage.getItem(
        `csc:evaluation:${run_id}`,
      );

      if (saved) {
        try {
          setMeta(JSON.parse(saved));
        } catch {
          // Optional metadata is not required for the result.
        }
      }

      getEvaluation(run_id)
        .then(setResult)
        .catch((err) => {
          setError(
            err instanceof Error
              ? err.message
              : "Unable to load this evaluation.",
          );
        });
    });
  }, [params]);

  const passRate = useMemo(() => {
    if (!result || result.total_cases === 0) {
      return 0;
    }

    return Math.round(
      (result.passed_cases / result.total_cases) * 100,
    );
  }, [result]);

  if (error) {
    return (
      <main className="site-shell">
        <nav className="nav">
          <Link href="/" className="logo">
            <span className="logo-mark">C</span>
            <span className="logo-name">
              Cross-System Context
            </span>
          </Link>
        </nav>

        <section className="empty-state">
          <div className="section-kicker">
            RESULT UNAVAILABLE
          </div>

          <h1>We could not load this evaluation.</h1>

          <p>{error}</p>

          <Link
            href="/evaluate"
            className="button button-primary"
          >
            Start another evaluation
          </Link>
        </section>
      </main>
    );
  }

  if (!result) {
    return (
      <main className="site-shell">
        <nav className="nav">
          <Link href="/" className="logo">
            <span className="logo-mark">C</span>
            <span className="logo-name">
              Cross-System Context
            </span>
          </Link>
        </nav>

        <section className="loading-state">
          <div className="loader-ring" />
          <span>Loading evaluation...</span>
        </section>
      </main>
    );
  }

  return (
    <main className="site-shell">
      <nav className="nav">
        <Link href="/" className="logo">
          <span className="logo-mark">C</span>
          <span className="logo-name">
            Cross-System Context
          </span>
        </Link>

        <div className="nav-links">
          <Link href="/evaluate">Evaluations</Link>
          <Link href="/integrate">Integrate</Link>
        </div>
      </nav>

      <section className="result-hero">
        <Link href="/evaluate" className="back-link">
          <span>←</span>
          New evaluation
        </Link>

        <div className="result-title-row">
          <div>
            <div className="overline">
              EVALUATION RESULT
            </div>

            <h1>
              {meta.name || "Controlled evaluation"}
            </h1>
          </div>

          <span className="complete-badge">
            <span className="status-dot" />
            Complete
          </span>
        </div>

        {meta.objective && (
          <p className="result-objective">
            {meta.objective}
          </p>
        )}
      </section>

      <section className="result-stat-grid">
        <div className="result-stat result-stat-primary">
          <span className="stat-label">
            CASES PASSED
          </span>

          <strong>
            {result.passed_cases}
            <small> / {result.total_cases}</small>
          </strong>

          <p>
            All controlled cases completed.
          </p>
        </div>

        <div className="result-stat">
          <span className="stat-label">
            COVERAGE
          </span>

          <strong>{passRate}%</strong>

          <p>
            Cases passing the evaluation criteria.
          </p>
        </div>

        <div className="result-stat">
          <span className="stat-label">
            STATUS
          </span>

          <strong>Complete</strong>

          <p>
            Evaluation finished successfully.
          </p>
        </div>
      </section>

      <section className="result-section">
        <div className="section-heading-row">
          <div>
            <div className="section-kicker">
              CASE EXPLORER
            </div>

            <h2>Inspect every case.</h2>
          </div>

          <div className="case-count">
            {result.cases?.length ?? 0} cases
          </div>
        </div>

        <div className="case-table">
          <div className="case-table-head">
            <span>Case</span>
            <span>Split</span>
            <span>Checks</span>
            <span>Status</span>
            <span />
          </div>

          {(result.cases ?? []).map((item) => {
            const checks = Object.values(
              item.dimensions,
            );

            const checksPassed =
              checks.filter(Boolean).length;

            return (
              <Link
                key={item.pair_id}
                href={`/evaluations/${runId}/cases/${item.pair_id}`}
                className="case-row"
              >
                <strong>{item.pair_id}</strong>

                <span className="muted-cell">
                  {item.split}
                </span>

                <span className="muted-cell">
                  {checksPassed} / {checks.length}
                </span>

                <span className="case-status">
                  <span className="status-dot" />
                  {item.passed ? "Passed" : "Review"}
                </span>

                <span className="case-arrow">
                  →
                </span>
              </Link>
            );
          })}
        </div>
      </section>

      <section className="result-section technical">
        <div>
          <div className="section-kicker">
            TECHNICAL DETAILS
          </div>

          <h2>What powered this result?</h2>
        </div>

        <div className="technical-grid">
          <div>
            <span>Evaluation engine</span>
            <strong>
              {result.evaluation_version}
            </strong>
          </div>

          <div>
            <span>Dataset</span>
            <strong>{result.source}</strong>
          </div>

          <div>
            <span>Run ID</span>
            <strong>{result.run_id}</strong>
          </div>
        </div>
      </section>
    </main>
  );
}