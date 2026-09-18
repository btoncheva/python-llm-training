import os
import json
import anthropic

# Load key from environment — never hardcode
api_key = os.environ.get("ANTHROPIC_API_KEY")

# Create client
client = anthropic.Anthropic(api_key=api_key)

def ask_claude(prompt):
    response = client.messages.create(
        model="claude-sonnet-4-6",
        max_tokens=1024,
        messages=[
            {"role": "user", "content": prompt}
        ]
    )
    # Extract text from response
    return response.content[0].text

# Test it
answer = ask_claude("What are the 3 most important Python concepts for a Java developer to learn?")
print(answer)