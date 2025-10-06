# Legacy Code Cleanup Plan

**Created**: 2025-10-06
**Target Completion**: Q1-Q2 2026 (3-6 months post-DDD migration)
**Status**: 📋 Planning Phase

---

## 📋 Executive Summary

This document outlines the plan to remove legacy compatibility layers introduced during the DDD migration. These layers were necessary to maintain backward compatibility during the transition but should be removed once the new architecture is stable.

### Goals
1. Remove all legacy global instances
2. Enforce dependency injection everywhere
3. Clean up compatibility re-exports
4. Update all deprecated imports
5. Remove legacy exception classes

### Timeline
- **Phase 1** (Month 1-2): Add deprecation warnings
- **Phase 2** (Month 3-4): Update all internal imports
- **Phase 3** (Month 5-6): Remove legacy code

---

## 🎯 Legacy Code Inventory

### 1. Configuration Global Instances

#### File: `app/src/config/app_config.py`
**Line**: 568
**Code**:
```python
# Legacy global instance kept for backward compatibility during transition
# Note: AppConfig should be retrieved from DI container
config = AppConfig()
```

**Impact**:
- Used by legacy code that hasn't migrated to DI
- Should be replaced with DI container injection

**Action Plan**:
1. Add deprecation warning (Phase 1)
2. Find all usages of `from app.src.config.app_config import config`
3. Update to use DI container
4. Remove global instance

**Estimated Effort**: 4 hours

---

#### File: `app/src/config/monitoring_config.py`
**Line**: 98
**Code**:
```python
# Legacy global instance kept for backward compatibility during transition
# Note: MonitoringConfig should be retrieved from DI container
monitoring_config = MonitoringConfig()
```

**Impact**: Similar to AppConfig
**Action Plan**: Same as AppConfig
**Estimated Effort**: 2 hours

---

#### File: `app/src/config/socket_config.py`
**Line**: 112
**Code**:
```python
# Legacy global instance kept for backward compatibility during transition
# Note: SocketConfig should be retrieved from DI container
socket_config = SocketConfig()
```

**Impact**: Similar to AppConfig
**Action Plan**: Same as AppConfig
**Estimated Effort**: 2 hours

---

### 2. Domain Layer Global Instances

#### File: `app/src/domain/audio/container.py`
**Line**: 143
**Code**:
```python
# Legacy global instance for backward compatibility
# Use dependency injection to get AudioDomainContainer instead
audio_container = AudioDomainContainer()
```

**Impact**:
- Audio system initialization
- Critical component, needs careful migration

**Action Plan**:
1. Add deprecation warning
2. Audit all direct usages
3. Update to use DI container
4. Remove after verification

**Estimated Effort**: 6 hours

---

#### File: `app/src/domain/bootstrap.py`
**Line**: 180
**Code**:
```python
# Legacy global instance kept for backward compatibility during transition
# Note: DomainBootstrap should be retrieved from DI container
domain_bootstrap = DomainBootstrap()
```

**Impact**:
- Domain initialization
- Very critical, affects entire domain layer

**Action Plan**:
1. Add deprecation warning
2. Comprehensive testing before removal
3. Update main.py and other entry points
4. Remove carefully

**Estimated Effort**: 8 hours

---

### 3. Error Handling Legacy Code

#### File: `app/src/infrastructure/error_handling/unified_error_handler.py`

**Line 491**: Legacy exception classes
```python
# Legacy exception classes for compatibility
```

**Line 505**: Legacy global instance
```python
# Legacy global instance kept for backward compatibility during transition
# Note: UnifiedErrorHandler should be retrieved from DI container
error_handler = UnifiedErrorHandler()
```

**Impact**:
- Error handling throughout application
- Need to ensure all error handling migrated

**Action Plan**:
1. Identify all legacy exception usage
2. Update to new unified exceptions
3. Add deprecation warnings
4. Remove after migration complete

