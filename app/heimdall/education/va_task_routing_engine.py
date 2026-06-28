from typing import Any, Dict, List
from datetime import datetime, timedelta


def make_task(
    title: str,
    priority: str,
    owner_role: str,
    due_hours: int,
    approval_required: bool = False,
    notes: str = "",
) -> Dict[str, Any]:
    return {
        "title": title,
        "priority": priority,
        "owner_role": owner_role,
        "status": "OPEN",
        "created_at": datetime.utcnow().isoformat(),
        "due_at": (datetime.utcnow() + timedelta(hours=due_hours)).isoformat(),
        "approval_required": approval_required,
        "notes": notes,
    }


def route_va_tasks(command_result: Dict[str, Any], deal: Dict[str, Any]) -> Dict[str, Any]:
    command = command_result.get("command")
    tasks: List[Dict[str, Any]] = []

    if command in ["HOLD_MISSING_INFORMATION", "POSSIBLE_DEAL_MORE_DUE_DILIGENCE"]:
        for item in command_result.get("missing_data", []):
            tasks.append(make_task(
                title=f"Collect missing data: {item}",
                priority="high",
                owner_role="VA_RESEARCH",
                due_hours=12,
                notes="Required before Heimdall can approve next action.",
            ))

        tasks.extend([
            make_task("Verify seller authority/ownership", "high", "VA_DUE_DILIGENCE", 12),
            make_task("Collect property photos", "medium", "VA_SELLER_SUPPORT", 24),
            make_task("Confirm tax/title status checkpoint", "high", "VA_DUE_DILIGENCE", 24),
        ])

    elif command == "BUILD_BUYER_LIST_FIRST":
        tasks.extend([
            make_task("Run buyer sourcing plan for this city", "high", "VA_BUYER_RESEARCH", 12),
            make_task("Find 20 potential cash buyers", "high", "VA_BUYER_RESEARCH", 24),
            make_task("Tag buyer buy-boxes", "high", "VA_BUYER_RESEARCH", 36),
            make_task("Verify proof-of-funds status where possible", "medium", "VA_BUYER_RESEARCH", 48),
        ])

    elif command == "SOURCE_OR_MATCH_BUYERS_FIRST":
        tasks.extend([
            make_task("Match deal against current buyer list", "high", "VA_BUYER_COORDINATION", 6),
            make_task("Add missing buyer profiles", "medium", "VA_BUYER_RESEARCH", 24),
            make_task("Prepare buyer outreach queue", "high", "VA_BUYER_COORDINATION", 12, True),
        ])

    elif command == "RENEGOTIATE":
        tasks.extend([
            make_task("Prepare seller renegotiation notes", "high", "VA_SELLER_SUPPORT", 6, True),
            make_task("Confirm updated MAO and repair assumptions", "high", "VA_DUE_DILIGENCE", 12),
            make_task("Draft seller follow-up message", "high", "VA_SELLER_SUPPORT", 6, True),
        ])

    elif command == "STRONG_CANDIDATE_APPROVAL_REQUIRED":
        tasks.extend([
            make_task("Prepare lawyer review packet", "critical", "VA_DOCUMENTS", 6, True),
            make_task("Prepare seller offer summary", "critical", "VA_DOCUMENTS", 6, True),
            make_task("Prepare buyer teaser packet", "high", "VA_BUYER_COORDINATION", 8, True),
            make_task("Prepare buyer outreach queue", "high", "VA_BUYER_COORDINATION", 8, True),
            make_task("Confirm all red flags are resolved", "critical", "VA_DUE_DILIGENCE", 6),
        ])

    elif command in ["PASS_OR_HOLD", "PASS_OR_NURTURE"]:
        tasks.extend([
            make_task("Move seller into nurture sequence", "medium", "VA_SELLER_SUPPORT", 24),
            make_task("Record pass reason in deal notes", "medium", "VA_ADMIN", 12),
            make_task("Set 30-day follow-up reminder", "low", "VA_ADMIN", 24),
        ])

    else:
        tasks.append(make_task(
            title="Review Heimdall command manually",
            priority="medium",
            owner_role="VA_ADMIN",
            due_hours=24,
            approval_required=True,
            notes="Command type was not recognized by routing engine.",
        ))

    return {
        "deal_id": deal.get("id"),
        "property_address": deal.get("property_address"),
        "command": command,
        "task_count": len(tasks),
        "tasks": tasks,
        "human_approval_required_for_critical_tasks": True,
    }
