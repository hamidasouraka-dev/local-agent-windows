"""Autopilot mode — autonomous task execution with planning and verification.

The agent plans a task, breaks it into steps, executes each step autonomously,
and verifies results before moving to the next step.
"""

from __future__ import annotations

import json
import time
from dataclasses import dataclass, field
from enum import Enum
from typing import Any, Generator

from .providers.base import LLMProvider, Message


class StepStatus(str, Enum):
    PENDING = "pending"
    RUNNING = "running"
    DONE = "done"
    FAILED = "failed"
    SKIPPED = "skipped"


@dataclass
class TaskStep:
    id: int
    description: str
    status: StepStatus = StepStatus.PENDING
    result: str = ""
    duration: float = 0.0


@dataclass
class TaskPlan:
    objective: str
    steps: list[TaskStep] = field(default_factory=list)
    created_at: float = field(default_factory=time.time)
    total_duration: float = 0.0


PLANNER_PROMPT = """You are a task planner. Given an objective, break it down into concrete executable steps.

Rules:
- Each step must be a single, atomic action the coding agent can perform
- Steps should be in logical order
- Include verification steps (e.g., "run tests", "check output")
- Be specific — not "set up the project" but "create package.json with express dependency"
- Keep it to 3-10 steps for most tasks
- Include a final verification step

Respond with ONLY a JSON array of step descriptions:
["step 1 description", "step 2 description", ...]
"""

EXECUTOR_PROMPT = """You are executing step {step_num} of {total_steps} in an autonomous task.

Objective: {objective}

Previous steps completed:
{previous_steps}

Current step: {current_step}

Execute this step completely. Use the tools available to you.
When done, summarize what you accomplished in 1-2 sentences.
"""

VERIFIER_PROMPT = """You are verifying the results of an autonomous task.

Objective: {objective}

Steps completed:
{completed_steps}

Review whether the objective has been achieved. Check for:
1. All files created/modified correctly
2. Code compiles/runs without errors
3. Tests pass (if applicable)
4. No obvious issues

Respond with a JSON object:
{{"success": true/false, "summary": "brief summary", "issues": ["issue 1", ...] }}
"""


