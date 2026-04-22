from typing import Optional, Dict, Any
from google.cloud import firestore


class ReflexRuleEngine:
    """
    Handles fetching reflex rules from Firestore
    and evaluating lab results against those rules.
    """

    def __init__(self, collection_name: str = "reflex_rules") -> None:
        self.db = firestore.Client()
        self.collection_name = collection_name

    def get_reflex_rule(self, loinc_code: str, gender: str, age: int) -> Optional[Dict[str, Any]]:
        """
        Find a matching reflex rule based on:
        - LOINC code
        - patient gender
        - patient age
        """
        rules_ref = self.db.collection(self.collection_name)
        docs = rules_ref.where("loinc_code", "==", loinc_code).stream()

        for doc in docs:
            rule = doc.to_dict()

            gender_match = rule.get("gender", "ANY") in [gender, "ANY"]
            age_match = rule.get("age_min", 0) <= age <= rule.get("age_max", 120)

            if gender_match and age_match:
                return rule

        return None

    def _check_threshold(self, value: float, threshold: float, operator: str) -> bool:
        """
        Internal helper method to evaluate threshold logic.
        """
        operations = {
            "gt": value > threshold,
            "lt": value < threshold,
            "gte": value >= threshold,
            "lte": value <= threshold,
        }
        return operations.get(operator, False)

    def evaluate_lab_result(
        self,
        loinc_code: str,
        value: float,
        unit: str,
        gender: str,
        age: int
    ) -> Dict[str, Any]:
        """
        Evaluate a lab result against a matching reflex rule.
        """
        rule = self.get_reflex_rule(loinc_code, gender, age)

        if not rule:
            return {
                "reflex_needed": False,
                "reason": f"No reflex rule found for LOINC {loinc_code}",
            }

        threshold = rule["threshold"]
        operator = rule["operator"]
        triggered = self._check_threshold(value, threshold, operator)

        if triggered:
            reason = (
                f"REFLEX TRIGGERED: {rule.get('analyte_name')} {value} {unit} "
                f"{'exceeds' if operator in ['gt', 'gte'] else 'is below'} "
                f"threshold {threshold} {unit}"
            )
        else:
            reason = "Within normal range - no reflex needed"

        return {
            "reflex_needed": triggered,
            "loinc_code": loinc_code,
            "observed_value": value,
            "unit": unit,
            "threshold": threshold,
            "reflex_order_code": rule.get("reflex_order_code", ""),
            "reflex_test_name": rule.get("reflex_test_name", ""),
            "priority": rule.get("priority", "ROUTINE"),
            "clinical_guideline": rule.get("guideline_source", ""),
            "reason": reason,
        }