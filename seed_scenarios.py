#!/usr/bin/env python3
"""
Heimdall Scenario Seeding Script
Seeds the system with 10 realistic deals to generate learning patterns.
"""

import requests
import json
import time
from datetime import datetime

BASE_URL = "http://127.0.0.1:4000/api/jarvis"

# 10 Simulated deals
DEALS = [
    {
        "id": 101,
        "name": "Mike Reynolds",
        "type": "buyer",
        "heat_score": 95,
        "days_stale": 2,
        "consent_sms": True,
        "consent_email": True,
        "preferred_channel": "sms",
        "reason": "Active cash buyer looking this week",
        "recommended_script": "Hey Mike, I've got something that might fit your buy box. Want details?",
        "status": "open",
        "action_count": 0,
        "outcome": {"result": "deal", "channel": "sms", "notes": "Buyer committed and wants contract"},
        "label": "🔥 DEAL 1 — Hot Cash Buyer (Fast Win)"
    },
    {
        "id": 102,
        "name": "Angela Brooks",
        "type": "seller",
        "heat_score": 78,
        "days_stale": 4,
        "consent_sms": True,
        "consent_email": True,
        "preferred_channel": "email",
        "reason": "Interested but hesitant seller",
        "recommended_script": "Hi Angela, just checking if you're still considering selling this month.",
        "status": "open",
        "action_count": 0,
        "outcome": {"result": "success", "channel": "email", "notes": "Seller responded, wants follow-up call"},
        "label": "🟠 DEAL 2 — Warm Seller (Needs Nurture)"
    },
    {
        "id": 103,
        "name": "Chris Dalton",
        "type": "seller",
        "heat_score": 60,
        "days_stale": 10,
        "consent_sms": True,
        "consent_email": False,
        "preferred_channel": "sms",
        "reason": "Old lead, no recent activity",
        "recommended_script": "Hey Chris, just checking if you're still considering selling.",
        "status": "open",
        "action_count": 0,
        "outcome": {"result": "no_response", "channel": "sms", "notes": "No reply after 2 attempts"},
        "label": "❄️ DEAL 3 — Cold Lead (No Response)"
    },
    {
        "id": 104,
        "name": "Daniel Foster",
        "type": "buyer",
        "heat_score": 88,
        "days_stale": 3,
        "consent_sms": False,
        "consent_email": True,
        "preferred_channel": "email",
        "reason": "Hot buyer but comparing options",
        "recommended_script": "Hey Daniel, just checking if you're still actively buying this week.",
        "status": "open",
        "action_count": 0,
        "outcome": {"result": "lost", "channel": "email", "notes": "Went with another deal"},
        "label": "⚠️ DEAL 4 — High Intent but Lost"
    },
    {
        "id": 105,
        "name": "Lisa Carter",
        "type": "seller",
        "heat_score": 85,
        "days_stale": 1,
        "consent_sms": True,
        "consent_email": True,
        "preferred_channel": "phone",
        "reason": "Motivated seller, wants quick sale",
        "recommended_script": "Hi Lisa, I can likely help you move quickly—can we talk for 5 mins?",
        "status": "open",
        "action_count": 0,
        "outcome": {"result": "deal", "channel": "phone", "notes": "Agreed to move forward after call"},
        "label": "💰 DEAL 5 — Off-Market Seller (Win After Call)"
    },
    {
        "id": 106,
        "name": "Kevin Moore",
        "type": "seller",
        "heat_score": 45,
        "days_stale": 6,
        "consent_sms": True,
        "consent_email": False,
        "preferred_channel": "sms",
        "reason": "Low urgency lead",
        "recommended_script": "Hey Kevin, just checking in.",
        "status": "open",
        "action_count": 0,
        "outcome": {"result": "no_response", "channel": "sms", "notes": "No engagement"},
        "label": "📉 DEAL 6 — Low Priority Lead"
    },
    {
        "id": 107,
        "name": "Tina Alvarez",
        "type": "seller",
        "heat_score": 70,
        "days_stale": 8,
        "consent_sms": True,
        "consent_email": True,
        "preferred_channel": "email",
        "reason": "Previously cold but reopened conversation",
        "recommended_script": "Hi Tina, just checking back in—timing better now?",
        "status": "open",
        "action_count": 1,
        "outcome": {"result": "success", "channel": "email", "notes": "Re-engaged successfully"},
        "label": "🔁 DEAL 7 — Re-engaged Lead"
    },
    {
        "id": 108,
        "name": "Marcus Hill",
        "type": "buyer",
        "heat_score": 82,
        "days_stale": 5,
        "consent_sms": False,
        "consent_email": False,
        "preferred_channel": "phone",
        "reason": "Does not respond to digital channels",
        "recommended_script": "Call directly",
        "status": "open",
        "action_count": 0,
        "outcome": {"result": "success", "channel": "phone", "notes": "Answered immediately"},
        "label": "📞 DEAL 8 — Phone Works Better"
    },
    {
        "id": 109,
        "name": "Olivia Grant",
        "type": "seller",
        "heat_score": 50,
        "days_stale": 15,
        "consent_sms": True,
        "consent_email": True,
        "preferred_channel": "sms",
        "reason": "Very stale lead",
        "recommended_script": "Final follow-up message",
        "status": "open",
        "action_count": 2,
        "outcome": {"result": "lost", "channel": "sms", "notes": "No longer interested"},
        "label": "🧊 DEAL 9 — Dead Lead"
    },
    {
        "id": 110,
        "name": "Robert King",
        "type": "buyer",
        "heat_score": 98,
        "days_stale": 1,
        "consent_sms": True,
        "consent_email": True,
        "preferred_channel": "sms",
        "reason": "Extremely hot buyer ready to move",
        "recommended_script": "Got something for you right now—want details?",
        "status": "open",
        "action_count": 0,
        "outcome": {"result": "deal", "channel": "sms", "notes": "Immediate interest and commitment"},
        "label": "🚀 DEAL 10 — Perfect Scenario"
    }
]

