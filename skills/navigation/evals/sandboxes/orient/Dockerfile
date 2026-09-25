FROM python:3.12-slim
WORKDIR /srv
COPY . .
RUN pip install .
CMD ["uvicorn", "invoicer.web:app", "--host", "0.0.0.0", "--port", "8080"]
