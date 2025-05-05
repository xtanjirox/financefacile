from django.db.models.signals import post_save
from django.dispatch import receiver
from accounts.models import Company
from core.models import ProductCategory

@receiver(post_save, sender=Company)
def create_uncategorized_category(sender, instance, created, **kwargs):
    """
    Create an 'Uncategorized' product category for each new company
    """
    if created:
        # Check if the company already has an 'Uncategorized' category
        uncategorized_exists = ProductCategory.objects.filter(
            company=instance, 
            name='Uncategorized'
        ).exists()
        
        if not uncategorized_exists:
            # Create the 'Uncategorized' category for this company
            ProductCategory.objects.create(
                company=instance,
                name='Uncategorized',
                parent=None  # This is a top-level category
            )
