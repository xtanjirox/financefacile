from django.shortcuts import render
from django.db.models import Q
from core.models import Product, Invoice, ProductCategory

def global_search(request):
    query = request.GET.get('q', '').strip()
    products = invoices = categories = []
    if query:
        products = Product.objects.filter(
            Q(name__icontains=query) | Q(sku__icontains=query) | Q(description__icontains=query)
        )
        invoices = Invoice.objects.filter(
            Q(id__icontains=query) | Q(created_at__icontains=query)
        )
        categories = ProductCategory.objects.filter(
            Q(name__icontains=query)
        )
    return render(request, 'search_results.html', {
        'page_title': 'Search Results',
        'page_title_badge': 'Search Results',
        'query': query,
        'products': products,
        'invoices': invoices,
        'categories': categories,
    })
