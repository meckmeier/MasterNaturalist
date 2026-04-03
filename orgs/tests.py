from django.test import TestCase

# Create your tests here.
from django.test import TestCase
from django.utils import timezone
from orgs.models import Session, Activity, Organization

class SessionQuerySetTests(TestCase):
    def setUp(self):
        """Set up test data for sessions, activities, and orgs."""
        today = timezone.now().date()

        # Organizations
        self.org1 = Organization.objects.create(org_name="Org 1", deleted=False)
        self.org2 = Organization.objects.create(org_name="Org 2", deleted=True)

        # Activities
        self.act1 = Activity.objects.create(org=self.org1, deleted=False)
        self.act2 = Activity.objects.create(org=self.org1, deleted=True)
        self.act3 = Activity.objects.create(org=self.org2, deleted=False)

        # Sessions
        # Upcoming session, active
        self.sess1 = Session.objects.create(activity=self.act1, start=today, deleted=False)
        # Upcoming session, activity deleted
        self.sess2 = Session.objects.create(activity=self.act2, start=today, deleted=False)
        # Upcoming session, org deleted
        self.sess3 = Session.objects.create(activity=self.act3, start=today, deleted=False)
        # Session deleted itself
        self.sess4 = Session.objects.create(activity=self.act1, start=today, deleted=True)

    def test_upcoming_filters_deleted(self):
        """Test that upcoming() excludes deleted sessions, activities, and orgs."""
        qs = Session.objects.upcoming()

        # Only sess1 should remain
        self.assertIn(self.sess1, qs)
        self.assertNotIn(self.sess2, qs)
        self.assertNotIn(self.sess3, qs)
        self.assertNotIn(self.sess4, qs)