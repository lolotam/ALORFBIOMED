"""
Data service for managing equipment maintenance data.
"""
import json
import logging
import io
import csv
from pathlib import Path
from typing import List, Dict, Any, Optional, Literal, Union, TextIO, get_args
from datetime import datetime, date, timedelta

from dateutil.relativedelta import relativedelta
import pandas as pd
from pydantic import ValidationError

from app.config import Config
from app.models.ppm import PPMEntry
from app.models.ocm import OCMEntry


logger = logging.getLogger(__name__)


class DataService:
    """Service for managing equipment maintenance data."""
    @staticmethod
    def ensure_data_files_exist():
        """Ensure data directory and files exist."""
        logger.debug("Ensuring data files exist")
        data_dir = Path(Config.DATA_DIR)
        logger.debug(f"Using data directory: {data_dir}")
        data_dir.mkdir(exist_ok=True)

        ppm_path = Path(Config.PPM_JSON_PATH)
        ocm_path = Path(Config.OCM_JSON_PATH)

        logger.debug(f"Checking PPM data file: {ppm_path}")
        if not ppm_path.exists():
            logger.info(f"Creating new PPM data file: {ppm_path}")
            with open(ppm_path, 'w') as f:
                json.dump([], f)

        logger.debug(f"Checking OCM data file: {ocm_path}")
        if not ocm_path.exists():
            logger.info(f"Creating new OCM data file: {ocm_path}")
            with open(ocm_path, 'w') as f:
                json.dump([], f)

        DataService.ensure_settings_file_exists() # Ensure settings file also exists

    @staticmethod
    def ensure_settings_file_exists():
        """Ensure settings.json file exists with default values."""
        settings_path = Path(Config.SETTINGS_JSON_PATH)
        logger.debug(f"Checking existence of settings file: {settings_path}")
        if not settings_path.exists():
            logger.info(f"Settings file not found. Creating new settings file: {settings_path}")
            default_settings = {
                "email_notifications_enabled": True,
                "email_reminder_interval_minutes": 60,
                "recipient_email": "",
                "push_notifications_enabled": False, # Default for push notifications
                "push_notification_interval_minutes": 60 # Default interval for push
            }
            try:
                with open(settings_path, 'w') as f:
                    json.dump(default_settings, f, indent=2)
                logger.info(f"Successfully created settings file {settings_path} with defaults: {default_settings}")
            except IOError as e:
                logger.error(f"IOError creating settings file {settings_path}: {e}", exc_info=True)
                # Depending on recovery strategy, you might want to raise this
            except Exception as e:
                logger.error(f"Unexpected error creating settings file {settings_path}: {e}", exc_info=True)
        else:
            logger.debug(f"Settings file {settings_path} already exists.")

    @staticmethod
    def load_settings() -> Dict[str, Any]:
        """Load settings from settings.json file."""
        logger.debug("Attempting to load settings.")
        DataService.ensure_settings_file_exists() # Make sure it exists before loading

        settings_path = Path(Config.SETTINGS_JSON_PATH)
        default_settings = {
            "email_notifications_enabled": True,
            "email_reminder_interval_minutes": 60,
            "recipient_email": "",
            "push_notifications_enabled": False,
            "push_notification_interval_minutes": 60
        }

        try:
            logger.debug(f"Reading settings from file: {settings_path}")
            with open(settings_path, 'r') as f:
                content = f.read()
                if not content.strip(): # Check if content is empty or just whitespace
                    logger.warning(f"Settings file {settings_path} is empty. Returning default settings: {default_settings}")
                    return default_settings.copy()

                settings = json.loads(content)
                logger.info(f"Successfully loaded settings from {settings_path}: {settings}")
                # Ensure essential keys are present, otherwise merge with defaults
                # This handles cases where the file might exist but be partially corrupted or missing keys
                final_settings = default_settings.copy()
                final_settings.update(settings) # Overwrite defaults with loaded settings
                if final_settings != settings:
                    logger.warning(f"Loaded settings were missing some keys. Merged with defaults: {final_settings}")
                return final_settings
        except FileNotFoundError:
            # This should ideally be caught by ensure_settings_file_exists, but as a robust fallback:
            logger.error(f"Settings file {settings_path} not found despite check. Returning default settings: {default_settings}", exc_info=True)
            return default_settings.copy()
        except json.JSONDecodeError:
            logger.error(f"Error decoding JSON from {settings_path}. File content might be corrupted. Returning default settings: {default_settings}", exc_info=True)
            return default_settings.copy()
        except Exception as e:
            logger.error(f"Unexpected error loading settings from {settings_path}: {e}. Returning default settings: {default_settings}", exc_info=True)
            return default_settings.copy()

    @staticmethod
    def save_settings(settings_data: Dict[str, Any]):
        """Save settings to settings.json file.

        Args:
            settings_data: Dictionary containing settings to save.
        """
        settings_path = Path(Config.SETTINGS_JSON_PATH)
        logger.info(f"Attempting to save settings to {settings_path}. Data: {settings_data}")
        try:
            DataService.ensure_settings_file_exists() # Ensure directory exists and file can be created if needed
            with open(settings_path, 'w') as f:
                json.dump(settings_data, f, indent=2)
            logger.info(f"Settings saved successfully to {settings_path}.")
        except IOError as e:
            logger.error(f"IOError saving settings to {settings_path}: {e}", exc_info=True)
            raise ValueError("Failed to save settings due to IO error.") from e
        except Exception as e:
            logger.error(f"Unexpected error saving settings to {settings_path}: {e}", exc_info=True)
            raise ValueError("Failed to save settings due to an unexpected error.") from e

    @staticmethod
    def load_data(data_type: Literal['ppm', 'ocm', 'training']) -> List[Dict[str, Any]]:
        """Load data from JSON file.

        Args:
            data_type: Type of data to load ('ppm', 'ocm', or 'training')

        Returns:
            List of data entries
        """
        logger.debug("Starting load_data method with data_type='%s'", data_type)

        try:
            logger.debug("Calling DataService.ensure_data_files_exist()")
            DataService.ensure_data_files_exist()

            logger.debug("Determining file path based on data_type")
            if data_type == 'ppm':
                file_path = Config.PPM_JSON_PATH
                logger.debug("Selected PPM file path: %s", file_path)
            elif data_type == 'ocm':
                file_path = Config.OCM_JSON_PATH
                logger.debug("Selected OCM file path: %s", file_path)
            else:  # training
                file_path = Path(Config.DATA_DIR) / "training.json"
                logger.debug("Selected Training file path: %s", file_path)

            logger.debug("Opening file for reading: %s", file_path)
            with open(file_path, 'r') as f:
                logger.debug("Reading content from file: %s", file_path)
                content = f.read()

                logger.debug("Checking if file content is empty")
                if not content:
                    logger.debug("File is empty. Returning an empty list.")
                    return []

                logger.debug("Attempting to decode JSON content")
                try:
                    data = json.loads(content)
                except json.JSONDecodeError as e:
                    logger.error(f"Error decoding JSON from {file_path}: {str(e)}. Returning empty list.")
                    return []

                logger.debug("Successfully decoded JSON. Data type: %s", type(data))
                logger.debug("Loaded data sample (first 2 items): %s", data[:2] if isinstance(data, list) else data)

                logger.debug("Returning loaded data with %d entries", len(data) if isinstance(data, list) else 0)
                return data

        except FileNotFoundError:
            logger.warning(f"Data file {file_path} not found. Returning empty list.")
            return []
        except Exception as e:
            logger.error(f"Unexpected error loading {data_type} data from {file_path}: {str(e)}. Returning empty list.")
            return []
    
    @staticmethod
    def save_data(data: List[Dict[str, Any]], data_type: Literal['ppm', 'ocm', 'training']):
        """Save data to JSON file.

        Args:
            data: List of data entries to save
            data_type: Type of data to save ('ppm', 'ocm', or 'training')
        """
        try:
            DataService.ensure_data_files_exist()

            if data_type == 'ppm':
                file_path = Config.PPM_JSON_PATH
            elif data_type == 'ocm':
                file_path = Config.OCM_JSON_PATH
            else:  # training
                file_path = Path(Config.DATA_DIR) / "training.json"
                
            with open(file_path, 'w') as f:
                json.dump(data, f, indent=2)
        except IOError as e:
            logger.error(f"IOError saving {data_type} data to {file_path}: {str(e)}")
            # Potentially re-raise a custom exception or handle as critical
            raise ValueError(f"Failed to save {data_type} data due to IO error.") from e
        except Exception as e:
            logger.error(f"Unexpected error saving {data_type} data to {file_path}: {str(e)}")
            raise ValueError(f"Failed to save {data_type} data due to an unexpected error.") from e

    # --- Push Subscription Management ---
    @staticmethod
    def get_push_subscriptions_path() -> Path:
        """Returns the path to the push_subscriptions.json file."""
        return Path(Config.DATA_DIR) / "push_subscriptions.json"

    @staticmethod
    def ensure_push_subscriptions_file_exists():
        """Ensure push_subscriptions.json file exists."""
        subscriptions_path = DataService.get_push_subscriptions_path()
        if not subscriptions_path.exists():
            logger.info(f"Creating new push subscriptions file: {subscriptions_path}")
            with open(subscriptions_path, 'w') as f:
                json.dump([], f) # Initialize with an empty list

    @staticmethod
    def load_push_subscriptions() -> List[Dict[str, Any]]:
        """Load push subscriptions from push_subscriptions.json."""
        DataService.ensure_push_subscriptions_file_exists()
        subscriptions_path = DataService.get_push_subscriptions_path()
        try:
            with open(subscriptions_path, 'r') as f:
                content = f.read()
                if not content.strip():
                    return []
                subscriptions = json.loads(content)
                if not isinstance(subscriptions, list): # Ensure it's a list
                    logger.warning(f"Push subscriptions file {subscriptions_path} does not contain a list. Resetting.")
                    return []
                return subscriptions
        except (FileNotFoundError, json.JSONDecodeError) as e:
            logger.error(f"Error loading push subscriptions from {subscriptions_path}: {e}. Returning empty list.", exc_info=True)
            return []

    @staticmethod
    def save_push_subscriptions(subscriptions: List[Dict[str, Any]]):
        """Save push subscriptions to push_subscriptions.json."""
        DataService.ensure_push_subscriptions_file_exists()
        subscriptions_path = DataService.get_push_subscriptions_path()
        try:
            with open(subscriptions_path, 'w') as f:
                json.dump(subscriptions, f, indent=2)
            logger.info(f"Push subscriptions saved successfully to {subscriptions_path}.")
        except IOError as e:
            logger.error(f"IOError saving push subscriptions to {subscriptions_path}: {e}", exc_info=True)
            raise ValueError("Failed to save push subscriptions due to IO error.") from e

    @staticmethod
    def add_push_subscription(subscription_info: Dict[str, Any]):
        """Adds a new push subscription if it doesn't already exist."""
        subscriptions = DataService.load_push_subscriptions()
        # Assuming subscription_info contains an 'endpoint' field that is unique
        endpoint = subscription_info.get("endpoint")
        if not endpoint:
            logger.warning("Attempted to add push subscription without an endpoint.")
            return

        exists = any(sub.get("endpoint") == endpoint for sub in subscriptions)
        if not exists:
            subscriptions.append(subscription_info)
            DataService.save_push_subscriptions(subscriptions)
            logger.info(f"Added new push subscription: {endpoint}")
        else:
            logger.info(f"Push subscription already exists: {endpoint}")

    @staticmethod
    def remove_push_subscription(endpoint_to_remove: str):
        """Removes a push subscription by its endpoint."""
        subscriptions = DataService.load_push_subscriptions()
        updated_subscriptions = [sub for sub in subscriptions if sub.get("endpoint") != endpoint_to_remove]

        if len(updated_subscriptions) < len(subscriptions):
            DataService.save_push_subscriptions(updated_subscriptions)
            logger.info(f"Removed push subscription: {endpoint_to_remove}")
        else:
            logger.info(f"Push subscription not found for removal: {endpoint_to_remove}")

    # --- End Push Subscription Management ---


    @staticmethod
    def calculate_status(entry_data: Dict[str, Any], data_type: Literal['ppm', 'ocm']) -> Literal["Upcoming", "Overdue", "Maintained"]:
        """
        Calculates the status of a PPM or OCM entry.
        """
        today = datetime.now().date()

        if data_type == 'ppm':
            today_date = datetime.now().date()
            is_overdue = False  # Becomes true if any past quarter_date has no engineer

            # Variables to summarize quarter states
            num_past_due_quarters_total = 0  # Count of quarters with date < today
            num_past_due_quarters_maintained = 0  # Count of past_due quarters with an engineer
            num_future_quarters = 0  # Count of quarters with date >= today
            # has_any_valid_quarter_date = False # Not strictly needed for the final logic flow with current defaults

            quarter_keys = ['PPM_Q_I', 'PPM_Q_II', 'PPM_Q_III', 'PPM_Q_IV']

            for q_key in quarter_keys:
                quarter_info = entry_data.get(q_key, {})
                # Ensure quarter_info is a dict, useful if data is malformed (though Pydantic should handle)
                if not isinstance(quarter_info, dict): quarter_info = {}

                quarter_date_str = quarter_info.get('quarter_date')
                engineer = quarter_info.get('engineer', "")
                engineer_name = engineer.strip() if engineer else ""  # Safe handling of None values

                if not quarter_date_str:
                    continue  # Skip this quarter if no date is specified

                try:
                    current_quarter_date = datetime.strptime(quarter_date_str, '%d/%m/%Y').date()
                    # has_any_valid_quarter_date = True # A valid date was found and parsed
                except ValueError:
                    logger.warning(
                        f"Invalid quarter_date format for PPM entry {entry_data.get('SERIAL', 'N/A')}, "
                        f"quarter {q_key}: '{quarter_date_str}'. Skipping this date for status calc."
                    )
                    continue  # Skip if date is invalid

                if current_quarter_date < today_date:
                    num_past_due_quarters_total += 1
                    if engineer_name:  # Check if engineer string is not empty
                        num_past_due_quarters_maintained += 1
                    else:
                        is_overdue = True  # A past due quarter is not maintained
                else:  # current_quarter_date >= today_date
                    num_future_quarters += 1

            # --- Determine final status ---
            if is_overdue:
                return "Overdue"

            # If not overdue, check for Maintained or Upcoming
            if num_future_quarters > 0:
                # If there's any future work, and it's not overdue, it's Upcoming.
                # This implies any past work (if existing) was maintained.
                return "Upcoming"

            # No future quarters. All scheduled work is in the past (or no work scheduled).
            # And not 'Overdue', so all past work (if any) must have been maintained.
            if num_past_due_quarters_total > 0:
                # There was past work, and it's all maintained (since not 'Overdue').
                # This also implies num_past_due_quarters_maintained == num_past_due_quarters_total
                return "Maintained"

            # Default cases:
            # 1. No future quarters, no past due quarters (e.g., all dates were invalid, or no dates at all).
            #    This means has_any_valid_quarter_date would be False if we tracked it.
            # In these scenarios, "Upcoming" seems a safe default.
            return "Upcoming"

        elif data_type == 'ocm':
            next_maintenance_str = entry_data.get("Next_Maintenance")
            service_date_str = entry_data.get("Service_Date") # Assuming Service_Date means it was maintained

            if not next_maintenance_str:
                return "Upcoming" # Or some other default if no maintenance date

            try:
                next_maintenance_date = datetime.strptime(next_maintenance_str, '%d/%m/%Y').date()
            except ValueError:
                logger.warning(f"Invalid Next_Maintenance date format for {entry_data.get('SERIAL')}: {next_maintenance_str}")
                return "Upcoming" # Default status if date is invalid

            # If there's a service date, and it's on or after the next maintenance, consider it Maintained.
            # Or if service date is recent enough (e.g. within the last year, assuming annual cycle).
            # This logic can be complex.
            if service_date_str:
                try:
                    service_date = datetime.strptime(service_date_str, '%d/%m/%Y').date()
                    # Example: Maintained if serviced after or on the next maintenance due date,
                    # or if serviced recently (e.g. within the last maintenance cycle period if known)
                    if service_date >= next_maintenance_date: # This might not be the right condition
                        return "Maintained"
                    # A more robust check: if service_date is after the *previous* theoretical maintenance date
                    # and before or on the *next* one.
                    # For simplicity now: if Next_Maintenance is in future, and we had a service date,
                    # it's complex to know if it's "Maintained" for the *next* cycle yet.
                    # Let's assume if Next_Maintenance is in the future, it's "Upcoming" unless service date is very recent.
                except ValueError:
                    logger.warning(f"Invalid Service_Date format for {entry_data.get('SERIAL')}: {service_date_str}")

            if next_maintenance_date < today:
                return "Overdue"
            else:
                return "Upcoming"

        return "Upcoming" # Default fallback

    @staticmethod
    def _calculate_ppm_quarter_dates(installation_date_str: Optional[str]) -> List[Optional[str]]:
        """
        Calculates four quarterly PPM dates.
        Q1 is 3 months after installation_date_str or today if not provided/invalid.
        Q2, Q3, Q4 are 3 months after the previous quarter.
        Returns dates as DD/MM/YYYY strings.
        """
        base_date = None
        if installation_date_str:
            try:
                base_date = datetime.strptime(installation_date_str, '%d/%m/%Y').date()
            except ValueError:
                logger.warning(f"Invalid Installation_Date format '{installation_date_str}'. Using today for PPM quarter calculation.")
                base_date = datetime.today().date()
        else:
            base_date = datetime.today().date()

        q_dates = []
        current_q_date = base_date
        for _ in range(4):
            current_q_date += relativedelta(months=3)
            q_dates.append(current_q_date.strftime('%d/%m/%Y'))
        return q_dates

    @staticmethod
    def _ensure_unique_serial(data: List[Dict[str, Any]], new_entry: Dict[str, Any], data_type: Literal['ppm', 'ocm'], exclude_serial: Optional[str] = None):
        """Ensure Serial/SERIAL is unique in the data."""
        serial_key = 'SERIAL' if data_type == 'ppm' else 'Serial'
        serial = new_entry.get(serial_key)
        if not serial:
            raise ValueError(f"{serial_key} cannot be empty.")

        if exclude_serial and serial == exclude_serial:
            return

        count = sum(1 for entry in data if entry.get(serial_key) == serial)
        if count >= 1:
            raise ValueError(f"Duplicate {serial_key} detected: {serial}")

    @staticmethod
    def reindex(data: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Reindex entries after deletion or reordering.
        
        Args:
            data: List of entries to reindex
            
        Returns:
            List of reindexed entries with sequential NO values (1, 2, 3, ...)
        """
        logger.debug(f"Reindexing {len(data)} entries with sequential NO values")
        for i, entry in enumerate(data, start=1):
            entry['NO'] = i
            serial_key = 'SERIAL' if 'SERIAL' in entry else 'Serial'
            logger.debug(f"Set NO={i} for entry with {serial_key}: {entry.get(serial_key)}")
        logger.info(f"Successfully reindexed {len(data)} entries with NO values 1-{len(data)}")
        return data

    @staticmethod
    def add_entry(data_type: Literal['ppm', 'ocm'], entry: Dict[str, Any]) -> Dict[str, Any]:
        """Add a new entry to the data.
        
        Args:
            data_type: Type of data to add entry to ('ppm' or 'ocm')
            entry: Entry data to add
            
        Returns:
            Added entry with assigned NO
        """
        logger.debug("Starting add_entry function.")
        logger.debug(f"Received data_type: {data_type}")
        logger.debug(f"Received entry: {entry}")

        try:
            # Create copy of entry to avoid modifying original
            entry_copy = entry.copy()
            logger.debug(f"Created copy of entry: {entry_copy}")

            # Remove NO if present (we'll calculate it)
            entry_copy.pop('NO', None)
            logger.debug(f"After removing 'NO': {entry_copy}")

            # Load existing data to calculate new NO
            all_data = DataService.load_data(data_type)
            new_no = len(all_data) + 1
            logger.debug(f"Calculated new NO: {new_no}")

            # Add NO to entry_copy before validation
            entry_copy['NO'] = new_no
            logger.debug(f"Added NO to entry: {entry_copy}")

            if 'Status' in entry_copy and entry_copy['Status']:
                logger.debug(f"Using provided Status: {entry_copy['Status']}")
            else:
                # Calculate Status if not provided or empty
                calculated_status = DataService.calculate_status(entry_copy, data_type)
                entry_copy['Status'] = calculated_status
                logger.debug(f"Calculated Status: {calculated_status}")

            # Process and validate the entry
            if data_type == 'ppm':
                logger.debug("Processing PPM entry...")
                # PPM specific processing
                if isinstance(entry_copy.get('Status'), str) and not entry_copy['Status'].strip():
                    entry_copy['Status'] = None

                # Process PPM quarter fields
                for quarter_key in ['PPM_Q_I', 'PPM_Q_II', 'PPM_Q_III', 'PPM_Q_IV']:
                    if isinstance(entry_copy.get(quarter_key), str):
                        entry_copy[quarter_key] = {
                            'engineer': entry_copy[quarter_key]
                        }
                    elif isinstance(entry_copy.get(quarter_key), dict):
                        entry_copy[quarter_key].setdefault('engineer', None)
                        logger.debug(f"Ensured 'engineer' key in {quarter_key}: {entry_copy[quarter_key]}")

                logger.debug(f"Final entry_copy before PPM validation: {entry_copy}")
                validated_entry_model = PPMEntry(**entry_copy)
            else:
                logger.debug("Processing OCM entry...")
                logger.debug(f"Final entry_copy before OCM validation: {entry_copy}")
                validated_entry_model = OCMEntry(**entry_copy)

            validated_entry = validated_entry_model.model_dump()
            logger.debug(f"Validated entry after model dump: {validated_entry}")

            # Ensure serial is unique
            DataService._ensure_unique_serial(all_data, validated_entry, data_type)

            # Add to data at the beginning (new records appear at top)
            all_data.insert(0, validated_entry)
            logger.debug(f"Added entry to beginning of data. New total: {len(all_data)}")

            # Save updated data
            DataService.save_data(all_data, data_type)
            logger.info(f"Successfully added new {data_type} entry with NO: {new_no}")

            return validated_entry

        except ValidationError as e:
            logger.error(f"Validation error adding {data_type} entry: {str(e)}")
            raise ValueError(str(e))
        except Exception as e:
            logger.error(f"Error adding {data_type} entry: {str(e)}", exc_info=True)
            raise

    @staticmethod
    def update_entry(data_type: Literal['ppm', 'ocm'], serial: str, updated_data: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """Update an existing entry.

        Args:
            data_type: Type of data to update ('ppm' or 'ocm')
            serial: Serial number of entry to update
            updated_data: New data for the entry

        Returns:
            Updated entry if successful, None if entry not found

        Raises:
            ValueError: If validation fails
        """
        logger.info(f"Attempting to update {data_type} entry with serial: {serial}")
        logger.debug(f"Update data received: {updated_data}")

        try:
            # Load all data
            logger.debug(f"Loading all {data_type} data to find entry with serial {serial}")
            data = DataService.load_data(data_type)
            
            # Find and update the entry
            found = False
            for i, entry in enumerate(data):
                entry_serial = entry.get('Serial', entry.get('SERIAL'))
                logger.debug(f"Comparing entry serial '{entry_serial}' with update serial '{serial}'")
                
                if entry_serial == serial:
                    logger.info(f"Found matching {data_type} entry to update")
                    logger.debug(f"Original entry data: {entry}")
                    
                    # Preserve required fields if not in updated_data
                    if data_type == 'ocm' and 'NO' not in updated_data and 'NO' in entry:
                        logger.debug(f"Preserving NO field from original entry: {entry['NO']}")
                        updated_data['NO'] = entry['NO']
                    
                    # Validate updated data
                    logger.debug(f"Validating updated data for {data_type}: {updated_data}")
                    try:
                        if data_type == 'ppm':
                            # If 'Status' is not in updated_data and 'Status' is in the original entry,
                            # preserve the original 'Status'.
                            if 'Status' not in updated_data and 'Status' in entry:
                                updated_data['Status'] = entry['Status']
                            PPMEntry(**updated_data)
                        else:
                            OCMEntry(**updated_data)
                        logger.debug("Data validation successful")
                    except ValidationError as e:
                        logger.error(f"Validation error for {data_type} update: {str(e)}")
                        raise ValueError(f"Invalid {data_type.upper()} data: {str(e)}")
                    
                    # Update the entry
                    data[i] = updated_data
                    found = True
                    logger.debug(f"Updated entry data: {updated_data}")
                    break
            
            if not found:
                logger.warning(f"No {data_type} entry found with serial {serial} for update")
                return None
            
            # Save the updated data
            logger.info(f"Saving updated {data_type} data")
            DataService.save_data(data, data_type)
            
            logger.info(f"Successfully updated {data_type} entry with serial {serial}")
            return updated_data

        except Exception as e:
            logger.error(f"Error updating {data_type} entry with serial {serial}: {str(e)}", exc_info=True)
            raise

    @staticmethod
    def delete_entry(data_type: Literal['ppm', 'ocm'], SERIAL: str) -> bool:
        """Delete an entry.

        Args:
            data_type: Type of data to delete entry from ('ppm' or 'ocm')
            SERIAL: SERIAL of entry to delete

        Returns:
            True if entry was deleted, False if not found
        """
        logger.info(f"Attempting to delete {data_type} entry with serial: {SERIAL}")
        
        try:
            data = DataService.load_data(data_type)
            initial_len = len(data)
            logger.debug(f"Loaded {initial_len} entries from {data_type} data")
            
            # Handle different serial field names for PPM and OCM
            serial_field = 'SERIAL' if data_type == 'ppm' else 'Serial'
            logger.debug(f"Using serial field name: {serial_field}")
            
            # Find the entry to delete first
            entry_to_delete = None
            entry_index = -1
            
            for i, entry in enumerate(data):
                entry_serial = entry.get(serial_field)
                logger.debug(f"Comparing entry serial '{entry_serial}' with target serial '{SERIAL}'")
                if entry_serial == SERIAL:
                    entry_to_delete = entry
                    entry_index = i
                    break
            
            if entry_to_delete is None:
                logger.warning(f"No {data_type} entry found with serial {SERIAL}")
                return False
                
            logger.info(f"Found {data_type} entry to delete: {entry_to_delete}")
            
            # Remove the entry
            data.pop(entry_index)
            logger.debug(f"Removed entry at index {entry_index}")
            
            # Reindex the remaining entries
            reindexed_data = DataService.reindex(data)
            logger.debug(f"Reindexed remaining {len(reindexed_data)} entries")
            
            # Save the updated data
            DataService.save_data(reindexed_data, data_type)
            logger.info(f"Successfully deleted {data_type} entry with serial {SERIAL}")
            
            return True
            
        except Exception as e:
            logger.error(f"Error deleting {data_type} entry with serial {SERIAL}: {str(e)}", exc_info=True)
            raise

    @staticmethod
    def get_entry(data_type: Literal['ppm', 'ocm'], serial: str) -> Optional[Dict[str, Any]]:
        """Get a single entry by serial number.

        Args:
            data_type: Type of data to search ('ppm' or 'ocm')
            serial: Serial number to search for (can be URL-safe or original format)

        Returns:
            Entry if found, None otherwise
        """
        logger.info(f"Attempting to get {data_type} entry with serial: {serial}")
        try:
            # Load all data
            logger.debug(f"Loading all {data_type} data to search for serial {serial}")
            data = DataService.load_data(data_type)

            # Try URL-safe serial lookup first
            from app.utils.url_utils import find_equipment_by_url_safe_serial

            logger.debug(f"Searching for entry with serial {serial} in {len(data)} {data_type} entries using URL-safe lookup")
            found_entry = find_equipment_by_url_safe_serial(serial, data)

            if found_entry:
                logger.info(f"Found matching {data_type} entry for serial {serial} using URL-safe lookup")
                logger.debug(f"Entry data: {found_entry}")
                return found_entry

            # Fallback to original direct matching for backward compatibility
            logger.debug(f"URL-safe lookup failed, trying direct serial matching")
            for entry in data:
                entry_serial = entry.get('Serial', entry.get('SERIAL'))  # Handle both field names
                logger.debug(f"Comparing entry serial '{entry_serial}' with search serial '{serial}'")
                if entry_serial == serial:
                    logger.info(f"Found matching {data_type} entry for serial {serial} using direct match")
                    logger.debug(f"Entry data: {entry}")
                    return entry

            logger.warning(f"No {data_type} entry found with serial {serial}")
            return None

        except Exception as e:
            logger.error(f"Error retrieving {data_type} entry with serial {serial}: {str(e)}", exc_info=True)
            return None

    @staticmethod
    def get_all_entries(data_type: Literal['ppm', 'ocm']) -> List[Dict[str, Any]]:
        """Get all entries with history flags and sorted by history status.

        Args:
            data_type: Type of data to get entries from ('ppm' or 'ocm')

        Returns:
            List of all entries, sorted with equipment having history first
        """
        entries = DataService.load_data(data_type)

        # Update history flags for all entries
        DataService._update_all_history_flags(entries, data_type)

        # Sort entries: equipment with history first, then by NO (newest first)
        entries.sort(key=lambda x: (not x.get('has_history', False), -(x.get('NO', 0))))

        return entries

    @staticmethod
    def _update_all_history_flags(entries: List[Dict[str, Any]], data_type: str):
        """Update has_history flags for all entries by checking history data.

        Args:
            entries: List of equipment entries to update
            data_type: Type of data ('ppm' or 'ocm')
        """
        try:
            # Import here to avoid circular imports
            from app.services.history_service import HistoryService

            # Load all history data once
            history_data = HistoryService._load_history_data()

            # Create a set of equipment IDs that have history
            equipment_with_history = set()
            for note in history_data:
                if note.get('equipment_type') == data_type.lower():
                    equipment_with_history.add(note.get('equipment_id'))

            # Update has_history flag for each entry
            serial_field = 'SERIAL' if data_type == 'ppm' else 'Serial'
            for entry in entries:
                equipment_id = entry.get(serial_field)
                entry['has_history'] = equipment_id in equipment_with_history

        except Exception as e:
            logger.error(f"Error updating history flags: {e}")
            # Set all to False if there's an error
            for entry in entries:
                entry['has_history'] = False

    @staticmethod
    def get_entries_paginated(data_type: Literal['ppm', 'ocm'], page: int = 1, per_page: int = 100) -> Dict[str, Any]:
        """Get paginated entries for the specified data type.

        Args:
            data_type: Type of data to retrieve ('ppm' or 'ocm')
            page: Page number (1-based)
            per_page: Number of entries per page

        Returns:
            Dictionary containing:
            - 'entries': List of entries for the current page
            - 'total': Total number of entries
            - 'page': Current page number
            - 'per_page': Entries per page
            - 'total_pages': Total number of pages
            - 'has_prev': Whether there's a previous page
            - 'has_next': Whether there's a next page
            - 'prev_page': Previous page number (None if no previous)
            - 'next_page': Next page number (None if no next)
        """
        logger.debug(f"Getting paginated {data_type} entries - page {page}, per_page {per_page}")
        
        try:
            # Get all data using the same logic as get_all_entries
            entries = DataService.load_data(data_type)
            
            # Update history flags for all entries
            DataService._update_all_history_flags(entries, data_type)
            
            # Sort entries: equipment with history first, then by NO (newest first)
            entries.sort(key=lambda x: (not x.get('has_history', False), -(x.get('NO', 0))))
            
            total_entries = len(entries)
            total_pages = max(1, (total_entries + per_page - 1) // per_page)  # Ceiling division
            
            # Ensure page is within valid range
            page = max(1, min(page, total_pages))
            
            # Calculate start and end indices
            start_idx = (page - 1) * per_page
            end_idx = start_idx + per_page
            
            # Get entries for current page
            page_entries = entries[start_idx:end_idx]
            
            # Calculate pagination info
            has_prev = page > 1
            has_next = page < total_pages
            prev_page = page - 1 if has_prev else None
            next_page = page + 1 if has_next else None
            
            pagination_info = {
                'entries': page_entries,
                'total': total_entries,
                'page': page,
                'per_page': per_page,
                'total_pages': total_pages,
                'has_prev': has_prev,
                'has_next': has_next,
                'prev_page': prev_page,
                'next_page': next_page
            }
            
            logger.debug(f"Successfully retrieved page {page}/{total_pages} with {len(page_entries)} {data_type} entries")
            return pagination_info
            
        except Exception as e:
            logger.error(f"Error getting paginated {data_type} entries: {str(e)}")
            # Return empty pagination info on error
            return {
                'entries': [],
                'total': 0,
                'page': 1,
                'per_page': per_page,
                'total_pages': 1,
                'has_prev': False,
                'has_next': False,
                'prev_page': None,
                'next_page': None
            }

    @staticmethod
    def import_data(data_type: Literal['ppm', 'ocm'], file_stream: TextIO) -> Dict[str, Any]:
        """
        Bulk import data from a CSV file stream.
        'NO' field in CSV is ignored. SERIAL uniqueness is enforced by replacing existing.
        Status is calculated if not provided or invalid.
        """
        logger.info(f"Starting bulk import for data type: {data_type}")
        added_count = 0
        updated_count = 0
        skipped_count = 0
        errors = []

        try:
            logger.debug("Reading CSV file with pandas")
            df = pd.read_csv(file_stream, dtype=str)
            df.fillna('', inplace=True)
            logger.debug(f"CSV columns found: {', '.join(df.columns)}")

            if 'SERIAL' not in df.columns:
                error_msg = "CSV file missing required SERIAL column"
                logger.error(error_msg)
                errors.append(error_msg)
                return {"errors": errors}

            if data_type == 'ppm':
                logger.debug("Processing PPM data")
                # Define expected CSV columns for PPM import
                expected_columns = ['MODEL', 'SERIAL', 'MANUFACTURER', 'Department']
                missing_columns = [col for col in expected_columns if col not in df.columns]
                if missing_columns:
                    error_msg = f"Missing required columns for PPM: {', '.join(missing_columns)}"
                    logger.error(error_msg)
                    errors.append(error_msg)
                    return {"errors": errors}
            else:  # ocm
                logger.debug("Processing OCM data")
                expected_columns = ['MODEL', 'SERIAL', 'MANUFACTURER', 'Service_Date']
                missing_columns = [col for col in expected_columns if col not in df.columns]
                if missing_columns:
                    error_msg = f"Missing required columns for OCM: {', '.join(missing_columns)}"
                    logger.error(error_msg)
                    errors.append(error_msg)
                    return {"errors": errors}

            logger.info(f"Found {len(df)} rows to process")
            current_data = DataService.load_data(data_type)
            logger.debug(f"Loaded {len(current_data)} existing records")
            current_data_map = {entry.get('SERIAL'): entry for entry in current_data}

            processed_data = current_data.copy()  # Start with existing data

            for index, row in df.iterrows():
                try:
                    logger.debug(f"Processing row {index + 1}/{len(df)}")
                    serial = row.get('SERIAL', '').strip()
                    
                    if not serial:
                        logger.warning(f"Skipping row {index + 1}: Empty SERIAL")
                        skipped_count += 1
                        errors.append(f"Row {index + 1}: Empty SERIAL")
                        continue
                    
                    entry_data = row.to_dict()
                    entry_data = {k: str(v).strip() if isinstance(v, str) else v for k, v in entry_data.items()}
                      # First get the Q1 date to base other quarters on
                    q1_date = entry_data.get("PPM_Q_I.date", "")
                    base_date = None
                    if q1_date:
                        try:
                            base_date = datetime.strptime(q1_date, '%d/%m/%Y').date()
                        except ValueError:
                            logger.warning(f"Invalid Q1 date format: {q1_date}")
                            base_date = None
                    
                    if not base_date:
                        # If no valid Q1 date, fall back to installation date or current date
                        installation_date = entry_data.get("Installation_Date", "")
                        if installation_date:
                            try:
                                base_date = datetime.strptime(installation_date, '%d/%m/%Y').date()
                            except ValueError:
                                base_date = datetime.now().date()
                        else:
                            base_date = datetime.now().date()

                    # Calculate quarter dates based on Q1 date
                    q_dates = []
                    current_date = base_date
                    for _ in range(4):
                        if not q_dates:  # First quarter uses actual Q1 date if available
                            q_dates.append(q1_date if q1_date else current_date.strftime('%d/%m/%Y'))
                        else:
                            current_date += relativedelta(months=3)
                            q_dates.append(current_date.strftime('%d/%m/%Y'))

                    # Transform the data to match PPM structure, starting with NO
                    transformed_entry = {
                        "NO": len(processed_data) + 1,  # Add NO at the beginning
                        "Department": entry_data.get("Department", ""),
                        "Name": entry_data.get("Name", ""),
                        "MODEL": entry_data.get("MODEL", ""),
                        "SERIAL": serial,
                        "MANUFACTURER": entry_data.get("MANUFACTURER", ""),
                        "LOG_Number": entry_data.get("LOG_Number", ""),
                        "Installation_Date": entry_data.get("Installation_Date", ""),
                        "Warranty_End": entry_data.get("Warranty_End", "")
                    }

                    # Process PPM quarters
                    transformed_entry["PPM_Q_I"] = {
                        "engineer": entry_data.get("PPM_Q_I.engineer", ""),
                        "quarter_date": q_dates[0]
                    }
                    transformed_entry["PPM_Q_II"] = {
                        "engineer": entry_data.get("PPM_Q_II.engineer", ""),
                        "quarter_date": q_dates[1]
                    }
                    transformed_entry["PPM_Q_III"] = {
                        "engineer": entry_data.get("PPM_Q_III.engineer", ""),
                        "quarter_date": q_dates[2]
                    }
                    transformed_entry["PPM_Q_IV"] = {
                        "engineer": entry_data.get("PPM_Q_IV.engineer", ""),
                        "quarter_date": q_dates[3]
                    }
                    
                    # Calculate Status if not present
                    transformed_entry["Status"] = entry_data.get("Status") or DataService.calculate_status(transformed_entry, data_type)

                    if serial in current_data_map:
                        # Update existing record
                        for i, entry in enumerate(processed_data):
                            if entry.get('SERIAL') == serial:
                                processed_data[i].update(transformed_entry)
                                break
                        logger.debug(f"Updated existing record for SERIAL: {serial}")
                        updated_count += 1
                    else:
                        # Add new record with NO field
                        transformed_entry["NO"] = len(processed_data) + 1
                        processed_data.append(transformed_entry)
                        logger.debug(f"Added new record for SERIAL: {serial}")
                        added_count += 1

                except Exception as row_error:
                    error_msg = f"Error processing row {index + 1}: {str(row_error)}"
                    logger.error(error_msg, exc_info=True)
                    errors.append(error_msg)
                    skipped_count += 1

            # Reindex all data to ensure sequential NO values (1, 2, 3, ...)
            reindexed_data = DataService.reindex(processed_data)
            logger.info(f"Reindexed {len(reindexed_data)} entries with sequential NO values after import")
            
            # Save the updated and reindexed data back to the JSON file
            DataService.save_data(reindexed_data, data_type)

            logger.info(f"Import complete. Added: {added_count}, Updated: {updated_count}, Skipped: {skipped_count}")
            if errors:
                logger.warning(f"Import completed with {len(errors)} errors")

            return {
                "added_count": added_count,
                "updated_count": updated_count,
                "skipped_count": skipped_count,
                "errors": errors
            }

        except Exception as e:
            error_msg = f"Error during import: {str(e)}"
            logger.exception(error_msg)
            errors.append(error_msg)
            return {
                "added_count": added_count,
                "updated_count": updated_count,
                "skipped_count": skipped_count,
                "errors": errors
            }
    @classmethod
    def export_data(cls, data_type: Literal['ppm', 'ocm', 'training']) -> str:
        """Export data to CSV format."""
        logger.debug(f"DataService.export_data called for {data_type}")
        try:
            # Load data from appropriate file
            data = cls.load_data(data_type)
            logger.debug(f"Loaded {len(data) if data else 0} entries for export")
            
            if not data:
                logger.warning(f"No {data_type} data available for export")
                return ""

            # Convert data for export
            from app.services.import_export import ImportExportService
            logger.debug(f"Calling ImportExportService.export_to_csv for {data_type}")
            success, message, csv_content = ImportExportService.export_to_csv(data_type)
            
            if not success:
                logger.error(f"Export failed: {message}")
                return ""
                
            logger.debug(f"Export successful. CSV content length: {len(csv_content)} bytes")
            logger.debug(f"First 200 characters of CSV: {csv_content[:200]}")
            return csv_content
            
        except Exception as e:
            logger.exception(f"Error in export_data for {data_type}: {str(e)}")
            raise

    @staticmethod
    def update_all_ppm_statuses():
        """
        Recalculates and updates the status for all PPM entries in ppm.json.
        Saves the data back to the file if any statuses were changed.
        """
        logger.info("Starting update of all PPM statuses.")
        try:
            all_ppm_data = DataService.load_data('ppm')
            if not all_ppm_data:
                logger.info("No PPM data found to update statuses.")
                return

            statuses_changed_count = 0
            updated_data = []

            for entry in all_ppm_data:
                original_status = entry.get('Status')
                # Ensure entry is mutable for in-place update if needed, or create a copy
                entry_copy = entry.copy()

                new_status = DataService.calculate_status(entry_copy, 'ppm')

                if original_status != new_status:
                    entry_copy['Status'] = new_status
                    statuses_changed_count += 1
                    logger.debug(f"PPM SERIAL {entry_copy.get('SERIAL', 'N/A')}: Status changed from '{original_status}' to '{new_status}'.")

                updated_data.append(entry_copy)

            if statuses_changed_count > 0:
                DataService.save_data(updated_data, 'ppm')
                logger.info(f"Successfully updated statuses for {statuses_changed_count} PPM entries. Data saved.")
            else:
                logger.info("No PPM statuses required updating.")

        except Exception as e:
            logger.error(f"Error during PPM status update process: {str(e)}", exc_info=True)
            # Depending on application design, might want to raise this or handle more gracefully.

    @staticmethod
    def reindex_all_data(data_type: Literal['ppm', 'ocm']) -> bool:
        """
        Reindex all data for a specific data type to ensure sequential NO values.
        
        Args:
            data_type: Type of data to reindex ('ppm' or 'ocm')
            
        Returns:
            bool: True if reindexing was successful, False otherwise
        """
        logger.info(f"Starting reindex of all {data_type} data")
        try:
            # Load existing data
            data = DataService.load_data(data_type)
            logger.debug(f"Loaded {len(data)} {data_type} entries for reindexing")
            
            if not data:
                logger.info(f"No {data_type} data found to reindex")
                return True
            
            # Reindex all entries
            reindexed_data = DataService.reindex(data)
            
            # Save the reindexed data
            DataService.save_data(reindexed_data, data_type)
            
            logger.info(f"Successfully reindexed all {len(reindexed_data)} {data_type} entries with sequential NO values 1-{len(reindexed_data)}")
            return True
            
        except Exception as e:
            logger.error(f"Error reindexing {data_type} data: {str(e)}", exc_info=True)
            return False
