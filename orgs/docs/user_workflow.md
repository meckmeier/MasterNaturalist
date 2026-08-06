# User Workflow
WildPaths uses Django's authentication framework together with django-allauth
to manage user registration, authentication, password management, and email
verification. Django provides the underlying user model, authentication,
sessions, and password validation. django-allauth provides the account
management workflow. WildPaths customizes the signup process, user interface,
and organization invitation process.

## Authentication Architecture
    Django
        ↓
    django-allauth
        ↓
    WildPaths customizations

|Feature	|Provider	|WildPaths customization|
|---|---|---|
|User model	|Django	|Custom User model|
|Authentication	|Django	|Uses standard session authentication|
|Login/logout	|django-allauth	|Custom templates|
|Registration	|django-allauth	|Custom signup form|
|Email verification	|django-allauth	|Mandatory verification|
|Password reset	|django-allauth	|Custom templates and email logging|
|Password rules	|Django	|Default validators|
|Invitation acceptance	|WildPaths	|Creates OrgManager during signup|
|Profile creation	|WildPaths	|Creates Profile automatically|
|Email sending	|WildPaths	|Routes through safe_send_mail()|
|CAPTCHA	|WildPaths	|Cloudflare Turnstile|

## Implemenation - django
This decorator is used to indicate which views require login in views:
@login_required

- def org_mgmt(request):
- def org_set_default_location
- def profile_view(request)
- def org_manager_add
- def upload_csv
- def upload_review_raw
- def upload_build_pending
- def upload_review_locations
- def upload_review_activitie
- ... etc.

### settings.py

AUTH_USER_MODEL = 'orgs.User'

AUTH_PASSWORD_VALIDATORS = [   {'NAME': 'django.contrib.auth.password_validation.UserAttributeSimilarityValidator',},
    {'NAME': 'django.contrib.auth.password_validation.MinimumLengthValidator', },
    {'NAME': 'django.contrib.auth.password_validation.CommonPasswordValidator', },
    {'NAME': 'django.contrib.auth.password_validation.NumericPasswordValidator', },]

AUTHENTICATION_BACKENDS = [
    'django.contrib.auth.backends.ModelBackend',
    'allauth.account.auth_backends.AuthenticationBackend',
]

### models.py

    class User(AbstractUser):
        pass

    class Profile(models.Model):
        user = models.OneToOneField(User, on_delete=models.CASCADE, related_name='profile')
        bio=models.TextField(blank=True)
        is_master_naturalist = models.BooleanField(default=False)
        my_region = models.ForeignKey( Region, null=True, blank=True, on_delete=models.SET_NULL)
        # Personalization Toggles
        include_online = models.BooleanField(default=True)
        terms_accepted_at = models.DateTimeField(null=True, blank=True)
        
        def __str__(self):
            return f'{self.user.username}'
        
        @property
        def following_orgs(self):
            return Organization.objects.filter(following__profile=self)
        
        def following_count(self):
            return self.following.count()
        
        def has_published_uploads(self):
            return self.published_uploads.exists()
        
        @property
        def is_org_manager(self):
            return self.managers.exists()


## Implementation- allauth
MasterNaturalist.settings.py level settings implements allauths

    urlpatterns = [
        path('', include('orgs.urls')),
        path('admin/', admin.site.urls),
        **path("accounts/", include("allauth.urls")),**
    ]

### urls.py
URL aliases is to provide cleaner URLs such as /login and /register. They simply redirect to the named allauth views (account_login, account_signup, etc.). Once those views execute, allauth automatically renders the corresponding template from templates/account/ if you've provided one.

>   - from django.contrib.auth import views as auth_views

>    - path("login", lambda request: redirect("account_login"), name="login"),
>    - path("logout", lambda request: redirect("account_logout"), name="logout"),
>    - path("register", lambda request: redirect("account_signup"), name="register"),
>    - path("password_reset/", lambda request: redirect("account_reset_password"), name="password_reset"),


