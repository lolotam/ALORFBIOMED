"""
File upload utilities for secure file handling.
"""
import os
import uuid
import mimetypes
from pathlib import Path
from typing import Optional, Tuple, List
from werkzeug.utils import secure_filename
from werkzeug.datastructures import FileStorage
import logging

logger = logging.getLogger(__name__)

# Allowed file extensions and their MIME types
ALLOWED_EXTENSIONS = {
    # Images
    'jpg': ['image/jpeg'],
    'jpeg': ['image/jpeg'],
    'png': ['image/png'],
    'gif': ['image/gif'],
    'webp': ['image/webp'],
    # Documents
    'pdf': ['application/pdf'],
    'doc': ['application/msword'],
    'docx': ['application/vnd.openxmlformats-officedocument.wordprocessingml.document'],
    'txt': ['text/plain'],
    'rtf': ['application/rtf', 'text/rtf']
}

# Maximum file size (10MB)
MAX_FILE_SIZE = 10 * 1024 * 1024

# Upload directories
UPLOAD_DIRS = {
    'history': 'app/static/uploads/history',
    'profiles': 'app/static/uploads/profiles'
}


def ensure_upload_directories():
    """Ensure all upload directories exist."""
    for dir_type, dir_path in UPLOAD_DIRS.items():
        try:
            os.makedirs(dir_path, exist_ok=True)
            logger.info(f"Ensured upload directory exists: {dir_path}")
        except Exception as e:
            logger.error(f"Failed to create upload directory {dir_path}: {e}")
            raise


def is_allowed_file(filename: str, file_type: str = 'all') -> bool:
    """
    Check if a file extension is allowed.
    
    Args:
        filename: Name of the file
        file_type: Type of file ('image', 'document', or 'all')
    
    Returns:
        bool: True if file is allowed, False otherwise
    """
    if not filename or '.' not in filename:
        return False
    
    extension = filename.rsplit('.', 1)[1].lower()
    
    if file_type == 'image':
        image_extensions = ['jpg', 'jpeg', 'png', 'gif', 'webp']
        return extension in image_extensions
    elif file_type == 'document':
        document_extensions = ['pdf', 'doc', 'docx', 'txt', 'rtf']
        return extension in document_extensions
    else:  # 'all'
        return extension in ALLOWED_EXTENSIONS


def validate_file(file: FileStorage, file_type: str = 'all') -> Tuple[bool, str]:
    """
    Validate an uploaded file.
    
    Args:
        file: The uploaded file
        file_type: Type of file ('image', 'document', or 'all')
    
    Returns:
        Tuple[bool, str]: (is_valid, error_message)
    """
    if not file or not file.filename:
        return False, "No file selected"
    
    # Check file extension
    if not is_allowed_file(file.filename, file_type):
        allowed_exts = list(ALLOWED_EXTENSIONS.keys())
        if file_type == 'image':
            allowed_exts = ['jpg', 'jpeg', 'png', 'gif', 'webp']
        elif file_type == 'document':
            allowed_exts = ['pdf', 'doc', 'docx', 'txt', 'rtf']
        return False, f"File type not allowed. Allowed types: {', '.join(allowed_exts)}"
    
    # Check file size
    file.seek(0, os.SEEK_END)
    file_size = file.tell()
    file.seek(0)  # Reset file pointer
    
    if file_size > MAX_FILE_SIZE:
        return False, f"File size too large. Maximum size: {MAX_FILE_SIZE // (1024*1024)}MB"
    
    if file_size == 0:
        return False, "File is empty"
    
    # Validate MIME type
    extension = file.filename.rsplit('.', 1)[1].lower()
    allowed_mimes = ALLOWED_EXTENSIONS.get(extension, [])
    
    if file.mimetype and file.mimetype not in allowed_mimes:
        return False, f"Invalid file type. Expected: {', '.join(allowed_mimes)}"
    
    return True, ""


