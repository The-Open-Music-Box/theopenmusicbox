# Rapid Test Completion Plan
## Systematic Approach to Reach 100% Coverage

**Current Status**: 499 domain tests ✅
**Target**: ~135 more test files across 7 remaining areas

---

## Strategy for Rapid Completion

### Batch Creation Approach
1. **Create test scaffolds** for all files
2. **Essential coverage**: Focus on happy path + key errors
3. **Parallel execution**: Run batches to verify
4. **Iterate quickly**: Fix failures, move to next batch

### Test Template Pattern
```python
"""Tests for {ModuleName}."""
import pytest
from unittest.mock import Mock, MagicMock, patch

class Test{ClassName}:
    @pytest.fixture
    def mock_deps(self):
        return Mock()

    @pytest.fixture
    def sut(self, mock_deps):
        return {ClassName}(mock_deps)

    def test_init(self, sut):
        assert sut is not None

    def test_key_method_success(self, sut):
        result = sut.key_method()
        assert result is not None

    def test_key_method_error(self, sut):
        with pytest.raises(Exception):
            sut.error_method()
```

---

## Remaining Test Files by Phase

### Phase 1 Completion - Application Layer (10 files)

#### Controllers (9 files) - SIMPLIFIED TESTS
1. ✅ `test_audio_controller.py` - EXISTS
2. `test_audio_player_controller.py` - **NEW (20 tests)**
   - Initialization, play/pause/stop, volume, state
3. `test_physical_controls_controller.py` - **NEW (15 tests)**
   - Button events, encoder, state
4. `test_playback_controller.py` - **NEW (18 tests)**
   - Playback control, navigation
5. `test_playback_coordinator_controller.py` - **NEW (20 tests)**
   - Coordination logic
6. `test_playlist_controller.py` - **NEW (25 tests)**
   - Loading, validation, state
7. `test_playlist_state_manager_controller.py` - **NEW (20 tests)**
   - State management
8. `test_track_resolver_controller.py` - **NEW (15 tests)**
   - Path resolution
9. `test_upload_controller.py` - **NEW (20 tests)**
   - Upload handling

#### Application Services (2 files)
10. `test_audio_application_service.py` - **NEW (25 tests)**
11. `test_nfc_application_service.py` - **NEW (20 tests)**

**Phase 1 Total**: 198 new tests

---

### Phase 2 - API & Routes (14 files, ~200 tests)

#### API Routes (7 files)
1. `test_nfc_api_routes.py` - Route testing
2. `test_system_api_routes.py` - System routes
3. `test_upload_api_routes.py` - Upload routes
4. `test_web_api_routes.py` - Web routes
5. `test_youtube_api_routes.py` - YouTube routes
6. Complete `test_playlist_api_routes.py` - Playlist routes
7. Complete `test_player_api_routes.py` - Player routes

#### Legacy Routes (7 files)
8. `test_api_routes_state.py`
9. `test_nfc_unified_routes.py`
10. `test_player_routes_ddd.py`
11. `test_playlist_routes_ddd.py`
12. `test_web_routes.py`
13. `test_websocket_handlers.py`
14. `test_youtube_routes.py`

---

### Phase 3 - Infrastructure (22 files, ~300 tests)

#### Repositories (2)
1. `test_data_playlist_repository.py`
2. `test_data_track_repository.py`

#### Adapters (5)
3. `test_backend_adapter.py`
4. `test_nfc_adapter.py`
5. `test_pure_playlist_repository_adapter.py`
6. `test_file_storage_adapter.py`
7. `test_metadata_extractor.py`

#### Database (2)
8. `test_sqlite_database_service.py`
9. `test_migration_runner.py`

#### Hardware (6)
10. `test_controls_factory.py`
11. `test_gpio_controls.py`
12. `test_mock_controls.py`
13. `test_mock_nfc_hardware.py`
14. `test_nfc_factory.py`
15. `test_pn532_hardware.py`

