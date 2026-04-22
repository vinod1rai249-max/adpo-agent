import base64
import json
import os
from typing import List, Dict, Any

import pandas as pd
import requests
import streamlit as st
from google.cloud import firestore


# ---------------------------------
# Config
# ---------------------------------
DEFAULT_PROJECT_ID = os.getenv("GOOGLE_CLOUD_PROJECT") or os.getenv("PROJECT_ID") or "adpo-healthcare-agent"
DEFAULT_API_BASE_URL = os.getenv("API_BASE_URL") or "http://127.0.0.1:8000"


# ---------------------------------
# Firestore helper
# ---------------------------------
class AuditLogViewer:
    def __init__(self, project_id: str, collection_name: str = "audit_events"):
        self.project_id = project_id
        self.collection_name = collection_name
        self.db = firestore.Client(project=self.project_id)

    def fetch_logs(self, patient_id: str = "", limit: int = 50) -> List[Dict[str, Any]]:
        docs = self.db.collection(self.collection_name).stream()

        records = []
        for doc in docs:
            data = doc.to_dict()
            data["document_id"] = doc.id
            records.append(data)

        if patient_id.strip():
            records = [
                r for r in records
                if str(r.get("patient_id", "")).strip() == patient_id.strip()
            ]

        records.sort(key=lambda x: str(x.get("timestamp", "")), reverse=True)
        return records[:limit]


# ---------------------------------
# UI helpers
# ---------------------------------
def action_color(action: str) -> str:
    if action == "AUTO_ORDER_CREATED" or action == "REFLEX_ORDER_CREATED":
        return "#d1fae5"
    if action == "HITL_ESCALATION":
        return "#fee2e2"
    if action == "NO_REFLEX":
        return "#dbeafe"
    return "#f3f4f6"


def action_emoji(action: str) -> str:
    if action == "AUTO_ORDER_CREATED" or action == "REFLEX_ORDER_CREATED":
        return "🟢"
    if action == "HITL_ESCALATION":
        return "🔴"
    if action == "NO_REFLEX":
        return "🔵"
    return "⚪"


def render_status_card(title: str, value: str, bg_color: str):
    st.markdown(
        f"""
        <div style="
            background-color:{bg_color};
            padding:16px;
            border-radius:16px;
            border:1px solid #e5e7eb;
            box-shadow:0 1px 6px rgba(0,0,0,0.06);
            margin-bottom:8px;
        ">
            <div style="font-size:14px;color:#374151;">{title}</div>
            <div style="font-size:22px;font-weight:700;color:#111827;">{value}</div>
        </div>
        """,
        unsafe_allow_html=True,
    )


