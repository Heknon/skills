FROM python:3.12-slim
WORKDIR /app
COPY requirements.txt .
RUN pip install -r requirements.txt
COPY common/ common/
COPY api/ api/
CMD ["python", "api/main.py", "quote", "1", "1"]
