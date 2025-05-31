import logging
from django.conf import settings

from django.views.generic import (
    DetailView, UpdateView, 
    DeleteView, ListView, CreateView)
from django.db.models import Sum
from django.views import View
from django.urls import reverse_lazy
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib import messages

from core import models, tables
import core.forms
from core.forms import DateRangeFilterFormNew
from accounts import models as ac_models


from .base import BaseListView, FormViewMixin, BaseDeleteView
from .auth_mixins import BaseViewMixin, ProductPermissionMixin, InvoicePermissionMixin, CompanyFilterMixin


from django.http import JsonResponse


logger = logging.getLogger(__name__)

class ProductCategoryListView(BaseListView):
    model = models.ProductCategory
    table_class = tables.ProductCategoryTable
    filter_class = None
    get_stats = False
    table_pagination = {'per_page': 10}
    create_url = reverse_lazy('category-create')
    segment = 'categories'
    detail = True
    template_name = 'products/product_category_list_modern.html'
    
    def get_queryset(self):
        logger.info("\n=== Starting get_queryset for user: %s ===", self.request.user)
        # Start with the base queryset
        queryset = super().get_queryset()
        user = self.request.user
        
        # Log user and profile info for debugging
        logger.info(f"User: {user} (ID: {user.id if user.id else 'anon'})")
        logger.info(f"User attributes: is_authenticated={user.is_authenticated}, is_staff={user.is_staff}, is_superuser={user.is_superuser}")
        
        if user.is_authenticated:
            logger.info("User is authenticated")
            if hasattr(user, 'profile'):
                logger.info(f"User has profile: {user.profile}")
                if hasattr(user.profile, 'company'):
                    logger.info(f"User's company: {user.profile.company} (ID: {user.profile.company.id if user.profile.company else 'None'})")
                else:
                    logger.warning("User's profile has no company attribute")
            else:
                logger.warning("User has no profile")
        else:
            logger.warning("User is not authenticated")
        
        # Log all categories in the database with their company info
        try:
            all_categories = list(queryset.values('id', 'name', 'company__id', 'company__name'))
            logger.info("\n=== All categories in database ===")
            for cat in all_categories:
                logger.info(f"- {cat['name']} (ID: {cat['id']}) - Company: {cat['company__name']} (ID: {cat['company__id']})")
        except Exception as e:
            logger.error(f"Error fetching categories: {str(e)}")
        
        # Superusers and staff can see all categories
        if user.is_superuser or user.is_staff:
            logger.info("\n=== User is superuser or staff, returning all categories ===")
            return queryset
        
        # Regular users can see their company's categories
        if hasattr(user, 'profile') and hasattr(user.profile, 'company') and user.profile.company:
            company = user.profile.company
            logger.info(f"\n=== Filtering categories for company: {company.name} (ID: {company.id}) ===")
            company_categories = list(queryset.filter(company=company).values('id', 'name'))
            logger.info(f"Found {len(company_categories)} categories for this company")
            for cat in company_categories:
                logger.info(f"- {cat['name']} (ID: {cat['id']})")
            return queryset.filter(company=company)
        
        # Log if user has no company
        if hasattr(user, 'profile'):
            logger.warning("\n=== User has profile but no company assigned ===")
        else:
            logger.warning("\n=== User has no profile ===")
            
        # For debugging, return all categories if in development
        if settings.DEBUG:
            logger.warning("\n=== DEBUG mode: Returning all categories ===")
            return queryset
            
        logger.warning("\n=== No categories to return ===")
        return queryset.none()
    
    def get_context_data(self, **kwargs):
        logger.info("\n=== Starting get_context_data ===")
        context = super().get_context_data(**kwargs)
        
        # Get the filtered queryset
        queryset = self.get_queryset()
        context['has_categories'] = queryset.exists()
        logger.info(f"has_categories: {context['has_categories']}")
        
        # Initialize the table with the filtered queryset and request
        table = self.table_class(queryset, order_by='name')
        
        # Configure the table's request attribute for URL generation
        if not hasattr(table, 'request'):
            table.request = self.request
        
        # Add the table to the context
        context['table'] = table
        context['segment'] = self.segment
        context['create_url'] = self.create_url
        
        # Configure the table for rendering
        table.paginate(page=self.request.GET.get('page', 1), per_page=10)
        
        # Log table data for debugging
        if hasattr(table, 'rows'):
            rows = list(table.rows)
            logger.info(f"Number of rows in table: {len(rows)}")
            for i, row in enumerate(rows, 1):
                logger.info(f"Row {i}: {row}")
        else:
            logger.warning("Table has no rows attribute")
        
        # Add dashboard card data
        total_categories = 0
        total_products_in_categories = 0
        inventory_value = 0
        
        # If user has a company profile, count products and categories
        if hasattr(self.request.user, 'profile') and self.request.user.profile.company:
            company = self.request.user.profile.company
            
            # Count total categories
            total_categories = models.ProductCategory.objects.filter(company=company).count()
            
            # Count products in categories and calculate inventory value
            from django.db.models import Sum, F
            products_query = models.Product.objects.filter(company=company, category__isnull=False)
            
            total_products_in_categories = products_query.count()
            
            # Calculate inventory value (quantity * selling_price)
            inventory_value_result = products_query.aggregate(
                total_value=Sum(F('quantity') * F('selling_price'), default=0)
            )
            inventory_value = inventory_value_result['total_value'] or 0
            
            # Format inventory value as currency
            from django.contrib.humanize.templatetags.humanize import intcomma
            inventory_value = f"${intcomma(round(inventory_value, 2))}"
        
        context['total_categories'] = total_categories
        context['total_products_in_categories'] = total_products_in_categories
        context['inventory_value'] = inventory_value
            
        logger.info(f"Context keys: {context.keys()}")
        return context
    
    def get(self, request, *args, **kwargs):
        # Always render the list view - the template will handle showing the empty state
        return super().get(request, *args, **kwargs)


