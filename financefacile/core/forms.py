from django.forms import inlineformset_factory
from django import forms
from django.utils import timezone

from crispy_forms.helper import FormHelper
from crispy_forms.layout import Div, Layout, Submit, HTML

from core import models
from django_select2 import forms as s2forms


class CategoryMultiSelectWidget(s2forms.Select2MultipleWidget):
    def build_attrs(self, *args, **kwargs):
        attrs = super().build_attrs(*args, **kwargs)
        attrs.update({
            'data-placeholder': 'Select categories...',
            'data-allow-clear': 'true',
            'data-close-on-select': 'false',
            'style': 'width: 100%;',
        })
        return attrs


class DateRangeFilterFormNew(forms.Form):
    start_date = forms.DateField(
        label='Start Date',
        required=False,
        widget=forms.DateInput(attrs={'type': 'date', 'class': 'form-control'})
    )
    end_date = forms.DateField(
        label='End Date',
        required=False,
        widget=forms.DateInput(attrs={'type': 'date', 'class': 'form-control'})
    )

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        # Setup crispy form helper
        self.helper = FormHelper()
        self.helper.form_method = 'get'
        self.helper.form_class = 'form-inline'
        self.helper.layout = Layout(
            Div(
                Div('start_date', css_class='col-md-3'),
                Div('end_date', css_class='col-md-3'),
                Div(
                    Submit('submit', 'Filter', css_class='btn-primary me-2'),
                    HTML('<a href="?" class="btn btn-secondary">Reset</a>'),
                    css_class='col-md-3 d-flex align-items-end'
                ),
                css_class='row'
            )
        )

    def clean(self):
        cleaned_data = super().clean()
        start_date = cleaned_data.get('start_date')
        end_date = cleaned_data.get('end_date')

        if start_date and end_date and start_date > end_date:
            raise forms.ValidationError('End date must be after start date')

        return cleaned_data
    

class DateRangeFilterForm(forms.Form):
    start_date = forms.DateField(
        label='Start Date',
        required=False,
        widget=forms.DateInput(attrs={'type': 'date', 'class': 'form-control'})
    )
    end_date = forms.DateField(
        label='End Date',
        required=False,
        widget=forms.DateInput(attrs={'type': 'date', 'class': 'form-control'})
    )
    category_name = forms.MultipleChoiceField(
        label='Categories',
        required=False,
        widget=CategoryMultiSelectWidget()
    )

    def __init__(self, *args, **kwargs):
        # Extract user from kwargs
        self.user = kwargs.pop('user', None)
        
        super().__init__(*args, **kwargs)
        
        # Dynamically populate category choices, filtered by company
        categories_queryset = models.ExpenseCategory.objects.all().order_by('name')
        
        # Filter categories by company if user is provided
        if self.user and hasattr(self.user, 'profile') and hasattr(self.user.profile, 'company') and self.user.profile.company:
            categories_queryset = categories_queryset.filter(company=self.user.profile.company)
        
        self.fields['category_name'].choices = [
            ('', '---------')] + [(cat.name, cat.name) for cat in categories_queryset]

        # Setup crispy form helper
        self.helper = FormHelper()
        self.helper.form_method = 'get'
        self.helper.form_class = 'form-inline'
        self.helper.layout = Layout(
            Div(
                Div('start_date', css_class='col-md-3'),
                Div('end_date', css_class='col-md-3'),
                Div('category_name', css_class='col-md-3'),
                Div(
                    Submit('submit', 'Filter', css_class='btn-primary me-2'),
                    HTML('<a href="?" class="btn btn-secondary">Reset</a>'),
                    css_class='col-md-3 d-flex align-items-end'
                ),
                css_class='row'
            )
        )

    def clean(self):
        cleaned_data = super().clean()
        start_date = cleaned_data.get('start_date')
        end_date = cleaned_data.get('end_date')

        if start_date and end_date and start_date > end_date:
            raise forms.ValidationError('End date must be after start date')

        return cleaned_data


