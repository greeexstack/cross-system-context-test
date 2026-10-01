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
  "support_changed": true,
  "decision_strength_changed": false
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