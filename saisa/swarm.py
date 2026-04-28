"""Cognitive Swarm — multi-agent framework for parallel task execution.

Lightweight implementation: agents are specialized prompt prefixes
that run on the same LLM provider, not separate processes.
This keeps it fast and doesn't kill the computer.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any

from .providers.base import LLMProvider, Message


@dataclass
class AgentRole:
    name: str
    specialty: str
    system_prompt: str
    tools_filter: list[str] | None = None  # restrict to subset of tools


# ── Pre-defined agent roles ─────────────────────────────────────────────

DEVELOPER = AgentRole(
    name="Developer",
    specialty="Code generation, architecture, debugging, testing",
    system_prompt="""You are a Senior Developer Agent. Your role:
- Write clean, production-ready code
- Follow best practices and design patterns
- Generate tests alongside code
- Explain architectural decisions concisely
Focus on code quality, performance, and maintainability.""",
)

DEVOPS = AgentRole(
    name="DevOps",
    specialty="Deployment, CI/CD, Docker, infrastructure",
    system_prompt="""You are a DevOps Agent. Your role:
- Configure Docker, Kubernetes, CI/CD pipelines
- Write Dockerfiles, docker-compose, GitHub Actions
- Set up monitoring and logging
- Optimize build and deploy processes
Focus on reliability, automation, and infrastructure-as-code.""",
)

SECURITY = AgentRole(
    name="Security",
    specialty="Vulnerability scanning, security best practices",
    system_prompt="""You are a Security Agent. Your role:
- Review code for security vulnerabilities
- Check for exposed secrets, SQL injection, XSS, CSRF
- Suggest secure coding patterns
- Review dependency vulnerabilities
Focus on defense-in-depth and zero-trust principles.""",
)

ARCHITECT = AgentRole(
    name="Architect",
    specialty="System design, technology selection, scalability",
    system_prompt="""You are a Software Architect Agent. Your role:
- Design system architecture and data models
- Choose appropriate technologies and patterns
- Plan for scalability and maintainability
- Create technical specifications
Focus on clean architecture, SOLID principles, and pragmatic design.""",
)

REVIEWER = AgentRole(
    name="Reviewer",
    specialty="Code review, quality assurance, best practices",
    system_prompt="""You are a Code Review Agent. Your role:
- Review code for bugs, edge cases, and logic errors
- Check for code style and convention consistency
- Suggest improvements and optimizations
- Verify test coverage and quality
Be constructive but thorough. Flag issues by severity.""",
)

AVAILABLE_AGENTS: dict[str, AgentRole] = {
    "developer": DEVELOPER,
    "devops": DEVOPS,
    "security": SECURITY,
    "architect": ARCHITECT,
    "reviewer": REVIEWER,
}


class SwarmOrchestrator:
    """Orchestrates multiple specialized agents on a single LLM provider."""

    def __init__(self, provider: LLMProvider) -> None:
        self.provider = provider
        self._results: list[dict[str, Any]] = []

    def run_agent(
        self,
        role: AgentRole,
        task: str,
        context: str = "",
    ) -> str:
        """Run a single specialized agent on a task."""
        system_msg = Message(role="system", content=role.system_prompt)
        user_content = f"Task: {task}"
        if context:
            user_content += f"\n\nContext:\n{context}"
        user_msg = Message(role="user", content=user_content)

        response = self.provider.chat([system_msg, user_msg], tools=[])

        result = {
            "agent": role.name,
            "task": task,
            "response": response.content,
        }
        self._results.append(result)
        return response.content

    def run_swarm(
        self,
        task: str,
        agents: list[str] | None = None,
        context: str = "",
    ) -> list[dict[str, Any]]:
        """Run multiple agents sequentially on related aspects of a task.

        Each agent gets the previous agents' outputs as context.
        """
        agent_names = agents or ["architect", "developer", "security"]
        results: list[dict[str, Any]] = []
        accumulated_context = context

        for agent_name in agent_names:
            role = AVAILABLE_AGENTS.get(agent_name)
            if role is None:
                results.append({"agent": agent_name, "error": "Unknown agent"})
                continue

            output = self.run_agent(role, task, accumulated_context)
            results.append({
                "agent": role.name,
                "specialty": role.specialty,
                "response": output,
            })
            accumulated_context += f"\n\n--- {role.name} Agent Output ---\n{output}"

        return results

    def list_agents(self) -> list[dict[str, str]]:
        """List available agents."""
        return [
            {"name": role.name, "specialty": role.specialty}
            for role in AVAILABLE_AGENTS.values()
        ]