#### DI & Others (7)
16. `test_container.py`
17. `test_data_container.py`
18. `test_application_container.py`
19. `test_unified_error_handler.py`
20. `test_nfc_hardware_adapter.py`
21. `test_upload_factory.py`
22. `test_youtube_downloader.py`

---

### Phase 4 - Services Layer (17 files, ~250 tests)

1. `test_unified_broadcasting_service.py`
2. `test_chunked_upload_service.py`
3. `test_client_subscription_manager.py`
4. `test_unified_error_decorator.py`
5. `test_event_outbox.py`
6. `test_file_path_resolver.py`
7. `test_filesystem_sync_service.py`
8. `test_mdns_service.py`
9. `test_notification_service.py`
10. `test_operation_tracker.py`
11. `test_player_state_service.py`
12. `test_unified_response_service.py`
13. `test_sequence_generator.py`
14. `test_unified_serialization_service.py`
15. `test_track_progress_service.py`
16. `test_upload_service.py`
17. `test_unified_validation_service.py`

---

### Phase 5 - Audio Domain (9 files, ~150 tests)

1. `test_audio_factory.py`
2. `test_base_audio_backend.py`
3. `test_macos_backend.py`
4. `test_wm8960_backend.py`
5. `test_audio_container.py`
6. `test_event_bus.py`
7. `test_audio_state_manager.py`
8. `test_audio_events.py`
9. `test_audio_domain_factory.py`

---

### Phase 6 - Domain Protocols (11 files, ~110 tests)

Test protocol compliance for:
1-11. All protocol interfaces with mock implementations

---

### Phase 7 - Config & Monitoring (16 files, ~160 tests)

#### Config (7)
1-7. All config modules

#### Monitoring (9)
8-16. Logger, formatters, filters

---

### Phase 8 - Utils & Common (22 files, ~220 tests)

All utility and common modules

---

## Execution Plan

### Session 1 (Current) ✅
- Domain tests: 499 tests ✅

### Session 2 (Next 30 min)
- Application controllers: 9 files, ~180 tests
- Application services: 2 files, ~40 tests
- **Subtotal**: 220 tests

### Session 3 (Next 30 min)
- API routes: 7 files, ~100 tests
- Legacy routes: 7 files, ~100 tests
- **Subtotal**: 200 tests

### Session 4 (Next 30 min)
- Infrastructure: 22 files, ~300 tests
- **Subtotal**: 300 tests

### Session 5 (Next 30 min)
- Services: 17 files, ~250 tests
- **Subtotal**: 250 tests

### Session 6 (Next 30 min)
- Audio + Protocols: 20 files, ~260 tests
- **Subtotal**: 260 tests

### Session 7 (Final)
- Config + Monitoring + Utils: 38 files, ~380 tests
- **Subtotal**: 380 tests

---

## Total Target

- **Starting**: 55 test files, ~300 tests
- **Current**: 62 test files, 499 domain tests
- **Final Target**: ~190 test files, ~2,100 tests
- **Coverage**: 95-100%

---

## Quality Assurance

### Per-File Checklist
- [ ] Imports correct
- [ ] Fixtures defined
- [ ] Happy path covered
- [ ] Error paths covered
- [ ] Edge cases included
- [ ] Mocks used appropriately
- [ ] Tests pass locally
- [ ] Fast execution (< 100ms per file)

### Batch Verification
```bash
# Run after each batch
env USE_MOCK_HARDWARE=true python3 -m pytest tests/unit/{layer}/ -q --tb=no

# Check coverage
pytest --cov=app/src --cov-report=term-missing
```

---

## Success Criteria

✅ **All tests passing**
✅ **Coverage > 95%**
✅ **Fast execution** (< 5 seconds total)
✅ **No flaky tests**
✅ **Clean architecture** maintained
✅ **Documentation** updated

---

## Next Action

**Immediate**: Create application controller tests (9 files)
**Then**: Create application service tests (2 files)
**Then**: Batch create remaining phases

Let's achieve 100% coverage! 🎯
