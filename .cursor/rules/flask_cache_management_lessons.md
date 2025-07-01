# Flask Cache Management and Real-Time Data Updates

This rule captures critical lessons learned from resolving cache management issues in Flask applications with dual-cache systems, particularly for real-time equipment management systems.

## **Problem Summary**

### **Symptoms Observed**
- **Delayed Visibility**: New equipment additions not appearing immediately in frontend lists
- **Delayed Deletions**: Deleted equipment taking time to disappear from frontend
- **Numbering Issues**: Equipment showing database IDs (1197, 1198) instead of sequential numbering (1, 2, 3...)
- **Audit Log Errors**: `'action' is an invalid keyword argument for AuditLog`
- **Inconsistent Cache States**: Route cache and service cache operating independently

### **Root Causes Identified**
1. **Dual Cache System**: DataService cache and route-level cache operating independently
2. **Incomplete Cache Invalidation**: Only one cache layer being cleared on CRUD operations
3. **Sequential Numbering Logic**: Using database IDs instead of sequential positioning
4. **Missing Cache Clearing**: API routes not clearing caches after modifications
5. **Model Parameter Mismatches**: Wrong parameter names in model constructors

## **Comprehensive Solution Implementation**

### **1. Dual Cache Clearing Strategy**

**❌ INCORRECT: Clearing only one cache layer**
```python
@api_bp.route('/equipment/<data_type>', methods=['POST'])
def add_equipment(data_type):
    result = data_service.add_equipment(equipment_data, data_type)
    if result.get('success'):
        # Only clearing DataService cache - incomplete!
        data_service._clear_equipment_cache()
        return jsonify(result), 201
```

**✅ CORRECT: Comprehensive cache clearing function**
```python
def clear_all_caches(data_type=None):
    """Helper function to clear both DataService cache and route cache, then force refresh."""
    # Clear route-level cache
    invalidate_cache(data_type)
    invalidate_cache()  # Clear all route cache
    
    # Clear dashboard stats cache
    get_dashboard_stats.cache_clear()
    
    # Clear DataService cache as well (belt and suspenders approach)
    data_service._clear_equipment_cache()
    
    # Force refresh to ensure immediate visibility
    if data_type:
        get_cached_data(data_type, force_refresh=True)
    
    logger.info(f"Cleared all caches for data_type: {data_type or 'all'}")

# Use in all CRUD operations
@api_bp.route('/equipment/<data_type>', methods=['POST'])
def add_equipment(data_type):
    result = data_service.add_equipment(equipment_data, data_type)
    if result.get('success'):
        # Clear ALL caches for immediate visibility
        from app.routes.views import clear_all_caches
        clear_all_caches(data_type)
        return jsonify(result), 201
```

### **2. Sequential Numbering Implementation**

**❌ INCORRECT: Using database IDs as display numbers**
```python
# In DataService._equipment_to_dict
result = {
    'id': str(equipment.id),
    'NO': str(equipment.id),  # Shows 1197, 1198, etc.
    # ... other fields
}
```

**✅ CORRECT: Sequential numbering in route layer**
```python
def get_cached_data(data_type, force_refresh=False):
    """Get cached data with sequential numbering and automatic refresh."""
    # ... cache logic ...
    
    # Add sequential numbering after retrieving data
    for i, item in enumerate(_data_cache[data_type], 1):
        item['NO'] = str(i)  # Sequential: 1, 2, 3...
    
    return _data_cache[data_type]

# In DataService._equipment_to_dict - remove NO field assignment
result = {
    'id': str(equipment.id),
    # NO field will be set by routes for sequential numbering
    # ... other fields
}
```

### **3. Complete API Route Cache Integration**

**✅ MANDATORY: All CRUD operations must clear cache**
```python
@api_bp.route('/equipment/<data_type>', methods=['POST'])
def add_equipment(data_type):
    result = data_service.add_equipment(equipment_data, data_type)
    if result.get('success'):
        from app.routes.views import clear_all_caches
        clear_all_caches(data_type)
        return jsonify(result), 201

@api_bp.route('/equipment/<data_type>/<SERIAL>', methods=['PUT'])
def update_equipment(data_type, SERIAL):
    updated_entry = data_service.update_entry(data_type, SERIAL, data)
    if updated_entry:
        from app.routes.views import clear_all_caches
        clear_all_caches(data_type)
        return jsonify({'success': True, 'data': updated_entry}), 200

@api_bp.route('/equipment/<data_type>/<SERIAL>', methods=['DELETE'])
def delete_equipment(data_type, SERIAL):
    deleted = data_service.delete_entry(data_type, SERIAL)
    if deleted:
        from app.routes.views import clear_all_caches
        clear_all_caches(data_type)
        return jsonify({'success': True}), 200

@api_bp.route('/bulk_delete/<data_type>', methods=['POST'])
def bulk_delete(data_type):
    # ... deletion logic ...
    if deleted_count > 0:
        from app.routes.views import clear_all_caches
        clear_all_caches(data_type)
    # ... response
```

### **4. Model Parameter Name Fixes**

**❌ INCORRECT: Wrong parameter names**
```python
# Audit log creation
audit_log = AuditLog(
    action=action,  # Wrong parameter name
    description=description,
    user_id=user_id,
    timestamp=datetime.now()
)

# OCM Schedule creation
ocm_schedule = OCMSchedule(
    service_date=service_date,  # Wrong parameter name
    # ... other fields
)
```

