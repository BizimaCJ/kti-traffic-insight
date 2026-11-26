#!/usr/bin/env python
import os
import sys


def main():
    os.environ.setdefault("DJANGO_SETTINGS_MODULE", "kti.settings")
    from django.core.management import execute_from_command_line
    from django.db.utils import OperationalError

    try:
        execute_from_command_line(sys.argv)
    except OperationalError as exc:
        reason = str(exc).strip().splitlines()[0] if str(exc).strip() else "unknown error"
        sys.stderr.write(
            f"\nCannot reach the database: {reason}\n"
            "Check that PostgreSQL is running and that KTI_DATABASE_URL in .env is correct "
            "(host, port, user, password, database name).\n"
        )
        sys.exit(1)


if __name__ == "__main__":
    main()