class CalendarEventFilterForm(forms.Form):
    start_date = forms.DateField(
        label='Start Date',
        required=False,
        widget=forms.DateInput(attrs={'type': 'date', 'class': 'form-control select2'})
    )
    end_date = forms.DateField(
        label='End Date',
        required=False,
        widget=forms.DateInput(attrs={'type': 'date', 'class': 'form-control select2'})
    )
    theme = forms.MultipleChoiceField(
        label='Theme',
        required=False,
        widget=s2forms.Select2MultipleWidget(attrs={'class': 'form-select select2-multiple', 'data-placeholder': 'Select themes...'})
    )

    def __init__(self, *args, **kwargs):
        # Extract theme choices from kwargs
        theme_choices = kwargs.pop('theme_choices', None)
        
        super().__init__(*args, **kwargs)
        
        # Set theme choices if provided
        if theme_choices:
            self.fields['theme'].choices = theme_choices
        else:
            # Default theme choices from CalendarEvent model
            self.fields['theme'].choices = [
                ('primary', 'Primary'),
                ('secondary', 'Secondary'),
                ('success', 'Success'),
                ('danger', 'Danger'),
                ('warning', 'Warning'),
                ('info', 'Info'),
                ('dark', 'Dark'),
            ]

        # Setup crispy form helper
        self.helper = FormHelper()
        self.helper.form_method = 'get'
        self.helper.form_class = 'form-inline'
        self.helper.layout = Layout(
            Div(
                Div('start_date', css_class='col-md-3'),
                Div('end_date', css_class='col-md-3'),
                Div('theme', css_class='col-md-3'),
                Div(
                    Submit('submit', 'Filter', css_class='btn-primary me-2'),
                    HTML('<a href="?" class="btn btn-secondary">Reset</a>'),
                    css_class='col-md-3 d-flex align-items-end'
                ),
                css_class='row'
            )
        )

    def clean(self):
        cleaned_data = super().clean()
        start_date = cleaned_data.get('start_date')
        end_date = cleaned_data.get('end_date')

        if start_date and end_date and start_date > end_date:
            raise forms.ValidationError('End date must be after start date')

        return cleaned_data


class DateRangeCategoryFilterForm(forms.Form):
    start_date = forms.DateField(
        label='Start Date',
        required=False,
        widget=forms.DateInput(attrs={'type': 'date', 'class': 'form-control'})
    )
    end_date = forms.DateField(
        label='End Date',
        required=False,
        widget=forms.DateInput(attrs={'type': 'date', 'class': 'form-control'})
    )


    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        # Setup crispy form helper
        self.helper = FormHelper()
        self.helper.form_method = 'get'
        self.helper.form_class = 'form-inline'
        self.helper.layout = Layout(
            Div(
                Div('start_date', css_class='col-md-3'),
                Div('end_date', css_class='col-md-3'),
                Div(
                    Submit('submit', 'Filter', css_class='btn-primary me-2'),
                    HTML('<a href="?" class="btn btn-secondary">Reset</a>'),
                    css_class='col-md-3 d-flex align-items-end'
                ),
                css_class='row'
            )
        )

    def clean(self):
        cleaned_data = super().clean()
        start_date = cleaned_data.get('start_date')
        end_date = cleaned_data.get('end_date')

        if start_date and end_date and start_date > end_date:
            raise forms.ValidationError('End date must be after start date')

        return cleaned_data

