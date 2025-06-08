from django.shortcuts import render, get_object_or_404
from django.contrib.auth import authenticate, login, logout
from django.http import *
from django.views.generic import TemplateView
from django.conf import settings
from django.db.models import Sum, Func, CharField
from django.contrib.auth.mixins import LoginRequiredMixin

from core import models
from core.models import CalendarEvent
from accounts.models import Company

from datetime import timedelta, datetime
from decimal import Decimal

import json
from django.utils import timezone

# Custom JSON encoder to handle Decimal types
class DecimalEncoder(json.JSONEncoder):
    def default(self, obj):
        if isinstance(obj, Decimal):
            return float(obj)
        return super(DecimalEncoder, self).default(obj)


class CompanyMixin(LoginRequiredMixin):
    """
    Mixin to handle company-specific functionality for class-based views.
    Assumes the user is authenticated and has a profile with a company.
    """
    def get_company(self):
        """Get the user's company."""
        if not hasattr(self.request.user, 'profile'):
            raise ValueError("User has no profile")
        if not hasattr(self.request.user.profile, 'company'):
            raise ValueError("User's profile has no company")
        return self.request.user.profile.company
        
    def get_queryset(self):
        """Filter queryset by user's company."""
        queryset = super().get_queryset()
        if hasattr(queryset, 'filter'):
            return queryset.filter(company=self.get_company())
        return queryset
        
    def form_valid(self, form):
        """Set the company before saving the form."""
        if hasattr(form.instance, 'company') and not form.instance.company_id:
            form.instance.company = self.get_company()
        return super().form_valid(form)




class MonthName(Func):
    function = 'TRIM'
    template = "%(function)s(TO_CHAR(%(expressions)s, 'Month'))"
    output_field = CharField()


def generate_ls_month_year():
    ls_month_year = []
    current_date = timezone.now()
    for i in range(12):
        month_year = current_date.strftime("%B%Y")
        ls_month_year.append(month_year)
        current_date = current_date.replace(day=1) - timedelta(days=5)
    return ls_month_year[::-1]


