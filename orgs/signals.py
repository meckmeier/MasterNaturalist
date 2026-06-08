# signals.py

from django.contrib.auth.models import User
from django.db.models.signals import post_save,  post_delete
from django.dispatch import receiver
from .models import Profile, Organization, OrgManager, ActivityUpload


@receiver(post_save, sender=User)
def create_user_profile(sender, instance, created, **kwargs):
    if created:
        Profile.objects.get_or_create(user=instance)



@receiver(post_delete, sender=ActivityUpload)
def delete_upload_file(sender, instance, **kwargs):
    if instance.file:
        instance.file.delete(save=False)