class ProductCategoryCreateView(CreateView, FormViewMixin):
    model = models.ProductCategory
    template_name = 'products/product_category_form_modern.html'
    fields = ['name', 'parent']
    segment = 'categories'
    success_url = reverse_lazy('category-list')
    
    def get_form(self, form_class=None):
        form = super().get_form(form_class)
        # Filter parent categories to only show those from the same company
        if 'parent' in form.fields and hasattr(self.request.user, 'profile') and self.request.user.profile.company:
            form.fields['parent'].queryset = models.ProductCategory.objects.filter(
                company=self.request.user.profile.company
            )
        return form
    
    def form_valid(self, form):
        # Set the company for the new category
        category = form.save(commit=False)
        if hasattr(self.request.user, 'profile') and self.request.user.profile.company:
            category.company = self.request.user.profile.company
        category.save()
        return super().form_valid(form)


class ProductCategoryUpdateView(UpdateView, FormViewMixin, CompanyFilterMixin):
    model = models.ProductCategory
    template_name = 'products/product_category_form_modern.html'
    fields = ['name', 'parent']
    segment = 'categories'
    success_url = reverse_lazy('category-list')
    company_field = 'company'  # Field name for company relationship
    
    def get_form(self, form_class=None):
        form = super().get_form(form_class)
        # Filter parent categories to only show those from the same company
        if 'parent' in form.fields and hasattr(self.request.user, 'profile') and self.request.user.profile.company:
            form.fields['parent'].queryset = models.ProductCategory.objects.filter(
                company=self.request.user.profile.company
            )


class ProductCategoryDeleteView(BaseDeleteView, CompanyFilterMixin):
    model = models.ProductCategory
    success_url = reverse_lazy('category-list')
    company_field = 'company'  # Field name for company relationship
    template_name = 'products/product_category_confirm_delete.html'
    skip_confirmation = False  # Override the BaseDeleteView setting to show confirmation page
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        # Get related products for this category
        related_products = self.object.products.all()
        context['related_products'] = related_products[:10]  # Limit to 10 products to avoid large pages
        context['related_products_count'] = related_products.count()
        
        # Check if this is the Uncategorized category
        if self.object.name == 'Uncategorized':
            context['is_uncategorized'] = True
        
        return context
        
    def post(self, request, *args, **kwargs):
        self.object = self.get_object()
        
        # Prevent deletion of the Uncategorized category
        if self.object.name == 'Uncategorized':
            messages.error(request, "The 'Uncategorized' category cannot be deleted as it's a system category.")
            return redirect('category-list')
            
        # Get related products for this category
        related_products_count = self.object.products.count()
        
        # If there are related products, show a warning
        if related_products_count > 0:
            messages.warning(request, f"This category has {related_products_count} related products. These products will be moved to the 'Uncategorized' category.")
            
            # Find or create Uncategorized category for this company
            uncategorized, created = models.ProductCategory.objects.get_or_create(
                company=self.object.company,
                name='Uncategorized',
                defaults={'parent': None}
            )
            
            # Move all products to the Uncategorized category
            self.object.products.update(category=uncategorized)
        
        return super().post(request, *args, **kwargs)


class ProductListView(ProductPermissionMixin, CompanyFilterMixin, ListView):
    model = models.Product
    template_name = 'products/product_list.html'
    create_url = reverse_lazy('product-create')
    segment = 'products'
    context_object_name = 'products'
    
    def get_queryset(self):
        # First get the company-filtered queryset from CompanyFilterMixin
        queryset = super().get_queryset()
        
        # Check if we should show archived products
        show_archived = self.request.GET.get('show_archived', 'false').lower() == 'true'
        
        # Filter out archived products by default
        if not show_archived:
            queryset = queryset.filter(is_archived=False)
            
        return queryset
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        products = self.get_queryset()
        
        # Add flag for whether we're showing archived products
        show_archived = self.request.GET.get('show_archived', 'false').lower() == 'true'
        context['show_archived'] = show_archived
        
        # Get count of archived products for the current company only
        user = self.request.user
        archived_query = models.Product.objects.filter(is_archived=True)
        
        if hasattr(user, 'profile') and hasattr(user.profile, 'company') and user.profile.company:
            archived_query = archived_query.filter(company=user.profile.company)
            
        context['archived_products_count'] = archived_query.count()
        
        # Add products to context for direct rendering in template
        context['products'] = products
        context['total_products'] = products.count()
        
        # Calculate total inventory value (cost × quantity)
        total_inventory_value = sum(product.unit_cost * product.quantity for product in products)
        context['total_inventory_value'] = total_inventory_value
        
        # Calculate potential revenue (selling price × quantity)
        total_potential_revenue = sum(product.selling_price * product.quantity for product in products)
        context['total_potential_revenue'] = total_potential_revenue
        
        # Add product count for stats
        context['product_count'] = products.count()
        
        # Add create URL and segment for template
        context['create_url'] = self.create_url
        context['segment'] = self.segment
        context['page_title'] = "Products"
        context['page_title_badge'] = "Products"
        
        # Add currency symbol to context
        user = self.request.user
        currency_symbol = 'DT'  # Default currency
        if hasattr(user, 'profile') and hasattr(user.profile, 'company') and user.profile.company:
            try:
                company_settings = ac_models.CompanySettings.objects.get(company=user.profile.company)
                currency_symbol = company_settings.currency
            except ac_models.CompanySettings.DoesNotExist:
                pass
        context['currency_symbol'] = currency_symbol
        
        return context


