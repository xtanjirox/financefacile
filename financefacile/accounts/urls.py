from django.urls import path, include
from . import views

# Authentication and profile management URLs
auth_patterns = [
    path('login/', views.CustomLoginView.as_view(), name='login'),
    path('logout/', views.CustomLogoutView.as_view(), name='logout'),
    path('profile/', views.ProfileView.as_view(), name='profile'),
    path('profile/edit/', views.ProfileUpdateView.as_view(), name='profile-edit'),
    path('profile/password/', views.CustomPasswordChangeView.as_view(), name='password-change'),
]

# User management URLs (admin only)
users_patterns = [
    path('', views.UsersListView.as_view(), name='users-list'),
    path('<int:pk>/permissions/', views.UserPermissionsView.as_view(), name='user-permissions'),
    path('<int:pk>/toggle-active/', views.toggle_user_active, name='toggle-user-active'),
]

# Company management URLs
organizations_patterns = [
    path('', views.CompanyListView.as_view(), name='company-list'),
    path('create/', views.CompanyCreateView.as_view(), name='company-create'),
    path('<int:pk>/', views.CompanyDetailView.as_view(), name='company-detail'),
    path('<int:pk>/edit/', views.CompanyUpdateView.as_view(), name='company-edit'),
    path('<int:pk>/settings/', views.CompanySettingsUpdateView.as_view(), name='company-settings'),
    path('<int:pk>/members/', views.CompanyMembersView.as_view(), name='company-members'),
    path('<int:company_id>/create-user/', views.CompanyUserCreateView.as_view(), name='company-user-create'),
    path('<int:company_id>/assign-user/<int:user_id>/', views.assign_user_to_company, name='assign-user-to-company'),
    path('<int:company_id>/remove-user/<int:user_id>/', views.remove_user_from_company, name='remove-user-from-company'),
    path('<int:company_id>/delete-user/<int:user_id>/', views.delete_company_user, name='delete-company-user'),
]

urlpatterns = [
    # Registration page
    path('register/', views.RegistrationView.as_view(), name='register'),
    
    # Email confirmation
    path('confirm-email/<str:uidb64>/<str:token>/', views.confirm_email, name='confirm-email'),
    path('resend-confirmation/', views.ResendConfirmationEmailView.as_view(), name='resend-confirmation'),
    
    # Include namespaced URL patterns
    path('auth/', include((auth_patterns, 'auth'))),
    path('users/', include((users_patterns, 'users'))),
    path('companies/', include((organizations_patterns, 'organizations'))),
]
