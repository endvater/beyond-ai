FROM python:3.12-slim

ARG BEYOND_AI_VERSION=dev

WORKDIR /app

ENV BEYOND_AI_VERSION=${BEYOND_AI_VERSION}

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY shared/ ./shared/
COPY sanctions/ ./sanctions/

EXPOSE 8000

CMD ["uvicorn", "sanctions.src.main:app", "--host", "0.0.0.0", "--port", "8000"]
