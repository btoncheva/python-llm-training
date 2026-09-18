import os
import json
import anthropic

client = anthropic.Anthropic(api_key=os.environ.get("ANTHROPIC_API_KEY"))

SYSTEM = """You are a senior QA automation engineer.
Given a feature description, generate comprehensive test cases.
Respond ONLY with a valid JSON object. No markdown. No extra text.

Example output:
{
    "feature": "feature name",
    "test_suite": [
        {
            "id": "TC-001",
            "title": "Verify successful login with valid credentials",
            "type": "positive",
            "priority": "high",
            "steps": [
                "Navigate to login page",
                "Enter valid username and password",
                "Click login button"
            ],
            "expected_result": "User is redirected to dashboard"
        }
    ]
}

Types: positive, negative, edge_case, security, performance
Priorities: high, medium, low"""

def generate_test_cases(feature_description, count=6):
    response = client.messages.create(
        model="claude-sonnet-4-6",
        max_tokens=2048,
        system=SYSTEM,
        messages=[{
            "role": "user",
            "content": f"Generate {count} test cases for this feature:\n\n{feature_description}"
        }]
    )
    return json.loads(response.content[0].text)

# Feature description — like what a PM would write
feature = """
User Registration Flow:
Users can register with email and password.
Email must be unique and valid format.
Password must be minimum 8 characters, contain one uppercase,
one number, and one special character.
After registration, user receives a confirmation email.
Account is inactive until email is confirmed.
"""

result = generate_test_cases(feature, count=8)

# Save to file
with open("test_suite.json", "w") as f:
    json.dump(result, f, indent=2)

# Print summary
print(f"Feature: {result['feature']}")
print(f"Generated {len(result['test_suite'])} test cases\n")

for tc in result['test_suite']:
    print(f"[{tc['priority'].upper()}] {tc['id']} — {tc['title']}")
    print(f"  Type: {tc['type']}")
    print(f"  Expected: {tc['expected_result']}")
    print()