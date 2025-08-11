# Transparent Agent
A tiny, explainable agent that shows every prompt, tool call, and file it touches.

Goal: you give it context + a task → it plans, codes, searches, runs, and returns a clear, audited report of everything it did.
Scope: minimal demo you can clone, run, and extend.

Why this exists
Most agents feel like a black box. This MVP is a glass box:

100% I/O explainability: every external input and output is logged (prompts, parameters, tool calls, files, web queries, results).

Deterministic-ish replays: same inputs/model/settings → reproducible run + side-effects in a sandbox.

Local-first: logs stored locally; no telemetry; redact secrets by default.

Model-agnostic: defaults to gpt-5-thinking (or any OpenAI Chat Completions model) but can point to other providers / local models.

Note: “100% explainability” here means everything observable outside the model’s private scratchpad (all prompts/responses/tool I/O). Models don’t expose hidden chain-of-thought; we store a rationale summary instead.

Quickstart (60 seconds)
bash
Copy
Edit
# 1) Clone
git clone https://github.com/<you>/transparent-agent
cd transparent-agent

# 2) Setup (Python 3.11+)
python -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt

# 3) Configure
cp .env.example .env
# edit .env to set: OPENAI_API_KEY=... MODEL=gpt-5-thinking

# 4) Run a demo task
python -m agent run \
  --goal "Write a Python function to dedupe emails, add tests, and explain decisions." \
  --context "examples/sample_context.md" \
  --tools "web,code,fs" \
  --report out/report.md

# 5) Open the report
open out/report.md   # or just cat it
What you’ll see
A single Run Report that’s easy to read and share:

Inputs (task, context, model, seed, config)

Plan (high-level steps)

Tool Timeline (web searches, code runs, file writes) with timestamps

LLM Exchanges (full prompts + responses, redactions applied)

Artifacts (files created/modified)

Tests & Results

Costs & Tokens (by step and total)

Final Answer + Next Steps

Reproduce this run (one command)

Minimal example command
bash
Copy
Edit
python -m agent run \
  --goal "Research top 3 pitfalls of running H100 at home, cite sources, output markdown." \
  --context "notes/hardware_constraints.txt" \
  --tools "web" \
  --report out/h100_pitfalls.md \
  --seed 42
Sample (truncated) report
md
Copy
Edit
# Run Report — 2025-08-11T16:24:03Z

## Inputs
- goal: Research top 3 pitfalls of running H100 at home, cite sources, output markdown.
- context: notes/hardware_constraints.txt (sha256: 7f2…c1a)
- model: gpt-5-thinking  | temperature: 0.2 | seed: 42
- tools: web
- policy: redact_secrets=true, persist_logs=true, sandbox=.sandbox/

## Plan
1) Extract constraints from context
2) Issue targeted web queries
3) Aggregate credible sources
4) Write summary with citations

## Tool Timeline
- [16:24:05] web.search q="H100 home power requirements"
- [16:24:06] web.open url="…" status=200
- [16:24:09] web.search q="H100 PCIe vs SXM install considerations"
- [16:24:12] file.write path=".sandbox/draft.md" bytes=1432

## LLM Exchanges
### Request #1
**prompt.json** (sha256: 1af…9b0)
```json
{
  "system": "You are a meticulous research agent. Cite reputable sources.",
  "messages": [
    {"role":"user","content":"Goal: Research pitfalls..."},
    {"role":"user","content":"Context excerpt: <…>"}
  ],
  "params": {"temperature":0.2,"seed":42}
}
response.md (tokens_in=534, tokens_out=718, latency=2.1s)

Rationale (summary): Will prioritize power, form factor, and cooling.
Draft bullets with 3–5 sources each…

Artifacts
.sandbox/draft.md (sha256: 51e…ab2)

out/h100_pitfalls.md (sha256: 7b9…e31)

Tests
none in this run

Cost & Tokens
model: gpt-5-thinking

total_tokens_in: 1,238 | total_tokens_out: 1,961

estimated_cost_usd: $0.XX

Final Answer
See: out/h100_pitfalls.md

Reproduce This Run
bash
Copy
Edit
python -m agent replay runs/2025-08-11T16-24-03Z.jsonl
yaml
Copy
Edit

---

## Architecture (MVP)

[CLI] → [Orchestrator]
→ [Planner] → [LLM] (plan)
→ [Executor] ↔ [Tools: web | code | fs | shell]
→ [Tracer] (jsonl log)
→ [Reporter] (Markdown/HTML)

markdown
Copy
Edit

- **Orchestrator**: wires config, seeds, and timeouts.
- **Planner**: asks the model for a simple step plan + rationale summary.
- **Executor**: runs steps with tools, streams events to the **Tracer**.
- **Tracer**: append-only JSONL (hash each record, include parent hash).
- **Reporter**: builds a human-readable report from the trace + artifacts.

---

## Explainability

- **Prompts & Params**: saved verbatim (`prompt.json`) with model, temperature, seed.
- **Responses**: saved as `response.md` (or JSON), plus token counts & latency.
- **Tool Calls**: every call (args + outputs), TTY captured for shell/code runs.
- **Files**: every create/modify with content hash; diffs for edits.
- **Cost Accounting**: per step + total (tokens in/out, estimated $).
- **Replays**: `agent replay <run.jsonl>` reproduces the report locally.
- **Privacy**: secrets redacted at capture (set via `REDACT_KEYS`); logs stay local.

---

## Install

```bash
python -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt
cp .env.example .env
.env

