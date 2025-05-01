from django.urls import path
from . import views

urlpatterns = [
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
]
