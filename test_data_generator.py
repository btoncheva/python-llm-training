import os
import json
import anthropic

client = anthropic.Anthropic(api_key=os.environ.get("ANTHROPIC_API_KEY"))

SYSTEM = """You are a QA test data specialist.
Generate realistic, diverse test data based on the schema provided.
Respond ONLY with a valid JSON array. No markdown. No extra text.
Include edge cases and boundary values naturally in the dataset."""

def generate_test_data(schema_description, count=5):
    response = client.messages.create(
        model="claude-sonnet-4-6",
        max_tokens=2048,
        system=SYSTEM,
        messages=[{
            "role": "user",
            "content": f"Generate {count} test records for:\n\n{schema_description}"
        }]
    )
    return json.loads(response.content[0].text)

# Define what data you need
schema = """
User registration form with these fields:
- email: valid and invalid formats, include boundary cases
- password: mix of valid and invalid (too short, missing special chars, etc)
- age: integer, include boundary values (17, 18, 99, 100, 0, negative)
- username: alphanumeric, 3-20 chars, include edge cases
- expected_valid: boolean — whether this record should pass validation
"""

data = generate_test_data(schema, count=8)

with open("test_data.json", "w") as f:
    json.dump(data, f, indent=2)

print(f"Generated {len(data)} test records\n")

valid_count = sum(1 for r in data if r.get("expected_valid"))
invalid_count = len(data) - valid_count

print(f"Valid records   : {valid_count}")
print(f"Invalid records : {invalid_count}")
print("\nSample records:")
for record in data[:8]:
    status = "✓ valid" if record.get("expected_valid") else "✗ invalid"
    print(f"  {status} — {record.get('email')} / age: {record.get('age')}")