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

    context = {
        'total_charge': total_charge,
        'total_revenue': total_revenue,
        'total_marge': total_revenue - total_charge,
        'data': json.dumps(stats),
        'table': models.FinanceEntry.objects.all().order_by('-entry_date')[:8],
        'ls_stats': [total_revenue, total_charge],
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

