import argparse
import os
from datetime import datetime
from pathlib import Path

from dotenv import load_dotenv


def run(goal: str, context_paths: str, tools: str, report_path: str) -> None:
    """Execute a minimal run and write a markdown report."""
    load_dotenv()
    context_texts = []
    if context_paths:
        for p in context_paths.split(","):
            p = p.strip()
            if not p:
                continue
            try:
                with open(p, "r", encoding="utf-8") as f:
                    context_texts.append(f.read())
            except FileNotFoundError:
                context_texts.append(f"[missing context file: {p}]")
    context_content = "\n\n".join(context_texts)

    model = os.getenv("MODEL", "gpt-4o-mini")
    api_key = os.getenv("OPENAI_API_KEY")
    if api_key:
        try:
            from openai import OpenAI

            client = OpenAI(api_key=api_key)
            messages = [
                {"role": "system", "content": "You are a helpful assistant."},
                {"role": "user", "content": f"Goal: {goal}\nContext:\n{context_content}"},
            ]
            completion = client.chat.completions.create(
                model=model,
                messages=messages,
            )
            result = completion.choices[0].message.content
        except Exception as e:  # pragma: no cover - best effort
            result = f"Model call failed: {e}"
    else:
        result = "OPENAI_API_KEY not set. Skipping model call."

    report = f"""# Run Report - {datetime.utcnow().isoformat()}Z

## Inputs
- goal: {goal}
- context files: {context_paths}
- model: {model}
- tools: {tools}

## Output
{result}
"""

    report_file = Path(report_path)
    report_file.parent.mkdir(parents=True, exist_ok=True)
    report_file.write_text(report, encoding="utf-8")
    print(f"Report written to {report_file}")


def main() -> None:
    parser = argparse.ArgumentParser(prog="agent")
    subparsers = parser.add_subparsers(dest="command")

    run_parser = subparsers.add_parser("run", help="run a goal")
    run_parser.add_argument("--goal", required=True)
    run_parser.add_argument("--context", default="")
    run_parser.add_argument("--tools", default="")
    run_parser.add_argument("--report", default="out/report.md")

    args = parser.parse_args()
    if args.command == "run":
        run(args.goal, args.context, args.tools, args.report)
    else:
        parser.print_help()


if __name__ == "__main__":
    main()
