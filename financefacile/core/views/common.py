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
    total_charge = sum(models.FinanceEntry.objects.filter(
        finance_entry_type=models.EntryType.CHARGE
    ).values_list('entry_value', flat=True))

    total_revenue = sum(models.FinanceEntry.objects.filter(
        finance_entry_type=models.EntryType.REVENUE
    ).values_list('entry_value', flat=True))

    qs_stats = models.FinanceEntry.objects.all().annotate(
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
    products = models.Product.objects.all()
    product_count = products.count()
    total_pieces = sum(p.quantity for p in products)
    warehouse_value = 0
    for p in products:
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
    parent_categories = models.ProductCategory.objects.filter(parent__isnull=True)
    products = models.Product.objects.select_related('category')
    category_qty = {}
    for parent in parent_categories:
        # Get all descendant categories (children, grandchildren, etc.)
        descendants = set()
        stack = [parent]
        while stack:
            cat = stack.pop()
            descendants.add(cat.id)
            stack.extend(list(cat.children.all()))
        # Aggregate the quantity for all products in this parent category and its descendants
        qty = products.filter(category_id__in=descendants).aggregate(total=Sum('quantity'))['total'] or 0
        category_qty[parent.name] = qty
    pie_products_by_category = {
        'labels': list(category_qty.keys()),
        'datasets': [{
            'label': 'Product Quantity',
            'data': list(category_qty.values()),
        }]
    }

    # --- Pie chart: inventory value by parent category ---
    from django.utils import timezone
    now = timezone.now()
    value_by_parent = {}
    for parent in parent_categories:
        descendants = set()
        stack = [parent]
        while stack:
            cat = stack.pop()
            descendants.add(cat.id)
            stack.extend(list(cat.children.all()))
        value = 0
        for p in products.filter(category_id__in=descendants):
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
        'labels': list(value_by_parent.keys()),
        'datasets': [{
            'label': 'Valeur du stock',
            'data': list(value_by_parent.values()),
        }]
    }

    # --- Pie chart: sold products by parent category (invoices) ---
    from core.models import InvoiceItem
    sold_qty_by_parent = {}
    for parent in parent_categories:
        descendants = set()
        stack = [parent]
        while stack:
            cat = stack.pop()
            descendants.add(cat.id)
            stack.extend(list(cat.children.all()))
        sold_qty = InvoiceItem.objects.filter(product__category_id__in=descendants).aggregate(total=Sum('quantity'))['total'] or 0
        sold_qty_by_parent[parent.name] = sold_qty
    pie_invoice_by_category = {
        'labels': list(sold_qty_by_parent.keys()),
        'datasets': [{
            'label': 'Produits vendus',
            'data': list(sold_qty_by_parent.values()),
        }]
    }

    # --- Calculate the sum of all invoices for dashboard card ---
    invoices = models.Invoice.objects.prefetch_related('items').all()
    total_invoice_price = sum(inv.get_total() for inv in invoices)

    recent_invoices = models.Invoice.objects.order_by('-created_at')[:10]

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
        'recent_invoices': recent_invoices,
    }
    return render(request, 'index.html', context)
    context = {
        'total_charge': total_charge,
        'total_revenue': total_revenue,
        'total_marge': total_revenue - total_charge,
        'data': json.dumps(stats),
        'table': models.FinanceEntry.objects.all().order_by('-entry_date')[:8],
        'ls_stats': [total_revenue, total_charge],
        'product_count': product_count,
        'warehouse_value': warehouse_value,
        'total_pieces': total_pieces,
        'pie_products_by_category': json.dumps(pie_products_by_category),
        'pie_value_by_category': json.dumps(pie_value_by_category),
        'pie_invoice_by_category': json.dumps(pie_invoice_by_category),
        'total_invoice_price': total_invoice_price,
        'recent_invoices': recent_invoices,
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

