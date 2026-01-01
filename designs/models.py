"""
Designs App - Models

Design uploads and customization notes.
Maps to: designs_design, designs_customization_note tables
"""

from django.db import models
from django.conf import settings


def design_file_path(instance, filename):
    """Generate upload path for design files."""
    return f'designs/{instance.order_id or "library"}/{filename}'


class Design(models.Model):
    """
    Design files (uploaded or from library).
    
    Maps to: designs_design table
    """
    
    FILE_TYPES = [
        ('pdf', 'PDF'),
        ('jpg', 'JPEG'),
        ('png', 'PNG'),
    ]
    
    order = models.ForeignKey(
        'orders.Order',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='designs'
    )
    name = models.CharField(max_length=255)
    description = models.TextField(blank=True, null=True)
    
    design_file_name = models.CharField(max_length=255, blank=True, null=True)
    design_file_path = models.CharField(max_length=500, blank=True, null=True)
    file_size_kb = models.PositiveIntegerField(null=True, blank=True)
    file_type = models.CharField(max_length=20, choices=FILE_TYPES, blank=True, null=True)
    
    is_approved = models.BooleanField(default=False)
    is_custom = models.BooleanField(default=True)  # False for library designs
    
    uploaded_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.RESTRICT,
        related_name='uploaded_designs'
    )
    uploaded_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        db_table = 'designs_design'
        ordering = ['-uploaded_at']
        indexes = [
            models.Index(fields=['order'], name='idx_design_order'),
            models.Index(fields=['is_approved'], name='idx_design_approved'),
            models.Index(fields=['file_type'], name='idx_design_file_type'),
        ]
    
    def __str__(self):
        return self.name
    
    def approve(self):
        """Approve the design."""
        self.is_approved = True
        self.save(update_fields=['is_approved'])


class CustomizationNote(models.Model):
    """
    Notes attached to designs for customization instructions.
    
    Maps to: designs_customization_note table
    """
    
    design = models.ForeignKey(
        Design,
        on_delete=models.CASCADE,
        related_name='notes'
    )
    note_text = models.TextField()
    noted_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.RESTRICT,
        related_name='design_notes'
    )
    added_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        db_table = 'designs_customization_note'
        ordering = ['-added_at']
        indexes = [
            models.Index(fields=['design'], name='idx_custom_note_design'),
        ]
    
    def __str__(self):
        return f"Note on {self.design.name} by {self.noted_by.username}"