**Estimated Effort**: 6 hours

---

### 4. Service Layer Global Instances

#### File: `app/src/services/player_state_service.py`
**Line**: 375
**Code**:
```python
# Legacy global instance removed - use dependency injection
# Note: PlayerStateService should be retrieved from DI container
```

**Impact**: Already documented as removed
**Action**: Verify no legacy usage remains
**Estimated Effort**: 1 hour

---

#### File: `app/src/services/error/unified_error_decorator.py`
**Line**: 518
**Code**:
```python
# Legacy global instance kept for backward compatibility during transition
```

**Impact**: Error decoration system
**Action Plan**: Similar to error handler
**Estimated Effort**: 3 hours

---

### 5. Data Layer Legacy Code

#### File: `app/src/data/database_manager.py`
**Line**: 86
**Code**:
```python
# Database manager should be retrieved from DI container
```

**Impact**: Database access
**Action Plan**: Ensure all DB access uses DI
**Estimated Effort**: 4 hours

---

### 6. Deprecated Module Re-exports

#### File: `app/src/monitoring/config.py`
**Entire file**: Deprecated re-export module

**Code**:
```python
"""
DEPRECATED: MonitoringConfig has been moved to app.src.config.monitoring_config
This module re-exports from the new location for backward compatibility.
"""
```

**Impact**: Import compatibility
**Action Plan**:
1. Find all imports from old location
2. Update to new location
3. Add import-time deprecation warning
4. Remove file after migration

**Estimated Effort**: 2 hours

---

## 📊 Summary Statistics

### Total Legacy Items: 11
- **Config Global Instances**: 3 files
- **Domain Global Instances**: 2 files
- **Error Handling Legacy**: 2 locations
- **Service Global Instances**: 2 files
- **Data Layer Legacy**: 1 file
- **Deprecated Modules**: 1 file

### Total Estimated Effort: 38 hours (~1 week)

---

## 🚀 Implementation Phases

### Phase 1: Deprecation Warnings (Weeks 1-2)
**Goal**: Make legacy code visible

**Tasks**:
1. Add `warnings.warn()` to all global instances
2. Add deprecation notices to docstrings
3. Create migration guide document
4. Announce to team

**Script**:
```python
import warnings

def add_deprecation_warning(old_path: str, new_path: str, removal_version: str = "v2.0"):
    """Add deprecation warning to legacy code."""
    warnings.warn(
        f"{old_path} is deprecated. Use {new_path} instead. "
        f"Will be removed in {removal_version}",
        DeprecationWarning,
        stacklevel=2
    )
```

**Deliverables**:
- ✅ All legacy code has deprecation warnings
- ✅ Migration guide published
- ✅ Team notified

---

### Phase 2: Internal Migration (Weeks 3-8)
**Goal**: Update all internal code to use DI

**Tasks per file**:
1. **Search**: `grep -r "from app.src.config.app_config import config" .`
2. **Update**: Replace with DI container injection
3. **Test**: Ensure functionality unchanged
4. **Document**: Update in migration log

**Example Migration**:
```python
# OLD (legacy)
from app.src.config.app_config import config

def some_function():
    path = config.upload_path

# NEW (DI)
from app.src.dependencies import get_config

def some_function(config = Depends(get_config)):
    path = config.upload_path
```

**Deliverables**:
- ✅ All internal imports updated
- ✅ All tests passing
- ✅ No new legacy usage

---

### Phase 3: External Migration (Weeks 9-16)
**Goal**: Update any external code/plugins

**Tasks**:
1. Identify external consumers
2. Provide migration examples
3. Support migration efforts
4. Set deprecation deadline

**Communication**:
- Email notification (Week 9)
- Migration workshop (Week 11)
- Deadline reminder (Week 14)
- Final warning (Week 15)

**Deliverables**:
- ✅ External code migrated
- ✅ Deprecation warnings acknowledged
- ✅ Ready for removal

