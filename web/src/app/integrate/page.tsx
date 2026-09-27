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
          <Link href="/evaluate">
            Evaluations
          </Link>

          <Link
            href="/integrate"
            className="nav-active"
          >
            Integrate
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
          Connect the evaluation engine to your application.
        </h1>

        <p>
          The current integration surface is a REST API over
          the validated controlled evaluation. Your application
          can create a run and inspect its result.
        </p>
      </section>

      <section className="integration-grid">
        <div className="integration-main">
          <div className="section-kicker">
            01 / CREATE A RUN
          </div>

          <h2>
            Send a request
          </h2>

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

          <div className="section-kicker integration-step">
            02 / READ THE RESULT
          </div>

          <h2>
            Inspect the completed evaluation
          </h2>

          <div className="code-card">
            <div className="code-toolbar">
              <span>
                GET /v1/evaluations/{'{run_id}'}
              </span>

              <span>
                JSON
              </span>
            </div>

            <pre>{`{
  "status": "completed",
  "total_cases": 20,
  "passed_cases": 20
}`}</pre>
          </div>
        </div>

        <aside className="integration-side">
          <div className="integration-card">
            <div className="section-kicker">
              CURRENT BOUNDARY
            </div>

            <h3>
              What this API does today
            </h3>

            <ul>
              <li>
                Runs the validated controlled evaluation.
              </li>

              <li>
                Returns case-level results.
              </li>

              <li>
                Exposes detailed case evidence.
              </li>

              <li>
                Provides OpenAPI documentation.
              </li>
            </ul>
          </div>

          <div className="integration-card subtle">
            <div className="section-kicker">
              IMPORTANT
            </div>

            <h3>
              Your own business data is not evaluated yet.
            </h3>

            <p>
              The current product deliberately exposes the
              validated experiment rather than pretending
              arbitrary customer data can already be evaluated
              with the same guarantees.
            </p>
          </div>
        </aside>
      </section>
    </main>
  );
}