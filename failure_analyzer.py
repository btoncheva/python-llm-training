import os
import json
import anthropic

client = anthropic.Anthropic(api_key=os.environ.get("ANTHROPIC_API_KEY"))

SYSTEM = """You are a senior QA automation engineer specializing in test failure analysis.
Given a test failure report, identify patterns, root causes, and recommended actions.
Respond ONLY with valid JSON. No markdown. No extra text.

Output format:
{
    "summary": "one sentence overview of the failure pattern",
    "total_failures": number,
    "failure_patterns": [
        {
            "pattern": "pattern name",
            "affected_tests": ["test1", "test2"],
            "likely_cause": "explanation",
            "recommended_action": "what to do"
        }
    ],
    "priority_fix": "the single most important thing to fix first",
    "environment_issue": true or false
}"""

def analyze_failures(test_report):
    response = client.messages.create(
        model="claude-sonnet-4-6",
        max_tokens=2048,
        system=SYSTEM,
        messages=[{
            "role": "user",
            "content": f"Analyze these test failures:\n\n{json.dumps(test_report, indent=2)}"
        }]
    )
    return json.loads(response.content[0].text)

# Simulated test report — in real life this comes from your test framework
test_report = {
    "run_id": "RUN-2024-001",
    "environment": "staging",
    "total_tests": 120,
    "failures": [
        {
            "test": "test_login_valid_credentials",
            "error": "TimeoutException: element not found after 30s",
            "module": "authentication"
        },
        {
            "test": "test_login_remember_me",
            "error": "TimeoutException: element not found after 30s",
            "module": "authentication"
        },
        {
            "test": "test_payment_visa",
            "error": "AssertionError: expected 200 got 503",
            "module": "payment"
        },
        {
            "test": "test_payment_mastercard",
            "error": "AssertionError: expected 200 got 503",
            "module": "payment"
        },
        {
            "test": "test_payment_amex",
            "error": "AssertionError: expected 200 got 503",
            "module": "payment"
        },
        {
            "test": "test_user_profile_update",
            "error": "AssertionError: expected 'John' got 'null'",
            "module": "profile"
        }
    ]
}

analysis = analyze_failures(test_report)

# Save full analysis
with open("failure_analysis.json", "w") as f:
    json.dump(analysis, f, indent=2)

# Print actionable summary
print(f"Summary: {analysis['summary']}")
print(f"Environment issue: {analysis['environment_issue']}")
print(f"Priority fix: {analysis['priority_fix']}")
print(f"\nFailure patterns found: {len(analysis['failure_patterns'])}")

for pattern in analysis['failure_patterns']:
    print(f"\n  Pattern : {pattern['pattern']}")
    print(f"  Cause   : {pattern['likely_cause']}")
    print(f"  Action  : {pattern['recommended_action']}")
    print(f"  Tests   : {', '.join(pattern['affected_tests'])}")