---

### Phase 4: Legacy Code Removal (Weeks 17-20)
**Goal**: Remove all legacy compatibility layers

**Tasks**:
1. Create backup branch
2. Remove global instances
3. Remove deprecated modules
4. Remove legacy exception classes
5. Update documentation
6. Final testing

**Removal Checklist**:
- [ ] Remove `config = AppConfig()` from app_config.py
- [ ] Remove `monitoring_config = MonitoringConfig()` from monitoring_config.py
- [ ] Remove `socket_config = SocketConfig()` from socket_config.py
- [ ] Remove `audio_container = AudioDomainContainer()` from container.py
- [ ] Remove `domain_bootstrap = DomainBootstrap()` from bootstrap.py
- [ ] Remove `error_handler = UnifiedErrorHandler()` from unified_error_handler.py
- [ ] Remove legacy exception classes
- [ ] Remove deprecated decorator global instance
- [ ] Remove app/src/monitoring/config.py file
- [ ] Remove database manager legacy comments
- [ ] Update all documentation

**Deliverables**:
- ✅ All legacy code removed
- ✅ All tests passing
- ✅ Documentation updated
- ✅ Release notes created

---

## 🔍 Detection & Monitoring

### Finding Legacy Usage

**Script: `scripts/find_legacy_usage.sh`**
```bash
#!/bin/bash
# Find all legacy code usage

echo "=== Legacy Config Global Instances ==="
grep -r "from app.src.config.app_config import config" app/ tests/ --include="*.py"
grep -r "from app.src.config.monitoring_config import monitoring_config" app/ tests/ --include="*.py"
grep -r "from app.src.config.socket_config import socket_config" app/ tests/ --include="*.py"

echo ""
echo "=== Legacy Domain Global Instances ==="
grep -r "from app.src.domain.audio.container import audio_container" app/ tests/ --include="*.py"
grep -r "from app.src.domain.bootstrap import domain_bootstrap" app/ tests/ --include="*.py"

echo ""
echo "=== Legacy Error Handling ==="
grep -r "from app.src.infrastructure.error_handling.unified_error_handler import error_handler" app/ tests/ --include="*.py"

echo ""
echo "=== Deprecated Imports ==="
grep -r "from app.src.monitoring.config import" app/ tests/ --include="*.py"

echo ""
echo "=== Legacy Exception Classes ==="
grep -r "AudioError\|PlaylistError\|NFCError" app/ tests/ --include="*.py" | grep -v "# "
```

**Run weekly during migration**

---

## ✅ Success Criteria

### Phase 1 Complete When:
- [ ] All global instances have deprecation warnings
- [ ] Migration guide published
- [ ] All developers aware

### Phase 2 Complete When:
- [ ] No internal code uses legacy imports
- [ ] All tests pass
- [ ] Code review approved

### Phase 3 Complete When:
- [ ] No external code uses legacy imports
- [ ] All consumers migrated
- [ ] Deadline reached

### Phase 4 Complete When:
- [ ] All legacy code removed
- [ ] All tests pass (>1,580)
- [ ] Documentation updated
- [ ] Release notes published

---

## 📈 Progress Tracking

### Weekly Check-ins
- Monday: Review progress
- Wednesday: Update status
- Friday: Report blockers

### Metrics to Track
- Number of legacy usages found
- Number of files migrated
- Test pass rate
- Deprecation warnings triggered (in logs)

### Reporting Template
```
Week X Progress Report:
- Files migrated: X/Y
- Legacy usages remaining: N
- Tests passing: X/1,580
- Blockers: [list]
- Next week plan: [summary]
```

---

## 🚨 Risk Mitigation

### Risk 1: Breaking Changes
**Mitigation**:
- Comprehensive test coverage
- Gradual rollout
- Feature flags for legacy support

### Risk 2: Unknown Dependencies
**Mitigation**:
- Thorough code search
- Deprecation warnings in logs
- Extended timeline for Phase 3

