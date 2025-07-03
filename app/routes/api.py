"""API routes for managing equipment maintenance data."""
import logging
import os
from pathlib import Path

import io # Added for TextIOWrapper
import logging
from pathlib import Path

from flask import Blueprint, jsonify, request, Response, current_app, session, send_file # Added session and send_file
from app.decorators import permission_required # Updated import location
from datetime import datetime

from app.services.data_service import DataService
from app.services.history_service import HistoryService
from app.models.history import HistoryNoteCreate, HistoryNoteUpdate, HistorySearchFilter
# training_service is imported directly in the route functions now
# from app.services.training_service import TrainingService
from app.config import Config # Added for VAPID public key
from app.services import training_service # Import the module
from flask_login import current_user

# ImportExportService and ValidationService removed

api_bp = Blueprint('api', __name__)
logger = logging.getLogger(__name__)
if not logger.hasHandlers():
    root_logger = logging.getLogger()
    for handler in root_logger.handlers:
        logger.addHandler(handler)

@api_bp.route("/equipment/<data_type>", methods=["GET"])
@permission_required(["equipment_ppm_read", "equipment_ocm_read"])
def get_equipment(data_type):
    """Get all equipment entries."""
    if data_type not in ('ppm', 'ocm'):
        return jsonify({"error": "Invalid data type"}), 400

    try:
        entries = DataService.get_all_entries(data_type)
        return jsonify(entries), 200
    except Exception as e:
        logger.error(f"Error getting {data_type} entries: {str(e)}")
        return jsonify({"error": "Failed to retrieve equipment data"}), 500

@api_bp.route("/equipment/<data_type>/<SERIAL>", methods=["GET"])
@permission_required(["equipment_ppm_read", "equipment_ocm_read"])
def get_equipment_by_serial(data_type, SERIAL):
    """Get a specific equipment entry by SERIAL."""
    if data_type not in ('ppm', 'ocm'):
        return jsonify({"error": "Invalid data type"}), 400

    try:
        entry = DataService.get_entry(data_type, SERIAL)
        if entry:
            return jsonify(entry), 200
        else:
            return jsonify({"error": f"Equipment with serial '{SERIAL}' not found"}), 404
    except Exception as e:
        logger.error(f"Error getting {data_type} entry {SERIAL}: {str(e)}")
        return jsonify({"error": "Failed to retrieve equipment data"}), 500

@api_bp.route("/equipment/<data_type>", methods=["POST"])
@permission_required(["equipment_ppm_write", "equipment_ocm_write"])
def add_equipment(data_type):
    """Add a new equipment entry."""
    if data_type not in ('ppm', 'ocm'):
        return jsonify({"error": "Invalid data type"}), 400

    if not request.is_json:
        return jsonify({"error": "Request must be JSON"}), 400

    data = request.get_json()

    # Basic validation (more thorough validation in service layer)
    # if 'SERIAL' not in data: # This will be caught by DataService Pydantic validation
    #      return jsonify({"error": "SERIAL is required"}), 400

    try:
        # Data is passed directly; Pydantic validation happens in DataService.add_entry
        added_entry = DataService.add_entry(data_type, data)
        return jsonify(added_entry), 201
    except ValueError as e:
        logger.warning(f"Validation error adding {data_type} entry: {str(e)}")
        return jsonify({"error": str(e)}), 400
    except Exception as e:
        logger.error(f"Error adding {data_type} entry: {str(e)}")
        return jsonify({"error": "Failed to add equipment"}), 500


@api_bp.route("/equipment/<data_type>/<SERIAL>", methods=["PUT"])
@permission_required(["equipment_ppm_write", "equipment_ocm_write"])
def update_equipment(data_type, SERIAL):
    """Update an existing equipment entry."""
    if data_type not in ('ppm', 'ocm'):
        return jsonify({"error": "Invalid data type"}), 400

    if not request.is_json:
        return jsonify({"error": "Request must be JSON"}), 400

    data = request.get_json()

    # Ensure SERIAL in payload matches the URL parameter
    if data.get('SERIAL') != SERIAL:
         return jsonify({"error": "SERIAL in payload must match URL parameter"}), 400

    try:
        # Convert JSON data if needed before validation/update
        updated_entry = DataService.update_entry(data_type, SERIAL, data)
        return jsonify(updated_entry), 200
    except ValueError as e:
        logger.warning(f"Validation error updating {data_type} entry {SERIAL}: {str(e)}")
        return jsonify({"error": str(e)}), 400
    except KeyError:
         return jsonify({"error": f"Equipment with serial '{SERIAL}' not found"}), 404
    except Exception as e:
        logger.error(f"Error updating {data_type} entry {SERIAL}: {str(e)}")
        return jsonify({"error": "Failed to update equipment"}), 500


@api_bp.route("/equipment/<data_type>/<SERIAL>", methods=["DELETE"])
@permission_required(["equipment_ppm_delete", "equipment_ocm_delete"])
def delete_equipment(data_type, SERIAL):
    """Delete an equipment entry."""
    if data_type not in ('ppm', 'ocm'):
        return jsonify({"error": "Invalid data type"}), 400

    try:
        deleted = DataService.delete_entry(data_type, SERIAL)
        if deleted:
            return jsonify({"message": f"Equipment with serial '{SERIAL}' deleted successfully"}), 200
        else:
            return jsonify({"error": f"Equipment with serial '{SERIAL}' not found"}), 404
    except Exception as e:
        logger.error(f"Error deleting {data_type} entry {SERIAL}: {str(e)}")
        return jsonify({"error": "Failed to delete equipment"}), 500


@api_bp.route("/export/<data_type>", methods=["GET"])
@permission_required(["export_data"])
def export_data(data_type):
    """Export data to CSV."""
    if data_type not in ('ppm', 'ocm'):
        return jsonify({"error": "Invalid data type"}), 400

    try:
        csv_content = DataService.export_data(data_type)
        if csv_content is None or csv_content == "": # Handle empty data case from service
            # Optionally return 204 No Content, or an empty CSV with headers
            # Current DataService.export_data returns "" if no data.
            # For consistency, we can make it return headers only.
            # For now, if it's empty string, send it as such.
            pass

        filename = f"{data_type}_export_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv"
        return Response(
            csv_content,
            mimetype="text/csv",
            headers={"Content-disposition":
                        f"attachment; filename={filename}"})
    except Exception as e:
        logger.error(f"Error exporting {data_type} data: {str(e)}")
        return jsonify({"error": f"Failed to export {data_type} data"}), 500


