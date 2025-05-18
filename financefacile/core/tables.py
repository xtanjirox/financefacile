import logging
import django_tables2 as tables
from . import models

ACTIONS_BUTTONS_TEMPLATE = """
    <a href="get_absolute_url" class="btn btn-sm shadow-sm me-1" style="background: #fffde7; color: #f9a825; border-radius: 7px; font-weight: 500; border: none;" data-bs-toggle="tooltip" title="Edit">
        <i class="fas fa-edit"></i>
    </a>
    <a href="get_delete_url" class="btn btn-sm shadow-sm me-1" style="background: #ffebee; color: #c62828; border-radius: 7px; font-weight: 500; border: none;" data-bs-toggle="tooltip" title="Delete">
        <i class="fas fa-trash"></i>
    </a>
"""

DEFAULT_TABLE_ATTRS = {
    "id": "datatables-orders",
    "class": "table table-responsive table-striped dataTable no-footer dtr-inline",
    "width": "100%",
    "aria - describedby": "datatables-orders_info",
    "style": "width: 100%;"
}


class ProductTable(tables.Table):
    actions = tables.TemplateColumn(ACTIONS_BUTTONS_TEMPLATE)
    category = tables.Column(accessor='category.name', verbose_name='Category')

    class Meta:
        model = models.Product
        attrs = {"class": "table table-material"}
        fields = ('name', 'sku', 'category', 'quantity', 'unit_cost', 'selling_price')


class ProductCategoryTable(tables.Table):
    actions = tables.TemplateColumn(ACTIONS_BUTTONS_TEMPLATE, orderable=False, verbose_name='Actions')
    parent = tables.Column(accessor='parent.name', verbose_name='Parent Category')
    
    class Meta:
        model = models.ProductCategory
        attrs = {
            'class': 'table table-striped table-hover',
            'id': 'categoriesTable',
            'style': 'width: 100%',
        }
        fields = ('name', 'parent', 'actions')
        order_by = 'name'
        
    def render_actions(self, value, record):
        if value is None:
            value = ''
        try:
            url = value.replace('get_absolute_url', record.get_absolute_url())
            if hasattr(record, 'get_delete_url') and record.get_delete_url():
                url = url.replace('get_delete_url', record.get_delete_url())
            if hasattr(record, 'get_update_url') and record.get_update_url():
                url = url.replace('get_update_url', record.get_update_url())
            return url
        except Exception as e:
            logger = logging.getLogger(__name__)
            logger.error(f"Error rendering actions for record {record.id}: {str(e)}")
            return ''
'''
class EntryCategoryTable(tables.Table):
    actions = tables.TemplateColumn(ACTIONS_BUTTONS_TEMPLATE)

    class Meta:
        model = models.EntryCategory
        attrs = DEFAULT_TABLE_ATTRS
        fields = ('category_title', 'finance_entry_type')
'''

'''
class EntriesTable(tables.Table):
    actions = tables.TemplateColumn(ACTIONS_BUTTONS_TEMPLATE)

    class Meta:
        model = models.FinanceEntry
        attrs = DEFAULT_TABLE_ATTRS
        fields = ('entry_label', 'entry_category', 'finance_entry_type', 'entry_value', 'entry_date')
'''