"""
Core App - Tests

Test cases for validators and sanitizers.
"""

import io
from django.test import TestCase
from django.core.exceptions import ValidationError
from django.core.files.uploadedfile import SimpleUploadedFile

from .validators import (
    SecureFileValidator,
    SecureImageValidator,
    SecureDesignValidator,
    FileValidationError,
    validate_image_file,
    validate_design_file,
)
from .sanitizers import (
    sanitize_html,
    strip_all_html,
    sanitize_text,
    sanitize_filename,
    SanitizedCharField,
    SanitizedTextField,
    SafeHTMLField,
)


class SecureFileValidatorTests(TestCase):
    """Test cases for file validators."""
    
    def test_file_size_validation_passes(self):
        """Test that files within size limit pass validation."""
        validator = SecureFileValidator(max_size_mb=1)
        # Create a small file (100 bytes)
        file = SimpleUploadedFile(
            "test.jpg",
            b'\xff\xd8\xff' + b'0' * 100,  # JPEG header + content
            content_type="image/jpeg"
        )
        # Should not raise
        validator.validate_file_size(file)
    
    def test_file_size_validation_fails_for_large_files(self):
        """Test that files exceeding size limit fail validation."""
        validator = SecureFileValidator(max_size_mb=0.001)  # ~1KB limit
        # Create a file larger than limit
        file = SimpleUploadedFile(
            "large.jpg",
            b'\xff\xd8\xff' + b'0' * 10000,
            content_type="image/jpeg"
        )
        with self.assertRaises(FileValidationError) as context:
            validator.validate_file_size(file)
        self.assertIn('exceeds', str(context.exception))
    
    def test_extension_validation_passes(self):
        """Test that allowed extensions pass validation."""
        validator = SecureFileValidator(allowed_extensions=['jpg', 'png'])
        file = SimpleUploadedFile("test.jpg", b'content', content_type="image/jpeg")
        # Should not raise
        validator.validate_extension(file)
    
    def test_extension_validation_fails_for_disallowed(self):
        """Test that disallowed extensions fail validation."""
        validator = SecureFileValidator(allowed_extensions=['jpg', 'png'])
        file = SimpleUploadedFile("test.exe", b'content', content_type="application/x-msdownload")
        with self.assertRaises(FileValidationError) as context:
            validator.validate_extension(file)
        self.assertIn('not allowed', str(context.exception))
    
    def test_extension_case_insensitive(self):
        """Test that extension validation is case-insensitive."""
        validator = SecureFileValidator(allowed_extensions=['jpg', 'png'])
        file = SimpleUploadedFile("test.JPG", b'content', content_type="image/jpeg")
        # Should not raise
        validator.validate_extension(file)


class SecureImageValidatorTests(TestCase):
    """Test cases specifically for image validation."""
    
    def test_valid_jpeg_passes(self):
        """Test that valid JPEG files pass."""
        validator = SecureImageValidator()
        # JPEG magic bytes
        jpeg_data = b'\xff\xd8\xff\xe0\x00\x10JFIF' + b'\x00' * 100
        file = SimpleUploadedFile("photo.jpg", jpeg_data, content_type="image/jpeg")
        # Should not raise
        try:
            validator(file)
        except FileValidationError:
            self.fail("Valid JPEG should pass validation")
    
    def test_valid_png_passes(self):
        """Test that valid PNG files pass."""
        validator = SecureImageValidator()
        # PNG magic bytes
        png_data = b'\x89PNG\r\n\x1a\n' + b'\x00' * 100
        file = SimpleUploadedFile("image.png", png_data, content_type="image/png")
        # Should not raise
        try:
            validator(file)
        except FileValidationError:
            self.fail("Valid PNG should pass validation")


class SecureDesignValidatorTests(TestCase):
    """Test cases for design file validation."""
    
    def test_pdf_passes(self):
        """Test that PDF files pass design validation."""
        validator = SecureDesignValidator()
        # PDF magic bytes
        pdf_data = b'%PDF-1.4' + b'\x00' * 100
        file = SimpleUploadedFile("design.pdf", pdf_data, content_type="application/pdf")
        # Should not raise
        try:
            validator(file)
        except FileValidationError:
            self.fail("Valid PDF should pass validation")


