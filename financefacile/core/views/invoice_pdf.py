import io
from django.http import HttpResponse
from django.shortcuts import get_object_or_404
from reportlab.lib.pagesizes import letter
from reportlab.lib import colors
from reportlab.platypus import SimpleDocTemplate, Table, TableStyle, Paragraph, Spacer
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import inch
from core.models import Invoice
from django.utils import timezone
from accounts.models import CompanySettings

def generate_invoice_pdf(request, pk):
    """Generate a PDF invoice for the specified invoice ID"""
    
    # Get the invoice object
    invoice = get_object_or_404(Invoice, pk=pk)
    
    # Get the currency symbol from company settings
    currency_symbol = 'DT'  # Default currency
    if invoice.company:
        try:
            company_settings = CompanySettings.objects.get(company=invoice.company)
            currency_symbol = company_settings.currency
        except CompanySettings.DoesNotExist:
            pass
    
    # Create a file-like buffer to receive PDF data
    buffer = io.BytesIO()
    
    # Create the PDF object using the buffer as its "file"
    doc = SimpleDocTemplate(buffer, pagesize=letter)
    
    # Container for the 'Flowable' objects
    elements = []
    
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
    
    # Add invoice header
    elements.append(Paragraph(f"INVOICE INV-{invoice.pk}", title_style))
    elements.append(Spacer(1, 0.25*inch))
    
    # Add invoice date
    date_str = invoice.created_at.strftime('%Y-%m-%d %H:%M')
    elements.append(Paragraph(f"Date: {date_str}", normal_style))
    elements.append(Spacer(1, 0.1*inch))
    
    # Add company information if available
    if invoice.company:
        company_style = ParagraphStyle(
            'Company',
            parent=styles['Heading3'],
            fontSize=12,
            spaceAfter=6
        )
        company_info_style = ParagraphStyle(
            'CompanyInfo',
            parent=normal_style,
            fontSize=10,
            leftIndent=10
        )
        
        elements.append(Paragraph("Company Information:", company_style))
        elements.append(Paragraph(f"<b>Name:</b> {invoice.company.name}", company_info_style))
        
        if invoice.company.siret_number:
            elements.append(Paragraph(f"<b>SIRET Number:</b> {invoice.company.siret_number}", company_info_style))
        
        if invoice.company.address:
            elements.append(Paragraph(f"<b>Address:</b> {invoice.company.address}", company_info_style))
        
        if invoice.company.phone_number:
            elements.append(Paragraph(f"<b>Phone:</b> {invoice.company.phone_number}", company_info_style))
        
        elements.append(Spacer(1, 0.25*inch))
    
    # Add invoice items section header
    elements.append(Paragraph("Invoice Items:", header_style))
    elements.append(Spacer(1, 0.1*inch))
    
    # Create table for invoice items
    data = [['Product', 'Quantity', 'Price', 'Total']]
    
    # Add invoice items to table
    for item in invoice.items.all():
        data.append([
            item.product.name,
            str(item.quantity),
            f"{item.selling_price:.2f} {currency_symbol}",
            f"{item.total_price:.2f} {currency_symbol}"
        ])
    
    # Create the table
    items_table = Table(data, colWidths=[3*inch, 1*inch, 1.25*inch, 1.25*inch])
    
    # Add style to items table
    items_style = TableStyle([
        ('BACKGROUND', (0, 0), (-1, 0), colors.lightblue),
        ('TEXTCOLOR', (0, 0), (-1, 0), colors.black),
        ('ALIGN', (0, 0), (-1, 0), 'CENTER'),
        ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
        ('FONTSIZE', (0, 0), (-1, 0), 12),
        ('BOTTOMPADDING', (0, 0), (-1, 0), 12),
        ('BACKGROUND', (0, 1), (-1, -1), colors.white),
        ('TEXTCOLOR', (0, 1), (-1, -1), colors.black),
        ('ALIGN', (0, 1), (0, -1), 'LEFT'),
        ('ALIGN', (1, 1), (-1, -1), 'RIGHT'),
        ('FONTNAME', (0, 1), (-1, -1), 'Helvetica'),
        ('FONTSIZE', (0, 1), (-1, -1), 10),
        ('GRID', (0, 0), (-1, -1), 0.5, colors.grey),
    ])
    items_table.setStyle(items_style)
    
    # Add items table to elements
    elements.append(items_table)
    elements.append(Spacer(1, 0.25*inch))
    
    # Add invoice summary section header
    elements.append(Paragraph("Invoice Summary:", header_style))
    elements.append(Spacer(1, 0.1*inch))
    
    # Create table for invoice summary
    summary_data = [
        ['Subtotal:', f"{invoice.get_subtotal():.2f} {currency_symbol}"],
        [f"TVA ({invoice.get_tva_rate():.2f}%):", f"{invoice.get_tva_amount():.2f} {currency_symbol}"],
    ]
    
    # Add stamp fee if included
    if invoice.include_stamp_fee:
        summary_data.append(['Stamp Fee:', f"{invoice.get_stamp_fee():.2f} {currency_symbol}"])
    
    # Add total row
    summary_data.append(['Total:', f"{invoice.get_total():.2f} {currency_symbol}"])
    
    # Create the summary table
    summary_table = Table(summary_data, colWidths=[2*inch, 1*inch])
    
    # Add style to summary table
    summary_style = TableStyle([
        ('ALIGN', (0, 0), (0, -1), 'RIGHT'),
        ('ALIGN', (1, 0), (1, -1), 'RIGHT'),
        ('FONTNAME', (0, -1), (1, -1), 'Helvetica-Bold'),
        ('LINEABOVE', (0, -1), (1, -1), 1, colors.black),
    ])
    summary_table.setStyle(summary_style)
    
    # Add summary table to elements
    elements.append(summary_table)
    
    # Add footer with generation timestamp
    elements.append(Spacer(1, 0.5*inch))
    timestamp = timezone.now().strftime('%Y-%m-%d %H:%M:%S')
    elements.append(Paragraph(f"Generated on: {timestamp}", 
                             ParagraphStyle('Footer', parent=normal_style, fontSize=8, textColor=colors.grey)))
    
    # Build the PDF
    doc.build(elements)
    
    # Get the value of the BytesIO buffer
    pdf = buffer.getvalue()
    buffer.close()
    
    # Create the HTTP response with PDF content
    response = HttpResponse(content_type='application/pdf')
    response['Content-Disposition'] = f'attachment; filename="invoice_{invoice.pk}.pdf"'
    response.write(pdf)
    
    return response
