from django.db import models
from django.contrib.auth.models import User
from django.db.models.signals import post_save
from django.dispatch import receiver

class Company(models.Model):
    name = models.CharField(max_length=255)
    siret_number = models.CharField(max_length=14, blank=True, null=True)
    address = models.TextField(blank=True, null=True)
    phone_number = models.CharField(max_length=20, blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        verbose_name = 'Company'
        verbose_name_plural = 'Companies'
    
    def __str__(self):
        return self.name

class CompanySettings(models.Model):
    """Company-specific settings that can only be modified by company administrators"""
    company = models.OneToOneField(Company, on_delete=models.CASCADE, related_name='settings')
    default_tva_rate = models.DecimalField(
        max_digits=5, 
        decimal_places=2, 
        default=19.00,
        help_text="Default TVA (VAT) rate in percentage (e.g., 19.00 for 19%)"
    )
    stamp_fee = models.DecimalField(
        max_digits=6, 
        decimal_places=2, 
        default=1.00,
        help_text="Stamp fee amount to be added to all invoices"
    )
    
    class Meta:
        verbose_name = 'Company Settings'
        verbose_name_plural = 'Company Settings'
    
    def __str__(self):
        return f"{self.company.name} Settings"

class UserProfile(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name='profile')
    company = models.ForeignKey(Company, on_delete=models.CASCADE, related_name='members', null=True, blank=True)
    is_company_admin = models.BooleanField(default=False, help_text="Designates whether this user can manage company settings")
    avatar = models.ImageField(upload_to='avatars/', null=True, blank=True)
    
    def __str__(self):
        return f"{self.user.username}'s Profile"
        
    def get_avatar_url(self):
        if self.avatar and hasattr(self.avatar, 'url'):
            return self.avatar.url
        return None
        
    def get_initials(self):
        """Return the first two letters of the username for the default avatar"""
        return self.user.username[:2].upper() if self.user.username else "--"

@receiver(post_save, sender=User)
def create_user_profile(sender, instance, created, **kwargs):
    """Create a UserProfile for each new User"""
    if created:
        UserProfile.objects.create(user=instance)

@receiver(post_save, sender=User)
def save_user_profile(sender, instance, **kwargs):
    """Save the UserProfile when the User is saved"""
    instance.profile.save()

@receiver(post_save, sender=Company)
def create_company_settings(sender, instance, created, **kwargs):
    """Create CompanySettings for each new Company"""
    if created:
        CompanySettings.objects.create(company=instance)