class ProductDataJsonView(BaseViewMixin, View):
    """
    View to return product data in JSON format for DataTables
    """
    def get(self, request, *args, **kwargs):
        import logging
        logger = logging.getLogger(__name__)
        
        logger.info(f"ProductDataJsonView: Request received from user {self.request.user.username}")
        
        # Get products filtered by company
        if self.request.user.is_superuser or self.request.user.is_staff:
            products = models.Product.objects.all()
            logger.info(f"ProductDataJsonView: Admin user, found {products.count()} products")
        elif hasattr(self.request.user, 'profile') and self.request.user.profile and self.request.user.profile.company:
            company = self.request.user.profile.company
            logger.info(f"ProductDataJsonView: Company user, company: {company.name}, id: {company.id}")
            products = models.Product.objects.filter(company=company)
            logger.info(f"ProductDataJsonView: Found {products.count()} products for company {company.name}")
        else:
            logger.info(f"ProductDataJsonView: No company found for user {self.request.user.username}")
            products = models.Product.objects.none()
        
        # Prepare data for DataTables
        data = []
        try:
            from django.utils.html import format_html
            from django.urls import reverse
            
            for product in products:
                # Create action buttons HTML
                actions = format_html(
                    '<a href="{}" class="btn btn-sm btn-primary me-1" data-bs-toggle="tooltip" title="View Details"><i class="fas fa-eye"></i></a> ' +
                    '<a href="{}" class="btn btn-sm btn-info me-1" data-bs-toggle="tooltip" title="Edit"><i class="fas fa-edit"></i></a> ' +
                    '<a href="{}" class="btn btn-sm btn-danger me-1" data-bs-toggle="tooltip" title="Delete"><i class="fas fa-trash"></i></a>',
                    reverse('product-detail', args=[product.id]),
                    reverse('product-update', args=[product.id]),
                    reverse('product-delete', args=[product.id])
                )
                
                # Format category name
                category_name = product.category.name if product.category else '-'
                
                # Add product data
                data.append({
                    'id': product.id,
                    'name': product.name,
                    'sku': product.sku or '-',
                    'category': category_name,
                    'quantity': product.quantity,
                    'unit_cost': float(product.unit_cost),
                    'selling_price': float(product.selling_price),
                    'actions': actions
                })
            
            logger.info(f"ProductDataJsonView: Successfully prepared data for {len(data)} products")
        except Exception as e:
            logger.error(f"ProductDataJsonView: Error preparing product data: {str(e)}")
            import traceback
            logger.error(traceback.format_exc())
        
        response_data = {'data': data}
        logger.info(f"ProductDataJsonView: Returning response with {len(data)} products")
        return JsonResponse(response_data)


class ProductCreateView(ProductPermissionMixin, CreateView):
    model = models.Product
    form_class = core.forms.ProductForm
    template_name = 'products/product_form.html'
    segment = 'products'
    success_url = reverse_lazy('product-list')
    
    def get_form(self, form_class=None):
        form = super().get_form(form_class)
        # Filter category choices to only show categories from the user's company
        if not self.request.user.is_superuser and not self.request.user.is_staff:
            if hasattr(self.request.user, 'profile') and self.request.user.profile.company:
                form.fields['category'].queryset = models.ProductCategory.objects.filter(
                    company=self.request.user.profile.company
                )
        return form
    
    def form_valid(self, form):
        # Set the company for the new product
        product = form.save(commit=False)
        
        # Debug logging for image upload
        logger.info(f"ProductCreateView.form_valid: Processing product form with data: {form.cleaned_data}")
        logger.info(f"ProductCreateView.form_valid: Image file in request.FILES: {self.request.FILES}")
        
        if 'image' in form.cleaned_data and form.cleaned_data['image']:
            logger.info(f"ProductCreateView.form_valid: Image file detected: {form.cleaned_data['image']}")
        else:
            logger.info("ProductCreateView.form_valid: No image file in form.cleaned_data")
            
        if not self.request.user.is_superuser and not self.request.user.is_staff:
            if hasattr(self.request.user, 'profile') and self.request.user.profile.company:
                product.company = self.request.user.profile.company
        
        # Save the product
        product.save()
        logger.info(f"ProductCreateView.form_valid: Product saved with ID: {product.id}, Image: {product.image}")
        
        return super().form_valid(form)

class ProductUpdateView(ProductPermissionMixin, UpdateView):
    model = models.Product
    form_class = core.forms.ProductForm
    template_name = 'products/product_form.html'
    segment = 'products'
    success_url = reverse_lazy('product-list')
    
    def form_valid(self, form):
        # Debug logging for image upload
        logger.info(f"ProductUpdateView.form_valid: Processing product form with data: {form.cleaned_data}")
        logger.info(f"ProductUpdateView.form_valid: Image file in request.FILES: {self.request.FILES}")
        
        if 'image' in form.cleaned_data and form.cleaned_data['image']:
            logger.info(f"ProductUpdateView.form_valid: Image file detected: {form.cleaned_data['image']}")
        else:
            logger.info("ProductUpdateView.form_valid: No image file in form.cleaned_data")
            
        # Save the product
        response = super().form_valid(form)
        logger.info(f"ProductUpdateView.form_valid: Product saved with ID: {self.object.id}, Image: {self.object.image}")
        
        return response
        
    def get_queryset(self):
        # Ensure users can only update products from their company
        queryset = super().get_queryset()
        if self.request.user.is_superuser or self.request.user.is_staff:
            return queryset
        if hasattr(self.request.user, 'profile') and self.request.user.profile.company:
            return queryset.filter(company=self.request.user.profile.company)
        return queryset.none()


