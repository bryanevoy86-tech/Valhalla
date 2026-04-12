"""
Intake Parser Service - extracts structured fields from raw opportunity text
"""
import re
from typing import Optional, Dict, Any
import logging

logger = logging.getLogger(__name__)


class IntakeParserService:
    """
    Parses raw opportunity text into structured fields.
    
    Extracts:
    - Prices (asking, offer, estimated value)
    - Property specs (beds, baths, SF)
    - Condition/issues
    - Location
    - Contact info
    - Timeline/urgency
    """
    
    def parse(self, raw_text: str) -> Dict[str, Any]:
        """
        Parse raw opportunity text.
        
        Returns: {
            "raw_text": str,
            "extracted_fields": {
                "location": str,
                "property_type": str,
                "bedrooms": int,
                "bathrooms": int,
                "square_feet": int,
                "asking_price": float,
                "estimated_arv": float,
                "estimated_repair_cost": float,
                "condition_notes": str,
                "urgency": str,  # normal, moderate, urgent
                "contact_info": str,
            },
            "confidence": float,  # 0-100 on parse quality
            "missing_fields": [list],
            "extraction_summary": str,
        }
        """
        
        if not raw_text or not isinstance(raw_text, str):
            return {
                "raw_text": raw_text,
                "extracted_fields": {},
                "confidence": 0,
                "missing_fields": ["Valid input required"],
                "extraction_summary": "No valid text to parse"
            }
        
        extracted = {}
        
        # Extract prices
        extracted["asking_price"] = self._extract_asking_price(raw_text)
        extracted["estimated_arv"] = self._extract_arv_estimate(raw_text)
        extracted["estimated_repair_cost"] = self._extract_repair_estimate(raw_text)
        
        # Extract property specs
        extracted["property_type"] = self._extract_property_type(raw_text)
        extracted["bedrooms"] = self._extract_bedrooms(raw_text)
        extracted["bathrooms"] = self._extract_bathrooms(raw_text)
        extracted["square_feet"] = self._extract_square_feet(raw_text)
        
        # Extract qualitative info
        extracted["location"] = self._extract_location(raw_text)
        extracted["condition_notes"] = self._extract_condition(raw_text)
        extracted["urgency"] = self._extract_urgency(raw_text)
        extracted["contact_info"] = self._extract_contact(raw_text)
        
        # Calculate confidence based on field density
        filled_fields = sum(1 for v in extracted.values() if v is not None and v != "unknown")
        total_fields = len(extracted)
        confidence = (filled_fields / total_fields * 100) if total_fields > 0 else 0
        
        # Identify missing critical fields
        missing = []
        critical_fields = ["asking_price", "bedrooms", "square_feet"]
        for field in critical_fields:
            if extracted.get(field) is None:
                missing.append(field)
        
        return {
            "raw_text": raw_text[:500],  # Truncate for storage
            "extracted_fields": extracted,
            "confidence": min(100, max(0, confidence)),
            "missing_fields": missing,
            "extraction_summary": self._summarize_extraction(extracted),
        }
    
    def _extract_asking_price(self, text: str) -> Optional[float]:
        """Extract asking/list price"""
        patterns = [
            r'asking.{0,20}?\$[\d,]+',
            r'list.{0,20}?\$[\d,]+',
            r'price.{0,20}?\$[\d,]+',
            r'asking.{0,20}?[\d,]+',
            r'\$[\d,]+(?:\s*(asking|list|offer|price))?'
        ]
        
        for pattern in patterns:
            matches = re.findall(pattern, text, re.IGNORECASE)
            if matches:
                # Extract just the number
                price_match = re.search(r'\$?([\d,]+)', str(matches[0]))
                if price_match:
                    try:
                        return float(price_match.group(1).replace(',', ''))
                    except:
                        continue
        return None
    
    def _extract_arv_estimate(self, text: str) -> Optional[float]:
        """Extract After-Repair Value estimate"""
        patterns = [
            r'arv.{0,20}?\$[\d,]+',
            r'after.?repair.{0,15}?\$[\d,]+',
            r'estimated value.{0,15}?\$[\d,]+',
            r'should be worth.{0,15}?\$[\d,]+',
        ]
        
        for pattern in patterns:
            matches = re.findall(pattern, text, re.IGNORECASE)
            if matches:
                price_match = re.search(r'\$?([\d,]+)', str(matches[0]))
                if price_match:
                    try:
                        return float(price_match.group(1).replace(',', ''))
                    except:
                        continue
        return None
    
    def _extract_repair_estimate(self, text: str) -> Optional[float]:
        """Extract repair cost estimate"""
        patterns = [
            r'repair.{0,20}?(?:\$|estimate)[\d,]+',
            r'rehab.{0,20}?(?:\$|estimate)[\d,]+',
            r'renovation.{0,20}?(?:\$|estimate)[\d,]+',
            r'work needed.{0,20}?\$[\d,]+',
            r'needs.*?[\d,]+k?',
        ]
        
        for pattern in patterns:
            matches = re.findall(pattern, text, re.IGNORECASE)
            if matches:
                # Try extracting dollar amount
                price_match = re.search(r'\$?([\d,]+)', str(matches[0]))
                if price_match:
                    try:
                        value = price_match.group(1).replace(',', '')
                        # If it looks like thousands (k suffix), multiply by 1000
                        if 'k' in str(matches[0]).lower():
                            return float(value) * 1000
                        return float(value)
                    except:
                        continue
        return None
    
    def _extract_bedrooms(self, text: str) -> Optional[int]:
        """Extract bedroom count"""
        pattern = r'(\d+)\s*(?:bed|bedroom|br|b\.?r\.?)'
        matches = re.findall(pattern, text, re.IGNORECASE)
        if matches:
            try:
                return int(matches[0])
            except:
                return None
        return None
    
    def _extract_bathrooms(self, text: str) -> Optional[int]:
        """Extract bathroom count"""
        pattern = r'(\d+(?:\.\d+)?)\s*(?:bath|bathroom|ba|b\.?a\.?)'
        matches = re.findall(pattern, text, re.IGNORECASE)
        if matches:
            try:
                return int(float(matches[0]))
            except:
                return None
        return None
    
    def _extract_square_feet(self, text: str) -> Optional[int]:
        """Extract square footage"""
        patterns = [
            r'(\d+)\s*(?:sf|sq\.?\s*ft|square feet)',
            r'(\d+)\s*sqft',
        ]
        
        for pattern in patterns:
            matches = re.findall(pattern, text, re.IGNORECASE)
            if matches:
                try:
                    return int(matches[0])
                except:
                    continue
        return None
    
    def _extract_property_type(self, text: str) -> Optional[str]:
        """Identify property type"""
        type_keywords = {
            "single_family": ["house", "single family", "home", "sfh", "sf home"],
            "multi_family": ["duplex", "triplex", "multi-family", "4-plex", "apartment", "complex"],
            "commercial": ["commercial", "retail", "office", "strip mall", "shopping"],
            "land": ["land", "lot", "vacant", "raw ground"],
            "mobile": ["mobile home", "manufactured home", "trailer", "rv park"],
        }
        
        text_lower = text.lower()
        for prop_type, keywords in type_keywords.items():
            if any(kw in text_lower for kw in keywords):
                return prop_type
        
        return None
    
    def _extract_location(self, text: str) -> Optional[str]:
        """Extract location/address"""
        # Look for patterns like "at 123 Main St" or "located on..."
        patterns = [
            r'at\s+([^,\.]+(?:st|ave|rd|blvd|drive|lane|circle)\.?)',
            r'located (?:at|in|on)\s+([^,\.]+)',
            r'address[:\s]+([^,\.]+)',
        ]
        
        for pattern in patterns:
            matches = re.findall(pattern, text, re.IGNORECASE)
            if matches:
                return matches[0].strip()
        
        return None
    
    def _extract_condition(self, text: str) -> Optional[str]:
        """Extract property condition notes"""
        condition_keywords = {
            "excellent": ["excellent", "perfect", "mint", "move-in ready", "turnkey"],
            "good": ["good", "solid", "well maintained"],
            "fair": ["fair", "average", "needs some work", "cosmetic"],
            "poor": ["poor", "needs work", "distressed", "fixer upper", "as-is"],
        }
        
        text_lower = text.lower()
        for condition, keywords in condition_keywords.items():
            for keyword in keywords:
                if keyword in text_lower:
                    return condition
        
        return None
    
    def _extract_urgency(self, text: str) -> str:
        """Determine urgency from text"""
        urgent_keywords = ["urgent", "asap", "rush", "today", "immediately", "cannot wait"]
        moderate_keywords = ["soon", "week", "quick", "quickly"]
        
        text_lower = text.lower()
        
        if any(kw in text_lower for kw in urgent_keywords):
            return "urgent"
        elif any(kw in text_lower for kw in moderate_keywords):
            return "moderate"
        else:
            return "normal"
    
    def _extract_contact(self, text: str) -> Optional[str]:
        """Extract contact information"""
        patterns = [
            r'(?:call|contact|phone)[:\s]+([0-9\-\(\)\s]+)',
            r'(?:email|reach)[:\s]+([^\s,\.]+@[^\s,\.]+)',
            r'contact:\s+([^,\.]+)',
        ]
        
        for pattern in patterns:
            matches = re.findall(pattern, text, re.IGNORECASE)
            if matches:
                return matches[0].strip()
        
        return None
    
    def _summarize_extraction(self, fields: dict) -> str:
        """Generate summary of extracted information"""
        parts = []
        
        if fields.get("bedrooms"):
            parts.append(f"{fields['bedrooms']}bd")
        if fields.get("bathrooms"):
            parts.append(f"{fields['bathrooms']}ba")
        if fields.get("square_feet"):
            parts.append(f"{fields['square_feet']}sf")
        
        if parts:
            spec_str = ", ".join(parts)
        else:
            spec_str = "specs unknown"
        
        if fields.get("asking_price"):
            price_str = f"asking ${fields['asking_price']:,.0f}"
        else:
            price_str = "price unknown"
        
        location = fields.get("location") or "location unknown"
        
        return f"{spec_str} | {price_str} | {location}"
