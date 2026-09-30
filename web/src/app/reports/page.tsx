"use client";

import Link from "next/link";
import { useEffect, useState } from "react";
import {
  deleteUserEvaluation,
  getUserEvaluations,
  starUserEvaluation,
  unstarUserEvaluation,
  type UserEvaluationResult,
} from "@/lib/api";
import { getResultState } from "@/lib/userEvaluationResult";

function formatDate(value: string) {
  return new Intl.DateTimeFormat("en", {
    dateStyle: "medium",
  }).format(new Date(value));
}

function formatSentence(value: string) {
  const sentence = value.trim().replace(/\s+/g, " ");

  if (!sentence) {
    return "No objective provided.";
  }

  return sentence.charAt(0).toUpperCase() + sentence.slice(1);
}

export default function ReportsPage() {
  const [reports, setReports] = useState<UserEvaluationResult[]>([]);
  const [error, setError] = useState("");
  const [actionError, setActionError] = useState("");
  const [processingRunId, setProcessingRunId] = useState<string | null>(
    null,
  );

  useEffect(() => {
    getUserEvaluations()
      .then(setReports)
      .catch((err) => {
        setError(
          err instanceof Error
            ? err.message
            : "Unable to load your reports.",
        );
      });
  }, []);

  async function handleStarToggle(report: UserEvaluationResult) {
    setActionError("");
    setProcessingRunId(report.run_id);

    try {
      const updated = report.starred
        ? await unstarUserEvaluation(report.run_id)
        : await starUserEvaluation(report.run_id);

      setReports((current) =>
        current.map((item) =>
          item.run_id === updated.run_id ? updated : item,
        ),
      );
    } catch (err) {
      setActionError(
        err instanceof Error
          ? err.message
          : "Unable to update this report.",
      );
    } finally {
      setProcessingRunId(null);
    }
  }

  async function handleDelete(report: UserEvaluationResult) {
    const confirmed = window.confirm(
      `Delete "${report.name}"? This report will be removed from your active reports.`,
    );

    if (!confirmed) {
      return;
    }

    setActionError("");
    setProcessingRunId(report.run_id);

    try {
      await deleteUserEvaluation(report.run_id);

      setReports((current) =>
        current.filter((item) => item.run_id !== report.run_id),
      );
    } catch (err) {
      setActionError(
        err instanceof Error
          ? err.message
          : "Unable to delete this report.",
      );
    } finally {
      setProcessingRunId(null);
    }
  }

  if (error) {
    return (
      <main className="site-shell reports-page">
        <nav className="nav">
          <Link href="/" className="logo">
            <span className="logo-mark">C</span>
            <span className="logo-name">Cross-System Context</span>
          </Link>

          <div className="nav-links">
            <Link href="/evaluate">Evaluations</Link>
            <Link href="/integrate">Integrate</Link>
          </div>
        </nav>

        <section className="empty-state reports-empty-state">
          <div className="section-kicker">REPORTS</div>
          <h1>We could not load your reports.</h1>
          <p>{error}</p>

          <Link href="/evaluate" className="button button-primary">
            Start an evaluation
          </Link>
        </section>
      </main>
    );
  }

  return (
    <main className="site-shell reports-page">
      <nav className="nav">
        <Link href="/" className="logo">
          <span className="logo-mark">C</span>
          <span className="logo-name">Cross-System Context</span>
        </Link>

        <div className="nav-links">
          <Link href="/evaluate">Evaluations</Link>
          <Link href="/integrate">Integrate</Link>
        </div>
      </nav>

      <header className="reports-header">
        <div className="section-kicker">REPORTS</div>

        <h1>Your evaluation reports.</h1>

        <p>
          Revisit completed evaluations, see what conclusion was reached,
          and open the full report when you need the underlying context.
        </p>

        <Link href="/evaluate" className="button button-primary">
          Start an evaluation
          <span>→</span>
        </Link>
      </header>

      {actionError ? (
        <p className="reports-action-error" role="alert">
          {actionError}
        </p>
      ) : null}

      {reports.length === 0 ? (
        <section className="reports-empty">
          <div className="section-kicker">NO REPORTS YET</div>

          <h2>Your completed evaluations will appear here.</h2>

          <p>
            Run your first evaluation to create a report you can return to
            later.
          </p>
        </section>
      ) : (
        <section className="report-list" aria-label="Evaluation reports">
          {reports.map((report) => {
            const state = getResultState(report);
            const isProcessing = processingRunId === report.run_id;

            return (
              <article className="report-card" key={report.run_id}>
                <div className="report-card-top">
                  <span
                    className={`report-card-status report-card-status-${state.kind}`}
                  >
                    {state.label}
                  </span>

                  <span className="report-card-date">
                    {formatDate(report.created_at)}
                  </span>
                </div>

                <h2>{report.name}</h2>

                <p className="report-card-purpose">
                  {formatSentence(report.objective)}
                </p>

                <div className="report-card-bottom">
                  <span>
                    {report.record_type === "opportunity"
                      ? "Opportunity"
                      : "Service order"}
                  </span>

                  <div className="report-card-actions">
                    <button
                      type="button"
                      className={`report-card-action ${
                        report.starred
                          ? "report-card-action-starred"
                          : ""
                      }`}
                      aria-label={
                        report.starred
                          ? `Unstar ${report.name}`
                          : `Star ${report.name}`
                      }
                      title={
                        report.starred
                          ? "Unstar report"
                          : "Star report"
                      }
                      disabled={isProcessing}
                      onClick={() => handleStarToggle(report)}
                    >
                      {report.starred ? "★" : "☆"}
                    </button>

                    <button
                      type="button"
                      className="report-card-action report-card-action-delete"
                      aria-label={`Delete ${report.name}`}
                      title="Delete report"
                      disabled={isProcessing}
                      onClick={() => handleDelete(report)}
                    >
                      Delete
                    </button>

                    <Link
                      href={`/reports/${report.run_id}`}
                      className="report-card-link"
                    >
                      Open report
                      <span aria-hidden="true">→</span>
                    </Link>
                  </div>
                </div>
              </article>
            );
          })}
        </section>
      )}
    </main>
  );
}