"""
CLI Script để seed development data.

Usage:
    python seed_dev.py              # Seed minimal (chỉ admin)
    python seed_dev.py --full       # Seed full (admin + event + teams + users)
"""

import sys
import argparse
from app.db.session import SessionLocal
from app.db.seed import run_seed


def main():
    parser = argparse.ArgumentParser(description="Seed development data")
    parser.add_argument(
        "--full",
        action="store_true",
        help="Seed full development data (admin + event + teams + users)"
    )

    args = parser.parse_args()

    mode = "development" if args.full else "minimal"

    db = SessionLocal()
    try:
        run_seed(db, mode=mode)
        print("\n✅ Seed completed successfully!")
    except Exception as e:
        print(f"\n❌ Seed failed: {str(e)}")
        sys.exit(1)
    finally:
        db.close()


if __name__ == "__main__":
    main()