@api_bp.route("/import/<data_type>", methods=["POST"])
@permission_required(["import_data"])
def import_data(data_type):
    """Import data from CSV with robust encoding detection and handling."""
    if data_type not in ('ppm', 'ocm'):
        return jsonify({"error": "Invalid data type"}), 400

    if 'file' not in request.files:
        return jsonify({"error": "No file part"}), 400

    file = request.files['file']
    if file.filename == '':
        return jsonify({"error": "No selected file"}), 400

    if file and file.filename.endswith('.csv'):
        try:
            # Import encoding detection utility
            from app.utils.encoding_utils import EncodingDetector
            
            logger.info(f"Starting import of {data_type} data from file: {file.filename}")
            
            # Use robust encoding detection to create text stream
            file_stream, encoding_used, encoding_error = EncodingDetector.safe_read_csv_with_encoding(
                file.stream, 
                preferred_encoding=None  # Let auto-detection handle it
            )
            
            if encoding_error:
                logger.error(f"Encoding detection failed for file {file.filename}: {encoding_error}")
                return jsonify({
                    "error": f"Failed to read file due to encoding issues: {encoding_error}",
                    "details": "The file may be corrupted or use an unsupported text encoding. Please ensure the file is saved in UTF-8 format.",
                    "suggestions": [
                        "Try saving the file as UTF-8 in Excel or your CSV editor",
                        "Check if the file contains special characters that may cause encoding issues",
                        "Ensure the file is not corrupted"
                    ]
                }), 400
            
            logger.info(f"Successfully detected and using encoding: {encoding_used} for file: {file.filename}")

            # Call DataService.import_data directly with the properly encoded stream
            import_results = DataService.import_data(data_type, file_stream)
            
            # Add encoding information to the results
            import_results['encoding_used'] = encoding_used
            import_results['file_name'] = file.filename

            # Check for errors in import_results to determine status code
            if import_results.get("errors") and (import_results.get("added_count", 0) == 0 and import_results.get("updated_count", 0) == 0) :
                # If there are errors and nothing was added or updated, consider it a failure.
                # Or if only skipped_count > 0 and errors exist.
                status_code = 400 # Bad request if all rows failed or file was problematic
            elif import_results.get("errors"):
                status_code = 207 # Multi-Status if some rows succeeded and some failed
            else:
                status_code = 200 # OK if all succeeded

            return jsonify(import_results), status_code

        except UnicodeDecodeError as e:
            logger.error(f"Unicode encoding error importing {data_type} data from {file.filename}: {str(e)}")
            return jsonify({
                "error": f"File encoding error: Unable to read the file due to character encoding issues",
                "details": f"The file contains characters that cannot be decoded. Error at position {e.start}: {str(e)}",
                "suggestions": [
                    "Save the file in UTF-8 encoding",
                    "Remove or replace special characters in the file",
                    "Use a text editor to check for hidden or problematic characters",
                    "Try converting the file encoding using a tool like Notepad++ or Excel"
                ],
                "technical_details": str(e)
            }), 400
        except Exception as e:
            logger.error(f"Error importing {data_type} data from {file.filename}: {str(e)}", exc_info=True)
            
            # Check if it's an encoding-related error
            error_str = str(e).lower()
            if any(keyword in error_str for keyword in ['codec', 'decode', 'encoding', 'utf-8', 'unicode']):
                return jsonify({
                    "error": f"File encoding error: {str(e)}",
                    "details": "The file appears to have encoding issues. This often happens with files created in different text encodings.",
                    "suggestions": [
                        "Try saving the file as UTF-8 in your spreadsheet application",
                        "Check for special characters or symbols in your data",
                        "Use 'Save As' and select UTF-8 encoding in Excel or LibreOffice"
                    ],
                    "file_name": file.filename
                }), 400
            else:
                return jsonify({
                    "error": f"Failed to import {data_type} data: {str(e)}", 
                    "details": str(e),
                    "file_name": file.filename
                }), 500
    else:
        return jsonify({"error": "Invalid file type, only CSV allowed"}), 400

@api_bp.route("/bulk_delete/<data_type>", methods=["POST"])
@permission_required(["equipment_ppm_delete", "equipment_ocm_delete"])
def bulk_delete(data_type):
    """Handle bulk deletion of equipment entries."""
    if data_type not in ('ppm', 'ocm'):
        return jsonify({'success': False, 'message': 'Invalid data type'}), 400

    serials = request.json.get('serials', [])
    if not serials:
        return jsonify({'success': False, 'message': 'No serials provided'}), 400

    deleted_count = 0
    not_found = 0

    for serial in serials:
        if DataService.delete_entry(data_type, serial):
            deleted_count += 1
        else:
            not_found += 1

    return jsonify({
        'success': True,
        'deleted_count': deleted_count,
        'not_found': not_found
    })



# Training Records API Routes

@api_bp.route("/trainings", methods=["POST"])
@permission_required(["training_write"])
def add_training_route():
    if not request.is_json:
        logger.warning("Add training request is not JSON")
        return jsonify({"error": "Request must be JSON"}), 400
    data = request.get_json()
    logger.info(f"Received data for new training: {data}")
    try:
        new_record = training_service.add_training(data)
        logger.info(f"Successfully added new training record with ID: {new_record.id}")
        return jsonify(new_record.to_dict()), 201
    except ValueError as e:
        logger.warning(f"Validation error adding training: {str(e)}")
        return jsonify({"error": str(e)}), 400
    except Exception as e:
        logger.error(f"Error adding training record: {str(e)}", exc_info=True)
        return jsonify({"error": "Failed to add training record"}), 500

@api_bp.route("/trainings", methods=["GET"])
@permission_required(["training_read"])
def get_all_trainings_route():
    try:
        records = training_service.get_all_trainings()
        return jsonify([record.to_dict() for record in records]), 200
    except Exception as e:
        logger.error(f"Error getting all training records: {str(e)}", exc_info=True)
        return jsonify({"error": "Failed to retrieve training records"}), 500

@api_bp.route("/trainings/<training_id>", methods=["GET"])
@permission_required(["training_read"])
def get_training_by_id_route(training_id):
    try:
        # Use training_id as string since the data stores IDs as strings
        record = training_service.get_training_by_id(training_id)
        if record:
            return jsonify(record.to_dict()), 200
        else:
            logger.warning(f"Training record with ID {training_id} not found.")
            return jsonify({"error": "Training record not found"}), 404
    except Exception as e:
        logger.error(f"Error getting training record {training_id}: {str(e)}", exc_info=True)
        return jsonify({"error": "Failed to retrieve training record"}), 500

