"""
Catalog App - Models

Garment types, work types, and product images.
Maps to: catalog_garment_type, catalog_work_type, 
         catalog_garment_work_type, catalog_product_image tables
"""

from django.db import models
from django.core.validators import MinValueValidator
import os


def product_image_path(instance, filename):
    """Generate upload path for product images."""
    ext = filename.split('.')[-1]
    return f'catalog/garments/{instance.garment_type.id}/{filename}'


class GarmentType(models.Model):
    """
    Types of garments available.
    
    Maps to: catalog_garment_type table
    
    Examples: Blouse, Kurti, Saree, Suit, Lehenga
    """
    
    name = models.CharField(max_length=100, unique=True)
    description = models.TextField(blank=True, null=True)
    base_price = models.DecimalField(
        max_digits=10, 
        decimal_places=2,
        validators=[MinValueValidator(0)]
    )
    fabric_requirement_meters = models.DecimalField(
        max_digits=5,
        decimal_places=2,
        validators=[MinValueValidator(0)]
    )
    stitching_days_estimate = models.PositiveIntegerField(default=7)
    
    is_active = models.BooleanField(default=True)
    is_deleted = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        db_table = 'catalog_garment_type'
        indexes = [
            models.Index(fields=['is_active'], name='idx_garment_is_active'),
            models.Index(fields=['base_price'], name='idx_garment_base_price'),
        ]
    
    def __str__(self):
        return self.name
    
    def get_cover_image(self):
        """Get the cover image for this garment type."""
        return self.images.filter(is_cover_image=True).first()
    
    def get_supported_work_types(self):
        """Get all supported work types for this garment."""
        return WorkType.objects.filter(
            garment_work_types__garment_type=self,
            garment_work_types__is_supported=True,
            is_deleted=False
        )


class WorkType(models.Model):
    """
    Types of embellishment/work.
    
    Maps to: catalog_work_type table
    
    Examples: Mirror, Jardoshi, Handwork, Embroidery
    """
    
    name = models.CharField(max_length=100, unique=True)
    description = models.TextField(blank=True, null=True)
    extra_charge = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        default=0.00,
        validators=[MinValueValidator(0)]
    )
    labor_hours_estimate = models.PositiveIntegerField(default=8)
    
    is_deleted = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        db_table = 'catalog_work_type'
        indexes = [
            models.Index(fields=['name'], name='idx_work_type_name'),
        ]
    
    def __str__(self):
        return f"{self.name} (+₹{self.extra_charge})"


class GarmentWorkType(models.Model):
    """
    Mapping of which work types are supported for which garments.
    
    Maps to: catalog_garment_work_type table
    """
    
    garment_type = models.ForeignKey(
        GarmentType,
        on_delete=models.CASCADE,
        related_name='garment_work_types'
    )
    work_type = models.ForeignKey(
        WorkType,
        on_delete=models.CASCADE,
        related_name='garment_work_types'
    )
    is_supported = models.BooleanField(default=True)
    
    class Meta:
        db_table = 'catalog_garment_work_type'
        unique_together = ('garment_type', 'work_type')
        indexes = [
            models.Index(fields=['garment_type'], name='idx_gwt_garment'),
        ]
    
    def __str__(self):
        return f"{self.garment_type.name} - {self.work_type.name}"


class ProductImage(models.Model):
    """
    Images for garment types.
    
    Maps to: catalog_product_image table
    """
    
    garment_type = models.ForeignKey(
        GarmentType,
        on_delete=models.CASCADE,
        related_name='images'
    )
    image_url = models.CharField(max_length=500)  # Can be URL or file path
    image_filename = models.CharField(max_length=255)
    file_size_kb = models.PositiveIntegerField(null=True, blank=True)
    
    is_cover_image = models.BooleanField(default=False)
    display_order = models.PositiveIntegerField(default=0)
    
    uploaded_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        db_table = 'catalog_product_image'
        ordering = ['display_order', '-uploaded_at']
        indexes = [
            models.Index(fields=['garment_type'], name='idx_prod_img_garment'),
            models.Index(fields=['is_cover_image'], name='idx_prod_img_cover'),
        ]
    
    def __str__(self):
        return f"{self.garment_type.name} - {self.image_filename}"
    
    def save(self, *args, **kwargs):
        # Ensure only one cover image per garment type
        if self.is_cover_image:
            ProductImage.objects.filter(
                garment_type=self.garment_type,
                is_cover_image=True
            ).exclude(pk=self.pk).update(is_cover_image=False)
        super().save(*args, **kwargs)
