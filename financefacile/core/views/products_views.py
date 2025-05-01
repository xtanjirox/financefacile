from django.views.generic import DetailView, UpdateView, DeleteView
from django_select2 import forms as s2forms
from core.forms import DateRangeFilterForm, DateRangeCategoryFilterForm
from django.db.models import Q, Sum
from django.views.generic import ListView
from django.forms import modelformset_factory
from django.views.generic.edit import CreateView
from django.views import View
from django.views.generic import ListView, CreateView, UpdateView, DeleteView, DetailView
from django.urls import reverse_lazy
from django.shortcuts import redirect, render
from django.db.models import Sum
from django.contrib.auth.decorators import login_required
from django.utils.decorators import method_decorator

from core import models, tables
from core.models import InvoiceItem
import core.forms
from .base import BaseListView, FormViewMixin, BaseDeleteView
from .auth_mixins import BaseViewMixin, ProductPermissionMixin


class ProductCategoryListView(BaseListView):
    model = models.ProductCategory
    table_class = tables.ProductCategoryTable
    filter_class = None
    get_stats = False
    table_pagination = {'per_page': 10}
    create_url = reverse_lazy('category-create')
    segment = 'categories'
    detail = True


class ProductCategoryCreateView(CreateView, FormViewMixin):
    model = models.ProductCategory
    template_name = 'generic/create.html'
    fields = '__all__'
    segment = 'categories'
    success_url = reverse_lazy('category-list')


class ProductCategoryUpdateView(UpdateView, FormViewMixin):
    model = models.ProductCategory
    template_name = 'generic/detail.html'
    fields = '__all__'
    segment = 'categories'
    success_url = reverse_lazy('category-list')


class ProductCategoryDeleteView(BaseDeleteView):
    model = models.ProductCategory
    success_url = reverse_lazy('category-list')


class ProductListView(BaseListView):
    model = models.Product
    table_class = tables.ProductTable
    template_name = 'products/product_list.html'
    filter_class = None
    get_stats = False
    table_pagination = {'per_page': 10}
    create_url = reverse_lazy('product-create')
    segment = 'products'
    detail = True
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        
        # Calculate inventory stats
        products = models.Product.objects.all()
        
        # Calculate total inventory value (cost × quantity)
        total_inventory_value = sum(product.unit_cost * product.quantity for product in products)
        context['total_inventory_value'] = total_inventory_value
        
        # Calculate potential revenue (selling price × quantity)
        total_potential_revenue = sum(product.selling_price * product.quantity for product in products)
        context['total_potential_revenue'] = total_potential_revenue
        
        return context


class ProductCreateView(CreateView):
    def dispatch(self, *args, **kwargs):
        import sys
        print("DISPATCH ProductCreateView", file=sys.stderr)
        return super().dispatch(*args, **kwargs)

    model = models.Product
    form_class = core.forms.ProductForm
    print(form_class)
    template_name = 'generic/create.html'
    segment = 'products'
    success_url = reverse_lazy('product-list')


class ProductUpdateView(UpdateView):
    model = models.Product
    form_class = core.forms.ProductForm
    template_name = 'generic/detail.html'
    segment = 'products'
    success_url = reverse_lazy('product-list')


class ProductDeleteView(BaseDeleteView):
    model = models.Product
    success_url = reverse_lazy('product-list')


class ProductDetailView(DetailView):
    model = models.Product
    template_name = 'products/product_detail.html'
    context_object_name = 'object'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        # Find all InvoiceItems for this product, prefetch related invoice
        context['invoices'] = InvoiceItem.objects.filter(
            product=self.object).select_related('invoice')
        return context


class InvoiceCreateView(CreateView):
    model = models.Invoice
    form_class = core.forms.InvoiceForm
    template_name = 'invoices/invoice_form.html'
    success_url = None  # Will be set in form_valid

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        if self.request.POST:
            context['formset'] = core.forms.InvoiceItemFormSet(
                self.request.POST)
        else:
            context['formset'] = core.forms.InvoiceItemFormSet()
        self.add_products_to_context(context)
        return context

    def add_products_to_context(self, context):
        context['products'] = models.Product.objects.all()

    def form_valid(self, form):
        context = self.get_context_data()
        formset = context['formset']
        if not formset.is_valid():
            return self.form_invalid(form)
        self.object = form.save(commit=False)
        self.save_custom_total(form)
        self.object.save()
        formset.instance = self.object
        formset.save()
        self.update_inventory(formset)
        return redirect(self.object.get_absolute_url())

    def save_custom_total(self, form):
        invoice_total = form.cleaned_data.get('invoice_total')
        if invoice_total is not None:
            self.object.custom_total = invoice_total

    def update_inventory(self, formset):
        for item in self.object.items.all():
            product = item.product
            product.quantity = max(0, product.quantity - item.quantity)
            product.save()


