"""
Opportunity Classifier Service - classifies opportunity type and category
"""
import re
from typing import Optional, Tuple
import logging

logger = logging.getLogger(__name__)


class OpportunityClassifier:
    """
    Classifies raw opportunity text into a structured type.
    
    Categories (case_type):
    - real_estate: Property deals
    - business: Service/product businesses
    - arbitrage: Buy low/sell high opportunities
    - jv: Joint venture or partnership
    - unknown: Unclear/mixed
    """
    
    # Real estate keywords
    REAL_ESTATE_KEYWORDS = {
        "property", "house", "apartment", "condo", "townhouse", "dwelling", "residence",
        "rental", "tenant", "lease", "mortgage", "deed", "parcel", "lot", "acre",
        "square feet", "sf", "bedroom", "bed", "bath", "bathroom", "kitchen", "garage",
        "roofing", "foundation", "plumbing", "electrical", "hvac", "inspection",
        "appraisal", "listing", "mls", "realtor", "broker", "flip", "wholesale",
        "fix and flip", "fnh", "arv", "rehab", "renovation", "repair", "repair costs",
        "asking price", "list price", "offer", "escrow", "closing", "title",
        "fixer-upper", "distressed", "foreclosure", "short sale", "reo", "bank-owned",
        "estate sale", "probate", "subject-to", "assumable", "zoning", "subdivision",
        "neighborhood", "school district", "location", "down payment", "financing",
        "hard money", "private lender", "va loan", "fha loan", "conventional loan"
    }
    
    BUSINESS_KEYWORDS = {
        "business", "company", "startup", "service", "client", "customer", "revenue",
        "profit", "income", "business model", "employees", "staffing", "contract",
        "consulting", "agency", "franchise", "license", "permit", "subscription",
        "saas", "software", "app", "platform", "marketplace", "ecommerce", "online store",
        "retail", "restaurant", "cafe", "bar", "salon", "gym", "hotel", "motel",
        "transportation", "freight", "logistics", "warehouse", "manufacturing",
        "distributor", "wholesale", "vendor", "supplier", "inventory", "stock"
    }
    
    ARBITRAGE_KEYWORDS = {
        "buy low", "sell high", "arbitrage", "price difference", "discount",
        "clearance", "inventory liquidation", "closeout", "bulk purchase",
        "resale", "flip", "marketplace", "auction", "commodity", "futures",
        "crypto", "stock", "fund", "spread", "margin", "leverage"
    }
    
    JV_KEYWORDS = {
        "partnership", "joint venture", "jv", "partner", "collaborate", "team up",
        "cooperation", "combine resources", "split", "equity stake", "co-ownership",
        "merge", "acquisition", "alliance", "deal structure", "co-invest"
    }
    
    def __init__(self):
        """Initialize classifier"""
        self.keywords = {
            "real_estate": self.REAL_ESTATE_KEYWORDS,
            "business": self.BUSINESS_KEYWORDS,
            "arbitrage": self.ARBITRAGE_KEYWORDS,
            "jv": self.JV_KEYWORDS,
        }
    
    def classify(self, text: str) -> Tuple[str, dict]:
        """
        Classify opportunity type from text.
        
        Returns: (classification, details_dict)
            where details = {
                "confidence": 0-100,
                "keywords_matched": [list],
                "reasoning": str,
            }
        """
        
        if not text or not isinstance(text, str):
            return "unknown", {
                "confidence": 0,
                "keywords_matched": [],
                "reasoning": "Invalid input"
            }
        
        text_lower = text.lower()
        scores = {}
        matched = {}
        
        # Score each category
        for category, keywords in self.keywords.items():
            matches = [kw for kw in keywords if kw in text_lower]
            word_count = len(text_lower.split())
            score = (len(matches) / max(1, len(keywords)) * 100) if matches else 0
            
            scores[category] = score
            matched[category] = matches
        
        # Determine primary classification
        if not any(scores.values()):
            # No keywords matched
            return "unknown", {
                "confidence": 0,
                "keywords_matched": [],
                "reasoning": "No recognizable keywords"
            }
        
        primary = max(scores, key=scores.get)
        confidence = scores[primary]
        
        # Check for mixed/ambiguous cases
        near_scores = [v for k, v in scores.items() if k != primary and v > 20]
        if near_scores and len(near_scores) > 1:
            # Multiple strong matches = complex/mixed
            if "jv" in [k for k, v in scores.items() if v > 20]:
                primary = "jv"  # JV takes precedence
                confidence = scores["jv"]
        
        reasoning = self._explain_classification(primary, matched[primary], text_lower)
        
        return primary, {
            "confidence": min(100, max(0, confidence)),
            "keywords_matched": matched[primary],
            "reasoning": reasoning,
            "alternative_scores": {k: v for k, v in scores.items() if k != primary}
        }
    
    def _explain_classification(self, category: str, keywords: list, text: str) -> str:
        """Generate human-readable explanation"""
        
        if not keywords:
            return f"Classified as {category} based on text context"
        
        keyword_str = ", ".join(keywords[:3])
        if len(keywords) > 3:
            keyword_str += f", and {len(keywords) - 3} more"
        
        explanations = {
            "real_estate": f"Real estate opportunity detected (keywords: {keyword_str})",
            "business": f"Business opportunity detected (keywords: {keyword_str})",
            "arbitrage": f"Arbitrage/pricing opportunity detected (keywords: {keyword_str})",
            "jv": f"Partnership/collaboration opportunity detected (keywords: {keyword_str})",
            "unknown": "Unable to classify into a specific category"
        }
        
        return explanations.get(category, "Unknown classification")
    
    def extract_key_phrases(self, text: str) -> list:
        """Extract important phrases from opportunity text"""
        
        important_phrases = []
        
        # Look for price patterns
        price_pattern = r'\$[\d,]+(?:\.\d{2})?'
        prices = re.findall(price_pattern, text)
        important_phrases.extend([f"Price: {p}" for p in prices])
        
        # Look for property descriptions
        bedroom_pattern = r'(\d+)\s*(?:bed|bedroom|br)'
        bathrooms_pattern = r'(\d+)\s*(?:bath|bathroom)'
        
        beds = re.findall(bedroom_pattern, text, re.IGNORECASE)
        baths = re.findall(bathrooms_pattern, text, re.IGNORECASE)
        
        if beds:
            important_phrases.append(f"Beds: {beds[0]}")
        if baths:
            important_phrases.append(f"Baths: {baths[0]}")
        
        # Look for locations (all-caps phrases or after "at" keyword)
        location_pattern = r'(?:at|located at|location|address)\s+([^,\.]+)'
        locations = re.findall(location_pattern, text, re.IGNORECASE)
        important_phrases.extend([f"Location: {loc.strip()}" for loc in locations])
        
        # Look for conditions
        condition_keywords = ["excellent", "good", "fair", "poor", "needs work", "turnkey", "move-in ready"]
        for keyword in condition_keywords:
            if keyword.lower() in text.lower():
                important_phrases.append(f"Condition: {keyword}")
                break
        
        return important_phrases[:5]  # Top 5 phrases


class ClassificationReasoner:
    """Provides reasoning for classification decisions"""
    
    @staticmethod
    def provide_strategy_reasoning(
        classification: str,
        extracted_phrases: list,
        confidence: float
    ) -> str:
        """
        Provide plain-language reasoning for recommended strategy.
        """
        
        confidence_qualifier = (
            "high confidence" if confidence > 75
            else "moderate confidence" if confidence > 50
            else "low confidence"
        )
        
        if classification == "real_estate":
            return (
                f"Based on property details ({confidence_qualifier}), "
                "this opportunity fits real estate wholesale or "
                "buy-and-hold strategies."
            )
        elif classification == "business":
            return (
                f"This appears to be a business opportunity ({confidence_qualifier}). "
                "Consider partnership or revenue-share structures."
            )
        elif classification == "arbitrage":
            return (
                f"Arbitrage opportunity ({confidence_qualifier}). "
                "Profit depends on executing buy/sell at target prices."
            )
        elif classification == "jv":
            return (
                f"Partnership opportunity ({confidence_qualifier}). "
                "Structure deal as JV with clear roles and profit split."
            )
        else:
            return (
                f"Opportunity classification unclear ({confidence_qualifier}). "
                "Manual review recommended before proceeding."
            )
