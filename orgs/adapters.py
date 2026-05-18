from allauth.account.adapter import DefaultAccountAdapter


class CustomAccountAdapter(DefaultAccountAdapter):

    def get_signup_form_initial_data(self, request):
        initial = super().get_signup_form_initial_data(request)

        invite_email = request.session.get("pending_org_invite_email")

        if invite_email:
            initial["email"] = invite_email

        return initial