@api_bp.route("/trainings/<training_id>", methods=["PUT"])
@permission_required(["training_write"])
def update_training_route(training_id):
    if not request.is_json:
        logger.warning(f"Update training request for ID {training_id} is not JSON")
        return jsonify({"error": "Request must be JSON"}), 400
    data = request.get_json()
    logger.info(f"Received data for updating training ID {training_id}: {data}")
    try:
        # Use training_id as string since the data stores IDs as strings
        updated_record = training_service.update_training(training_id, data)
        if updated_record:
            logger.info(f"Successfully updated training record with ID: {training_id}")
            return jsonify(updated_record.to_dict()), 200
        else:
            logger.warning(f"Training record with ID {training_id} not found for update.")
            return jsonify({"error": "Training record not found"}), 404
    except ValueError as e:
        logger.warning(f"Validation error updating training {training_id}: {str(e)}")
        return jsonify({"error": str(e)}), 400
    except Exception as e:
        logger.error(f"Error updating training record {training_id}: {str(e)}", exc_info=True)
        return jsonify({"error": "Failed to update training record"}), 500

@api_bp.route("/trainings/<training_id>", methods=["DELETE"])
@permission_required(["training_delete"])
def delete_training_route(training_id):
    try:
        # Use training_id as string since the data stores IDs as strings
        success = training_service.delete_training(training_id)
        if success:
            logger.info(f"Successfully deleted training record with ID: {training_id}")
            return jsonify({"message": "Training record deleted successfully"}), 200
        else:
            logger.warning(f"Training record with ID {training_id} not found for deletion.")
            return jsonify({"error": "Training record not found"}), 404
    except Exception as e:
        logger.error(f"Error deleting training record {training_id}: {str(e)}", exc_info=True)
        return jsonify({"error": "Failed to delete training record"}), 500

@api_bp.route("/trainings/bulk_delete", methods=["POST"])
@permission_required(["training_delete"])
def bulk_delete_training():
    """Handle bulk deletion of training records."""
    if not request.is_json:
        return jsonify({"error": "Request must be JSON"}), 400
    
    training_ids = request.json.get('training_ids', [])
    if not training_ids:
        return jsonify({'success': False, 'message': 'No training IDs provided'}), 400

    deleted_count = 0
    not_found = 0
    errors = []

    for training_id in training_ids:
        try:
            success = training_service.delete_training(str(training_id))
            if success:
                deleted_count += 1
                logger.info(f"Successfully deleted training record with ID: {training_id}")
            else:
                not_found += 1
                logger.warning(f"Training record with ID {training_id} not found for deletion.")
        except Exception as e:
            errors.append(f"Error deleting training ID {training_id}: {str(e)}")
            logger.error(f"Error deleting training record {training_id}: {str(e)}", exc_info=True)

    return jsonify({
        'success': True,
        'deleted_count': deleted_count,
        'not_found': not_found,
        'errors': errors,
        'total_requested': len(training_ids)
    })

# --- Application Settings API Routes ---

@api_bp.route("/settings", methods=["GET"])
@permission_required(["settings_read"])
def get_settings():
    """Get current application settings."""
    try:
        settings = DataService.load_settings()
        return jsonify(settings), 200
    except Exception as e:
        logger.error(f"Error loading settings: {str(e)}")
        return jsonify({"error": "Failed to load settings"}), 500

