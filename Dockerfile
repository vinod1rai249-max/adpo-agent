FROM python:3.11-slim

WORKDIR /app

COPY requirements.txt .

RUN pip install --no-cache-dir -r requirements.txt

COPY . .

ENV PORT=8080
ENV PROJECT_ID=adpo-healthcare-agent
ENV GOOGLE_CLOUD_PROJECT=adpo-healthcare-agent

CMD ["uvicorn", "adpo_agent.app:app", "--host", "0.0.0.0", "--port", "8080"]