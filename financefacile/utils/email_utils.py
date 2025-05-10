import os
from django.core.mail import EmailMultiAlternatives
from django.template.loader import render_to_string
from django.utils.html import strip_tags
from django.conf import settings
from django.contrib.sites.models import Site
from django.utils.http import urlsafe_base64_encode
from django.utils.encoding import force_bytes
from django.contrib.auth.tokens import default_token_generator


def send_confirmation_email(user):
    """
    Send a confirmation email to a newly registered user.
    
    Args:
        user: The User instance to send the confirmation email to
    """
    current_site = Site.objects.get_current()
    site_name = current_site.name
    domain = current_site.domain
    
    # Generate confirmation token
    uid = urlsafe_base64_encode(force_bytes(user.pk))
    token = default_token_generator.make_token(user)
    
    # Create confirmation link
    confirmation_link = f"http://{domain}/confirm-email/{uid}/{token}/"
    
    context = {
        'user': user,
        'confirmation_link': confirmation_link,
        'site_name': site_name,
        'domain': domain,
    }
    
    # Render email templates
    html_content = render_to_string('accounts/email/confirmation_email.html', context)
    text_content = strip_tags(html_content)
    
    # Create email
    subject = f"Confirm your {site_name} account"
    from_email = settings.DEFAULT_FROM_EMAIL
    to_email = user.email
    
    # Send email
    email = EmailMultiAlternatives(subject, text_content, from_email, [to_email])
    email.attach_alternative(html_content, "text/html")
    email.send()
    
    return True
