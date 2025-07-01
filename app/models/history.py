"""
Pydantic models for Equipment History Management.
"""
import logging
from datetime import datetime
from typing import List, Optional, Dict, Any
from pydantic import BaseModel, Field, field_validator
import uuid

logger = logging.getLogger(__name__)


class HistoryAttachment(BaseModel):
    """Model for history note attachments."""
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    note_id: str
    original_filename: str
    stored_filename: str
    file_path: str
    mime_type: str
    file_size: int  # in bytes
    upload_date: str = Field(default_factory=lambda: datetime.now().strftime('%Y-%m-%d %H:%M:%S'))
    
    @field_validator('original_filename', 'stored_filename', 'file_path', 'mime_type')
    @classmethod
    def validate_not_empty(cls, v: str) -> str:
        """Validate required fields are not empty."""
        if not v or not v.strip():
            raise ValueError("Field cannot be empty")
        return v.strip()
    
    @field_validator('file_size')
    @classmethod
    def validate_file_size(cls, v: int) -> int:
        """Validate file size is positive and within limits (10MB)."""
        if v <= 0:
            raise ValueError("File size must be positive")
        if v > 10 * 1024 * 1024:  # 10MB limit
            raise ValueError("File size cannot exceed 10MB")
        return v


class HistoryNote(BaseModel):
    """Model for equipment history notes."""
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    equipment_id: str  # This will be the SERIAL number
    equipment_type: str  # 'ppm' or 'ocm'
    author_id: str  # Username of the person who created the note
    author_name: str  # Display name for the author
    note_text: str
    created_at: str = Field(default_factory=lambda: datetime.now().strftime('%Y-%m-%d %H:%M:%S'))
    updated_at: Optional[str] = None
    last_modified_by: Optional[str] = None  # Username of last person who edited
    last_modified_by_name: Optional[str] = None  # Display name of last editor
    is_edited: bool = False  # Flag to indicate if note has been edited
    attachments: List[HistoryAttachment] = Field(default_factory=list)
    
    @field_validator('equipment_id', 'equipment_type', 'author_id', 'author_name', 'note_text')
    @classmethod
    def validate_not_empty(cls, v: str) -> str:
        """Validate required fields are not empty."""
        if not v or not v.strip():
            raise ValueError("Field cannot be empty")
        return v.strip()
    
    @field_validator('equipment_type')
    @classmethod
    def validate_equipment_type(cls, v: str) -> str:
        """Validate equipment type is valid."""
        v = v.strip().lower()
        if v not in ['ppm', 'ocm']:
            raise ValueError("Equipment type must be 'ppm' or 'ocm'")
        return v
    
    @field_validator('note_text')
    @classmethod
    def validate_note_text(cls, v: str) -> str:
        """Validate note text length."""
        v = v.strip()
        if len(v) < 10:
            raise ValueError("Note text must be at least 10 characters long")
        if len(v) > 5000:
            raise ValueError("Note text cannot exceed 5000 characters")
        return v
    
    def add_attachment(self, attachment: HistoryAttachment) -> None:
        """Add an attachment to this history note."""
        attachment.note_id = self.id
        self.attachments.append(attachment)
        self.updated_at = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
    
    def remove_attachment(self, attachment_id: str) -> bool:
        """Remove an attachment from this history note."""
        for i, attachment in enumerate(self.attachments):
            if attachment.id == attachment_id:
                self.attachments.pop(i)
                self.updated_at = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
                return True
        return False
    
    def get_attachment_by_id(self, attachment_id: str) -> Optional[HistoryAttachment]:
        """Get an attachment by its ID."""
        for attachment in self.attachments:
            if attachment.id == attachment_id:
                return attachment
        return None


class HistoryNoteCreate(BaseModel):
    """Model for creating a new history note (without ID and timestamps)."""
    equipment_id: str
    equipment_type: str
    author_id: str
    author_name: str
    note_text: str


class HistoryNoteUpdate(BaseModel):
    """Model for updating an existing history note."""
    note_text: str
    modified_by: str
    modified_by_name: str

    @field_validator('note_text')
    @classmethod
    def validate_note_text_length(cls, v: str) -> str:
        """Validate note text length and content."""
        if not v or not v.strip():
            raise ValueError("Note text cannot be empty")

        v = v.strip()
        if len(v) < 10:
            raise ValueError("Note text must be at least 10 characters long")
        if len(v) > 5000:
            raise ValueError("Note text cannot exceed 5000 characters")
        return v

    @field_validator('modified_by', 'modified_by_name')
    @classmethod
    def validate_user_fields(cls, v: str) -> str:
        """Validate user-related fields are not empty."""
        if not v or not v.strip():
            raise ValueError("User field cannot be empty")
        return v.strip()


class HistorySearchFilter(BaseModel):
    """Model for history search and filtering."""
    equipment_id: Optional[str] = None
    equipment_type: Optional[str] = None
    author_id: Optional[str] = None
    start_date: Optional[str] = None
    end_date: Optional[str] = None
    search_text: Optional[str] = None
    
    @field_validator('equipment_type')
    @classmethod
    def validate_equipment_type(cls, v: Optional[str]) -> Optional[str]:
        """Validate equipment type is valid."""
        if v is None:
            return v
        v = v.strip().lower()
        if v not in ['ppm', 'ocm', '']:
            raise ValueError("Equipment type must be 'ppm' or 'ocm'")
        return v if v else None
