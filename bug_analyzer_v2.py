import os
import json
import time
import anthropic

client = anthropic.Anthropic(api_key=os.environ.get("ANTHROPIC_API_KEY"))

SYSTEM = """You are a senior QA automation expert.

Analyze bug descriptions with careful reasoning. Respond ONLY with a valid JSON object.
No markdown. No code fences. No extra text before or after the JSON.

Example input:
"Dropdown menu does not close when clicking outside of it"

Example output:
{
    "reasoning": "Click-outside detection is missing, common in custom UI components",
    "root_cause": "Missing event listener for click-outside detection",
    "severity": "low",
    "affected_area": "ui-components",
    "test_cases": [
        "Click outside dropdown and verify it closes",
        "Open dropdown, click another element, verify dropdown closes",
        "Verify dropdown closes on Escape key press"
    ]
}

Now analyze the bug provided by the user using the exact same format."""

def analyze_bug(description, retries=3):
    for attempt in range(retries):
        try:
            response = client.messages.create(
                model="claude-sonnet-4-6",
                max_tokens=1024,
                system=SYSTEM,
                messages=[{"role": "user", "content": description}]
            )
            return json.loads(response.content[0].text)

        except json.JSONDecodeError:
            print(f"  Invalid JSON on attempt {attempt + 1}, retrying...")
            time.sleep(1)

        except anthropic.RateLimitError:
            wait = 2 ** attempt
            print(f"  Rate limited, waiting {wait}s...")
            time.sleep(wait)

        except anthropic.APIError as e:
            print(f"  API error: {e}")
            return None

    return None

bugs = [
    {"id": "BUG-101", "description": "Login button unresponsive after session timeout on mobile Safari"},
    {"id": "BUG-102", "description": "Payment form accepts expired credit cards without validation"},
    {"id": "BUG-103", "description": "Search results not updating when filter is changed rapidly"},
]

results = []
for bug in bugs:
    print(f"Analyzing {bug['id']}...")
    analysis = analyze_bug(bug["description"])
    if analysis:
        results.append({
            "id": bug["id"],
            "description": bug["description"],
            "analysis": analysis
        })
        print(f"  [{analysis['severity'].upper()}] {analysis['affected_area']}")
    time.sleep(0.5)

with open("bug_analysis_v2.json", "w") as f:
    json.dump(results, f, indent=2)

print(f"\nDone. {len(results)}/{len(bugs)} bugs analyzed.")