def flatten_logs(logs: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    rows = []

    for row in logs:
        decision = row.get("decision", {})
        if isinstance(decision, dict):
            decision_summary = decision.get("reason", "")
            priority = decision.get("priority", "")
            reflex_needed = decision.get("reflex_needed", "")
        else:
            decision_summary = str(decision)
            priority = ""
            reflex_needed = ""

        action = row.get("action", row.get("event_type", "UNKNOWN"))

        rows.append({
            "document_id": row.get("document_id"),
            "timestamp": row.get("timestamp"),
            "patient_id": row.get("patient_id"),
            "loinc_code": row.get("loinc_code"),
            "action": action,
            "priority": priority,
            "reflex_needed": reflex_needed,
            "order_id": row.get("order_id", row.get("details")),
            "decision_summary": decision_summary,
        })

    return rows


# ---------------------------------
# Page setup
# ---------------------------------
st.set_page_config(page_title="ADPO Premium Dashboard", layout="wide")

st.markdown(
    """
    <style>
        .main > div {
            padding-top: 1rem;
        }
        div[data-testid="stMetricValue"] {
            font-size: 1.5rem;
        }
    </style>
    """,
    unsafe_allow_html=True,
)

st.title("ADPO Clinical Reflex Dashboard")
st.caption("Audit visibility, decision intelligence, and live testing")

viewer = AuditLogViewer(project_id=DEFAULT_PROJECT_ID)

# ---------------------------------
# Sidebar
# ---------------------------------
with st.sidebar:
    st.header("Dashboard Controls")

    api_base_url = st.text_input("API Base URL", value=DEFAULT_API_BASE_URL)
    patient_filter = st.text_input("Filter by Patient ID", value="")
    limit = st.slider("Max records", min_value=5, max_value=200, value=50, step=5)

    if st.button("Refresh dashboard"):
        st.rerun()

# ---------------------------------
# Load data
# ---------------------------------
logs = viewer.fetch_logs(patient_id=patient_filter, limit=limit)
table_rows = flatten_logs(logs)

# ---------------------------------
# Top summary
# ---------------------------------
st.subheader("Summary")

total_events = len(table_rows)
auto_orders = sum(1 for r in table_rows if r["action"] in ["AUTO_ORDER_CREATED", "REFLEX_ORDER_CREATED"])
hitl_count = sum(1 for r in table_rows if r["action"] == "HITL_ESCALATION")
no_reflex_count = sum(1 for r in table_rows if r["action"] == "NO_REFLEX")

c1, c2, c3, c4 = st.columns(4)
with c1:
    render_status_card("Total Events", str(total_events), "#f3f4f6")
with c2:
    render_status_card("Auto Orders", str(auto_orders), "#d1fae5")
with c3:
    render_status_card("HITL Escalations", str(hitl_count), "#fee2e2")
with c4:
    render_status_card("No Reflex", str(no_reflex_count), "#dbeafe")

tab1, tab2 = st.tabs(["Audit Explorer", "Live API Tester"])

# ---------------------------------
# TAB 1 - Audit Explorer
# ---------------------------------
with tab1:
    st.subheader("Audit Event Table")

    if not table_rows:
        st.warning("No audit records found.")
    else:
        display_df = pd.DataFrame(table_rows)
        st.dataframe(display_df, use_container_width=True)

        st.subheader("Record Detail View")

        selected_doc_id = st.selectbox(
            "Choose a document",
            options=[r["document_id"] for r in table_rows]
        )

        selected = next((r for r in logs if r.get("document_id") == selected_doc_id), None)

        if selected:
            action = selected.get("action", selected.get("event_type", "UNKNOWN"))
            decision = selected.get("decision", {})

            if isinstance(decision, dict):
                priority = decision.get("priority", "N/A")
                reason = decision.get("reason", "N/A")
                reflex_needed = str(decision.get("reflex_needed", "N/A"))
            else:
                priority = "N/A"
                reason = str(decision)
                reflex_needed = "N/A"

            d1, d2, d3, d4 = st.columns(4)
            with d1:
                render_status_card("Action", f"{action_emoji(action)} {action}", action_color(action))
            with d2:
                render_status_card("Priority", str(priority), "#fef3c7")
            with d3:
                render_status_card("Reflex Needed", str(reflex_needed), "#e0f2fe")
            with d4:
                render_status_card("Patient ID", str(selected.get("patient_id", "N/A")), "#f3f4f6")

            st.markdown("### Decision Reason")
            st.info(reason)

            if "explanation" in selected and selected["explanation"]:
                st.markdown("### AI Explanation")
                st.success(selected["explanation"])

            st.markdown("### Full Audit JSON")
            st.json(selected)

# ---------------------------------
# TAB 2 - Live API Tester
# ---------------------------------
with tab2:
    st.subheader("Trigger Clinical Scenarios")

    sample_case = st.selectbox(
        "Choose sample case",
        ["PSA Normal", "PSA High", "INR Critical", "Custom"]
    )

    if sample_case == "PSA Normal":
        default_values = {
            "patient_id": "10c1c74f-770d-4808-b343-ff7cec13730e",
            "loinc_code": "2857-1",
            "value": 2.1,
            "unit": "ng/mL",
            "age": 66,
            "gender": "male",
            "observation_id": "a84085a1-876e-419a-8e27-5c78412be571",
        }
    elif sample_case == "PSA High":
        default_values = {
            "patient_id": "21f9c599-3ac0-41f5-b5b9-5c290185b6b9",
            "loinc_code": "2857-1",
            "value": 6.8,
            "unit": "ng/mL",
            "age": 66,
            "gender": "male",
            "observation_id": "d008e9d7-1e63-4874-b95b-5ff7ed4e3331",
        }
    elif sample_case == "INR Critical":
        default_values = {
            "patient_id": "572f0997-ebee-4b20-8155-d16e62272b54",
            "loinc_code": "34714-6",
            "value": 5.9,
            "unit": "INR",
            "age": 77,
            "gender": "female",
            "observation_id": "bf5087d9-df20-4670-9201-1246506bee79",
        }
    else:
        default_values = {
            "patient_id": "",
            "loinc_code": "",
            "value": 0.0,
            "unit": "",
            "age": 0,
            "gender": "male",
            "observation_id": "",
        }

    col1, col2 = st.columns(2)

    with col1:
        patient_id = st.text_input("Patient ID", value=default_values["patient_id"])
        loinc_code = st.text_input("LOINC Code", value=default_values["loinc_code"])
        value = st.number_input("Result Value", value=float(default_values["value"]))
        unit = st.text_input("Unit", value=default_values["unit"])

    with col2:
        age = st.number_input("Age", value=int(default_values["age"]))
        gender = st.selectbox(
            "Gender",
            options=["male", "female"],
            index=0 if default_values["gender"] == "male" else 1
        )
        observation_id = st.text_input("Observation ID", value=default_values["observation_id"])

    if st.button("Submit Scenario"):
        payload_data = {
            "patient_id": patient_id,
            "loinc_code": loinc_code,
            "value": value,
            "unit": unit,
            "age": age,
            "gender": gender,
            "observation_id": observation_id,
        }

        encoded = base64.b64encode(json.dumps(payload_data).encode("utf-8")).decode("utf-8")

        body = {
            "message": {
                "data": encoded
            }
        }

        try:
            response = requests.post(
                f"{api_base_url}/process-lab-result",
                json=body,
                timeout=90,
            )

            response_json = response.json()

            st.markdown("### API Status")
            st.write(response.status_code)

            if response.ok:
                action_text = response_json.get("response", "Processed")
                st.success(action_text)

                if "explanation" in response_json and response_json["explanation"]:
                    st.markdown("### AI Explanation")
                    st.info(response_json["explanation"])

                if "decision" in response_json:
                    decision = response_json["decision"]
                    st.markdown("### Decision")
                    st.json(decision)

                if "order_result" in response_json:
                    st.markdown("### Order Result")
                    st.json(response_json["order_result"])

                if "audit_id" in response_json:
                    st.markdown("### Audit ID")
                    st.code(response_json["audit_id"])

            else:
                st.error("API returned an error")
                st.json(response_json)

        except Exception as e:
            st.error(f"Request failed: {str(e)}")