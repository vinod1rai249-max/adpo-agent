import json
from typing import Any, Dict

from google.adk.agents import Agent

from adpo_agent.audit import AuditLogger
from adpo_agent.fhir_client import FHIRClient
from adpo_agent.lab_rules import ReflexRuleEngine


class ADPOOrchestrator:
    """
    Main business orchestrator for evaluating lab results
    and creating reflex orders when needed.
    """

    def __init__(self) -> None:
        self.rule_engine = ReflexRuleEngine()
        self.fhir_client = FHIRClient()
        self.audit_logger = AuditLogger()

    def check_lab_reflex_rules(
        self,
        patient_id: str,
        loinc_code: str,
        result_value: float,
        result_unit: str,
        patient_gender: str,
        patient_age: int,
    ) -> Dict[str, Any]:
        decision = self.rule_engine.evaluate_lab_result(
            loinc_code=loinc_code,
            value=result_value,
            unit=result_unit,
            gender=patient_gender,
            age=patient_age,
        )
        decision["patient_id"] = patient_id
        print(f"[ADPO] Rule evaluation: {json.dumps(decision, indent=2)}")
        return decision

    def create_reflex_order(
        self,
        patient_id: str,
        order_code: str,
        order_name: str,
        source_observation_id: str,
        priority: str = "routine",
    ) -> Dict[str, Any]:
        result = self.fhir_client.create_service_request(
            patient_id=patient_id,
            order_code=order_code,
            order_name=order_name,
            source_obs_id=source_observation_id,
            priority=priority,
        )

        self.audit_logger.write_event(
            patient_id=patient_id,
            event_type="REFLEX_ORDER_CREATED",
            decision="AUTO_APPROVED",
            details=order_code,
        )
        return result


orchestrator = ADPOOrchestrator()


def check_lab_reflex_rules(
    patient_id: str,
    loinc_code: str,
    result_value: float,
    result_unit: str,
    patient_gender: str,
    patient_age: int,
) -> Dict[str, Any]:
    return orchestrator.check_lab_reflex_rules(
        patient_id=patient_id,
        loinc_code=loinc_code,
        result_value=result_value,
        result_unit=result_unit,
        patient_gender=patient_gender,
        patient_age=patient_age,
    )


def create_reflex_order(
    patient_id: str,
    order_code: str,
    order_name: str,
    source_observation_id: str,
    priority: str = "routine",
) -> Dict[str, Any]:
    return orchestrator.create_reflex_order(
        patient_id=patient_id,
        order_code=order_code,
        order_name=order_name,
        source_observation_id=source_observation_id,
        priority=priority,
    )


root_agent = Agent(
    name="ADPO_Orchestrator",
    model="gemini-1.5-pro-002",
    instruction="""
You are a Diagnostic Path Orchestrator for a clinical laboratory.

Your job is to evaluate lab results and trigger appropriate follow-up tests.

EXACT STEPS TO FOLLOW:
1. Call check_lab_reflex_rules with the provided patient data.
2. If reflex_needed = false: respond 'No reflex required. Reason: [reason]'
3. If reflex_needed = true AND priority = STAT:
   - Respond 'URGENT: HITL review required for [patient_id]'
   - Do NOT create an order automatically
4. If reflex_needed = true AND priority = ROUTINE:
   - Call create_reflex_order with the reflex_order_code and reflex_test_name
   - Confirm the order was created with the FHIR resource ID

SAFETY RULES:
- Never infer or guess numeric values.
- Never create an order without a valid LOINC code.
- If any parameter is missing, respond 'MISSING DATA — HITL required'
- Always include the source Observation ID in every order you create.
""",
    tools=[check_lab_reflex_rules, create_reflex_order],
)