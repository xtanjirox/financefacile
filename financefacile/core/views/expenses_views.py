from django.shortcuts import render, redirect, get_object_or_404
from django.contrib import messages
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
        
        # Initialize filter form with the current user
        filter_form = DateRangeFilterForm(self.request.GET or None, user=self.request.user)
        context['filter_form'] = filter_form
        context['page_title'] = 'Expenses'
        context['page_title_badge'] = 'Expenses'
        
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
            
            # Get expense data by category for the filtered data
            expense_by_category = expense_queryset.filter(filter_query).values('category__name').annotate(
                total=Sum('amount')
            ).order_by('-total')
            
            # Prepare data for ApexCharts
            expense_categories_labels = [item['category__name'] or 'Uncategorized' for item in expense_by_category]
            expense_categories_series = [float(item['total']) for item in expense_by_category]
            
            # Add to context
            context['expense_categories_labels'] = expense_categories_labels
            context['expense_categories_series'] = expense_categories_series
        
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
        
        # Get expense data by category for the current month (non-filtered view)
        if not is_filtered:
            expense_by_category = expense_queryset.filter(month_filter).values('category__name').annotate(
                total=Sum('amount')
            ).order_by('-total')
            
            # Prepare data for ApexCharts
            expense_categories_labels = [item['category__name'] or 'Uncategorized' for item in expense_by_category]
            expense_categories_series = [float(item['total']) for item in expense_by_category]
            
            # Add to context
            context['expense_categories_labels'] = expense_categories_labels
            context['expense_categories_series'] = expense_categories_series
            
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
    template_name = 'expenses/expense_form_product_style.html'
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
    template_name = 'expenses/expense_form_product_style.html'
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
    template_name = 'expenses/expense_categories_list_modern.html'
    context_object_name = 'categories'
    
    def get_queryset(self):
        # Filter categories by the user's company
        queryset = super().get_queryset()
        if self.request.user.is_superuser or self.request.user.is_staff:
            return queryset
        if hasattr(self.request.user, 'profile') and self.request.user.profile.company:
            return queryset.filter(company=self.request.user.profile.company)
        return queryset.none()
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        
        # Get total expenses count
        total_expenses = 0
        monthly_expenses = 0
        
        from django.utils import timezone
        import datetime
        
        # Get current month's start and end dates
        today = timezone.now().date()
        month_start = datetime.date(today.year, today.month, 1)
        
        # If user has a company profile, count expenses
        if hasattr(self.request.user, 'profile') and self.request.user.profile.company:
            company = self.request.user.profile.company
            from ..models import Expense
            
            # Count total expenses
            total_expenses = Expense.objects.filter(company=company).count()
            
            # Count expenses for current month
            monthly_expenses = Expense.objects.filter(
                company=company,
                date__gte=month_start,
                date__lte=today
            ).count()
        
        context['total_expenses'] = total_expenses
        context['monthly_expenses'] = monthly_expenses
        
        return context

class ExpenseCategoryCreateView(BaseViewMixin, ExpensePermissionMixin, CreateView):
    model = ExpenseCategory
    form_class = ExpenseCategoryForm
    template_name = 'expenses/expense_category_form_modern.html'
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
    template_name = 'expenses/expense_category_form_modern.html'
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
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        # Count related expenses for this category
        related_expenses_count = Expense.objects.filter(category=self.object).count()
        context['related_expenses_count'] = related_expenses_count
        return context
        
    def post(self, request, *args, **kwargs):
        self.object = self.get_object()
        # Check if category has related expenses
        related_expenses_count = Expense.objects.filter(category=self.object).count()
        if related_expenses_count > 0:
            messages.error(request, f"Cannot delete category '{self.object.name}' because it has {related_expenses_count} related expenses.")
            return redirect('expense-categories-list')
        return super().post(request, *args, **kwargs)
