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
from .views.calendar_views import (
    CalendarEventListView, CalendarEventCreateView, CalendarEventUpdateView, 
    CalendarEventDeleteView, CalendarEventDetailView, calendar_events_json, date_events
)
from .views.calendar_display import CalendarDisplayView
from .notification_views import get_user_notifications, mark_notification_read, mark_all_read

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
    
    # Calendar URLs
    path('calendar/', CalendarDisplayView.as_view(), name='calendar-display'),
    path('calendar/list/', CalendarEventListView.as_view(), name='calendar-event-list'),
    path('calendar/events/', calendar_events_json, name='calendar-events-json'),
    path('calendar/events/create/', CalendarEventCreateView.as_view(), name='calendar-event-create'),
    path('calendar/events/<int:pk>/', CalendarEventDetailView.as_view(), name='calendar-event-detail'),
    path('calendar/events/update/<int:pk>/', CalendarEventUpdateView.as_view(), name='calendar-event-update'),
    path('calendar/events/delete/<int:pk>/', CalendarEventDeleteView.as_view(), name='calendar-event-delete'),
    path('calendar/date/<int:year>/<int:month>/<int:day>/', date_events, name='calendar-date-events'),
    path('products/pdf/<int:pk>/', generate_product_pdf, name='product-pdf'),
    path('search/', search_views.global_search, name='global-search'),
    path('api/live-search/', search_api.live_search, name='live-search-api'),
    
    # Notification URLs
    path('api/notifications/', get_user_notifications, name='get-notifications'),  # Keep for backward compatibility
    path('core/api/notifications/', get_user_notifications, name='get-notifications-core'),  # New path matching JavaScript
    path('notifications/read/<int:notification_id>/', mark_notification_read, name='mark-notification-read'),
    path('core/notifications/read/<int:notification_id>/', mark_notification_read, name='mark-notification-read-core'),
    path('notifications/read-all/', mark_all_read, name='mark-all-notifications-read'),
    path('core/notifications/read-all/', mark_all_read, name='mark-all-notifications-read-core'),
    
    path(r'', login_required(views.home), name='home'),

    
    #path(r'finance_entry', views.FianceEntryListView.as_view(), name='entry-list'),
    #path(r'finance_entry/update/<pk>', views.FianceEntryUpdateView.as_view(), name='entry-update'),
    #path(r'finance_entry/create/', views.FianceEntryCreateView.as_view(), name='entry-create'),
    #path(r'finance_entry/delete/<pk>', views.FianceEntryDeleteView.as_view(), name='entry-delete'),
    
    # path(r'revenue', views.RevenueListView.as_view(), name='revenue-list'),

#    path(r'charge', views.ChargeListView.as_view(), name='charge-list'),



    path(r'logout/', views.LogoutView.as_view()),
    path(r'login/', views.LoginView.as_view()),

]
