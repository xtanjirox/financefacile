from django.shortcuts import render, get_object_or_404, redirect
from django.urls import reverse_lazy
from django.views import View
from django.views.generic import ListView, CreateView, UpdateView, DeleteView
from django.contrib.auth.decorators import login_required
from django.utils.decorators import method_decorator
from django.utils import timezone
from django.db.models import Sum, Q

from core.models import Expense, ExpenseCategory
from core.forms import ExpenseForm, ExpenseCategoryForm, DateRangeFilterForm
from .auth_mixins import BaseViewMixin, ExpensePermissionMixin, CompanyFilterMixin
from accounts.models import CompanySettings

class ExpenseListView(BaseViewMixin, ExpensePermissionMixin, CompanyFilterMixin, ListView):
    model = Expense
    template_name = 'expenses/expenses_list.html'
    context_object_name = 'expenses'
    
    def get_queryset(self):
        queryset = super().get_queryset()
        
        # Get filter parameters from request
        start_date = self.request.GET.get('start_date')
        end_date = self.request.GET.get('end_date')
        category_names = self.request.GET.getlist('category_name')
        
        # Apply date range filter if provided
        if start_date:
            queryset = queryset.filter(date__gte=start_date)
        if end_date:
            queryset = queryset.filter(date__lte=end_date)
        if category_names:
            # Filter by multiple category names
            queryset = queryset.filter(category__name__in=category_names)
            
        return queryset.order_by('-date')

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        now = timezone.now()
        
        # Initialize filter form
        filter_form = DateRangeFilterForm(self.request.GET or None)
        context['filter_form'] = filter_form
        
        # Get filter parameters
        start_date = self.request.GET.get('start_date')
        end_date = self.request.GET.get('end_date')
        category_names = self.request.GET.getlist('category_name')
        
        # Create base queryset filtered by company
        expense_queryset = Expense.objects
        if not self.request.user.is_superuser and not self.request.user.is_staff:
            if hasattr(self.request.user, 'profile') and self.request.user.profile.company:
                expense_queryset = expense_queryset.filter(company=self.request.user.profile.company)
        
        # Current month expenses for the stats card
        month_filter = Q(date__year=now.year, date__month=now.month)
        
        # Build filter for stats
        filter_query = Q()
        is_filtered = False
        filter_description = []
        
        if start_date:
            filter_query &= Q(date__gte=start_date)
            context['filter_start_date'] = start_date
            filter_description.append(f"From {start_date}")
            is_filtered = True
            
        if end_date:
            filter_query &= Q(date__lte=end_date)
            context['filter_end_date'] = end_date
            filter_description.append(f"To {end_date}")
            is_filtered = True
            
        if category_names:
            filter_query &= Q(category__name__in=category_names)
            context['filter_category_names'] = category_names
            categories_str = ", ".join(category_names)
            filter_description.append(f"Categories: {categories_str}")
            is_filtered = True
        
        # Apply filters to stats if provided
        if is_filtered:
            context['is_filtered'] = True
            context['filter_description'] = ", ".join(filter_description)
            context['filtered_total'] = expense_queryset.filter(filter_query).aggregate(total=Sum('amount'))['total'] or 0
        
        # Calculate current month stats regardless of filter
        month_expenses = expense_queryset.filter(month_filter)
        context['total_expenses'] = month_expenses.aggregate(total=Sum('amount'))['total'] or 0
        
        # Previous month
        prev_year = now.year if now.month > 1 else now.year - 1
        prev_month = now.month - 1 if now.month > 1 else 12
        prev_month_expenses = expense_queryset.filter(date__year=prev_year, date__month=prev_month)
        prev_total = prev_month_expenses.aggregate(total=Sum('amount'))['total'] or 0
        context['previous_month_expenses'] = prev_total
        
        # Percentage change
        if prev_total == 0 and context['total_expenses'] == 0:
            context['month_change_percent'] = 0
        elif prev_total == 0:
            context['month_change_percent'] = 100
        else:
            context['month_change_percent'] = ((context['total_expenses'] - prev_total) / prev_total) * 100
        
        # Add currency symbol to context
        currency_symbol = 'DT'  # Default currency
        if hasattr(self.request.user, 'profile') and hasattr(self.request.user.profile, 'company') and self.request.user.profile.company:
            try:
                company_settings = CompanySettings.objects.get(company=self.request.user.profile.company)
                currency_symbol = company_settings.currency
            except CompanySettings.DoesNotExist:
                pass
        context['currency_symbol'] = currency_symbol
            
        return context

