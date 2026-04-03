from django.test import TestCase
from django.utils import timezone
from datetime import timedelta

from orgs.models import Session, Activity, Organization


class SessionQuerySetTests(TestCase):
    def setUp(self):
        today = timezone.now().date()

        # --- Organizations ---
        self.org_active = Organization.objects.create(
            org_name="Active Org", deleted=False
        )
        self.org_deleted = Organization.objects.create(
            org_name="Deleted Org", deleted=True
        )

        # --- Activities ---
        self.act_active = Activity.objects.create(
            org=self.org_active, deleted=False
        )
        self.act_deleted = Activity.objects.create(
            org=self.org_active, deleted=True
        )
        self.act_org_deleted = Activity.objects.create(
            org=self.org_deleted, deleted=False
        )

        # --- Sessions ---
        # Valid upcoming
        self.upcoming_valid = Session.objects.create(
            activity=self.act_active,
            start=today + timedelta(days=5),
            deleted=False
        )

        # Deleted activity
        self.upcoming_act_deleted = Session.objects.create(
            activity=self.act_deleted,
            start=today + timedelta(days=5),
            deleted=False
        )

        # Deleted org
        self.upcoming_org_deleted = Session.objects.create(
            activity=self.act_org_deleted,
            start=today + timedelta(days=5),
            deleted=False
        )

        # Deleted session
        self.upcoming_session_deleted = Session.objects.create(
            activity=self.act_active,
            start=today + timedelta(days=5),
            deleted=True
        )

        # Ongoing session
        self.ongoing_valid = Session.objects.create(
            activity=self.act_active,
            start=today - timedelta(days=2),
            end=today + timedelta(days=2),
            deleted=False
        )

        # Past session (should not show in current/upcoming/ongoing)
        self.past_session = Session.objects.create(
            activity=self.act_active,
            start=today - timedelta(days=10),
            end=today - timedelta(days=5),
            deleted=False
        )

    # -------------------------
    # ACTIVE
    # -------------------------
    def test_active_filters_deleted(self):
        qs = Session.objects.active()

        self.assertIn(self.upcoming_valid, qs)
        self.assertNotIn(self.upcoming_act_deleted, qs)
        self.assertNotIn(self.upcoming_org_deleted, qs)
        self.assertNotIn(self.upcoming_session_deleted, qs)

    # -------------------------
    # UPCOMING
    # -------------------------
    def test_upcoming(self):
        qs = Session.objects.upcoming()

        self.assertIn(self.upcoming_valid, qs)

        # Ensure deleted ones are excluded
        self.assertNotIn(self.upcoming_act_deleted, qs)
        self.assertNotIn(self.upcoming_org_deleted, qs)
        self.assertNotIn(self.upcoming_session_deleted, qs)

        # Ongoing should not be here
        self.assertNotIn(self.ongoing_valid, qs)

    # -------------------------
    # ONGOING
    # -------------------------
    def test_ongoing(self):
        qs = Session.objects.ongoing()

        self.assertIn(self.ongoing_valid, qs)

        # Upcoming should not be here
        self.assertNotIn(self.upcoming_valid, qs)

        # Deleted should not be here
        self.assertNotIn(self.upcoming_act_deleted, qs)

    # -------------------------
    # CURRENT (combined logic)
    # -------------------------
    def test_current(self):
        qs = Session.objects.current()

        self.assertIn(self.upcoming_valid, qs)
        self.assertIn(self.ongoing_valid, qs)

        # Past should not be included
        self.assertNotIn(self.past_session, qs)

        # Deleted should not be included
        self.assertNotIn(self.upcoming_act_deleted, qs)
        self.assertNotIn(self.upcoming_org_deleted, qs)
        self.assertNotIn(self.upcoming_session_deleted, qs)