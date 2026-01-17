"""
Messaging service: templates CRUD, email/SMS senders, and user-preferences-aware notifications.
"""
from typing import Optional, Dict, Any, List, cast
from sqlalchemy.orm import Session
from app.messaging.models import EmailTemplate
from app.messaging.schemas import EmailTemplateCreate
from app.messaging.email_utils import send_email
from app.messaging.sms_utils import send_sms
from app.users.service import UserProfileService


class MessagingService:
    def __init__(self, db: Session):
        self.db = db

    # Templates
    def create_template(self, data: EmailTemplateCreate) -> EmailTemplate:
        existing = self.db.query(EmailTemplate).filter(EmailTemplate.template_name == data.template_name).first()
        if existing:
            raise ValueError(f"Template '{data.template_name}' already exists")
        tmpl = EmailTemplate(**data.model_dump())
        self.db.add(tmpl)
        self.db.commit()
        self.db.refresh(tmpl)
        return tmpl

    def get_template(self, name: str) -> Optional[EmailTemplate]:
        return self.db.query(EmailTemplate).filter(EmailTemplate.template_name == name).first()

    def list_templates(self) -> List[EmailTemplate]:
        return self.db.query(EmailTemplate).all()

    def delete_template(self, template_id: int) -> bool:
        tmpl = self.db.query(EmailTemplate).filter(EmailTemplate.template_id == template_id).first()
        if not tmpl:
            return False
        self.db.delete(tmpl)
        self.db.commit()
        return True

    # Sending helpers
    def render_template(self, name: str, variables: Dict[str, Any]) -> Optional[Dict[str, str]]:
        tmpl = self.get_template(name)
        if not tmpl:
            return None
        subject = tmpl.subject.format(**variables)
        body = tmpl.body.format(**variables)
        return {"subject": subject, "body": body}

    def send_email_raw(self, to: str, subject: str, body: str, html: bool = False) -> Dict[str, str]:
        return send_email(subject, to, body, html=html)

    def send_sms_raw(self, to: str, message: str) -> Dict[str, str]:
        return send_sms(to, message)

    def send_with_template(self, template_name: str, to: Optional[str], user_id: Optional[int], variables: Dict[str, Any]) -> Dict[str, str]:
        # Resolve email address
        if not to and user_id is not None:
            user_svc = UserProfileService(self.db)
            profile = user_svc.get_profile(user_id)
            if not profile:
                return {"status": "failure", "message": "User not found"}
            to = cast(Optional[str], (str(getattr(profile, "email", "")) or None))
        if not to:
            return {"status": "failure", "message": "Recipient email not provided"}

        rendered = self.render_template(template_name, variables)
        if not rendered:
            return {"status": "failure", "message": "Template not found"}
        return self.send_email_raw(to, rendered["subject"], rendered["body"]) 

    def notify_user_by_preferences(self, user_id: int, subject: str, body: str, sms_message: Optional[str] = None) -> Dict[str, Any]:
        user_svc = UserProfileService(self.db)
        profile = user_svc.get_profile(user_id)
        if not profile:
            return {"status": "failure", "message": "User not found"}
        prefs = user_svc.get_preferences(user_id)

        # Basic preference interpretation from existing model
        # email allowed if 'email' in notification_preferences; sms if 'sms' in notification_preferences
        notify_pref_val = ""
        if prefs is not None:
            pref_attr = getattr(prefs, "notification_preferences", None)
            if isinstance(pref_attr, str):
                notify_pref_val = pref_attr
            elif pref_attr is not None:
                try:
                    notify_pref_val = str(pref_attr)
                except Exception:
                    notify_pref_val = ""
        notify_pref = notify_pref_val.lower()
        allow_email = "email" in notify_pref or notify_pref == ""  # default allow email
        allow_sms = "sms" in notify_pref

        results: Dict[str, Any] = {"email": None, "sms": None}
        if allow_email:
            email_addr = str(getattr(profile, "email", ""))
            if email_addr:
                results["email"] = self.send_email_raw(email_addr, subject, body)
        if allow_sms and sms_message:
            phone_val = getattr(profile, "phone_number", None)
            phone_number = str(phone_val) if isinstance(phone_val, str) else ""
            if phone_number:
                results["sms"] = self.send_sms_raw(phone_number, sms_message)

        # No channel allowed or applicable
        if not results["email"] and not results["sms"]:
            return {"status": "failure", "message": "No notification channel allowed or available"}

        return {"status": "success", "results": results}
