FROM python:3.12-slim
COPY requirements.txt /app/requirements.txt
RUN pip install -r /app/requirements.txt
COPY common/ /app/common/
COPY worker/ /app/worker/
ENV PYTHONPATH=/app
WORKDIR /srv
CMD ["python", "-m", "worker", "1.10", "2.20"]
