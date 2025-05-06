from django import template
from django.utils.safestring import mark_safe
from accounts.models import CompanySettings

register = template.Library()

@register.simple_tag(takes_context=True)
def get_currency_symbol(context):
    """
    Returns the currency symbol for the current user's company
    """
    request = context.get('request')
    if not request or not hasattr(request, 'user') or not request.user.is_authenticated:
        return 'DT'  # Default currency if no user is authenticated
    
    # Try to get the user's company and its settings
    if hasattr(request.user, 'profile') and hasattr(request.user.profile, 'company'):
        company = request.user.profile.company
        if company:
            try:
                settings = CompanySettings.objects.get(company=company)
                return settings.currency
            except CompanySettings.DoesNotExist:
                pass
    
    # Default to DT if no company settings found
    return 'DT'

@register.filter(name='currency')
def currency(value, symbol=None):
    """
    Formats a number as currency with the given symbol
    Usage: {{ value|currency:"$" }} or {{ value|currency }}
    """
    if value is None:
        return ''
    
    try:
        value = float(value)
        formatted = f"{value:,.2f}"
    except (ValueError, TypeError):
        return value
    
    if symbol:
        return f"{formatted} {symbol}"
    else:
        return formatted

@register.simple_tag(takes_context=True)
def format_currency(context, value):
    """
    Formats a number as currency with the current user's company currency symbol
    Usage: {% format_currency value %}
    """
    if value is None:
        return ''
    
    try:
        value = float(value)
        formatted = f"{value:,.2f}"
    except (ValueError, TypeError):
        return value
    
    symbol = get_currency_symbol(context)
    return mark_safe(f"{formatted} {symbol}")
