FROM python:3.12-slim

ARG SERVICE=lancamentos

WORKDIR /app

COPY services/${SERVICE}/requirements.txt /tmp/requirements.txt
RUN pip install --no-cache-dir -r /tmp/requirements.txt \
    && adduser --disabled-password --gecos "" appuser

COPY services/${SERVICE}/app /app/app

USER appuser

ENV PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1

EXPOSE 8000

CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]
