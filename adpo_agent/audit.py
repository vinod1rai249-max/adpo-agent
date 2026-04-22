import os
from datetime import datetime, timezone
from typing import Any, Dict, Optional

from google.cloud import firestore


class AuditLogger:
    def __init__(self, collection_name: str = "audit_events", project_id: Optional[str] = None) -> None:
        self.project_id = project_id or os.getenv("GOOGLE_CLOUD_PROJECT") or os.getenv("PROJECT_ID")
        self.db = firestore.Client(project=self.project_id)
        self.collection_name = collection_name

    def write_event(self, event: Dict[str, Any]) -> str:
        event["timestamp"] = datetime.now(timezone.utc).isoformat()
        doc_ref = self.db.collection(self.collection_name).document()
        doc_ref.set(event)
        return doc_ref.id

    def write_decision_event(
        self,
        patient_id: str,
        loinc_code: str,
        observation_id: str,
        decision: Dict[str, Any],
        action: str,
        order_id: Optional[str] = None,
    ) -> str:
        event = {
            "patient_id": patient_id,
            "loinc_code": loinc_code,
            "observation_id": observation_id,
            "action": action,
            "order_id": order_id,
            "decision": decision,
        }
        return self.write_event(event)