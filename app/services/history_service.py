"""
Service for managing equipment history notes and attachments.
"""
import json
import os
import logging
from datetime import datetime
from pathlib import Path
from typing import List, Optional, Dict, Any
from werkzeug.datastructures import FileStorage

from app.models.history import HistoryNote, HistoryNoteCreate, HistoryNoteUpdate, HistoryAttachment, HistorySearchFilter
from app.utils.file_utils import save_uploaded_file, delete_file, ensure_upload_directories
from app.services.data_service import DataService

logger = logging.getLogger(__name__)


class HistoryService:
    """Service for managing equipment history."""
    
    HISTORY_DATA_PATH = Path(__file__).parent.parent.parent / 'data' / 'equipment_history.json'
    
    @staticmethod
    def _ensure_history_file_exists():
        """Ensure the history data file exists."""
        try:
            if not os.path.exists(HistoryService.HISTORY_DATA_PATH):
                # Create directory if it doesn't exist
                os.makedirs(os.path.dirname(HistoryService.HISTORY_DATA_PATH), exist_ok=True)
                
                # Create initial empty history file
                HistoryService._save_history_data([])
                logger.info(f"Created history data file at {HistoryService.HISTORY_DATA_PATH}")
        except Exception as e:
            logger.error(f"Error ensuring history file exists: {e}")
    
    @staticmethod
    def _load_history_data() -> List[Dict[str, Any]]:
        """Load history data from JSON file."""
        try:
            HistoryService._ensure_history_file_exists()
            
            with open(HistoryService.HISTORY_DATA_PATH, 'r', encoding='utf-8') as file:
                data = json.load(file)
                logger.debug(f"Loaded {len(data)} history entries")
                return data
        except FileNotFoundError:
            logger.warning(f"History file {HistoryService.HISTORY_DATA_PATH} not found. Returning empty list.")
            return []
        except Exception as e:
            logger.error(f"Error loading history data: {e}")
            return []
    
    @staticmethod
    def _save_history_data(history_data: List[Dict[str, Any]]):
        """Save history data to JSON file."""
        try:
            # Ensure directory exists
            os.makedirs(os.path.dirname(HistoryService.HISTORY_DATA_PATH), exist_ok=True)
            
            with open(HistoryService.HISTORY_DATA_PATH, 'w', encoding='utf-8') as file:
                json.dump(history_data, file, indent=2, ensure_ascii=False)
                logger.debug(f"Saved {len(history_data)} history entries")
        except Exception as e:
            logger.error(f"Error saving history data: {e}")
            raise
    
    @staticmethod
    def create_history_note(note_data: HistoryNoteCreate) -> Optional[HistoryNote]:
        """
        Create a new history note.
        
        Args:
            note_data: Data for creating the history note
        
        Returns:
            HistoryNote: Created history note or None if failed
        """
        try:
            # Create new history note
            history_note = HistoryNote(
                equipment_id=note_data.equipment_id,
                equipment_type=note_data.equipment_type,
                author_id=note_data.author_id,
                author_name=note_data.author_name,
                note_text=note_data.note_text
            )
            
            # Load existing history data
            history_data = HistoryService._load_history_data()
            
            # Add new note
            history_data.append(history_note.model_dump())
            
            # Save updated data
            HistoryService._save_history_data(history_data)
            
            # Update equipment has_history flag
            HistoryService._update_equipment_history_flag(note_data.equipment_id, note_data.equipment_type, True)

            # Log audit event
            from app.services.audit_service import AuditService
            AuditService.log_event(
                event_type=AuditService.EVENT_TYPES['HISTORY_ADDED'],
                performed_by=note_data.author_id,
                description=f"Added history note to {note_data.equipment_type.upper()} equipment {note_data.equipment_id}",
                status=AuditService.STATUS_SUCCESS,
                details={
                    "equipment_id": note_data.equipment_id,
                    "equipment_type": note_data.equipment_type,
                    "note_id": history_note.id,
                    "note_length": len(note_data.note_text)
                }
            )

            logger.info(f"Created history note {history_note.id} for equipment {note_data.equipment_id}")
            return history_note
            
        except Exception as e:
            logger.error(f"Error creating history note: {e}")
            return None
    
    @staticmethod
    def update_history_note(note_id: str, update_data: HistoryNoteUpdate) -> Optional[HistoryNote]:
        """
        Update an existing history note.

        Args:
            note_id: ID of the history note to update
            update_data: Data for updating the history note

        Returns:
            HistoryNote: Updated history note or None if failed
        """
        try:
            # Load existing history data
            history_data = HistoryService._load_history_data()

            # Find and update the note
            for note_data in history_data:
                if note_data.get('id') == note_id:
                    # Update the note content
                    note_data['note_text'] = update_data.note_text
                    note_data['updated_at'] = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
                    note_data['last_modified_by'] = update_data.modified_by
                    note_data['last_modified_by_name'] = update_data.modified_by_name
                    note_data['is_edited'] = True

                    # Save updated data
                    HistoryService._save_history_data(history_data)

                    # Log audit event
                    from app.services.audit_service import AuditService
                    AuditService.log_event(
                        event_type=AuditService.EVENT_TYPES['HISTORY_UPDATED'],
                        performed_by=update_data.modified_by,
                        description=f"Updated history note for {note_data.get('equipment_type', '').upper()} equipment {note_data.get('equipment_id', '')}",
                        status=AuditService.STATUS_SUCCESS,
                        details={
                            "note_id": note_id,
                            "equipment_id": note_data.get('equipment_id'),
                            "equipment_type": note_data.get('equipment_type'),
                            "original_author": note_data.get('author_id'),
                            "modified_by": update_data.modified_by
                        }
                    )

                    # Return updated note
                    updated_note = HistoryNote(**note_data)
                    logger.info(f"Updated history note {note_id}")
                    return updated_note

            logger.warning(f"History note {note_id} not found for update")
            return None

        except Exception as e:
            logger.error(f"Error updating history note {note_id}: {e}")
            return None

    @staticmethod
    def get_history_note(note_id: str) -> Optional[HistoryNote]:
        """
        Get a history note by ID.
        
        Args:
            note_id: ID of the history note
        
        Returns:
            HistoryNote: History note or None if not found
        """
        try:
            history_data = HistoryService._load_history_data()
            
            for note_data in history_data:
                if note_data.get('id') == note_id:
                    return HistoryNote(**note_data)
            
            return None
            
        except Exception as e:
            logger.error(f"Error getting history note {note_id}: {e}")
            return None
    
    @staticmethod
    def get_equipment_history(equipment_id: str, equipment_type: str) -> List[HistoryNote]:
        """
        Get all history notes for a specific equipment.

        Args:
            equipment_id: Equipment ID (SERIAL number, can be URL-safe or original format)
            equipment_type: Equipment type ('ppm' or 'ocm')

        Returns:
            List[HistoryNote]: List of history notes
        """
        try:
            # Convert URL-safe serial back to original format for database lookup
            from app.utils.url_utils import url_safe_to_serial
            original_equipment_id = url_safe_to_serial(equipment_id)

            logger.debug(f"Looking for history notes for equipment_id: '{equipment_id}' (original: '{original_equipment_id}')")

            history_data = HistoryService._load_history_data()

            equipment_history = []
            for note_data in history_data:
                note_equipment_id = note_data.get('equipment_id')
                note_equipment_type = note_data.get('equipment_type')

                # Try both URL-safe and original serial formats
                if ((note_equipment_id == equipment_id or note_equipment_id == original_equipment_id) and
                    note_equipment_type == equipment_type.lower()):
                    equipment_history.append(HistoryNote(**note_data))

            # Sort by created_at descending (newest first)
            equipment_history.sort(key=lambda x: x.created_at, reverse=True)

            logger.debug(f"Found {len(equipment_history)} history notes for equipment {equipment_id}")
            return equipment_history
            
        except Exception as e:
            logger.error(f"Error getting equipment history for {equipment_id}: {e}")
            return []
    
    @staticmethod
    def add_attachment_to_note(note_id: str, file: FileStorage, uploaded_by: str) -> Optional[HistoryAttachment]:
        """
        Add an attachment to a history note.
        
        Args:
            note_id: ID of the history note
            file: Uploaded file
            uploaded_by: Username of the person uploading
        
        Returns:
            HistoryAttachment: Created attachment or None if failed
        """
        try:
            # Ensure upload directories exist
            ensure_upload_directories()
            
            # Save the uploaded file
            success, error_msg, file_info = save_uploaded_file(file, 'history', 'all')
            if not success:
                logger.error(f"Failed to save attachment: {error_msg}")
                return None
            
            # Create attachment object
            attachment = HistoryAttachment(
                note_id=note_id,
                original_filename=file_info['original_filename'],
                stored_filename=file_info['stored_filename'],
                file_path=file_info['file_path'],
                mime_type=file_info['mime_type'],
                file_size=file_info['file_size']
            )
            
            # Load history data
            history_data = HistoryService._load_history_data()
            
            # Find and update the note
            for note_data in history_data:
                if note_data.get('id') == note_id:
                    if 'attachments' not in note_data:
                        note_data['attachments'] = []
                    
                    note_data['attachments'].append(attachment.model_dump())
                    note_data['updated_at'] = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
                    break
            else:
                # Note not found, clean up uploaded file
                delete_file(file_info['file_path'])
                logger.error(f"History note {note_id} not found")
                return None
            
            # Save updated data
            HistoryService._save_history_data(history_data)

            # Log audit event
            from app.services.audit_service import AuditService
            AuditService.log_event(
                event_type=AuditService.EVENT_TYPES['HISTORY_ATTACHMENT_ADDED'],
                performed_by=uploaded_by,
                description=f"Added attachment '{attachment.original_filename}' to history note",
                status=AuditService.STATUS_SUCCESS,
                details={
                    "note_id": note_id,
                    "attachment_id": attachment.id,
                    "filename": attachment.original_filename,
                    "file_size": attachment.file_size
                }
            )

            logger.info(f"Added attachment {attachment.id} to history note {note_id}")
            return attachment
            
        except Exception as e:
            logger.error(f"Error adding attachment to note {note_id}: {e}")
            return None

    @staticmethod
    def remove_attachment(note_id: str, attachment_id: str) -> bool:
        """
        Remove an attachment from a history note.

        Args:
            note_id: ID of the history note
            attachment_id: ID of the attachment to remove

        Returns:
            bool: True if removed successfully, False otherwise
        """
        try:
            # Load history data
            history_data = HistoryService._load_history_data()

            # Find the note and attachment
            for note_data in history_data:
                if note_data.get('id') == note_id:
                    attachments = note_data.get('attachments', [])

                    for i, attachment_data in enumerate(attachments):
                        if attachment_data.get('id') == attachment_id:
                            # Delete the physical file
                            file_path = attachment_data.get('file_path')
                            if file_path:
                                delete_file(file_path)

                            # Remove from list
                            attachments.pop(i)
                            note_data['updated_at'] = datetime.now().strftime('%Y-%m-%d %H:%M:%S')

                            # Save updated data
                            HistoryService._save_history_data(history_data)

                            # Log audit event
                            from app.services.audit_service import AuditService
                            AuditService.log_event(
                                event_type=AuditService.EVENT_TYPES['HISTORY_ATTACHMENT_DELETED'],
                                performed_by="System",  # Could be enhanced to track actual user
                                description=f"Removed attachment from history note",
                                status=AuditService.STATUS_SUCCESS,
                                details={
                                    "note_id": note_id,
                                    "attachment_id": attachment_id,
                                    "filename": attachment_data.get('original_filename', 'Unknown')
                                }
                            )

                            logger.info(f"Removed attachment {attachment_id} from note {note_id}")
                            return True

            logger.warning(f"Attachment {attachment_id} not found in note {note_id}")
            return False

        except Exception as e:
            logger.error(f"Error removing attachment {attachment_id}: {e}")
            return False

    @staticmethod
    def delete_history_note(note_id: str) -> bool:
        """
        Delete a history note and all its attachments.

        Args:
            note_id: ID of the history note to delete

        Returns:
            bool: True if deleted successfully, False otherwise
        """
        try:
            # Load history data
            history_data = HistoryService._load_history_data()

            # Find and remove the note
            for i, note_data in enumerate(history_data):
                if note_data.get('id') == note_id:
                    # Delete all attachments
                    attachments = note_data.get('attachments', [])
                    for attachment_data in attachments:
                        file_path = attachment_data.get('file_path')
                        if file_path:
                            delete_file(file_path)

                    # Remove note from list
                    equipment_id = note_data.get('equipment_id')
                    equipment_type = note_data.get('equipment_type')
                    history_data.pop(i)

                    # Save updated data
                    HistoryService._save_history_data(history_data)

                    # Check if equipment still has history
                    remaining_history = HistoryService.get_equipment_history(equipment_id, equipment_type)
                    if not remaining_history:
                        HistoryService._update_equipment_history_flag(equipment_id, equipment_type, False)

                    # Log audit event
                    from app.services.audit_service import AuditService
                    AuditService.log_event(
                        event_type=AuditService.EVENT_TYPES['HISTORY_DELETED'],
                        performed_by="System",  # Could be enhanced to track actual user
                        description=f"Deleted history note from {equipment_type.upper()} equipment {equipment_id}",
                        status=AuditService.STATUS_SUCCESS,
                        details={
                            "equipment_id": equipment_id,
                            "equipment_type": equipment_type,
                            "note_id": note_id,
                            "attachments_deleted": len(attachments)
                        }
                    )

                    logger.info(f"Deleted history note {note_id}")
                    return True

            logger.warning(f"History note {note_id} not found")
            return False

        except Exception as e:
            logger.error(f"Error deleting history note {note_id}: {e}")
            return False

    @staticmethod
    def search_history(search_filter: HistorySearchFilter) -> List[HistoryNote]:
        """
        Search history notes with filters.

        Args:
            search_filter: Search criteria

        Returns:
            List[HistoryNote]: Filtered history notes
        """
        try:
            history_data = HistoryService._load_history_data()
            filtered_notes = []

            for note_data in history_data:
                note = HistoryNote(**note_data)

                # Apply filters
                if search_filter.equipment_id and note.equipment_id != search_filter.equipment_id:
                    continue

                if search_filter.equipment_type and note.equipment_type != search_filter.equipment_type.lower():
                    continue

                if search_filter.author_id and note.author_id != search_filter.author_id:
                    continue

                if search_filter.start_date:
                    if note.created_at < search_filter.start_date:
                        continue

                if search_filter.end_date:
                    if note.created_at > search_filter.end_date:
                        continue

                if search_filter.search_text:
                    search_text = search_filter.search_text.lower()
                    if (search_text not in note.note_text.lower() and
                        search_text not in note.author_name.lower()):
                        continue

                filtered_notes.append(note)

            # Sort by created_at descending
            filtered_notes.sort(key=lambda x: x.created_at, reverse=True)

            logger.debug(f"Found {len(filtered_notes)} history notes matching search criteria")
            return filtered_notes

        except Exception as e:
            logger.error(f"Error searching history: {e}")
            return []

    @staticmethod
    def _update_equipment_history_flag(equipment_id: str, equipment_type: str, has_history: bool):
        """
        Update the has_history flag for an equipment.

        Args:
            equipment_id: Equipment ID (SERIAL number)
            equipment_type: Equipment type ('ppm' or 'ocm')
            has_history: Whether equipment has history
        """
        try:
            # Load equipment data
            equipment_data = DataService.load_data(equipment_type)

            # Find and update equipment
            for equipment in equipment_data:
                serial_field = 'SERIAL' if equipment_type == 'ppm' else 'Serial'
                if equipment.get(serial_field) == equipment_id:
                    equipment['has_history'] = has_history
                    break

            # Save updated equipment data
            DataService.save_data(equipment_data, equipment_type)

            logger.debug(f"Updated has_history flag for {equipment_type} equipment {equipment_id}: {has_history}")

        except Exception as e:
            logger.error(f"Error updating equipment history flag: {e}")

    @staticmethod
    def can_user_modify_note(note: HistoryNote, user_id: str, user_role: str = None) -> bool:
        """
        Check if a user can modify (edit/delete) a history note.

        Args:
            note: The history note to check
            user_id: Username of the user
            user_role: Role of the user (Admin, Editor, Viewer)

        Returns:
            bool: True if user can modify the note, False otherwise
        """
        try:
            # Admins can modify any note
            if user_role and user_role.lower() == 'admin':
                return True

            # Original author can modify their own notes
            if note.author_id == user_id:
                return True

            # Last modifier can edit notes they've previously edited
            if note.last_modified_by == user_id:
                return True

            return False

        except Exception as e:
            logger.error(f"Error checking user permissions for note {note.id}: {e}")
            return False

    @staticmethod
    def get_all_history() -> List[HistoryNote]:
        """
        Get all history notes.

        Returns:
            List[HistoryNote]: All history notes
        """
        try:
            history_data = HistoryService._load_history_data()

            all_notes = []
            for note_data in history_data:
                all_notes.append(HistoryNote(**note_data))

            # Sort by created_at descending
            all_notes.sort(key=lambda x: x.created_at, reverse=True)

            return all_notes

        except Exception as e:
            logger.error(f"Error getting all history: {e}")
            return []
