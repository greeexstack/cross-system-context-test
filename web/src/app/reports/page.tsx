"use client";

import Link from "next/link";
import { useEffect, useState } from "react";
import {
  getUserEvaluations,
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

                  <Link
                    href={`/reports/${report.run_id}`}
                    className="report-card-link"
                  >
                    Open report
                    <span aria-hidden="true">→</span>
                  </Link>
                </div>
              </article>
            );
          })}
        </section>
      )}
    </main>
  );
}