import os
import json
import time
import anthropic

client = anthropic.Anthropic(api_key=os.environ.get("ANTHROPIC_API_KEY"))

SYSTEM = """You are a QA automation expert.
Analyze each bug and respond ONLY with a JSON object, no markdown, no extra text:
{
    "root_cause": "brief root cause",
    "severity": "low|medium|high|critical",
    "test_cases": ["test case 1", "test case 2", "test case 3"]
}"""

def analyze_bug(description):
    try:
        response = client.messages.create(
            model="claude-sonnet-4-6",
            max_tokens=1024,
            system=SYSTEM,
            messages=[{"role": "user", "content": description}]
        )
        return json.loads(response.content[0].text)
    except json.JSONDecodeError:
        print(f"Invalid JSON response for: {description[:50]}")
        return None
    except anthropic.APIError as e:
        print(f"API error: {e}")
        return None

# Bug reports to analyze
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
    time.sleep(0.5)  # small delay between calls — good practice

# Save results
with open("bug_analysis.json", "w") as f:
    json.dump(results, f, indent=2)

print(f"\nAnalyzed {len(results)} bugs. Results saved to bug_analysis.json")

# Print summary
for r in results:
    a = r["analysis"]
    print(f"\n{r['id']} [{a['severity'].upper()}]")
    print(f"  Root cause: {a['root_cause']}")
    print(f"  Test cases: {len(a['test_cases'])}")