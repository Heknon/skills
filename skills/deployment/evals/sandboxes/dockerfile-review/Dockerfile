ARG PIP_TOKEN
ARG BASE=python:3.12-slim
FROM ${BASE}
WORKDIR /app
COPY . .
RUN pip install --index-url https://__token__:${PIP_TOKEN}@pypi.internal.example.com/simple -r requirements.txt
RUN chgrp -R 0 /app && chmod -R g=u /app
HEALTHCHECK CMD curl -f http://localhost:8080/healthz || exit 1
USER 1001
EXPOSE 8080
CMD python -m reports