class ProductDeleteView(ProductPermissionMixin, View):
    model = models.Product
    template_name = 'products/product_archive_confirm.html'
    success_url = reverse_lazy('product-list')
    
    def get_context_data(self, **kwargs):
        context = kwargs
        # Check if product is used in any invoices
        if 'object' in context:
            product = context['object']
            context['invoice_items_count'] = models.InvoiceItem.objects.filter(product=product).count()
        return context

    def get(self, request, *args, **kwargs):
        # Get the product object
        self.object = get_object_or_404(models.Product, pk=kwargs.get('pk'))

        # Check if the product belongs to the user's company
        if not request.user.is_superuser and not request.user.is_staff:
            if hasattr(request.user, 'profile') and request.user.profile.company:
                if self.object.company != request.user.profile.company:
                    messages.error(request, "You don't have permission to archive this product.")
                    return redirect('product-list')

        # Check if product is used in any invoices (for future reference)
        # We're just checking if the product is used in invoices but not taking any action based on it yet
        models.InvoiceItem.objects.filter(product=self.object).count()

        # Archive the product instead of deleting it
        self.object.is_archived = True
        self.object.save()

        return redirect(self.success_url)

    def get_queryset(self):
        # Ensure users can only delete products from their company
        queryset = super().get_queryset()
        if self.request.user.is_superuser or self.request.user.is_staff:
            return queryset
        if hasattr(self.request.user, 'profile') and self.request.user.profile.company:
            return queryset.filter(company=self.request.user.profile.company)
        return queryset.none()


class ProductRestoreView(BaseViewMixin, View):
    model = models.Product
    template_name = 'products/product_restore_confirm.html'
    success_url = reverse_lazy('product-list')
    
    def get_context_data(self, **kwargs):
        context = kwargs
        return context
    
    def get(self, request, *args, **kwargs):
        self.object = get_object_or_404(models.Product, pk=kwargs['pk'])
        context = self.get_context_data(object=self.object)
        return render(request, self.template_name, context)
    
    def post(self, request, *args, **kwargs):
        self.object = get_object_or_404(models.Product, pk=kwargs['pk'])
        
        # Restore the product by setting is_archived to False
        self.object.is_archived = False
        self.object.save()
        
        return redirect(self.success_url)


class ProductDetailView(ProductPermissionMixin, DetailView):
    model = models.Product
    template_name = 'products/product_detail.html'
    context_object_name = 'object'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        
        # Find all InvoiceItems for this product
        invoice_items = models.InvoiceItem.objects.filter(product=self.object).select_related('invoice')
        
        # Calculate total quantity sold
        total_quantity_sold = sum(item.quantity for item in invoice_items)
        context['total_quantity_sold'] = total_quantity_sold
        
        # Calculate total revenue from this product
        total_revenue = sum(item.total_price for item in invoice_items)
        context['total_revenue'] = total_revenue
        
        # Get the unique invoices containing this product
        invoices_data = []
        for item in invoice_items:
            invoice = item.invoice
            # Add invoice data with additional information
            invoices_data.append({
                'id': invoice.id,
                'invoice_number': f'INV-{invoice.id:06d}',  # Format invoice number
                'date': invoice.created_at,
                'client_name': f'Company {invoice.company.name}' if invoice.company else 'N/A',  # Use company name as client
                'total': item.total_price,  # Use the item's total price
                'quantity': item.quantity,  # Include quantity sold
                'status': 'paid',  # Default status since we don't have a status field
                'url': reverse_lazy('invoice-detail', kwargs={'pk': invoice.pk})
            })
        
        context['invoices'] = invoices_data
        return context


