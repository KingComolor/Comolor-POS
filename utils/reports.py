from io import BytesIO
from reportlab.lib.pagesizes import letter, A4
from reportlab.platypus import SimpleDocTemplate, Table, TableStyle, Paragraph, Spacer
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import inch
from reportlab.lib import colors
from datetime import datetime
import csv
import io

def generate_sales_report_pdf(sales_data, shop_name, report_title, date_range=None):
    """Generate PDF sales report"""
    buffer = BytesIO()
    doc = SimpleDocTemplate(buffer, pagesize=A4)
    
    # Styles
    styles = getSampleStyleSheet()
    title_style = ParagraphStyle(
        'CustomTitle',
        parent=styles['Heading1'],
        fontSize=18,
        spaceAfter=30,
        alignment=1  # Center
    )
    
    story = []
    
    # Title
    story.append(Paragraph(report_title, title_style))
    story.append(Paragraph(f"<b>Shop:</b> {shop_name}", styles['Normal']))
    
    if date_range:
        story.append(Paragraph(f"<b>Period:</b> {date_range}", styles['Normal']))
    
    story.append(Paragraph(f"<b>Generated:</b> {datetime.now().strftime('%Y-%m-%d %H:%M')}", styles['Normal']))
    story.append(Spacer(1, 20))
    
    # Sales table
    if sales_data:
        table_data = [['Receipt #', 'Date', 'Cashier', 'Items', 'Total', 'Payment']]
        
        for sale in sales_data:
            table_data.append([
                sale.receipt_number,
                sale.created_at.strftime('%Y-%m-%d %H:%M'),
                sale.cashier_user.username,
                len(sale.items),
                f"KES {sale.total_amount:,.2f}",
                sale.payment_method.upper()
            ])
        
        # Calculate totals
        total_sales = sum(sale.total_amount for sale in sales_data)
        cash_sales = sum(sale.total_amount for sale in sales_data if sale.payment_method == 'cash')
        mpesa_sales = sum(sale.total_amount for sale in sales_data if sale.payment_method == 'mpesa')
        
        table_data.append(['', '', '', '', '', ''])
        table_data.append(['', '', '', 'TOTAL:', f"KES {total_sales:,.2f}", ''])
        table_data.append(['', '', '', 'Cash:', f"KES {cash_sales:,.2f}", ''])
        table_data.append(['', '', '', 'MPesa:', f"KES {mpesa_sales:,.2f}", ''])
        
        table = Table(table_data)
        table.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (-1, 0), colors.grey),
            ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
            ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
            ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
            ('FONTSIZE', (0, 0), (-1, 0), 12),
            ('BOTTOMPADDING', (0, 0), (-1, 0), 12),
            ('BACKGROUND', (0, 1), (-1, -4), colors.beige),
            ('BACKGROUND', (0, -3), (-1, -1), colors.lightgrey),
            ('FONTNAME', (0, -3), (-1, -1), 'Helvetica-Bold'),
            ('GRID', (0, 0), (-1, -1), 1, colors.black)
        ]))
        
        story.append(table)
    else:
        story.append(Paragraph("No sales data found for the specified period.", styles['Normal']))
    
    doc.build(story)
    buffer.seek(0)
    return buffer

def generate_product_report_pdf(products_data, shop_name):
    """Generate PDF product report"""
    buffer = BytesIO()
    doc = SimpleDocTemplate(buffer, pagesize=A4)
    
    styles = getSampleStyleSheet()
    title_style = ParagraphStyle(
        'CustomTitle',
        parent=styles['Heading1'],
        fontSize=18,
        spaceAfter=30,
        alignment=1
    )
    
    story = []
    
    # Title
    story.append(Paragraph("Product Inventory Report", title_style))
    story.append(Paragraph(f"<b>Shop:</b> {shop_name}", styles['Normal']))
    story.append(Paragraph(f"<b>Generated:</b> {datetime.now().strftime('%Y-%m-%d %H:%M')}", styles['Normal']))
    story.append(Spacer(1, 20))
    
    # Products table
    if products_data:
        table_data = [['Name', 'Category', 'Price', 'Stock', 'Status']]
        
        for product in products_data:
            status = "Low Stock" if product.is_low_stock else "In Stock"
            if not product.is_active:
                status = "Inactive"
            
            table_data.append([
                product.name,
                product.category.name if product.category else 'Uncategorized',
                f"KES {product.price:,.2f}",
                str(product.stock_quantity),
                status
            ])
        
        table = Table(table_data)
        table.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (-1, 0), colors.grey),
            ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
            ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
            ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
            ('FONTSIZE', (0, 0), (-1, 0), 12),
            ('BOTTOMPADDING', (0, 0), (-1, 0), 12),
            ('BACKGROUND', (0, 1), (-1, -1), colors.beige),
            ('GRID', (0, 0), (-1, -1), 1, colors.black)
        ]))
        
        story.append(table)
    else:
        story.append(Paragraph("No products found.", styles['Normal']))
    
    doc.build(story)
    buffer.seek(0)
    return buffer

def generate_sales_csv(sales_data):
    """Generate CSV sales report"""
    output = io.StringIO()
    writer = csv.writer(output)
    
    # Header
    writer.writerow(['Receipt Number', 'Date', 'Cashier', 'Customer Phone', 'Customer Name', 
                     'Subtotal', 'Tax', 'Total', 'Payment Method', 'MPesa Receipt', 'Status'])
    
    # Data
    for sale in sales_data:
        writer.writerow([
            sale.receipt_number,
            sale.created_at.strftime('%Y-%m-%d %H:%M:%S'),
            sale.cashier_user.username,
            sale.customer_phone or '',
            sale.customer_name or '',
            float(sale.subtotal),
            float(sale.tax_amount),
            float(sale.total_amount),
            sale.payment_method,
            sale.mpesa_receipt or '',
            sale.status
        ])
    
    output.seek(0)
    return output.getvalue()

def generate_products_csv(products_data):
    """Generate CSV products report"""
    output = io.StringIO()
    writer = csv.writer(output)
    
    # Header
    writer.writerow(['Name', 'Description', 'Category', 'SKU', 'Barcode', 'Price', 
                     'Cost Price', 'Stock Quantity', 'Low Stock Threshold', 'Status'])
    
    # Data
    for product in products_data:
        writer.writerow([
            product.name,
            product.description or '',
            product.category.name if product.category else '',
            product.sku or '',
            product.barcode or '',
            float(product.price),
            float(product.cost_price),
            product.stock_quantity,
            product.low_stock_threshold,
            'Active' if product.is_active else 'Inactive'
        ])
    
    output.seek(0)
    return output.getvalue()
