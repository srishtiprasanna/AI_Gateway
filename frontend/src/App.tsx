import { useState } from "react";
import ReactMarkdown from "react-markdown";
import remarkGfm from "remark-gfm";
import "./App.css";

interface GatewayData {
  provider: string;
  model: string;
  latency: number;
  usage?: {
    prompt_tokens: number;
    completion_tokens: number;
    total_tokens: number;
  };
}

interface ResearchData {
  topic: string;
  report: string;
  sources: {
    arxiv?: unknown;
    web?: unknown;
    youtube?: unknown;
    memory?: unknown;
  };
  gateway: GatewayData;
}

function App() {
  const [topic, setTopic] = useState("");
  const [report, setReport] = useState("");
  const [gateway, setGateway] = useState<GatewayData | null>(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState("");

  const startResearch = async () => {
    if (!topic.trim()) {
      setError("Enter a topic to start your research.");
      return;
    }

    setLoading(true);
    setError("");
    setReport("");
    setGateway(null);

    try {
      const response = await fetch("http://127.0.0.1:8000/research", {
        method: "POST",
        headers: {
          "Content-Type": "application/json",
        },
        body: JSON.stringify({
          topic: topic.trim(),
        }),
      });

      if (!response.ok) {
        throw new Error("Research request failed.");
      }

      const data: ResearchData = await response.json();

      setReport(data.report);
      setGateway(data.gateway);
    } catch (error) {
      console.error(error);

      setError(
        "Could not connect to the Research Agent. Make sure FastAPI is running."
      );
    } finally {
      setLoading(false);
    }
  };

  const resetResearch = () => {
    setReport("");
    setGateway(null);
    setTopic("");
    setError("");
  };

  const getModelName = (model: string) => {
    if (model.includes("/")) {
      return model.split("/").pop();
    }

    return model;
  };

  return (
    <div className="app">
      <div className="glow glow-one"></div>
      <div className="glow glow-two"></div>

      {/* NAVBAR */}

      <nav className="navbar">
        <div className="brand">
          <div className="brand-icon">✦</div>
          <span>Scout</span>
        </div>

        <div className="nav-status">
          <span className="status-dot"></span>
          MCP + AI Gateway
        </div>
      </nav>

      <main className="main-content">

        {/* HOME */}

        {!report && !loading && (
          <section className="hero">
            <div className="eyebrow">
              <span>✦</span> MULTI-SOURCE INTELLIGENCE
            </div>

            <h1>
              Research anything.
              <br />
              <span>Understand everything.</span>
            </h1>

            <p className="hero-description">
              An AI research agent that searches academic papers, the live web,
              YouTube explanations, and persistent memory before generating
              your research report.
            </p>

            <div className="search-card">
              <div className="input-wrapper">
                <span className="search-icon">⌕</span>

                <input
                  type="text"
                  placeholder="What would you like to research?"
                  value={topic}
                  onChange={(e) => setTopic(e.target.value)}
                  onKeyDown={(e) => {
                    if (e.key === "Enter") {
                      startResearch();
                    }
                  }}
                />
              </div>

              <button onClick={startResearch}>
                Start Research
                <span>→</span>
              </button>
            </div>

            <div className="suggestions">
              <span>Try:</span>

              {[
                "Agentic AI",
                "Quantum Computing",
                "AI in Healthcare",
                "Climate Change",
              ].map((item) => (
                <button
                  key={item}
                  onClick={() => setTopic(item)}
                >
                  {item}
                </button>
              ))}
            </div>

            <div className="source-grid">
              <div className="source-card">
                <div className="source-icon paper">⌁</div>

                <div>
                  <strong>Academic</strong>
                  <p>arXiv papers</p>
                </div>
              </div>

              <div className="source-card">
                <div className="source-icon web">◉</div>

                <div>
                  <strong>Web</strong>
                  <p>Current information</p>
                </div>
              </div>

              <div className="source-card">
                <div className="source-icon youtube">▶</div>

                <div>
                  <strong>YouTube</strong>
                  <p>Videos & transcripts</p>
                </div>
              </div>

              <div className="source-card">
                <div className="source-icon memory">✦</div>

                <div>
                  <strong>Memory</strong>
                  <p>Persistent context</p>
                </div>
              </div>
            </div>
          </section>
        )}

        {/* LOADING */}

        {loading && (
          <section className="researching">
            <div className="researching-header">
              <div className="spinner"></div>

              <div>
                <div className="eyebrow">RESEARCH IN PROGRESS</div>

                <h2>Gathering intelligence...</h2>

                <p>
                  We're searching multiple sources for{" "}
                  <strong>"{topic}"</strong>
                </p>
              </div>
            </div>

            <div className="pipeline">

              <div className="pipeline-item active">
                <span>01</span>

                <div>
                  <strong>Academic Papers</strong>
                  <p>Searching arXiv</p>
                </div>

                <b>✓</b>
              </div>

              <div className="pipeline-item active">
                <span>02</span>

                <div>
                  <strong>Current Web</strong>
                  <p>Searching live sources</p>
                </div>

                <b>✓</b>
              </div>

              <div className="pipeline-item active">
                <span>03</span>

                <div>
                  <strong>Video Knowledge</strong>
                  <p>Finding YouTube explanations</p>
                </div>

                <b>✓</b>
              </div>

              <div className="pipeline-item active">
                <span>04</span>

                <div>
                  <strong>Research Memory</strong>
                  <p>Checking previous context</p>
                </div>

                <b>✓</b>
              </div>

              <div className="pipeline-item current">
                <span>05</span>

                <div>
                  <strong>AI Synthesis</strong>
                  <p>Building your research report</p>
                </div>

                <div className="mini-spinner"></div>
              </div>

            </div>
          </section>
        )}

        {/* ERROR */}

        {error && <div className="error">{error}</div>}

        {/* RESULT */}

        {report && !loading && (
          <section className="result">

            {/* RESULT HEADER */}

            <div className="result-top">

              <div>
                <div className="eyebrow">
                  RESEARCH COMPLETE
                </div>

                <h2>{topic}</h2>

                <p className="result-subtitle">
                  Multi-source research synthesized by the AI Gateway
                </p>
              </div>

              <button
                className="new-search"
                onClick={resetResearch}
              >
                ← New Research
              </button>

            </div>

            {/* SOURCE OVERVIEW */}

            <div className="research-source-bar">

              <div>
                <span className="source-number">01</span>

                <div>
                  <strong>Academic</strong>
                  <p>arXiv</p>
                </div>
              </div>

              <div>
                <span className="source-number">02</span>

                <div>
                  <strong>Web</strong>
                  <p>Live search</p>
                </div>
              </div>

              <div>
                <span className="source-number">03</span>

                <div>
                  <strong>Video</strong>
                  <p>YouTube</p>
                </div>
              </div>

              <div>
                <span className="source-number">04</span>

                <div>
                  <strong>Memory</strong>
                  <p>Persistent context</p>
                </div>
              </div>

            </div>

            {/* REPORT */}

            <div className="report-card">

              <div className="report-label">
                <span>✦</span>
                AI RESEARCH REPORT
              </div>

              <div className="report-content">

                <ReactMarkdown
                  remarkPlugins={[remarkGfm]}
                  components={{
                    h1: ({ children }) => (
                      <h1 className="report-h1">{children}</h1>
                    ),

                    h2: ({ children }) => (
                      <h2 className="report-h2">{children}</h2>
                    ),

                    h3: ({ children }) => (
                      <h3 className="report-h3">{children}</h3>
                    ),

                    p: ({ children }) => (
                      <p className="report-paragraph">{children}</p>
                    ),

                    strong: ({ children }) => (
                      <strong className="report-strong">
                        {children}
                      </strong>
                    ),

                    table: ({ children }) => (
                      <div className="table-wrapper">
                        <table>{children}</table>
                      </div>
                    ),

                    a: ({ href, children }) => (
                      <a
                        href={href}
                        target="_blank"
                        rel="noopener noreferrer"
                        className="report-link"
                      >
                        {children}
                      </a>
                    ),

                    li: ({ children }) => (
                      <li className="report-list-item">
                        {children}
                      </li>
                    ),
                  }}
                >
                  {report}
                </ReactMarkdown>

              </div>
            </div>

            {/* GATEWAY */}

            {gateway && (
              <div className="gateway-card">

                <div className="gateway-heading">
                  <div className="gateway-icon">✦</div>

                  <div>
                    <div className="gateway-label">
                      POWERED BY
                    </div>

                    <strong>AI Gateway</strong>
                  </div>
                </div>

                <div className="gateway-stat">
                  <span>MODEL</span>
                  <strong>
                    {getModelName(gateway.model)}
                  </strong>
                </div>

                <div className="gateway-stat">
                  <span>PROVIDER</span>
                  <strong>{gateway.provider}</strong>
                </div>

                <div className="gateway-stat">
                  <span>LATENCY</span>
                  <strong>
                    {gateway.latency}s
                  </strong>
                </div>

                <div className="gateway-stat">
                  <span>STATUS</span>

                  <strong className="online">
                    <i></i>
                    Online
                  </strong>
                </div>

              </div>
            )}

            {/* TOKEN USAGE */}

            {gateway?.usage && (
              <div className="usage-card">

                <div>
                  <span>INPUT TOKENS</span>
                  <strong>
                    {gateway.usage.prompt_tokens.toLocaleString()}
                  </strong>
                </div>

                <div>
                  <span>OUTPUT TOKENS</span>
                  <strong>
                    {gateway.usage.completion_tokens.toLocaleString()}
                  </strong>
                </div>

                <div>
                  <span>TOTAL TOKENS</span>
                  <strong>
                    {gateway.usage.total_tokens.toLocaleString()}
                  </strong>
                </div>

              </div>
            )}

          </section>
        )}

      </main>

      <footer>
        <span>Scout - AI Research Agent</span>
        <span>Built with MCP + AI Gateway</span>
      </footer>
    </div>
  );
}

export default App;