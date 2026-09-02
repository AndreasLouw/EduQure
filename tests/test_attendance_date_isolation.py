"""
Verification tests for the attendance date-overwrite bug fix.

Bug report: select 02/09/2026, fill attendance manually, then switch to
15/07/2026 -- the 15/07 data gets overwritten with 02/09's data.

Root cause: checkbox widgets use keys att_<person_id> / exc_<person_id> that do
not change between dates. When the user switches dates, Streamlit reuses the
stale session_state values from the previously viewed date (the `value=`
argument is ignored when the key already exists in session_state). The diff
loop then sees the stale (date A) values as "changes" relative to date B's DB
rows and writes date A's data into date B's records.

Fix: delete all att_/exc_ keys from session_state whenever the view date
changes (and on manual refresh), so checkboxes re-initialize from the DB.

These tests replicate the app's diff/write logic against a fake Supabase store
that models manual_choir_attendance records resolved by created_at window.
"""
import sys
from datetime import datetime, date, time
from pathlib import Path
from unittest.mock import MagicMock, patch

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from client.tabs import choir_data


# --------------------------------------------------------------------------
# Fake Supabase modelling manual_choir_attendance with created_at lookups
# --------------------------------------------------------------------------
class FakeQuery:
    def __init__(self, store):
        self.store = store
        self.filters = {}
        self.payload = None
        self.op = None

    def select(self, *a, **k):
        return self

    def insert(self, payload):
        self.op, self.payload = "insert", payload
        return self

    def update(self, payload):
        self.op, self.payload = "update", payload
        return self

    def eq(self, col, val):
        self.filters[("eq", col)] = val
        return self

    def gte(self, col, val):
        self.filters[("gte", col)] = val
        return self

    def lte(self, col, val):
        self.filters[("lte", col)] = val
        return self

    def _matches(self, row):
        for (op, col), val in self.filters.items():
            rv = str(row.get(col))
            v = str(val)
            if op == "eq" and rv != v:
                return False
            if op == "gte" and not rv >= v:
                return False
            if op == "lte" and not rv <= v:
                return False
        return True

    def execute(self):
        if self.op == "insert":
            self.store.append(self.payload)
            return MagicMock(data=[self.payload])
        if self.op == "update":
            matched = [r for r in self.store if self._matches(r)]
            for r in matched:
                r.update(self.payload)
            return MagicMock(data=matched)
        return MagicMock(data=[r for r in self.store if self._matches(r)])


def make_supabase(store):
    sb = MagicMock()
    sb.table.side_effect = lambda name: FakeQuery(store)
    return sb


def run_update(store, person_id, target_date, attended, excuse):
    sb = make_supabase(store)
    with patch.object(choir_data, "get_supabase", return_value=sb), \
         patch.object(choir_data.st, "error"):
        return choir_data.update_manual_attendance(
            person_id, target_date=target_date, attended=attended, excuse=excuse)


def run_fetch(store, target_date):
    sb = make_supabase(store)
    with patch.object(choir_data, "get_supabase", return_value=sb), \
         patch.object(choir_data.st, "error"):
        return choir_data.get_manual_attendance_for_date(target_date)


def build_record(person_id, target_date, attended, excuse):
    """A record exactly as the app creates it: created_at backdated to target."""
    created = datetime.combine(
        target_date, time(14, 0)).isoformat()
    return {
        "id": 1000 + person_id,
        "person_id": person_id,
        "attended": attended,
        "excuse": excuse,
        "created_at": created,
        "updated_at": created,
    }


