"""
Bootstrap Super Administrator Utility for EduResolve AI.
Allows safe, controlled initialization of the platform's super administrator.
"""
import os
import sys
import argparse
import getpass

# Add backend directory to path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from app.database.connection import SessionLocal
from app.services.bootstrap_service import seed_roles, bootstrap_super_admin

def main():
    parser = argparse.ArgumentParser(description="Bootstrap the initial EduResolve AI Super Administrator.")
    parser.add_argument("--email", help="Super Admin Email address")
    parser.add_argument("--password", help="Super Admin Password (min 8 chars)")
    parser.add_argument("--name", default="System Super Admin", help="Full name of the Super Administrator")
    args = parser.parse_args()

    email = args.email or os.getenv("BOOTSTRAP_SUPERADMIN_EMAIL")
    if not email:
        email = input("Enter Super Admin Email: ").strip()

    password = args.password or os.getenv("BOOTSTRAP_SUPERADMIN_PASSWORD")
    if not password:
        password = getpass.getpass("Enter Super Admin Password (min 8 chars): ").strip()
        confirm = getpass.getpass("Confirm Super Admin Password: ").strip()
        if password != confirm:
            print("ERROR: Passwords do not match.")
            sys.exit(1)

    db = SessionLocal()
    try:
        # Seed baseline roles
        seed_roles(db)
        print("[SUCCESS] Baseline system roles verified.")

        # Create or update super admin
        user = bootstrap_super_admin(db, email=email, password=password, full_name=args.name)
        print(f"[SUCCESS] Super Administrator successfully initialized: {user.email} (ID: {user.id})")
    except Exception as e:
        print(f"ERROR: Failed to bootstrap super administrator: {e}")
        sys.exit(1)

    finally:
        db.close()

if __name__ == "__main__":
    main()
