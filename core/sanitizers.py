"""
Core App - Input Sanitizers

HTML and text sanitization utilities for security.
Uses bleach for safe HTML sanitization.
"""

import re
import bleach
from django import forms
from django.utils.html import strip_tags


# Allowed HTML tags for user content (minimal safe set)
ALLOWED_TAGS = [
    'b', 'i', 'u', 'strong', 'em',
    'p', 'br',
    'ul', 'ol', 'li',
]

# Allowed HTML attributes (minimal safe set)
ALLOWED_ATTRIBUTES = {
    '*': [],  # No attributes allowed by default
}


def sanitize_html(text, allowed_tags=None, allowed_attributes=None):
    """
    Sanitize HTML content, keeping only safe tags.
    
    Args:
        text: Input text that may contain HTML
        allowed_tags: List of allowed HTML tags (default: minimal safe set)
        allowed_attributes: Dict of allowed attributes per tag
    
    Returns:
        Sanitized text with dangerous HTML removed
    """
    if not text:
        return text
    
    # First remove script and style tag contents entirely
    text = re.sub(r'<script[^>]*>.*?</script>', '', text, flags=re.IGNORECASE | re.DOTALL)
    text = re.sub(r'<style[^>]*>.*?</style>', '', text, flags=re.IGNORECASE | re.DOTALL)
    
    tags = allowed_tags if allowed_tags is not None else ALLOWED_TAGS
    attrs = allowed_attributes if allowed_attributes is not None else ALLOWED_ATTRIBUTES
    
    return bleach.clean(
        text,
        tags=tags,
        attributes=attrs,
        strip=True
    )


def strip_all_html(text):
    """
    Strip ALL HTML tags from text.
    
    Args:
        text: Input text that may contain HTML
    
    Returns:
        Plain text with all HTML removed
    """
    if not text:
        return text
    
    # First remove script and style tag contents entirely
    text = re.sub(r'<script[^>]*>.*?</script>', '', text, flags=re.IGNORECASE | re.DOTALL)
    text = re.sub(r'<style[^>]*>.*?</style>', '', text, flags=re.IGNORECASE | re.DOTALL)
    
    # Use bleach to clean remaining tags
    cleaned = bleach.clean(text, tags=[], strip=True)
    # Additional safety: use Django's strip_tags as backup
    return strip_tags(cleaned)


def sanitize_text(text):
    """
    Sanitize plain text input.
    
    Removes:
    - All HTML tags
    - Script injection attempts
    - Null bytes and control characters
    
    Args:
        text: Input text
    
    Returns:
        Sanitized plain text
    """
    if not text:
        return text
    
    # Remove null bytes first
    text = text.replace('\x00', '')
    
    # Remove control characters (except newlines and tabs) BEFORE HTML stripping
    text = re.sub(r'[\x00-\x08\x0b\x0c\x0e-\x1f\x7f]', '', text)
    
    # Strip HTML
    text = strip_all_html(text)
    
    # Normalize whitespace (but preserve newlines)
    text = re.sub(r'[^\S\n]+', ' ', text)
    
    return text.strip()


def sanitize_filename(filename):
    """
    Sanitize a filename for safe storage.
    
    Args:
        filename: Original filename
    
    Returns:
        Sanitized filename safe for storage
    """
    if not filename:
        return 'unnamed'
    
    # Remove path traversal attempts
    filename = filename.replace('..', '')
    filename = filename.replace('/', '')
    filename = filename.replace('\\', '')
    
    # Remove null bytes
    filename = filename.replace('\x00', '')
    
    # Keep only safe characters
    safe_chars = re.sub(r'[^\w\s\-\.]', '', filename)
    
    # Remove leading/trailing dots and spaces
    safe_chars = safe_chars.strip('. ')
    
    return safe_chars or 'unnamed'


class SanitizedCharField(forms.CharField):
    """
    CharField that automatically sanitizes input.
    
    Strips all HTML and dangerous characters.
    """
    
    def clean(self, value):
        value = super().clean(value)
        if value:
            value = sanitize_text(value)
        return value


class SanitizedTextField(forms.CharField):
    """
    TextField (multiline) that automatically sanitizes input.
    
    Strips all HTML and dangerous characters while preserving newlines.
    """
    
    widget = forms.Textarea
    
    def clean(self, value):
        value = super().clean(value)
        if value:
            value = sanitize_text(value)
        return value


class SafeHTMLField(forms.CharField):
    """
    TextField that allows limited safe HTML formatting.
    
    Keeps only basic formatting tags like <b>, <i>, <p>, <br>.
    """
    
    widget = forms.Textarea
    
    def clean(self, value):
        value = super().clean(value)
        if value:
            value = sanitize_html(value)
        return value


class SanitizedFormMixin:
    """
    Mixin for forms to auto-sanitize text fields.
    
    Usage:
        class MyForm(SanitizedFormMixin, forms.Form):
            sanitize_fields = ['description', 'notes']
    """
    
    sanitize_fields = []  # Override in subclass
    
    def clean(self):
        cleaned_data = super().clean()
        
        for field_name in self.sanitize_fields:
            if field_name in cleaned_data and cleaned_data[field_name]:
                cleaned_data[field_name] = sanitize_text(cleaned_data[field_name])
        
        return cleaned_data
