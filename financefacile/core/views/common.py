from django.shortcuts import render
from django.contrib.auth import authenticate, login, logout
from django.http import *
from django.views.generic import TemplateView
from django.conf import settings

from django.db.models.functions import ExtractMonth, ExtractYear, Concat
from django.db.models import Sum, Func, CharField

from django.core.exceptions import ObjectDoesNotExist

from core import models

from datetime import datetime, timedelta

import json


class MonthName(Func):
    function = 'TRIM'
    template = "%(function)s(TO_CHAR(%(expressions)s, 'Month'))"
    output_field = CharField()


def generate_ls_month_year():
    ls_month_year = []
    current_date = datetime.now()
    for i in range(12):
        month_year = current_date.strftime("%B%Y")
        ls_month_year.append(month_year)
        current_date = current_date.replace(day=1) - timedelta(days=5)
    return ls_month_year[::-1]


def generate_stat_by_entry_type(queryset, entry_type, ls_month_year):
    stat_list = []
    for month_year in ls_month_year:
        try:
            stat_list.append(queryset.get(
                finance_entry_type=entry_type,
                month_year=month_year).get('total_sum'))
        except ObjectDoesNotExist:
            stat_list.append(0)
    return stat_list


def home(request):
    # Get the user's company and currency
    user_company = None
    currency_symbol = 'DT'  # Default currency
    
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
    
    # Filter finance entries by company
    finance_entries_charge = models.FinanceEntry.objects.filter(finance_entry_type=models.EntryType.CHARGE)
    finance_entries_revenue = models.FinanceEntry.objects.filter(finance_entry_type=models.EntryType.REVENUE)
    finance_entries_all = models.FinanceEntry.objects.all()
    
    # Apply company filter if user has a company
    if user_company:
        finance_entries_charge = finance_entries_charge.filter(company=user_company)
        finance_entries_revenue = finance_entries_revenue.filter(company=user_company)
        finance_entries_all = finance_entries_all.filter(company=user_company)
    
    total_charge = sum(finance_entries_charge.values_list('entry_value', flat=True) or [0])
    total_revenue = sum(finance_entries_revenue.values_list('entry_value', flat=True) or [0])

    qs_stats = finance_entries_all.annotate(
        month=ExtractMonth("entry_date"),
        year=ExtractYear('entry_date'),
        month_name=MonthName('entry_date')
    ).annotate(
        month_year=Concat('month_name', 'year', output_field=CharField())
    ).values('month_year', 'finance_entry_type').annotate(
        total_sum=Sum('entry_value')
    ).order_by('month_year', 'finance_entry_type')

    ls_month_year = generate_ls_month_year()
    revenue_stats = generate_stat_by_entry_type(qs_stats, models.EntryType.REVENUE, ls_month_year)
    charge_stats = generate_stat_by_entry_type(qs_stats, models.EntryType.CHARGE, ls_month_year)

    stats = {
        'labels': ls_month_year,
        'datasets': [{
            "label": "Revenues (dt)",
            "data": revenue_stats
        }, {
            "label": "Charges (dt)",
            "data": charge_stats
        }
        ]
    }

    # --- Product stats for warehouse flash cards ---
    from datetime import timedelta
    from django.utils import timezone
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
    products_with_category = models.Product.objects.select_related('category').filter(is_archived=False)
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
    from django.utils import timezone
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

    # --- Pie chart: sold products by parent category (invoices) ---
    from core.models import InvoiceItem
    sold_qty_by_parent = {}
    
    for parent in parent_categories_query:
        descendants = set()
        stack = [parent]
        while stack:
            cat = stack.pop()
            descendants.add(cat.id)
            stack.extend(list(cat.children.all()))
        # Get invoice items query
        invoice_items_query = InvoiceItem.objects.filter(product__category_id__in=descendants)
        # Filter by company if user has a company
        if user_company:
            invoice_items_query = invoice_items_query.filter(invoice__company=user_company)
        sold_qty = invoice_items_query.aggregate(total=Sum('quantity'))['total'] or 0
        sold_qty_by_parent[parent.name] = sold_qty
        
    pie_invoice_by_category = {
        'labels': list(sold_qty_by_parent.keys()) if sold_qty_by_parent else [],
        'datasets': [{
            'label': 'Produits vendus',
            'data': list(sold_qty_by_parent.values()) if sold_qty_by_parent else [],
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

    context = {
        'total_charge': total_charge,
        'total_revenue': total_revenue,
        'stats': stats,
        'pie_products_by_category': json.dumps(pie_products_by_category),
        'pie_value_by_category': json.dumps(pie_value_by_category),
        'pie_invoice_by_category': json.dumps(pie_invoice_by_category),
        'product_count': product_count,
        'total_pieces': total_pieces,
        'warehouse_value': warehouse_value,
        'total_invoice_price': total_invoice_price,
        'recent_invoices': recent_invoices_query,
        'currency_symbol': currency_symbol,  # Add currency symbol to context
    }
    return render(request, 'index.html', context)


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