class InvoiceCreateView(InvoicePermissionMixin, CreateView, FormViewMixin):
    model = models.Invoice
    form_class = core.forms.InvoiceForm
    template_name = 'invoices/invoice_form_new.html'
    success_url = None
    
    def get_initial(self):
        initial = super().get_initial()
        
        # Add user to initial data
        initial['user'] = self.request.user
        
        # Get default TVA rate from company settings
        default_tva_rate = 19.0  # Default fallback
        if hasattr(self.request.user, 'profile') and self.request.user.profile.company:
            company = self.request.user.profile.company
            if hasattr(company, 'settings'):
                default_tva_rate = company.settings.default_tva_rate
                print(f"[VIEW] Using company default TVA rate: {default_tva_rate}")
        
        # Set initial values for TVA rate and include_stamp_fee
        initial['tva_rate'] = default_tva_rate
        initial['include_stamp_fee'] = True
        
        return initial

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        
        # Get the company for the current user
        company = None
        if hasattr(self.request.user, 'profile') and self.request.user.profile and self.request.user.profile.company:
            company = self.request.user.profile.company
        
        # Pass the company to the formset
        if self.request.POST:
            context['formset'] = core.forms.InvoiceItemFormSet(self.request.POST, company=company)
        else:
            context['formset'] = core.forms.InvoiceItemFormSet(company=company)
        context['page_title'] = 'Create Invoice'
        context['page_title_badge'] = 'Create Invoice'
        
        self.add_products_to_context(context)
        return context

    def add_products_to_context(self, context):
        # Add products to context for the select2 widget, filtered by company and excluding archived products
        if self.request.user.is_superuser or self.request.user.is_staff:
            products = models.Product.objects.filter(is_archived=False)
        elif hasattr(self.request.user, 'profile') and self.request.user.profile.company:
            products = models.Product.objects.filter(company=self.request.user.profile.company, is_archived=False)
        else:
            products = models.Product.objects.none()
            
        context['products'] = products
        context['product_json'] = [
            {'id': p.id, 'text': p.name, 'price': float(p.selling_price)} for p in products
        ]
        return context

    def form_valid(self, form):
        import logging
        logger = logging.getLogger(__name__)
        logger.info("--- InvoiceCreateView.form_valid --- START ---")
        logger.info(f"Raw POST data: {self.request.POST}")
        logger.info(f"Form cleaned_data: {form.cleaned_data}")
        logger.info(f"Form fields: {form.fields.keys()}")
        logger.info(f"TVA rate in POST: {self.request.POST.get('tva_rate')}")
        logger.info(f"TVA rate in cleaned_data: {form.cleaned_data.get('tva_rate')}")
        logger.info(f"include_stamp_fee in POST: {self.request.POST.get('include_stamp_fee')}")
        logger.info(f"include_stamp_fee in cleaned_data: {form.cleaned_data.get('include_stamp_fee')}")

        context = self.get_context_data()
        formset = context['formset']
        
        logger.info(f"Formset is_valid: {formset.is_valid()}")
        if not formset.is_valid():
            logger.error(f"Formset errors: {formset.errors}")
            logger.error(f"Formset non_form_errors: {formset.non_form_errors()}")
            # Return form invalid if formset has errors
            return self.form_invalid(form)

        # Save the invoice
        self.object = form.save(commit=False)
        
        # Set the company and created_by for the new invoice
        if hasattr(self.request.user, 'profile') and self.request.user.profile.company:
            self.object.company = self.request.user.profile.company
        else:
             logger.warning("User has no profile or company assigned.")
             # Handle cases where company might be required? Or allow None?
             # For now, let it be None if not found.
             pass 
        
        self.object.created_by = self.request.user
        
        # Get values directly from cleaned_data
        tva_rate = form.cleaned_data.get('tva_rate')
        include_stamp_fee = form.cleaned_data.get('include_stamp_fee', False) # Default to False if not present

        logger.info(f"Values from cleaned_data: tva_rate={tva_rate} ({type(tva_rate)}), include_stamp_fee={include_stamp_fee} ({type(include_stamp_fee)})")        
        
        # Check if the values are in the raw POST data
        raw_tva_rate = self.request.POST.get('tva_rate')
        raw_include_stamp_fee = self.request.POST.get('include_stamp_fee')
        logger.info(f"Raw values from POST: tva_rate={raw_tva_rate}, include_stamp_fee={raw_include_stamp_fee}")
        
        # Try to convert raw values if needed
        if raw_tva_rate and tva_rate is None:
            try:
                from decimal import Decimal
                tva_rate = Decimal(raw_tva_rate)
                logger.info(f"Converted raw tva_rate to Decimal: {tva_rate}")
            except Exception as e:
                logger.error(f"Error converting raw tva_rate: {e}")
        
        # --- Simplified Logic for Debugging --- 
        # Directly assign form values if they exist. Handle None explicitly.
        if tva_rate is not None and tva_rate != '':
            self.object.tva_rate = tva_rate
            logger.info(f"Set self.object.tva_rate = {self.object.tva_rate}")
        else:
            # Get default TVA rate from company settings
            default_tva_rate = 19.0  # Default fallback
            if hasattr(self.request.user, 'profile') and self.request.user.profile.company:
                company = self.request.user.profile.company
                # Get company settings directly
                # from accounts.models import CompanySettings
                try:
                    settings = ac_models.CompanySettings.objects.get(company=company)
                    default_tva_rate = settings.default_tva_rate
                    logger.info(f"Got default TVA rate from company settings: {default_tva_rate}")
                except Exception as e:
                    logger.error(f"Error getting company settings: {e}")
            
            logger.warning(f"TVA rate received as None from form. Setting to default {default_tva_rate}")
            self.object.tva_rate = default_tva_rate

        # For include_stamp_fee, use the raw value if available
        if raw_include_stamp_fee == 'on':
            self.object.include_stamp_fee = True
            logger.info("Setting include_stamp_fee to True based on raw POST data")
        else:
            self.object.include_stamp_fee = include_stamp_fee or False
            logger.info(f"Setting include_stamp_fee to {self.object.include_stamp_fee} based on cleaned_data or default")
        
        logger.info(f"Final values: tva_rate={self.object.tva_rate}, include_stamp_fee={self.object.include_stamp_fee}")
        # --- End Simplified Logic --- 
                
        # Save the invoice *before* saving formset
        try:
            self.object.save()
            logger.info(f"Invoice object saved successfully (ID: {self.object.pk})")
        except Exception as e:
            logger.error(f"Error saving invoice object: {e}")
            # Add error to form and return invalid
            form.add_error(None, f"Error saving invoice: {e}")
            return self.form_invalid(form)

        # Save the formset
        formset.instance = self.object
        try:
            # First save the formset
            invoice_items = formset.save()
            logger.info("Formset saved successfully.")
            
            # Now update product inventory for each invoice item
            for item in invoice_items:
                try:
                    product = item.product
                    requested_quantity = int(item.quantity)  # Ensure quantity is an integer
                    
                    logger.info(f"Processing inventory update for product {product.name} (ID: {product.id}). Requested: {requested_quantity}, Current stock: {product.quantity}")
                    
                    if product.quantity < requested_quantity:
                        # Not enough stock
                        logger.error(f"Not enough stock for product {product.name} (ID: {product.id}). Requested: {requested_quantity}, Available: {product.quantity}")
                        form.add_error(None, f"Not enough stock for product {product.name}. Requested: {requested_quantity}, Available: {product.quantity}")
                        # Delete the invoice and return form_invalid
                        self.object.delete()
                        return self.form_invalid(form)
                    
                    # Update product quantity - explicitly deduct the requested quantity
                    original_quantity = product.quantity
                    product.quantity = original_quantity - requested_quantity
                    product.save()
                    logger.info(f"Updated inventory for product {product.name} (ID: {product.id}). Original: {original_quantity}, Deducted: {requested_quantity}, New quantity: {product.quantity}")
                    
                    # Double-check the update was correct
                    if product.quantity != original_quantity - requested_quantity:
                        logger.error(f"Inventory update error: Expected {original_quantity - requested_quantity} but got {product.quantity}")
                        form.add_error(None, f"Error updating inventory for product {product.name}: Quantity mismatch")
                        # Try to fix it
                        product.quantity = original_quantity - requested_quantity
                        product.save()
                except Exception as e:
                    logger.error(f"Error updating product inventory: {e}")
                    # Add error but continue with other products
                    form.add_error(None, f"Error updating inventory for product {item.product.name if item.product else 'Unknown'}: {e}")
        except Exception as e:
            logger.error(f"Error saving formset: {e}")
            # Add error to form and return invalid
            form.add_error(None, f"Error saving invoice items: {e}")
            # Delete the just-created invoice object if items fail
            self.object.delete()
            return self.form_invalid(form)

        logger.info("--- InvoiceCreateView.form_valid --- END ---")
        return super().form_valid(form)

    def form_invalid(self, form):
        import logging
        logger = logging.getLogger(__name__)
        logger.warning("--- InvoiceCreateView.form_invalid --- START ---")
        logger.warning(f"Form errors: {form.errors}")
        context = self.get_context_data() # Re-fetch context
        formset = context['formset']
        if not formset.is_valid():
             logger.warning(f"Formset errors: {formset.errors}")
             logger.warning(f"Formset non_form_errors: {formset.non_form_errors()}")
        logger.warning("--- InvoiceCreateView.form_invalid --- END ---")
        # Ensure formset is passed back to the template on invalid form
        return self.render_to_response(self.get_context_data(form=form, formset=formset))


