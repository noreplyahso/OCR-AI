# Migration Map

This file maps the current repository into the new architecture.

## Bootstrap

- `main.py`
  - old role: runtime import collector plus Qt startup
  - new role: `src/drb_inspection/app/bootstrap.py`

## UI Shell

- `lib/StackUI.py`
  - new home: `src/drb_inspection/ui/shell.py`
- `lib/Login_Screen.py`
  - new home: `src/drb_inspection/ui/screens/login/`
- `lib/Main_Screen.py`
  - new home: `src/drb_inspection/ui/screens/main/`

## Adapters

- `lib/Camera_Program.py`
  - new home: `src/drb_inspection/adapters/camera/`
  - current case: `PylonCameraAdapter` for Basler cameras
  - future extension points already reserved for Hikrobot, Irayple, and OPT vendor SDK adapters
- `lib/PLC.py`
  - new home: `src/drb_inspection/adapters/plc/`
  - current case: Mitsubishi PLC through `SLMPProtocol`
  - protocol layer still supports Modbus TCP and Modbus RTU for future Siemens/Delta/generic deployments
- `lib/Database.py`
  - new home: `src/drb_inspection/adapters/db/`

## Pipeline and Plugins

- `lib/Display.py`
  - split into:
    - `domain/inspection/`
    - `application/use_cases/`
    - `plugins/ocr/`
  - already migrated in V2:
    - OCR expected-text matching logic
    - ROI crop and clockwise rotation helper
    - legacy OCR runtime gateway boundary
- `Runtime_Software.py`
  - new role: local studio/admin tool or AI worker support code
- `RunTime_Sofware/`
  - split into:
    - `runtime/`
    - `models/`
    - plugin-owned assets

## Phase Order

1. create stable contracts and recipe format
2. move adapters behind interfaces
3. create inspection pipeline
4. move OCR execution into plugin
5. make UI consume the new use case API
6. add classify plugin
7. add segment plugin

## Current Status

Completed in V2:
- contracts and recipe loader
- inspection pipeline and cycle use case
- basic camera, PLC, and DB adapter boundaries
- OCR plugin with ROI-aware preprocess and expected-text matcher
- login/session/product flow extracted from legacy screen logic into use cases
- role-based access/profile logic extracted from `right_access()`
- screen presenter/state layer added for login and main shell flow
- Qt stacked shell added on top of the presenter layer
- runtime settings added for headless mode and optional pylon camera mode
- hardware abstraction expanded for the current Basler + Mitsubishi SLMP case while preserving the multi-vendor camera/PLC factories
- camera runtime settings now apply product exposure and session ROI/image size before preview or inspection cycle

Next:
- migrate more of the production OCR flow from `lib/Display.py`
- connect the new Qt screens to more of the real legacy UI behavior
- migrate more of the product/session/config flows from `lib/Main_Screen.py`
- execute UI parity plan in `docs/UI_PARITY_PLAN.md`
