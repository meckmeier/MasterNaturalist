from allauth.account.adapter import DefaultAccountAdapter
from django.conf import settings
from orgs.utils import safe_send_mail


class CustomAccountAdapter(DefaultAccountAdapter):

    def get_signup_form_initial_data(self, request):
        initial = super().get_signup_form_initial_data(request)

        invite_email = request.session.get("pending_org_invite_email")

        if invite_email:
            initial["email"] = invite_email

        return initial

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