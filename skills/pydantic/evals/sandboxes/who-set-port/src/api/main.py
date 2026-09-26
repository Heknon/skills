from api.config import Settings


def main() -> None:
    settings = Settings()
    print(f"api listening on port {settings.port} (log level {settings.log_level})")


if __name__ == "__main__":
    main()
