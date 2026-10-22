"""The command line: run on your data, review in a CSV, check the examples, write a config file;
and one command per companion workflow (commands.py)."""

import argparse
import json
import sys
import tempfile
from pathlib import Path

import yaml

from . import pipeline
from .commands import COMMANDS
from .core import runner
from .core.checks import compare_example

PROG = "contacts-nayose"
TRUE = {"1", "true", "yes", "on"}


def cast(value, kind):
    if value is None:
        return None
    if kind == "INT":
        return int(value)
    if kind == "FLOAT":
        return float(value)
    if kind == "BOOLEAN":
        return value if isinstance(value, bool) else str(value).lower() in TRUE
    return value


def given(args, module) -> dict:
    """Input values: the config file, then the options (an option wins)."""
    config = getattr(args, "config", None)
    values = (yaml.safe_load(Path(config).read_text(encoding="utf-8")) or {}) if config else {}
    for name, (_, kind, *_) in module.INPUTS.items():
        if getattr(args, name, None) is not None:
            values[name] = getattr(args, name)
        if name in values:
            values[name] = cast(values[name], kind)
    return values


def run(args, module=pipeline) -> int:
    out = Path(args.out)
    out.mkdir(parents=True, exist_ok=True)
    store = out / "reviews.csv"  # every decision so far
    labels = runner.read_reviews(store) | runner.read_reviews(Path(args.reviews) if getattr(args, "reviews", None) else None)
    runner.write_reviews(store, labels)
    rt = module.run(out, labels, **given(args, module))
    for line in rt.lines:
        print(line)
    for name, path in runner.write_outputs(rt, out).items():
        print(f"→ {name}: {path}")
    asked = runner.review_batch(rt, out / "review_batch.csv")
    if asked:
        print(f"→ {asked} pairs to review: fill the decision column of {out / 'review_batch.csv'} (same / different),"
              f" then run again with --reviews {out / 'review_batch.csv'}")
    failed = [c for c in rt.checks if not c["passed"]]
    print(f"{len(rt.checks) - len(failed)} of {len(rt.checks)} checks passed")
    return 1 if failed else 0


def check_examples() -> list[str]:
    """Every example's expectations and every stage Check, on the shipped example data."""
    problems = []
    for command, module in [("run", pipeline), *COMMANDS.items()]:
        for example in module.EXAMPLES:
            with tempfile.TemporaryDirectory() as tmp:
                rt = module.run(Path(tmp), {}, **example["given"])
                data = {name: runner.plain(value) for name, value in rt.outputs.items()}
                where = f"{command} {example['id']}"
                problems += [f"{where}: {m}" for m in compare_example(example["expect"], data, {"lines": rt.lines})]
                problems += [f"{where}: check failed · {c['says']} · {c['evidence']}" for c in rt.checks if not c["passed"]]
    return problems


def check(_args) -> int:
    total = len(pipeline.EXAMPLES) + sum(len(m.EXAMPLES) for m in COMMANDS.values())
    if not total:
        print("No examples to run.")
        return 0
    problems = check_examples()
    for p in problems:
        print("✗", p)
    print(f"{total} example(s): " + ("all passed" if not problems else f"{len(problems)} problem(s)"))
    return 1 if problems else 0


def init(args) -> int:
    """A config file with every input, its description and its default, to edit."""
    path = Path(args.path)
    if path.exists():
        print(f"{path} exists; not overwritten.")
        return 1
    lines = [f"# {pipeline.TITLE} {pipeline.VERSION}: input values. Edit, then: {PROG} run --config {path}"]
    for name, (default, _, description, *_) in pipeline.INPUTS.items():
        lines.append(f"\n# {description}" if description else "")
        if isinstance(default, str) and "\n" in default:
            lines.append(f"{name}: |\n" + "\n".join("  " + x for x in default.splitlines()))
        else:
            lines.append(f"{name}: {json.dumps(default, ensure_ascii=False)}")
    path.write_text("\n".join(lines).strip() + "\n", encoding="utf-8")
    print(f"Wrote {path}")
    return 0


def options(parser, module) -> None:
    """One option per input of a workflow, with its description, default and choices."""
    for name, (default, kind, description, *rest) in module.INPUTS.items():
        shown = str(default).splitlines()[0][:40] if default not in (None, "") else ""
        tip = f"{description} (default: {shown})".replace("%", "%%")
        choices = rest[0] if rest and rest[0] else None
        parser.add_argument(f"--{name.replace('_', '-')}", dest=name, default=None, help=tip, choices=choices)


def main(argv=None) -> None:
    for stream in (sys.stdout, sys.stderr):  # Windows writes a pipe or file in its code page otherwise
        if hasattr(stream, "reconfigure"):
            stream.reconfigure(encoding="utf-8", errors="replace")
    parser = argparse.ArgumentParser(prog=PROG, description=pipeline.PURPOSE.replace("%", "%%"))
    sub = parser.add_subparsers(dest="command", required=True)
    go = sub.add_parser("run", help="run on your data")
    options(go, pipeline)
    go.add_argument("--config", help=f"a YAML file of input values (write one with: {PROG} init)")
    go.add_argument("--reviews", help="your filled-in review CSV (decision: same / different)")
    go.add_argument("--out", default="out", help="where results, reviews and run folders go")
    sub.add_parser("check", help="run the examples and every stage Check; exit 1 if any fails")
    start = sub.add_parser("init", help="write a config file with every input to edit")
    start.add_argument("path", nargs="?", default="config.yaml")
    for command, module in COMMANDS.items():
        more = sub.add_parser(command, help=module.PURPOSE.replace("%", "%%"))
        options(more, module)
        more.add_argument("--out", default=command, help="where its results and run folders go")
    args = parser.parse_args(argv)
    if args.command in COMMANDS:
        sys.exit(run(args, COMMANDS[args.command]))
    sys.exit({"run": run, "check": check, "init": init}[args.command](args))
