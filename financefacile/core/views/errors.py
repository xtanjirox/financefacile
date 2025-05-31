from django.shortcuts import render
from django.utils.translation import gettext_lazy as _

def custom_404_view(request, exception):
    """Custom 404 error view that renders our modern 404 page."""
    context = {
        'title': _('Page Not Found'),
        'exception': str(exception) if str(exception) else _('The requested page was not found.')
    }
    return render(request, '404.html', context, status=404)

def custom_403_view(request, exception=None):
    """Custom 403 error view that renders our modern permission denied page."""
    context = {
        'title': _('Permission Denied'),
        'exception': str(exception) if exception and str(exception) else _('You do not have permission to access this resource.')
    }
    return render(request, '403.html', context, status=403)
