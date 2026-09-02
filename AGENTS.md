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

## Key domain knowledge

- `manual_choir_attendance` table: records are scoped to a date via the
  `created_at` window; inserts stamp `created_at` with the target practice
  date (see `update_manual_attendance` in `client/tabs/choir_data.py`).
  There is no confirmed `date` column — don't query one without checking.
- Attendance checkboxes use session_state keys `att_<person_id>` /
  `exc_<person_id>`. These are shared across all dates; when adding views
  that change per-date context, clear them (see `render_session_attendance`).
  Fixed cross-date overwrite bug in commit 788863b.

## Tests

- `tests/test_attendance_date_isolation.py` — regression test for the
  cross-date attendance overwrite. Run: `python tests/test_attendance_date_isolation.py`
  (plain script, no pytest infra in repo; needs streamlit + supabase installed).
