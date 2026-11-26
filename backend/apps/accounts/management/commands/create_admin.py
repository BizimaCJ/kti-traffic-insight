import getpass

from django.contrib.auth import get_user_model
from django.contrib.auth.password_validation import validate_password
from django.core.exceptions import ValidationError
from django.core.management.base import BaseCommand, CommandError


class Command(BaseCommand):
    help = "Create (or update the password of) an administrator account. There is no public registration."

    def add_arguments(self, parser):
        parser.add_argument("--username", required=True)
        parser.add_argument("--name", default="", help="full name, e.g. 'Admin One'")
        parser.add_argument("--password", help="omit to be asked for it safely")

    def handle(self, *args, **options):
        password = options["password"] or getpass.getpass("Password: ")
        try:
            validate_password(password)
        except ValidationError as exc:
            raise CommandError("; ".join(exc.messages))
        User = get_user_model()
        user, created = User.objects.get_or_create(username=options["username"])
        first, _, last = options["name"].partition(" ")
        if options["name"]:
            user.first_name, user.last_name = first, last
        user.is_staff = True
        user.is_active = True
        user.set_password(password)
        user.save()
        self.stdout.write(self.style.SUCCESS(f"Administrator '{user.username}' {'created' if created else 'updated'}."))