@api_bp.route("/settings", methods=["POST"])
@permission_required(["settings_manage"])
def save_settings():
    """Save application settings."""
    # Added detailed logging for headers and raw body
    logger.info(f"save_settings called. Request Method: {request.method}")
    logger.info(f"Request Headers: {request.headers}")
    logger.info(f"Request Content-Type: {request.content_type}")
    logger.info(f"Request is_json: {request.is_json}")
    logger.debug(f"Request raw data: {request.get_data(as_text=True)}") # Log raw data

    # Try to parse JSON irrespective of Content-Type header, handle failure gracefully
    data = request.get_json(force=True, silent=True)

    if data is None:
        logger.warning(f"Failed to parse request body as JSON. Request data (first 200 chars): {request.data[:200]}...")
        # The frontend reported "Invalid request format. Expected JSON."
        # We'll return a similar error, but make it clear it's from our explicit check.
        return jsonify({"error": "Invalid request format. Expected JSON data."}), 400

    logger.info(f"Successfully parsed settings data: {data}")

    # Basic validation for expected keys and types (more flexible now)
    email_notifications_enabled = data.get("email_notifications_enabled")
    email_reminder_interval_minutes = data.get("email_reminder_interval_minutes")
    recipient_email = data.get("recipient_email", "") # Default to empty string if not provided

    push_notifications_enabled = data.get("push_notifications_enabled")
    push_notification_interval_minutes = data.get("push_notification_interval_minutes")

    # Only validate if the fields are provided
    if email_notifications_enabled is not None and not isinstance(email_notifications_enabled, bool):
        return jsonify({"error": "Invalid type for email_notifications_enabled, boolean expected."}), 400
    if email_reminder_interval_minutes is not None and (not isinstance(email_reminder_interval_minutes, int) or email_reminder_interval_minutes <= 0):
        err_msg = "Invalid value for email_reminder_interval_minutes, positive integer expected."
        return jsonify({"error": err_msg}), 400
    if recipient_email is not None and not isinstance(recipient_email, str):
        return jsonify({"error": "Invalid type for recipient_email, string expected."}), 400

    if push_notifications_enabled is not None and not isinstance(push_notifications_enabled, bool):
        return jsonify({"error": "Invalid type for push_notifications_enabled, boolean expected."}), 400
    if push_notification_interval_minutes is not None and (not isinstance(push_notification_interval_minutes, int) or push_notification_interval_minutes <= 0):
        err_msg = "Invalid value for push_notification_interval_minutes, positive integer expected."
        return jsonify({"error": err_msg}), 400

    # Extract new scheduling fields
    use_daily_send_time = data.get("use_daily_send_time")
    use_legacy_interval = data.get("use_legacy_interval")
    email_send_time = data.get("email_send_time", "")
    enable_automatic_reminders = data.get("enable_automatic_reminders")
    scheduler_interval_hours = data.get("scheduler_interval_hours")

    # Extract reminder timing fields
    reminder_timing_60_days = data.get("reminder_timing_60_days")
    reminder_timing_14_days = data.get("reminder_timing_14_days")
    reminder_timing_1_day = data.get("reminder_timing_1_day")

    # Extract CC emails field
    cc_emails = data.get("cc_emails")
    
    # Construct settings object to save all known settings
    settings_to_save = {}
    
    # Only add fields that are provided
    if email_notifications_enabled is not None:
        settings_to_save["email_notifications_enabled"] = email_notifications_enabled
    if email_reminder_interval_minutes is not None:
        settings_to_save["email_reminder_interval_minutes"] = email_reminder_interval_minutes
    if recipient_email is not None:
        settings_to_save["recipient_email"] = recipient_email.strip()
    if push_notifications_enabled is not None:
        settings_to_save["push_notifications_enabled"] = push_notifications_enabled
    if push_notification_interval_minutes is not None:
        settings_to_save["push_notification_interval_minutes"] = push_notification_interval_minutes
    
    # Add new fields if provided
    if use_daily_send_time is not None:
        settings_to_save["use_daily_send_time"] = use_daily_send_time
    if use_legacy_interval is not None:
        settings_to_save["use_legacy_interval"] = use_legacy_interval
    if email_send_time:
        settings_to_save["email_send_time"] = email_send_time
    if enable_automatic_reminders is not None:
        settings_to_save["enable_automatic_reminders"] = enable_automatic_reminders
    if scheduler_interval_hours is not None:
        settings_to_save["scheduler_interval_hours"] = scheduler_interval_hours

    # Add reminder timing fields if provided
    if reminder_timing_60_days is not None:
        # Update the reminder_timing nested structure
        if "reminder_timing" not in settings_to_save:
            settings_to_save["reminder_timing"] = {}
        settings_to_save["reminder_timing"]["60_days_before"] = reminder_timing_60_days
    if reminder_timing_14_days is not None:
        if "reminder_timing" not in settings_to_save:
            settings_to_save["reminder_timing"] = {}
        settings_to_save["reminder_timing"]["14_days_before"] = reminder_timing_14_days
    if reminder_timing_1_day is not None:
        if "reminder_timing" not in settings_to_save:
            settings_to_save["reminder_timing"] = {}
        settings_to_save["reminder_timing"]["1_day_before"] = reminder_timing_1_day

    # Add CC emails field if provided
    if cc_emails is not None:
        settings_to_save["cc_emails"] = cc_emails.strip()

    # Preserve any other settings that might be in data/settings.json but not managed through this API call
    # This requires loading current settings first.
    try:
        current_settings = DataService.load_settings()

        # Handle reminder_timing structure properly - merge nested dict
        if "reminder_timing" in settings_to_save:
            if "reminder_timing" not in current_settings:
                current_settings["reminder_timing"] = {}
            current_settings["reminder_timing"].update(settings_to_save["reminder_timing"])
            # Remove from settings_to_save to avoid overwriting the whole structure
            reminder_timing_update = settings_to_save.pop("reminder_timing")

        # Update current_settings with validated values from the request
        current_settings.update(settings_to_save)

        # Now save the merged settings
        DataService.save_settings(current_settings)
        logger.info(f"Settings saved successfully: {current_settings}")
        return jsonify({"message": "Settings saved successfully", "settings": current_settings}), 200
    except ValueError as e: # Catch specific error from save_settings for IO issues
        logger.error(f"Error saving settings (ValueError): {str(e)}")
        return jsonify({"error": f"Failed to save settings: {str(e)}"}), 500
    except Exception as e:
        logger.error(f"Unexpected error saving settings: {str(e)}")
        return jsonify({"error": "Failed to save settings due to an unexpected error"}), 500

@api_bp.route('/health')
def health_check():
    return 'OK', 200

# --- Push Notification API Routes ---

@api_bp.route('/vapid_public_key', methods=['GET'])
def vapid_public_key():
    """Provide the VAPID public key to the client."""
    if not Config.VAPID_PUBLIC_KEY:
        logger.error("VAPID_PUBLIC_KEY not configured on the server.")
        return jsonify({"error": "VAPID public key not configured."}), 500
    return jsonify({"publicKey": Config.VAPID_PUBLIC_KEY}), 200

@api_bp.route('/push_subscribe', methods=['POST'])
def push_subscribe():
    """
    Subscribes a client for push notifications.
    Expects a JSON payload with the PushSubscription object.
    Example: {"endpoint": "...", "keys": {"p256dh": "...", "auth": "..."}}
    """
    if not request.is_json:
        return jsonify({"error": "Request must be JSON"}), 400

    subscription_info = request.get_json()
    if not subscription_info or not subscription_info.get("endpoint"):
        return jsonify({"error": "Invalid subscription object. 'endpoint' is required."}), 400

    # Basic validation of the subscription object structure (more can be added)
    if not isinstance(subscription_info.get("keys"), dict) or \
       not subscription_info["keys"].get("p256dh") or \
       not subscription_info["keys"].get("auth"):
        return jsonify({"error": "Invalid subscription object structure. 'keys.p256dh' and 'keys.auth' are required."}), 400

    try:
        DataService.add_push_subscription(subscription_info)
        logger.info(f"Successfully subscribed for push notifications: {subscription_info.get('endpoint')[:50]}...")
        return jsonify({"message": "Subscription successful"}), 201
    except Exception as e:
        logger.error(f"Error subscribing for push notifications: {str(e)}", exc_info=True)
        return jsonify({"error": "Failed to subscribe for push notifications"}), 500

@api_bp.route('/push_unsubscribe', methods=['POST'])
def push_unsubscribe():
    """
    Unsubscribes a client from push notifications.
    Expects a JSON payload with the endpoint to unsubscribe.
    Example: {"endpoint": "..."}
    """
    if not request.is_json:
        return jsonify({"error": "Request must be JSON"}), 400

    data = request.get_json()
    endpoint_to_remove = data.get("endpoint")

    if not endpoint_to_remove:
        return jsonify({"error": "Invalid request. 'endpoint' is required."}), 400

    try:
        DataService.remove_push_subscription(endpoint_to_remove)
        logger.info(f"Successfully unsubscribed from push notifications: {endpoint_to_remove[:50]}...")
        return jsonify({"message": "Unsubscription successful"}), 200
    except Exception as e:
        logger.error(f"Error unsubscribing from push notifications: {str(e)}", exc_info=True)
        return jsonify({"error": "Failed to unsubscribe from push notifications"}), 500

