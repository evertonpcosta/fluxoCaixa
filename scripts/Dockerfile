FROM python:3.12-slim

WORKDIR /app

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY _common.py gerar_observabilidade.py ./

CMD ["python", "gerar_observabilidade.py", "--duration", "90", "--rps", "5"]