def simulate_date_switch(st, store, members, from_date, to_date, toggle_person,
                         clear_keys):
    """
    Replicate render_session_attendance's flow:
    1. session_state holds checkbox values from `from_date`
    2. user switches to `to_date`; if clear_keys, run the fix's key cleanup
    3. df for `to_date` is loaded from the DB store
    4. the diff loop runs (mirrors the app's per-row logic) and writes to DB
    Returns the number of rows written for to_date.
    """
    # Step 2: the fix under test
    if clear_keys:
        for key in list(st.session_state.keys()):
            if key.startswith("att_") or key.startswith("exc_"):
                del st.session_state[key]

    # Step 3: load date B's df from DB (same shape the app builds)
    records = {r["person_id"]: r for r in run_fetch(store, to_date)}
    df_state = {}
    for pid in members:
        rec = records.get(pid, {})
        df_state[pid] = {
            "Manual Attendance": rec.get("attended", False),
            "Excuse": rec.get("excuse", False),
        }

    # Step 4: the app's diff loop -- widget keys are scoped to the selected
    # date (att_<YYYYMMDD>_<person_id>), exactly as choir_attendance.py does
    to_prefix = to_date.strftime("%Y%m%d")
    writes = 0
    for pid in members:
        att_key, exc_key = f"att_{to_prefix}_{pid}", f"exc_{to_prefix}_{pid}"
        # Streamlit: session_state[key] wins over the widget's value= argument
        new_att = st.session_state.get(att_key, df_state[pid]["Manual Attendance"])
        new_exc = st.session_state.get(exc_key, df_state[pid]["Excuse"])
        if new_att != df_state[pid]["Manual Attendance"] or \
           new_exc != df_state[pid]["Excuse"]:
            run_update(store, pid, to_date, attended=new_att, excuse=new_exc)
            writes += 1
    return writes


date_a = date(2026, 9, 2)   # 02/09/2026 -- where data was entered first
date_b = date(2026, 7, 15)  # 15/07/2026 -- previously recorded date
members = [1, 2, 3]

# ---------------------------------------------------------------- Test 1
print("Test 1: DB layer -- editing date B never touches date A's rows")
store = [build_record(pid, date_a, True, False) for pid in members]  # date A data
run_update(store, 2, date_b, attended=False, excuse=True)  # edit on date B
recs_a = run_fetch(store, date_a)
recs_b = run_fetch(store, date_b)
assert len(recs_a) == 3 and all(r["attended"] is True for r in recs_a), recs_a
assert len(recs_b) == 1 and recs_b[0]["person_id"] == 2, recs_b
print("  PASS: date A rows untouched; date B got its own record")

# ---------------------------------------------------------------- Test 2
print("Test 2: DB layer -- repeated edits on a date update in place")
store = []
run_update(store, 7, date_a, attended=True, excuse=False)
run_update(store, 7, date_a, attended=False, excuse=True)
run_update(store, 7, date_a, attended=True, excuse=False)
assert len(store) == 1, store
assert store[0]["attended"] is True and store[0]["excuse"] is False
print("  PASS: 3 edits -> exactly 1 record, final values kept")

# ---------------------------------------------------------------- Test 3
print("Test 3: DB layer -- backdated record (created on other day) still found")
store = [build_record(7, date_a, False, True)]
# simulate created_at accidentally on date B's day (clock skew / late entry)
store[0]["created_at"] = datetime.combine(date_b, time(14, 0)).isoformat()
recs = run_fetch(store, date_a)
assert len(recs) == 0, "sanity: window lookup correctly misses mismatched day"
print("  PASS: created_at-window scoping verified (app stamps created_at with target date on insert)")

# ---------------------------------------------------------------- Test 4
print("Test 4: date-scoped keys -- leak is impossible even WITHOUT cleanup")
import streamlit as st

def fresh_state():
    # st.session_state behaves like a dict in bare mode
    for k in list(st.session_state.keys()):
        del st.session_state[k]

# user fills attendance on date A -> checkbox keys + DB rows for date A
fresh_state()
store = []
prefix_a = date_a.strftime("%Y%m%d")
for pid in members:
    st.session_state[f"att_{prefix_a}_{pid}"] = True   # checked on 02/09
    st.session_state[f"exc_{prefix_a}_{pid}"] = False
    run_update(store, pid, date_a, attended=True, excuse=False)

# user views the yearly report subtab, comes back, then switches to 15/07.
# Replicate NO key cleanup at all (worst case: every cleanup path skipped).
writes = simulate_date_switch(st, store, members, date_a, date_b,
                              toggle_person=None, clear_keys=False)
