from billing.config import Settings


def main() -> None:
    settings = Settings()
    print(f"billing listening on port {settings.port}, currency {settings.currency}")


if __name__ == "__main__":
    main()
