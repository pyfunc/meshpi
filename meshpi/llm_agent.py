"""
meshpi.llm_agent
================
LiteLLM-powered NLP agent for Raspberry Pi management.

The agent understands natural language commands and translates them to:
  - config pushes
  - hardware profile applications
  - diagnostic analysis
  - repair command sequences
  - system queries

Supports any LiteLLM-compatible provider:
  LITELLM_MODEL=gpt-4o / claude-3-5-sonnet / ollama/llama3.2 / etc.
"""

from __future__ import annotations

import json
import os
from typing import Any, Callable, Optional

from rich.console import Console
from rich.markdown import Markdown
from rich.panel import Panel
from rich.prompt import Prompt

console = Console()

# Tool definitions for function-calling
TOOLS = [
    {
        "type": "function",
        "function": {
            "name": "get_diagnostics",
            "description": "Fetch full diagnostics from a specific connected RPi client",
            "parameters": {
                "type": "object",
                "properties": {
                    "device_id": {"type": "string", "description": "Device hostname or ID"},
                },
                "required": ["device_id"],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "push_config",
            "description": "Push updated configuration values to one or more RPi clients",
            "parameters": {
                "type": "object",
                "properties": {
                    "device_ids": {
                        "type": "array",
                        "items": {"type": "string"},
                        "description": "List of device IDs to update, or ['*'] for all",
                    },
                    "config_updates": {
                        "type": "object",
                        "description": "Key-value pairs to update in the device config",
                    },
                },
                "required": ["device_ids", "config_updates"],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "apply_hardware_profile",
            "description": "Apply a hardware peripheral profile to an RPi client",
            "parameters": {
                "type": "object",
                "properties": {
                    "device_id":  {"type": "string"},
                    "profile_id": {
                        "type": "string",
                        "description": "Hardware profile ID (e.g. 'oled_ssd1306_i2c', 'sensor_bme280')",
                    },
                },
                "required": ["device_id", "profile_id"],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "run_command",
            "description": "Run a shell command on a specific RPi client via SSH",
            "parameters": {
                "type": "object",
                "properties": {
                    "device_id": {"type": "string"},
                    "command":   {"type": "string", "description": "Shell command to execute"},
                    "timeout":   {"type": "integer", "description": "Timeout in seconds", "default": 30},
                },
                "required": ["device_id", "command"],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "reboot_device",
            "description": "Reboot an RPi client",
            "parameters": {
                "type": "object",
                "properties": {
                    "device_id": {"type": "string"},
                    "delay_secs": {"type": "integer", "default": 5},
                },
                "required": ["device_id"],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "list_devices",
            "description": "List all known MeshPi client devices and their status",
            "parameters": {"type": "object", "properties": {}},
        },
    },
    {
        "type": "function",
        "function": {
            "name": "list_hardware_profiles",
            "description": "List available hardware profiles optionally filtered by category or tag",
            "parameters": {
                "type": "object",
                "properties": {
                    "category": {"type": "string"},
                    "tag":      {"type": "string"},
                },
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "analyze_diagnostics",
            "description": "Analyze diagnostics and return a health assessment with recommendations",
            "parameters": {
                "type": "object",
                "properties": {
                    "device_id": {"type": "string"},
                },
                "required": ["device_id"],
            },
        },
    },
]

SYSTEM_PROMPT = """You are MeshPi Agent, an expert Raspberry Pi fleet management assistant.

You help administrators manage multiple Raspberry Pi devices via natural language.
You have tools to: view diagnostics, push configs, apply hardware profiles, run commands, reboot devices.

Guidelines:
- Always confirm destructive actions (reboot, passwd change) before executing
- When diagnosing issues, fetch diagnostics first, then reason step-by-step
- Suggest the minimal set of changes needed to fix a problem
- When recommending hardware profiles, explain what they install
- Be concise but thorough — operators are technical
- Commands run as the configured RPI_USER via SSH (sudo available)
- Respond in the same language as the user

Available hardware profile categories: display, gpio, sensor, camera, audio, networking, hat, storage
"""


class MeshPiAgent:
    """LiteLLM-backed conversational agent for RPi fleet management."""

    def __init__(
        self,
        tool_executor: Callable[[str, dict], Any],
        model: Optional[str] = None,
        api_base: Optional[str] = None,
    ):
        self.tool_executor = tool_executor
        self.model = model or os.getenv("LITELLM_MODEL", "gpt-4o-mini")
        self.api_base = api_base or os.getenv("LITELLM_API_BASE")
        self.history: list[dict] = []
        self._client = None

    def _get_client(self):
        if self._client is None:
            try:
                import litellm
                self._client = litellm
            except ImportError:
                raise ImportError(
                    "LiteLLM not installed. Run: pip install litellm\n"
                    "Then set LITELLM_MODEL and LITELLM_API_KEY environment variables."
                )
        return self._client

    def chat(self, user_message: str) -> str:
        """Send a message and return the agent's response, executing tools as needed."""
        litellm = self._get_client()

        self.history.append({"role": "user", "content": user_message})

        kwargs: dict = {
            "model": self.model,
            "messages": [{"role": "system", "content": SYSTEM_PROMPT}] + self.history,
            "tools": TOOLS,
            "tool_choice": "auto",
        }
        if self.api_base:
            kwargs["api_base"] = self.api_base

        # Agentic loop
        max_iterations = 8
        for _ in range(max_iterations):
            response = litellm.completion(**kwargs)
            msg = response.choices[0].message

            # Append assistant turn to history
            self.history.append(msg.model_dump() if hasattr(msg, "model_dump") else dict(msg))

            # No tool calls → done
            if not msg.tool_calls:
                return msg.content or ""

            # Execute tool calls
            for tc in msg.tool_calls:
                fn_name = tc.function.name
                try:
                    fn_args = json.loads(tc.function.arguments)
                except json.JSONDecodeError:
                    fn_args = {}

                console.print(f"  [dim cyan]⚙ Tool:[/dim cyan] [bold]{fn_name}[/bold]({json.dumps(fn_args, ensure_ascii=False)[:120]})")

                try:
                    result = self.tool_executor(fn_name, fn_args)
                    result_str = json.dumps(result, ensure_ascii=False, default=str)
                except Exception as exc:
                    result_str = json.dumps({"error": str(exc)})

                self.history.append({
                    "role": "tool",
                    "tool_call_id": tc.id,
                    "content": result_str,
                })

            # Update messages for next iteration
            kwargs["messages"] = [{"role": "system", "content": SYSTEM_PROMPT}] + self.history

        return "Max iterations reached."

    def reset(self) -> None:
        self.history.clear()


# ─────────────────────────────────────────────────────────────────────────────
# Tool executor — wired to real meshpi subsystems
# ─────────────────────────────────────────────────────────────────────────────

def build_tool_executor(ws_manager=None) -> Callable[[str, dict], Any]:
    """
    Build the tool executor function wired to real meshpi subsystems.

    Args:
        ws_manager: Optional WebSocket manager from host.py for pushing commands
    """
    from .registry import registry
    from .diagnostics import format_summary
    from .hardware.profiles import list_profiles, PROFILES

    def execute(fn_name: str, args: dict) -> Any:

        if fn_name == "list_devices":
            devices = registry.all_devices()
            return [
                {
                    "device_id":        d.device_id,
                    "address":          d.address,
                    "online":           d.online,
                    "applied_profiles": d.applied_profiles,
                    "last_seen":        d.last_seen,
                    "notes":            d.notes,
                }
                for d in devices
            ]

        elif fn_name == "get_diagnostics":
            device_id = args["device_id"]
            rec = registry.get(device_id)
            if not rec:
                return {"error": f"Device '{device_id}' not found in registry"}
            return rec.last_diagnostics or {"error": "No diagnostics available yet"}

        elif fn_name == "analyze_diagnostics":
            device_id = args["device_id"]
            rec = registry.get(device_id)
            if not rec or not rec.last_diagnostics:
                return {"error": "No diagnostics data available"}
            return {"summary": format_summary(rec.last_diagnostics)}

        elif fn_name == "list_hardware_profiles":
            profiles = list_profiles(
                category=args.get("category"),
                tag=args.get("tag"),
            )
            return [
                {"id": p.id, "name": p.name, "category": p.category, "description": p.description, "tags": p.tags}
                for p in profiles
            ]

        elif fn_name == "push_config":
            device_ids = args["device_ids"]
            updates = args["config_updates"]
            if ws_manager:
                return ws_manager.push_config_update(device_ids, updates)
            return {"status": "ws_manager not available — config queued"}

        elif fn_name == "apply_hardware_profile":
            if ws_manager:
                return ws_manager.push_command(
                    args["device_id"],
                    {"action": "apply_profile", "profile_id": args["profile_id"]},
                )
            return {"status": "ws_manager not available"}

        elif fn_name == "run_command":
            if ws_manager:
                return ws_manager.push_command(
                    args["device_id"],
                    {"action": "run_command", "command": args["command"], "timeout": args.get("timeout", 30)},
                )
            return {"status": "ws_manager not available"}

        elif fn_name == "reboot_device":
            if ws_manager:
                return ws_manager.push_command(
                    args["device_id"],
                    {"action": "reboot", "delay_secs": args.get("delay_secs", 5)},
                )
            return {"status": "ws_manager not available"}

        return {"error": f"Unknown tool: {fn_name}"}

    return execute


# ─────────────────────────────────────────────────────────────────────────────
# Interactive REPL
# ─────────────────────────────────────────────────────────────────────────────

def run_agent_repl(ws_manager=None) -> None:
    """Launch an interactive NLP shell for managing the RPi fleet."""
    console.print(Panel.fit(
        "[bold cyan]MeshPi LLM Agent[/bold cyan]\n"
        f"Model: [bold]{os.getenv('LITELLM_MODEL', 'gpt-4o-mini')}[/bold]\n"
        "Type your command in natural language. [dim]'exit' or Ctrl+C to quit.[/dim]",
        border_style="cyan",
    ))

    # Check for API key
    if not os.getenv("LITELLM_API_KEY") and not os.getenv("OPENAI_API_KEY") and not os.getenv("ANTHROPIC_API_KEY"):
        console.print("\n[yellow]⚠ No LLM API key found.[/yellow]")
        console.print("Set one of: LITELLM_API_KEY, OPENAI_API_KEY, ANTHROPIC_API_KEY")
        console.print("Or use a local model: [bold]LITELLM_MODEL=ollama/llama3.2 meshpi agent[/bold]\n")

    executor = build_tool_executor(ws_manager)
    agent = MeshPiAgent(tool_executor=executor)

    try:
        while True:
            user_input = Prompt.ask("\n[bold cyan]You[/bold cyan]")
            if user_input.strip().lower() in ("exit", "quit", "q", ":q"):
                break
            if user_input.strip() == "reset":
                agent.reset()
                console.print("[dim]Conversation history cleared.[/dim]")
                continue

            console.print()
            with console.status("[cyan]Thinking…[/cyan]"):
                response = agent.chat(user_input)

            console.print(Panel(
                Markdown(response),
                title="[bold]MeshPi Agent[/bold]",
                border_style="green",
                expand=False,
            ))

    except KeyboardInterrupt:
        pass

    console.print("\n[dim]Agent session ended.[/dim]")
