# services/api/app/services/ui_map.py

"""
UI Map Service for PACK U: Frontend Preparation
Provides a structured, machine-readable map of API modules, sections, and endpoints
for WeWeb and other frontends to auto-generate UI screens and navigation.
"""

from __future__ import annotations

from typing import Any, Dict, List


def get_ui_map() -> Dict[str, Any]:
    """
    Returns a structured map for frontend navigation and builders.
    Grouped by logical modules (Professionals, Contracts, Deals, Audit, Governance, Debug).
    
    This map is curated and designed for UI generation, not a raw route list.
    Use /debug/routes (PACK S) for the complete, unfiltered route list.
    """

    return {
        "modules": [
            {
                "id": "professionals",
                "label": "Professionals",
                "description": "Professional management, scorecards, retainers, tasks, and handoff packets",
                "sections": [
                    {
                        "id": "scorecard",
                        "label": "Scorecards",
                        "description": "Track professional performance and interactions",
                        "endpoints": [
                            {
                                "method": "POST",
                                "path": "/pros/scorecard/professionals",
                                "summary": "Create or update professional profile",
                                "tags": ["Professionals"],
                            },
                            {
                                "method": "POST",
                                "path": "/pros/scorecard/interactions",
                                "summary": "Log interaction with professional",
                                "tags": ["Professionals", "Interactions"],
                            },
                            {
                                "method": "GET",
                                "path": "/pros/scorecard/{professional_id}",
                                "summary": "Get professional scorecard",
                                "tags": ["Professionals"],
                            },
                        ],
                    },
                    {
                        "id": "retainers",
                        "label": "Retainers",
                        "description": "Retainer agreements and management",
                        "endpoints": [
                            {
                                "method": "POST",
                                "path": "/pros/retainers/",
                                "summary": "Create retainer",
                                "tags": ["Professionals", "Retainers"],
                            },
                            {
                                "method": "GET",
                                "path": "/pros/retainers/{retainer_id}",
                                "summary": "Get retainer details",
                                "tags": ["Professionals", "Retainers"],
                            },
                        ],
                    },
                    {
                        "id": "tasks",
                        "label": "Professional Tasks",
                        "description": "Tasks assigned to professionals on deals",
                        "endpoints": [
                            {
                                "method": "POST",
                                "path": "/pros/tasks/",
                                "summary": "Create professional task",
                                "tags": ["Professionals", "Tasks"],
                            },
                            {
                                "method": "GET",
                                "path": "/pros/tasks/by-professional/{professional_id}",
                                "summary": "List professional tasks",
                                "tags": ["Professionals", "Tasks"],
                            },
                            {
                                "method": "GET",
                                "path": "/pros/tasks/by-deal/{deal_id}",
                                "summary": "List deal tasks",
                                "tags": ["Professionals", "Tasks", "Deals"],
                            },
                        ],
                    },
                    {
                        "id": "handoff",
                        "label": "Handoff Packets",
                        "description": "Generate handoff packets for professionals",
                        "endpoints": [
                            {
                                "method": "GET",
                                "path": "/pros/handoff/{professional_id}/{deal_id}",
                                "summary": "Generate handoff packet",
                                "tags": ["Professionals", "Handoff"],
                            },
                        ],
                    },
                ],
            },
            {
                "id": "contracts",
                "label": "Contracts & Documents",
                "description": "Contract management and document routing",
                "sections": [
                    {
                        "id": "lifecycle",
                        "label": "Contract Lifecycle",
                        "description": "Manage contract creation, updates, and status transitions",
                        "endpoints": [
                            {
                                "method": "POST",
                                "path": "/contracts/lifecycle/",
                                "summary": "Create contract",
                                "tags": ["Contracts"],
                            },
                            {
                                "method": "PATCH",
                                "path": "/contracts/lifecycle/{contract_id}/status",
                                "summary": "Update contract status",
                                "tags": ["Contracts"],
                            },
                            {
                                "method": "GET",
                                "path": "/contracts/lifecycle/by-deal/{deal_id}",
                                "summary": "List deal contracts",
                                "tags": ["Contracts", "Deals"],
                            },
                        ],
                    },
                    {
                        "id": "documents",
                        "label": "Document Routing",
                        "description": "Route documents to professionals",
                        "endpoints": [
                            {
                                "method": "POST",
                                "path": "/documents/routes/",
                                "summary": "Create document route",
                                "tags": ["Documents"],
                            },
                            {
                                "method": "GET",
                                "path": "/documents/routes/by-deal/{deal_id}",
                                "summary": "List routed documents for deal",
                                "tags": ["Documents", "Deals"],
                            },
                            {
                                "method": "GET",
                                "path": "/documents/routes/by-professional/{professional_id}",
                                "summary": "List routed documents for professional",
                                "tags": ["Documents", "Professionals"],
                            },
                        ],
                    },
                ],
            },
            {
                "id": "deals",
                "label": "Deals",
                "description": "Deal management and finalization",
                "sections": [
                    {
                        "id": "finalization",
                        "label": "Deal Finalization",
                        "description": "Check readiness and finalize deals",
                        "endpoints": [
                            {
                                "method": "GET",
                                "path": "/deals/finalization/status/{deal_id}",
                                "summary": "Check deal finalization status",
                                "tags": ["Deals"],
                            },
                            {
                                "method": "POST",
                                "path": "/deals/finalization/{deal_id}",
                                "summary": "Finalize deal",
                                "tags": ["Deals"],
                            },
                        ],
                    },
                ],
            },
            {
                "id": "audit_governance",
                "label": "Audit & Governance",
                "description": "Compliance auditing and governance decision logging",
                "sections": [
                    {
                        "id": "audit",
                        "label": "Internal Auditor",
                        "description": "Scan deals for compliance issues",
                        "endpoints": [
                            {
                                "method": "POST",
                                "path": "/audit/scan/deal/{deal_id}",
                                "summary": "Run audit on deal",
                                "tags": ["Audit"],
                            },
                            {
                                "method": "GET",
                                "path": "/audit/events/open",
                                "summary": "List open audit events",
                                "tags": ["Audit"],
                            },
                            {
                                "method": "GET",
                                "path": "/audit/summary",
                                "summary": "Get audit summary",
                                "tags": ["Audit"],
                            },
                        ],
                    },
                    {
                        "id": "governance",
                        "label": "Governance Decisions",
                        "description": "Record leadership decisions",
                        "endpoints": [
                            {
                                "method": "POST",
                                "path": "/governance/decisions/",
                                "summary": "Record governance decision",
                                "tags": ["Governance"],
                            },
                            {
                                "method": "GET",
                                "path": "/governance/decisions/subject/{subject_type}/{subject_id}",
                                "summary": "List decisions for subject",
                                "tags": ["Governance"],
                            },
                            {
                                "method": "GET",
                                "path": "/governance/decisions/by-role/{role}",
                                "summary": "List decisions by role",
                                "tags": ["Governance"],
                            },
                        ],
                    },
                ],
            },
            {
                "id": "debug_system",
                "label": "Debug & System",
                "description": "System introspection and health checks",
                "sections": [
                    {
                        "id": "routes",
                        "label": "Route Listing",
                        "description": "Complete list of all registered routes",
                        "endpoints": [
                            {
                                "method": "GET",
                                "path": "/debug/routes",
                                "summary": "List all routes",
                                "tags": ["Debug"],
                            },
                        ],
                    },
                    {
                        "id": "system",
                        "label": "System Health",
                        "description": "System snapshot including DB and subsystems",
                        "endpoints": [
                            {
                                "method": "GET",
                                "path": "/debug/system",
                                "summary": "Get system snapshot",
                                "tags": ["Debug"],
                            },
                        ],
                    },
                ],
            },
        ],
        "metadata": {
            "version": "1.0",
            "description": "Machine-readable API map for frontend UI generation",
            "last_updated": "2025-12-05",
        },
    }