### template/account
WildPaths overrides selected django-allauth templates by placing files in templates/account/. Django's template loader automatically finds these project templates before the default templates included with django-allauth. No additional configuration is required beyond ensuring the project's templates directory is included in the TEMPLATES setting.

This folder includes the login forms identified above.
> * email_confirm.html
> * login.html
> * password_change.html
> * password_reset_done.html
> * password_reset_from_key_done.html
> * password_reset.html
> * signup.html
> * verification_sent.html


### adapters.py
This file tells allauth to use a custom form for signup, so i can include the Profile and OrgManager records if appropriate.
Also includes code to use my send_safe_email function so that the email gets logged and I can throttle send rates if needed.

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

### forms.py
This code allows me to create the Profile with the User name and to add the user to an OrgManager if it's coming from that Add Org routine.

    from allauth.account.forms import SignupForm

    class CustomSignupForm(SignupForm):
        turnstile = TurnstileField()
        first_name = forms.CharField(max_length=150, required=False)
        last_name = forms.CharField(max_length=150, required=False)
        accept_terms = forms.BooleanField(
            required=True,
            label="I agree to the Terms of Service and Privacy Policy",   )
        def __init__(self, *args, **kwargs):       
            super().__init__(*args, **kwargs)       
            for field in self.fields.values():
                if isinstance(field.widget, forms.CheckboxInput):
                    field.widget.attrs["class"] = "form-check-input"
                else:
                    field.widget.attrs["class"] = "form-control"       

        def save(self, request):
            user = super().save(request)
            user.first_name = self.cleaned_data.get("first_name", "").strip()
            user.last_name = self.cleaned_data.get("last_name", "").strip()
            user.save()
            profile, created = Profile.objects.get_or_create(user=user)
            profile.terms_accepted_at = timezone.now()
            profile.save()
            token = request.session.pop("pending_org_invite_token", None)
            if token:
                invite = OrgInvite.objects.filter( token=token, accepted=False,).first()

                if invite:
                    OrgManager.objects.get_or_create(profile=profile, org=invite.org, defaults={"role": invite.role}, )
                    invite.accepted = True
                    invite.accepted_at = timezone.now()
                    invite.save()
            return user


### settings.py

    PASSWORD_RESET_TIMEOUT = 60*60*24
    SITE_ID = 1
    ACCOUNT_SIGNUP_FIELDS = ['email*', 'username*', 'password1*', 'password2*']
    ACCOUNT_UNIQUE_EMAIL = True
    ACCOUNT_ADAPTER = "orgs.adapters.CustomAccountAdapter"
    ACCOUNT_EMAIL_VERIFICATION = "mandatory"
    ACCOUNT_LOGIN_METHODS = {"email", "username"}
    ACCOUNT_FORMS = {    "signup": "orgs.forms.CustomSignupForm",}
    INSTALLED_APPS = [    'allauth',    'allauth.account',]
    MIDDLEWARE = [ 'allauth.account.middleware.AccountMiddleware', ]


## Implementation - CAPTCHA
Wildpaths users Cloudflare.Turnstyle to handle CAPTCHA configuration (used to make sure you are a person)

    TURNSTILE_SITEKEY = os.environ.get("TURNSTILE_SITEKEY")
    TURNSTILE_SECRET = os.environ.get("TURNSTILE_SECRET")

 Email configuration

 Outbound authentication emails are sent through Anymail/Postmark in production and the console backend during development.

 ## User Workflow
 Users can create a new user name directly by using the Register link from the main landing page.

 Also can receive an invite in email, if they use the Add Organization menu option before they have created a username. This flow examines the email address from the Add form, and if it already exists will add the username to the OrgManagers table. But if that email does not exist, then it will generate an email with a link for the user to create the username. Once they create it, the link will add the username created to the OrgManager table. 

 