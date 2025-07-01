# Flask SQLite Migration: Critical Lessons Learned

This rule captures essential lessons from migrating a Flask application from JSON file storage to SQLite database, including common pitfalls and their solutions based on real troubleshooting experience.

## **Database Migration Issues**

### **Problem 1: Missing Required Fields in Model Migration**
- **Error**: `IntegrityError: NOT NULL constraint failed: equipment.log_number`
- **Cause**: SQLAlchemy models require all non-nullable fields, but migration script wasn't providing them
- **Context**: Equipment model had mandatory fields like `log_number`, `department_id`, `manufacturer_id`

**❌ DON'T: Ignore required model fields**
```python
# This will fail - missing required fields
equipment = Equipment(
    serial_number=serial,
    name=item.get('Name', ''),
    model=item.get('MODEL', '')
    # Missing: log_number, department_id, manufacturer_id
)
```

**✅ DO: Provide all required fields with fallbacks**
```python
equipment = Equipment(
    serial_number=serial,
    name=item.get('Name', '').strip() or 'Unknown Equipment',
    model=item.get('MODEL', '').strip(),
    log_number=item.get('LOG_NUMBER', '') or f"AUTO_{serial}",  # Auto-generate if missing
    department_id=department.id if department else 1,  # Default department
    manufacturer_id=manufacturer.id if manufacturer else 1,  # Default manufacturer
    category_id=category.id if category else None,
    installation_date=self.parse_date(item.get('Installation_Date')),
    warranty_end_date=self.parse_date(item.get('Warranty_End')),
    status=EquipmentStatus.ACTIVE,
    created_at=datetime.now(),
    updated_at=datetime.now()
)
```

### **Problem 2: Enum Value Mismatches**
- **Error**: `ValueError: 'PENDING' is not a valid MaintenanceStatus`
- **Cause**: JSON data used different status values than SQLAlchemy enum definitions
- **Context**: MaintenanceStatus enum didn't include 'PENDING', only 'UPCOMING'

**❌ DON'T: Assume JSON values match enum values**
```python
# This will fail if JSON contains 'PENDING' but enum only has 'UPCOMING'
status = MaintenanceStatus.PENDING  # AttributeError
```

**✅ DO: Map JSON values to correct enum values**
```python
# Map status strings to correct enum values
status_str = quarter_data.get('status')
status = MaintenanceStatus.UPCOMING  # Default
if status_str:
    if status_str.lower() in ['completed', 'done', 'maintained']:
        status = MaintenanceStatus.COMPLETED
    elif status_str.lower() in ['in progress', 'ongoing']:
        status = MaintenanceStatus.IN_PROGRESS
    elif status_str.lower() in ['overdue', 'delayed']:
        status = MaintenanceStatus.OVERDUE
    # Default: UPCOMING for 'pending' or unknown values
```

### **Problem 3: Constructor Parameter Mismatches**
- **Error**: `TypeError: __init__() missing 1 required positional argument: 'maintenance_type'`
- **Cause**: Model constructors changed but migration code wasn't updated
- **Context**: EquipmentCategory required maintenance_type parameter

**❌ DON'T: Use old constructor signatures**
```python
# This will fail - missing required parameter
category = EquipmentCategory(name=category_name)
```

**✅ DO: Check current model constructors and provide all required parameters**
```python
def get_or_create_category(self, session, equipment_name: str, maintenance_type: str):
    category = EquipmentCategory(
        name=category_name,
        maintenance_type=maintenance_type  # Required parameter
    )
    session.add(category)
    session.flush()
    return category
```

## **Missing Service Methods After Migration**

### **Problem 4: Export Methods Not Implemented**
- **Error**: `'DataService' object has no attribute 'export_data'`
- **Cause**: Migration from JSON files removed export functionality without replacement
- **Context**: Views expected export_data method but it was never implemented for SQLite

**❌ DON'T: Leave service methods unimplemented after migration**
```python
# Routes expect this method but it doesn't exist
data_service.export_data('ppm')  # AttributeError
```

