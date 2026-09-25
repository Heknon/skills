from app.router import App
from app.routers import orders

API_PREFIX = "/api/v1"

app = App()
app.include(orders.router, prefix=API_PREFIX)