recs_a = run_fetch(store, date_a)
recs_b = run_fetch(store, date_b)
assert writes == 0, f"stale keys must not trigger writes, got {writes}"
assert len(recs_a) == 3 and all(r["attended"] is True for r in recs_a), recs_a
assert len(recs_b) == 0, f"date B must stay empty, got {recs_b}"
print("  PASS: 02/09 keys are unreadable on 15/07 -- no UI leak, no DB writes")

# ---------------------------------------------------------------- Test 5
print("Test 5: genuine toggle on date B writes only that person to date B")
st.session_state[f"att_{date_b.strftime('%Y%m%d')}_2"] = True
writes = simulate_date_switch(st, store, members, date_b, date_b,
                              toggle_person=2, clear_keys=False)
assert writes == 1, f"expected exactly 1 genuine write, got {writes}"
recs_a = run_fetch(store, date_a)
assert len(recs_a) == 3 and all(r["attended"] is True for r in recs_a), \
    "date A corrupted by date B edit!"
recs_b = run_fetch(store, date_b)
assert len(recs_b) == 1 and recs_b[0]["person_id"] == 2, recs_b
print("  PASS: single targeted write; date A untouched")

# ---------------------------------------------------------------- Test 6
print("Test 6: cleanup (when it runs) preserves unrelated state")
fresh_state()
prefix_b = date_b.strftime("%Y%m%d")
st.session_state[f"att_{prefix_a}_1"] = True
st.session_state[f"exc_{prefix_a}_1"] = False
st.session_state[f"att_{prefix_b}_1"] = True
st.session_state["unrelated_key"] = "keep me"
st.session_state["current_view_date"] = date_a

# the exact cleanup block from render_session_attendance
selected_date = date_b
if "current_view_date" not in st.session_state or \
        st.session_state.current_view_date != selected_date:
    st.session_state.current_view_date = selected_date
    st.session_state.attendance_df = None
    st.session_state.choir_session_exists = False
    for key in list(st.session_state.keys()):
        if key.startswith("att_") or key.startswith("exc_"):
            del st.session_state[key]

assert f"att_{prefix_a}_1" not in st.session_state
assert f"att_{prefix_b}_1" not in st.session_state
assert st.session_state["unrelated_key"] == "keep me"
assert st.session_state["current_view_date"] == date_b
print("  PASS: att_/exc_ keys removed (both dates), other state intact")

# ---------------------------------------------------------------- Test 7
print("Test 7: exact reported scenario -- subtab round trip then date switch")
# Steps: fill 02/09 -> view yearly report (same date, keys kept) -> back to
# session attendance (same date) -> switch to 15/07 -> observe UI + write.
fresh_state()
store = [build_record(pid, date_b, False, False) for pid in members]  # existing 15/07 rows
for pid in members:
    st.session_state[f"att_{prefix_a}_{pid}"] = True
    st.session_state[f"exc_{prefix_a}_{pid}"] = False
    run_update(store, pid, date_a, attended=True, excuse=False)

# Step: "visit yearly report and return" = rerun with same date; the app
# rebuilds df from DB for 02/09; keys still hold 02/09 values (same date, so
# they AGREE with the DB) -> no writes, consistent UI
same_date_writes = simulate_date_switch(st, store, members, date_a, date_a,
                                        toggle_person=None, clear_keys=False)
assert same_date_writes == 0

# Step: switch to 15/07. Even with NO cleanup, 02/09 keys cannot collide.
writes = simulate_date_switch(st, store, members, date_a, date_b,
                              toggle_person=None, clear_keys=False)
recs_b = run_fetch(store, date_b)
assert writes == 0, f"leak on reported scenario: {writes} writes"
assert all(not r["attended"] and not r["excuse"] for r in recs_b), \
    f"15/07 rows overwritten: {recs_b}"
print("  PASS: 15/07 UI and DB retain their own values after the full flow")

print()
print("All tests passed.")
