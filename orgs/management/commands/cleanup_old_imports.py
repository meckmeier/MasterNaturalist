from datetime import timedelta

from django.core.management.base import BaseCommand
from django.db import transaction
from django.utils import timezone

from orgs.models import (
    ActivityUpload,
    RawLoadData,
    Pending_Location,
    Pending_Activity,
    Pending_Session,
)


class Command(BaseCommand):
    help = "Delete old import records and their uploaded files."

    def add_arguments(self, parser):
        parser.add_argument(
            "--days",
            type=int,
            default=90,
            help="Delete imports older than this many days. Default: 90.",
        )

        parser.add_argument(
            "--status",
            nargs="+",
            default=["published", "error"],
            help="Upload statuses eligible for cleanup. Default: published error.",
        )

        parser.add_argument(
            "--delete",
            action="store_true",
            help="Actually delete records and files. Without this, runs in preview mode.",
        )

    def handle(self, *args, **options):
        days = options["days"]
        statuses = options["status"]
        actually_delete = options["delete"]

        cutoff = timezone.now() - timedelta(days=days)

        old_uploads = ActivityUpload.objects.filter(
            uploaded_at__lt=cutoff,
            status__in=statuses,
        )

        self.stdout.write("")
        self.stdout.write(f"Cleanup imports older than {days} days")
        self.stdout.write(f"Statuses: {', '.join(statuses)}")
        self.stdout.write(f"Cutoff: {cutoff:%Y-%m-%d %H:%M}")
        self.stdout.write(f"Found uploads: {old_uploads.count()}")

        if not old_uploads.exists():
            self.stdout.write(self.style.SUCCESS("Nothing to clean up."))
            return

        for upload in old_uploads:
            self.stdout.write("")
            self.stdout.write(f"Upload {upload.id} — status={upload.status}")

            raw_count = RawLoadData.objects.filter(upload=upload).count()
            pending_location_count = Pending_Location.objects.filter(source_upload=upload).count()
            pending_activity_count = Pending_Activity.objects.filter(source_upload=upload).count()
            pending_session_count = Pending_Session.objects.filter(source_upload=upload).count()

            self.stdout.write(f"  RawLoadData: {raw_count}")
            self.stdout.write(f"  Pending_Location: {pending_location_count}")
            self.stdout.write(f"  Pending_Activity: {pending_activity_count}")
            self.stdout.write(f"  Pending_Session: {pending_session_count}")

            if upload.file:
                self.stdout.write(f"  File: {upload.file.name}")
            else:
                self.stdout.write("  File: none")

            if actually_delete:
                with transaction.atomic():
                    if upload.file:
                        upload.file.delete(save=False)

                    Pending_Session.objects.filter(source_upload=upload).delete()
                    Pending_Activity.objects.filter(source_upload=upload).delete()
                    Pending_Location.objects.filter(source_upload=upload).delete()
                    RawLoadData.objects.filter(upload=upload).delete()

                    upload.delete()

                self.stdout.write(self.style.SUCCESS("  Deleted."))

        if not actually_delete:
            self.stdout.write("")
            self.stdout.write(self.style.WARNING("Preview only. Nothing was deleted."))
            self.stdout.write("Run again with --delete to actually delete them.")