FROM python:alpine
RUN apk add --no-cache libxslt
RUN python -m venv /venv
ENV PATH=/venv/bin:$PATH
COPY . .
RUN pip install -r requirements.txt
CMD uvicorn --workers 4 --port 5000 --host 0.0.0.0 --ssl-certfile /ssl/server.crt --ssl-keyfile /ssl/server.key app:app