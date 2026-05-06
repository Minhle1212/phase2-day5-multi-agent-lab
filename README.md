# Lab 20: Multi-Agent Research System

Research assistant that takes a complex query, gathers information, analyzes it, and produces a final answer.

## Architecture

```
User Query
   |
   v
Supervisor / Router
   |------> Researcher Agent  -> research_notes
   |------> Analyst Agent     -> analysis_notes
   |------> Writer Agent      -> final_answer
   |
   v
Trace + Benchmark Report
```

## Setup

### 1. Create environment

```bash
python -m venv .venv
.venv\Scripts\activate  # Windows
# source .venv/bin/activate  # macOS/Linux
```

### 2. Install dependencies

```bash
pip install -e ".[llm,dev]"
```

### 3. Configure environment

```bash
cp .env.example .env
```

Edit `.env` with your API keys:

```env
OPENAI_API_KEY=sk-...
TAVILY_API_KEY=tvly-...  # Optional - for live web search
LANGSMITH_API_KEY=...     # Optional - for tracing
LANGSMITH_TRACING=true
```

### 4. Run baseline (single agent)

```bash
python -m multi_agent_research_lab.cli baseline --query "Explain GraphRAG vs standard RAG"
```

### 5. Run multi-agent pipeline

```bash
python -m multi_agent_research_lab.cli multi-agent --query "Explain GraphRAG vs standard RAG"
```

## Results

| Run | Latency | Cost | Citation Coverage |
|-----|--------:|-----:|-----------------:|
| baseline | 17.46s | $0.0004 | 0% |
| multi-agent | 42.35s | $0.0012 | 67% |

**Key Trade-offs:**
- Multi-agent costs 3x more but provides sourced citations
- Multi-agent is 2.4x slower due to sequential agent calls
- Quality improvements (citations, analysis depth) justify cost for research tasks

## Files

```
src/multi_agent_research_lab/
├── agents/           # Supervisor, Researcher, Analyst, Writer
├── core/             # State, schemas, config
├── graph/            # LangGraph workflow
├── services/         # LLM client, search client
├── evaluation/        # Benchmark runner
├── observability/     # Tracing (LangSmith)
└── cli.py            # CLI entrypoint

reports/
├── benchmark_report.md
├── exit_ticket.md
└── traces/           # Execution traces
```

## Common Issues

**Python 3.10 compatibility:** If you see `required associated type` errors, use Python 3.11+ or patch `pyproject.toml`:

```toml
[tool.coverage.run]
source = ["src"]
omit = ["*__pycache__*", "*.pyc"]
branch = true

[tool.coverage.report]
exclude-lines = [
    "pragma: no cover",
    "if TYPE_CHECKING:",
]
```

**Missing API keys:** Set `OPENAI_API_KEY` in `.env`. Without it, the CLI returns placeholder responses.
