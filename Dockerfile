FROM python:3.12-slim

ARG BEYOND_AI_VERSION=dev

WORKDIR /app

ENV BEYOND_AI_VERSION=${BEYOND_AI_VERSION}

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY shared/ ./shared/
COPY sanctions/ ./sanctions/

RUN addgroup --system beyondai && adduser --system --ingroup beyondai beyondai \
    && chown -R beyondai:beyondai /app

USER beyondai

EXPOSE 8000

CMD ["uvicorn", "sanctions.src.main:app", "--host", "0.0.0.0", "--port", "8000"]
