"""
Feedback App - Models

Customer feedback and ratings after order completion.
Maps to: feedback_feedback table
"""

from django.db import models
from django.conf import settings
from django.core.validators import MinValueValidator, MaxValueValidator


class Feedback(models.Model):
    """
    Customer feedback and ratings.
    
    Maps to: feedback_feedback table
    
    Only allowed after order completion.
    """
    
    order = models.OneToOneField(
        'orders.Order',
        on_delete=models.CASCADE,
        related_name='feedback'
    )
    customer = models.ForeignKey(
        'customers.CustomerProfile',
        on_delete=models.CASCADE,
        related_name='feedbacks'
    )
    
    # Overall rating (1-5)
    rating = models.PositiveSmallIntegerField(
        validators=[MinValueValidator(1), MaxValueValidator(5)]
    )
    comment_text = models.TextField(blank=True, null=True)
    
    # Category ratings (optional, 1-5)
    tailor_skill_rating = models.PositiveSmallIntegerField(
        null=True,
        blank=True,
        validators=[MinValueValidator(1), MaxValueValidator(5)]
    )
    punctuality_rating = models.PositiveSmallIntegerField(
        null=True,
        blank=True,
        validators=[MinValueValidator(1), MaxValueValidator(5)]
    )
    service_rating = models.PositiveSmallIntegerField(
        null=True,
        blank=True,
        validators=[MinValueValidator(1), MaxValueValidator(5)]
    )
    
    # Verification & Moderation
    is_verified_purchase = models.BooleanField(default=True)
    is_moderated = models.BooleanField(default=False)
    is_approved = models.BooleanField(default=True)
    
    moderated_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='moderated_feedbacks'
    )
    moderation_notes = models.TextField(blank=True, null=True)
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        db_table = 'feedback_feedback'
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['order'], name='idx_feedback_order'),
            models.Index(fields=['customer'], name='idx_feedback_customer'),
            models.Index(fields=['rating'], name='idx_feedback_rating'),
            models.Index(fields=['created_at'], name='idx_feedback_created'),
        ]
    
    def __str__(self):
        return f"Feedback for {self.order.order_number}: {self.rating}/5"
