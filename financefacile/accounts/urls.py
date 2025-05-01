from django.urls import path
from . import views

urlpatterns = [
    # Landing page
    path('', views.LandingPageView.as_view(), name='landing-page'),
    path('register/', views.RegistrationView.as_view(), name='register'),
    # Authentication
    path('login/', views.CustomLoginView.as_view(), name='login'),
    path('logout/', views.CustomLogoutView.as_view(), name='logout'),
    
    # Profile management
    path('profile/', views.ProfileView.as_view(), name='profile'),
    path('profile/edit/', views.ProfileUpdateView.as_view(), name='profile-edit'),
    path('profile/password/', views.CustomPasswordChangeView.as_view(), name='password-change'),
    
    # User management (admin only)
    path('users/', views.UsersListView.as_view(), name='users-list'),
    path('users/<int:pk>/permissions/', views.UserPermissionsView.as_view(), name='user-permissions'),
    path('users/<int:pk>/toggle-active/', views.toggle_user_active, name='toggle-user-active'),
    
    # Company management
    path('companies/', views.CompanyListView.as_view(), name='company-list'),
    path('companies/create/', views.CompanyCreateView.as_view(), name='company-create'),
    path('companies/<int:pk>/', views.CompanyDetailView.as_view(), name='company-detail'),
    path('companies/<int:pk>/edit/', views.CompanyUpdateView.as_view(), name='company-edit'),
    path('companies/<int:pk>/settings/', views.CompanySettingsUpdateView.as_view(), name='company-settings'),
    path('companies/<int:pk>/members/', views.CompanyMembersView.as_view(), name='company-members'),
    path('companies/<int:company_id>/create-user/', views.CompanyUserCreateView.as_view(), name='company-user-create'),
    path('companies/<int:company_id>/assign-user/<int:user_id>/', views.assign_user_to_company, name='assign-user-to-company'),
    path('companies/<int:company_id>/remove-user/<int:user_id>/', views.remove_user_from_company, name='remove-user-from-company'),
]
