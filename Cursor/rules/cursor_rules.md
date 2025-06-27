# Project-Specific Rules and Best Practices

This document outlines key learnings, architectural patterns, and solutions to common problems encountered in the Hospital Equipment Management System project. Following these guidelines will help maintain code quality, prevent recurring issues, and ensure consistency.

## 1. Data Handling and Integrity

### 1.1. Data Type Consistency (Especially for IDs)
- **Problem**: Inconsistencies between string and integer IDs (e.g., in `training.json`) caused lookup failures and type errors.
- **Rule**: All record IDs stored in JSON files **must be treated as strings** throughout the application.
- **Implementation**:
    - When generating new IDs, convert them to strings immediately: `new_id = str(max(existing_ids) + 1)`.
    - In all service functions (`get`, `update`, `delete`), ensure comparisons are string-to-string: `if str(record.id) == str(target_id):`.
    - This prevents `TypeError` exceptions and ensures reliable data retrieval.

### 1.2. Handling `None` Values in Data
- **Problem**: `AttributeError: 'NoneType' object has no attribute 'strip'` occurred when processing records with optional fields (like `engineer`) that were `None`.
- **Rule**: **Never call string methods directly on optional fields**. Always perform a `None` check first.
- **Implementation**:
    - Use safe handling patterns: `value = data.get('key'); processed_value = value.strip() if value else ''`. This is robust and prevents crashes from missing data.

### 1.3. JSON Data Corruption
- **Problem**: JSON files (`ppm.json`, `training.json`) became corrupted (truncated or malformed) during write operations, causing the application to fail on startup.
- **Rule**: The application must have a data backup and recovery mechanism. When JSON decoding errors occur, the first step is to validate the integrity of the JSON file and restore from a backup if necessary.
- **Implementation**:
    - **Backup**: The system automatically creates backups.
    - **Recovery**: Manually identify the latest valid backup file (e.g., `training.json.backup_YYYYMMDD_HHMMSS`) and use it to overwrite the corrupted file.
    - **Prevention**: While not fully implemented, future work should consider atomic write operations (writing to a temporary file, then renaming) to prevent corruption during writes.

## 2. Business Logic and Services

### 2.1. Calculated Fields (e.g., Status)
- **Problem**: The `Status` field for PPM equipment was not being calculated on manual addition, leading to data inconsistency and errors.
- **Rule**: The calculation for derived fields (like `Status`) must be centralized and applied consistently across all data entry points (manual forms, bulk imports).
- **Implementation**:
    - Place calculation logic in the relevant `DataService` method (e.g., `DataService.calculate_status()`).
    - Call this calculation logic from all creation/update pathways, ideally from a central method like `DataService.add_entry()`.

### 2.2. Bulk Import Logic
- **Problem**: The initial bulk import functionality only skipped duplicates but did not update existing records.
- **Rule**: Bulk import functionality must clearly define its behavior for existing records. If updates are required, the logic must find records by a unique key (`SERIAL` for equipment) and apply the new data.
- **Implementation**:
    - The `ImportExportService.import_from_csv()` method was modified to check for existing entries.
    - If an entry exists, `DataService.update_entry()` is called.
    - If not, `DataService.add_entry()` is called.
    - Provide clear user feedback, such as: "X new entries added, Y existing entries updated."

## 3. API and Route Design

### 3.1. Efficient Bulk Operations
- **Problem**: The frontend performed bulk deletion of training records by sending many individual DELETE requests, which is inefficient.
- **Rule**: For any bulk action, create a single, dedicated API endpoint to handle the batch operation.
- **Implementation**:
    - A new endpoint, `DELETE /api/trainings/bulk`, was created.
    - It accepts a JSON payload with a list of IDs: `{ "ids": ["1", "2", "3"] }`.
    - This significantly reduces network overhead and improves performance.

### 3.2. Role-Based Access Control (RBAC)
- **Problem**: Users were denied access to delete training records because their roles had a generic `training_manage` permission, but the endpoint required a specific `training_delete` permission.
- **Rule**: Be specific and granular with permission checks. Ensure that role definitions in `data/settings.json` precisely match the permissions required by the `@permission_required()` decorator in the routes.
- **Implementation**:
    - The `Admin` and `Editor` roles were updated to include `training_write` and `training_delete`.

