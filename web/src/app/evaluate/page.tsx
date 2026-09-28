"use client";

import Link from "next/link";
import { useState } from "react";
import {
  createUserEvaluation,
  type UserEvaluationResult,
} from "@/lib/api";

type Stage = "details" | "review" | "running" | "complete";

type EvaluationMeta = {
  name: string;
  objective: string;
  workflow: string;
  record_type: "opportunity" | "service_order";
};

export default function EvaluatePage() {
  const [stage, setStage] = useState<Stage>("details");

  const [showEvaluationGuide, setShowEvaluationGuide] =
    useState(false);

  const [name, setName] = useState("");
  const [objective, setObjective] = useState("");
  const [workflow, setWorkflow] = useState("");

  const [recordType, setRecordType] = useState<
    "opportunity" | "service_order"
  >("opportunity");

  const [primaryContext, setPrimaryContext] = useState("");
  const [additionalContext, setAdditionalContext] =
    useState("");

  const [result, setResult] =
    useState<UserEvaluationResult | null>(null);

  const [error, setError] = useState("");

  const detailsValid =
    name.trim().length >= 2 &&
    objective.trim().length >= 10 &&
    primaryContext.trim().length >= 10 &&
    additionalContext.trim().length >= 1;

  function review() {
    if (!detailsValid) {
      return;
    }

    setError("");
    setStage("review");
  }

  async function run() {
    setStage("running");
    setError("");

    try {
      const evaluation = await createUserEvaluation({
        name: name.trim(),
        objective: objective.trim(),
        workflow: workflow.trim(),
        record_type: recordType,
        primary_context: primaryContext.trim(),
        additional_context: additionalContext.trim(),
      });

      const meta: EvaluationMeta = {
        name: name.trim(),
        objective: objective.trim(),
        workflow: workflow.trim(),
        record_type: recordType,
      };

      window.sessionStorage.setItem(
        `csc:user-evaluation:${evaluation.run_id}`,
        JSON.stringify(meta),
      );

      setResult(evaluation);
      setStage("complete");
    } catch (err) {
      setError(
        err instanceof Error
          ? err.message
          : "Evaluation failed.",
      );
      setStage("review");
    }
  }

  return (
    <main className="site-shell evaluate-page">
      <nav className="nav">
        <Link href="/" className="logo">
          <span className="logo-mark">C</span>
          <span className="logo-name">
            Cross-System Context
          </span>
        </Link>

        <div className="nav-links">
          <Link
            href="/evaluate"
            className="nav-active"
          >
            Evaluations
          </Link>

          <Link href="/integrate">
            Integrate
          </Link>
        </div>
      </nav>

      <section className="page-header compact">
        <Link href="/" className="back-link">
          <span>←</span>
          Home
        </Link>

        <div className="overline">
          NEW EVALUATION
        </div>

        <h1>
          Understand what is happening
          <br />
          in your business.
        </h1>

        <p>
          Describe the business situation, add the
          information that may change it, and tell us
          what you want to understand.
        </p>
      </section>

      <section className="wizard-shell">
        <div className="wizard-progress">
          <div
            className={`wizard-item ${
              stage !== "details"
                ? "done"
                : "active"
            }`}
          >
            <span>01</span>

            <div>
              <strong>Describe</strong>
              <small>
                Provide the situation
              </small>
            </div>
          </div>

          <div
            className={`wizard-line ${
              stage !== "details"
                ? "filled"
                : ""
            }`}
          />

          <div
            className={`wizard-item ${
              stage === "review" ||
              stage === "running"
                ? "active"
                : stage === "complete"
                  ? "done"
                  : ""
            }`}
          >
            <span>02</span>

            <div>
              <strong>Review</strong>
              <small>
                Confirm the inputs
              </small>
            </div>
          </div>

          <div
            className={`wizard-line ${
              stage === "complete"
                ? "filled"
                : ""
            }`}
          />

          <div
            className={`wizard-item ${
              stage === "complete"
                ? "done active"
                : ""
            }`}
          >
            <span>03</span>

            <div>
              <strong>Result</strong>
              <small>
                Understand the change
              </small>
            </div>
          </div>
        </div>

        {stage === "details" && (
          <div className="form-card">
            <div className="form-card-header">
              <div>
                <div className="section-kicker">
                  EVALUATION DETAILS
                </div>

                <h2>
                  What are you trying to understand?
                </h2>
              </div>

              <div className="quiet-badge">
                User evaluation
              </div>
            </div>

            <div className="evaluation-guide">
              <button
                type="button"
                className="evaluation-guide-toggle"
                onClick={() =>
                  setShowEvaluationGuide(
                    (current) => !current,
                  )
                }
                aria-expanded={showEvaluationGuide}
                aria-controls="evaluation-guide-content"
              >
                <span className="evaluation-guide-title">
                  What can I evaluate with this tool?
                </span>

                <span
                  className={`evaluation-guide-chevron ${
                    showEvaluationGuide
                      ? "open"
                      : ""
                  }`}
                  aria-hidden="true"
                />
              </button>

              {showEvaluationGuide && (
                <div
                  id="evaluation-guide-content"
                  className="evaluation-guide-content"
                >
                  <p className="evaluation-guide-intro">
                    The tool is designed for business
                    situations where additional
                    information may change or strengthen
                    your understanding of what is
                    happening.
                  </p>

                  <div className="evaluation-guide-grid">
                    <div>
                      <strong>
                        Customer follow-up
                      </strong>

                      <p>
                        Determine whether a customer
                        communication indicates that a
                        quote or proposal needs
                        follow-up.
                      </p>
                    </div>

                    <div>
                      <strong>
                        Pending decisions
                      </strong>

                      <p>
                        Understand whether a quote or
                        proposal is still waiting for a
                        customer decision.
                      </p>
                    </div>

                    <div>
                      <strong>
                        Open discussions
                      </strong>

                      <p>
                        Identify whether a customer
                        discussion or negotiation is
                        still active.
                      </p>
                    </div>

                    <div>
                      <strong>
                        Service next steps
                      </strong>

                      <p>
                        Identify situations where a
                        service appears complete but the
                        next business step is unclear.
                      </p>
                    </div>

                    <div>
                      <strong>
                        New business context
                      </strong>

                      <p>
                        See whether additional customer
                        or communication information
                        changes the conclusion.
                      </p>
                    </div>
                  </div>

                  <div className="evaluation-guide-example">
                    <div className="section-kicker">
                      EXAMPLE
                    </div>

                    <div>
                      <span>
                        Current situation
                      </span>

                      <p>
                        A quote was sent to the customer
                        three days ago and no decision has
                        been recorded.
                      </p>
                    </div>

                    <div>
                      <span>
                        Additional information
                      </span>

                      <p>
                        The customer replied asking
                        whether the quote can be revised
                        before Friday.
                      </p>
                    </div>

                    <div>
                      <span>
                        Question
                      </span>

                      <p>
                        Does this communication change
                        the follow-up decision?
                      </p>
                    </div>
                  </div>
                </div>
              )}
            </div>

            <div className="form-grid">
              <label className="field full">
                <span>
                  Evaluation name
                </span>

                <input
                  value={name}
                  onChange={(event) =>
                    setName(event.target.value)
                  }
                  placeholder="e.g. Quote follow-up decision"
                  maxLength={100}
                />
              </label>

              <label className="field full">
                <span>
                  What do you want to understand?
                </span>

                <textarea
                  value={objective}
                  onChange={(event) =>
                    setObjective(event.target.value)
                  }
                  placeholder="e.g. Determine whether the latest customer communication changes how this opportunity should be interpreted."
                  rows={4}
                  maxLength={1000}
                />
              </label>

              <label className="field">
                <span>
                  Workflow or team{" "}
                  <em>Optional</em>
                </span>

                <input
                  value={workflow}
                  onChange={(event) =>
                    setWorkflow(event.target.value)
                  }
                  placeholder="e.g. Sales"
                  maxLength={100}
                />
              </label>

              <label className="field">
                <span>
                  Record type
                </span>

                <select
                  value={recordType}
                  onChange={(event) =>
                    setRecordType(
                      event.target.value as
                        | "opportunity"
                        | "service_order",
                    )
                  }
                >
                  <option value="opportunity">
                    Opportunity
                  </option>

                  <option value="service_order">
                    Service order
                  </option>
                </select>
              </label>

              <label className="field full">
                <span>
                  Current situation
                </span>

                <textarea
                  value={primaryContext}
                  onChange={(event) =>
                    setPrimaryContext(
                      event.target.value,
                    )
                  }
                  placeholder="Describe what is happening now, including the customer, order, opportunity, or service situation."
                  rows={5}
                  maxLength={4000}
                />
              </label>

              <label className="field full">
                <span>
                  Additional information
                </span>

                <textarea
                  value={additionalContext}
                  onChange={(event) =>
                    setAdditionalContext(
                      event.target.value,
                    )
                  }
                  placeholder="Add the communication, observation, or other information that may change your understanding of the situation."
                  rows={5}
                  maxLength={4000}
                />
              </label>
            </div>

            <div className="info-note">
              <div className="info-note-icon">
                i
              </div>

              <div>
                <strong>
                  Your information drives the result.
                </strong>

                <p>
                  The evaluation uses the situation
                  and additional information you provide
                  to identify whether the conclusion
                  changes or becomes clearer.
                </p>
              </div>
            </div>

            <div className="form-footer">
              <span>
                You will receive a clear conclusion, the
                information behind it, and what changed
                when new context was added.
              </span>

              <button
                className="button button-primary"
                onClick={review}
                disabled={!detailsValid}
              >
                Review evaluation
                <span>→</span>
              </button>
            </div>
          </div>
        )}

        {stage === "review" && (
  <div className="form-card review-card">
    <div className="form-card-header">
      <div>
        <div className="section-kicker">
          READY TO RUN
        </div>

        <h2>
          Review your evaluation
        </h2>

        <p className="review-intro">
          Make sure the question and information below
          are correct before running the evaluation.
        </p>
      </div>
    </div>

    <div className="review-overview">
      <div className="review-overview-label">
        You're evaluating
      </div>

      <h3>
        {name}
      </h3>

      <div className="review-meta-line">
        <span>{workflow || "No workflow specified"}</span>
        <span className="review-meta-separator">•</span>
        <span>
          {recordType === "service_order"
            ? "Service order"
            : "Opportunity"}
        </span>
      </div>
    </div>

    <div className="review-question">
      <div className="review-block-label">
        Your question
      </div>

      <blockquote>
        “{objective.trim()}”
      </blockquote>
    </div>

    <div className="review-context-grid">
      <div className="review-context-card">
        <div className="review-block-label">
          Current situation
        </div>

        <p>
          “{primaryContext.trim()}”
        </p>
      </div>

      <div className="review-context-card">
        <div className="review-block-label">
          Additional information
        </div>

        <p>
          “{additionalContext.trim()}”
        </p>
      </div>
    </div>

    {error && (
      <div className="error-box">
        {error}
      </div>
    )}

    <div className="review-actions">
      <button
        className="button button-ghost"
        onClick={() => setStage("details")}
      >
        ← Edit Details
      </button>

      <button
        className="button button-primary"
        onClick={run}
      >
        Run Evaluation
        <span>→</span>
      </button>
    </div>
  </div>
)}

        {stage === "running" && (
          <div className="running-card">
            <div className="loader-ring" />

            <div className="section-kicker">
              RUNNING EVALUATION
            </div>

            <h2>
  Reviewing the information you provided.
</h2>

<p>
  We are checking your current business situation
  first, then seeing whether the additional
  information changes or strengthens the conclusion.
</p>
          </div>
        )}

        {stage === "complete" && result && (
          <div className="success-card">
            <div className="success-icon">
              ✓
            </div>

            <div className="section-kicker">
              EVALUATION COMPLETE
            </div>

            <h2>
  Your evaluation is ready.
</h2>

<p>
  The result shows what we found from your
  original situation and what changed after
  the additional information was considered.
</p>

            <div className="success-summary">
              <div>
  <span>
    Evaluation
  </span>

  <strong>
    {name}
  </strong>
</div>

<div>
  <span>
    Conclusion
  </span>

  <strong>
    {result.interpretation_changed
      ? "Changed"
      : "No material change"}
  </strong>
</div>

<div>
  <span>
    Additional information
  </span>

  <strong>
    {result.support_changed
      ? "Added useful support"
      : "Did not change the support"}
  </strong>
</div>
            </div>

            <Link
              href={`/user-evaluations/${result.run_id}`}
              className="button button-primary"
            >
              Open result
              <span>→</span>
            </Link>
          </div>
        )}
      </section>
    </main>
  );
}