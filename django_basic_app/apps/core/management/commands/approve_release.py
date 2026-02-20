"""
Management command: approve_release

Called by CI to approve all rows in a release that are ready.
By default approves both DRAFT and FUTURE rows.
Use --only-future to approve only FUTURE rows (leaves DRAFT untouched).

Usage:
    python manage.py approve_release --release-version v1.1.0
    python manage.py approve_release --release-version v1.1.0 --only-future
"""
from django.core.management.base import BaseCommand, CommandError
from apps.core.models import Release
from apps.core.mixins import DataStatus
from apps.core.services import get_versioned_models


class Command(BaseCommand):
    help = 'Approve all eligible rows in a release (CI only)'

    def add_arguments(self, parser):
        parser.add_argument('--release-version', required=True)
        parser.add_argument(
            '--only-future',
            action='store_true',
            help='Only approve FUTURE rows, leave DRAFT untouched',
        )

    def handle(self, *args, **options):
        version = options['release_version']
        only_future = options['only_future']

        try:
            release = Release.objects.get(version=version)
        except Release.DoesNotExist:
            raise CommandError(f'Release "{version}" does not exist.')

        statuses_to_approve = (
            [DataStatus.FUTURE]
            if only_future
            else [DataStatus.DRAFT, DataStatus.FUTURE]
        )

        total = 0
        for model in get_versioned_models():
            rows = model.objects.for_release(release).filter(status__in=statuses_to_approve)
            count = rows.count()
            rows.update(status=DataStatus.APPROVED)
            if count:
                self.stdout.write(f'  {model.__name__}: {count} rows approved')
            total += count

        self.stdout.write(self.style.SUCCESS(
            f'\n✅ {total} rows approved in release {version}.'
        ))