def home(request):
    # Get the user's company and currency
    user_company = None
    currency_symbol = 'DT'  # Default currency
    upcoming_events = []
    
    # Get upcoming calendar events if user is authenticated
    if request.user.is_authenticated and hasattr(request.user, 'profile') and hasattr(request.user.profile, 'company'):
        user_company = request.user.profile.company
        # Get next 10 upcoming events starting from the current date, ordered by start date
        today = timezone.localdate() 
        upcoming_events = CalendarEvent.objects.filter(
            company=user_company,
            start_date__date__gte=today
        ).order_by('start_date')[:10]
    else:
        upcoming_events = []
    
    if hasattr(request.user, 'profile') and hasattr(request.user.profile, 'company'):
        user_company = request.user.profile.company
        
        # Get currency from company settings
        if user_company:
            try:
                from accounts.models import CompanySettings
                company_settings = CompanySettings.objects.get(company=user_company)
                currency_symbol = company_settings.currency
            except Exception:
                # Use default if settings not found
                pass

    # --- Product stats for warehouse flash cards ---
    
    now = timezone.now()
    
    # Get all active products (exclude archived)
    products_query = models.Product.objects.filter(is_archived=False)
    
    # Filter products by company if user has a company
    if user_company:
        products_query = products_query.filter(company=user_company)
    
    product_count = products_query.count()
    total_pieces = sum(p.quantity for p in products_query) if product_count > 0 else 0
    warehouse_value = 0
    
    if product_count > 0:
        for p in products_query:
            age = now - p.created_at
            if age < timedelta(days=30):
                value = p.value_current
            elif age < timedelta(days=60):
                value = p.value_1_month
            elif age < timedelta(days=90):
                value = p.value_2_month
            else:
                value = p.value_3_month
            warehouse_value += p.quantity * value

    # --- Pie chart: products by parent category ---
    # Get parent categories
    parent_categories_query = models.ProductCategory.objects.filter(parent__isnull=True)
    
    # Filter categories by company if user has a company
    if user_company:
        parent_categories_query = parent_categories_query.filter(company=user_company)
        
    # Get products with category information (exclude archived)
    products_with_category = models.Product.objects \
        .select_related('category') \
        .filter(is_archived=False)

    if user_company:
        products_with_category = products_with_category.filter(company=user_company)
    category_qty = {}
    
    for parent in parent_categories_query:
        # Get all descendant categories (children, grandchildren, etc.)
        descendants = set()
        stack = [parent]
        while stack:
            cat = stack.pop()
            descendants.add(cat.id)
            stack.extend(list(cat.children.all()))
        # Aggregate the quantity for all products in this parent category and its descendants
        qty = products_with_category.filter(category_id__in=descendants).aggregate(total=Sum('quantity'))['total'] or 0
        category_qty[parent.name] = qty
    pie_products_by_category = {
        'labels': list(category_qty.keys()) if category_qty else [],
        'datasets': [{
            'label': 'Product Quantity',
            'data': list(category_qty.values()) if category_qty else [],
        }]
    }

    # --- Pie chart: inventory value by parent category ---
    now = timezone.now()
    value_by_parent = {}
    
    for parent in parent_categories_query:
        descendants = set()
        stack = [parent]
        while stack:
            cat = stack.pop()
            descendants.add(cat.id)
            stack.extend(list(cat.children.all()))
        value = 0
        for p in products_with_category.filter(category_id__in=descendants):
            age = now - p.created_at
            if age.days < 30:
                v = p.value_current
            elif age.days < 60:
                v = p.value_1_month
            elif age.days < 90:
                v = p.value_2_month
            else:
                v = p.value_3_month
            value += p.quantity * v
        value_by_parent[parent.name] = float(value)
        
    pie_value_by_category = {
        'labels': list(value_by_parent.keys()) if value_by_parent else [],
        'datasets': [{
            'label': 'Valeur du stock',
            'data': list(value_by_parent.values()) if value_by_parent else [],
        }]
    }

    # --- Pie chart: sold products by parent category (invoices) - total selling value ---
    
    sold_value_by_parent = {}
    
    for parent in parent_categories_query:
        descendants = set()
        stack = [parent]
        while stack:
            cat = stack.pop()
            descendants.add(cat.id)
            stack.extend(list(cat.children.all()))
        # Get invoice items query
        invoice_items_query = models.InvoiceItem.objects.filter(product__category_id__in=descendants)
        # Filter by company if user has a company
        if user_company:
            invoice_items_query = invoice_items_query.filter(invoice__company=user_company)
        # Calculate total selling value (total_price is quantity * selling_price)
        sold_value = invoice_items_query.aggregate(total=Sum('total_price'))['total'] or 0
        sold_value_by_parent[parent.name] = float(sold_value)
        
    pie_invoice_by_category = {
        'labels': list(sold_value_by_parent.keys()) if sold_value_by_parent else [],
        'datasets': [{
            'label': 'Valeur des ventes',
            'data': list(sold_value_by_parent.values()) if sold_value_by_parent else [],
        }]
    }

    # --- Calculate the sum of all invoices for dashboard card ---
    # Get all invoices
    invoices_query = models.Invoice.objects.all().prefetch_related('items')
    # Filter invoices by company if user has a company
    if user_company:
        invoices_query = invoices_query.filter(company=user_company)
    total_invoice_price = sum(inv.get_total() for inv in invoices_query) if invoices_query.exists() else 0

    # Get recent invoices - filter by company first, then slice
    recent_invoices_query = models.Invoice.objects.all()
    # Filter recent invoices by company if user has a company
    if user_company:
        recent_invoices_query = recent_invoices_query.filter(company=user_company)
    # Now take the slice after filtering
    recent_invoices_query = recent_invoices_query.order_by('-created_at')[:10]

    # Get current date information for Revenue Forecast component
    current_date = timezone.now()
    current_year = current_date.year
    previous_year = current_year - 1
    
    # Get month names for dropdown
    current_month = current_date.strftime("%B")
    next_month_date = current_date.replace(day=1) + timedelta(days=32)
    next_month_date = next_month_date.replace(day=1)
    next_month = next_month_date.strftime("%B")
    
    next_next_month_date = next_month_date.replace(day=1) + timedelta(days=32)
    next_next_month_date = next_next_month_date.replace(day=1)
    next_next_month = next_next_month_date.strftime("%B")
    
    # Generate monthly revenue data for current and previous years
    monthly_revenue_current_year = [0] * 12
    monthly_revenue_previous_year = [0] * 12
    
    # Generate monthly expense data for current and previous years
    monthly_expense_current_year = [0] * 12
    monthly_expense_previous_year = [0] * 12
    
    if user_company:
        # Get all invoices for current and previous year - use timezone-aware datetimes
        tz = timezone.get_current_timezone()
        current_year_start = timezone.make_aware(datetime(current_year, 1, 1), tz)
        current_year_end = timezone.make_aware(datetime(current_year, 12, 31, 23, 59, 59), tz)
        previous_year_start = timezone.make_aware(datetime(previous_year, 1, 1), tz)
        previous_year_end = timezone.make_aware(datetime(previous_year, 12, 31, 23, 59, 59), tz)
        
        # Get current year invoices
        current_year_invoices = models.Invoice.objects.filter(
            company=user_company,
            created_at__gte=current_year_start,
            created_at__lte=current_year_end
        )
        
        # Get previous year invoices
        previous_year_invoices = models.Invoice.objects.filter(
            company=user_company,
            created_at__gte=previous_year_start,
            created_at__lte=previous_year_end
        )
        
        # Get current year expenses
        current_year_expenses = models.Expense.objects.filter(
            company=user_company,
            date__gte=current_year_start.date(),
            date__lte=current_year_end.date()
        )
        
        # Get previous year expenses
        previous_year_expenses = models.Expense.objects.filter(
            company=user_company,
            date__gte=previous_year_start.date(),
            date__lte=previous_year_end.date()
        )
        
        # Calculate monthly revenue for current year
        for invoice in current_year_invoices:
            month_index = invoice.created_at.month - 1  # 0-based index
            monthly_revenue_current_year[month_index] += float(invoice.get_total())
        
        # Calculate monthly revenue for previous year
        for invoice in previous_year_invoices:
            month_index = invoice.created_at.month - 1  # 0-based index
            monthly_revenue_previous_year[month_index] += float(invoice.get_total())
        
        # Calculate monthly expenses for current year
        for expense in current_year_expenses:
            month_index = expense.date.month - 1  # 0-based index
            monthly_expense_current_year[month_index] += float(expense.amount)
        
        # Calculate monthly expenses for previous year
        for expense in previous_year_expenses:
            month_index = expense.date.month - 1  # 0-based index
            monthly_expense_previous_year[month_index] += float(expense.amount)
        
        # Calculate total previous year revenue
        previous_year_revenue = float(sum(monthly_revenue_previous_year))
    else:
        previous_year_revenue = 0
    
    # Get upcoming calendar events for the current user's company
    upcoming_events = []
    if user_company:
        upcoming_events = models.CalendarEvent.objects.filter(
            company=user_company,
            start_date__gte=timezone.now()
        ).order_by('start_date')[:20]  # Limit to 20 upcoming events
        
    # Get last 10 invoices
    recent_invoices = []
    if user_company:
        recent_invoices = models.Invoice.objects.filter(
            company=user_company
        ).order_by('-created_at')[:10]
        
    # Get last 10 expenses
    recent_expenses = []
    if user_company:
        recent_expenses = models.Expense.objects.filter(
            company=user_company
        ).order_by('-date')[:10]
    
    context = {
        'pie_products_by_category': json.dumps(pie_products_by_category, cls=DecimalEncoder),
        'pie_value_by_category': json.dumps(pie_value_by_category, cls=DecimalEncoder),
        'upcoming_events': upcoming_events,
        'recent_invoices': recent_invoices,
        'recent_expenses': recent_expenses,
        'pie_invoice_by_category': json.dumps(pie_invoice_by_category, cls=DecimalEncoder),
        'product_count': product_count,
        'total_pieces': total_pieces,
        'warehouse_value': warehouse_value,
        'total_invoice_price': total_invoice_price,
        'recent_invoices': recent_invoices_query,
        'currency_symbol': currency_symbol,  # Add currency symbol to context
        'upcoming_events': upcoming_events,  # Add upcoming events to context
        
        # Revenue Forecast context variables
        'current_year': current_year,
        'previous_year': previous_year,
        'current_month': current_month,
        'next_month': next_month,
        'next_next_month': next_next_month,
        'monthly_revenue_current_year': json.dumps(monthly_revenue_current_year, cls=DecimalEncoder),
        'monthly_revenue_previous_year': json.dumps(monthly_revenue_previous_year, cls=DecimalEncoder),
        'monthly_expense_current_year': json.dumps(monthly_expense_current_year, cls=DecimalEncoder),
        'monthly_expense_previous_year': json.dumps(monthly_expense_previous_year, cls=DecimalEncoder),
        'previous_year_revenue': previous_year_revenue,
    }
    context['page_title'] = 'Dashboard'
    context['page_title_badge'] = 'Dashboard'
    return render(request, 'index.html', context)


