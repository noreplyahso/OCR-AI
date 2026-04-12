# UI Parity Plan

This file defines the UI refactor plan for V2.

Rule:
- V1 is the source of truth for operator-facing behavior and visual priority.
- V2 keeps the new architecture, but the runtime UI must behave like V1 where V1 already works well.
- Debug and artifact features added in V2 are allowed, but they must not dominate the operator workflow.

## Scope

This plan covers:
- login screen parity
- main runtime screen parity
- operator workflow parity
- safe placement of V2-only diagnostics

This plan does not yet cover:
- training/admin studio screens
- classify/segment dedicated screens
- installer branding

## Source Files

V1 reference:
- `form_UI/screenLogin.ui`
- `form_UI/screenMain.ui`
- `lib/Login_Screen.py`
- `lib/Main_Screen.py`

V2 target:
- `src/drb_inspection/ui/qt/login_widget.py`
- `src/drb_inspection/ui/qt/main_widget.py`
- `src/drb_inspection/ui/qt/theme.py`
- `src/drb_inspection/ui/shell.py`

## Gap Summary

Current V2 status:
- login and main flow work
- hardware/runtime functions exist
- OCR/debug/history/artifact features exist
- visual hierarchy does not match V1

Main gaps:
- V2 login lacks V1 branding and visual identity
- V2 main screen is debug-first instead of operator-first
- preview/result/action areas are not visually dominant enough
- V2 exposes too much configuration on the main runtime surface
- V1 uses stronger visual status language for connected/disconnected, auto/manual, OK/NG, checking

## Design Rules

These rules must stay fixed during UI work:

1. The primary focus of the runtime screen is:
   - live image
   - result
   - machine actions

2. Runtime operators should not need to scan debug text to understand machine state.

3. Configuration and diagnostics must move to secondary panels, drawers, tabs, or collapsible sections.

4. Buttons and status colors should follow V1 semantics:
   - connected/on/active: highlighted
   - disconnected/off/inactive: muted
   - OK: green emphasis
   - NG: red emphasis
   - Checking: neutral animated or clearly transitional

5. Keep the V2 architecture:
   - presenters, state objects, and use cases remain intact
   - only widget composition, layout, and rendering priority change

## Phase Plan

### Phase 1: Login Screen Parity

Goal:
- make V2 login feel like the V1 product, not a generic admin form

Tasks:
- add DRB/Vision Center branding area
- add background treatment inspired by V1
- move login form into centered branded card
- add clear password toggle button
- preserve current login logic and validation messages
- remove demo-oriented wording from the runtime-facing login surface

Acceptance:
- user can recognize the screen as the same product family as V1
- login still transitions to main reliably
- no hardware call is triggered just by rendering login

### Phase 2: Main Screen Layout Parity

Goal:
- make the screen visually operator-first like V1

Tasks:
- promote live preview block to the primary central area
- promote result/status block near preview
- group runtime control buttons like V1:
  - connect/disconnect camera
  - connect/disconnect PLC
  - live camera
  - real-time / AI checking
  - auto/manual
  - record
  - reset counter
- compress the current top header into a thin status strip
- move session/product/config controls into a dedicated settings panel
- keep artifact/history/diagnostics in a secondary area or collapsible panel

Acceptance:
- operator can identify result, preview, and control buttons within one glance
- debug text is visible only when needed, not dominant

### Phase 3: Status Language Parity

Goal:
- make V2 status feedback behave visually like V1

Tasks:
- add stronger result badge styling for:
  - OK
  - NG
  - Checking
  - No cycle
- add stronger button state styling for:
  - auto/manual
  - AI checking
  - live preview
  - camera connected/disconnected
  - PLC connected/disconnected
- ensure transitions are obvious during cycle hold and live resume

Acceptance:
- user can understand machine state without reading the diagnostics panel

### Phase 4: Runtime Workflow Parity

Goal:
- align operator workflow with V1 while keeping V2 internals

Tasks:
- keep main actions on the runtime surface only
- move rarely-used edits to settings section
- ensure preview/result sequence mirrors V1:
  - live
  - grab/check
  - hold result
  - resume
- ensure OCR empty state still shows `Checking`
- ensure cycle counters and quantity are visually close to result area

Acceptance:
- same operator can use V2 with minimal retraining from V1

### Phase 5: Secondary Panels for V2 Additions

Goal:
- keep V2 debug power without harming the operator UI

Tasks:
- place OCR diagnostics in a collapsible section
- place recent history in a collapsible section or bottom drawer
- place artifact links in a collapsible section
- keep advanced ROI movement controls in a secondary settings area

Acceptance:
- V2 keeps its debug advantages
- operator-facing surface remains clean

## Implementation Order

Implement in this exact order:

1. Login visual parity
2. Main screen layout parity
3. Status styling parity
4. Runtime workflow parity
5. Secondary debug panels cleanup

Reason:
- layout and hierarchy must be fixed first
- only after that should detailed control placement be adjusted

## Safe Refactor Rules

While implementing the UI plan:
- do not change use case contracts unless the widget layer cannot support the required behavior
- do not change OCR result rules during pure UI work
- do not move hardware calls into widget constructors
- do not auto-connect hardware during screen render
- do not reintroduce auto-preview on login for hardware camera

## Definition Of Done

UI parity is complete when:
- V2 login is visually recognizable as the V1 product family
- V2 main screen prioritizes preview, result, and runtime controls like V1
- operator workflows are possible without opening debug panels
- debug/history/artifact functions still exist but are secondary
- Basler + Mitsubishi runtime can be used from the V2 main screen without screen-blocking issues

## Execution Checklist

- [ ] Phase 1 login screen parity
- [ ] Phase 2 main screen layout parity
- [ ] Phase 3 status language parity
- [ ] Phase 4 runtime workflow parity
- [ ] Phase 5 secondary debug panels cleanup
- [ ] Basler runtime smoke test after UI changes
- [ ] Regression test: `python -m pytest DRB-OCR-AI-V2/tests -q`

