"""
Regression tests for the Phase 3 data_editor attendance table.

The per-row checkbox grid was replaced with one st.data_editor. Edit
processing lives in choir_attendance.process_editor_edits (module-level so
it is testable without a Streamlit runtime). These tests pin the behaviors
the old checkbox flow guaranteed:

1. An edit targets the right PERSON (positional row -> person_id index) and
   the right DATE (update_manual_attendance receives target_date)
2. Mutual exclusivity: marking attended clears excuse and vice versa
3. Present/Time In presentation updates exactly like the old flow
   (attended -> Present set + Time In stamped when not card-present)
4. Unchecking writes the full cleared state (attended=False, excuse=False)
5. No-op edits and out-of-range rows are skipped
6. Editor widget keys remain date-scoped, and cleanup clears
   attendance_editor* keys so editor state cannot leak across dates
"""
import sys
from pathlib import Path
from datetime import date

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

import pandas as pd
from client.tabs import choir_attendance


def make_df():
    return pd.DataFrame(
        {
            "Name and Surname": ["Ann Botha", "Ben Smith", "Cara Joubert"],
            "Grade": [8, 9, 10],
            "Present": ["", "", ""],
            "Time In": ["-", "17:03", "-"],
            "Manual Attendance": [False, True, False],
            "Excuse": [False, False, True],
            "is_present_via_card": [False, True, False],
        },
        index=[101, 102, 103],
    )


# ---------------------------------------------------------------- Test 1
print("Test 1: edit targets correct person and date")
calls = []
choir_attendance.update_manual_attendance = (
    lambda pid, target_date, attended, excuse: calls.append(
        (pid, target_date, attended, excuse)
    ) or True
)
df = make_df()
n = choir_attendance.process_editor_edits(
    df, {1: {"Manual Attendance": False}}, date(2026, 9, 2), "17:05"
)
# Positional row 1 = person 102 (who was attended) -> unchecking
assert n == 1, n
assert calls == [(102, date(2026, 9, 2), False, False)], calls
assert not df.at[102, "Manual Attendance"] and not df.at[102, "Excuse"]
# Card-present member: Present stays checked, Time In (card scan) untouched
assert df.at[102, "Present"] == "✅" and df.at[102, "Time In"] == "17:03"
print("  PASS: row maps to person_id 102; uncheck persisted with full cleared state")

# ---------------------------------------------------------------- Test 2
print("Test 2: mutual exclusivity in both directions")
calls.clear()
df = make_df()
# Ann (row 0, card absent) marked attended -> excuse stays False, Present/Time In stamped
n = choir_attendance.process_editor_edits(
    df, {0: {"Manual Attendance": True}}, date(2026, 9, 2), "17:05"
)
assert n == 1 and calls[0][0] == 101
assert calls[0][2] is True and calls[0][3] is False
assert df.at[101, "Present"] == "✅" and df.at[101, "Time In"] == "17:05"

# Cara (row 2, card absent, excused) marked attended -> excuse forced False
calls.clear()
n = choir_attendance.process_editor_edits(
    df, {2: {"Manual Attendance": True}}, date(2026, 9, 2), "17:10"
)
assert calls[0][2] is True and calls[0][3] is False, calls
assert not df.at[103, "Excuse"] and df.at[103, "Present"] == "✅"

# Attending Ann then excusing her -> attended forced False
calls.clear()
n = choir_attendance.process_editor_edits(
    df, {0: {"Excuse": True}}, date(2026, 9, 2), "17:12"
)
assert calls[0][2] is False and calls[0][3] is True, calls
assert not df.at[101, "Manual Attendance"]
assert df.at[101, "Present"] == "📝" and df.at[101, "Time In"] == "-"
print("  PASS: attend clears excuse; excuse clears attend; presentation follows")

# ---------------------------------------------------------------- Test 3
print("Test 3: no-op edits and out-of-range rows skipped")
calls.clear()
df = make_df()
n = choir_attendance.process_editor_edits(
    df,
    {0: {"Manual Attendance": False}, 2: {"Excuse": True}, 99: {"Excuse": True}, "x": {"Excuse": True}},
    date(2026, 9, 2),
    "17:05",
)
assert n == 0 and calls == [], (n, calls)
print("  PASS: same-value edits and bad row indices produce no writes")

# ---------------------------------------------------------------- Test 4
print("Test 4: batch of edits in one pass")
calls.clear()
df = make_df()
n = choir_attendance.process_editor_edits(
    df,
    {0: {"Manual Attendance": True}, 1: {"Excuse": True}},
    date(2026, 9, 2),
    "17:05",
)
assert n == 2
assert {c[0]: (c[2], c[3]) for c in calls} == {101: (True, False), 102: (False, True)}
# Ben (102) was card-present: excusing him keeps Present, Time In untouched
assert df.at[102, "Present"] == "✅" and df.at[102, "Time In"] == "17:03"
print("  PASS: multiple edits applied in one call")

# ---------------------------------------------------------------- Test 5
print("Test 5: editor keys date-scoped; cleanup clears attendance_editor* keys")
import inspect
src = inspect.getsource(choir_attendance)
assert 'f"attendance_editor_{date_prefix}"' in src, "editor key must be date-scoped"
assert src.count('key.startswith("attendance_editor")') >= 2, \
    "date-change and refresh cleanups must both clear editor keys"
# Simulate the cleanup semantics: stale key from another date is removed
fake_state = {"attendance_editor_20260715": {}, "attendance_editor_20260902": {}}
for key in list(fake_state.keys()):
    if key.startswith("attendance_editor"):
        del fake_state[key]
assert fake_state == {}, fake_state
print("  PASS: editor state cannot leak across dates")

# ---------------------------------------------------------------- Test 6
print("Test 6: editor widget key is never assigned to (forbidden in Streamlit 1.52+)")
assert 'st.session_state[editor_key] =' not in src, (
    "writing to a st.data_editor widget key raises "
    "StreamlitValueAssignmentNotAllowedError (writes_allowed=False)"
)
print("  PASS: no forbidden write to the editor key")

print()
print("All tests passed.")