class ExpenseCreateView(BaseViewMixin, ExpensePermissionMixin, CreateView):
    model = Expense
    form_class = ExpenseForm
    template_name = 'expenses/expense_form.html'
    success_url = reverse_lazy('expenses-list')
    
    def get_form(self, form_class=None):
        form = super().get_form(form_class)
        # Filter category choices to only show categories from the user's company
        if not self.request.user.is_superuser and not self.request.user.is_staff:
            if hasattr(self.request.user, 'profile') and self.request.user.profile.company:
                form.fields['category'].queryset = ExpenseCategory.objects.filter(
                    company=self.request.user.profile.company
                )
        return form
    
    def form_valid(self, form):
        # Set the company and created_by for the new expense
        expense = form.save(commit=False)
        if not self.request.user.is_superuser and not self.request.user.is_staff:
            if hasattr(self.request.user, 'profile') and self.request.user.profile.company:
                expense.company = self.request.user.profile.company
        elif hasattr(self.request.user, 'profile') and self.request.user.profile.company:
            expense.company = self.request.user.profile.company
        
        expense.created_by = self.request.user
        expense.save()
        return super().form_valid(form)

class ExpenseUpdateView(BaseViewMixin, ExpensePermissionMixin, UpdateView):
    model = Expense
    form_class = ExpenseForm
    template_name = 'expenses/expense_form.html'
    success_url = reverse_lazy('expenses-list')
    
    def get_queryset(self):
        # Ensure users can only update expenses from their company
        queryset = super().get_queryset()
        if self.request.user.is_superuser or self.request.user.is_staff:
            return queryset
        if hasattr(self.request.user, 'profile') and self.request.user.profile.company:
            return queryset.filter(company=self.request.user.profile.company)
        return queryset.none()
    
    def get_form(self, form_class=None):
        form = super().get_form(form_class)
        # Filter category choices to only show categories from the user's company
        if not self.request.user.is_superuser and not self.request.user.is_staff:
            if hasattr(self.request.user, 'profile') and self.request.user.profile.company:
                form.fields['category'].queryset = ExpenseCategory.objects.filter(
                    company=self.request.user.profile.company
                )
        return form

class ExpenseDeleteView(BaseViewMixin, ExpensePermissionMixin, DeleteView):
    model = Expense
    template_name = 'expenses/expense_confirm_delete.html'
    success_url = reverse_lazy('expenses-list')
    
    def get_queryset(self):
        # Ensure users can only delete expenses from their company
        queryset = super().get_queryset()
        if self.request.user.is_superuser or self.request.user.is_staff:
            return queryset
        if hasattr(self.request.user, 'profile') and self.request.user.profile.company:
            return queryset.filter(company=self.request.user.profile.company)
        return queryset.none()

class ExpenseCategoryListView(BaseViewMixin, ExpensePermissionMixin, ListView):
    model = ExpenseCategory
    template_name = 'expenses/expense_categories_list.html'
    context_object_name = 'categories'
    
    def get_queryset(self):
        # Filter categories by the user's company
        queryset = super().get_queryset()
        if self.request.user.is_superuser or self.request.user.is_staff:
            return queryset
        if hasattr(self.request.user, 'profile') and self.request.user.profile.company:
            return queryset.filter(company=self.request.user.profile.company)
        return queryset.none()

class ExpenseCategoryCreateView(BaseViewMixin, ExpensePermissionMixin, CreateView):
    model = ExpenseCategory
    form_class = ExpenseCategoryForm
    template_name = 'expenses/expense_category_form.html'
    success_url = reverse_lazy('expense-categories-list')
    
    def form_valid(self, form):
        # Set the company for the new expense category
        category = form.save(commit=False)
        if not self.request.user.is_superuser and not self.request.user.is_staff:
            if hasattr(self.request.user, 'profile') and self.request.user.profile.company:
                category.company = self.request.user.profile.company
        elif hasattr(self.request.user, 'profile') and self.request.user.profile.company:
            category.company = self.request.user.profile.company
        category.save()
        return super().form_valid(form)

class ExpenseCategoryUpdateView(BaseViewMixin, ExpensePermissionMixin, UpdateView):
    model = ExpenseCategory
    form_class = ExpenseCategoryForm
    template_name = 'expenses/expense_category_form.html'
    success_url = reverse_lazy('expense-categories-list')
    
    def get_queryset(self):
        # Ensure users can only update categories from their company
        queryset = super().get_queryset()
        if self.request.user.is_superuser or self.request.user.is_staff:
            return queryset
        if hasattr(self.request.user, 'profile') and self.request.user.profile.company:
            return queryset.filter(company=self.request.user.profile.company)
        return queryset.none()

class ExpenseCategoryDeleteView(BaseViewMixin, ExpensePermissionMixin, DeleteView):
    model = ExpenseCategory
    template_name = 'expenses/expense_category_confirm_delete.html'
    success_url = reverse_lazy('expense-categories-list')
    
    def get_queryset(self):
        # Ensure users can only delete categories from their company
        queryset = super().get_queryset()
        if self.request.user.is_superuser or self.request.user.is_staff:
            return queryset
        if hasattr(self.request.user, 'profile') and self.request.user.profile.company:
            return queryset.filter(company=self.request.user.profile.company)
        return queryset.none()