class InvoiceListView(InvoicePermissionMixin, ListView):
    model = models.Invoice
    template_name = 'invoices/invoice_list.html'
    context_object_name = 'invoices'
    
    def get_queryset(self):
        # Start with the base queryset
        queryset = super().get_queryset()
        user = self.request.user
        
        # Always filter by company, even for superusers and staff
        # This ensures data isolation between companies
        if hasattr(user, 'profile') and hasattr(user.profile, 'company') and user.profile.company:
            company = user.profile.company
            queryset = queryset.filter(company=company)
        else:
            # Users without a company can't see any invoices
            return queryset.none()
        
        # Get filter parameters from request
        start_date = self.request.GET.get('start_date')
        end_date = self.request.GET.get('end_date')
        status = self.request.GET.get('status')
        
        # Apply date range filter if provided
        if start_date:
            queryset = queryset.filter(created_at__date__gte=start_date)
        if end_date:
            queryset = queryset.filter(created_at__date__lte=end_date)
            
        # Apply status filter if provided
        if status:
            if status == 'paid':
                queryset = queryset.filter(is_paid=True)
            elif status == 'unpaid':
                queryset = queryset.filter(is_paid=False)
        
        # Order by most recent first
        return queryset.order_by('-created_at')

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        
        # Initialize filter form
        filter_form = DateRangeFilterFormNew(self.request.GET or None)
        context['filter_form'] = filter_form
        context['page_title'] = 'Invoices'
        context['page_title_badge'] = 'Invoices'
        
        # Get filter parameters
        start_date = self.request.GET.get('start_date')
        end_date = self.request.GET.get('end_date')
        status = self.request.GET.get('status')
        
        # Build filter description
        filter_description = []
        is_filtered = False
        
        if start_date:
            filter_description.append(f"From {start_date}")
            is_filtered = True
            
        if end_date:
            filter_description.append(f"To {end_date}")
            is_filtered = True
            
        if status:
            filter_description.append(f"Status: {status.title()}")
            is_filtered = True
            
        if is_filtered:
            context['is_filtered'] = True
            context['filter_description'] = ", ".join(filter_description)
            
        # Create base queryset filtered by company
        invoice_queryset = models.Invoice.objects
        user = self.request.user
        
        # Always filter by company, even for superusers and staff
        if hasattr(user, 'profile') and hasattr(user.profile, 'company') and user.profile.company:
            invoice_queryset = invoice_queryset.filter(company=user.profile.company)
        else:
            # If user has no company, they shouldn't see any invoices
            invoice_queryset = invoice_queryset.none()
        
        # Calculate filtered stats if filter is applied
        if start_date or end_date:
            filter_kwargs = {}
            if start_date:
                filter_kwargs['created_at__date__gte'] = start_date
            if end_date:
                filter_kwargs['created_at__date__lte'] = end_date
            
            filtered_invoices = invoice_queryset.filter(**filter_kwargs)
            filtered_invoice_items = models.InvoiceItem.objects.filter(
                invoice__in=filtered_invoices
            )

            context['filtered_total_items'] = filtered_invoice_items.aggregate(
                total=Sum('quantity'))['total'] or 0
            context['filtered_total_value'] = sum(
                item.quantity * item.product.unit_cost for item in filtered_invoice_items.select_related('product')
            )
            context['filtered_total_price'] = filtered_invoices.aggregate(
                total=Sum('items__total_price'))['total'] or 0

        # Calculate overall stats for user's company only
        user = self.request.user
        company = None
        if hasattr(user, 'profile') and hasattr(user.profile, 'company') and user.profile.company:
            company = user.profile.company
        
        if company:
            # Filter invoice items by the user's company
            company_invoice_items = models.InvoiceItem.objects.filter(invoice__company=company)
            
            # Calculate stats based on company's data only
            total_items_sold = company_invoice_items.aggregate(
                total=Sum('quantity'))['total'] or 0
                
            total_inventory_sold_value = sum(
                item.quantity * item.product.unit_cost 
                for item in company_invoice_items.select_related('product')
            ) if company_invoice_items.exists() else 0
            
            total_invoice_price = models.Invoice.objects.filter(company=company).aggregate(
                total=Sum('items__total_price'))['total'] or 0
        else:
            # No company, no stats
            total_items_sold = 0
            total_inventory_sold_value = 0
            total_invoice_price = 0

        # Add currency symbol to context
        currency_symbol = 'DT'  # Default currency
        if company:
            try:
                company_settings = ac_models.CompanySettings.objects.get(company=company)
                currency_symbol = company_settings.currency
            except ac_models.CompanySettings.DoesNotExist:
                pass
        
        context.update({
            'total_items_sold': total_items_sold,
            'total_inventory_sold_value': total_inventory_sold_value,
            'total_invoice_price': total_invoice_price,
            'currency_symbol': currency_symbol,
        })
        return context

