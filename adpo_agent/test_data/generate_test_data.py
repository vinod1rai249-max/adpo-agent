import json
from datetime import datetime, timezone
from typing import Any, Dict, List


class TestDataGenerator:
    def __init__(self) -> None:
        self.test_patients: List[Dict[str, Any]] = []
        self.test_observations: List[Dict[str, Any]] = []

    def make_patient(
        self,
        patient_id: str,
        given: str,
        family: str,
        gender: str,
        birth_year: int,
    ) -> Dict[str, Any]:
        return {
            "resourceType": "Patient",
            "id": patient_id,
            "name": [
                {
                    "use": "official",
                    "given": [given],
                    "family": family,
                }
            ],
            "gender": gender,
            "birthDate": f"{birth_year}-06-15",
            "identifier": [
                {
                    "system": "urn:adpo:test-patients",
                    "value": patient_id,
                }
            ],
        }

    def make_observation(
        self,
        obs_id: str,
        patient_id: str,
        loinc_code: str,
        display: str,
        value: float,
        unit: str,
        unit_code: str,
    ) -> Dict[str, Any]:
        return {
            "resourceType": "Observation",
            "id": obs_id,
            "status": "final",
            "category": [
                {
                    "coding": [
                        {
                            "system": "http://terminology.hl7.org/CodeSystem/observation-category",
                            "code": "laboratory",
                            "display": "Laboratory",
                        }
                    ]
                }
            ],
            "code": {
                "coding": [
                    {
                        "system": "http://loinc.org",
                        "code": loinc_code,
                        "display": display,
                    }
                ]
            },
            "subject": {"reference": f"Patient/{patient_id}"},
            "effectiveDateTime": datetime.now(timezone.utc).isoformat(),
            "valueQuantity": {
                "value": value,
                "unit": unit,
                "system": "http://unitsofmeasure.org",
                "code": unit_code,
            },
            "identifier": [
                {
                    "system": "urn:adpo:observations",
                    "value": obs_id,
                }
            ],
        }

    def generate(self) -> None:
        p1_id = "test-patient-psa-normal"
        self.test_patients.append(self.make_patient(p1_id, "James", "Wilson", "male", 1960))
        self.test_observations.append(
            self.make_observation("obs-psa-normal", p1_id, "2857-1", "PSA Total", 2.1, "ng/mL", "ng/mL")
        )

        p2_id = "test-patient-psa-high"
        self.test_patients.append(self.make_patient(p2_id, "Robert", "Johnson", "male", 1958))
        self.test_observations.append(
            self.make_observation("obs-psa-high", p2_id, "2857-1", "PSA Total", 6.8, "ng/mL", "ng/mL")
        )

        p3_id = "test-patient-hba1c-normal"
        self.test_patients.append(self.make_patient(p3_id, "Maria", "Garcia", "female", 1975))
        self.test_observations.append(
            self.make_observation("obs-hba1c-normal", p3_id, "4548-4", "HbA1c", 7.2, "%", "%")
        )

        p4_id = "test-patient-hba1c-high"
        self.test_patients.append(self.make_patient(p4_id, "Linda", "Smith", "female", 1969))
        self.test_observations.append(
            self.make_observation("obs-hba1c-high", p4_id, "4548-4", "HbA1c", 11.3, "%", "%")
        )

        p5_id = "test-patient-inr-normal"
        self.test_patients.append(self.make_patient(p5_id, "David", "Brown", "male", 1952))
        self.test_observations.append(
            self.make_observation("obs-inr-normal", p5_id, "34714-6", "INR", 2.1, "INR", "{INR}")
        )

        p6_id = "test-patient-inr-critical"
        self.test_patients.append(self.make_patient(p6_id, "Barbara", "Taylor", "female", 1948))
        self.test_observations.append(
            self.make_observation("obs-inr-critical", p6_id, "34714-6", "INR", 5.9, "INR", "{INR}")
        )

        p7_id = "test-patient-egfr-normal"
        self.test_patients.append(self.make_patient(p7_id, "Susan", "Anderson", "female", 1965))
        self.test_observations.append(
            self.make_observation(
                "obs-egfr-normal",
                p7_id,
                "62238-1",
                "eGFR",
                72.0,
                "mL/min/1.73m2",
                "mL/min/{1.73_m2}",
            )
        )

        p8_id = "test-patient-egfr-low"
        self.test_patients.append(self.make_patient(p8_id, "Michael", "Martinez", "male", 1950))
        self.test_observations.append(
            self.make_observation(
                "obs-egfr-low",
                p8_id,
                "62238-1",
                "eGFR",
                18.0,
                "mL/min/1.73m2",
                "mL/min/{1.73_m2}",
            )
        )

    def save(self) -> None:
        with open("adpo_agent/test_data/patients.json", "w", encoding="utf-8") as f:
            json.dump(self.test_patients, f, indent=2)

        with open("adpo_agent/test_data/observations.json", "w", encoding="utf-8") as f:
            json.dump(self.test_observations, f, indent=2)

        print(f"Generated {len(self.test_patients)} patients")
        print(f"Generated {len(self.test_observations)} observations")
        print("Files saved: adpo_agent/test_data/patients.json, adpo_agent/test_data/observations.json")


if __name__ == "__main__":
    generator = TestDataGenerator()
    generator.generate()
    generator.save()