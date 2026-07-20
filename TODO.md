# TODO

## Goal
Make the Excel/CSV viewer reliable as a three-pane data browser, with correct filtering, row selection, and detail-column customization.

## Tasks

### 1. Stabilize Core State And Rendering
- [x] Preserve stable original row IDs through filtering and row-card rendering.
- [x] Make global search match rows when any column contains the query.
- [x] Fix `/apply` so HTMX swaps the correct row-list content and updates row counts.
- [x] Ensure selected rows reset or remain valid after search, filters, sheet changes, and file changes.

### 2. Fix Detail Column Selection
- [x] Make selected detail columns authoritative, including an intentional empty selection.
- [x] Keep the sidebar chip state consistent after All, Clear, individual chip toggles, and Apply.
- [x] Return only the intended detail-pane/sidebar fragments from detail-column updates.

### 3. Fix Sidebar Filtering And Configuration
- [x] Make chip filters submit and clear server-side state correctly.
- [x] Preserve unrelated filters while changing search, text filters, or chip filters.
- [x] Allow subtitle column selection to be cleared.
- [x] Avoid rendering active controls that can submit invalid requests before a file is loaded.

### 4. Improve Three-Pane UX
- [x] Add keyboard-accessible row cards with arrow navigation and Enter/Space selection.
- [x] Reset the detail pane scroll when a new row/detail selection renders.
- [x] Add copy-to-clipboard controls for detail values.
- [x] Keep the visual design restrained and usable for dense data inspection.

### 5. Validation And Git Checkpoints
- [x] Add focused tests for filtering, row identity, detail-column selection, and config behavior.
- [x] Run syntax checks and the test suite.
- [x] Commit completed work in logical git commits.

## Notes
- No unrelated refactors unless required to make the listed behavior correct.
- Existing user/generated files and untracked review files must not be reverted.
- The global in-memory state is acceptable for a local desktop-style tool in this pass, but it should remain clearly local-use oriented.