class InvoiceUpdateView(InvoicePermissionMixin, UpdateView, FormViewMixin):
    model = models.Invoice
    form_class = core.forms.InvoiceForm
    template_name = 'invoices/invoice_form_modern.html'
    success_url = reverse_lazy('invoice-list')
    
    def get_initial(self):
        initial = super().get_initial()
        
        # Add user to initial data
        initial['user'] = self.request.user
        
        # Get default TVA rate from company settings
        default_tva_rate = 19.0  # Default fallback
        if hasattr(self.request.user, 'profile') and self.request.user.profile.company:
            company = self.request.user.profile.company
            if hasattr(company, 'settings'):
                default_tva_rate = company.settings.default_tva_rate
                print(f"[VIEW] Using company default TVA rate: {default_tva_rate}")
        
        # Set initial values for TVA rate and include_stamp_fee
        initial['tva_rate'] = default_tva_rate
        initial['include_stamp_fee'] = True
        
        return initial
    
    def get_queryset(self):
        # Ensure users can only update invoices from their company
        queryset = super().get_queryset()
        if self.request.user.is_superuser or self.request.user.is_staff:
            return queryset
        if hasattr(self.request.user, 'profile') and self.request.user.profile.company:
            return queryset.filter(company=self.request.user.profile.company)
        return queryset.none()
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        if self.request.POST:
            context['formset'] = core.forms.InvoiceItemFormSet(
                self.request.POST, instance=self.object)
        else:
            context['formset'] = core.forms.InvoiceItemFormSet(
                instance=self.object)
        
        # Add products to context for the select2 widget, filtered by company
        if self.request.user.is_superuser or self.request.user.is_staff:
            products = models.Product.objects.all()
        elif hasattr(self.request.user, 'profile') and self.request.user.profile.company:
            products = models.Product.objects.filter(company=self.request.user.profile.company)
        else:
            products = models.Product.objects.none()
            
        context['products'] = products
        context['product_json'] = [
            {'id': p.id, 'text': p.name, 'price': float(p.selling_price)} for p in products
        ]
        context['page_title'] = 'Update Invoice'
        context['page_title_badge'] = 'Update Invoice'
        
        return context
        
    def form_valid(self, form):
        import logging
        from django.db import transaction
        logger = logging.getLogger(__name__)
        logger.debug('InvoiceUpdateView.form_valid called')
        logger.debug(f'Form valid: {form.is_valid()}')
        logger.debug(f'POST data: {self.request.POST}')
        
        with transaction.atomic():
            context = self.get_context_data()
            formset = context['formset']
            logger.info(f"Formset is_valid: {formset.is_valid()}")
            if not formset.is_valid():
                logger.error(f"Formset errors: {formset.errors}")
                logger.error(f"Formset non_form_errors: {formset.non_form_errors()}")
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
        import logging
        logger = logging.getLogger(__name__)
        logger.info("--- InvoiceUpdateView._save_invoice_with_total --- START ---")
        logger.info(f"Raw POST data: {self.request.POST}")
        logger.info(f"Form cleaned_data: {form.cleaned_data}")

        # Save invoice object without committing to DB
        obj = form.save(commit=False)
        
        # Get form values
        tva_rate = form.cleaned_data.get('tva_rate')
        include_stamp_fee = form.cleaned_data.get('include_stamp_fee', False) # Default False
        invoice_total = form.cleaned_data.get('invoice_total')

        logger.info(f"Values from cleaned_data: tva_rate={tva_rate} ({type(tva_rate)}), include_stamp_fee={include_stamp_fee} ({type(include_stamp_fee)}), invoice_total={invoice_total}")
        
        # Check if the values are in the raw POST data
        raw_tva_rate = self.request.POST.get('tva_rate')
        raw_include_stamp_fee = self.request.POST.get('include_stamp_fee')
        logger.info(f"Raw values from POST: tva_rate={raw_tva_rate}, include_stamp_fee={raw_include_stamp_fee}")
        
        # Try to convert raw values if needed
        if raw_tva_rate and tva_rate is None:
            try:
                from decimal import Decimal
                tva_rate = Decimal(raw_tva_rate)
                logger.info(f"Converted raw tva_rate to Decimal: {tva_rate}")
            except Exception as e:
                logger.error(f"Error converting raw tva_rate: {e}")
        
        # --- Simplified Logic for Debugging --- 
        if tva_rate is not None and tva_rate != '':
            obj.tva_rate = tva_rate
            logger.info(f"Set obj.tva_rate = {obj.tva_rate}")
        else:
            # Get default TVA rate from company settings
            default_tva_rate = 19.0  # Default fallback
            if hasattr(self.request.user, 'profile') and self.request.user.profile.company:
                company = self.request.user.profile.company
                # Get company settings directly
                # from accounts.models import CompanySettings
                try:
                    settings = ac_models.CompanySettings.objects.get(company=company)
                    default_tva_rate = settings.default_tva_rate
                    logger.info(f"Got default TVA rate from company settings: {default_tva_rate}")
                except Exception as e:
                    logger.error(f"Error getting company settings: {e}")
            
            logger.warning(f"Update: TVA rate received as None from form. Setting to default {default_tva_rate}")
            obj.tva_rate = default_tva_rate
        
        # For include_stamp_fee, use the raw value if available
        if raw_include_stamp_fee == 'on':
            obj.include_stamp_fee = True
            logger.info("Setting include_stamp_fee to True based on raw POST data")
        else:
            obj.include_stamp_fee = include_stamp_fee or False
            logger.info(f"Setting include_stamp_fee to {obj.include_stamp_fee} based on cleaned_data or default")
        
        logger.info(f"Final values: tva_rate={obj.tva_rate}, include_stamp_fee={obj.include_stamp_fee}")
        # --- End Simplified Logic --- 
        
        # Save custom total from form
        if invoice_total is not None:
            obj.custom_total = invoice_total
            logger.info(f"Set obj.custom_total = {obj.custom_total}")
        else:
            # If not provided, ensure it's None so model calculates it
            obj.custom_total = None 
            logger.info("Set obj.custom_total = None")
            
        try:
            obj.save()
            logger.info(f"Invoice object updated successfully (ID: {obj.pk})")
        except Exception as e:
             logger.error(f"Error saving updated invoice object: {e}")
             form.add_error(None, f"Error saving invoice: {e}")
             # We are already inside form_valid, how to signal error? 
             # Re-raising or handling might be needed depending on flow.
             # For now, log and continue, but saving items might fail.
             # Ideally, this save logic should be inside form_valid directly.
             raise # Re-raise to be caught by form_valid/form_invalid

        logger.info("--- InvoiceUpdateView._save_invoice_with_total --- END ---")
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
        logger.error(f'Formset non_form_errors: {formset.non_form_errors()}')