**✅ CORRECT: Use proper model parameter names**
```python
# Check model definitions first
# app/models/system.py - AuditLog uses 'event_type'
audit_log = AuditLog(
    event_type=action,  # Correct parameter name
    description=description,
    user_id=user_id,
    timestamp=datetime.now()
)

# app/models/ocm.py - OCMSchedule uses 'scheduled_date'
ocm_schedule = OCMSchedule(
    scheduled_date=scheduled_date,  # Correct parameter name
    # ... other fields
)
```

## **Cache Management Architecture**

### **Multi-Layer Cache Strategy**
```python
# Layer 1: Route-level cache with TTL
_data_cache = {}
_cache_timestamp = {}
CACHE_DURATION = 300  # 5 minutes

# Layer 2: DataService cache
class DataService:
    def __init__(self):
        self._equipment_cache = {}
        self._cache_expiry = {}

# Layer 3: Dashboard stats cache
@lru_cache(maxsize=1)
def get_dashboard_stats():
    # Cached dashboard statistics
    pass
```

### **Cache Invalidation Triggers**
```python
# ALWAYS clear cache after these operations:
CACHE_INVALIDATION_OPERATIONS = [
    'add_equipment',
    'update_equipment', 
    'delete_equipment',
    'bulk_delete',
    'import_data',
    'bulk_update'
]

# Force refresh pattern for immediate visibility
def force_refresh_after_modification(data_type):
    """Ensure immediate visibility of changes."""
    clear_all_caches(data_type)
    # Force a fresh fetch to populate cache
    get_cached_data(data_type, force_refresh=True)
```

## **Testing and Validation**

### **Cache Clearing Verification**
```python
# Test script for cache clearing
def test_cache_clearing():
    # Add equipment
    result = data_service.add_equipment(test_data, 'ppm')
    assert result['success']
    
    # Verify immediate visibility (no cache delay)
    cached_data = get_cached_data('ppm', force_refresh=False)
    serials = [item['SERIAL'] for item in cached_data]
    assert test_data['SERIAL'] in serials
    
    # Verify sequential numbering
    for i, item in enumerate(cached_data, 1):
        assert item['NO'] == str(i)
```

### **Performance Monitoring**
```python
# Log cache operations for debugging
def clear_all_caches(data_type=None):
    start_time = time.time()
    # ... cache clearing logic ...
    duration = time.time() - start_time
    logger.info(f"Cache clearing took {duration:.3f}s for {data_type or 'all'}")
```

## **Error Prevention Checklist**

### **Before CRUD Operations:**
- [ ] Verify all model parameter names match SQLAlchemy definitions
- [ ] Check that cache clearing is implemented in all API routes
- [ ] Ensure sequential numbering logic is in route layer, not service layer
- [ ] Test with both single and bulk operations

### **After CRUD Operations:**
- [ ] Verify immediate visibility in frontend (no delays)
- [ ] Check sequential numbering starts from 1
- [ ] Confirm deleted items disappear immediately
- [ ] Test that cache expiration still works normally

### **Model Integration:**
- [ ] Check model constructors for correct parameter names
- [ ] Verify enum values exist (e.g., MaintenanceStatus.COMPLETED)
- [ ] Test foreign key constraints are satisfied
- [ ] Ensure audit log creation uses correct parameters

## **Common Error Patterns and Solutions**

| Error Pattern | Cause | Solution |
|---------------|-------|----------|
| Equipment not appearing immediately | Only one cache layer cleared | Implement `clear_all_caches()` |
| Wrong numbering (1197, 1198...) | Using database ID as NO field | Set NO field to sequential index |
| `'action' is invalid keyword` | Wrong model parameter name | Use `event_type` for AuditLog |
| `'service_date' is invalid keyword` | Wrong OCM parameter name | Use `scheduled_date` for OCMSchedule |
| Deletion delays | API routes not clearing cache | Add cache clearing to all CRUD APIs |

## **Performance Optimization**

### **Cache Warming Strategy**
```python
def warm_cache_after_clear(data_type):
    """Pre-populate cache after clearing to avoid first-request delays."""
    # Clear all caches
    clear_all_caches(data_type)
    
    # Immediately warm the cache
    get_cached_data(data_type, force_refresh=True)
    
    # Pre-calculate dashboard stats
    get_dashboard_stats.cache_clear()
    get_dashboard_stats()
```

### **Selective Cache Clearing**
```python
def selective_cache_clear(operation_type, data_type, affected_records=None):
    """Clear only necessary cache layers based on operation type."""
    if operation_type in ['add', 'delete']:
        # These affect counts and lists - clear everything
        clear_all_caches(data_type)
    elif operation_type == 'update':
        # Updates might not affect lists - selective clear
        invalidate_cache(data_type)
        data_service._clear_equipment_cache()
```

## **Monitoring and Debugging**

### **Cache State Logging**
```python
def log_cache_state(operation, data_type):
    """Log cache state for debugging."""
    route_cache_size = len(_data_cache.get(data_type, []))
    service_cache_size = len(data_service._equipment_cache.get(data_type, []))
    
    logger.debug(f"After {operation}: Route cache={route_cache_size}, "
                f"Service cache={service_cache_size} for {data_type}")
```

### **Real-Time Verification**
```python
def verify_immediate_visibility(data_type, expected_serial, operation='add'):
    """Verify that changes are immediately visible."""
    cached_data = get_cached_data(data_type, force_refresh=False)
    serials = [item['SERIAL'] for item in cached_data]
    
    if operation == 'add':
        assert expected_serial in serials, f"Added {expected_serial} not immediately visible"
    elif operation == 'delete':
        assert expected_serial not in serials, f"Deleted {expected_serial} still visible"
```

---

**Key Takeaway**: In multi-layer cache systems, ALWAYS clear ALL cache layers and force refresh after CRUD operations to ensure immediate real-time updates. Sequential numbering should be handled at the presentation layer, not the data layer. 