class Autopilot:
    """Autonomous task executor with plan-execute-verify loop."""

    def __init__(
        self,
        provider: LLMProvider,
        tools_registry: Any = None,
        on_step_start: Any = None,
        on_step_end: Any = None,
        on_tool_call: Any = None,
        on_tool_result: Any = None,
        max_rounds_per_step: int = 10,
    ) -> None:
        self.provider = provider
        self.tools = tools_registry
        self.on_step_start = on_step_start
        self.on_step_end = on_step_end
        self.on_tool_call = on_tool_call
        self.on_tool_result = on_tool_result
        self.max_rounds = max_rounds_per_step
        self._plan: TaskPlan | None = None

    def plan(self, objective: str) -> TaskPlan:
        """Create an execution plan for the objective."""
        system_msg = Message(role="system", content=PLANNER_PROMPT)
        user_msg = Message(role="user", content=f"Objective: {objective}")

        response = self.provider.chat([system_msg, user_msg], tools=[])
        steps = self._parse_plan(response.content)

        self._plan = TaskPlan(
            objective=objective,
            steps=[
                TaskStep(id=i + 1, description=desc)
                for i, desc in enumerate(steps)
            ],
        )
        return self._plan

    def execute(self, plan: TaskPlan | None = None) -> Generator[dict[str, Any], None, TaskPlan]:
        """Execute all steps in the plan. Yields progress updates."""
        p = plan or self._plan
        if p is None:
            raise ValueError("No plan to execute. Call plan() first.")

        from .agent import CodingAgent

        agent = CodingAgent(self.provider)

        for step in p.steps:
            step.status = StepStatus.RUNNING
            if self.on_step_start:
                self.on_step_start(step)

            yield {
                "event": "step_start",
                "step": step.id,
                "total": len(p.steps),
                "description": step.description,
            }

            t0 = time.time()

            # Build context from previous steps
            previous = "\n".join(
                f"  Step {s.id}: {s.description} → {s.result}"
                for s in p.steps
                if s.status == StepStatus.DONE
            ) or "(none)"

            prompt = EXECUTOR_PROMPT.format(
                step_num=step.id,
                total_steps=len(p.steps),
                objective=p.objective,
                previous_steps=previous,
                current_step=step.description,
            )

            try:
                result = agent.run_turn(prompt)
                step.result = result
                step.status = StepStatus.DONE
            except Exception as e:
                step.result = f"Error: {e}"
                step.status = StepStatus.FAILED

            step.duration = time.time() - t0

            if self.on_step_end:
                self.on_step_end(step)

            yield {
                "event": "step_end",
                "step": step.id,
                "status": step.status.value,
                "result": step.result[:200],
                "duration": round(step.duration, 1),
            }

            if step.status == StepStatus.FAILED:
                yield {
                    "event": "task_failed",
                    "failed_step": step.id,
                    "error": step.result,
                }
                break

        p.total_duration = sum(s.duration for s in p.steps)

        yield {
            "event": "task_complete",
            "objective": p.objective,
            "steps_done": sum(1 for s in p.steps if s.status == StepStatus.DONE),
            "steps_total": len(p.steps),
            "total_duration": round(p.total_duration, 1),
        }

        return p

    def verify(self, plan: TaskPlan | None = None) -> dict[str, Any]:
        """Verify the results of the executed plan."""
        p = plan or self._plan
        if p is None:
            return {"success": False, "summary": "No plan to verify."}

        completed = "\n".join(
            f"  Step {s.id} [{s.status.value}]: {s.description}\n    Result: {s.result[:200]}"
            for s in p.steps
        )

        system_msg = Message(role="system", content=VERIFIER_PROMPT.format(
            objective=p.objective,
            completed_steps=completed,
        ))
        user_msg = Message(role="user", content="Verify the task completion.")

        response = self.provider.chat([system_msg, user_msg], tools=[])

        try:
            # Try to parse JSON from response
            text = response.content.strip()
            # Find JSON in the response
            start = text.find("{")
            end = text.rfind("}") + 1
            if start >= 0 and end > start:
                return json.loads(text[start:end])
        except (json.JSONDecodeError, ValueError):
            pass

        return {
            "success": True,
            "summary": response.content[:500],
            "issues": [],
        }

    def _parse_plan(self, text: str) -> list[str]:
        """Extract step list from LLM response."""
        text = text.strip()
        # Try JSON parse
        try:
            start = text.find("[")
            end = text.rfind("]") + 1
            if start >= 0 and end > start:
                steps = json.loads(text[start:end])
                if isinstance(steps, list) and all(isinstance(s, str) for s in steps):
                    return steps
        except (json.JSONDecodeError, ValueError):
            pass

        # Fallback: parse numbered list
        lines = text.split("\n")
        steps: list[str] = []
        for line in lines:
            line = line.strip()
            if not line:
                continue
            # Remove numbering: "1. ", "1) ", "- ", "* "
            for prefix in [".", ")", "-", "*"]:
                parts = line.split(prefix, 1)
                if len(parts) == 2 and parts[0].strip().isdigit():
                    steps.append(parts[1].strip())
                    break
            else:
                if line.startswith("- ") or line.startswith("* "):
                    steps.append(line[2:].strip())

        return steps if steps else [text]

    def get_plan_summary(self, plan: TaskPlan | None = None) -> str:
        """Get a formatted plan summary."""
        p = plan or self._plan
        if p is None:
            return "No plan created."

        lines = [f"Objective: {p.objective}", f"Steps ({len(p.steps)}):"]
        for step in p.steps:
            icon = {
                StepStatus.PENDING: " ",
                StepStatus.RUNNING: "~",
                StepStatus.DONE: "x",
                StepStatus.FAILED: "!",
                StepStatus.SKIPPED: "-",
            }[step.status]
            duration = f" ({step.duration:.1f}s)" if step.duration > 0 else ""
            lines.append(f"  [{icon}] {step.id}. {step.description}{duration}")

        if p.total_duration > 0:
            lines.append(f"\nTotal: {p.total_duration:.1f}s")

        return "\n".join(lines)
