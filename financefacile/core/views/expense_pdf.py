import io
from django.http import HttpResponse
from django.shortcuts import get_object_or_404
from reportlab.lib.pagesizes import letter
from reportlab.lib import colors
from reportlab.platypus import SimpleDocTemplate, Table, TableStyle, Paragraph, Spacer
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import inch
from core.models import Expense, ExpenseCategory
from django.utils import timezone
from django.db.models import Sum
from datetime import datetime, timedelta

def generate_expense_pdf(request, pk=None):
    """
    Generate a PDF for a specific expense or a summary of filtered expenses.
    If pk is provided, generates a PDF for that specific expense.
    If pk is None, generates a summary PDF of all expenses based on filter parameters.
    """
    buffer = io.BytesIO()
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
    elements = []
    
    if pk:
        # Single expense PDF
        expense = get_object_or_404(Expense, pk=pk)
        
        elements.extend([
            Paragraph("EXPENSE DETAILS", title_style),
            Spacer(1, 0.25*inch),
            Paragraph(f"Category: {expense.category.name}", normal_style),
            Spacer(1, 0.1*inch),
            Paragraph(f"Date: {expense.date.strftime('%Y-%m-%d')}", normal_style),
            Spacer(1, 0.1*inch),
            Paragraph(f"Amount: {expense.amount:.2f}", normal_style),
            Spacer(1, 0.25*inch)
        ])
        
        if expense.description:
            elements.extend([
                Paragraph("Description:", header_style),
                Paragraph(expense.description, normal_style),
                Spacer(1, 0.25*inch)
            ])
        
        filename = f"expense_{expense.pk}_{expense.date}.pdf"
    else:
        # Filter parameters
        start_date = request.GET.get('start_date')
        end_date = request.GET.get('end_date')
        categories = request.GET.getlist('categories')
        
        # Build query
        expenses_query = Expense.objects.all()
        
        filter_description = "All Expenses"
        
        if start_date and end_date:
            from contextlib import suppress
            with suppress(ValueError):
                start_date = datetime.strptime(start_date, '%Y-%m-%d').date()
                end_date = datetime.strptime(end_date, '%Y-%m-%d').date()
                expenses_query = expenses_query.filter(date__range=[start_date, end_date])
                filter_description = f"Expenses from {start_date} to {end_date}"
        
        if categories and (category_names := ExpenseCategory.objects.filter(id__in=categories).values_list('name', flat=True)):
            expenses_query = expenses_query.filter(category__id__in=categories)
            filter_description += f" in categories: {', '.join(category_names)}"
        
        # Order by date
        expenses = expenses_query.order_by('-date')
        
        # Calculate totals
        total_amount = expenses.aggregate(total=Sum('amount'))['total'] or 0
        
        # Create the report header elements
        def create_report_header():
            return [
                Paragraph("EXPENSES REPORT", title_style),
                Spacer(1, 0.25*inch),
                Paragraph(filter_description, normal_style),
                Spacer(1, 0.25*inch),
                Paragraph(f"Total Amount: {total_amount:.2f}", header_style),
                Spacer(1, 0.25*inch)
            ]
            
        elements.extend(create_report_header())
        
        # Create table for expenses
        if expenses.exists():
            data = [['Date', 'Category', 'Amount', 'Description']]
            
            # Add expenses to table
            data.extend([
                [
                    expense.date.strftime('%Y-%m-%d'),
                    expense.category.name,
                    f"{expense.amount:.2f}",
                    expense.description or ""
                ] for expense in expenses
            ])
            
            # Add total row
            data.append(['', 'TOTAL', f"{total_amount:.2f}", ''])
            
            # Create the expenses table
            expenses_table = Table(data, colWidths=[1*inch, 1.5*inch, 1*inch, 2.5*inch])
            
            # Add style to expenses table
            table_style = TableStyle([
                ('BACKGROUND', (0, 0), (-1, 0), colors.lightblue),
                ('TEXTCOLOR', (0, 0), (-1, 0), colors.black),
                ('ALIGN', (0, 0), (-1, 0), 'CENTER'),
                ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
                ('FONTSIZE', (0, 0), (-1, 0), 12),
                ('BOTTOMPADDING', (0, 0), (-1, 0), 12),
                ('BACKGROUND', (0, 1), (-1, -2), colors.white),
                ('TEXTCOLOR', (0, 1), (-1, -1), colors.black),
                ('ALIGN', (0, 1), (0, -1), 'LEFT'),
                ('ALIGN', (2, 1), (2, -1), 'RIGHT'),
                ('FONTNAME', (0, 1), (-1, -1), 'Helvetica'),
                ('FONTSIZE', (0, 1), (-1, -1), 10),
                ('GRID', (0, 0), (-1, -2), 0.5, colors.grey),
                ('LINEABOVE', (0, -1), (-1, -1), 1, colors.black),
                ('FONTNAME', (1, -1), (2, -1), 'Helvetica-Bold'),
            ])
            expenses_table.setStyle(table_style)
            
            # Add expenses table to elements
            elements.append(expenses_table)
        else:
            elements.append(Paragraph("No expenses found matching the criteria.", normal_style))
        
        # Category breakdown
        if expenses.exists():
            elements.extend([
                Spacer(1, 0.5*inch),
                Paragraph("Expense Breakdown by Category", header_style),
                Spacer(1, 0.1*inch)
            ])
            
            # Calculate totals by category
            category_totals = {}
            for expense in expenses:
                category_name = expense.category.name
                if category_name not in category_totals:
                    category_totals[category_name] = 0
                category_totals[category_name] += expense.amount
            
            # Create table for category breakdown
            category_data = [['Category', 'Amount', 'Percentage']]
            
            # Add categories to table
            for category, amount in category_totals.items():
                percentage = (amount / total_amount) * 100 if total_amount > 0 else 0
                category_data.append([
                    category,
                    f"{amount:.2f}",
                    f"{percentage:.1f}%"
                ])
            
            # Create the category table
            category_table = Table(category_data, colWidths=[3*inch, 1.5*inch, 1.5*inch])
            
            # Add style to category table
            category_style = TableStyle([
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
            category_table.setStyle(category_style)
            
            # Add category table to elements
            elements.append(category_table)
        
        filename = f"expenses_report_{timezone.now().strftime('%Y%m%d')}.pdf"
    
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
    response['Content-Disposition'] = f'attachment; filename="{filename}"'
    response.write(pdf)
    
    return response
