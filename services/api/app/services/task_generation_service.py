"""
Task Generation Service - creates operator task list from routing decision
"""
from typing import List, Dict, Any
from enum import Enum
import logging

logger = logging.getLogger(__name__)


class TaskCategory(str, Enum):
    """Task categories"""
    VERIFICATION = "verification"
    CONTACT = "contact"
    ANALYSIS = "analysis"
    LOGISTICS = "logistics"
    DECISION = "decision"


class ExecutionTaskGenerationService:
    """
    Generates actionable task list for operator based on:
    - Execution pipeline selected
    - Opportunity type
    - Missing information
    - Confidence level
    """
    
    def generate_tasks(
        self,
        case_id: int,
        pipeline: str,
        classification: str,
        assessment: dict,
        extracted_fields: dict,
        missing_fields: List[str],
    ) -> List[Dict[str, Any]]:
        """
        Generate task list for operator.
        
        Returns list of tasks:
            {
                "title": str,
                "instructions": str,
                "category": TaskCategory,
                "priority": 1-10 (1=urgent),
                "sequence": int (order in list),
                "due_date": days from now,
            }
        """
        
        tasks = []
        sequence = 1
        
        if pipeline == "blocked":
            return [{
                "case_id": case_id,
                "title": "Blocked - Review blockers",
                "instructions": (
                    f"This opportunity cannot proceed. Reason: {assessment.get('reason', 'Unknown')}\n"
                    "Review with manager if you believe this is an error."
                ),
                "category": TaskCategory.DECISION.value,
                "priority": 1,
                "sequence": 1,
                "due_days": 1,
            }]
        
        if pipeline == "manual_review":
            return [{
                "case_id": case_id,
                "title": "Submit for manual underwriting review",
                "instructions": (
                    "This opportunity doesn't have enough data for automated processing.\n"
                    "Gather all available information and submit to manual underwriting.\n"
                    "Expected decision time: 2 business days."
                ),
                "category": TaskCategory.DECISION.value,
                "priority": 1,
                "sequence": 1,
                "due_days": 1,
            }]
        
        # Verification tasks (always first)
        verification_tasks = self._generate_verification_tasks(
            pipeline=pipeline,
            classification=classification,
            extracted_fields=extracted_fields,
            missing_fields=missing_fields,
        )
        for task in verification_tasks:
            task["sequence"] = sequence
            task["case_id"] = case_id
            tasks.append(task)
            sequence += 1
        
        # Contact tasks if needed
        if self._needs_contact_tasks(assessment):
            contact_tasks = self._generate_contact_tasks(classification)
            for task in contact_tasks:
                task["sequence"] = sequence
                task["case_id"] = case_id
                tasks.append(task)
                sequence += 1
        
        # Analysis tasks
        analysis_tasks = self._generate_analysis_tasks(pipeline, assessment)
        for task in analysis_tasks:
            task["sequence"] = sequence
            task["case_id"] = case_id
            tasks.append(task)
            sequence += 1
        
        # Decision task (last)
        tasks.append({
            "case_id": case_id,
            "title": "Decide: Proceed or pass?",
            "instructions": (
                "Review all completed tasks and information gathered.\n"
                f"Decision: {self._get_recommendation(pipeline, assessment)}\n"
                "Click 'Yes' to proceed or 'No' to archive."
            ),
            "category": TaskCategory.DECISION.value,
            "priority": 1,
            "sequence": sequence,
            "due_days": 14,
        })
        
        return tasks
    
    def _generate_verification_tasks(
        self,
        pipeline: str,
        classification: str,
        extracted_fields: dict,
        missing_fields: list,
    ) -> List[Dict[str, Any]]:
        """Generate verification tasks"""
        
        tasks = []
        priority_sequence = 1
        
        if classification == "real_estate":
            # Priority 1: Verify property exists
            tasks.append({
                "title": "Verify property exists and matches description",
                "instructions": (
                    "Confirm the property is real and details are accurate:\n"
                    f"- Location: {extracted_fields.get('location', 'Unknown')}\n"
                    f"- Type: {extracted_fields.get('property_type', 'Unknown')}\n"
                    f"- Specs: {extracted_fields.get('bedrooms')}bd/{extracted_fields.get('bathrooms')}ba\n"
                    "Methods: Google Maps, MLS, County Assessor website, or phone call"
                ),
                "category": TaskCategory.VERIFICATION.value,
                "priority": 1,
                "due_days": 1,
            })
            
            # Priority 2: Check title status
            if pipeline in ["standard_wholesale", "fix_and_flip", "buy_and_hold"]:
                tasks.append({
                    "title": "Verify title status (clear or issues noted)",
                    "instructions": (
                        "Check for liens, mortgages, or other title issues:\n"
                        "- Order title search from title company (~$50-100)\n"
                        "- Or request seller provide title commitment\n"
                        "- Document any issues found"
                    ),
                    "category": TaskCategory.VERIFICATION.value,
                    "priority": 2,
                    "due_days": 2,
                })
            
            # Priority 3: Property condition (if needed)
            if "estimated_repair_cost" in missing_fields:
                tasks.append({
                    "title": "Assess property condition",
                    "instructions": (
                        "Determine actual condition and repair needs:\n"
                        "- Drive by property for visual inspection\n"
                        "- Or arrange professional inspection (~$300-500)\n"
                        "- Document major issues and estimated repair costs"
                    ),
                    "category": TaskCategory.VERIFICATION.value,
                    "priority": 2,
                    "due_days": 3,
                })
            
            # Priority 4: Market comparables
            if pipeline in ["standard_wholesale", "fix_and_flip"]:
                tasks.append({
                    "title": "Pull market comparables for valuation",
                    "instructions": (
                        "Verify estimated value is realistic:\n"
                        "- Find 3-5 recent sales of similar properties\n"
                        "- Within 1 mile and last 6 months if possible\n"
                        "- Review MLS or Zillow for comparable sales\n"
                        "- Adjust for condition/location differences"
                    ),
                    "category": TaskCategory.ANALYSIS.value,
                    "priority": 3,
                    "due_days": 2,
                })
        
        elif classification == "business":
            tasks.append({
                "title": "Verify business legitimacy",
                "instructions": (
                    "Confirm the business is real and operating:\n"
                    "- Check business registration with state\n"
                    "- Verify business license and permits\n"
                    "- Review online presence (website, social media, reviews)\n"
                    "- Confirm operator/owner identity"
                ),
                "category": TaskCategory.VERIFICATION.value,
                "priority": 1,
                "due_days": 1,
            })
            
            tasks.append({
                "title": "Request current financial information",
                "instructions": (
                    "Get documentation of actual performance:\n"
                    "- Request last 2 years of tax returns or P&L statements\n"
                    "- Get last 3-6 months of bank statements\n"
                    "- Ask for customer/revenue list if applicable\n"
                    "- Document revenue and expense trends"
                ),
                "category": TaskCategory.CONTACT.value,
                "priority": 2,
                "due_days": 3,
            })
        
        elif classification == "jv":
            tasks.append({
                "title": "Verify partner legitimacy and capacity",
                "instructions": (
                    "Confirm partner is credible and can execute:\n"
                    "- Get background on partner (LinkedIn, references)\n"
                    "- Verify financial capacity (ask for bank statement)\n"
                    "- Check past deals/references\n"
                    "- Assess if they have resources needed"
                ),
                "category": TaskCategory.VERIFICATION.value,
                "priority": 1,
                "due_days": 2,
            })
        
        return tasks
    
    def _needs_contact_tasks(self, assessment: dict) -> bool:
        """Determine if contact/negotiation tasks needed"""
        confidence = assessment.get("confidence_score", 50)
        return confidence < 75
    
    def _generate_contact_tasks(self, classification: str) -> List[Dict[str, Any]]:
        """Generate tasks requiring contact with parties"""
        
        tasks = []
        
        if classification == "real_estate":
            tasks.append({
                "title": "Contact seller to confirm motivation",
                "instructions": (
                    "Understand seller's situation and timeline:\n"
                    "- Why are they selling?\n"
                    "- What's their timeline (days/weeks/months)?\n"
                    "- Will they negotiate on price?\n"
                    "- Are there any other interested buyers?\n"
                    "- Document responses"
                ),
                "category": TaskCategory.CONTACT.value,
                "priority": 3,
                "due_days": 2,
            })
        
        elif classification == "business":
            tasks.append({
                "title": "Call operator/owner for deep dive",
                "instructions": (
                    "Understand the business model and opportunity:\n"
                    "- How do they make money? (What's the business model?)\n"
                    "- What are current revenues and expenses?\n"
                    "- What's the specific opportunity being offered?\n"
                    "- What role do we need to play?\n"
                    "- What's their timeline?\n"
                    "- Record detailed notes"
                ),
                "category": TaskCategory.CONTACT.value,
                "priority": 2,
                "due_days": 2,
            })
        
        return tasks
    
    def _generate_analysis_tasks(self, pipeline: str, assessment: dict) -> List[Dict[str, Any]]:
        """Generate analytical tasks based on pipeline"""
        
        tasks = []
        risk_score = assessment.get("risk_score", 50)
        
        if pipeline == "quick_wholesale":
            tasks.append({
                "title": "Calculate wholesale spread",
                "instructions": (
                    "Determine our offer price and profit margin:\n"
                    f"- ARV (estimated value): ${assessment.get('estimated_value', 0):,.0f}\n"
                    f"- Estimated repairs: ${assessment.get('estimated_repair_cost', 0):,.0f}\n"
                    "- Buyer's profit needed: ~15-20%\n"
                    "- Our profit target: ~$10k-$15k\n"
                    "- Calculate: Our offer = ARV - repairs - buyer profit - our profit"
                ),
                "category": TaskCategory.ANALYSIS.value,
                "priority": 2,
                "due_days": 1,
            })
        
        elif pipeline in ["standard_wholesale", "fix_and_flip"]:
            tasks.append({
                "title": "Create deal analysis spreadsheet",
                "instructions": (
                    "Document complete deal math:\n"
                    "- Purchase price\n"
                    "- Estimated repairs (itemized if possible)\n"
                    "- Carrying costs (if applicable)\n"
                    "- Closing costs and fees\n"
                    "- ARV (based on comps)\n"
                    "- Profit calculation\n"
                    "- Sensitivity analysis (best/worst case)"
                ),
                "category": TaskCategory.ANALYSIS.value,
                "priority": 2,
                "due_days": 2,
            })
        
        # Risk-based tasks
        if risk_score > 60:
            tasks.append({
                "title": "Document risk mitigations",
                "instructions": (
                    "This deal has moderate-to-high risk. Plan mitigations:\n"
                    f"- Risk score: {risk_score}/100\n"
                    "- What could go wrong?\n"
                    "- What's our backup plan?\n"
                    "- Do we have insurance/contingencies?\n"
                    "- Is this acceptable risk level?"
                ),
                "category": TaskCategory.DECISION.value,
                "priority": 2,
                "due_days": 3,
            })
        
        return tasks
    
    def _get_recommendation(self, pipeline: str, assessment: dict) -> str:
        """Get recommendation for operator"""
        
        if pipeline == "blocked":
            return "❌ BLOCKED - Do not proceed"
        
        profit = assessment.get("estimated_profit", 0)
        confidence = assessment.get("confidence_score", 50)
        risk = assessment.get("risk_score", 50)
        
        if confidence < 50:
            return "⚠️ LOW CONFIDENCE - Request manual review"
        
        if risk > 70:
            return "⚠️ HIGH RISK - Consider passing or reducing exposure"
        
        if profit < 5000:
            return "✓ MARGINAL PROFIT - Verify numbers before committing"
        
        if confidence < 70 or risk > 50:
            return "✓ CONDITIONAL - Acceptable if confident in above analysis"
        
        return f"✓ RECOMMENDED - Solid opportunity ({profit/1000:.1f}k profit estimated)"
