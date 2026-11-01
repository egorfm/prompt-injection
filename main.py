#!/usr/bin/env python3
"""
Interactive CLI for the Indirect Prompt Injection Lab.
Demonstrates the attack in a naive agent vs. multi-layer defense in a hardened agent.
"""

import sys
import os
from typing import Dict, Any

from mock_environment import MockEnvironment
from agent import VulnerableAgent, DefendedAgent
from scenarios import SCENARIOS
from config import GEMINI_API_KEY, IS_SIMULATION_MODE, GEMINI_MODEL

# Try importing rich for enhanced UI, fallback to standard colored output
try:
    from rich.console import Console
    from rich.panel import Panel
    from rich.table import Table
    from rich import print as rprint
    HAS_RICH = True
    console = Console()
except ImportError:
    HAS_RICH = False


def print_banner():
    title = """
========================================================================
       🛡️  GEMINI INDIRECT PROMPT INJECTION RESEARCH LAB  🛡️
========================================================================
  Exploring untrusted data vectors, tool hijacking & mitigation layers
========================================================================
"""
    if HAS_RICH:
        console.print(Panel.fit(
            "[bold cyan]🛡️  GEMINI INDIRECT PROMPT INJECTION RESEARCH LAB  🛡️[/bold cyan]\n"
            "[dim]Exploring untrusted data vectors, tool hijacking & mitigation layers[/dim]",
            border_style="cyan"
        ))
    else:
        print(title)

    mode_info = f"Mode: [Real Gemini API ({GEMINI_MODEL})]" if not IS_SIMULATION_MODE else "Mode: [Simulation / Demo Mode (No API key set)]"
    print(mode_info + "\n")


def display_scenario(scenario_key: str):
    sc = SCENARIOS[scenario_key]
    if HAS_RICH:
        table = Table(title="Selected Scenario", show_header=False, border_style="yellow")
        table.add_column("Field", style="bold yellow", width=15)
        table.add_column("Value", style="white")
        table.add_row("Name", sc["name"])
        table.add_row("User Goal", sc["user_goal"])
        table.add_row("Description", sc["description"])
        console.print(table)
    else:
        print(f"--- Scenario: {sc['name']} ---")
        print(f"User Goal: {sc['user_goal']}")
        print(f"Description: {sc['description']}\n")


def print_step(step: Dict[str, Any]):
    stype = step.get("type")

    if HAS_RICH:
        if stype == "thought":
            console.print(f"[dim italic]🤔 {step['text']}[/dim italic]")
        elif stype == "defense":
            console.print(f"[bold blue]🛡️  {step['text']}[/bold blue]")
        elif stype == "tool_call":
            console.print(f"[bold cyan]⚙️  TOOL CALL:[/bold cyan] [green]{step['tool']}[/green] args={step.get('args', {})}")
            if "result" in step:
                console.print(f"   [dim]↳ Result: {step['result']}[/dim]")
        elif stype == "guardrail_blocked":
            console.print(Panel(
                f"[bold red]⛔ {step['reason']}[/bold red]\nTarget Tool: [yellow]{step['tool']}[/yellow]",
                title="[red]GUARDRAIL INTERVENTION[/red]",
                border_style="red"
            ))
        elif stype == "response":
            console.print(Panel(step["text"], title="[green]Assistant Final Output[/green]", border_style="green"))
        elif stype == "warning":
            console.print(f"[yellow]⚠️ {step['text']}[/yellow]")
    else:
        if stype == "thought":
            print(f"  [Thought] {step['text']}")
        elif stype == "defense":
            print(f"  [Defense] {step['text']}")
        elif stype == "tool_call":
            print(f"  [Tool Call] {step['tool']}({step.get('args', {})})")
            if "result" in step:
                print(f"    ↳ Result: {step['result']}")
        elif stype == "guardrail_blocked":
            print(f"\n  ⛔ [BLOCKED BY GUARDRAIL] {step['reason']}\n")
        elif stype == "response":
            print(f"\n--- Assistant Response ---\n{step['text']}\n--------------------------\n")
        elif stype == "warning":
            print(f"  ⚠️ {step['text']}")


def run_experiment(agent_type: str, scenario_key: str):
    env = MockEnvironment()
    scenario = SCENARIOS[scenario_key]
    user_goal = scenario["user_goal"]

    print("\n" + "=" * 65)
    if agent_type == "vulnerable":
        header = "🔴 RUNNING: VULNERABLE AGENT (Naive - No Boundary Enforcement)"
        print(f"\033[1;31m{header}\033[0m" if not HAS_RICH else f"[bold red]{header}[/bold red]")
        agent = VulnerableAgent(env)
    else:
        header = "🟢 RUNNING: DEFENDED AGENT (Hardened - XML Boundaries & Guardrails)"
        print(f"\033[1;32m{header}\033[0m" if not HAS_RICH else f"[bold green]{header}[/bold green]")
        agent = DefendedAgent(env)
    print("=" * 65 + "\n")

    result = agent.run(user_goal)

    for step in result["steps"]:
        print_step(step)

    # Inspect audit log
    print("\n--- Security Audit Report ---")
    if env.audit.security_violations:
        for v in env.audit.security_violations:
            if HAS_RICH:
                console.print(f"[bold red]🚨 VIOLATION DETECTED:[/bold red] {v}")
            else:
                print(f"  🚨 VIOLATION DETECTED: {v}")
        status_msg = "❌ RESULT: System Compromised (Indirect Prompt Injection Succeeded)"
        print(f"\033[1;31m{status_msg}\033[0m" if not HAS_RICH else f"[bold red]{status_msg}[/bold red]")
    else:
        status_msg = "✅ RESULT: Protected (No Unauthorized Data Exfiltration or Tool Abuse)"
        print(f"\033[1;32m{status_msg}\033[0m" if not HAS_RICH else f"[bold green]{status_msg}[/bold green]")
    print("-" * 65 + "\n")


def main():
    print_banner()

    while True:
        print("Select an option:")
        print("1. Run Vulnerable Agent vs. Defended Agent (Side-by-side comparison)")
        print("2. Run Vulnerable Agent only")
        print("3. Run Defended Agent only")
        print("4. Inspect Raw Malicious Payload in Email")
        print("5. Exit")

        choice = input("\nEnter choice (1-5): ").strip()

        if choice == "1":
            display_scenario("exfiltration")
            run_experiment("vulnerable", "exfiltration")
            input("Press [Enter] to run the Defended Agent...")
            run_experiment("defended", "exfiltration")
        elif choice == "2":
            display_scenario("exfiltration")
            run_experiment("vulnerable", "exfiltration")
        elif choice == "3":
            display_scenario("exfiltration")
            run_experiment("defended", "exfiltration")
        elif choice == "4":
            env = MockEnvironment()
            malicious_email = env.emails[2]
            print("\n" + "-" * 60)
            print(f"From: {malicious_email['sender']}")
            print(f"Subject: {malicious_email['subject']}")
            print("Body:")
            print(malicious_email["body"])
            print("-" * 60 + "\n")
        elif choice == "5" or choice.lower() in ["exit", "q", "quit"]:
            print("Exiting lab. Stay secure!")
            break
        else:
            print("Invalid choice, please select 1-5.")


if __name__ == "__main__":
    main()
