FROM registry.example.com/mirror/library/python:3.12-slim-trixie
RUN useradd --create-home appuser
WORKDIR /home/appuser/app
COPY . .
RUN pip install --no-cache-dir .
RUN mkdir -p /home/appuser/app/data
USER appuser
EXPOSE 80
CMD ["python", "-m", "reports"]
