# Email logging workflow

*Postmark* is the platform for sending emails from WildPathsWI.org.
> * user name: meckmeier
> * server: Master Naturalist
> * Using Transactional Emails.

I have added a homegrown email logging workflow, so i can throttle this feature. I have been bot attacked here twice, so I have a switch to disable this if I send too many emails.

## Implementation

### utils.py
> def safe_send_mail

This is used in all mhy view send email steps.

### models.py

class EmailLog(models.Model):
    sent_at = models.DateTimeField(auto_now_add=True)
    category = models.CharField(max_length=50)
    recipient = models.EmailField()
    subject = models.CharField(max_length=255)
    status = models.CharField(
    max_length=30,
    choices=[
        ("SENT", "Sent"),
        ("BLOCKED_HOURLY", "Blocked Hourly"),
        ("BLOCKED_MONTHLY", "Blocked Monthly"),
        ("DISABLED", "Email Disabled"),
        ("FAILED", "Send Failed"),
        ("PENDING", "Pending"),
    ],
    default="SENT",
)

### adapters.py (for allauth emails)

    def send_mail(self, template_prefix, email, context):
        message = self.render_mail(template_prefix, email, context)

        return safe_send_mail(
            subject=message.subject,
            message=message.body,
            from_email=message.from_email or settings.DEFAULT_FROM_EMAIL,
            recipient_list=message.to,
            category=template_prefix,
            html_message=getattr(message, "alternatives", [("", None)])[0][0]
            if getattr(message, "alternatives", None)
            else None,
        )


### Adjust the settings with ENV variables:
EMAIL_ENABLED=True
EMAIL_HOURLY_LIMIT=50
EMAIL_MONTHLY_LIMIT=100
POSTMARK_BILLING_DAY=27

## Other mail settings:


if DEBUG:
    # In development, send admin error emails to the console.
    ADMINS = [
        ("Mary", "mary@eckmeier.com"),
    ]
    EMAIL_BACKEND = "django.core.mail.backends.console.EmailBackend"
    DEFAULT_FROM_EMAIL = "noreply@example.com"
else:
    # In production, no admin emails are sent. to protect postmark
    ADMINS = []
    EMAIL_BACKEND = "anymail.backends.postmark.EmailBackend"
    DEFAULT_FROM_EMAIL = os.getenv("DEFAULT_FROM_EMAIL")

DEFAULT_FROM_EMAIL = os.environ.get(
    "DEFAULT_FROM_EMAIL",
    "mary@eckmeier.com"
)
EMAIL_ENABLED = os.getenv("EMAIL_ENABLED", "True") == "True"
EMAIL_HOURLY_LIMIT = int(os.getenv("EMAIL_HOURLY_LIMIT", "50"))
EMAIL_MONTHLY_LIMIT = int(os.getenv("EMAIL_MONTHLY_LIMIT", "9000"))
POSTMARK_BILLING_DAY = int(os.getenv("POSTMARK_BILLING_DAY", "22"))

SERVER_EMAIL = DEFAULT_FROM_EMAIL

EMAIL_TIMEOUT = 10  # seconds