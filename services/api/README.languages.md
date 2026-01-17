# Pack 21 — Multi-Language Support (i18n)

This pack introduces a simple, extensible language and translation layer to the API, plus a minimal UI dashboard for quick manual testing.

## Endpoints

- GET /api/languages/languages
  - Returns a list of available languages: `[ { code, name } ]`

- GET /api/languages/translate/{content_id}/{lang_code}
  - Returns a translation object: `{ content_id, language, text }`
  - Demo content IDs included: `content_001`, `content_002`
  - Supported language codes: `en`, `es`, `fr` (demo)

## UI Dashboard

- GET /api/ui-dashboard/lang-dashboard-ui
  - Simple HTML page to fetch languages and translate sample content.

## Notes

- Current implementation uses an in-memory table of demo translations in `app/lang/service.py`.
- Replace with a database-backed or external i18n provider as needed.
- The router is guarded in `main.py` so the app remains robust if the i18n module is modified or temporarily unavailable.
