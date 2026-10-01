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
type EvaluationEvidenceRecord = {
  evidence: EvaluationResult["cases"][number]["variant"]["evidence"][number];
  cases: string[];
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
  const [statusFilter, setStatusFilter] = useState<
    "all" | "passed" | "review"
  >("all");

  const [dimensionFilter, setDimensionFilter] =
    useState("all");

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
  const dimensionOptions = useMemo(() => {
    if (!result) {
      return [];
    }

    const dimensions = new Set<string>();

    for (const item of result.cases ?? []) {
      for (const dimension of Object.keys(item.dimensions)) {
        dimensions.add(dimension);
      }
    }

    return Array.from(dimensions).sort();
  }, [result]);

  const filteredCases = useMemo(() => {
    if (!result) {
      return [];
    }

    return (result.cases ?? []).filter((item) => {
      const matchesStatus =
        statusFilter === "all" ||
        (statusFilter === "passed" && item.passed) ||
        (statusFilter === "review" && !item.passed);

      const matchesDimension =
  dimensionFilter === "all" ||
  item.dimensions[dimensionFilter] === false;

      return matchesStatus && matchesDimension;
    });
  }, [result, statusFilter, dimensionFilter]);
  const evidenceCount = useMemo(() => {
    if (!result) {
      return 0;
    }

    return new Set(
      result.cases.flatMap((item) =>
        item.variant.evidence.map(
          (evidence) => evidence.evidence_id,
        ),
      ),
    ).size;
  }, [result]);

  const contextChecksPassed =
    (result?.dimensions.context_sensitivity?.passed ?? 0) ===
      (result?.dimensions.context_sensitivity?.total ?? 0) &&
    (result?.dimensions.context_resistance?.passed ?? 0) ===
      (result?.dimensions.context_resistance?.total ?? 0);
        const evidenceRecords = useMemo<EvaluationEvidenceRecord[]>(() => {
    if (!result) {
      return [];
    }

    const records = new Map<
      string,
      EvaluationEvidenceRecord
    >();

    for (const item of result.cases) {
      for (const evidence of item.variant.evidence) {
        const existing = records.get(
          evidence.evidence_id,
        );

        if (existing) {
          if (!existing.cases.includes(item.pair_id)) {
            existing.cases.push(item.pair_id);
          }

          continue;
        }

        records.set(evidence.evidence_id, {
          evidence,
          cases: [item.pair_id],
        });
      }
    }

    return Array.from(records.values());
  }, [result]);
  function formatDimension(value: string) {
    return value
      .replaceAll("_", " ")
      .replace(/\b\w/g, (letter) => letter.toUpperCase());
  }

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
          <Link href="/">
            Overview
          </Link>

          <Link href="/evaluate" className="nav-active">
            Evaluations
          </Link>

          <Link href="/integrate">
            Integrations
          </Link>

          <Link href="/reports">
            Reports
          </Link>
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
 <section className="result-overview">
        <div className="result-overview-heading">
          <div>
            <div className="section-kicker">
              WHY THIS RESULT
            </div>

            <h2>See what supported the evaluation.</h2>

            <p>
              The result is backed by evidence checks,
              subject matching, information timing, and
              context validation.
            </p>
          </div>
        </div>

        <div className="result-overview-grid">
          <div className="result-overview-card">
            <span>Evidence considered</span>
            <strong>{evidenceCount}</strong>
            <p>
              Evidence records used across the evaluated cases.
            </p>
          </div>

          <div className="result-overview-card">
            <span>Identity</span>
            <strong>
              {result.dimensions.identity_integrity?.passed ?? 0}
              {" / "}
              {result.dimensions.identity_integrity?.total ?? 0}
            </strong>
            <p>
              Evidence matched to the evaluated subject.
            </p>
          </div>

          <div className="result-overview-card">
            <span>Information timing</span>
            <strong>
              {result.dimensions.temporal_integrity?.passed ?? 0}
              {" / "}
              {result.dimensions.temporal_integrity?.total ?? 0}
            </strong>
            <p>
              Timing checks completed against the case requirements.
            </p>
          </div>

          <div className="result-overview-card">
            <span>Context handling</span>
            <strong>
              {contextChecksPassed
                ? "Validated"
                : "Review needed"}
            </strong>
            <p>
              Relevant context was tested for both change and resistance to irrelevant change.
            </p>
          </div>

          <div className="result-overview-card">
            <span>Provenance</span>
            <strong>{result.evaluation_version}</strong>
            <p>
              {result.source} · Run {result.run_id}
            </p>
          </div>
        </div>
      </section>
      <section className="result-section evidence-overview">
        <div className="section-heading-row">
          <div>
            <div className="section-kicker">
              EVIDENCE USED
            </div>

            <h2>Review the information behind the result.</h2>

            <p>
              These evidence records were considered across the
              evaluated cases. Open a case to inspect the full
              validation chain.
            </p>
          </div>

          <div className="case-count">
            {evidenceRecords.length} evidence{" "}
            {evidenceRecords.length === 1
              ? "record"
              : "records"}
          </div>
        </div>

        {evidenceRecords.length === 0 ? (
          <div className="evidence-overview-empty">
            No evidence records were used in this evaluation.
          </div>
        ) : (
          <div className="evidence-overview-list">
            {evidenceRecords.map((record) => {
              const direction =
                record.evidence.direction === "inbound"
                  ? "Incoming"
                  : record.evidence.direction === "outbound"
                    ? "Outgoing"
                    : formatDimension(
                        record.evidence.direction,
                      );

              const channel = formatDimension(
                record.evidence.channel,
              );

              const occurredAt = new Date(
                record.evidence.occurred_at,
              );

              const occurredLabel = Number.isNaN(
                occurredAt.getTime(),
              )
                ? record.evidence.occurred_at
                : new Intl.DateTimeFormat("en", {
                    dateStyle: "medium",
                    timeStyle: "short",
                  }).format(occurredAt);

              return (
                <article
                  key={record.evidence.evidence_id}
                  className="evidence-overview-card"
                >
                  <div className="evidence-overview-top">
                    <div>
                      <span className="evidence-overview-id">
                        {record.evidence.evidence_id}
                      </span>

                      <strong>
                        {record.evidence.subject}
                      </strong>
                    </div>

                    <span className="evidence-overview-type">
                      {direction} · {channel}
                    </span>
                  </div>

                  <p className="evidence-overview-summary">
                    {record.evidence.summary}
                  </p>

                  <div className="evidence-overview-footer">
                    <span>{occurredLabel}</span>

                    <span>
                      Used in {record.cases.length}{" "}
                      {record.cases.length === 1
                        ? "case"
                        : "cases"}
                    </span>

                    <Link
                      href={`/evaluations/${runId}/cases/${record.cases[0]}`}
                    >
                      Open case →
                    </Link>
                  </div>
                </article>
              );
            })}
          </div>
        )}
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
  {filteredCases.length} of {result.cases?.length ?? 0} cases
</div>
        </div>
<div className="case-filters" aria-label="Case filters">
  <label>
    <span>Result</span>

    <select
      value={statusFilter}
      onChange={(event) =>
        setStatusFilter(
          event.target.value as "all" | "passed" | "review",
        )
      }
    >
      <option value="all">All results</option>
      <option value="passed">Passed</option>
      <option value="review">Requires review</option>
    </select>
  </label>

  <label>
    <span>Evaluation dimension</span>

    <select
      value={dimensionFilter}
      onChange={(event) =>
        setDimensionFilter(event.target.value)
      }
    >
      <option value="all">All dimensions</option>

      {dimensionOptions.map((dimension) => (
        <option key={dimension} value={dimension}>
          {formatDimension(dimension)}
        </option>
      ))}
    </select>
  </label>
</div>
        <div className="case-table">
          <div className="case-table-head">
            <span>Case</span>
            <span>Split</span>
            <span>Checks</span>
            <span>Status</span>
            <span />
          </div>
          {filteredCases.length === 0 ? (
  <div className="case-filter-empty">
    No cases match the selected filters.
  </div>
) : (
  filteredCases.map((item) => {
    const checks = Object.values(item.dimensions);

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
  })
)}

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