class InvoiceForm(forms.ModelForm):
    invoice_total = forms.DecimalField(
        max_digits=12, decimal_places=2, required=False,
        label="Invoice Total",
        widget=forms.NumberInput(attrs={
                                 "class": "form-control form-control-lg invoice-grand-total", "placeholder": "Total invoice amount"})
    )
    client_name = forms.CharField(
        max_length=255, required=False,
        label="Client Name",
        widget=forms.TextInput(attrs={"class": "form-control", "placeholder": "Client name"})
    )
    client_address = forms.CharField(
        max_length=255, required=False,
        label="Client Address",
        widget=forms.Textarea(attrs={"class": "form-control", "rows": 2, "placeholder": "Client address"})
    )
    tva_rate = forms.DecimalField(
        max_digits=5, decimal_places=2, required=False,
        label="TVA Rate (%)",
        widget=forms.NumberInput(attrs={"class": "form-control", "step": "0.01", "min": "0", "max": "100", "placeholder": "TVA Rate"})
    )
    include_stamp_fee = forms.BooleanField(
        required=False,
        label="Include Stamp Fee",
        widget=forms.CheckboxInput(attrs={"class": "form-check-input"})
    )
    
    def __init__(self, *args, **kwargs):
        # Extract user from initial data if present
        user = kwargs.get('initial', {}).get('user')
        
        super().__init__(*args, **kwargs)
        
        # Set default values for TVA rate and include_stamp_fee
        default_tva_rate = 19.0  # Default value
        stamp_fee = 1.0  # Default value
        
        print(f"[DEBUG] User: {user.username if user else 'None'}")
        
        # Try to get company settings directly from the database
        if user and hasattr(user, 'profile') and user.profile and user.profile.company:
            company = user.profile.company
            print(f"[DEBUG] Company found: {company.name} (ID: {company.id})")
            
            # Get company settings directly from the database
            from accounts.models import CompanySettings
            try:
                settings = CompanySettings.objects.get(company=company)
                default_tva_rate = settings.default_tva_rate
                stamp_fee = settings.stamp_fee
                print(f"[DEBUG] Found company settings! Default TVA rate: {default_tva_rate}, Stamp fee: {stamp_fee}")
            except Exception as e:
                print(f"[DEBUG] Error getting company settings: {e}")
        else:
            print(f"[DEBUG] No company or profile found, using default TVA rate: {default_tva_rate}")
        
        # Ensure default_tva_rate is a Decimal for consistency
        from decimal import Decimal
        if not isinstance(default_tva_rate, Decimal):
            default_tva_rate = Decimal(str(default_tva_rate))
        
        # For new invoices, set initial values
        if not self.instance.pk:  # New invoice
            self.fields['tva_rate'].initial = default_tva_rate
            self.initial['tva_rate'] = default_tva_rate  # Set in both places to ensure it's picked up
            print(f"[DEBUG] Setting initial TVA rate for new invoice: {default_tva_rate}")
            self.fields['include_stamp_fee'].initial = True
        # For existing invoices, use the existing values
        else:
            if self.instance.tva_rate is not None:
                self.fields['tva_rate'].initial = self.instance.tva_rate
                self.initial['tva_rate'] = self.instance.tva_rate  # Set in both places
                print(f"[DEBUG] Setting initial TVA rate from existing invoice: {self.instance.tva_rate}")
            
            # For existing invoices, get stamp fee from the company
            if self.instance.company:
                # Get company settings directly
                from accounts.models import CompanySettings
                try:
                    settings = CompanySettings.objects.get(company=self.instance.company)
                    stamp_fee = settings.stamp_fee
                    print(f"[DEBUG] Got stamp fee from company settings: {stamp_fee}")
                except Exception as e:
                    print(f"[DEBUG] Error getting stamp fee from company settings: {e}")
        
        # Set help text for the stamp fee field
        self.fields['include_stamp_fee'].help_text = f"Include stamp fee of {stamp_fee} in this invoice"

    class Meta:
        model = models.Invoice
        fields = ['client_name', 'client_address', 'tva_rate', 'include_stamp_fee']