@api_bp.route('/test-push', methods=['POST'])
def send_test_push():
    """Send a test push notification to verify push notification configuration."""
    logger.info("Received request to send test push notification via API.")
    
    try:
        from app.services.push_notification_service import PushNotificationService
        from app.config import Config
        
        # Check VAPID configuration first
        if not Config.VAPID_PRIVATE_KEY or not Config.VAPID_PUBLIC_KEY:
            logger.error("VAPID keys not configured")
            return jsonify({
                'error': 'Push notifications not configured. Please set VAPID_PRIVATE_KEY and VAPID_PUBLIC_KEY in your environment variables or .env file.'
            }), 400
        
        # Load current settings
        settings = DataService.load_settings()
        push_enabled = settings.get('push_notifications_enabled', False)
        
        if not push_enabled:
            return jsonify({'error': 'Push notifications are disabled in settings. Please enable them first.'}), 400
        
        # Check subscriptions
        subscriptions = DataService.load_push_subscriptions()
        if not subscriptions:
            return jsonify({'error': 'No push subscriptions found. Please subscribe to push notifications first.'}), 400
        
        # Send test push notification
        test_message = f"Test push notification sent at {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}"
        
        import asyncio
        try:
            # Run the async function
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)
            success = loop.run_until_complete(PushNotificationService.send_push_notification(test_message))
            loop.close()
            
            if success:
                logger.info(f"Test push notification sent successfully to {len(subscriptions)} subscription(s)")
                return jsonify({'message': f'Test push notification sent successfully to {len(subscriptions)} device(s)!'}), 200
            else:
                logger.error("Failed to send test push notification")
                return jsonify({'error': 'Failed to send test push notification. Please check your VAPID keys and push subscriptions.'}), 500
                
        except Exception as e:
            logger.error(f"Error in async push notification: {str(e)}")
            return jsonify({'error': f'Error sending test push notification: {str(e)}'}), 500
            
    except ImportError:
        logger.error("PushNotificationService not available")
        return jsonify({'error': 'Push notification service not available.'}), 500
    except Exception as e:
        logger.error(f"Error sending test push notification: {str(e)}")
        return jsonify({'error': f'Error sending test push notification: {str(e)}'}), 500

@api_bp.route('/training/import', methods=['POST'])
def import_training_data():
    """API endpoint for training data import that returns JSON response."""
    try:
        logger.info("Training import API endpoint called")
        
        if 'file' not in request.files:
            logger.warning("No file provided in training import request")
            return jsonify({'success': False, 'error': 'No file provided'}), 400
        
        file = request.files['file']
        if file.filename == '':
            logger.warning("No file selected in training import request")
            return jsonify({'success': False, 'error': 'No file selected'}), 400
        
        if not file.filename.endswith('.csv'):
            logger.warning(f"Invalid file type: {file.filename}")
            return jsonify({'success': False, 'error': 'File must be a CSV'}), 400
        
        # Import the training data using the import service
        from app.services.import_export import ImportExportService
        
        # Save the uploaded file temporarily
        import tempfile
        import os
        
        with tempfile.NamedTemporaryFile(delete=False, suffix='.csv') as temp_file:
            file.save(temp_file.name)
            temp_file_path = temp_file.name
        
        try:
            logger.info(f"Starting training import from file: {file.filename}")
            success, message, stats = ImportExportService.import_from_csv('training', temp_file_path)
            
            # Clean up temp file
            os.unlink(temp_file_path)
            
            if success:
                logger.info(f"Training import successful: {message}, Stats: {stats}")
                return jsonify({
                    'success': True,
                    'message': message,
                    'stats': stats,
                    'redirect_url': '/training'
                })
            else:
                logger.error(f"Training import failed: {message}")
                return jsonify({'success': False, 'error': message}), 400
                
        except Exception as e:
            # Clean up temp file on error
            if os.path.exists(temp_file_path):
                os.unlink(temp_file_path)
            logger.error(f"Error during training import: {e}", exc_info=True)
            raise e
            
    except Exception as e:
        logger.error(f"Error in training import API: {e}", exc_info=True)
        return jsonify({'success': False, 'error': str(e)}), 500

@api_bp.route('/import/auto', methods=['POST'])
def import_auto():
    """Auto-detect CSV type and import data."""
    if 'file' not in request.files:
        return jsonify({"error": "No file part"}), 400

    file = request.files['file']
    if file.filename == '':
        return jsonify({"error": "No selected file"}), 400

    if file and file.filename.endswith('.csv'):
        try:
            # Import the import service
            from app.services.import_export import ImportExportService
            
            # Save the uploaded file temporarily
            import tempfile
            import os
            
            with tempfile.NamedTemporaryFile(delete=False, suffix='.csv') as temp_file:
                file.save(temp_file.name)
                temp_file_path = temp_file.name
            
            try:
                # First, detect the CSV type with encoding detection
                import pandas as pd
                from app.utils.encoding_utils import EncodingDetector
                
                # Detect encoding for the temp file
                with open(temp_file_path, 'rb') as binary_file:
                    encoding, confidence = EncodingDetector.detect_encoding(binary_file)
                    logger.info(f"Auto-import detected encoding: {encoding} (confidence: {confidence:.2%})")
                
                # Read CSV with detected encoding
                try:
                    df = pd.read_csv(temp_file_path, dtype=str, encoding=encoding)
                except UnicodeDecodeError:
                    logger.warning(f"Encoding {encoding} failed, trying fallback encodings")
                    # Try common encodings as fallback
                    for fallback_encoding in EncodingDetector.COMMON_ENCODINGS:
                        try:
                            df = pd.read_csv(temp_file_path, dtype=str, encoding=fallback_encoding)
                            logger.info(f"Successfully read file with fallback encoding: {fallback_encoding}")
                            break
                        except UnicodeDecodeError:
                            continue
                    else:
                        # Last resort: use errors='replace'
                        df = pd.read_csv(temp_file_path, dtype=str, encoding='utf-8', encoding_errors='replace')
                        logger.warning("Using UTF-8 with error replacement for auto-import")
                
                detected_type = ImportExportService.detect_csv_type(df.columns.tolist())
                
                if detected_type == 'unknown':
                    # Clean up temp file
                    os.unlink(temp_file_path)
                    return jsonify({"error": "Unable to determine CSV type - required columns missing"}), 400
                
                logger.info(f"Auto-detected CSV type: {detected_type}")
                
                # Import using the detected type
                success, message, stats = ImportExportService.import_from_csv(detected_type, temp_file_path)
                
                # Clean up temp file
                os.unlink(temp_file_path)
                
                if success:
                    logger.info(f"Auto-import successful for {detected_type}: {message}, Stats: {stats}")
                    return jsonify({
                        'success': True,
                        'message': message,
                        'type': detected_type,
                        'stats': stats
                    })
                else:
                    logger.error(f"Auto-import failed for {detected_type}: {message}")
                    return jsonify({'error': message, 'type': detected_type}), 400
                    
            except Exception as e:
                # Clean up temp file on error
                if os.path.exists(temp_file_path):
                    os.unlink(temp_file_path)
                logger.error(f"Error during auto-import: {e}", exc_info=True)
                raise e
                
        except Exception as e:
            logger.error(f"Error in auto-import: {e}", exc_info=True)
            return jsonify({"error": f"Failed to import data: {str(e)}"}), 500
    else:
        return jsonify({"error": "Invalid file type, only CSV allowed"}), 400

