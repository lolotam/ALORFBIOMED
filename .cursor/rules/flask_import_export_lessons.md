# Flask Import/Export System: Lessons Learned and Solutions

## Overview
This document captures critical lessons learned from implementing and troubleshooting the import/export functionality in the Hospital Equipment System, particularly during the migration from JSON to SQLite database.

## Problem Categories

### 1. Import System Architecture Issues

**Problem**: Import functionality calling non-existent DataService methods
- **Symptoms**: `'DataService' object has no attribute '_reindex_entries'` and `save_data()` method errors
- **Root Cause**: Import service designed for file-based system but database service uses different method names

**Solution Applied**:
```python
# Added missing compatibility methods to DataService
@staticmethod
def _reindex_entries(data_type: str) -> None:
    """Static method for compatibility with import system (no-op for database)."""
    pass

# Updated import service to use database methods instead of file operations
```

### 2. Unique Constraint Violations

**Problem**: Import failures due to duplicate data in template files
- **Symptoms**: `UNIQUE constraint failed: equipment.log_number` and `equipment.serial_number`
- **Root Cause**: Template files contained real existing data instead of sample data

**Solution Applied**:
```python
# Added duplicate detection and unique identifier generation
if original_log in existing_log_numbers:
    counter = 1
    new_log = f"{original_log}_IMPORT_{counter}"
    while new_log in existing_log_numbers:
        counter += 1
        new_log = f"{original_log}_IMPORT_{counter}"
    row_dict['Log_Number'] = new_log
```

### 3. Date Parsing Performance Issues

**Problem**: Log flooding with "Could not parse date: N/A" warnings
- **Symptoms**: Thousands of warning messages for N/A date values
- **Root Cause**: Date parsing function not handling N/A values silently

**Solution Applied**:
```python
def _parse_date(self, date_str: str) -> Optional[datetime]:
    """Parse date string with silent N/A handling."""
    if not date_str or date_str.strip().upper() in ['N/A', 'NA', '']:
        return None  # Silent handling for N/A values
    # ... rest of parsing logic
```

### 4. Variable Scope and Initialization Issues

**Problem**: `cannot access local variable 'stats' where it is not associated with a value`
- **Root Cause**: Stats dictionary initialized after potential error conditions
- **Solution**: Early initialization of stats dictionary

### 5. Cache Management After Import

**Problem**: Imported data not immediately visible in frontend
- **Root Cause**: Cache not cleared after import operations
- **Solution Applied**:
```python
# Clear cache after successful import
try:
    from app.routes.views import clear_all_caches
    clear_all_caches(data_type)
    logger.info("Cache cleared after import")
except Exception as e:
    logger.warning(f"Could not clear cache after import: {e}")
```

## Upsert Functionality Implementation

### 6. Upsert Logic for Equipment and Training Records

**User Requirement**: 
- **PPM/OCM**: Update existing records when serial_number already exists
- **Training**: Update existing records when employee_id already exists

**Implementation Strategy**:

#### Equipment Upsert (PPM/OCM)
```python
# Determine key field based on data type for upsert logic
if data_type == 'ppm':
    key_field = 'SERIAL'
elif data_type == 'ocm':
    key_field = 'Serial'

# Create mapping of existing records by key for upsert
existing_records = {entry.get(key_field): entry for entry in current_data if entry.get(key_field)}

# Check if this is an update or insert
is_update = record_key in existing_records

if is_update:
    # Get the existing equipment record and update it
    existing_record = existing_records[record_key]
    equipment_id = existing_record.get('id')
    result = data_service.update_entry(data_type, str(equipment_id), entry)
else:
    # Add as new equipment
    result = data_service.add_equipment(entry, data_type)
```

#### Training Upsert
```python
# For training, use employee_id as the unique key
key_field = 'employee_id'  # Use employee_id for training upserts

# Find existing training record by employee_id
existing_record = existing_records[record_key]
training_id = existing_record.get('id')

if training_id:
    result = data_service.update_entry(data_type, str(training_id), entry)
else:
    result = data_service.add_entry(data_type, entry)
```

#### Enhanced CSV Reading
```python
# Read CSV with utf-8-sig encoding to handle Excel-exported CSVs safely
df = pd.read_csv(file_path, dtype=str, encoding='utf-8-sig')

# Strip whitespace from all string values to avoid issues
for key, value in row_dict.items():
    if isinstance(value, str):
        row_dict[key] = value.strip()
```

#### Import Statistics Tracking
```python
stats = {
    "total_rows": len(df),
    "imported": 0,      # New records added
    "updated": 0,       # Existing records updated
    "skipped": 0,       # Records skipped due to errors
    "errors": 0,        # Total errors encountered
    "skipped_details": [],
    "error_details": []
}
```

### 7. Model Constraints for Upsert

**Equipment Model** (already properly configured):
```python
class Equipment(BaseModel):
    serial_number = Column(String(100), nullable=False, unique=True, index=True)
    log_number = Column(String(100), nullable=False, unique=True, index=True)
```