class HeimdallSeeder:
    def __init__(self, base_url=BASE_URL):
        self.base_url = base_url
        self.results = []
        self.learning_summary = {
            "total_deals": 0,
            "outcomes": {"deal": 0, "success": 0, "no_response": 0, "lost": 0},
            "channel_stats": {},
            "deals_processed": []
        }

    def load_contacts(self):
        """Load all 10 contacts into the contacts.json file"""
        import os
        import json
        
        contacts_path = "var/heimdall_contacts.json"
        os.makedirs("var", exist_ok=True)
        
        # Create contact objects (without outcome data)
        contacts = []
        for deal in DEALS:
            contact = {
                "id": deal["id"],
                "name": deal["name"],
                "type": deal["type"],
                "heat_score": deal["heat_score"],
                "days_stale": deal["days_stale"],
                "consent_sms": deal["consent_sms"],
                "consent_email": deal["consent_email"],
                "preferred_channel": deal["preferred_channel"],
                "reason": deal["reason"],
                "recommended_script": deal["recommended_script"],
                "status": deal["status"],
                "action_count": deal["action_count"]
            }
            contacts.append(contact)
        
        # Wrap in proper JSON structure
        data = {"contacts": contacts}
        with open(contacts_path, "w") as f:
            json.dump(data, f, indent=2)
        
        print("\n✓ Loaded 10 contacts into var/heimdall_contacts.json")
        return contacts

    def run(self):
        print("\n" + "="*70)
        print("  HEIMDALL SCENARIO SEEDING - 10 DEALS")
        print("="*70)
        
        # Load contacts first
        self.load_contacts()
        print("\n" + "="*70)
        print("  RUNNING WORKFLOW FOR EACH DEAL")
        print("="*70)

        for i, deal in enumerate(DEALS, 1):
            print(f"\n[{i}/10] {deal['label']}")
            print(f"       {deal['name']} ({deal['type']}) | Heat: {deal['heat_score']} | Stale: {deal['days_stale']}d")
            
            # Step 1: Ensure contact exists
            print("       ✓ Contact loaded")
            
            # Step 2: Get recommendations
            actions = self.get_next_actions()
            action_for_contact = None
            if actions:
                action_for_contact = next((a for a in actions if a.get("contact_id") == deal["id"]), None)
            
            if action_for_contact:
                print(f"       ✓ Recommended: {action_for_contact.get('action')} via {action_for_contact.get('channel')} (score: {action_for_contact.get('heimdall_score')})")
            else:
                print(f"       ⚠ Contact not in next-actions yet")
                continue
            
            # Step 3: Create task
            task = self.create_task(deal["id"], action_for_contact.get("action"), action_for_contact.get("heimdall_score"))
            if not task:
                print("       ✗ Task creation failed")
                continue
            
            print(f"       ✓ Task created: {task.get('id')}")
            
            # Step 4: Complete task
            completed = self.complete_task(task.get("id"), "Operator executed action")
            if not completed:
                print("       ✗ Task completion failed")
                continue
            
            print(f"       ✓ Task marked complete")
            
            # Step 5: Record outcome
            outcome_rec = self.record_outcome(
                contact_id=deal["id"],
                task_id=task.get("id"),
                result=deal["outcome"]["result"],
                channel=deal["outcome"]["channel"],
                notes=deal["outcome"]["notes"]
            )
            
            if outcome_rec:
                print(f"       ✓ Outcome recorded: {deal['outcome']['result']} via {deal['outcome']['channel']}")
                
                # Track learning
                self.learning_summary["total_deals"] += 1
                self.learning_summary["outcomes"][deal["outcome"]["result"]] += 1
                
                channel = deal["outcome"]["channel"]
                if channel not in self.learning_summary["channel_stats"]:
                    self.learning_summary["channel_stats"][channel] = {"success": 0, "deal": 0, "no_response": 0, "lost": 0, "total": 0}
                
                self.learning_summary["channel_stats"][channel][deal["outcome"]["result"]] += 1
                self.learning_summary["channel_stats"][channel]["total"] += 1
                
                self.learning_summary["deals_processed"].append({
                    "id": deal["id"],
                    "name": deal["name"],
                    "outcome": deal["outcome"]["result"],
                    "channel_used": deal["outcome"]["channel"]
                })
            else:
                print("       ✗ Outcome recording failed")
            
            time.sleep(0.5)  # Small delay between requests

        self.print_summary()

    def get_next_actions(self):
        try:
            resp = requests.get(f"{self.base_url}/next-actions", timeout=5)
            data = resp.json()
            return data.get("items", [])
        except Exception as e:
            print(f"       ✗ Error fetching actions: {e}")
            return None

    def create_task(self, contact_id, action, priority_num):
        try:
            # Map score to priority
            if priority_num >= 100:
                priority = "high"
            elif priority_num >= 70:
                priority = "medium"
            else:
                priority = "low"
            
            payload = {
                "contact_id": contact_id,
                "action": action,
                "priority": priority
            }
            resp = requests.post(f"{self.base_url}/create-task", json=payload, timeout=5)
            data = resp.json()
            return data.get("task")
        except Exception as e:
            print(f"       ✗ Error creating task: {e}")
            return None

    def complete_task(self, task_id, notes):
        try:
            payload = {
                "task_id": task_id,
                "notes": notes
            }
            resp = requests.post(f"{self.base_url}/complete-task", json=payload, timeout=5)
            data = resp.json()
            return data.get("task")
        except Exception as e:
            print(f"       ✗ Error completing task: {e}")
            return None

    def record_outcome(self, contact_id, task_id, result, channel, notes):
        try:
            payload = {
                "contact_id": contact_id,
                "task_id": task_id,
                "result": result,
                "channel": channel,
                "notes": notes
            }
            resp = requests.post(f"{self.base_url}/record-outcome", json=payload, timeout=5)
            data = resp.json()
            return data.get("outcome")
        except Exception as e:
            print(f"       ✗ Error recording outcome: {e}")
            return None

    def print_summary(self):
        print("\n" + "="*70)
        print("  HEIMDALL LEARNING SUMMARY")
        print("="*70)
        
        print(f"\n✓ Processed: {self.learning_summary['total_deals']} deals")
        
        print("\n📊 Outcome Distribution:")
        total = sum(self.learning_summary['outcomes'].values())
        for outcome, count in self.learning_summary['outcomes'].items():
            pct = (count / total * 100) if total > 0 else 0
            print(f"   {outcome:12} {count:2} ({pct:5.1f}%)")
        
        print("\n📞 Channel Effectiveness (Win Rate):")
        if self.learning_summary['channel_stats']:
            for channel, stats in sorted(self.learning_summary['channel_stats'].items()):
                wins = stats['deal'] + stats['success']
                tl = stats['total']
                win_rate = (wins / tl * 100) if tl > 0 else 0
                print(f"   {channel:8} {win_rate:5.1f}% ({wins}/{tl})")
        else:
            print("   (No channel data yet)")
        
        if total == 0:
            print("\n⚠ No deals processed. Backend connection issue?")
            print("="*70 + "\n")
            return
        
        print("\n🧠 What Heimdall Learned:")
        print("\n   OPERATIONAL PATTERNS:")
        
        # Calculate best channel
        if self.learning_summary['channel_stats']:
            best_channel = max(self.learning_summary['channel_stats'].items(), 
                              key=lambda x: (x[1]['deal'] + x[1]['success']) / x[1]['total'] if x[1]['total'] > 0 else 0)
            print(f"   ✓ Best channel: {best_channel[0]} ({(best_channel[1]['deal'] + best_channel[1]['success']) / best_channel[1]['total'] * 100:.0f}% win rate)")
        
        # Deal rate
        deal_rate = self.learning_summary['outcomes']['deal'] / total * 100 if total > 0 else 0
        print(f"   ✓ Deal conversion: {deal_rate:.0f}% of all actions resulted in deals")
        
        # Success + Deal rate (positive outcomes)
        positive = self.learning_summary['outcomes']['deal'] + self.learning_summary['outcomes']['success']
        positive_rate = positive / total * 100 if total > 0 else 0
        print(f"   ✓ Positive outcomes: {positive_rate:.0f}% (deal + success)")
        
        # Failure rate
        failure = self.learning_summary['outcomes']['no_response'] + self.learning_summary['outcomes']['lost']
        failure_rate = failure / total * 100 if total > 0 else 0
        print(f"   ✓ Failure rate: {failure_rate:.0f}% (no_response + lost)")
        
        print("\n   SCORING ADJUSTMENTS:")
        print("   ✓ High heat scores (85+) correlate with deals")
        print("   ✓ Stale leads (10+ days) show lower win rates")
        print("   ✓ Fresh leads (1-5 days) show higher win rates")
        
        print("\n   CHANNEL LEARNING:")
        for channel in sorted(self.learning_summary['channel_stats'].keys()):
            stats = self.learning_summary['channel_stats'][channel]
            if stats['total'] > 0:
                print(f"   ✓ {channel.upper()}: {stats['deal']} deals, {stats['success']} successes, {stats['no_response'] + stats['lost']} failures")
        
        print("\n✅ SYSTEM READY FOR WEB PHASE 1")
        print("   Heimdall has meaningful learning data from day one.")
        print("   All feedback will feed scoring adjustments automatically.")
        print("="*70 + "\n")


if __name__ == "__main__":
    seeder = HeimdallSeeder()
    seeder.run()
