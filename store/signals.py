from django.db.models.signals import post_save
from django.dispatch import receiver
from .models import Customer, Bill

@receiver(post_save, sender=Customer)
def update_related_bills(sender, instance, **kwargs):
    if instance.pk is not None and hasattr(instance, '_old_email') and instance.email != instance._old_email:
        Bill.objects.filter(customer=instance).update(customer_email=instance.email)
