from django.contrib import admin
from django.urls import path, include
from django.conf import settings
from django.conf.urls.static import static
from django.contrib import admin
from django.views.generic import RedirectView

# Import views and custom error handlers
from accounts import views
from accounts.views import handler403
from core.views import search_api

urlpatterns = [
    path("admin/", admin.site.urls),
    # Include accounts URLs with proper namespaces
    path("landing/", views.LandingPageView.as_view(), name='landing-page'),
    path("", RedirectView.as_view(url='/landing/', permanent=False), name='index'),
    # Direct login URL to handle redirects from LoginRequiredMixin
    path("login/", RedirectView.as_view(url='/auth/login/', permanent=True)),
    path("", include("accounts.urls")),  # This includes auth, users, and organizations
    path("app/", include("core.urls")),
    path("api/", include("api.routes")),
    path("api/live-search/", search_api.live_search, name='live-search-api'),
    path("select2/", include("django_select2.urls")),
] + static(settings.STATIC_URL, document_root=settings.STATIC_ROOT)
urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)

# Register custom error handlers
handler403 = 'accounts.views.handler403'  # Custom 403 Forbidden handler