@api_bp.route('/send-immediate-reminders', methods=['POST'])
@permission_required(["settings_manage"])
def send_immediate_reminders():
    """Send immediate maintenance reminder emails for all priority levels."""
    logger.info("Received request to send immediate reminder emails.")
    try:
        from app.services.email_service import EmailService
        
        # Process reminders immediately without waiting for scheduler
        import asyncio
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        
        try:
            # Get the coroutine result
            emails_sent = loop.run_until_complete(EmailService.process_reminders())
            logger.info(f"Immediate reminders processed. Emails sent: {emails_sent}")
            
            return jsonify({
                'success': True,
                'message': 'Immediate reminder emails sent successfully',
                'emails_sent': emails_sent
            }), 200
            
        finally:
            loop.close()
            
    except Exception as e:
        logger.error(f"Error sending immediate reminders: {str(e)}", exc_info=True)
        return jsonify({
            'error': f'Failed to send immediate reminders: {str(e)}'
        }), 500

@api_bp.route('/restore-backup', methods=['POST'])
@permission_required(["backup_manage"])
def restore_backup():
    """Restore from backup file."""
    logger.info("Received backup restore request.")
    try:
        if 'backup_file' not in request.files:
            return jsonify({'error': 'No backup file provided'}), 400
        
        file = request.files['backup_file']
        backup_type = request.form.get('backup_type', 'unknown')
        
        if file.filename == '':
            return jsonify({'error': 'No file selected'}), 400
        
        from app.services.backup_service import BackupService
        
        # Determine backup type from file extension if not specified
        if backup_type == 'unknown':
            if file.filename.lower().endswith('.zip'):
                backup_type = 'full'
            elif file.filename.lower().endswith('.json'):
                backup_type = 'settings'
            else:
                return jsonify({'error': 'Unsupported file type. Please upload .zip or .json files only.'}), 400
        
        # Save uploaded file temporarily
        import tempfile
        import os
        
        with tempfile.NamedTemporaryFile(delete=False, suffix=os.path.splitext(file.filename)[1]) as temp_file:
            file.save(temp_file.name)
            temp_file_path = temp_file.name
        
        try:
            if backup_type == 'settings':
                result = BackupService.restore_settings_backup(temp_file_path)
            else:
                result = BackupService.restore_full_backup(temp_file_path)
            
            if result['success']:
                return jsonify({
                    'success': True,
                    'message': result.get('message', 'Backup restored successfully'),
                    'restored_items': result.get('restored_items', 0)
                }), 200
            else:
                return jsonify({
                    'error': result.get('error', 'Failed to restore backup')
                }), 500
                
        finally:
            # Clean up temporary file
            try:
                os.unlink(temp_file_path)
            except OSError:
                pass
                
    except Exception as e:
        logger.error(f"Error restoring backup: {str(e)}", exc_info=True)
        return jsonify({
            'error': f'Failed to restore backup: {str(e)}'
        }), 500

@api_bp.route('/backup-settings', methods=['POST'])
@permission_required(['backup_manage'])
def save_backup_settings():
    """Save backup settings via API."""
    logger.info("Received request to save backup settings via API.")

    try:
        # Get JSON data from request
        data = request.get_json()
        if not data:
            return jsonify({'error': 'No data provided'}), 400

        # Load current settings
        current_settings = DataService.load_settings()

        # Update backup-related settings
        backup_settings = {
            'automatic_backup_enabled': data.get('automatic_backup_enabled', False),
            'automatic_backup_interval_hours': int(data.get('automatic_backup_interval_hours', 24))
        }

        # Validate interval
        if backup_settings['automatic_backup_interval_hours'] < 1:
            return jsonify({'error': 'Backup interval must be at least 1 hour'}), 400

        # Update current settings with backup settings
        current_settings.update(backup_settings)

        # Save updated settings
        DataService.save_settings(current_settings)

        logger.info(f"Backup settings saved successfully: {backup_settings}")

        # Log audit event
        from app.services.audit_service import AuditService
        AuditService.log_event(
            event_type=AuditService.EVENT_TYPES['SETTING_CHANGED'],
            performed_by="User",
            description="Backup settings updated via API",
            status=AuditService.STATUS_SUCCESS,
            details=backup_settings
        )

        return jsonify({
            'success': True,
            'message': 'Backup settings saved successfully',
            'settings': backup_settings
        }), 200

    except Exception as e:
        logger.error(f"Error saving backup settings: {str(e)}")
        return jsonify({'error': f'Failed to save backup settings: {str(e)}'}), 500

@api_bp.route('/backup', methods=['POST'])
@permission_required(['backup_manage'])
def create_backup():
    """Create a backup via API."""
    logger.info("Received request to create backup via API.")

    try:
        # Get backup type from request (default to settings)
        data = request.get_json() or {}
        backup_type = data.get('backup_type', 'settings')

        if backup_type not in ['full', 'settings']:
            return jsonify({'error': 'Invalid backup type. Must be "full" or "settings"'}), 400

        # Create backup based on type
        from app.services.backup_service import BackupService

        if backup_type == 'full':
            result = BackupService.create_full_backup()
        else:
            result = BackupService.create_settings_backup()

        if result['success']:
            logger.info(f"Backup created successfully: {result['filename']}")
            return jsonify({
                'success': True,
                'message': result['message'],
                'filename': result['filename'],
                'backup_type': backup_type
            }), 200
        else:
            logger.error(f"Backup creation failed: {result.get('error', 'Unknown error')}")
            return jsonify({'error': result.get('error', 'Failed to create backup')}), 500

    except Exception as e:
        logger.error(f"Error creating backup: {str(e)}")
        return jsonify({'error': f'Failed to create backup: {str(e)}'}), 500

