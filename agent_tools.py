import os
import json
import anthropic

client = anthropic.Anthropic(api_key=os.environ.get("ANTHROPIC_API_KEY"))

# ── tool definitions ───────────────────────────────────────
# These are descriptions Claude reads to decide which tool to call.
# Think of them as the interface, not the implementation.

TOOLS = [
    {
        "name": "read_file",
        "description": "Read the contents of a file by filename",
        "input_schema": {
            "type": "object",
            "properties": {
                "filename": {
                    "type": "string",
                    "description": "The name of the file to read"
                }
            },
            "required": ["filename"]
        }
    },
    {
        "name": "list_files",
        "description": "List all .json files in the current directory",
        "input_schema": {
            "type": "object",
            "properties": {}
        }
    },
    {
        "name": "summarize_json",
        "description": "Count items in a JSON file and return a summary",
        "input_schema": {
            "type": "object",
            "properties": {
                "filename": {
                    "type": "string",
                    "description": "The JSON file to summarize"
                }
            },
            "required": ["filename"]
        }
    }
]

# ── tool implementations ───────────────────────────────────
# The actual Python functions that run when Claude calls a tool.

def read_file(filename):
    try:
        with open(filename, "r") as f:
            return f.read()
    except FileNotFoundError:
        return f"Error: file '{filename}' not found"

def list_files():
    import glob
    files = glob.glob("*.json")
    return json.dumps(files)

def summarize_json(filename):
    try:
        with open(filename, "r") as f:
            data = json.load(f)
        if isinstance(data, list):
            return f"{filename} contains {len(data)} items"
        elif isinstance(data, dict):
            return f"{filename} contains keys: {list(data.keys())}"
    except Exception as e:
        return f"Error reading {filename}: {e}"

# ── tool router ────────────────────────────────────────────
# Maps tool names to their implementations.

def run_tool(tool_name, tool_input):
    print(f"  [tool] {tool_name}({tool_input})")
    if tool_name == "read_file":
        return read_file(**tool_input)
    elif tool_name == "list_files":
        return list_files()
    elif tool_name == "summarize_json":
        return summarize_json(**tool_input)
    else:
        return f"Unknown tool: {tool_name}"

# ── agent loop ─────────────────────────────────────────────
# This is the core of tool use — keep calling Claude until
# it stops requesting tools and returns a final answer.

def run_agent(user_message):
    print(f"\nUser: {user_message}")
    print("-" * 40)

    messages = [{"role": "user", "content": user_message}]

    while True:
        response = client.messages.create(
            model="claude-sonnet-4-6",
            max_tokens=1024,
            tools=TOOLS,
            messages=messages
        )

        # Check why Claude stopped
        if response.stop_reason == "end_turn":
            # Claude is done — extract final text response
            final = next(b.text for b in response.content if b.type == "text")
            print(f"\nClaude: {final}")
            return final

        elif response.stop_reason == "tool_use":
            # Claude wants to call a tool
            # Add Claude's response to history
            messages.append({
                "role": "assistant",
                "content": response.content
            })

            # Execute each tool Claude requested
            tool_results = []
            for block in response.content:
                if block.type == "tool_use":
                    result = run_tool(block.name, block.input)
                    tool_results.append({
                        "type": "tool_result",
                        "tool_use_id": block.id,
                        "content": str(result)
                    })

            # Add tool results back to history
            messages.append({
                "role": "user",
                "content": tool_results
            })
            # Loop continues — Claude will process results
            # and either call more tools or give final answer

# ── test it ────────────────────────────────────────────────

run_agent("What JSON files do I have and how many items are in each one?")