class InvoiceItemForm(forms.ModelForm):
    class Meta:
        model = models.InvoiceItem
        fields = ['product', 'quantity', 'selling_price']

    def __init__(self, *args, **kwargs):
        # Get company from kwargs if available
        company = kwargs.pop('company', None)
        super().__init__(*args, **kwargs)
        
        # Filter products by stock > 0 and exclude archived products (i.e., only 'active' products)
        product_queryset = models.Product.objects.filter(quantity__gt=0, is_archived=False)
        
        # If company is provided, filter by company as well
        if company:
            product_queryset = product_queryset.filter(company=company)
        
        self.fields['product'].queryset = product_queryset
        self.fields['product'].widget = ProductWidget()
        self.fields['product'].help_text = 'Select a product from inventory'

        # If the form instance has a product that is no longer in the active queryset (e.g., archived),
        # clear it from the initial data for this form instance. This prevents it from being shown
        # as selected and potentially being added by the widget to the dropdown choices.
        instance = kwargs.get('instance')
        if instance and instance.pk and instance.product:
            if not product_queryset.filter(pk=instance.product.pk).exists():
                # The current product for this item is inactive.
                # Check if 'product' is in self.initial and if it matches the instance's product pk.
                if self.initial.get('product') == instance.product.pk:
                    self.initial['product'] = None
                else:
                    pass
            else:
                pass
        
        # Add validation for quantity
        self.fields['quantity'].widget.attrs.update({
            'min': '1', 
            'class': 'form-control',
            'data-bs-toggle': 'tooltip',
            'title': 'Enter quantity (must not exceed available stock)'
        })
        
        self.fields['selling_price'].widget.attrs.update({
            'min': '0', 
            'class': 'form-control',
            'data-bs-toggle': 'tooltip',
            'title': 'Enter selling price'
        })
        
        # Add help text
        self.fields['product'].help_text = 'Only products with available stock are shown'
        # self.fields['quantity'].help_text = 'Must not exceed available product stock'
    
    def clean(self):
        cleaned_data = super().clean()
        product = cleaned_data.get('product')
        quantity = cleaned_data.get('quantity')
        
        # If both product and quantity are provided, check if quantity exceeds stock
        if product and quantity:
            # Get the current stock level
            available_stock = product.quantity
            
            # Check if requested quantity exceeds available stock
            if quantity > available_stock:
                self.add_error('quantity', 
                               f'Insufficient stock! Only {available_stock} units of "{product.name}" available.')
                raise forms.ValidationError(
                    f"Cannot create invoice: Requested quantity ({quantity}) exceeds available stock ({available_stock}) for {product.name}"
                )
        
        return cleaned_data


class BaseInvoiceItemFormSet(forms.BaseInlineFormSet):
    def __init__(self, *args, **kwargs):
        self.company = kwargs.pop('company', None)
        super().__init__(*args, **kwargs)
    
    def _construct_form(self, i, **kwargs):
        # Pass company to each form in the formset
        kwargs['company'] = self.company
        return super()._construct_form(i, **kwargs)
    
    def clean(self):
        """Validate the formset as a whole."""
        if any(self.errors):
            # Don't bother validating the formset if any of the forms have errors
            return
        
        products_quantities = {}
        
        # Collect all products and their requested quantities
        for form in self.forms:
            if form.cleaned_data and not form.cleaned_data.get('DELETE', False):
                product = form.cleaned_data.get('product')
                quantity = form.cleaned_data.get('quantity')
                
                if product and quantity:
                    # Add quantity to existing product or create new entry
                    if product in products_quantities:
                        products_quantities[product] += quantity
                    else:
                        products_quantities[product] = quantity
        
        # Check if any product's total quantity exceeds available stock
        for product, total_quantity in products_quantities.items():
            if total_quantity > product.quantity:
                raise forms.ValidationError(
                    f"Total quantity ({total_quantity}) for {product.name} exceeds available stock ({product.quantity})."
                )

InvoiceItemFormSet = inlineformset_factory(
    models.Invoice, models.InvoiceItem, form=InvoiceItemForm, formset=BaseInvoiceItemFormSet,
    fields=['product', 'quantity', 'selling_price'], extra=1, can_delete=True
)


class ProductCategoryWidget(s2forms.Select2MultipleWidget):
    model = models.ProductCategory
    search_fields = ['name__icontains']

    def build_attrs(self, *args, **kwargs):
        attrs = super().build_attrs(*args, **kwargs)
        attrs.update({
            'data-placeholder': 'Select categories...',
            'data-allow-clear': 'true',
            'data-close-on-select': 'false',
            'class': 'form-control select2',
            'data-live-search': 'true',
            'style': 'width: 100%;'
        })
        return attrs


class ProductWidget(s2forms.Select2Widget):
    model = models.Product
    search_fields = ['name__icontains']

    def filter_queryset(self, request, term, queryset=None, field=None, **dependent_fields):
        # Always start with the queryset defined on the Django form field itself.
        # This queryset is already filtered for active products by InvoiceItemForm.__init__.
        if field:
            strict_queryset = field.queryset
        elif queryset is not None:
            strict_queryset = queryset # Fallback, though field.queryset is preferred
        else:
            # This case should ideally not happen if the widget is used with a ModelChoiceField
            strict_queryset = self.model.objects.none()

        # Apply search term filtering if a term is provided
        if term:
            return super().filter_queryset(request, term, queryset=strict_queryset, field=field, **dependent_fields)
        
        # If no search term, return the strict_queryset as is.
        # This prevents Select2Widget from adding back initial values that are not in our strict_queryset.
        return strict_queryset

    def build_attrs(self, *args, **kwargs):
        attrs = super().build_attrs(*args, **kwargs)
        attrs.update({
            'data-placeholder': 'Select a product...',
            'data-allow-clear': 'true',
            'class': 'form-control select2',
            'data-live-search': 'true',
            'style': 'width: 100%;'
        })
        return attrs


