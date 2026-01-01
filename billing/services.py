"""
Billing App - Services

Business logic for bill generation and invoice management.
"""

from django.db import transaction
from django.utils import timezone
from decimal import Decimal
from io import BytesIO

from .models import OrderBill, Invoice
from config.models import SystemConfiguration


class BillingService:
    """Service class for billing operations."""
    
    @staticmethod
    @transaction.atomic
    def generate_bill(order, advance_amount=Decimal('0.00')):
        """
        Generate a bill for an order.
        
        Args:
            order: Order instance
            advance_amount: Advance payment if any
        
        Returns:
            OrderBill instance
        """
        # Get system configuration
        config = SystemConfiguration.get_config()
        
        # Calculate base price from garment type
        base_price = order.garment_type.base_price
        
        # Calculate work type charges
        work_type_charges = order.get_total_work_type_charges()
        
        # Calculate alteration charges (if any)
        alteration_charges = Decimal('0.00')
        if hasattr(order, 'trial') and order.trial:
            for alt in order.trial.alterations.filter(is_included_in_original=False):
                alteration_charges += alt.estimated_cost
        
        # Calculate urgency surcharge
        urgency_surcharge = Decimal('0.00')
        if order.is_urgent:
            subtotal = base_price + work_type_charges + alteration_charges
            urgency_surcharge = subtotal * (order.urgency_multiplier - Decimal('1.00'))
        
        # Create or update bill
        bill, created = OrderBill.objects.update_or_create(
            order=order,
            defaults={
                'base_garment_price': base_price,
                'work_type_charges': work_type_charges,
                'alteration_charges': alteration_charges,
                'urgency_surcharge': urgency_surcharge,
                'tax_rate': config.default_tax_rate,
                'advance_amount': advance_amount,
            }
        )
        
        return bill
    
    @staticmethod
    @transaction.atomic
    def generate_invoice(bill, generated_by, due_days=7):
        """
        Generate an invoice from a bill.
        
        Args:
            bill: OrderBill instance
            generated_by: User generating the invoice
            due_days: Number of days until due
        
        Returns:
            Invoice instance
        """
        order = bill.order
        customer = order.customer.user
        
        invoice = Invoice.objects.create(
            invoice_number=Invoice.generate_invoice_number(),
            bill=bill,
            invoice_date=timezone.now().date(),
            due_date=timezone.now().date() + timezone.timedelta(days=due_days),
            customer_name=customer.get_full_name() or customer.username,
            customer_email=customer.email,
            customer_phone=order.customer.phone or '',
            status='ISSUED',
            generated_by=generated_by,
            issued_at=timezone.now(),
        )
        
        return invoice
    
    @staticmethod
    def generate_invoice_pdf(invoice):
        """
        Generate PDF for an invoice.
        
        Args:
            invoice: Invoice instance
        
        Returns:
            BytesIO containing PDF data
        """
        from reportlab.lib import colors
        from reportlab.lib.pagesizes import A4
        from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
        from reportlab.lib.units import inch
        from reportlab.platypus import SimpleDocTemplate, Table, TableStyle, Paragraph, Spacer
        
        buffer = BytesIO()
        doc = SimpleDocTemplate(buffer, pagesize=A4, topMargin=0.5*inch, bottomMargin=0.5*inch)
        
        elements = []
        styles = getSampleStyleSheet()
        
        # Header
        title_style = ParagraphStyle(
            'CustomTitle',
            parent=styles['Heading1'],
            fontSize=24,
            textColor=colors.HexColor('#4361ee'),
            spaceAfter=20,
        )
        elements.append(Paragraph('INVOICE', title_style))
        elements.append(Spacer(1, 12))
        
        # Invoice details
        bill = invoice.bill
        
        invoice_data = [
            ['Invoice No:', invoice.invoice_number],
            ['Date:', invoice.invoice_date.strftime('%B %d, %Y')],
            ['Due Date:', invoice.due_date.strftime('%B %d, %Y')],
            ['Order No:', bill.order.order_number],
        ]
        
        info_table = Table(invoice_data, colWidths=[2*inch, 3*inch])
        info_table.setStyle(TableStyle([
            ('FONTNAME', (0, 0), (0, -1), 'Helvetica-Bold'),
            ('FONTSIZE', (0, 0), (-1, -1), 10),
            ('BOTTOMPADDING', (0, 0), (-1, -1), 8),
        ]))
        elements.append(info_table)
        elements.append(Spacer(1, 20))
        
        # Customer details
        elements.append(Paragraph('Bill To:', styles['Heading3']))
        elements.append(Paragraph(invoice.customer_name, styles['Normal']))
        elements.append(Paragraph(invoice.customer_email, styles['Normal']))
        if invoice.customer_phone:
            elements.append(Paragraph(invoice.customer_phone, styles['Normal']))
        elements.append(Spacer(1, 20))
        
        # Line items
        items_data = [
            ['Description', 'Amount (₹)'],
            ['Base Garment Price', f'{bill.base_garment_price:,.2f}'],
        ]
        
        if bill.work_type_charges > 0:
            items_data.append(['Work Type Charges', f'{bill.work_type_charges:,.2f}'])
        
        if bill.alteration_charges > 0:
            items_data.append(['Alteration Charges', f'{bill.alteration_charges:,.2f}'])
        
        if bill.urgency_surcharge > 0:
            items_data.append(['Urgency Surcharge', f'{bill.urgency_surcharge:,.2f}'])
        
        items_data.append(['Subtotal', f'{bill.subtotal:,.2f}'])
        items_data.append([f'Tax ({bill.tax_rate}%)', f'{bill.tax_amount:,.2f}'])
        items_data.append(['Total', f'{bill.total_amount:,.2f}'])
        
        if bill.advance_amount > 0:
            items_data.append(['Less: Advance Paid', f'-{bill.advance_amount:,.2f}'])
            items_data.append(['Balance Due', f'{bill.balance_amount:,.2f}'])
        
        items_table = Table(items_data, colWidths=[4*inch, 2*inch])
        items_table.setStyle(TableStyle([
            ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
            ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#4361ee')),
            ('TEXTCOLOR', (0, 0), (-1, 0), colors.white),
            ('ALIGN', (1, 0), (1, -1), 'RIGHT'),
            ('FONTSIZE', (0, 0), (-1, -1), 10),
            ('BOTTOMPADDING', (0, 0), (-1, -1), 12),
            ('TOPPADDING', (0, 0), (-1, -1), 12),
            ('GRID', (0, 0), (-1, -1), 1, colors.HexColor('#dee2e6')),
            ('FONTNAME', (0, -1), (-1, -1), 'Helvetica-Bold'),
            ('BACKGROUND', (0, -1), (-1, -1), colors.HexColor('#f8f9fa')),
        ]))
        elements.append(items_table)
        
        # Build PDF
        doc.build(elements)
        buffer.seek(0)
        
        return buffer
    
    @staticmethod
    def get_pending_invoices():
        """Get all pending (unpaid) invoices."""
        return Invoice.objects.filter(
            status__in=['ISSUED', 'PARTIALLY_PAID', 'OVERDUE']
        ).select_related('bill__order').order_by('due_date')
    
    @staticmethod
    def get_overdue_invoices():
        """Get all overdue invoices."""
        import datetime
        today = datetime.date.today()
        return Invoice.objects.filter(
            status__in=['ISSUED', 'PARTIALLY_PAID'],
            due_date__lt=today
        ).select_related('bill__order').order_by('due_date')
