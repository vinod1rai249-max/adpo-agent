import base64
import json
import traceback

from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse

from adpo_agent.agent import orchestrator


class ADPOApplication:
    def __init__(self):
        self.app = FastAPI(title="ADPO Agent API")
        self._register_routes()

    def _register_routes(self):

        @self.app.get("/")
        async def home():
            return {
                "message": "ADPO Agent API is running",
                "health": "/health",
                "process_lab_result": "POST /process-lab-result"
            }

        @self.app.get("/health")
        async def health():
            return {"status": "healthy"}

        @self.app.post("/process-lab-result")
        async def process_lab_result(request: Request):
            try:
                envelope = await request.json()

                if not envelope:
                    return JSONResponse({"error": "No data"}, status_code=400)

                pubsub_message = envelope.get("message", {})
                encoded_data = pubsub_message.get("data", "")

                if not encoded_data:
                    return JSONResponse(
                        {"error": "Missing Pub/Sub message data"},
                        status_code=400,
                    )

                decoded_data = base64.b64decode(encoded_data).decode("utf-8")
                lab_event = json.loads(decoded_data)

                required_fields = [
                    "patient_id",
                    "loinc_code",
                    "value",
                    "unit",
                    "age",
                    "gender",
                    "observation_id",
                ]

                missing = [field for field in required_fields if field not in lab_event]
                if missing:
                    return JSONResponse(
                        {"error": f"Missing fields: {', '.join(missing)}"},
                        status_code=400,
                    )

                decision = orchestrator.check_lab_reflex_rules(
                    patient_id=lab_event["patient_id"],
                    loinc_code=lab_event["loinc_code"],
                    result_value=float(lab_event["value"]),
                    result_unit=lab_event["unit"],
                    patient_gender=lab_event["gender"],
                    patient_age=int(lab_event["age"]),
                )

                print(f"[ADPO] Decision: {decision}")

                if not decision.get("reflex_needed"):
                    return JSONResponse(
                        {
                            "status": "processed",
                            "response": f"No reflex required. Reason: {decision.get('reason')}",
                            "decision": decision,
                        },
                        status_code=200,
                    )

                if decision.get("priority", "").upper() == "STAT":
                    return JSONResponse(
                        {
                            "status": "processed",
                            "response": f"URGENT: HITL review required for {lab_event['patient_id']}",
                            "decision": decision,
                        },
                        status_code=200,
                    )

                order_result = orchestrator.create_reflex_order(
                    patient_id=lab_event["patient_id"],
                    order_code=decision["reflex_order_code"],
                    order_name=decision["reflex_test_name"],
                    source_observation_id=lab_event["observation_id"],
                    priority=decision.get("priority", "routine"),
                )

                order_id = order_result.get("id", "unknown")

                return JSONResponse(
                    {
                        "status": "processed",
                        "response": f"Reflex order created successfully. ServiceRequest ID: {order_id}",
                        "decision": decision,
                        "order_result": order_result,
                    },
                    status_code=200,
                )

            except Exception as e:
                print("[ERROR]", str(e))
                traceback.print_exc()
                return JSONResponse({"error": str(e)}, status_code=500)


adpo_application = ADPOApplication()
app = adpo_application.app