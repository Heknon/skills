from app.settings import load_settings


def create_app():
    settings = load_settings()
    return {"debug": settings["debug"]}
