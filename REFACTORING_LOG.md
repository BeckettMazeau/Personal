# Refactoring Log

## Identified Slop

1. **Simulated Delays in Frontend:**
   - Location: `FileCutter/frontend/src/components/ReviewInterface.jsx` in the `fetchFiles` function.
   - Details: Code contains `await new Promise(r => setTimeout(r, 600));` and `setTimeout(..., 800)` to simulate loading states that should just be derived from the actual API fetch.
   - Action: Remove `setTimeout` functions and directly fetch data from the API.

2. **Inline Styles in Frontend:**
   - Location: `FileCutter/frontend/src/components/ReviewInterface.jsx`.
   - Details: Header, Quick Select, and Loading Screen have heavy inline styles.
   - Action: Extract inline styles into `FileCutter/frontend/src/components/ReviewInterface.css`.

3. **Monolithic Frontend Component:**
   - Location: `FileCutter/frontend/src/components/ReviewInterface.jsx`.
   - Details: Component handles header, quick selection, file listing, and previewing all within a single file.
   - Action: Refactor by creating smaller components such as `ReviewHeader.jsx` and `QuickSelectBar.jsx`.

4. **Duplicated JSON Parsing Logic in Backend:**
   - Location: `FileCutter/backend/app/services/ai_orchestrator.py`.
   - Details: Stripping markdown `` ```json `` and parsing logic is duplicated in `tier_1_evaluation` and `tier_2_evaluation`.
   - Action: Extract logic to `clean_and_parse_json` in `FileCutter/backend/app/core/utils.py`.

5. **Hardcoded Database Paths and Cache Logic:**
   - Location: `FileCutter/backend/app/services/ai_orchestrator.py`.
   - Details: `ai_orchestrator.py` contains direct SQLite interactions and a hardcoded `file_cache.db`.
   - Action: Move path to `FileCutter/backend/app/core/config.py` and extract database operations to `FileCutter/backend/app/core/cache.py`.

6. **Unused Imports and Clean-Up:**
   - Location: Various files.
   - Details: Leftover imports and boilerplate from initial AI generation.
   - Action: Audit imports after refactoring.
