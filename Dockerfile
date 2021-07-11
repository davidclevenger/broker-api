FROM tiangolo/uvicorn-gunicorn-fastapi:python3.8

COPY ./api /app
COPY requirements.txt requirements.txt

ENV MAX_WORKERS=1

RUN pip install -r requirements.txt
