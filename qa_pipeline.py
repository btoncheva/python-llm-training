import os
import json
import time
import anthropic
from datetime import datetime

client = anthropic.Anthropic(api_key=os.environ.get("ANTHROPIC_API_KEY"))

# ── helpers ────────────────────────────────────────────────

def call_claude(system, user_message, max_tokens=2048):
    for attempt in range(3):
        try:
            response = client.messages.create(
                model="claude-sonnet-4-6",
                max_tokens=max_tokens,
                system=system,
                messages=[{"role": "user", "content": user_message}]
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

def save(data, filename):
    with open(filename, "w") as f:
        json.dump(data, f, indent=2)
    print(f"  Saved → {filename}")

# ── step 1: generate test cases ────────────────────────────

def generate_test_cases(feature):
    print("\n[1/3] Generating test cases...")
    result = call_claude(
        system="""You are a senior QA engineer. Generate test cases for the feature provided.
Respond ONLY with valid JSON, no markdown, no extra text:
{
  "feature": "feature name",
  "test_suite": [
    {
      "id": "TC-001",
      "title": "test title",
      "type": "positive|negative|edge_case|security",
      "priority": "high|medium|low",
      "steps": ["step 1", "step 2"],
      "expected_result": "what should happen"
    }
  ]
}""",
        user_message=f"Generate 6 test cases for:\n\n{feature}"
    )
    if result:
        save(result, "test_suite.json")
    return result

# ── step 2: generate test data ─────────────────────────────

def generate_test_data(feature):
    print("\n[2/3] Generating test data...")
    result = call_claude(
        system="""You are a QA test data specialist.
Generate realistic test data including edge cases and boundary values.
Respond ONLY with a valid JSON array, no markdown, no extra text.""",
        user_message=f"Generate 6 test data records for:\n\n{feature}"
    )
    if result:
        save(result, "test_data.json")
    return result

# ── step 3: analyze failures ───────────────────────────────

def analyze_failures(test_suite, test_data):
    print("\n[3/3] Analyzing potential failures...")

    # Simulate some failures based on generated test cases
    simulated_failures = []
    if test_suite:
        for i, tc in enumerate(test_suite.get("test_suite", [])[:3]):
            if tc.get("type") in ["negative", "edge_case", "security"]:
                simulated_failures.append({
                    "test": tc["id"],
                    "title": tc["title"],
                    "error": "AssertionError: actual result did not match expected",
                    "type": tc["type"]
                })

    if not simulated_failures:
        print("  No failures to analyze.")
        return None

    result = call_claude(
        system="""You are a senior QA engineer analyzing test failures.
Respond ONLY with valid JSON, no markdown, no extra text:
{
  "summary": "one sentence overview",
  "failure_patterns": [
    {
      "pattern": "pattern name",
      "affected_tests": ["TC-001"],
      "likely_cause": "explanation",
      "recommended_action": "what to fix"
    }
  ],
  "priority_fix": "most important fix",
  "environment_issue": true or false
}""",
        user_message=f"Analyze these test failures:\n\n{json.dumps(simulated_failures, indent=2)}"
    )
    if result:
        save(result, "failure_analysis.json")
    return result

# ── final report ───────────────────────────────────────────

def generate_report(feature, test_suite, test_data, failure_analysis):
    tc_count = len(test_suite.get("test_suite", [])) if test_suite else 0
    td_count = len(test_data) if test_data else 0
    fp_count = len(failure_analysis.get("failure_patterns", [])) if failure_analysis else 0

    report = {
        "generated_at": datetime.now().isoformat(),
        "feature": feature[:80],
        "summary": {
            "test_cases_generated": tc_count,
            "test_data_records": td_count,
            "failure_patterns_found": fp_count,
        },
        "files": [
            "test_suite.json",
            "test_data.json",
            "failure_analysis.json"
        ]
    }
    save(report, "pipeline_report.json")
    return report

# ── main ───────────────────────────────────────────────────

FEATURE = """
User Login Flow:
Users log in with email and password.
After 5 failed attempts the account is locked for 15 minutes.
Passwords are case-sensitive.
Session expires after 30 minutes of inactivity.
Remember Me option extends session to 7 days.
"""

print("=" * 50)
print("QA PIPELINE STARTING")
print("=" * 50)

test_suite      = generate_test_cases(FEATURE)
test_data       = generate_test_data(FEATURE)
failure_analysis = analyze_failures(test_suite, test_data)
report          = generate_report(FEATURE, test_suite, test_data, failure_analysis)

print("\n" + "=" * 50)
print("PIPELINE COMPLETE")
print("=" * 50)
print(f"Test cases   : {report['summary']['test_cases_generated']}")
print(f"Test data    : {report['summary']['test_data_records']}")
print(f"Failure patterns : {report['summary']['failure_patterns_found']}")
print("\nOutput files:")
for f in report["files"]:
    print(f"  → {f}")