def generate_secure_filename(original_filename: str) -> str:
    """
    Generate a secure filename with UUID prefix.
    
    Args:
        original_filename: Original filename
    
    Returns:
        str: Secure filename with UUID prefix
    """
    if not original_filename:
        return str(uuid.uuid4())
    
    # Get file extension
    extension = ""
    if '.' in original_filename:
        extension = '.' + original_filename.rsplit('.', 1)[1].lower()
    
    # Generate UUID-based filename
    secure_name = str(uuid.uuid4()) + extension
    return secure_name


def save_uploaded_file(file: FileStorage, upload_type: str, file_type: str = 'all') -> Tuple[bool, str, dict]:
    """
    Save an uploaded file securely.
    
    Args:
        file: The uploaded file
        upload_type: Type of upload ('history' or 'profiles')
        file_type: Type of file ('image', 'document', or 'all')
    
    Returns:
        Tuple[bool, str, dict]: (success, error_message, file_info)
    """
    try:
        # Validate file
        is_valid, error_msg = validate_file(file, file_type)
        if not is_valid:
            return False, error_msg, {}
        
        # Ensure upload directory exists
        if upload_type not in UPLOAD_DIRS:
            return False, f"Invalid upload type: {upload_type}", {}
        
        upload_dir = UPLOAD_DIRS[upload_type]
        os.makedirs(upload_dir, exist_ok=True)
        
        # Generate secure filename
        original_filename = secure_filename(file.filename)
        stored_filename = generate_secure_filename(original_filename)
        
        # Save file
        file_path = os.path.join(upload_dir, stored_filename)
        file.save(file_path)
        
        # Get file info
        file_size = os.path.getsize(file_path)
        mime_type = mimetypes.guess_type(file_path)[0] or file.mimetype or 'application/octet-stream'
        
        file_info = {
            'original_filename': original_filename,
            'stored_filename': stored_filename,
            'file_path': file_path,
            'relative_path': f"/static/uploads/{upload_type}/{stored_filename}",
            'file_size': file_size,
            'mime_type': mime_type
        }
        
        logger.info(f"File saved successfully: {file_path}")
        return True, "", file_info
        
    except Exception as e:
        logger.error(f"Error saving file: {e}")
        return False, f"Failed to save file: {str(e)}", {}


def delete_file(file_path: str) -> bool:
    """
    Delete a file safely.
    
    Args:
        file_path: Path to the file to delete
    
    Returns:
        bool: True if deleted successfully, False otherwise
    """
    try:
        if os.path.exists(file_path):
            os.remove(file_path)
            logger.info(f"File deleted successfully: {file_path}")
            return True
        else:
            logger.warning(f"File not found for deletion: {file_path}")
            return False
    except Exception as e:
        logger.error(f"Error deleting file {file_path}: {e}")
        return False


def get_file_url(upload_type: str, filename: str) -> str:
    """
    Get the URL for an uploaded file.
    
    Args:
        upload_type: Type of upload ('history' or 'profiles')
        filename: Name of the file
    
    Returns:
        str: URL to access the file
    """
    return f"/static/uploads/{upload_type}/{filename}"


def cleanup_orphaned_files(upload_type: str, active_filenames: List[str]) -> int:
    """
    Clean up orphaned files that are no longer referenced.
    
    Args:
        upload_type: Type of upload ('history' or 'profiles')
        active_filenames: List of filenames that are still in use
    
    Returns:
        int: Number of files deleted
    """
    try:
        if upload_type not in UPLOAD_DIRS:
            return 0
        
        upload_dir = UPLOAD_DIRS[upload_type]
        if not os.path.exists(upload_dir):
            return 0
        
        deleted_count = 0
        for filename in os.listdir(upload_dir):
            if filename not in active_filenames:
                file_path = os.path.join(upload_dir, filename)
                if delete_file(file_path):
                    deleted_count += 1
        
        logger.info(f"Cleaned up {deleted_count} orphaned files from {upload_dir}")
        return deleted_count
        
    except Exception as e:
        logger.error(f"Error cleaning up orphaned files: {e}")
        return 0
