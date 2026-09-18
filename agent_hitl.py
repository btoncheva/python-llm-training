import os
import json
import anthropic
from datetime import datetime

client = anthropic.Anthropic(api_key=os.environ.get("ANTHROPIC_API_KEY"))


def parse_json(text):
    text = text.strip()
    if text.startswith("```"):
        text = text.split("```")[1]
        if text.startswith("json"):
            text = text[4:]
    text = text.strip()
    try:
        return json.loads(text)
    except json.JSONDecodeError as e:
        print(f"  JSON parse error: {e}")
        print(f"  Raw response (first 200 chars): {text[:200]}")
        raise

# ── human checkpoint ───────────────────────────────────────
# This is the core of the pattern.
# Agent pauses, shows what it's about to do, waits for approval.

def human_checkpoint(action, details, risk_level="medium"):
    print(f"\n{'='*50}")
    print(f"HUMAN APPROVAL REQUIRED [{risk_level.upper()} RISK]")
    print(f"{'='*50}")
    print(f"Action  : {action}")
    print(f"Details : {json.dumps(details, indent=2) if isinstance(details, dict) else details}")
    print(f"{'='*50}")

    while True:
        choice = input("Approve? [y]es / [n]o / [m]odify: ").strip().lower()
        if choice in ("y", "yes"):
            print("  Approved. Continuing...")
            return {"approved": True, "modified": False, "feedback": None}
        elif choice in ("n", "no"):
            reason = input("  Reason for rejection: ").strip()
            print("  Rejected. Agent will adjust.")
            return {"approved": False, "modified": False, "feedback": reason}
        elif choice in ("m", "modify"):
            feedback = input("  Enter your modification or feedback: ").strip()
            print("  Modification noted. Agent will adjust.")
            return {"approved": True, "modified": True, "feedback": feedback}
        else:
            print("  Please enter y, n, or m")


# ── confidence checker ─────────────────────────────────────
# Ask Claude to rate its own confidence before proceeding.

def check_confidence(task, result):
    response = client.messages.create(
        model="claude-sonnet-4-6",
        max_tokens=256,
        system="""You are a QA agent evaluating your own output confidence.
Respond ONLY with valid JSON, no markdown:
{
  "confidence": 0-100,
  "concerns": ["concern1"],
  "needs_human_review": true|false
}""",
        messages=[{
            "role": "user",
            "content": f"Task: {task}\n\nMy output:\n{json.dumps(result, indent=2)}\n\nHow confident am I in this output?"
        }]
    )
    return parse_json(response.content[0].text)


# ── specialist agents ──────────────────────────────────────

def analyze_requirements(feature):
    print("  [agent] analyzing requirements...")
    response = client.messages.create(
        model="claude-sonnet-4-6",
        max_tokens=2048,
        system="""You are a QA requirements analyst.
Analyze the feature and identify testable requirements.
Respond ONLY with valid JSON, no markdown:
{
  "requirements": [
    {
      "id": "REQ-001",
      "description": "requirement text",
      "testable": true|false,
      "ambiguous": true|false,
      "risk": "high|medium|low"
    }
  ],
  "ambiguities": ["unclear point 1"],
  "assumptions": ["assumption 1"]
}""",
        messages=[{"role": "user", "content": f"{feature}\n\nLimit to maximum 6 requirements."}]
    )
    return parse_json(response.content[0].text)


def generate_test_plan(requirements, human_feedback=None):
    print("  [agent] generating test plan...")
    prompt = f"Requirements:\n{json.dumps(requirements, indent=2)}"
    if human_feedback:
        prompt += f"\n\nHuman feedback to incorporate:\n{human_feedback}"

    response = client.messages.create(
        model="claude-sonnet-4-6",
        max_tokens=4096,
        system="""You are a QA test planner.
Create a test plan from requirements.
Respond ONLY with valid JSON, no markdown:
{
  "test_plan": [
    {
      "req_id": "REQ-001",
      "test_cases": ["what to test 1", "what to test 2"],
      "priority": "high|medium|low",
      "automation_candidate": true|false
    }
  ],
  "total_cases": number,
  "automation_coverage": "percentage string"
}""",
        messages=[{"role": "user", "content": prompt}]
    )
    return parse_json(response.content[0].text)

def write_final_report(feature, requirements, test_plan, approvals):
    print("  [agent] writing final report...")
    response = client.messages.create(
        model="claude-sonnet-4-6",
        max_tokens=2048,
        system="""You are a QA report writer.
Write a concise test planning report in plain text, no markdown.
Include: overview, requirements summary, test plan summary, 
human review notes, and recommended next steps.""",
        messages=[{
            "role": "user",
            "content": f"""Feature: {feature}
Requirements: {json.dumps(requirements, indent=2)}
Test plan: {json.dumps(test_plan, indent=2)}
Human review notes: {json.dumps(approvals, indent=2)}"""
        }]
    )
    return response.content[0].text


