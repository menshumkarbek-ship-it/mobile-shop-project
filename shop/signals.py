import logging
from django.db.models.signals import post_save
from django.dispatch import receiver
from .models import Order

# Setup console event debugging logger
logger = logging.getLogger(__name__)

@receiver(post_save, sender=Order)
def log_new_order_event(sender, instance, created, **kwargs):
    """
    🎯 AUTOMATED SIGNAL TRIGGER: Executes instantly upon Order record instantiation.
    """
    if created:
        print(f"\n📡 [SIGNAL TRACKER] SUCCESS: Secure transaction instance caught for Order #{instance.id}!")
        print(f"💰 Transaction total value calculated at: ${instance.total_price if hasattr(instance, 'total_price') else 'Pending'}\n")
        logger.info(f"Order #{instance.id} logged seamlessly through signal router listeners.")