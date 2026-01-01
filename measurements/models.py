"""
Measurements App - Models

Measurement templates and customer measurements.
Maps to: measurements_measurement_template, measurements_measurement_set,
         measurements_measurement_value tables
"""

from django.db import models
from django.conf import settings


class MeasurementTemplate(models.Model):
    """
    Template defining what measurements are needed per garment type.
    
    Maps to: measurements_measurement_template table
    
    Examples: length, chest, waist, sleeve for different garments
    """
    
    UNIT_CHOICES = [
        ('inches', 'Inches'),
        ('cm', 'Centimeters'),
    ]
    
    garment_type = models.ForeignKey(
        'catalog.GarmentType',
        on_delete=models.CASCADE,
        related_name='measurement_templates'
    )
    measurement_field_name = models.CharField(max_length=100)  # 'length', 'chest', 'waist'
    display_label = models.CharField(max_length=150)  # "Total Length (Inches)"
    unit = models.CharField(max_length=20, choices=UNIT_CHOICES, default='inches')
    default_value = models.DecimalField(
        max_digits=8,
        decimal_places=2,
        null=True,
        blank=True
    )
    is_required = models.BooleanField(default=True)
    description_for_tailor = models.TextField(blank=True, null=True)
    display_order = models.PositiveIntegerField(default=0)
    
    class Meta:
        db_table = 'measurements_measurement_template'
        unique_together = ('garment_type', 'measurement_field_name')
        ordering = ['display_order']
        indexes = [
            models.Index(fields=['garment_type'], name='idx_meas_template_garment'),
        ]
    
    def __str__(self):
        return f"{self.garment_type.name} - {self.display_label}"


class MeasurementSet(models.Model):
    """
    A versioned set of measurements for a customer for a specific garment type.
    
    Maps to: measurements_measurement_set table
    
    Customers can have multiple measurement sets (versioning).
    Only one can be marked as default per garment type.
    """
    
    customer = models.ForeignKey(
        'customers.CustomerProfile',
        on_delete=models.CASCADE,
        related_name='measurement_sets'
    )
    garment_type = models.ForeignKey(
        'catalog.GarmentType',
        on_delete=models.RESTRICT,
        related_name='measurement_sets'
    )
    measurement_date = models.DateField()
    is_default = models.BooleanField(default=False)
    
    taken_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='measurements_taken'
    )
    notes = models.TextField(blank=True, null=True)
    
    is_deleted = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        db_table = 'measurements_measurement_set'
        ordering = ['-measurement_date']
        indexes = [
            models.Index(fields=['customer'], name='idx_meas_set_customer'),
            models.Index(fields=['garment_type'], name='idx_meas_set_garment'),
            models.Index(fields=['is_default'], name='idx_meas_set_default'),
            models.Index(fields=['measurement_date'], name='idx_meas_set_date'),
        ]
    
    def __str__(self):
        return f"{self.customer.user.get_full_name()} - {self.garment_type.name} ({self.measurement_date})"
    
    def save(self, *args, **kwargs):
        # Ensure only one default measurement set per customer per garment type
        if self.is_default:
            MeasurementSet.objects.filter(
                customer=self.customer,
                garment_type=self.garment_type,
                is_default=True
            ).exclude(pk=self.pk).update(is_default=False)
        super().save(*args, **kwargs)
    
    def get_values_dict(self):
        """Get all measurement values as a dictionary."""
        return {
            mv.template.measurement_field_name: mv.value
            for mv in self.measurement_values.all()
        }


class MeasurementValue(models.Model):
    """
    Individual measurement value within a measurement set.
    
    Maps to: measurements_measurement_value table
    """
    
    measurement_set = models.ForeignKey(
        MeasurementSet,
        on_delete=models.CASCADE,
        related_name='measurement_values'
    )
    template = models.ForeignKey(
        MeasurementTemplate,
        on_delete=models.RESTRICT,
        related_name='values'
    )
    value = models.DecimalField(max_digits=8, decimal_places=2)
    
    class Meta:
        db_table = 'measurements_measurement_value'
        unique_together = ('measurement_set', 'template')
        indexes = [
            models.Index(fields=['measurement_set'], name='idx_meas_value_set'),
        ]
    
    def __str__(self):
        return f"{self.template.display_label}: {self.value} {self.template.unit}"