**✅ DO: Implement all expected service methods for new backend**
```python
class DataService:
    def export_data(self, data_type: str) -> Dict[str, Any]:
        """Export data based on type."""
        try:
            if data_type == 'ppm':
                return self._export_ppm_data()
            elif data_type == 'ocm':
                return self._export_ocm_data()
            elif data_type == 'training':
                return self._export_training_data()
            else:
                raise ValueError(f"Unknown data type: {data_type}")
        except Exception as e:
            logger.error(f"Error exporting {data_type} data: {e}")
            return {'error': str(e), 'data': []}

    def _export_ppm_data(self) -> Dict[str, Any]:
        """Export PPM data from SQLite database."""
        with DatabaseSession() as session:
            schedules = session.query(PPMSchedule).join(Equipment).all()
            data = []
            for schedule in schedules:
                data.append({
                    'equipment_name': schedule.equipment.name,
                    'serial_number': schedule.equipment.serial_number,
                    'year': schedule.year,
                    'quarter': schedule.quarter.value,
                    'status': schedule.status.value
                })
            return {'data': data, 'count': len(data)}
```

## **Flask Development and Restart Protocol**

### **Problem 5: Changes Not Reflected After Code Updates**
- **Cause**: Flask auto-reload doesn't always catch deep service changes
- **Context**: New routes, service methods, or database changes need complete restart

**❌ DON'T: Rely only on Ctrl+C restart for major changes**
```bash
# This may not be sufficient for service/database changes
# Just using Ctrl+C and rerun flask
```

**✅ DO: Complete process kill for service/database changes**
```bash
# Windows - Kill all Python processes
taskkill /F /IM python.exe

# Linux/Mac - Kill specific process
pkill -f flask

# Then restart
python -m flask --app app.main:create_app run --debug --port 5001
```

### **Problem 6: Database Migration Validation**
- **Issue**: Not verifying migration success before declaring completion
- **Impact**: Empty tables appeared to be successful migration

**✅ DO: Always validate migration results**
```python
def validate_migration(self):
    """Validate migration success by checking record counts."""
    with DatabaseSession() as session:
        equipment_count = session.query(Equipment).count()
        ppm_count = session.query(PPMSchedule).count()
        ocm_count = session.query(OCMSchedule).count()
        
        logger.info(f"Migration validation:")
        logger.info(f"  Equipment: {equipment_count} records")
        logger.info(f"  PPM Schedules: {ppm_count} records")
        logger.info(f"  OCM Schedules: {ocm_count} records")
        
        if equipment_count == 0:
            logger.warning("No equipment records found - migration may have failed")
        return equipment_count > 0
```

## **Data Integrity and Error Handling**

### **Problem 7: Duplicate Key Handling**
- **Issue**: Attempting to insert duplicate records caused transaction failures
- **Solution**: Use merge or update-on-conflict patterns

**✅ DO: Handle duplicates gracefully**
```python
try:
    session.add(equipment)
    session.flush()
except IntegrityError as e:
    session.rollback()
    if 'UNIQUE constraint failed' in str(e):
        logger.warning(f"Duplicate equipment: {serial_number}, updating existing")
        existing = session.query(Equipment).filter_by(serial_number=serial_number).first()
        if existing:
            # Update existing record instead of creating new
            for key, value in equipment_data.items():
                setattr(existing, key, value)
```

## **Attribute Mapping Issues**

### **Problem 8: Model Attribute Mismatches**
- **Error**: `AttributeError: 'PPMSchedule' object has no attribute 'q1_date'`
- **Cause**: DataService methods using old JSON-based attribute names instead of SQLAlchemy model attributes
- **Context**: Migration changed data structure but service methods weren't updated

**❌ DON'T: Use old attribute names from JSON system**
```python
# This will fail - PPMSchedule doesn't have q1_date, q2_date, etc.
'q1_date': latest_ppm.q1_date.strftime('%d/%m/%Y'),
'service_date': latest_ocm.service_date.strftime('%d/%m/%Y')
```

**✅ DO: Use correct SQLAlchemy model attributes**
```python
# PPM Schedule attributes
{
    'quarter': latest_ppm.quarter.value if latest_ppm.quarter else '',
    'year': latest_ppm.year,
    'scheduled_date': latest_ppm.scheduled_date.strftime('%d/%m/%Y') if latest_ppm.scheduled_date else '',
    'completion_date': latest_ppm.completion_date.strftime('%d/%m/%Y') if latest_ppm.completion_date else '',
    'status': latest_ppm.status.value if latest_ppm.status else '',
    'engineer': latest_ppm.engineer.name if latest_ppm.engineer else '',
    'notes': latest_ppm.notes or '',
    'work_performed': latest_ppm.work_performed or ''
}

# OCM Schedule attributes  
{
    'year': latest_ocm.year,
    'scheduled_date': latest_ocm.scheduled_date.strftime('%d/%m/%Y') if latest_ocm.scheduled_date else '',
    'completion_date': latest_ocm.completion_date.strftime('%d/%m/%Y') if latest_ocm.completion_date else '',
    'status': latest_ocm.status.value if latest_ocm.status else '',
    'priority': latest_ocm.priority or '',
    'issue_description': latest_ocm.issue_description or '',
    'engineer': latest_ocm.engineer.name if latest_ocm.engineer else ''
}
```

