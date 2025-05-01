import io
from django.http import HttpResponse
from django.shortcuts import get_object_or_404
from reportlab.lib.pagesizes import letter
from reportlab.lib import colors
from reportlab.platypus import SimpleDocTemplate, Table, TableStyle, Paragraph, Spacer, Image
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import inch
from core.models import Product, InvoiceItem
from django.utils import timezone
from django.db.models import Sum

def generate_product_pdf(request, pk):
    """Generate a PDF for the specified product ID"""
    
    # Get the product object
    product = get_object_or_404(Product, pk=pk)
    
    # Create a file-like buffer to receive PDF data
    buffer = io.BytesIO()
    
    # Create the PDF object using the buffer as its "file"
    doc = SimpleDocTemplate(buffer, pagesize=letter)
    
    # Get styles
    styles = getSampleStyleSheet()
    
    # Custom styles
    title_style = ParagraphStyle(
        'Title',
        parent=styles['Heading1'],
        fontSize=16,
        alignment=1,  # Center alignment
        spaceAfter=12
    )
    
    header_style = ParagraphStyle(
        'Header',
        parent=styles['Heading2'],
        fontSize=14,
        spaceAfter=10
    )
    
    normal_style = styles["Normal"]
    
    # Container for the 'Flowable' objects with initial elements
    elements = [
        Paragraph(f"PRODUCT DETAILS: {product.name}", title_style),
        Spacer(1, 0.25*inch),
        Paragraph(f"SKU: {product.sku}", normal_style),
        Spacer(1, 0.25*inch)
    ]
    
    # Create table for product details
    data = [
        ['Description', product.description or 'No description provided.'],
        ['Quantity', str(product.quantity)],
        ['Unit Cost', f"{product.unit_cost:.2f}"],
        ['Selling Price', f"{product.selling_price:.2f}"],
        ['Current Value', f"{product.quantity * product.unit_cost:.2f}"]
    ]
    
    # Create the details table
    details_table = Table(data, colWidths=[2*inch, 4*inch])
    
    # Add style to details table
    details_style = TableStyle([
        ('BACKGROUND', (0, 0), (0, -1), colors.lightblue),
        ('TEXTCOLOR', (0, 0), (0, -1), colors.black),
        ('ALIGN', (0, 0), (0, -1), 'LEFT'),
        ('FONTNAME', (0, 0), (0, -1), 'Helvetica-Bold'),
        ('FONTSIZE', (0, 0), (0, -1), 12),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 10),
        ('BACKGROUND', (1, 0), (1, -1), colors.white),
        ('GRID', (0, 0), (-1, -1), 0.5, colors.grey),
    ])
    details_table.setStyle(details_style)
    
    # Add details table to elements
    elements.append(details_table)
    elements.append(Spacer(1, 0.5*inch))
    
    # Get invoice items for this product
    invoice_items = InvoiceItem.objects.filter(product=product)
    
    # Add sales history section if there are invoice items
    if invoice_items.exists():
        elements.extend([
            Paragraph("Sales History:", header_style),
            Spacer(1, 0.1*inch)
        ])
        
        # Create table for sales history
        sales_data = [['Invoice #', 'Date', 'Quantity', 'Price', 'Total']]
        
        # Add invoice items to table
        sales_data.extend([
            [
                str(item.invoice.pk),
                item.invoice.created_at.strftime('%Y-%m-%d'),
                str(item.quantity),
                f"{item.selling_price:.2f}",
                f"{item.total_price:.2f}"
            ] for item in invoice_items
        ])
        
        # Add summary row with totals
        total_quantity = invoice_items.aggregate(total=Sum('quantity'))['total'] or 0
        total_value = sum(item.total_price for item in invoice_items)
        sales_data.append(['', 'TOTAL', str(total_quantity), '', f"{total_value:.2f}"])
        
        # Create the sales table
        sales_table = Table(sales_data, colWidths=[1*inch, 1.5*inch, 1*inch, 1.25*inch, 1.25*inch])
        
        # Add style to sales table
        sales_style = TableStyle([
            ('BACKGROUND', (0, 0), (-1, 0), colors.lightblue),
            ('TEXTCOLOR', (0, 0), (-1, 0), colors.black),
            ('ALIGN', (0, 0), (-1, 0), 'CENTER'),
            ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
            ('FONTSIZE', (0, 0), (-1, 0), 12),
            ('BOTTOMPADDING', (0, 0), (-1, 0), 12),
            ('BACKGROUND', (0, 1), (-1, -2), colors.white),
            ('TEXTCOLOR', (0, 1), (-1, -1), colors.black),
            ('ALIGN', (0, 1), (0, -1), 'LEFT'),
            ('ALIGN', (2, 1), (-1, -1), 'RIGHT'),
            ('FONTNAME', (0, 1), (-1, -1), 'Helvetica'),
            ('FONTSIZE', (0, 1), (-1, -1), 10),
            ('GRID', (0, 0), (-1, -2), 0.5, colors.grey),
            ('LINEABOVE', (0, -1), (-1, -1), 1, colors.black),
            ('FONTNAME', (0, -1), (-1, -1), 'Helvetica-Bold'),
        ])
        sales_table.setStyle(sales_style)
        
        # Add sales table to elements
        elements.append(sales_table)
    
    # Add footer with generation timestamp
    timestamp = timezone.now().strftime('%Y-%m-%d %H:%M:%S')
    elements.extend([
        Spacer(1, 0.5*inch),
        Paragraph(f"Generated on: {timestamp}", 
                ParagraphStyle('Footer', parent=normal_style, fontSize=8, textColor=colors.grey))
    ])
    
    # Build the PDF
    doc.build(elements)
    
    # Get the value of the BytesIO buffer
    pdf = buffer.getvalue()
    buffer.close()
    
    # Create the HTTP response with PDF content
    response = HttpResponse(content_type='application/pdf')
    response['Content-Disposition'] = f'attachment; filename="product_{product.pk}_{product.name}.pdf"'
    response.write(pdf)
    
    return response
