from django.urls import path, include
from . import views
from core.views.expenses_views import (
    ExpenseListView, ExpenseCreateView, ExpenseUpdateView, ExpenseDeleteView,
    ExpenseCategoryListView, ExpenseCategoryCreateView, ExpenseCategoryUpdateView, ExpenseCategoryDeleteView
)
from .views import search_views
from .views import search_api
from .views.products_views import (
    ProductListView, ProductCreateView, ProductUpdateView, ProductDeleteView, ProductDetailView, ProductRestoreView,
    ProductCategoryListView, ProductCategoryCreateView, ProductCategoryUpdateView, ProductCategoryDeleteView,
    InvoiceCreateView, InvoiceListView, InvoiceDetailView, InvoiceUpdateView, InvoiceDeleteView,
    ProductDataJsonView
)
from .views.invoice_pdf import generate_invoice_pdf
from .views.product_pdf import generate_product_pdf
from .views.expense_pdf import generate_expense_pdf
from django.contrib.auth.decorators import login_required

urlpatterns = [
    path('expenses/', ExpenseListView.as_view(), name='expenses-list'),
    path('expenses/create/', ExpenseCreateView.as_view(), name='expense-create'),
    path('expenses/update/<int:pk>/', ExpenseUpdateView.as_view(), name='expense-update'),
    path('expenses/delete/<int:pk>/', ExpenseDeleteView.as_view(), name='expense-delete'),
    path('expenses/pdf/', generate_expense_pdf, name='expenses-pdf'),
    path('expenses/pdf/<int:pk>/', generate_expense_pdf, name='expense-pdf'),

    path('expense-categories/', ExpenseCategoryListView.as_view(), name='expense-categories-list'),
    path('expense-categories/create/', ExpenseCategoryCreateView.as_view(), name='expense-category-create'),
    path('expense-categories/update/<int:pk>/', ExpenseCategoryUpdateView.as_view(), name='expense-category-update'),
    path('expense-categories/delete/<int:pk>/', ExpenseCategoryDeleteView.as_view(), name='expense-category-delete'),
    path('select2/', include('django_select2.urls')),
    path('invoices/', InvoiceListView.as_view(), name='invoice-list'),
    path('invoices/create/', InvoiceCreateView.as_view(), name='invoice-create'),
    path('invoices/<int:pk>/', InvoiceDetailView.as_view(), name='invoice-detail'),
    path('invoices/update/<int:pk>/', InvoiceUpdateView.as_view(), name='invoice-update'),
    path('invoices/delete/<int:pk>/', InvoiceDeleteView.as_view(), name='invoice-delete'),
    path('invoices/pdf/<int:pk>/', generate_invoice_pdf, name='invoice-pdf'),
    # Product Category CRUD
    path('categories/', ProductCategoryListView.as_view(), name='category-list'),
    path('categories/create/', ProductCategoryCreateView.as_view(), name='category-create'),
    path('categories/update/<int:pk>/', ProductCategoryUpdateView.as_view(), name='category-update'),
    path('categories/delete/<int:pk>/', ProductCategoryDeleteView.as_view(), name='category-delete'),
    # Product URLs
    path('products/', ProductListView.as_view(), name='product-list'),
    path('products/data/', ProductDataJsonView.as_view(), name='product-data-json'),
    path('products/create/', ProductCreateView.as_view(), name='product-create'),
    path('products/<int:pk>/', ProductDetailView.as_view(), name='product-detail'),
    path('products/update/<int:pk>/', ProductUpdateView.as_view(), name='product-update'),
    path('products/delete/<int:pk>/', ProductDeleteView.as_view(), name='product-delete'),
    path('products/restore/<int:pk>/', ProductRestoreView.as_view(), name='product-restore'),
    path('products/pdf/<int:pk>/', generate_product_pdf, name='product-pdf'),
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