### Risk 3: Performance Impact
**Mitigation**:
- Benchmark before/after
- Monitor production metrics
- Rollback plan ready

---

## 📝 Migration Guide for Developers

### How to Migrate Your Code

**Step 1: Identify Legacy Usage**
```bash
# Run the detection script
./scripts/find_legacy_usage.sh
```

**Step 2: Update Imports**
```python
# BEFORE (legacy)
from app.src.config.app_config import config

def my_function():
    upload_path = config.upload_path

# AFTER (DI)
from app.src.dependencies import get_config
from fastapi import Depends

def my_function(config = Depends(get_config)):
    upload_path = config.upload_path
```

**Step 3: Update Tests**
```python
# BEFORE
from app.src.config.app_config import config

def test_something():
    assert config.upload_path == "expected"

# AFTER
from app.src.infrastructure.di.container import DIContainer

def test_something():
    container = DIContainer()
    config = container.get(AppConfig)
    assert config.upload_path == "expected"
```

**Step 4: Verify**
```bash
# Run tests
pytest tests/

# Check for warnings
python -W all your_script.py
```

---

## 📞 Support & Resources

### Documentation
- **DI Container Guide**: `/documentation/dependency-injection.md`
- **Migration Examples**: `/documentation/legacy-migration-examples.md`
- **Troubleshooting**: `/documentation/migration-troubleshooting.md`

### Contact
- **Migration Lead**: [Team Lead]
- **Slack Channel**: #ddd-migration
- **Office Hours**: Tuesdays 2-3 PM

### Useful Commands
```bash
# Find legacy usage
./scripts/find_legacy_usage.sh

# Run tests
pytest tests/ -v

# Check deprecation warnings
python -W all -m pytest tests/
```

---

## 🎯 Milestones

| Milestone | Target Date | Status |
|-----------|-------------|--------|
| Phase 1: Deprecation warnings added | Week 2 | ⏳ Pending |
| Phase 2: Internal migration complete | Week 8 | ⏳ Pending |
| Phase 3: External migration complete | Week 16 | ⏳ Pending |
| Phase 4: Legacy code removed | Week 20 | ⏳ Pending |
| **Final Release** | **Q2 2026** | **⏳ Pending** |

---

## 📋 Action Items

### Immediate (This Week)
- [ ] Review this plan with team
- [ ] Create migration guide
- [ ] Set up progress tracking
- [ ] Schedule kick-off meeting

### Next Week
- [ ] Add deprecation warnings (Phase 1)
- [ ] Create detection script
- [ ] Begin internal migration inventory

### Next Month
- [ ] Complete Phase 1
- [ ] Start Phase 2
- [ ] Monitor deprecation warnings

---

**Document Version**: 1.0
**Last Updated**: 2025-10-06
**Next Review**: Weekly during migration
**Status**: 📋 **Ready for Team Review**

---

## Appendix: File Change Summary

### Files to Modify
1. `app/src/config/app_config.py` - Remove global instance
2. `app/src/config/monitoring_config.py` - Remove global instance
3. `app/src/config/socket_config.py` - Remove global instance
4. `app/src/domain/audio/container.py` - Remove global instance
5. `app/src/domain/bootstrap.py` - Remove global instance
6. `app/src/infrastructure/error_handling/unified_error_handler.py` - Remove global + legacy classes
7. `app/src/services/error/unified_error_decorator.py` - Remove global instance
8. `app/src/data/database_manager.py` - Update comments
9. `app/src/monitoring/config.py` - **DELETE FILE**

### Files to Create
1. `documentation/legacy-migration-guide.md`
2. `documentation/legacy-migration-examples.md`
3. `scripts/find_legacy_usage.sh`
4. `scripts/add_deprecation_warnings.py`

### Total Changes: 9 files to modify, 1 to delete, 4 to create
