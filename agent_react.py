import os
import json
import glob
import anthropic

client = anthropic.Anthropic(api_key=os.environ.get("ANTHROPIC_API_KEY"))

# ── tools ──────────────────────────────────────────────────

TOOLS = [
    {
        "name": "list_files",
        "description": "List all .json files in the current directory",
        "input_schema": {"type": "object", "properties": {}}
    },
    {
        "name": "read_file",
        "description": "Read and return the full contents of a file",
        "input_schema": {
            "type": "object",
            "properties": {
                "filename": {"type": "string", "description": "File to read"}
            },
            "required": ["filename"]
        }
    },
    {
        "name": "count_items",
        "description": "Count items in a JSON file. Returns count and top-level keys or array length.",
        "input_schema": {
            "type": "object",
            "properties": {
                "filename": {"type": "string", "description": "JSON file to inspect"}
            },
            "required": ["filename"]
        }
    },
    {
        "name": "find_by_field",
        "description": "Search a JSON array file for items matching a field value",
        "input_schema": {
            "type": "object",
            "properties": {
                "filename": {"type": "string"},
                "field":    {"type": "string", "description": "Field name to search"},
                "value":    {"type": "string", "description": "Value to match"}
            },
            "required": ["filename", "field", "value"]
        }
    },
    {
        "name": "write_report",
        "description": "Write a text report to a file",
        "input_schema": {
            "type": "object",
            "properties": {
                "filename": {"type": "string", "description": "Output filename"},
                "content":  {"type": "string", "description": "Report content"}
            },
            "required": ["filename", "content"]
        }
    }
]

# ── tool implementations ───────────────────────────────────

def list_files():
    return json.dumps(glob.glob("*.json"))

def read_file(filename):
    try:
        with open(filename) as f:
            return f.read()
    except FileNotFoundError:
        return f"Error: '{filename}' not found"

def count_items(filename):
    try:
        with open(filename) as f:
            data = json.load(f)
        if isinstance(data, list):
            sample = data[0] if data else {}
            keys = list(sample.keys()) if isinstance(sample, dict) else []
            return json.dumps({
                "type": "array",
                "count": len(data),
                "fields": keys
            })
        elif isinstance(data, dict):
            return json.dumps({
                "type": "object",
                "keys": list(data.keys())
            })
    except Exception as e:
        return f"Error: {e}"

def find_by_field(filename, field, value):
    try:
        with open(filename) as f:
            data = json.load(f)
        if isinstance(data, list):
            matches = [i for i in data if str(i.get(field, "")).lower() == value.lower()]
            return json.dumps(matches)
        return "File is not a JSON array"
    except Exception as e:
        return f"Error: {e}"

def write_report(filename, content):
    with open(filename, "w") as f:
        f.write(content)
    return f"Report written to {filename}"

def run_tool(name, inputs):
    print(f"  [tool] {name}({json.dumps(inputs)})")
    if name == "list_files":   return list_files()
    if name == "read_file":    return read_file(**inputs)
    if name == "count_items":  return count_items(**inputs)
    if name == "find_by_field":return find_by_field(**inputs)
    if name == "write_report": return write_report(**inputs)
    return f"Unknown tool: {name}"

# ── ReAct loop ─────────────────────────────────────────────

SYSTEM = """You are a QA data analyst with access to tools.
When given a goal, reason step by step:
- First understand what data is available
- Then gather the information you need
- Then analyze and draw conclusions
- Finally write a report summarizing your findings

Think out loud — explain what you are doing and why before each tool call."""

def run_react_agent(goal, max_steps=15):
    print(f"\nGoal: {goal}")
    print("=" * 50)

    messages = [{"role": "user", "content": goal}]
    step = 0

    while step < max_steps:
        step += 1
        print(f"\n[step {step}]")

        response = client.messages.create(
            model="claude-sonnet-4-6",
            max_tokens=2048,
            system=SYSTEM,
            tools=TOOLS,
            messages=messages
        )

        # Print Claude's reasoning text as it thinks
        for block in response.content:
            if hasattr(block, "text") and block.text:
                print(f"  Reasoning: {block.text[:200]}...")

        if response.stop_reason == "end_turn":
            final = next(
                (b.text for b in response.content if hasattr(b, "text")),
                "Done."
            )
            print(f"\n{'=' * 50}")
            print("FINAL ANSWER:")
            print(final)
            return final

        elif response.stop_reason == "tool_use":
            messages.append({
                "role": "assistant",
                "content": response.content
            })

            tool_results = []
            for block in response.content:
                if block.type == "tool_use":
                    result = run_tool(block.name, block.input)
                    tool_results.append({
                        "type": "tool_result",
                        "tool_use_id": block.id,
                        "content": str(result)
                    })

            messages.append({
                "role": "user",
                "content": tool_results
            })

    print("Max steps reached")
    return None

# ── run it ─────────────────────────────────────────────────

run_react_agent(
    "Analyze all the JSON files in this directory. "
    "For each file understand its structure and contents. "
    "Then find any high priority or critical items across all files. "
    "Write a summary report to analysis_report.txt."
)