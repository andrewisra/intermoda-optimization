# Clean Refactor Notes

This branch is a clean refactor, not a safe legacy integration.

## Removed Legacy Concept

The previous mixed branch kept both systems:

- old `/eta`, `/density`, `/optimizer` modules, and
- new `/api/aits` modules.

This clean branch removes that dual-system approach. The project now has one final architecture under `src/aits` and one set of API routes.

## Teammate Work Migrated

The teammate GTFS pipeline was not discarded. It was migrated into:

- `src/aits/data/gtfs_downloader.py`
- `src/aits/data/gtfs_parser.py`
- `data/raw/gtfs_transjakarta.zip`

## Final API Routes

- `POST /api/predict/eta`
- `POST /api/predict/density`
- `POST /api/optimize/transfer`
- `GET /api/data/reference`
- `GET /api/data/simulator`
- `POST /api/incidents`

## Final Narrative

AITS treats MRT/LRT/KRL as fixed rail schedule anchors. AI predicts ETA and density. Personalized walking time and missed-connection risk scoring are used by a constraint-based optimizer to recommend non-rail operational actions.
