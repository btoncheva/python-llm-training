import os
import json
import anthropic

client = anthropic.Anthropic(api_key=os.environ.get("ANTHROPIC_API_KEY"))

# ── specialist agents ──────────────────────────────────────
# Each agent is just a function that calls Claude
# with a focused system prompt. That's it.

def parse_json(text):
    text = text.strip()
    if text.startswith("```"):
        text = text.split("```")[1]
        if text.startswith("json"):
            text = text[4:]
    return json.loads(text.strip())

def planner_agent(feature_description):
    """Breaks a feature into a structured test plan."""
    print("  [planner] analyzing feature...")
    response = client.messages.create(
        model="claude-sonnet-4-6",
        max_tokens=1024,
        system="""You are a QA test planner. 
Given a feature description, produce a structured test plan.
Respond ONLY with valid JSON, no markdown:
{
  "feature": "name",
  "risk_areas": ["area1", "area2"],
  "test_types_needed": ["positive", "negative", "edge_case", "security"],
  "priority": "high|medium|low",
  "estimated_cases": number
}""",
        messages=[{"role": "user", "content": feature_description}]
    )
    return parse_json(response.content[0].text)


def generator_agent(feature_description, plan):
    """Generates test cases based on the plan."""
    print("  [generator] creating test cases...")
    response = client.messages.create(
        model="claude-sonnet-4-6",
        max_tokens=4096,
        system="""You are a QA test case writer.
Given a feature and test plan, write detailed test cases.
Respond ONLY with valid JSON, no markdown:
{
  "test_cases": [
    {
      "id": "TC-001",
      "title": "title",
      "type": "positive|negative|edge_case|security",
      "priority": "high|medium|low",
      "steps": ["step1", "step2"],
      "expected_result": "what should happen"
    }
  ]
}""",
       messages=[{
    "role": "user",
    "content": f"Feature:\n{feature_description}\n\nPlan:\n{json.dumps(plan, indent=2)}\n\nGenerate maximum 8 test cases, prioritising the highest risk ones."
}]
    )
    return parse_json(response.content[0].text)


def reviewer_agent(test_cases, feature_description):
    """Reviews test cases for quality and coverage gaps."""
    print("  [reviewer] reviewing quality...")
    response = client.messages.create(
        model="claude-sonnet-4-6",
        max_tokens=1024,
        system="""You are a senior QA reviewer.
Review test cases for quality, coverage, and gaps.
Respond ONLY with valid JSON, no markdown:
{
  "verdict": "approved|needs_improvement",
  "coverage_score": 0-100,
  "issues": ["issue1", "issue2"],
  "missing_scenarios": ["scenario1", "scenario2"],
  "approved_cases": ["TC-001", "TC-002"]
}""",
        messages=[{
            "role": "user",
            "content": f"Feature:\n{feature_description}\n\nTest cases:\n{json.dumps(test_cases, indent=2)}"
        }]
    )
    return parse_json(response.content[0].text)


def reporter_agent(plan, test_cases, review):
    """Formats everything into a final human-readable report."""
    print("  [reporter] generating report...")
    response = client.messages.create(
        model="claude-sonnet-4-6",
        max_tokens=1024,
        system="""You are a QA report writer.
Summarize the test planning output into a clear, concise report.
Use plain text, no markdown. Keep it under 300 words.
Structure: Summary → Coverage → Key risks → Recommendations""",
        messages=[{
            "role": "user",
            "content": f"""Plan: {json.dumps(plan, indent=2)}
Test cases: {len(test_cases.get('test_cases', []))} generated
Review: {json.dumps(review, indent=2)}"""
        }]
    )
    return response.content[0].text


# ── orchestrator ───────────────────────────────────────────
# The orchestrator knows the full picture and decides
# what to delegate and in what order.

def orchestrator(feature_description):
    print(f"\nOrchestrator: starting pipeline")
    print(f"Feature: {feature_description[:60]}...")
    print("=" * 50)

    # Step 1 — delegate to planner
    print("\n[1/4] Delegating to planner agent...")
    plan = planner_agent(feature_description)
    print(f"  Plan: {plan['estimated_cases']} cases needed, priority={plan['priority']}")

    # Step 2 — delegate to generator with plan context
    print("\n[2/4] Delegating to generator agent...")
    test_cases = generator_agent(feature_description, plan)
    count = len(test_cases.get("test_cases", []))
    print(f"  Generated: {count} test cases")

    # Step 3 — delegate to reviewer
    print("\n[3/4] Delegating to reviewer agent...")
    review = reviewer_agent(test_cases, feature_description)
    print(f"  Verdict: {review['verdict']}, coverage: {review['coverage_score']}%")

    # Orchestrator decision — if review fails, regenerate once
    if review["verdict"] == "needs_improvement" and review["missing_scenarios"]:
        print("\n  Orchestrator: review flagged gaps, requesting additional cases...")
        extra_prompt = (
            f"{feature_description}\n\n"
            f"Also cover these missing scenarios:\n"
            + "\n".join(f"- {s}" for s in review["missing_scenarios"])
        )
        extra_cases = generator_agent(extra_prompt, plan)
        # Merge extra cases into main set
        test_cases["test_cases"].extend(extra_cases.get("test_cases", []))
        print(f"  Added {len(extra_cases.get('test_cases', []))} extra cases")

    # Step 4 — delegate to reporter
    print("\n[4/4] Delegating to reporter agent...")
    report = reporter_agent(plan, test_cases, review)

    # Orchestrator synthesizes final output
    final_output = {
        "feature":     feature_description[:80],
        "plan":        plan,
        "test_cases":  test_cases,
        "review":      review,
        "report":      report
    }

    # Save everything
    with open("multi_agent_output.json", "w") as f:
        json.dump(final_output, f, indent=2)

    with open("multi_agent_report.txt", "w") as f:
        f.write(report)

    print("\n" + "=" * 50)
    print("PIPELINE COMPLETE")
    print("=" * 50)
    print(f"Test cases  : {len(test_cases.get('test_cases', []))}")
    print(f"Coverage    : {review['coverage_score']}%")
    print(f"Verdict     : {review['verdict']}")
    print(f"\nReport:\n{report}")

    return final_output


# ── run it ─────────────────────────────────────────────────

orchestrator("""
Password reset flow:
User requests reset via email. System sends a time-limited token (expires in 1 hour).
User clicks link, enters new password. Password must meet complexity requirements.
Token is single-use and invalidated after use. 
Expired or already-used tokens show an appropriate error.
""")