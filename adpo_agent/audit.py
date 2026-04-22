from datetime import datetime, timezone
from typing import Any, Dict, Optional

from google.cloud import firestore


class AuditLogger:
    """
    Writes audit events into Firestore.
    """

    def __init__(self, collection_name: str = "audit_events") -> None:
        self.db = firestore.Client()
        self.collection_name = collection_name

    def build_event(
        self,
        patient_id: str,
        event_type: str,
        decision: str,
        details: Optional[str] = None,
    ) -> Dict[str, Any]:
        return {
            "patient_id": patient_id,
            "event_type": event_type,
            "decision": decision,
            "details": details or "",
            "timestamp": datetime.now(timezone.utc).isoformat(),
        }

    def write_event(
        self,
        patient_id: str,
        event_type: str,
        decision: str,
        details: Optional[str] = None,
    ) -> str:
        event = self.build_event(patient_id, event_type, decision, details)
        doc_ref = self.db.collection(self.collection_name).document()
        doc_ref.set(event)
        return doc_ref.id