ini
Copy
Edit
OPENAI_API_KEY=sk-...
MODEL=gpt-5-thinking       # or any Chat Completions model name
REDact_KEYS=OPENAI_API_KEY,API_KEY,SECRET
Optional:

Use other providers by setting OPENAI_BASE_URL + OPENAI_API_KEY.

Use local models via an OpenAI-compatible server (e.g., llama.cpp / vLLM) and point OPENAI_BASE_URL at it.

Usage
bash
Copy
Edit
# Basic
python -m agent run --goal "Make a CLI todo app in Python with tests" --tools "code,fs" --report out/todo.md

# With extra context files
python -m agent run --goal "Add a CSV import feature" --context "docs/spec.md,examples/data.csv" --tools "code,fs"

# Web-only research
python -m agent run --goal "Summarize Mixture-of-Experts basics with citations" --tools "web" --report out/moe.md
Artifacts land in .sandbox/ (generated code, data, etc) and out/ (reports).
Full traces are in runs/<timestamp>.jsonl.

Extending tools (tiny API)
Create tools/<name>.py:

python
Copy
Edit
# tools/grep.py
from agent_sdk import Tool, record

class Grep(Tool):
    name = "grep"
    description = "Search for a string in a file and return matching lines."
    schema = {"pattern": "str", "path": "str"}

    def run(self, pattern: str, path: str):
        out = []
        with open(path) as f:
            for i, line in enumerate(f, 1):
                if pattern in line:
                    out.append({"line": i, "text": line.rstrip()})
        record("tool_output", {"matches": out})  # goes into the trace
        return out
Register it in agent.config.yaml:

yaml
Copy
Edit
tools:
  - web
  - code
  - fs
  - grep
Configuration
agent.config.yaml (defaults shown)

yaml
Copy
Edit
model: ${MODEL}
temperature: 0.2
seed: 42
timeout_s: 120
sandbox_dir: ".sandbox"
out_dir: "out"
persist_logs: true
redact_secrets: true
redact_keys:
  - OPENAI_API_KEY
  - API_KEY
  - SECRET
tools:
  - web
  - code
  - fs
Safety & limits
Sandbox: code runs inside .sandbox/. Don’t point tools at sensitive paths.

No hidden telemetry: nothing is sent anywhere except the model endpoint you configure.

Rationales: stored as summaries; the model’s hidden scratchpad is not captured.

Roadmap
 HTML report with collapsible sections

 Better test runner + coverage

 First-class local model presets

 Multi-step “critic” review pass

 One-click share (redacted bundle)

FAQ
Can I see every prompt and response?
Yes—saved per exchange, with token counts and hashes. Secrets are redacted by default.

Can I use this offline?
Yes with a local, OpenAI-compatible model server. Web tool will be disabled.

How is this different from other agents?
It’s intentionally small, trace-first, and report-first. The report is the product.

License
MIT © You

Folder layout
arduino
Copy
Edit
transparent-agent/
  agent/               # orchestrator, planner, executor, reporter
  tools/               # web, code, fs, (add your own)
  runs/                # jsonl traces (gitignored)
  out/                 # human-readable reports (gitignored)
  .sandbox/            # artifacts (gitignored)
  examples/
  .env.example
  agent.config.yaml
  requirements.txt
  README.md
One-liner pitch (for the repo description)
Transparent Agent (MVP): a glass-box AI agent that plans, searches, codes, and returns a single, audited report with every prompt, tool call, file change, and cost. Reproducible. Local-first.