**Employee Model** (already properly configured):
```python
class Employee(BaseModel):
    employee_id = Column(String(50), nullable=False, unique=True, index=True)
```

**Training Upsert Logic**: Uses employee_id as unique identifier for legacy Training class compatibility.

## Template File Management

### 8. Clean Template Creation

**Problem**: Original templates contained real data causing import conflicts
**Solution**: Created clean sample templates

#### Clean PPM Template
```csv
MANUFACTURER,MODEL,SERIAL,Name,Department,Log_Number,PPM_Q_I_date,PPM_Q_I_engineer
Sample Manufacturer,Sample Model,SAMPLE_SERIAL_001,Sample Equipment 1,Sample Department,SAMPLE_LOG_001,2024-03-15,Sample Engineer
Sample Manufacturer 2,Sample Model 2,SAMPLE_SERIAL_002,Sample Equipment 2,Sample Department 2,SAMPLE_LOG_002,2024-06-15,Sample Engineer 2
```

#### Clean OCM Template
```csv
Department,Name,Model,Serial,Manufacturer,Log_Number,Installation_Date,Service_Date,Warranty_End
Sample Department,Sample Equipment,Sample Model,SAMPLE_SERIAL_003,Sample Manufacturer,SAMPLE_LOG_003,2024-01-01,2024-03-01,2025-01-01
Sample Department 2,Sample Equipment 2,Sample Model 2,SAMPLE_SERIAL_004,Sample Manufacturer 2,SAMPLE_LOG_004,2024-02-01,2024-04-01,2025-02-01
```

#### Clean Training Template
```csv
employee_id,name,department,machine_trainer_assignments,last_trained_date,next_due_date
EMP001,Sample Employee 1,Sample Department 1,"[{""machine"": ""Machine A"", ""trainer"": ""Trainer 1""}]",2024-01-15,2025-01-15
EMP002,Sample Employee 2,Sample Department 2,"[{""machine"": ""Machine B"", ""trainer"": ""Trainer 2""}, {""machine"": ""Machine C"", ""trainer"": ""Trainer 3""}]",2024-02-20,2025-02-20
```

## Best Practices

### Import Error Handling
1. **Wrap each row in try/except** to log specific errors without stopping the entire import
2. **Use .strip() on all string values** to avoid whitespace issues
3. **Handle N/A values consistently** throughout the import process
4. **Provide detailed error reporting** with row numbers and specific error messages

### Performance Optimization
1. **Use utf-8-sig encoding** for Excel compatibility
2. **Clear cache immediately after import** for real-time visibility
3. **Batch process updates** when possible
4. **Log import statistics** for monitoring and troubleshooting

### Data Integrity
1. **Generate unique identifiers** for conflicting log numbers/serial numbers
2. **Validate data before database operations** using Pydantic models
3. **Maintain referential integrity** for foreign key relationships
4. **Handle both insert and update operations** in the same import process

## Error Prevention Checklist

### Before Import:
- [ ] Verify template files contain only sample data
- [ ] Check for unique constraint conflicts
- [ ] Validate CSV encoding (use utf-8-sig for Excel files)
- [ ] Ensure required columns are present

### During Import:
- [ ] Strip whitespace from all string values
- [ ] Handle N/A values appropriately
- [ ] Log detailed error information with row numbers
- [ ] Track import statistics (imported, updated, errors)

### After Import:
- [ ] Clear all relevant caches
- [ ] Verify data visibility in frontend
- [ ] Check import statistics for accuracy
- [ ] Monitor for any constraint violations

## Future Improvements

1. **Batch Processing**: Implement batch updates for better performance with large datasets
2. **Validation Preview**: Show import preview before committing changes
3. **Rollback Capability**: Implement transaction rollback for failed imports
4. **Progress Tracking**: Real-time import progress indicators
5. **Column Mapping**: Allow users to map CSV columns to database fields
6. **Data Transformation**: Built-in data cleaning and transformation rules

---

**Remember**: The upsert functionality provides a seamless way to both import new data and update existing records, eliminating the need for manual data deduplication and ensuring data consistency across the system.

## 8. Upsert Functionality Implementation

### Problem: Duplicate Data on Re-import
**Issue**: When importing the same CSV file multiple times, the system would either skip existing records or create duplicates, leading to data inconsistency.

**User Requirement**: 
- For PPM/OCM: If a serial number already exists, update the existing record
- For Training: If an employee ID already exists, update their training record

### Solution: Comprehensive Upsert Implementation

**Key Changes Made**:

1. **Field Mapping Function**: Created `_map_csv_fields_to_service_format()` to properly convert CSV column names to DataService format:
```python
@staticmethod
def _map_csv_fields_to_service_format(row_dict: Dict[str, Any], data_type: str) -> Dict[str, Any]:
    """Map CSV field names to the format expected by DataService."""
    if data_type == 'ppm':
        field_mapping = {
            'MANUFACTURER': 'manufacturer',
            'MODEL': 'model', 
            'SERIAL': 'serial_number',
            'Name': 'name',
            'Department': 'department',
            'Log_Number': 'log_number',
            # ... other PPM fields
        }
    elif data_type == 'ocm':
        field_mapping = {
            'Department': 'department',
            'Name': 'name',
            'Model': 'model',
            'Serial': 'serial_number',
            # ... other OCM fields
        }
```

