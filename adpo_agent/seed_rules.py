from google.cloud import firestore


class ReflexRuleSeeder:
    """
    Seeds Firestore with predefined reflex rules.
    """

    def __init__(self, collection_name: str = "reflex_rules") -> None:
        self.db = firestore.Client()
        self.collection_name = collection_name
        self.rules = [
            {
                "loinc_code": "2857-1",
                "analyte_name": "PSA Total",
                "gender": "male",
                "age_min": 40,
                "age_max": 120,
                "operator": "gt",
                "threshold": 4.0,
                "expected_unit": "ng/mL",
                "reflex_order_code": "10508-0",
                "reflex_test_name": "PSA Free/Total Ratio",
                "priority": "ROUTINE",
                "guideline_source": "AUA PSA Guidelines 2023",
            },
            {
                "loinc_code": "4548-4",
                "analyte_name": "Hemoglobin A1c",
                "gender": "ANY",
                "age_min": 18,
                "age_max": 120,
                "operator": "gt",
                "threshold": 9.0,
                "expected_unit": "%",
                "reflex_order_code": "14647-2",
                "reflex_test_name": "Glucose Tolerance Test",
                "priority": "ROUTINE",
                "guideline_source": "ADA Standards of Care 2024",
            },
            {
                "loinc_code": "34714-6",
                "analyte_name": "INR (Coagulation)",
                "gender": "ANY",
                "age_min": 0,
                "age_max": 120,
                "operator": "gt",
                "threshold": 3.5,
                "expected_unit": "INR",
                "reflex_order_code": "5895-7",
                "reflex_test_name": "PT/PTT Panel with Mixing Study",
                "priority": "STAT",
                "guideline_source": "ASH Anticoagulation Guidelines",
            },
            {
                "loinc_code": "62238-1",
                "analyte_name": "eGFR (Kidney Function)",
                "gender": "ANY",
                "age_min": 18,
                "age_max": 120,
                "operator": "lt",
                "threshold": 30.0,
                "expected_unit": "mL/min/1.73m2",
                "reflex_order_code": "77147-7",
                "reflex_test_name": "Urine Albumin-Creatinine Ratio",
                "priority": "ROUTINE",
                "guideline_source": "KDIGO CKD Guidelines 2024",
            },
        ]

    def seed(self) -> None:
        collection = self.db.collection(self.collection_name)

        for rule in self.rules:
            doc_id = f"{rule['loinc_code']}_{rule['gender']}"
            collection.document(doc_id).set(rule)
            print(f"Seeded rule: {rule['analyte_name']} ({rule['loinc_code']})")

        print(f"Done. {len(self.rules)} rules loaded into Firestore.")


if __name__ == "__main__":
    seeder = ReflexRuleSeeder()
    seeder.seed()