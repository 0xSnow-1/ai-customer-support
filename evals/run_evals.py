
import json
from dataclasses import dataclass
from datetime import datetime
from pathlib import Path

from pydantic_evals import Case, Dataset
from pydantic_evals.evaluators import Evaluator, EvaluatorContext
from pydantic_evals.reporting import EvaluationReport
from rich.console import Console

from app.ai.decide import decide
from app.ai.schemas import Decision
from evals.golden_emails import GOLDEN_EMAILS

RUNS_DIR = Path(__file__).parent / "runs"


@dataclass
class SectionMatches(Evaluator):
    def evaluate(self, ctx: EvaluatorContext) -> bool:
        return ctx.output.section == ctx.expected_output["section"]


@dataclass
class ActionMatches(Evaluator):
    def evaluate(self, ctx: EvaluatorContext) -> bool:
        return ctx.output.action == ctx.expected_output["action"]


def run_pipeline(email: str) -> Decision:
    return decide(email)


dataset = Dataset(
    name="golden-emails",
    cases=[
        Case(
            name=case["name"],
            inputs=case["email"],
            expected_output={"section": case["section"], "action": case["action"]},
        )
        for case in GOLDEN_EMAILS
    ],
    evaluators=[SectionMatches(), ActionMatches()],
)


def _result(result):
    return {"value": result.value, "reason": result.reason}


def save_report(report: EvaluationReport, run_at: datetime) -> Path:
    RUNS_DIR.mkdir(exist_ok=True)
    name = report.dataset_name or report.name
    path = RUNS_DIR / f"{run_at:%Y-%m-%dT%H-%M-%S}-{name}"

    averages = report.averages()
    payload = {
        "run_at": run_at.isoformat(),
        "dataset": name,
        "averages": averages.model_dump() if averages else None,
        "cases": [
            {
                "name": case.name,
                "input": case.inputs,
                "expected": case.expected_output,
                "output": case.output.model_dump()
                if hasattr(case.output, "model_dump")
                else case.output,
                "assertions": {k: _result(v) for k, v in case.assertions.items()},
                "scores": {k: _result(v) for k, v in case.scores.items()},
                "labels": {k: _result(v) for k, v in case.labels.items()},
                "metrics": case.metrics,
                "task_duration": case.task_duration,
                "total_duration": case.total_duration,
            }
            for case in report.cases
        ],
        "failures": [
            {"name": failure.name, "error": failure.error_message}
            for failure in report.failures
        ],
    }
    path.with_suffix(".json").write_text(
        json.dumps(payload, indent=2, ensure_ascii=False) + "\n"
    )

    with path.with_suffix(".txt").open("w") as f:
        report.print(
            include_input=False,
            include_output=True,
            include_durations=False,
            console=Console(file=f, width=200),
        )

    return path


if __name__ == "__main__":
    run_at = datetime.now().astimezone()
    report = dataset.evaluate_sync(run_pipeline, max_concurrency=1)
    report.print(include_input=False, include_output=True, include_durations=False)
    path = save_report(report, run_at)
    print(f"\nSaved run to {path.with_suffix('.json')}")