# ── HITL orchestrator ──────────────────────────────────────

def run_hitl_agent(feature_description):
    print(f"\nHITL Agent starting")
    print(f"Feature: {feature_description[:60]}...")
    print("=" * 50)

    approval_log = []

    # ── step 1: analyze requirements ──────────────────────
    print("\n[1/3] Analyzing requirements...")
    requirements = analyze_requirements(feature_description)

    ambiguous = [r for r in requirements["requirements"] if r.get("ambiguous")]
    high_risk  = [r for r in requirements["requirements"] if r.get("risk") == "high"]

    print(f"  Found {len(requirements['requirements'])} requirements")
    print(f"  Ambiguous: {len(ambiguous)}, High risk: {len(high_risk)}")

    # Checkpoint 1 — pause if ambiguities or high risk requirements found
    if ambiguous or high_risk or requirements.get("ambiguities"):
        decision = human_checkpoint(
            action="Proceed with requirements analysis",
            details={
                "ambiguous_requirements": [r["id"] for r in ambiguous],
                "high_risk_requirements": [r["id"] for r in high_risk],
                "ambiguities_found": requirements.get("ambiguities", []),
                "assumptions_made": requirements.get("assumptions", [])
            },
            risk_level="medium"
        )
        approval_log.append({
            "checkpoint": "requirements_review",
            "decision": decision,
            "timestamp": datetime.now().isoformat()
        })

        if not decision["approved"]:
            print("\nAgent stopped at requirements review.")
            return None

        if decision["modified"]:
            # Re-analyze with human feedback
            print("  Re-analyzing with your feedback...")
            requirements = analyze_requirements(
                f"{feature_description}\n\nAdditional context: {decision['feedback']}"
            )

    # ── step 2: generate test plan ─────────────────────────
    print("\n[2/3] Generating test plan...")
    test_plan = generate_test_plan(requirements)

    # Check agent confidence
    confidence = check_confidence("generate test plan", test_plan)
    print(f"  Agent confidence: {confidence['confidence']}%")

    # Checkpoint 2 — pause if low confidence or large plan
    needs_review = (
        confidence["confidence"] < 75
        or confidence.get("needs_human_review")
        or test_plan.get("total_cases", 0) > 20
    )

    if needs_review:
        decision = human_checkpoint(
            action="Approve test plan before writing report",
            details={
                "total_cases": test_plan.get("total_cases"),
                "automation_coverage": test_plan.get("automation_coverage"),
                "agent_confidence": f"{confidence['confidence']}%",
                "agent_concerns": confidence.get("concerns", [])
            },
            risk_level="high" if confidence["confidence"] < 60 else "medium"
        )
        approval_log.append({
            "checkpoint": "test_plan_review",
            "decision": decision,
            "timestamp": datetime.now().isoformat()
        })

        if not decision["approved"]:
            print("\nAgent stopped at test plan review.")
            return None

        if decision["modified"]:
            print("  Regenerating test plan with your feedback...")
            test_plan = generate_test_plan(requirements, decision["feedback"])

    # ── step 3: write final report ─────────────────────────
    print("\n[3/3] Writing final report...")
    report = write_final_report(
        feature_description, requirements, test_plan, approval_log
    )

    # Checkpoint 3 — always require approval before saving report
    decision = human_checkpoint(
        action="Save and finalize report",
        details={
            "report_preview": report[:300] + "...",
            "output_files": ["hitl_report.txt", "hitl_output.json"]
        },
        risk_level="low"
    )
    approval_log.append({
        "checkpoint": "final_report",
        "decision": decision,
        "timestamp": datetime.now().isoformat()
    })

    if not decision["approved"]:
        print("\nReport not saved.")
        return None

    # Save outputs
    final_output = {
        "feature":      feature_description[:80],
        "requirements": requirements,
        "test_plan":    test_plan,
        "approval_log": approval_log,
        "report":       report
    }

    with open("hitl_output.json", "w") as f:
        json.dump(final_output, f, indent=2)

    with open("hitl_report.txt", "w") as f:
        f.write(report)

    print("\n" + "=" * 50)
    print("COMPLETE")
    print("=" * 50)
    print(f"Requirements : {len(requirements['requirements'])}")
    print(f"Test cases   : {test_plan.get('total_cases')}")
    print(f"Checkpoints  : {len(approval_log)}")
    print(f"\nFinal report:\n{report}")

    return final_output


# ── run it ─────────────────────────────────────────────────

run_hitl_agent("""
Two-factor authentication (2FA):
After password login, user receives a 6-digit OTP via SMS or email.
OTP expires after 5 minutes and is single-use.
User has 3 attempts before account is temporarily locked.
Users can choose between SMS and email delivery.
Backup codes available if primary method unavailable.
""")