def dashboard(request):
    # Get the user's company and currency
    user_company = None
    currency_symbol = 'DT'  # Default currency
    upcoming_events = []
    
    # Get upcoming calendar events if user is authenticated
    if request.user.is_authenticated and hasattr(request.user, 'profile') and hasattr(request.user.profile, 'company'):
        user_company = request.user.profile.company
        # Get next 10 upcoming events starting from the current date, ordered by start date
        today = timezone.localdate() 
        upcoming_events = CalendarEvent.objects.filter(
            company=user_company,
            start_date__date__gte=today
        ).order_by('start_date')[:10]
    else:
        upcoming_events = []
    
    if hasattr(request.user, 'profile') and hasattr(request.user.profile, 'company'):
        user_company = request.user.profile.company
        
        # Get currency from company settings
        if user_company:
            try:
                from accounts.models import CompanySettings
                company_settings = CompanySettings.objects.get(company=user_company)
                currency_symbol = company_settings.currency
            except Exception:
                # Use default if settings not found
                pass

    # --- Product stats for warehouse flash cards ---
    
    now = timezone.now()
    
    # Get all active products (exclude archived)
    products_query = models.Product.objects.filter(is_archived=False)
    
    # Filter products by company if user has a company
    if user_company:
        products_query = products_query.filter(company=user_company)
    
    product_count = products_query.count()
    total_pieces = sum(p.quantity for p in products_query) if product_count > 0 else 0
    warehouse_value = 0
    
    if product_count > 0:
        for p in products_query:
            age = now - p.created_at
            if age < timedelta(days=30):
                value = p.value_current
            elif age < timedelta(days=60):
                value = p.value_1_month
            elif age < timedelta(days=90):
                value = p.value_2_month
            else:
                value = p.value_3_month
            warehouse_value += p.quantity * value

    # --- Pie chart: products by parent category ---
    # Get parent categories
    parent_categories_query = models.ProductCategory.objects.filter(parent__isnull=True)
    
    # Filter categories by company if user has a company
    if user_company:
        parent_categories_query = parent_categories_query.filter(company=user_company)
        
    # Get products with category information (exclude archived)
    products_with_category = models.Product.objects \
        .select_related('category') \
        .filter(is_archived=False)

    if user_company:
        products_with_category = products_with_category.filter(company=user_company)
    category_qty = {}
    
    for parent in parent_categories_query:
        # Get all descendant categories (children, grandchildren, etc.)
        descendants = set()
        stack = [parent]
        while stack:
            cat = stack.pop()
            descendants.add(cat.id)
            stack.extend(list(cat.children.all()))
        # Aggregate the quantity for all products in this parent category and its descendants
        qty = products_with_category.filter(category_id__in=descendants).aggregate(total=Sum('quantity'))['total'] or 0
        category_qty[parent.name] = qty
    pie_products_by_category = {
        'labels': list(category_qty.keys()) if category_qty else [],
        'datasets': [{
            'label': 'Product Quantity',
            'data': list(category_qty.values()) if category_qty else [],
        }]
    }

    # --- Pie chart: inventory value by parent category ---
    now = timezone.now()
    value_by_parent = {}
    
    for parent in parent_categories_query:
        descendants = set()
        stack = [parent]
        while stack:
            cat = stack.pop()
            descendants.add(cat.id)
            stack.extend(list(cat.children.all()))
        value = 0
        for p in products_with_category.filter(category_id__in=descendants):
            age = now - p.created_at
            if age.days < 30:
                v = p.value_current
            elif age.days < 60:
                v = p.value_1_month
            elif age.days < 90:
                v = p.value_2_month
            else:
                v = p.value_3_month
            value += p.quantity * v
        value_by_parent[parent.name] = float(value)
        
    pie_value_by_category = {
        'labels': list(value_by_parent.keys()) if value_by_parent else [],
        'datasets': [{
            'label': 'Valeur du stock',
            'data': list(value_by_parent.values()) if value_by_parent else [],
        }]
    }

    # --- Pie chart: sold products by parent category (invoices) - total selling value ---
    
    sold_value_by_parent = {}
    
    for parent in parent_categories_query:
        descendants = set()
        stack = [parent]
        while stack:
            cat = stack.pop()
            descendants.add(cat.id)
            stack.extend(list(cat.children.all()))
        # Get invoice items query
        invoice_items_query = models.InvoiceItem.objects.filter(product__category_id__in=descendants)
        # Filter by company if user has a company
        if user_company:
            invoice_items_query = invoice_items_query.filter(invoice__company=user_company)
        # Calculate total selling value (total_price is quantity * selling_price)
        sold_value = invoice_items_query.aggregate(total=Sum('total_price'))['total'] or 0
        sold_value_by_parent[parent.name] = float(sold_value)
        
    pie_invoice_by_category = {
        'labels': list(sold_value_by_parent.keys()) if sold_value_by_parent else [],
        'datasets': [{
            'label': 'Valeur des ventes',
            'data': list(sold_value_by_parent.values()) if sold_value_by_parent else [],
        }]
    }

    # --- Calculate the sum of all invoices for dashboard card ---
    # Get all invoices
    invoices_query = models.Invoice.objects.all().prefetch_related('items')
    # Filter invoices by company if user has a company
    if user_company:
        invoices_query = invoices_query.filter(company=user_company)
    total_invoice_price = sum(inv.get_total() for inv in invoices_query) if invoices_query.exists() else 0

    # Get recent invoices - filter by company first, then slice
    recent_invoices_query = models.Invoice.objects.all()
    # Filter recent invoices by company if user has a company
    if user_company:
        recent_invoices_query = recent_invoices_query.filter(company=user_company)
    # Now take the slice after filtering
    recent_invoices_query = recent_invoices_query.order_by('-created_at')[:10]

    # Get current date information for Revenue Forecast component
    current_date = timezone.now()
    current_year = current_date.year
    previous_year = current_year - 1
    
    # Get month names for dropdown
    current_month = current_date.strftime("%B")
    next_month_date = current_date.replace(day=1) + timedelta(days=32)
    next_month_date = next_month_date.replace(day=1)
    next_month = next_month_date.strftime("%B")
    
    next_next_month_date = next_month_date.replace(day=1) + timedelta(days=32)
    next_next_month_date = next_next_month_date.replace(day=1)
    next_next_month = next_next_month_date.strftime("%B")
    
    # Generate monthly revenue data for current and previous years
    monthly_revenue_current_year = [0] * 12
    monthly_revenue_previous_year = [0] * 12
    
    # Generate monthly expense data for current and previous years
    monthly_expense_current_year = [0] * 12
    monthly_expense_previous_year = [0] * 12
    
    if user_company:
        # Get all invoices for current and previous year - use timezone-aware datetimes
        tz = timezone.get_current_timezone()
        current_year_start = timezone.make_aware(datetime(current_year, 1, 1), tz)
        current_year_end = timezone.make_aware(datetime(current_year, 12, 31, 23, 59, 59), tz)
        previous_year_start = timezone.make_aware(datetime(previous_year, 1, 1), tz)
        previous_year_end = timezone.make_aware(datetime(previous_year, 12, 31, 23, 59, 59), tz)
        
        # Get current year invoices
        current_year_invoices = models.Invoice.objects.filter(
            company=user_company,
            created_at__gte=current_year_start,
            created_at__lte=current_year_end
        )
        
        # Get previous year invoices
        previous_year_invoices = models.Invoice.objects.filter(
            company=user_company,
            created_at__gte=previous_year_start,
            created_at__lte=previous_year_end
        )
        
        # Get current year expenses
        current_year_expenses = models.Expense.objects.filter(
            company=user_company,
            date__gte=current_year_start.date(),
            date__lte=current_year_end.date()
        )
        
        # Get previous year expenses
        previous_year_expenses = models.Expense.objects.filter(
            company=user_company,
            date__gte=previous_year_start.date(),
            date__lte=previous_year_end.date()
        )
        
        # Calculate monthly revenue for current year
        for invoice in current_year_invoices:
            month_index = invoice.created_at.month - 1  # 0-based index
            monthly_revenue_current_year[month_index] += float(invoice.get_total())
        
        # Calculate monthly revenue for previous year
        for invoice in previous_year_invoices:
            month_index = invoice.created_at.month - 1  # 0-based index
            monthly_revenue_previous_year[month_index] += float(invoice.get_total())
        
        # Calculate monthly expenses for current year
        for expense in current_year_expenses:
            month_index = expense.date.month - 1  # 0-based index
            monthly_expense_current_year[month_index] += float(expense.amount)
        
        # Calculate monthly expenses for previous year
        for expense in previous_year_expenses:
            month_index = expense.date.month - 1  # 0-based index
            monthly_expense_previous_year[month_index] += float(expense.amount)
        
        # Calculate total previous year revenue
        previous_year_revenue = float(sum(monthly_revenue_previous_year))
    else:
        previous_year_revenue = 0
    
    # Get upcoming calendar events for the current user's company
    upcoming_events = []
    if user_company:
        upcoming_events = models.CalendarEvent.objects.filter(
            company=user_company,
            start_date__gte=timezone.now()
        ).order_by('start_date')[:20]  # Limit to 20 upcoming events
        
    # Get last 10 invoices
    recent_invoices = []
    if user_company:
        recent_invoices = models.Invoice.objects.filter(
            company=user_company
        ).order_by('-created_at')[:10]
        
    # Get last 10 expenses
    recent_expenses = []
    if user_company:
        recent_expenses = models.Expense.objects.filter(
            company=user_company
        ).order_by('-date')[:10]
    
    context = {
        'pie_products_by_category': json.dumps(pie_products_by_category, cls=DecimalEncoder),
        'pie_value_by_category': json.dumps(pie_value_by_category, cls=DecimalEncoder),
        'upcoming_events': upcoming_events,
        'recent_invoices': recent_invoices,
        'recent_expenses': recent_expenses,
        'pie_invoice_by_category': json.dumps(pie_invoice_by_category, cls=DecimalEncoder),
        'product_count': product_count,
        'total_pieces': total_pieces,
        'warehouse_value': warehouse_value,
        'total_invoice_price': total_invoice_price,
        'recent_invoices': recent_invoices_query,
        'currency_symbol': currency_symbol,  # Add currency symbol to context
        'upcoming_events': upcoming_events,  # Add upcoming events to context
        
        # Revenue Forecast context variables
        'current_year': current_year,
        'previous_year': previous_year,
        'current_month': current_month,
        'next_month': next_month,
        'next_next_month': next_next_month,
        'monthly_revenue_current_year': json.dumps(monthly_revenue_current_year, cls=DecimalEncoder),
        'monthly_revenue_previous_year': json.dumps(monthly_revenue_previous_year, cls=DecimalEncoder),
        'monthly_expense_current_year': json.dumps(monthly_expense_current_year, cls=DecimalEncoder),
        'monthly_expense_previous_year': json.dumps(monthly_expense_previous_year, cls=DecimalEncoder),
        'previous_year_revenue': previous_year_revenue,
    }
    context['page_title'] = 'Dashboard'
    context['page_title_badge'] = 'Dashboard'
    return render(request, 'dashboard.html', context)


# Login Logout Views
class LoginView(TemplateView):
    template_name = 'registration/login.html'

    def post(self, request, **kwargs):
        username = request.POST.get('username', False)
        password = request.POST.get('password', False)
        user = authenticate(username=username, password=password)
        print('user', user)
        if user is not None and user.is_active:
            login(request, user)
            return HttpResponseRedirect(settings.LOGIN_REDIRECT_URL)

        return render(request, self.template_name)


class LogoutView(TemplateView):
    template_name = 'registration/login.html'

    def get(self, request, **kwargs):
        logout(request)

        return render(request, self.template_name)

