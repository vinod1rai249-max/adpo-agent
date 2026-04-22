import json
from typing import Any, Dict

from google.adk.agents import Agent

from adpo_agent.audit import AuditLogger
from adpo_agent.fhir_client import FHIRClient
from adpo_agent.lab_rules import ReflexRuleEngine


class ADPOOrchestrator:
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
    instruction="Clinical reflex orchestration agent",
    tools=[check_lab_reflex_rules, create_reflex_order],
)