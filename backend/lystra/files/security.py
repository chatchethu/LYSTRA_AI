
import magic
import structlog
from typing import Tuple, Optional

logger = structlog.get_logger(__name__)

# Size limit constants
MAX_FILE_SIZE = 50 * 1024 * 1024  # 50 MB

# Allowlist mapping magic-detected MIME types to our supported categories
ALLOWED_MIMES = {
    "application/pdf": "pdf",
    "application/vnd.openxmlformats-officedocument.wordprocessingml.document": "docx",
    "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet": "xlsx",
    "application/vnd.openxmlformats-officedocument.presentationml.presentation": "pptx",
    "text/csv": "csv",
    "text/plain": "text",
    "text/markdown": "markdown",
    "application/json": "json",
    "application/xml": "xml",
    "text/xml": "xml",
    "image/jpeg": "image",
    "image/png": "image",
    "image/webp": "image",
}

class FileSecurityValidator:
    @staticmethod
    def validate_file_bytes(file_bytes: bytes, original_filename: str) -> Tuple[bool, Optional[str], Optional[str]]:
        """
        Validates file size, true MIME type (via magic), and checks against allowlist.
        Returns: (is_valid, mapped_type_category, error_message)
        """
        if len(file_bytes) > MAX_FILE_SIZE:
            return False, None, f"File exceeds maximum size of {MAX_FILE_SIZE//1024//1024}MB"
            
        try:
            # python-magic detects true file signature (magic bytes)
            true_mime = magic.from_buffer(file_bytes[:2048], mime=True)
        except Exception as e:
            logger.error("magic_mime_detection_failed", error=str(e))
            return False, None, "Failed to analyze file signature securely."

        logger.info("file_mime_detected", original_name=original_filename, true_mime=true_mime)

        category = ALLOWED_MIMES.get(true_mime)
        if not category:
            # Add strict blocking logging for malicious or unsupported stuff
            if true_mime.startswith("application/x-executable") or "macro" in true_mime.lower():
                logger.warning("executable_or_macro_blocked", mime=true_mime, filename=original_filename)
                return False, None, "Executable code or macro-enabled documents are strictly forbidden."
            return False, None, f"Unsupported file type: {true_mime}"

        return True, category, None

