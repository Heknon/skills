from app.config import load


def main():
    settings = load("settings.json")
    print(f"{settings['name']} listening on port {settings['port']}")


if __name__ == "__main__":
    main()