@api_bp.route('/backup/download/<backup_type>/<filename>', methods=['GET'])
@permission_required(['backup_manage'])
def download_backup_api(backup_type, filename):
    """Download a backup file via API."""
    logger.info(f"Received request to download backup: {backup_type}/{filename}")

    try:
        if backup_type not in ['full', 'settings']:
            return jsonify({'error': 'Invalid backup type'}), 400

        from app.services.backup_service import BackupService

        # Determine backup directory
        if backup_type == 'full':
            backup_path = os.path.join(BackupService.FULL_BACKUPS_DIR, filename)
        else:
            backup_path = os.path.join(BackupService.SETTINGS_BACKUPS_DIR, filename)

        if not os.path.exists(backup_path):
            return jsonify({'error': 'Backup file not found'}), 404

        # Log audit event
        from app.services.audit_service import AuditService
        AuditService.log_event(
            event_type=AuditService.EVENT_TYPES['DATA_EXPORT'],
            performed_by="User",
            description=f"Downloaded backup file via API: {filename}",
            status=AuditService.STATUS_SUCCESS,
            details={"backup_type": backup_type, "filename": filename}
        )

        return send_file(
            backup_path,
            as_attachment=True,
            download_name=filename,
            mimetype='application/octet-stream'
        )

    except Exception as e:
        logger.error(f"Error downloading backup: {str(e)}")
        return jsonify({'error': f'Failed to download backup: {str(e)}'}), 500

@api_bp.route('/test-email', methods=['POST'])
def send_test_email():
    """Send a test email to verify email configuration."""
    logger.info("Received request to send test email via API.")

    try:
        # Check email configuration first
        from app.config import Config

        if not Config.MAILJET_API_KEY or not Config.MAILJET_SECRET_KEY:
            logger.error("Mailjet API credentials not configured")
            return jsonify({
                'error': 'Email service not configured. Please set MAILJET_API_KEY and MAILJET_SECRET_KEY in your environment variables or .env file.'
            }), 400

        if not Config.EMAIL_SENDER:
            logger.error("Email sender not configured")
            return jsonify({
                'error': 'Email sender not configured. Please set EMAIL_SENDER in your environment variables or .env file.'
            }), 400
        
        from app.services.email_service import EmailService
        
        # Load current settings
        settings = DataService.load_settings()
        recipient_email = settings.get('recipient_email', '')
        cc_emails = settings.get('cc_emails', '')
        
        if not recipient_email:
            return jsonify({'error': 'No recipient email configured in settings. Please configure a recipient email first.'}), 400
        
        # Prepare test email content
        subject = "Hospital Equipment System - Test Email"
        body = f"""
        <h2>Test Email from Hospital Equipment System</h2>
        <p>This is a test email to verify your email configuration.</p>
        <p><strong>Sent to:</strong> {recipient_email}</p>
        {f'<p><strong>CC:</strong> {cc_emails}</p>' if cc_emails else ''}
        <p><strong>Sent at:</strong> {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}</p>
        <p>If you received this email, your email settings are working correctly!</p>
        <hr>
        <p><small>Email sent from: {Config.EMAIL_SENDER}</small></p>
        """
        
        # Prepare recipient list
        recipients = [recipient_email]
        if cc_emails:
            cc_list = [email.strip() for email in cc_emails.split(',') if email.strip()]
            recipients.extend(cc_list)
        
        # Send test email (using existing email service)
        success = EmailService.send_immediate_email(recipients, subject, body)
        
        if success:
            logger.info(f"Test email sent successfully to {recipients}")
            
            # Log to audit system
            try:
                from app.services.audit_service import AuditService
                AuditService.log_event(
                    event_type=AuditService.EVENT_TYPES['TEST_EMAIL'],
                    performed_by="User",
                    description=f"Test email sent successfully to {recipient_email}",
                    status=AuditService.STATUS_SUCCESS,
                    details={
                        "recipient": recipient_email,
                        "cc_emails": cc_emails,
                        "sender": Config.EMAIL_SENDER
                    }
                )
            except Exception as audit_error:
                logger.warning(f"Failed to log test email to audit system: {audit_error}")
            
            return jsonify({'message': f'Test email sent successfully to {recipient_email}!'}), 200
        else:
            logger.error("Failed to send test email")
            
            # Log failure to audit system
            try:
                from app.services.audit_service import AuditService
                AuditService.log_event(
                    event_type=AuditService.EVENT_TYPES['TEST_EMAIL'],
                    performed_by="User",
                    description=f"Failed to send test email to {recipient_email}",
                    status=AuditService.STATUS_FAILED,
                    details={
                        "recipient": recipient_email,
                        "error": "Email sending failed"
                    }
                )
            except Exception as audit_error:
                logger.warning(f"Failed to log failed test email to audit system: {audit_error}")
            
            return jsonify({'error': 'Failed to send test email. Please check your Mailjet API credentials and email configuration.'}), 500
            
    except ImportError:
        logger.error("EmailService not available")
        return jsonify({'error': 'Email service not available.'}), 500
    except Exception as e:
        logger.error(f"Error sending test email: {str(e)}")
        return jsonify({'error': f'Error sending test email: {str(e)}'}), 500


# Equipment History API Routes

@api_bp.route('/equipment/<equipment_type>/<equipment_id>/history', methods=['GET'])
@permission_required(['equipment_ppm_read', 'equipment_ocm_read'])
def get_equipment_history(equipment_type, equipment_id):
    """Get history notes for a specific equipment."""
    try:
        if equipment_type not in ['ppm', 'ocm']:
            return jsonify({'error': 'Invalid equipment type'}), 400

        history_notes = HistoryService.get_equipment_history(equipment_id, equipment_type)

        # Convert to dict for JSON response
        history_data = []
        for note in history_notes:
            note_dict = note.model_dump()
            # Add relative URLs for attachments
            for attachment in note_dict.get('attachments', []):
                attachment['download_url'] = f"/api/history/attachment/{attachment['id']}/download"
            history_data.append(note_dict)

        return jsonify({
            'success': True,
            'history': history_data,
            'count': len(history_data)
        })

    except Exception as e:
        logger.error(f"Error getting equipment history: {e}")
        return jsonify({'error': 'Failed to retrieve equipment history'}), 500