# Helper methods for invoice views

class InvoiceDeleteView(InvoicePermissionMixin, DeleteView):
    model = models.Invoice
    template_name = 'invoices/invoice_confirm_delete.html'
    success_url = reverse_lazy('invoice-list')
    
    def get_queryset(self):
        # Ensure users can only delete invoices from their company
        queryset = super().get_queryset()
        if self.request.user.is_superuser or self.request.user.is_staff:
            return queryset
        if hasattr(self.request.user, 'profile') and self.request.user.profile.company:
            return queryset.filter(company=self.request.user.profile.company)
        return queryset.none()

    def delete(self, request, *args, **kwargs):
        self.object = self.get_object()
        # Restore inventory for all items in the invoice
        for item in self.object.items.all():
            product = item.product
            product.quantity += item.quantity
            product.save()
        return super().delete(request, *args, **kwargs)


class InvoiceDetailView(InvoicePermissionMixin, DetailView):
    model = models.Invoice
    template_name = 'invoices/invoice_detail.html'
    context_object_name = 'invoice'
    
    def get_queryset(self):
        # Ensure users can only view invoices from their company
        queryset = super().get_queryset()
        user = self.request.user
        
        # Always filter by company, even for superusers and staff
        if hasattr(user, 'profile') and hasattr(user.profile, 'company') and user.profile.company:
            return queryset.filter(company=user.profile.company)
        
        # Users without a company can't see any invoices
        return queryset.none()
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        
        # Add currency symbol to context
        user = self.request.user
        currency_symbol = 'DT'  # Default currency
        if hasattr(user, 'profile') and hasattr(user.profile, 'company') and user.profile.company:
            try:
                company_settings = ac_models.CompanySettings.objects.get(company=user.profile.company)
                currency_symbol = company_settings.currency
            except ac_models.CompanySettings.DoesNotExist:
                pass
        context['currency_symbol'] = currency_symbol
        
        return context
