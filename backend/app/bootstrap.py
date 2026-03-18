import argparse

from .database import SessionLocal, ensure_database_schema_ready
from .seed import seed_base_data, seed_demo_data


def run_bootstrap(command: str) -> int:
    ensure_database_schema_ready()

    db = SessionLocal()
    try:
        if command == "init-base":
            seed_base_data(db)
        elif command == "seed-demo":
            seed_demo_data(db)
        else:
            raise ValueError(f"Unsupported bootstrap command: {command}")
    finally:
        db.close()

    return 0


def main() -> int:
    parser = argparse.ArgumentParser(description="Bootstrap MySQL data for AI App Square")
    parser.add_argument(
        "command",
        choices=("init-base", "seed-demo"),
        help="init-base seeds only system catalogs/users; seed-demo also loads demo business data",
    )
    args = parser.parse_args()
    return run_bootstrap(args.command)


if __name__ == "__main__":
    raise SystemExit(main())
