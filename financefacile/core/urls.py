from django.urls import path
from . import views
from django.contrib.auth.decorators import login_required

urlpatterns = [
    path(r'', login_required(views.home), name='home'),

    path(r'finance_entry', views.FianceEntryListView.as_view(), name='entry-list'),
    path(r'finance_entry/update/<pk>', views.FianceEntryUpdateView.as_view(), name='entry-update'),
    path(r'finance_entry/create/', views.FianceEntryCreateView.as_view(), name='entry-create'),
    path(r'finance_entry/delete/<pk>', views.FianceEntryDeleteView.as_view(), name='entry-delete'),

    path(r'revenue', views.RevenueListView.as_view(), name='revenue-list'),

    path(r'charge', views.ChargeListView.as_view(), name='charge-list'),

    path(r'category', views.CategoryListView.as_view(), name='category-list'),
    path(r'category/update/<pk>', views.CategoryUpdateView.as_view(), name='category-update'),
    path(r'category/create', views.CategoryCreateView.as_view(), name='category-create'),
    path(r'category/delete/<pk>', views.CategoryDeleteView.as_view(), name='category-delete'),

    path(r'logout/', views.LogoutView.as_view()),
    path(r'login/', views.LoginView.as_view()),

]
