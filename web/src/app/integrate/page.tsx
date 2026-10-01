import Link from "next/link";

export default function IntegratePage() {
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

          <Link href="/evaluate">
            Evaluations
          </Link>

          <Link href="/integrate" className="nav-active">
            Integrations
          </Link>

          <Link href="/reports">
            Reports
          </Link>
        </div>
      </nav>

      <section className="page-header">
        <Link href="/" className="back-link">
          <span>←</span>
          Home
        </Link>

        <div className="overline">
          INTEGRATION
        </div>

        <h1>
          Connect evaluation to your application.
        </h1>

        <p>
          The current API supports two distinct paths:
          evaluate user-supplied business context, or run the
          controlled research evaluation used to validate the
          system.
        </p>
      </section>
      <div className="integration-overview">
        <div className="integration-overview-card">
          <div className="section-kicker">
            API OVERVIEW
          </div>

          <h2>
            HTTP + JSON
          </h2>

          <p>
            The current API exposes evaluation and report operations over
            HTTP with JSON request and response bodies.
          </p>

          <div className="integration-status-row">
            <span>Health</span>
            <strong>GET /health</strong>
          </div>

          <div className="integration-status-row">
            <span>Version</span>
            <strong>v0.2</strong>
          </div>

          <div className="integration-status-row">
            <span>Storage</span>
            <strong>SQLite</strong>
          </div>
        </div>

        <div className="integration-overview-card subtle">
          <div className="section-kicker">
            CURRENT API BOUNDARY
          </div>

          <h2>
            What is available today
          </h2>

          <ul>
            <li>
              User evaluations over supplied business context.
            </li>
            <li>
              Retrieval of completed user evaluation results.
            </li>
            <li>
              Saved reports, starring, and deletion.
            </li>
            <li>
              Controlled v0.2 benchmark execution and case inspection.
            </li>
          </ul>

          <p>
            Authentication and SDK packages are not provided by the current
            experiment API.
          </p>
        </div>
      </div>
      <section className="integration-endpoints">
  <div className="section-kicker">
    API REFERENCE
  </div>

  <h2>
    Current endpoints
  </h2>

  <p>
    These are the API operations available in the current experiment.
    Authentication and SDK packages are not currently provided.
  </p>

  <div className="integration-endpoint-list">
    <div className="integration-status-row">
      <span>Health</span>
      <strong>GET /health</strong>
    </div>

    <div className="integration-status-row">
      <span>Create user evaluation</span>
      <strong>POST /v1/user-evaluations</strong>
    </div>

    <div className="integration-status-row">
      <span>Get user evaluation</span>
      <strong>GET /v1/user-evaluations/{"{"}run_id{"}"}</strong>
    </div>

    <div className="integration-status-row">
      <span>List user evaluations</span>
      <strong>GET /v1/user-evaluations</strong>
    </div>

    <div className="integration-status-row">
      <span>Star evaluation</span>
      <strong>POST /v1/user-evaluations/{"{"}run_id{"}"}/star</strong>
    </div>

    <div className="integration-status-row">
      <span>Unstar evaluation</span>
      <strong>DELETE /v1/user-evaluations/{"{"}run_id{"}"}/star</strong>
    </div>

    <div className="integration-status-row">
      <span>Delete evaluation</span>
      <strong>DELETE /v1/user-evaluations/{"{"}run_id{"}"}</strong>
    </div>

    <div className="integration-status-row">
      <span>Run frozen v0.2 benchmark</span>
      <strong>POST /v1/evaluations</strong>
    </div>

    <div className="integration-status-row">
      <span>Get benchmark run</span>
      <strong>GET /v1/evaluations/{"{"}run_id{"}"}</strong>
    </div>

    <div className="integration-status-row">
      <span>Inspect benchmark case</span>
      <strong>GET /v1/evaluations/{"{"}run_id{"}"}/cases/{"{"}pair_id{"}"}</strong>
    </div>
  </div>
</section>
      <section className="integration-grid">
        <div className="integration-main">
          <div className="section-kicker">
            01 / USER EVALUATION
          </div>

          <h2>
            Evaluate business context
          </h2>

          <p>
            Send a business situation and additional context.
            The API returns the original reasoning, the reasoning
            after the additional information, and whether the
            business conclusion changed.
          </p>

          <div className="code-card">
            <div className="code-toolbar">
              <span>
                POST /v1/user-evaluations
              </span>

              <span>
                JSON
              </span>
            </div>

            <pre>{`{
  "name": "Quote Follow-up Decision",
  "objective": "Determine whether the latest customer communication changes the follow-up decision.",
  "workflow": "Sales",
  "record_type": "opportunity",
  "primary_context": "A quote was sent to the customer and no decision has been recorded yet.",
  "additional_context": "The customer replied asking for an update and said they are ready to discuss the next step."
}`}</pre>
          </div>

          <div className="section-kicker integration-step">
            02 / READ THE USER RESULT
          </div>

          <h2>
            Inspect the business conclusion
          </h2>

          <div className="code-card">
            <div className="code-toolbar">
              <span>
                GET /v1/user-evaluations/{"{"}run_id{"}"}
              </span>

              <span>
                JSON
              </span>
            </div>

            <pre>{`{
  "status": "completed",
  "interpretation_changed": false,
  "base": {
    "support_level": "no_secondary_evidence",
    "decision_strength": "moderate"
  },
  "variant": {
    "support_level": "primary_only",
    "decision_strength": "moderate"
  }
}`}</pre>
          </div>

          <div className="section-kicker integration-step">
            03 / CONTROLLED VALIDATION
          </div>

          <h2>
            Run the validated benchmark
          </h2>

          <p>
            The controlled evaluation remains available as a
            separate research and validation surface. It runs the
            frozen 20-case dataset and exposes case-level results.
          </p>

          <div className="code-card">
            <div className="code-toolbar">
              <span>
                POST /v1/evaluations
              </span>

              <span>
                JSON
              </span>
            </div>

            <pre>{`{
  "evaluation_version": "v0.2",
  "source": "frozen-fixtures"
}`}</pre>
          </div>
        </div>

        <aside className="integration-side">
          <div className="integration-card">
            <div className="section-kicker">
              USER EVALUATION
            </div>

            <h3>
              What your application can do
            </h3>

            <ul>
              <li>
                Submit a business situation and additional
                information.
              </li>

              <li>
                Compare the original and updated reasoning.
              </li>

              <li>
                Inspect the evidence considered.
              </li>

              <li>
                Retrieve the result by run ID.
              </li>
            </ul>

            <Link
              href="/evaluate"
              className="button button-primary"
            >
              Try an evaluation
            </Link>
          </div>

          <div className="integration-card subtle">
            <div className="section-kicker">
              CONTROLLED BENCHMARK
            </div>

            <h3>
              Keep validation separate from user results.
            </h3>

            <p>
              User evaluations are reasoning results over
              user-supplied context. They are not scored against
              the frozen benchmark ground truth.
            </p>

            <p>
              The controlled benchmark remains the reproducible
              validation surface for the underlying experiment.
            </p>
          </div>
        </aside>
      </section>
    </main>
  );
}