import os
import time
from typing import List, Dict, Any

import pandas as pd
import streamlit as st
from google.cloud import firestore


# ----------------------------
# Firestore helper
# ----------------------------
class AuditLogViewer:
    def __init__(self, project_id: str | None = None, collection_name: str = "audit_events"):
        self.project_id = project_id or os.getenv("GOOGLE_CLOUD_PROJECT") or os.getenv("PROJECT_ID")
        self.collection_name = collection_name
        self.db = firestore.Client(project=self.project_id)

    def fetch_logs(self, patient_id: str = "", limit: int = 50) -> List[Dict[str, Any]]:
        docs = self.db.collection(self.collection_name).stream()

        records = []
        for doc in docs:
            data = doc.to_dict()
            data["document_id"] = doc.id
            records.append(data)

        # optional patient filter
        if patient_id.strip():
            records = [
                r for r in records
                if str(r.get("patient_id", "")).strip() == patient_id.strip()
            ]

        # sort latest first by timestamp if present
        records.sort(key=lambda x: str(x.get("timestamp", "")), reverse=True)

        return records[:limit]


# ----------------------------
# Streamlit app
# ----------------------------
st.set_page_config(page_title="ADPO Audit Dashboard", layout="wide")

st.title("ADPO Audit Dashboard")
st.caption("View clinical audit trail from Firestore")

project_id = os.getenv("GOOGLE_CLOUD_PROJECT") or os.getenv("PROJECT_ID") or "adpo-healthcare-agent"

viewer = AuditLogViewer(project_id=project_id)

with st.sidebar:
    st.header("Filters")

    patient_filter = st.text_input("Patient ID", value="")

    limit = st.slider("Max rows", min_value=5, max_value=200, value=50, step=5)

    auto_refresh = st.checkbox("Auto refresh every 10 sec", value=False)

    refresh_now = st.button("Refresh now")

# auto-refresh handling
if auto_refresh:
    time.sleep(1)

logs = viewer.fetch_logs(patient_id=patient_filter, limit=limit)

st.subheader("Audit Events")

if not logs:
    st.warning("No audit records found.")
else:
    # flatten useful top-level fields for table
    table_rows = []
    for row in logs:
        table_rows.append({
            "document_id": row.get("document_id"),
            "timestamp": row.get("timestamp"),
            "patient_id": row.get("patient_id"),
            "loinc_code": row.get("loinc_code"),
            "observation_id": row.get("observation_id"),
            "action": row.get("action", row.get("event_type")),
            "order_id": row.get("order_id", row.get("details")),
            "decision_summary": (
                row.get("decision", {}).get("reason")
                if isinstance(row.get("decision"), dict)
                else row.get("decision")
            ),
        })

    df = pd.DataFrame(table_rows)
    st.dataframe(df, use_container_width=True)

    st.subheader("Selected Record Details")

    selected_doc_id = st.selectbox(
        "Choose a document",
        options=[row["document_id"] for row in table_rows]
    )

    selected = next((r for r in logs if r.get("document_id") == selected_doc_id), None)
    if selected:
        st.json(selected)

if auto_refresh:
    st.rerun()