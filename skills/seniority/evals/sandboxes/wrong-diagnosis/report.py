import json
import sys


def load_config(path="config.yml"):
    values = {}
    with open(path) as handle:
        for line in handle:
            line = line.strip()
            if line and not line.startswith("#") and ":" in line:
                key, value = line.split(":", 1)
                values[key.strip()] = value.strip()
    return values


def main() -> int:
    config = load_config()
    print(json.dumps({"bucket": config["bucket"], "region": config["region"]}))
    return 0


if __name__ == "__main__":
    sys.exit(main())