## 4. Frontend and UI

### 4.1. Responsive Data Tables
- **Problem**: The PPM equipment table, with its many columns, was not user-friendly on smaller screens.
- **Rule**: Wide data tables must be wrapped in a responsive container that allows for horizontal scrolling.
- **Implementation**:
    - The `<table>` is wrapped in `<div class="table-responsive-wrapper"><div class="table-responsive">...</div></div>`.
    - Custom CSS was added to `main.css` for better scrollbar styling, a minimum table width, and sticky headers/columns to improve user experience.

# Cursor AI Development Rules

## Flask Application Development Rules

### 1. Flask Route Registration Issues

**Problem**: Flask BuildError "Could not build url for endpoint 'views.function_name'" even when route function exists

**Root Cause**: Flask development server doesn't always properly reload new routes, especially when:
- Background threads (schedulers) are running
- New services are added
- Template cache conflicts occur

**MANDATORY Fix Protocol**:
```bash
# 1. ALWAYS kill ALL Python processes (not just Ctrl+C)
taskkill /F /IM python.exe

# 2. Restart Flask completely
python app/main.py

# 3. Verify routes are registered (create test script if needed)
python -c "from app import create_app; app = create_app(); [print(rule) for rule in app.url_map.iter_rules() if 'target_route' in str(rule)]"
```

**Prevention Checklist**:
- [ ] Add new service imports to `app/services/__init__.py`
- [ ] Use complete process termination for route changes
- [ ] Never rely on auto-reload for new route additions
- [ ] Test route registration before debugging template issues
- [ ] Clear template cache with complete restart

### 2. Service Import Requirements

When adding new services (like AuditService):
```python
# MUST update app/services/__init__.py
from app.services.new_service import NewService
```

### 3. Flask Development Server Restart Protocol

**For New Routes/Services**:
- Complete process kill required
- Auto-reload is insufficient
- Background threads interfere with reload

**For Code Changes Only**:
- Ctrl+C restart usually sufficient
- Auto-reload works for logic changes

## General Development Rules

### 4. Error Debugging Hierarchy

1. **Complete Application Restart** - First step for route/import issues
2. **Check Service Imports** - Verify all services in `__init__.py`
3. **Route Registration Test** - Confirm Flask recognizes routes
4. **Template/Cache Issues** - Last resort, usually fixed by restart

### 5. Memory Management

- Always update memory when encountering new error patterns
- Document fix protocols for future reference
- Include prevention steps, not just solutions

### 6. Flask Application Architecture

**Route Organization**:
- Views in `app/routes/views.py`
- API endpoints in `app/routes/api.py`
- Services in `app/services/`
- Templates in `app/templates/`

**Service Integration**:
- Import in `app/services/__init__.py`
- Register routes in blueprint
- Complete restart for new integrations

## Testing Protocols

### 7. Route Testing

```python
# Quick route verification script
from app import create_app
app = create_app()
routes = [str(rule) for rule in app.url_map.iter_rules()]
target_routes = [r for r in routes if 'target_keyword' in r]
print(f"Found {len(target_routes)} matching routes")
```

### 8. Import Testing

```python
# Service import verification
try:
    from app.services.target_service import TargetService
    print("✅ Service imports successfully")
except ImportError as e:
    print(f"❌ Import failed: {e}")
```

## Error Prevention

### 9. Common Flask Pitfalls

- **Route Registration**: Always complete restart for new routes
- **Service Imports**: Update `__init__.py` files
- **Template Cache**: Complete restart clears cache issues
- **Background Threads**: Kill processes, don't just interrupt

### 10. Development Workflow

1. Add new service/route
2. Update relevant `__init__.py` files
3. **Complete process termination** (`taskkill /F /IM python.exe`)
4. Restart Flask application
5. Test route registration
6. Verify functionality

## Memory Update Protocol

When encountering new error patterns:
1. Document the error and solution
2. Add to memory with prevention steps
3. Update this rules file
4. Include debugging hierarchy

---

**Remember**: Flask development server auto-reload is unreliable for structural changes (new routes, services, imports). Always use complete process termination and restart for these changes. 