class InvoiceListView(BaseViewMixin, ProductPermissionMixin, ListView):
    model = models.Invoice
    template_name = 'invoices/invoice_list.html'
    context_object_name = 'invoices'

    def get_queryset(self):
        queryset = super().get_queryset()

        # Get filter parameters from request
        start_date = self.request.GET.get('start_date')
        end_date = self.request.GET.get('end_date')

        # Apply date range filter if provided
        if start_date:
            queryset = queryset.filter(created_at__date__gte=start_date)
        if end_date:
            queryset = queryset.filter(created_at__date__lte=end_date)

        return queryset.order_by('-created_at')

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        from core.models import InvoiceItem

        # Initialize filter form
        filter_form = DateRangeCategoryFilterForm(self.request.GET or None)
        context['filter_form'] = filter_form

        # Get date range parameters
        start_date = self.request.GET.get('start_date')
        end_date = self.request.GET.get('end_date')

        # Apply date range filter to stats if provided
        invoice_filter = Q()
        if start_date:
            invoice_filter &= Q(created_at__date__gte=start_date)
            context['filter_start_date'] = start_date
            context['is_filtered'] = True
        if end_date:
            invoice_filter &= Q(created_at__date__lte=end_date)
            context['filter_end_date'] = end_date
            context['is_filtered'] = True

        # Calculate filtered stats if filter is applied
        if start_date or end_date:
            filtered_invoices = models.Invoice.objects.filter(invoice_filter)
            filtered_invoice_items = InvoiceItem.objects.filter(
                invoice__in=filtered_invoices)

            context['filtered_total_items'] = filtered_invoice_items.aggregate(
                total=Sum('quantity'))['total'] or 0
            context['filtered_total_value'] = sum(
                item.quantity * item.product.unit_cost for item in filtered_invoice_items.select_related('product')
            )
            context['filtered_total_price'] = filtered_invoices.aggregate(
                total=Sum('items__total_price'))['total'] or 0

        # Calculate overall stats regardless of filter
        total_items_sold = InvoiceItem.objects.aggregate(
            total=Sum('quantity'))['total'] or 0
        total_inventory_sold_value = sum(
            item.quantity * item.product.unit_cost for item in InvoiceItem.objects.select_related('product').all()
        )
        total_invoice_price = models.Invoice.objects.aggregate(
            total=Sum('items__total_price'))['total'] or 0

        context.update({
            'total_items_sold': total_items_sold,
            'total_inventory_sold_value': total_inventory_sold_value,
            'total_invoice_price': total_invoice_price,
        })
        return context


class InvoiceUpdateView(UpdateView):
    model = models.Invoice
    form_class = core.forms.InvoiceForm
    template_name = 'invoices/invoice_form.html'
    success_url = reverse_lazy('invoice-list')

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        if self.request.POST:
            context['formset'] = core.forms.InvoiceItemFormSet(
                self.request.POST, instance=self.object)
        else:
            context['formset'] = core.forms.InvoiceItemFormSet(
                instance=self.object)
        # Add all products for JS price autofill
        context['products'] = models.Product.objects.all()
        return context

    def form_valid(self, form):
        import logging
        from django.db import transaction
        logger = logging.getLogger(__name__)
        context = self.get_context_data()
        formset = context['formset']
        logger.debug('InvoiceUpdateView.form_valid called')
        logger.debug(f'Form valid: {form.is_valid()}')
        logger.debug(f'Formset valid: {formset.is_valid()}')
        logger.debug(f'POST data: {self.request.POST}')

        with transaction.atomic():
            if not formset.is_valid():
                self._log_formset_errors(logger, formset)
                return self.form_invalid(form)

            # Process the valid form and formset
            obj = self._save_invoice_with_total(form)
            formset.instance = obj

            # Update inventory
            self._restore_previous_inventory(logger, obj)
            formset.save()
            logger.debug(f'Formset saved for invoice {obj.pk}')
            self._update_inventory_for_new_items(logger, obj)

            logger.info(f'Invoice {obj.pk} updated successfully.')
            return redirect(self.get_success_url())

    def _save_invoice_with_total(self, form):
        # Save invoice object without committing to DB
        obj = form.save(commit=False)
        # Save custom total from form
        invoice_total = form.cleaned_data.get('invoice_total')
        if invoice_total is not None:
            obj.custom_total = invoice_total
        obj.save()
        return obj

    def _restore_previous_inventory(self, logger, obj):
        # Restore inventory for all previous items
        previous_items = list(obj.items.all())
        logger.debug(
            f'Restoring inventory for previous items: {previous_items}')
        for item in previous_items:
            product = item.product
            logger.debug(
                f'Before restore: {product.name} quantity={product.quantity}, restoring {item.quantity}')
            product.quantity += item.quantity
            product.save()
            logger.debug(
                f'After restore: {product.name} quantity={product.quantity}')

    def _update_inventory_for_new_items(self, logger, obj):
        # Subtract inventory for all new items
        logger.debug(
            f'Adjusting inventory for new items: {list(obj.items.all())}')
        for item in obj.items.all():
            product = item.product
            logger.debug(
                f'Before subtract: {product.name} quantity={product.quantity}, subtracting {item.quantity}')
            product.quantity = max(0, product.quantity - item.quantity)
            product.save()
            logger.debug(
                f'After subtract: {product.name} quantity={product.quantity}')

    def _log_formset_errors(self, logger, formset):
        logger.error('Formset invalid during invoice update')
        logger.error(f'Formset errors: {formset.errors}')
        logger.error(f'Non-form errors: {formset.non_form_errors()}')


class InvoiceDeleteView(DeleteView):
    model = models.Invoice
    template_name = 'invoices/invoice_confirm_delete.html'
    success_url = reverse_lazy('invoice-list')

    def delete(self, request, *args, **kwargs):
        self.object = self.get_object()
        # Restore inventory for all items in the invoice
        for item in self.object.items.all():
            product = item.product
            product.quantity += item.quantity
            product.save()
        return super().delete(request, *args, **kwargs)


class InvoiceDetailView(DetailView):
    model = models.Invoice
    template_name = 'invoices/invoice_detail.html'
    context_object_name = 'invoice'
