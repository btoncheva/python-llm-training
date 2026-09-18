import os
import json
import anthropic

client = anthropic.Anthropic(api_key=os.environ.get("ANTHROPIC_API_KEY"))

def ask_claude(prompt):
    response = client.messages.create(
        model="claude-sonnet-4-6",
        max_tokens=512,
        messages=[
            {"role": "user", "content": prompt}
        ]
    )
    return response.content[0].text

def load_prompts(filename):
    with open(filename, "r") as f:
        return json.load(f)

def save_results(results, filename):
    with open(filename, "w") as f:
        json.dump(results, f, indent=2)
    print(f"Saved {len(results)} results to {filename}")

# Load prompts
prompts = load_prompts("prompts.json")

results = []
for item in prompts:
    print(f"Asking: {item['prompt'][:50]}...")
    answer = ask_claude(item["prompt"])
    results.append({
        "id": item["id"],
        "prompt": item["prompt"],
        "response": answer
    })

save_results(results, "results.json")