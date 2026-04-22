import json
import os
from typing import Any, Dict, List, Optional

import requests
from google.auth import default
from google.auth.transport.requests import Request


class FHIRTestDataLoader:
    def __init__(
        self,
        project_id: Optional[str] = None,
        location: str = "us-central1",
        dataset_id: str = "adpo-dataset",
        fhir_store: str = "adpo-fhir-store",
    ) -> None:
        self.project_id = project_id or os.getenv("PROJECT_ID") or os.getenv("GOOGLE_CLOUD_PROJECT")
        if not self.project_id:
            raise ValueError("PROJECT_ID or GOOGLE_CLOUD_PROJECT must be set")

        self.location = location
        self.dataset_id = dataset_id
        self.fhir_store = fhir_store

        self.base_url = (
            f"https://healthcare.googleapis.com/v1/projects/{self.project_id}/"
            f"locations/{self.location}/datasets/{self.dataset_id}/"
            f"fhirStores/{self.fhir_store}/fhir"
        )

    def get_token(self) -> str:
        creds, _ = default(scopes=["https://www.googleapis.com/auth/cloud-healthcare"])
        creds.refresh(Request())
        return creds.token

    def _headers(self, token: str) -> Dict[str, str]:
        return {
            "Authorization": f"Bearer {token}",
            "Content-Type": "application/fhir+json",
        }

    def load_json_file(self, path: str) -> List[Dict[str, Any]]:
        with open(path, "r", encoding="utf-8") as f:
            return json.load(f)

    def create_resource(self, resource_type: str, resource: Dict[str, Any], token: str) -> Dict[str, Any]:
        """
        Create a FHIR resource using POST so the server assigns the resource ID.
        """
        url = f"{self.base_url}/{resource_type}"
        response = requests.post(
            url,
            data=json.dumps(resource),
            headers=self._headers(token),
            timeout=30,
        )
        response.raise_for_status()
        return response.json()

    def run(self) -> None:
        token = self.get_token()

        patients = self.load_json_file("adpo_agent/test_data/patients.json")
        observations = self.load_json_file("adpo_agent/test_data/observations.json")

        # Map old local patient IDs to server-assigned patient IDs
        patient_id_map: Dict[str, str] = {}

        print("Uploading Patients...")
        for patient in patients:
            old_id = patient["id"]

            # Keep the original local ID in identifier, but remove top-level id
            patient_payload = dict(patient)
            patient_payload.pop("id", None)

            created_patient = self.create_resource("Patient", patient_payload, token)
            new_id = created_patient["id"]
            patient_id_map[old_id] = new_id

            print(f"OK Patient/{old_id} -> created as Patient/{new_id}")

        print("Uploading Observations...")
        for observation in observations:
            old_obs_id = observation["id"]
            subject_ref = observation.get("subject", {}).get("reference", "")

            # Example old ref: Patient/test-patient-psa-high
            old_patient_id = subject_ref.split("/", 1)[1] if "/" in subject_ref else subject_ref
            new_patient_id = patient_id_map.get(old_patient_id)

            if not new_patient_id:
                print(f"ERR Observation/{old_obs_id}: patient mapping not found for {old_patient_id}")
                continue

            observation_payload = dict(observation)
            observation_payload.pop("id", None)
            observation_payload["subject"] = {"reference": f"Patient/{new_patient_id}"}

            created_observation = self.create_resource("Observation", observation_payload, token)
            new_obs_id = created_observation["id"]

            print(
                f"OK Observation/{old_obs_id} -> created as Observation/{new_obs_id} "
                f"(subject Patient/{new_patient_id})"
            )

        print(f"Done. {len(patients)} patients and {len(observations)} observations processed.")


if __name__ == "__main__":
    loader = FHIRTestDataLoader()
    loader.run()