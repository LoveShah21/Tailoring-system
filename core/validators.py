"""
Core App - File Validators

Secure file upload validation with MIME type detection.
Uses python-magic for magic byte verification when available.
"""

import os
from django.conf import settings
from django.core.exceptions import ValidationError
from django.utils.deconstruct import deconstructible

# Try to import magic, but make it optional
try:
    import magic
    HAS_MAGIC = True
except (ImportError, OSError):
    HAS_MAGIC = False


# Magic byte signatures for common file types
MAGIC_BYTES = {
    # Images
    'image/jpeg': b'\xff\xd8\xff',
    'image/png': b'\x89PNG\r\n\x1a\n',
    'image/gif': b'GIF8',
    'image/webp': b'RIFF',
    # Documents
    'application/pdf': b'%PDF',
}

# Allowed MIME types mapping
ALLOWED_MIME_TYPES = {
    'image': [
        'image/jpeg',
        'image/png',
        'image/gif',
        'image/webp',
    ],
    'document': [
        'application/pdf',
        'image/jpeg',
        'image/png',
    ],
    'design': [
        'application/pdf',
        'image/jpeg',
        'image/png',
    ],
}


class FileValidationError(ValidationError):
    """Custom exception for file validation errors."""
    pass


@deconstructible
class SecureFileValidator:
    """
    Validates file uploads for security.
    
    Checks:
    1. File size within limits
    2. File extension in allowed list
    3. MIME type matches extension
    4. Magic bytes verify actual file content
    """
    
    def __init__(
        self,
        allowed_extensions=None,
        max_size_mb=5,
        file_type='image'
    ):
        """
        Initialize validator.
        
        Args:
            allowed_extensions: List of allowed extensions (without dot)
            max_size_mb: Maximum file size in MB
            file_type: 'image', 'document', or 'design'
        """
        self.allowed_extensions = allowed_extensions or getattr(
            settings, 'ALLOWED_IMAGE_EXTENSIONS', ['jpg', 'jpeg', 'png', 'gif', 'webp']
        )
        self.max_size_mb = max_size_mb
        self.max_size_bytes = max_size_mb * 1024 * 1024
        self.file_type = file_type
        self.allowed_mime_types = ALLOWED_MIME_TYPES.get(file_type, ALLOWED_MIME_TYPES['image'])
    
    def __call__(self, file):
        """Validate the uploaded file."""
        self.validate_file_size(file)
        self.validate_extension(file)
        self.validate_mime_type(file)
        return file
    
    def validate_file_size(self, file):
        """Check file size is within limits."""
        if file.size > self.max_size_bytes:
            raise FileValidationError(
                f'File size ({file.size / (1024*1024):.2f} MB) exceeds '
                f'maximum allowed size ({self.max_size_mb} MB).'
            )
    
    def validate_extension(self, file):
        """Check file extension is allowed."""
        name = getattr(file, 'name', '')
        if not name:
            raise FileValidationError('File must have a name.')
        
        ext = os.path.splitext(name)[1].lower().lstrip('.')
        
        if ext not in self.allowed_extensions:
            raise FileValidationError(
                f'File type ".{ext}" is not allowed. '
                f'Allowed types: {", ".join(self.allowed_extensions)}'
            )
    
    def validate_mime_type(self, file):
        """Verify MIME type using python-magic."""
        # Skip if magic is not available
        if not HAS_MAGIC:
            return
        
        # Read start of file for magic bytes
        file.seek(0)
        header = file.read(8192)
        file.seek(0)  # Reset file pointer
        
        try:
            mime = magic.from_buffer(header, mime=True)
        except Exception:
            # Fallback if magic fails
            mime = None
        
        if mime and mime not in self.allowed_mime_types:
            raise FileValidationError(
                f'File content type "{mime}" is not allowed. '
                f'This may indicate the file has been modified or renamed.'
            )
        
        # Additional check: verify magic bytes match expected
        self._verify_magic_bytes(header, mime)
    
    def _verify_magic_bytes(self, header, mime):
        """Verify magic bytes match the claimed MIME type."""
        if not mime:
            return
        
        expected_bytes = MAGIC_BYTES.get(mime)
        if expected_bytes:
            if not header.startswith(expected_bytes):
                raise FileValidationError(
                    'File content does not match its extension. '
                    'The file may have been renamed or corrupted.'
                )


@deconstructible
class SecureImageValidator(SecureFileValidator):
    """Validator specifically for image uploads."""
    
    def __init__(self, max_size_mb=5):
        super().__init__(
            allowed_extensions=getattr(
                settings, 'ALLOWED_IMAGE_EXTENSIONS',
                ['jpg', 'jpeg', 'png', 'gif', 'webp']
            ),
            max_size_mb=max_size_mb,
            file_type='image'
        )


@deconstructible
class SecureDesignValidator(SecureFileValidator):
    """Validator specifically for design file uploads."""
    
    def __init__(self, max_size_mb=10):
        super().__init__(
            allowed_extensions=getattr(
                settings, 'ALLOWED_DESIGN_EXTENSIONS',
                ['pdf', 'jpg', 'jpeg', 'png']
            ),
            max_size_mb=max_size_mb,
            file_type='design'
        )


def validate_image_file(file, max_size_mb=5):
    """
    Convenience function to validate an image file.
    
    Args:
        file: Uploaded file object
        max_size_mb: Maximum file size in MB
    
    Returns:
        Validated file object
    
    Raises:
        FileValidationError: If validation fails
    """
    validator = SecureImageValidator(max_size_mb=max_size_mb)
    return validator(file)


def validate_design_file(file, max_size_mb=10):
    """
    Convenience function to validate a design file.
    
    Args:
        file: Uploaded file object
        max_size_mb: Maximum file size in MB
    
    Returns:
        Validated file object
    
    Raises:
        FileValidationError: If validation fails
    """
    validator = SecureDesignValidator(max_size_mb=max_size_mb)
    return validator(file)