class ProductForm(forms.ModelForm):
    debug_marker = "THIS IS THE REAL ProductForm"

    def __init__(self, *args, **kwargs):
        self.request = kwargs.pop('request', None)
        super().__init__(*args, **kwargs)
        
        # Enhance the category field
        self.fields['category'].queryset = models.ProductCategory.objects.all().order_by('name')
        self.fields['category'].empty_label = "Select a category"
        self.fields['category'].widget.attrs.update({
            'class': 'form-select select2',
            'data-placeholder': 'Select a category'
        })
        
        # Remove company field if it exists using contextlib's suppress
        from contextlib import suppress
        with suppress(KeyError):
            del self.fields['company']
        
        # Set default TVA rate from company settings
        default_tva_rate = 19.0  # Default fallback
        
        # Try to get the company's default TVA rate
        if self.request and hasattr(self.request.user, 'profile') and self.request.user.profile.company:
            company = self.request.user.profile.company
            try:
                if hasattr(company, 'settings'):
                    default_tva_rate = company.settings.default_tva_rate
            except Exception:
                # If there's any error, fall back to the default
                pass
        
        # Set the default TVA rate for new products
        if not self.instance or not self.instance.pk:
            self.fields['tva_rate'].initial = default_tva_rate
            
        # We don't need to set initial value for price_with_tva as it's now a model field

    class Meta:
        model = models.Product
        fields = ['name', 'sku', 'category', 'quantity', 'unit_cost', 'selling_price', 'tva_rate',
                 'price_with_tva', 'value_current', 'value_1_month', 'value_2_month', 'value_3_month', 
                 'description', 'image']
        widgets = {
            'name': forms.TextInput(attrs={"class": "form-control", "style": "width: 100%;"}),
            'sku': forms.TextInput(attrs={"class": "form-control", "style": "width: 100%;"}),
            'quantity': forms.NumberInput(attrs={"class": "form-control", "style": "width: 100%;"}),
            'unit_cost': forms.NumberInput(attrs={"class": "form-control", "style": "width: 100%;"}),
            'selling_price': forms.NumberInput(attrs={"class": "form-control", "style": "width: 100%;", "step": "0.01"}),
            'tva_rate': forms.NumberInput(attrs={"class": "form-control", "style": "width: 100%;", "step": "0.01"}),
            'price_with_tva': forms.NumberInput(attrs={"class": "form-control", "style": "width: 100%;", "step": "0.01"}),
            'value_current': forms.NumberInput(attrs={"class": "form-control", "style": "width: 100%;"}),
            'value_1_month': forms.NumberInput(attrs={"class": "form-control", "style": "width: 100%;"}),
            'value_2_month': forms.NumberInput(attrs={"class": "form-control", "style": "width: 100%;"}),
            'value_3_month': forms.NumberInput(attrs={"class": "form-control", "style": "width: 100%;"}),
            'description': forms.Textarea(attrs={"class": "form-control", "rows": 4, "style": "width: 100%;"}),
            'image': forms.FileInput(attrs={"class": "form-control", "accept": "image/*"}),
        }


