from django.contrib import admin
from django.urls import path, include
from django.conf import settings
from django.conf.urls.static import static
from django.contrib import admin
from django.views.generic import RedirectView

# Import custom error handlers
from accounts.views import handler403

urlpatterns = [
    path("admin/", admin.site.urls),
    # Redirect root URL to landing page
    path("", RedirectView.as_view(url='/landing/', permanent=False), name='index'),
    path("landing/", include("accounts.urls")),
    path("app/", include("core.urls")),
    path("api/", include("api.routes")),
    path("accounts/", include("accounts.urls")),
    path("select2/", include("django_select2.urls")),
] + static(settings.STATIC_URL, document_root=settings.STATIC_ROOT)
urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)

# Register custom error handlers
handler403 = 'accounts.views.handler403'  # Custom 403 Forbidden handler
