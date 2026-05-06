# Design Template

## Problem

Build a research assistant that accepts a complex research query and produces a well-cited, structured answer. The system must:
- Accept natural language research queries
- Search for relevant sources
- Analyze and synthesize information from multiple sources
- Produce a final answer with citations
- Provide full observability via traces

## Why multi-agent?

A single agent cannot efficiently handle all three distinct tasks (search, analysis, writing) without:
1. **Context overflow** - Passing all search results through a single prompt wastes tokens
2. **Mixed expertise** - Research, analysis, and writing require different prompting strategies
3. **No parallelization** - Single agent runs sequentially even when subtasks are independent
4. **Harder to debug** - Tracing a monolithic prompt is harder than tracing discrete agent calls

Multi-agent enables:
- Specialized prompts per agent (better quality)
- Clearer debugging via per-agent traces
- Independent scaling of agent capabilities
- Reusable worker agents in other workflows

## Agent roles

| Agent | Responsibility | Input | Output | Failure mode |
|---|---|---|---|---|
| Supervisor | Orchestrates workflow, decides next agent | Full state | Updated `route_history` | Fallback to `done` after max iterations |
| Researcher | Search for sources, create research notes | `request.query` | `sources`, `research_notes` | Skip search, use LLM-only fallback |
| Analyst | Extract key claims, identify gaps | `research_notes` | `analysis_notes` | Return empty analysis with error logged |
| Writer | Synthesize final answer with citations | `research_notes`, `analysis_notes`, `sources` | `final_answer` | Return partial answer with warning |
| Critic | Validate citations and answer quality | `final_answer`, `sources` | `agent_results` findings | Return "no issues" if check fails |

## Shared state

| Field | Type | Why needed |
|---|---|---|
| `request` | ResearchQuery | The original query and parameters that all agents need |
| `iteration` | int | Track loop count to enforce max iterations guardrail |
| `route_history` | list[str] | Sequential log of agent calls for debugging |
| `sources` | list[SourceDocument] | Search results passed from Researcher to Writer |
| `research_notes` | str | Bullet notes with citations from Researcher |
| `analysis_notes` | str | Structured insights from Analyst |
| `final_answer` | str | Synthesized output from Writer |
| `agent_results` | list[AgentResult] | Per-agent token usage and cost for benchmarking |
| `trace` | list[dict] | Structured event log for observability |
| `errors` | list[str] | Captured exceptions for graceful degradation |

## Routing policy

```
┌─────────────┐
│  supervisor │
└──────┬──────┘
       │
       ▼
  ┌─────────────────────────────────────────┐
  │ if not research_notes    → researcher   │
  │ else if not analysis_notes → analyst    │
  │ else if not final_answer → writer      │
  │ else → done                           │
  └─────────────────────────────────────────┘
       │
       ▼
┌─────────────┐     ┌─────────────┐     ┌─────────────┐
│ researcher  │────▶│  supervisor │◀────│   analyst   │
└─────────────┘     └──────┬──────┘     └─────────────┘
       │                   │
       │                   ▼
       │            ┌─────────────┐
       │            │    writer   │
       │            └──────┬──────┘
       │                   │
       │                   ▼
       │            ┌─────────────┐
       └───────────▶│    done     │ (END)
                     └─────────────┘

Max iterations: 6 (from config)
```

## Guardrails

- **Max iterations**: 6 (configurable via `MAX_ITERATIONS`)
  - Supervisor returns `done` when iteration >= max
  - Prevents infinite loops in edge cases
- **Timeout**: 60 seconds per LLM call (configurable via `TIMEOUT_SECONDS`)
  - Prevents hanging on slow API responses
- **Retry**: 3 attempts with exponential backoff
  - Handles transient network failures
  - Multiplier: 1, min wait: 1s, max wait: 8s
- **Fallback**: If search fails, continue with LLM-only mode
  - Search errors are logged but don't crash workflow
- **Validation**: Supervisor checks state fields before routing
  - Ensures agents only run when their prerequisites are met

## Benchmark plan

| Metric | Method | Expected |
|---|---|---|
| Latency | wall-clock time from start to final_answer | Baseline < Multi-agent (single vs 3+ calls) |
| Cost | Sum of `cost_usd` from all `AgentResult.metadata` | Multi-agent higher (more LLM calls) |
| Quality | Peer rubric 0-10 | Multi-agent expected to score higher |
| Citation coverage | % of claims with [n] citations | Multi-agent expected higher |
| Failure rate | % of queries that error | Both should be 0% |

### Test queries

1. **Simple factual**: "What is the capital of France?"
   - Expected: Both pass, similar quality
   - Use case: Baseline should be sufficient

2. **Complex analysis**: "Explain how GraphRAG improves retrieval over standard RAG"
   - Expected: Multi-agent produces better-cited answer
   - Use case: Multi-agent specialization matters

3. **Multi-source synthesis**: "Compare Transformer vs Mamba architectures for long sequences"
   - Expected: Multi-agent finds more sources, better synthesis
   - Use case: Research + Analysis workflow adds value
