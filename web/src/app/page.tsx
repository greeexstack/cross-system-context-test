import Link from "next/link";

function ArrowIcon() {
  return (
    <svg viewBox="0 0 20 20" aria-hidden="true">
      <path
        d="M4 10h11M10.5 5.5 15 10l-4.5 4.5"
        fill="none"
        stroke="currentColor"
        strokeWidth="1.7"
        strokeLinecap="round"
        strokeLinejoin="round"
      />
    </svg>
  );
}

function ShieldIcon() {
  return (
    <svg viewBox="0 0 24 24" aria-hidden="true">
      <path
        d="M12 3.5 19 6v5.5c0 4.1-2.5 7.7-7 9-4.5-1.3-7-4.9-7-9V6l7-2.5Z"
        fill="none"
        stroke="currentColor"
        strokeWidth="1.5"
      />
      <path
        d="m9 12 2 2 4-4"
        fill="none"
        stroke="currentColor"
        strokeWidth="1.5"
        strokeLinecap="round"
        strokeLinejoin="round"
      />
    </svg>
  );
}

function LayersIcon() {
  return (
    <svg viewBox="0 0 24 24" aria-hidden="true">
      <path
        d="m12 4 8 4-8 4-8-4 8-4Zm-8 8 8 4 8-4m-16 4 8 4 8-4"
        fill="none"
        stroke="currentColor"
        strokeWidth="1.5"
        strokeLinecap="round"
        strokeLinejoin="round"
      />
    </svg>
  );
}

export default function Home() {
  return (
    <main className="site-shell">
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

      <section className="hero">
        <div className="hero-copy">
          <div className="overline">CONTEXT EVALUATION</div>

          <h1>
            See whether additional context actually changes the decision.
          </h1>

          <p className="hero-subtitle">
            Run a controlled evaluation, inspect the evidence behind each
            result, and separate meaningful context changes from noise.
          </p>

          <div className="hero-actions">
            <Link href="/evaluate" className="button button-primary">
              Start an evaluation
              <ArrowIcon />
            </Link>

            <Link href="/integrate" className="button button-ghost">
              Connect your system
            </Link>
          </div>

          <div className="trust-row">
            <span>
              <span className="trust-dot" />
              Controlled dataset
            </span>
            <span>20 cases</span>
            <span>Reproducible results</span>
          </div>
        </div>

        <div className="hero-visual">
          <div className="visual-window">
            <div className="window-top">
              <span className="window-label">EVALUATION</span>
              <span className="window-status">
                <span className="status-dot" />
                Complete
              </span>
            </div>

            <div className="visual-number">20 / 20</div>
            <div className="visual-title">Checks passed</div>

            <div className="visual-divider" />

            <div className="mini-row">
              <span>Context sensitivity</span>
              <strong>Verified</strong>
            </div>
            <div className="mini-row">
              <span>Identity integrity</span>
              <strong>Verified</strong>
            </div>
            <div className="mini-row">
              <span>Temporal integrity</span>
              <strong>Verified</strong>
            </div>

            <div className="visual-footer">
              Controlled evaluation dataset
            </div>
          </div>

          <div className="visual-glow visual-glow-one" />
          <div className="visual-glow visual-glow-two" />
        </div>
      </section>

      <section className="feature-strip">
        <div className="feature-card">
          <div className="feature-icon">
            <ShieldIcon />
          </div>
          <div>
            <h2>Controlled</h2>
            <p>Evaluate a fixed, validated set of cases.</p>
          </div>
        </div>

        <div className="feature-card">
          <div className="feature-icon">
            <LayersIcon />
          </div>
          <div>
            <h2>Case-level</h2>
            <p>Inspect what changed rather than only seeing a score.</p>
          </div>
        </div>

        <div className="feature-card">
          <div className="feature-icon">
            <ArrowIcon />
          </div>
          <div>
            <h2>Traceable</h2>
            <p>Move from an overall result down to the underlying case.</p>
          </div>
        </div>
      </section>

      <section className="home-bottom">
        <div className="section-kicker">A SIMPLE WORKFLOW</div>
        <h2>From question to evidence.</h2>

        <div className="workflow">
          <div className="workflow-step">
            <span>01</span>
            <div>
              <strong>Describe</strong>
              <p>Give the evaluation a name and state what you want to learn.</p>
            </div>
          </div>

          <div className="workflow-step">
            <span>02</span>
            <div>
              <strong>Run</strong>
              <p>Execute the controlled evaluation without changing its logic.</p>
            </div>
          </div>

          <div className="workflow-step">
            <span>03</span>
            <div>
              <strong>Inspect</strong>
              <p>Review the overall result, individual cases, and evidence.</p>
            </div>
          </div>
        </div>
      </section>
    </main>
  );
}