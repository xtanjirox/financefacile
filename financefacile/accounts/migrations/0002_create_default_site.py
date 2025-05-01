from django.db import migrations
from django.conf import settings

def create_default_site(apps, schema_editor):
    # We can't import the Site model directly as it may be a newer
    # version than this migration expects. We use the historical version.
    Site = apps.get_model('sites', 'Site')
    
    # Create default site if it doesn't exist
    Site.objects.get_or_create(
        id=settings.SITE_ID if hasattr(settings, 'SITE_ID') else 1,
        defaults={
            'domain': 'localhost:8000',
            'name': 'FinanceFacile'
        }
    )

class Migration(migrations.Migration):

    dependencies = [
        ('accounts', '0001_initial'),
        ('sites', '0002_alter_domain_unique'),
    ]

    operations = [
        migrations.RunPython(create_default_site),
    ]