## **Prevention Checklist**

### **Before Migration:**
- [ ] Map all model attributes between old and new systems
- [ ] Create comprehensive migration test scripts
- [ ] Verify all enum values match between systems
- [ ] Test database connection and model imports

### **During Migration:**
- [ ] Use database transactions for data integrity
- [ ] Handle duplicate data gracefully
- [ ] Log all migration steps and errors
- [ ] Validate data after each major step

### **After Migration:**
- [ ] Test all CRUD operations
- [ ] Verify export/import functionality
- [ ] Check navigation and UI components
- [ ] Complete Flask server restart
- [ ] Test with actual user workflows

## **✅ RESOLUTION SUMMARY (2025-06-24)**

**Successfully resolved all migration issues:**

### **Migration Results:**
- **1,197 equipment records** migrated from JSON to SQLite
- **3,748 PPM schedules** migrated successfully  
- **260 OCM schedules** migrated successfully
- **29 departments**, **467 manufacturers**, and **9 engineers** created

### **Fixed Issues:**
1. **Missing export_data methods** - Added complete export functionality to DataService
2. **Attribute mapping errors** - Fixed all model attribute mismatches:
   - PPM: `q1_date` → `scheduled_date`, `q1_status` → `status`
   - OCM: `service_date` → `scheduled_date`, `next_maintenance` → `completion_date`
3. **Add equipment functionality** - Fixed constructor calls and required fields
4. **Bulk barcode generation** - Restored with correct data access methods
5. **Import/export functionality** - All working with SQLite backend

### **Key Technical Fixes:**
- Updated `_get_ppm_data_for_equipment()` to use correct model attributes
- Updated `_get_ocm_data_for_equipment()` to use correct model attributes  
- Fixed `_create_ppm_schedule()` and `_create_ocm_schedule()` methods
- Added missing backward compatibility methods: `get_all_entries()`, `add_entry()`, etc.
- Implemented complete export functionality for all data types

### **Verification Commands:**
```bash
# Check migration success
python -c "import sqlite3; conn = sqlite3.connect('data/hospital_equipment_dev.db'); c = conn.cursor(); c.execute('SELECT COUNT(*) FROM equipment'); print('Equipment count:', c.fetchone()[0]); conn.close()"

# Test service functionality  
python -c "from app.services.data_service import DataService; ds = DataService(); print('PPM:', len(ds.get_all_entries('ppm'))); print('OCM:', len(ds.get_all_entries('ocm')))"
```

## **Quick Reference Commands**

```bash
# Complete Flask restart (required for service changes)
taskkill /F /IM python.exe
python -m flask --app app.main:create_app run --debug --port 5001

# Check database contents
python -c "import sqlite3; conn = sqlite3.connect('data/hospital_equipment_dev.db'); c = conn.cursor(); c.execute('SELECT COUNT(*) FROM equipment'); print('Equipment count:', c.fetchone()[0]); conn.close()"

# Test service methods
python -c "from app.services.data_service import DataService; ds = DataService(); print('PPM:', len(ds.get_all_entries('ppm'))); print('OCM:', len(ds.get_all_entries('ocm')))"
```

## **Related Files to Check**
- `app/models/maintenance.py` - Model attribute definitions
- `app/services/data_service.py` - Service method implementations  
- `app/routes/views.py` - Route handlers calling service methods
- `migrate_json_to_sqlite.py` - Migration script

---

**Remember**: Always verify that model attributes match between old JSON structure and new SQLAlchemy models. Test thoroughly after migration to catch attribute mismatches early.

## **Related Rules**

- **[Template Field Mapping Lessons](flask_template_field_mapping_lessons.md)** - Comprehensive guide for resolving template field name mismatches and data service integration issues after database migrations

---

**Remember**: Template errors in Flask often cascade, fixing one error may reveal others. Always restart the development server after significant template changes and read error messages carefully. 