from shop.config import Settings


def main() -> None:
    settings = Settings()
    print(f"shop on port {settings.port}, debug={settings.debug}")


if __name__ == "__main__":
    main()
