from django.urls import path, include
from . import views
from .views import search_views
from .views import search_api
from .views.products_views import (
    ProductListView, ProductCreateView, ProductUpdateView, ProductDeleteView, ProductDetailView,
    ProductCategoryListView, ProductCategoryCreateView, ProductCategoryUpdateView, ProductCategoryDeleteView,
    InvoiceCreateView, InvoiceListView, InvoiceDetailView, InvoiceUpdateView, InvoiceDeleteView,
)
from django.contrib.auth.decorators import login_required

urlpatterns = [
    path('select2/', include('django_select2.urls')),
    path('invoices/', InvoiceListView.as_view(), name='invoice-list'),
    path('invoices/create/', InvoiceCreateView.as_view(), name='invoice-create'),
    path('invoices/<int:pk>/', InvoiceDetailView.as_view(), name='invoice-detail'),
    path('invoices/update/<int:pk>/', InvoiceUpdateView.as_view(), name='invoice-update'),
    path('invoices/delete/<int:pk>/', InvoiceDeleteView.as_view(), name='invoice-delete'),
    # Product Category CRUD
    path('categories/', ProductCategoryListView.as_view(), name='category-list'),
    path('categories/create/', ProductCategoryCreateView.as_view(), name='category-create'),
    path('categories/update/<int:pk>/', ProductCategoryUpdateView.as_view(), name='category-update'),
    path('categories/delete/<int:pk>/', ProductCategoryDeleteView.as_view(), name='category-delete'),
    # Product URLs
    path(r'products', ProductListView.as_view(), name='product-list'),
    path(r'products/create/', ProductCreateView.as_view(), name='product-create'),
    path(r'products/<int:pk>/', ProductDetailView.as_view(), name='product-detail'),
    path(r'products/update/<int:pk>/', ProductUpdateView.as_view(), name='product-update'),
    path(r'products/delete/<int:pk>/', ProductDeleteView.as_view(), name='product-delete'),
    path('search/', search_views.global_search, name='global-search'),
    path('api/live-search/', search_api.live_search, name='live-search-api'),
    path(r'', login_required(views.home), name='home'),

    path(r'finance_entry', views.FianceEntryListView.as_view(), name='entry-list'),
    path(r'finance_entry/update/<pk>', views.FianceEntryUpdateView.as_view(), name='entry-update'),
    path(r'finance_entry/create/', views.FianceEntryCreateView.as_view(), name='entry-create'),
    path(r'finance_entry/delete/<pk>', views.FianceEntryDeleteView.as_view(), name='entry-delete'),

    path(r'revenue', views.RevenueListView.as_view(), name='revenue-list'),

    path(r'charge', views.ChargeListView.as_view(), name='charge-list'),



    path(r'logout/', views.LogoutView.as_view()),
    path(r'login/', views.LoginView.as_view()),

]
