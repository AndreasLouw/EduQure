"""
Regression tests for the Phase 1 performance work.

The old yearly report issued 2 Supabase queries PER practice date (2N total,
N = number of practice dates). The rewrite fetches all access logs and all
manual attendance for the year in 2 total queries and groups them in memory.

These tests verify:
1. get_logs_for_year / get_manual_attendance_for_year exist and the yearly
   report source no longer calls the per-date fetchers
2. build_yearly_matrix (extracted logic) groups by day correctly:
   - card-scan uids are matched per calendar day
   - manual attendance per day from the created_at grouping
   - excused-only days count as excused, not attended
   - percentage ignores excused days
3. day-boundary correctness: a scan at 23:59 and 00:01 land on their own days
"""
import sys
from pathlib import Path
from datetime import datetime, date

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from client.tabs import choir_data, choir_yearly_report


# ---------------------------------------------------------------- Test 1
print("Test 1: year fetchers exist; per-date fetchers removed from yearly report source")
import inspect

assert hasattr(choir_data, "get_logs_for_year"), "missing get_logs_for_year"
assert hasattr(choir_data, "get_manual_attendance_for_year"), "missing get_manual_attendance_for_year"

src = inspect.getsource(choir_yearly_report)
assert "get_logs_for_date_range" not in src, "yearly report still uses per-date log fetch"
assert "get_manual_attendance_for_date" not in src, "yearly report still uses per-date manual fetch"
assert "get_logs_for_year" in src and "get_manual_attendance_for_year" in src
print("  PASS: 2-query implementation wired in")

# ---------------------------------------------------------------- Test 2
print("Test 2: build_yearly_matrix groups data per day correctly")


def build_yearly_matrix(choir_rows, practice_days, logs, manual_by_day):
    """
    Extracted mirror of render_yearly_report's core logic so it can be tested
    without Supabase. choir_rows: list of dicts with name, surname, card_uid,
    person_id. practice_days: list of date objects. logs: list of dicts with
    card_uid + created_at. manual_by_day: {date: [records]}.
    """
    log_uids_by_day = {}
    if logs:
        dfl = __import__("pandas").DataFrame(logs)
        dfl = dfl.dropna(subset=["created_at"])
        days = __import__("pandas").to_datetime(dfl["created_at"]).dt.date
        for day, group in dfl.groupby(days):
            log_uids_by_day[day] = set(group["card_uid"].dropna().unique())

    matrix = []
    for person in choir_rows:
        row_data = {"Name": f"{person['name']} {person['surname']}"}
        total_attended = 0
        excused_count = 0
        for d in practice_days:
            in_logs = person.get("card_uid") in log_uids_by_day.get(d, set())
            day_records = manual_by_day.get(d, [])
            in_manual = any(r.get("person_id") == person["person_id"] and r.get("attended")
                            for r in day_records)
            in_excused = any(r.get("person_id") == person["person_id"] and r.get("excuse")
                             for r in day_records)
            if in_logs or in_manual:
                row_data[str(d)] = "Y"
                total_attended += 1
            elif in_excused:
                row_data[str(d)] = "E"
                excused_count += 1
            else:
                row_data[str(d)] = "N"
        row_data["Total"] = total_attended
        net = len(practice_days) - excused_count
        row_data["%"] = f"{total_attended / net * 100:.1f}%" if net > 0 else "N/A"
        matrix.append(row_data)
    return matrix


d1, d2, d3 = date(2026, 7, 15), date(2026, 9, 2), date(2026, 9, 9)
choir = [{"name": "Ann", "surname": "Botha", "card_uid": "UID1", "person_id": 1},
         {"name": "Ben", "surname": "Smith", "card_uid": None, "person_id": 2}]

# Ann scanned a card on d1 at 17:05; manual record marks her attended on d2;
# Ben excused on d2; nothing on d3 for anyone.
logs = [{"card_uid": "UID1", "created_at": datetime(2026, 7, 15, 17, 5).isoformat()}]
manual = {
    d2: [{"person_id": 1, "attended": True, "excuse": False},
         {"person_id": 2, "attended": False, "excuse": True}],
}
matrix = build_yearly_matrix(choir, [d1, d2, d3], logs, manual)

ann, ben = matrix[0], matrix[1]
assert ann[str(d1)] == "Y" and ann[str(d2)] == "Y" and ann[str(d3)] == "N", ann
assert ann["Total"] == 2 and ann["%"] == "66.7%", ann
assert ben[str(d1)] == "N" and ben[str(d2)] == "E" and ben[str(d3)] == "N", ben
assert ben["Total"] == 0 and ben["%"] == "0.0%", ben  # net = 3 - 1 excused = 2 -> 0/2 = 0.0%
print("  PASS: card scan, manual attendance, excuse, and percentages all correct")

# ---------------------------------------------------------------- Test 3
print("Test 3: day-boundary handling (23:59 vs 00:01 scans)")
logs = [
    {"card_uid": "UID1", "created_at": datetime(2026, 7, 15, 23, 59).isoformat()},
    {"card_uid": "UID1", "created_at": datetime(2026, 7, 16, 0, 1).isoformat()},
]
manual = {}
matrix = build_yearly_matrix(choir, [date(2026, 7, 15), date(2026, 7, 16)], logs, manual)
ann = matrix[0]
assert ann["2026-07-15"] == "Y" and ann["2026-07-16"] == "Y", ann
print("  PASS: scans grouped to their own calendar days")

# ---------------------------------------------------------------- Test 4
print("Test 4: write functions invalidate the year cache")
import streamlit as st

# Simulate: cache populated for 2026
st.cache_data.clear()  # baseline
choir_data.get_manual_attendance_for_year(2026)
# After a manual attendance write the cache must be cleared
# (update_manual_attendance calls get_manual_attendance_for_year.clear())
import re
src_update = inspect.getsource(choir_data.update_manual_attendance)
assert "get_manual_attendance_for_year.clear()" in src_update
src_mgmt = __import__("importlib").import_module("client.tabs.choir_management")
assert hasattr(src_mgmt, "clear_write_related_caches")
mgmt_src = inspect.getsource(src_mgmt)
for fn in ["add_person_to_choir", "remove_person_from_choir", "delete_practice_date",
           "add_practice_date", "update_person", "add_new_person", "delete_person"]:
    body = inspect.getsource(getattr(src_mgmt, fn))
    assert "clear_write_related_caches()" in body, f"{fn} does not invalidate caches"
print("  PASS: every Management write path invalidates caches")

print()
print("All tests passed.")
