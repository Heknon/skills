import uvicorn

from reports.app import app

uvicorn.run(app, host="0.0.0.0", port=8080)
