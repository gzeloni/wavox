FROM python:3.13-slim

WORKDIR /web

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY mkdocs.yml .
COPY docs/ docs/

RUN mkdocs build

COPY server.py .

CMD ["uvicorn", "server:app", "--host", "0.0.0.0", "--port", "3500"]