class SanitizeHTMLTests(TestCase):
    """Test cases for HTML sanitization."""
    
    def test_removes_script_tags(self):
        """Test that script tags are removed."""
        input_html = '<script>alert("xss")</script>Hello'
        result = sanitize_html(input_html)
        self.assertNotIn('<script>', result)
        self.assertNotIn('alert', result)
        self.assertIn('Hello', result)
    
    def test_removes_onclick_attributes(self):
        """Test that onclick and event handlers are removed."""
        input_html = '<div onclick="evil()">Click me</div>'
        result = sanitize_html(input_html)
        self.assertNotIn('onclick', result)
        self.assertIn('Click me', result)
    
    def test_keeps_safe_tags(self):
        """Test that safe formatting tags are kept."""
        input_html = '<strong>Bold</strong> and <em>italic</em>'
        result = sanitize_html(input_html)
        self.assertIn('<strong>Bold</strong>', result)
        self.assertIn('<em>italic</em>', result)
    
    def test_removes_iframe(self):
        """Test that iframes are removed."""
        input_html = '<iframe src="evil.com"></iframe>Content'
        result = sanitize_html(input_html)
        self.assertNotIn('iframe', result)
        self.assertIn('Content', result)
    
    def test_handles_none(self):
        """Test that None input returns None."""
        result = sanitize_html(None)
        self.assertIsNone(result)
    
    def test_handles_empty_string(self):
        """Test that empty string returns empty string."""
        result = sanitize_html('')
        self.assertEqual(result, '')


class StripAllHTMLTests(TestCase):
    """Test cases for stripping all HTML."""
    
    def test_strips_all_tags(self):
        """Test that all HTML tags are stripped."""
        input_html = '<div><strong>Hello</strong> <em>World</em></div>'
        result = strip_all_html(input_html)
        self.assertEqual(result.strip(), 'Hello World')
    
    def test_strips_script_content(self):
        """Test that script content is removed."""
        input_html = '<script>var x = 1;</script>Safe text'
        result = strip_all_html(input_html)
        self.assertNotIn('var x', result)
        self.assertIn('Safe text', result)


class SanitizeTextTests(TestCase):
    """Test cases for text sanitization."""
    
    def test_removes_null_bytes(self):
        """Test that null bytes are removed."""
        input_text = 'Hello\x00World'
        result = sanitize_text(input_text)
        self.assertEqual(result, 'HelloWorld')
    
    def test_removes_control_characters(self):
        """Test that control characters are removed."""
        input_text = 'Hello\x07World'  # Bell character
        result = sanitize_text(input_text)
        self.assertEqual(result, 'HelloWorld')
    
    def test_preserves_newlines(self):
        """Test that newlines are preserved."""
        input_text = 'Line1\nLine2'
        result = sanitize_text(input_text)
        self.assertIn('\n', result)
    
    def test_normalizes_whitespace(self):
        """Test that excessive whitespace is normalized."""
        input_text = 'Hello    World'
        result = sanitize_text(input_text)
        self.assertEqual(result, 'Hello World')


class SanitizeFilenameTests(TestCase):
    """Test cases for filename sanitization."""
    
    def test_removes_path_traversal(self):
        """Test that path traversal attempts are blocked."""
        result = sanitize_filename('../../../etc/passwd')
        self.assertNotIn('..', result)
        self.assertNotIn('/', result)
    
    def test_removes_null_bytes(self):
        """Test that null bytes are removed from filenames."""
        result = sanitize_filename('file\x00name.txt')
        self.assertNotIn('\x00', result)
    
    def test_removes_special_characters(self):
        """Test that unsafe characters are removed."""
        result = sanitize_filename('file<>:"|?*.txt')
        self.assertNotIn('<', result)
        self.assertNotIn('>', result)
        self.assertNotIn('|', result)
    
    def test_handles_empty_string(self):
        """Test that empty filename returns 'unnamed'."""
        result = sanitize_filename('')
        self.assertEqual(result, 'unnamed')
    
    def test_handles_none(self):
        """Test that None returns 'unnamed'."""
        result = sanitize_filename(None)
        self.assertEqual(result, 'unnamed')


class SanitizedFieldTests(TestCase):
    """Test cases for sanitized form fields."""
    
    def test_sanitized_char_field_strips_html(self):
        """Test that SanitizedCharField strips HTML."""
        field = SanitizedCharField()
        result = field.clean('<script>alert("xss")</script>Hello')
        self.assertNotIn('<script>', result)
        self.assertIn('Hello', result)
    
    def test_sanitized_text_field_preserves_newlines(self):
        """Test that SanitizedTextField preserves newlines."""
        field = SanitizedTextField()
        result = field.clean('Line1\nLine2')
        self.assertIn('\n', result)
    
    def test_safe_html_field_keeps_formatting(self):
        """Test that SafeHTMLField keeps safe formatting."""
        field = SafeHTMLField()
        result = field.clean('<strong>Bold</strong>')
        self.assertIn('<strong>', result)