class ExpenseForm(forms.ModelForm):
    class Meta:
        model = models.Expense
        fields = ['category', 'date', 'amount', 'description', 'attachment']
        widgets = {
            'date': forms.DateInput(attrs={'type': 'date'}, format='%Y-%m-%d'),
            'description': forms.Textarea(attrs={'rows': 2, 'placeholder': 'Optional'}),
            'attachment': forms.FileInput(attrs={'class': 'form-control'}),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['date'].input_formats = ['%Y-%m-%d']
        self.fields['date'].localize = False
        if self.instance and self.instance.pk and self.instance.date:
            self.fields['date'].initial = self.instance.date.strftime(
                '%Y-%m-%d')
        # Fix initial date if provided in DD/MM/YYYY
        if 'initial' in kwargs and 'date' in kwargs['initial']:
            d = kwargs['initial']['date']
            if isinstance(d, str) and '/' in d:
                try:
                    day, month, year = d.split('/')
                    self.fields['date'].initial = f"{year}-{month.zfill(2)}-{day.zfill(2)}"
                except Exception:
                    pass
        # If form is bound (POST), forcibly correct the value
        if self.is_bound:
            data = self.data.copy()
            val = data.get(self.add_prefix('date'))
            if val and '/' in val:
                try:
                    day, month, year = val.split('/')
                    data[self.add_prefix(
                        'date')] = f"{year}-{month.zfill(2)}-{day.zfill(2)}"
                    self.data = data
                except Exception:
                    pass


class ExpenseCategoryForm(forms.ModelForm):
    class Meta:
        model = models.ExpenseCategory
        fields = ['name']


class FilterForm(forms.Form):

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.helper = FormHelper()

        self.helper.form_tag = False
        fields = (Div(field, css_class='col-md-4')
                  for field in args[0].fields.keys())
        self.helper.layout = Layout(
            Div(
                *fields,
                css_class='row'
            )
        )

class ParticipantSelectWidget(s2forms.Select2MultipleWidget):
    def build_attrs(self, *args, **kwargs):
        attrs = super().build_attrs(*args, **kwargs)
        attrs.update({
            'data-placeholder': 'Select participants...',
            'data-allow-clear': 'true',
            'data-close-on-select': 'false',
            'style': 'width: 100%;',
        })
        return attrs


class CalendarEventForm(forms.ModelForm):
    """Form for creating and updating calendar events."""
    
    class Meta:
        model = models.CalendarEvent
        fields = ['title', 'description', 'start_date', 'end_date', 'all_day', 'theme', 'participants']
        widgets = {
            'title': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Event title',
            }),
            'description': forms.Textarea(attrs={
                'class': 'form-control',
                'rows': 3,
                'placeholder': 'Event description (optional)',
            }),
            'start_date': forms.DateTimeInput(
                attrs={
                    'type': 'datetime-local',
                    'class': 'form-control',
                },
                format='%Y-%m-%dT%H:%M'
            ),
            'end_date': forms.DateTimeInput(
                attrs={
                    'type': 'datetime-local',
                    'class': 'form-control',
                },
                format='%Y-%m-%dT%H:%M'
            ),
            'all_day': forms.CheckboxInput(attrs={
                'class': 'form-check-input',
            }),
            'theme': forms.Select(attrs={
                'class': 'form-select',
            }),
            'participants': ParticipantSelectWidget(),
        }
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        
        # Set initial values for datetime fields
        now = timezone.now()
        if not self.instance.pk:  # New event
            if not self.initial.get('start_date'):
                self.initial['start_date'] = now.replace(minute=0, second=0, microsecond=0)
            if not self.initial.get('end_date'):
                self.initial['end_date'] = (now.replace(minute=0, second=0, microsecond=0) + 
                                          timezone.timedelta(hours=1))
        
        # Set the format for datetime fields
        if 'start_date' in self.fields:
            self.fields['start_date'].input_formats = ['%Y-%m-%dT%H:%M']
        if 'end_date' in self.fields:
            self.fields['end_date'].input_formats = ['%Y-%m-%dT%H:%M']
        
        # Set choices for theme field
        self.fields['theme'].choices = [
            ('primary', 'Primary'),
            ('secondary', 'Secondary'),
            ('success', 'Success'),
            ('danger', 'Danger'),
            ('warning', 'Warning'),
            ('info', 'Info'),
            ('light', 'Light'),
            ('dark', 'Dark'),
        ]
    
    def clean(self):
        cleaned_data = super().clean()
        start_date = cleaned_data.get('start_date')
        end_date = cleaned_data.get('end_date')
        
        if start_date and end_date and start_date > end_date:
            self.add_error('end_date', 'End date must be after start date')
        
        return cleaned_data