@api_bp.route('/equipment/<equipment_type>/<equipment_id>/history', methods=['POST'])
@permission_required(['equipment_ppm_write', 'equipment_ocm_write'])
def add_equipment_history(equipment_type, equipment_id):
    """Add a new history note to equipment."""
    try:
        if equipment_type not in ['ppm', 'ocm']:
            return jsonify({'error': 'Invalid equipment type'}), 400

        if not current_user.is_authenticated:
            return jsonify({'error': 'Authentication required'}), 401

        # Get note text from request
        data = request.get_json()
        if not data or not data.get('note_text'):
            return jsonify({'error': 'Note text is required'}), 400

        # Create history note
        note_data = HistoryNoteCreate(
            equipment_id=equipment_id,
            equipment_type=equipment_type,
            author_id=current_user.username,
            author_name=current_user.username,  # Could be enhanced with display name
            note_text=data['note_text']
        )

        history_note = HistoryService.create_history_note(note_data)
        if not history_note:
            return jsonify({'error': 'Failed to create history note'}), 500

        # Log audit event
        from app.services.audit_service import log_equipment_action
        log_equipment_action(
            'History Added',
            equipment_type.upper(),
            equipment_id,
            current_user.username
        )

        return jsonify({
            'success': True,
            'message': 'History note added successfully',
            'note': history_note.model_dump()
        }), 201

    except Exception as e:
        logger.error(f"Error adding equipment history: {e}")
        return jsonify({'error': 'Failed to add history note'}), 500


@api_bp.route('/history/<note_id>/attachment', methods=['POST'])
@permission_required(['equipment_ppm_write', 'equipment_ocm_write'])
def add_history_attachment(note_id):
    """Add an attachment to a history note."""
    try:
        if not current_user.is_authenticated:
            return jsonify({'error': 'Authentication required'}), 401

        # Check if file was uploaded
        if 'file' not in request.files:
            return jsonify({'error': 'No file uploaded'}), 400

        file = request.files['file']
        if file.filename == '':
            return jsonify({'error': 'No file selected'}), 400

        # Add attachment to note
        attachment = HistoryService.add_attachment_to_note(note_id, file, current_user.username)
        if not attachment:
            return jsonify({'error': 'Failed to add attachment'}), 500

        return jsonify({
            'success': True,
            'message': 'Attachment added successfully',
            'attachment': attachment.model_dump()
        }), 201

    except Exception as e:
        logger.error(f"Error adding history attachment: {e}")
        return jsonify({'error': 'Failed to add attachment'}), 500


@api_bp.route('/history/attachment/<attachment_id>/download', methods=['GET'])
@permission_required(['equipment_ppm_read', 'equipment_ocm_read'])
def download_history_attachment(attachment_id):
    """Download a history attachment."""
    try:
        # Find the attachment in all history notes
        all_history = HistoryService.get_all_history()

        for note in all_history:
            attachment = note.get_attachment_by_id(attachment_id)
            if attachment:
                # Convert relative path to absolute path
                from pathlib import Path
                if os.path.isabs(attachment.file_path):
                    file_path = attachment.file_path
                else:
                    # Handle relative paths stored in database
                    relative_path = attachment.file_path

                    # Normalize path separators (handle both / and \)
                    relative_path = relative_path.replace('\\', '/')

                    # The file_path in database already includes 'app/' prefix, so use it directly
                    file_path = os.path.join(os.getcwd(), relative_path)

                # Check if file exists
                if not os.path.exists(file_path):
                    logger.error(f"Attachment file not found: {file_path}")
                    logger.error(f"Original file_path from database: {attachment.file_path}")
                    return jsonify({'error': 'File not found'}), 404

                logger.info(f"Sending attachment file: {file_path}")
                # Send file
                from flask import send_file
                return send_file(
                    file_path,
                    as_attachment=True,
                    download_name=attachment.original_filename,
                    mimetype=attachment.mime_type
                )

        return jsonify({'error': 'Attachment not found'}), 404

    except Exception as e:
        logger.error(f"Error downloading attachment: {e}")
        return jsonify({'error': 'Failed to download attachment'}), 500


@api_bp.route('/history/<note_id>', methods=['PUT'])
@permission_required(['equipment_ppm_write', 'equipment_ocm_write'])
def update_history_note(note_id):
    """Update a history note."""
    try:
        if not current_user.is_authenticated:
            return jsonify({'error': 'Authentication required'}), 401

        # Get the existing note first
        existing_note = HistoryService.get_history_note(note_id)
        if not existing_note:
            return jsonify({'error': 'History note not found'}), 404

        # Check if user can modify this note
        if not HistoryService.can_user_modify_note(existing_note, current_user.username, getattr(current_user, 'role', None)):
            return jsonify({'error': 'You do not have permission to edit this note'}), 403

        # Get update data from request
        data = request.get_json()
        if not data or not data.get('note_text'):
            return jsonify({'error': 'Note text is required'}), 400

        # Create update data
        try:
            update_data = HistoryNoteUpdate(
                note_text=data['note_text'],
                modified_by=current_user.username,
                modified_by_name=current_user.username  # Could be enhanced with display name
            )
        except ValueError as e:
            return jsonify({'error': f'Validation error: {str(e)}'}), 400

        # Update the note
        updated_note = HistoryService.update_history_note(note_id, update_data)
        if not updated_note:
            return jsonify({'error': 'Failed to update history note'}), 500

        return jsonify({
            'success': True,
            'message': 'History note updated successfully',
            'note': updated_note.model_dump()
        })

    except Exception as e:
        logger.error(f"Error updating history note: {e}")
        return jsonify({'error': 'Failed to update history note'}), 500


@api_bp.route('/history/<note_id>', methods=['DELETE'])
@permission_required(['equipment_ppm_write', 'equipment_ocm_write'])
def delete_history_note(note_id):
    """Delete a history note."""
    try:
        if not current_user.is_authenticated:
            return jsonify({'error': 'Authentication required'}), 401

        # Get note details for audit log and permission check
        note = HistoryService.get_history_note(note_id)
        if not note:
            return jsonify({'error': 'History note not found'}), 404

        # Check if user can modify this note
        if not HistoryService.can_user_modify_note(note, current_user.username, getattr(current_user, 'role', None)):
            return jsonify({'error': 'You do not have permission to delete this note'}), 403

        # Delete the note
        success = HistoryService.delete_history_note(note_id)
        if not success:
            return jsonify({'error': 'Failed to delete history note'}), 500

        # Log audit event
        from app.services.audit_service import log_equipment_action
        log_equipment_action(
            'History Deleted',
            note.equipment_type.upper(),
            note.equipment_id,
            current_user.username
        )

        return jsonify({
            'success': True,
            'message': 'History note deleted successfully'
        })

    except Exception as e:
        logger.error(f"Error deleting history note: {e}")
        return jsonify({'error': 'Failed to delete history note'}), 500