2. **Improved Detection Logic**: Enhanced `detect_csv_type()` to be case-insensitive and more flexible:
```python
@staticmethod
def detect_csv_type(columns: List[str]) -> Literal['ppm', 'ocm', 'training', 'unknown']:
    # Strip whitespace and normalize columns for case-insensitive comparison
    columns_normalized = {col.strip().lower() for col in columns}
    
    # PPM detection - look for PPM-specific columns
    ppm_indicators = {'ppm_q_i_date', 'ppm_q_ii_date', 'ppm_q_iii_date', 'ppm_q_iv_date'}
    ppm_basic_fields = {'serial', 'manufacturer', 'model', 'name', 'department'}
    
    # Check if it has PPM quarter indicators OR basic equipment fields
    has_ppm_quarters = any(indicator in columns_normalized for indicator in ppm_indicators)
    has_ppm_basics = ppm_basic_fields.issubset(columns_normalized)
    
    if has_ppm_quarters or (has_ppm_basics and any('ppm' in col for col in columns_normalized)):
        return 'ppm'
```

3. **Fixed Update Logic**: Corrected the update mechanism to use serial numbers (not IDs) for equipment updates:
```python
if is_update:
    # Update existing record
    existing_record = existing_records[record_key]
    
    # For equipment, update_entry expects serial number, not ID
    if data_type in ['ppm', 'ocm']:
        result = data_service.update_entry(data_type, record_key, mapped_data)
    else:  # training
        record_id = existing_record.get('id')
        if record_id:
            result = data_service.update_entry(data_type, str(record_id), mapped_data)
        else:
            result = False
```

4. **Comprehensive Import Statistics**: Enhanced stats tracking to distinguish between imports and updates:
```python
stats = {
    "total_rows": 0,
    "imported": 0,      # New records added
    "updated": 0,       # Existing records updated
    "skipped": 0,       # Records skipped due to errors
    "errors": 0,        # Total errors encountered
    "skipped_details": [],
    "error_details": []
}
```

### Testing Results

**PPM/OCM Upsert Test**:
- ✅ First import: 2 new records imported successfully
- ✅ Second import (same data with updates): 1 new record imported + 2 existing records updated
- ✅ Perfect upsert functionality achieved

**Key Success Metrics**:
- **Detection**: CSV type detection now works case-insensitively
- **Field Mapping**: CSV columns properly mapped to DataService format
- **Upsert Logic**: Existing records updated by serial number, new records added
- **Error Handling**: Comprehensive error reporting with detailed messages
- **Cache Management**: Automatic cache clearing for immediate visibility

### Implementation Notes

**Critical Fixes Applied**:
1. **Serial Number Matching**: Use CSV serial field for existing record detection
2. **DataService Integration**: Proper field name mapping for add_equipment() method
3. **Update Method**: Pass serial number (not ID) to update_entry() for equipment
4. **Error Handling**: Enhanced error messages with row numbers and specific issues

**Performance Considerations**:
- Existing records loaded once at start for efficient lookup
- Field mapping applied per row to handle different CSV formats
- Cache cleared only after successful import to maintain consistency

### Usage Examples

**PPM Import with Upsert**:
```csv
MANUFACTURER,MODEL,SERIAL,Name,Department,Log_Number,PPM_Q_I_date
Test Manufacturer,Test Model,SERIAL_001,Test Equipment,Test Dept,LOG_001,2024-03-15
Updated Manufacturer,Updated Model,SERIAL_001,Updated Equipment,Test Dept,LOG_001,2024-03-20
```
- First import: Creates new record
- Second import: Updates existing record based on SERIAL_001

**OCM Import with Upsert**:
```csv
Department,Name,Model,Serial,Manufacturer,Installation_Date,Service_Date
Test Dept,Test Equipment,Test Model,SERIAL_001,Test Manufacturer,2024-01-01,2024-03-01
Updated Dept,Updated Equipment,Updated Model,SERIAL_001,Updated Manufacturer,2024-01-01,2024-03-15
```
- First import: Creates new record
- Second import: Updates existing record based on Serial SERIAL_001

### Error Prevention

**Common Issues Resolved**:
- ❌ Field name mismatches between CSV and DataService
- ❌ Case sensitivity in column detection
- ❌ Using IDs instead of serial numbers for updates
- ❌ Missing field mapping for different CSV formats
- ❌ Inadequate error reporting for debugging

**Best Practices Established**:
- ✅ Always use serial numbers as unique identifiers for equipment
- ✅ Map CSV field names to DataService format before processing
- ✅ Provide comprehensive error messages with row numbers
- ✅ Clear cache after successful import for immediate visibility
- ✅ Track both new imports and updates in statistics

**Remember**: The upsert functionality now provides seamless data management, allowing users to import new equipment and update existing records in a single operation, eliminating data duplication and ensuring consistency across the Hospital Equipment System. 