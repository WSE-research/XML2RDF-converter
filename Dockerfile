FROM python:alpine
RUN apk add --no-cache libxslt
RUN python -m venv /venv
ENV PATH=/venv/bin:$PATH
COPY . .
RUN pip install -r requirements.txt
RUN pip install gunicorn
CMD gunicorn -w 4 -b 0.0.0.0:5000 app:app