from svc.config import load


def main():
    settings = load()
    print(f"{settings.name}: logging to {settings.log_dir}, timeout {settings.timeout}s")


if __name__ == "__main__":
    main()
