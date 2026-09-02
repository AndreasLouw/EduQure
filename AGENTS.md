# EduQure — Agent Notes

## User preferences (always apply)

- **Never add `Co-authored-by` trailers to commits.** Do not add
  `Co-authored-by: openhands <openhands@all-hands.dev>` or any other
  co-author trailer.
- Git identity: user.name "Andreas Louw", user.email "andreaslouw@gmail.com"
  (set globally; do not override repo-locally).

## Project layout

- Streamlit app; entry point `client/secured_dashboard.py` (see `streamlit_app.py`).
- `client/tabs/` — feature tabs; `client/utils/` — supabase client + auth.
- DB is Supabase (PostgREST). Schema docs in `client/README.md` are stale —
  verify columns against live usage in code before relying on them.

## Architecture: multipage app (Phase 2)

- `client/secured_dashboard.py` uses `st.navigation`/`st.Page` — only the
  active page's code (and its queries) execute per rerun. Never convert back
  to global `st.tabs`; all tab bodies executed on every rerun before this.
- Pages: Choir Attendance (default), Live Monitor, Access Logs, Management.
- Login gates BEFORE `st.navigation`; unauthenticated users never hit a page.
- Sidebar (app title, user, 🔄 Refresh Data, Log Out) is
  `client/utils/auth.py:render_sidebar()`. 🔄 Refresh Data calls
  `st.cache_data.clear()` then reruns — instant freshness for cached fetches.

## Caching (Phase 1)

- All read fetchers use `st.cache_data`: choir members / practice dates /
  yearly manual attendance (60s), access logs / unidentified cards (30s),
  persons (60s).
- Write paths MUST invalidate caches: `update_manual_attendance` clears the
  year cache; all Management writes call `clear_write_related_caches()`.
  Any new write function must follow this pattern.
- Yearly report fetches the whole year in 2 queries (`get_logs_for_year`,
  `get_manual_attendance_for_year`) — never reintroduce per-date query loops.

## Streamlit session-state gotcha (the overwrite bug class)

- When a widget's `key` exists in `session_state`, its `value=` argument is
  IGNORED. Unscoped keys leak the previous selection's values into the next
  one. This caused two real bugs: attendance checkboxes across dates (fixed
  788863b, then 9cedd71) and person-edit fields across persons (962c1a4).
- RULE: scope widget keys to the entity they edit — `att_<YYYYMMDD>_<pid>`,
  `edit_name_<person_id>`, etc. Shared keys are a data-corruption risk.

## Tests

- Plain scripts (no pytest infra): `python tests/test_<name>.py` from repo
  root; each inserts the repo root into `sys.path` and replicates app logic
  with fakes (bare-mode Streamlit semantics).
- `test_attendance_date_isolation.py` — cross-date attendance overwrite.
- `test_person_edit_key_scoping.py` — person-edit key leak.
- `test_yearly_report_queries.py` — 2-query yearly report + cache invalidation.
- `test_multipage_structure.py` — st.navigation structure + login gating.

## Key domain knowledge

- `manual_choir_attendance` table: records are scoped to a date via the
  `created_at` window; inserts stamp `created_at` with the target practice
  date (see `update_manual_attendance` in `client/tabs/choir_data.py`).
  There is no confirmed `date` column — don't query one without checking.
- Attendance checkbox keys are date-scoped (`att_<YYYYMMDD>_<person_id>`),
  so cross-date leaks are structurally impossible; date-change cleanup in
  `render_session_attendance` still resets df/pending state.

## Branches

- `main` — stable. `develop` — active work; phase commits land here.
