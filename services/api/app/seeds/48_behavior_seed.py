"""
Pack 48: Heimdall Behavioral Core
Seed default personas and script snippets
"""
import os
from sqlalchemy.orm import Session
from app.behavior.models import BehaviorWeight, ScriptSnippet


def seed_behavior(db: Session) -> None:
    """
    Seed default personas (consultant, closer, therapist, analyst) and sample script snippets.
    """
    # Default personas with psychology weights
    personas = [
        {
            "persona": "consultant",
            "trust_weight": 1.5,
            "urgency_weight": 0.8,
            "resistance_weight": 1.2,
            "sentiment_weight": 1.0,
            "authority_weight": 1.0,
            "tone_weight": 0.7
        },
        {
            "persona": "closer",
            "trust_weight": 1.0,
            "urgency_weight": 1.8,
            "resistance_weight": 0.5,
            "sentiment_weight": 0.8,
            "authority_weight": 1.2,
            "tone_weight": 1.0
        },
        {
            "persona": "therapist",
            "trust_weight": 2.0,
            "urgency_weight": 0.3,
            "resistance_weight": 1.5,
            "sentiment_weight": 1.8,
            "authority_weight": 0.5,
            "tone_weight": 1.2
        },
        {
            "persona": "analyst",
            "trust_weight": 1.2,
            "urgency_weight": 1.0,
            "resistance_weight": 1.0,
            "sentiment_weight": 0.7,
            "authority_weight": 1.5,
            "tone_weight": 0.5
        }
    ]

    for p in personas:
        existing = db.query(BehaviorWeight).filter_by(persona=p["persona"]).first()
        if not existing:
            weight = BehaviorWeight(**p)
            db.add(weight)

    db.commit()

    # Sample script snippets
    snippets = [
        {
            "snippet_name": "consultant_greeting_warm",
            "persona": "consultant",
            "intent": "greeting",
            "tone": "positive",
            "text": "Hi! I'm glad you reached out. Let's explore what would work best for your situation.",
            "confidence_threshold": 0.5
        },
        {
            "snippet_name": "closer_urgency_high",
            "persona": "closer",
            "intent": "close",
            "tone": "neutral",
            "text": "This opportunity won't last long. Let's finalize the terms today so you don't miss out.",
            "confidence_threshold": 0.7
        },
        {
            "snippet_name": "therapist_empathy",
            "persona": "therapist",
            "intent": "support",
            "tone": "positive",
            "text": "I understand this is a big decision. Take your time, and let me know how I can help ease any concerns.",
            "confidence_threshold": 0.4
        },
        {
            "snippet_name": "analyst_data_driven",
            "persona": "analyst",
            "intent": "analysis",
            "tone": "neutral",
            "text": "Based on the numbers, here's what makes sense: the ROI is strong, and the risk is manageable.",
            "confidence_threshold": 0.6
        }
    ]

    for s in snippets:
        existing = db.query(ScriptSnippet).filter_by(snippet_name=s["snippet_name"]).first()
        if not existing:
            snippet = ScriptSnippet(**s)
            db.add(snippet)

    db.commit()
    print("✅ Pack 48: Heimdall Behavioral Core seeded")
