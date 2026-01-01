"""
Catalog Template Tags

Custom template tags for catalog module.
"""

from django import template
from catalog.models import WorkType, GarmentWorkType

register = template.Library()


@register.simple_tag
def get_available_work_types(garment):
    """
    Get work types not yet enabled for a garment.
    
    Usage: {% get_available_work_types garment as available_work_types %}
    """
    enabled_ids = GarmentWorkType.objects.filter(
        garment_type=garment,
        is_supported=True
    ).values_list('work_type_id', flat=True)
    
    return WorkType.objects.filter(
        is_deleted=False
    ).exclude(
        id__in=enabled_ids
    ).order_by('name')
