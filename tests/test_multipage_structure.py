"""
Regression tests for the Phase 2 multipage conversion.

With st.tabs, ALL four section bodies executed on every full rerun, firing
every section's Supabase queries even when the user was looking at one tab.
The app now uses st.navigation/st.Page, so only the active page executes.

These tests verify the structure that guarantees that behavior:
1. secured_dashboard uses st.navigation with all 4 pages and no global st.tabs
2. Login gating is preserved (login renders instead of page.run when unauthenticated)
3. Sidebar refresh (cache clear) and logout survive the conversion
4. Every page module still exposes render()
5. requirements.txt keeps streamlit unpinned/compatible (st.navigation needs >= 1.36;
   env runs 1.63)
"""
import sys
import re
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

import inspect
from client import secured_dashboard
from client.utils import auth
from client.tabs import choir_attendance, live_monitor, access_logs, choir_management

# ---------------------------------------------------------------- Test 1
print("Test 1: st.navigation multipage with all 4 sections; no global st.tabs")
src = inspect.getsource(secured_dashboard)
assert "st.navigation" in src, "dashboard must use st.navigation"
assert "st.tabs(" not in src, "global st.tabs must be gone"
for mod_name in ["choir_attendance", "live_monitor", "access_logs", "choir_management"]:
    assert f"{mod_name}.render" in src, f"page missing: {mod_name}"
assert "default=True" in src, "attendance must be the default page"
# Every page needs an explicit unique url_path: Streamlit infers the pathname
# from callable.__name__ (all our entry points are named "render"), and the
# duplicate-pathname check only runs with a live script-run context, so it
# cannot be caught in bare-mode tests. Source-level assertion is the guard.
paths = re.findall(r'url_path="([^"]+)"', src)
assert len(paths) == 4, f"expected 4 explicit url_paths, got {paths}"
assert len(set(paths)) == 4, f"url_paths must be unique, got {paths}"
print("  PASS: 4 pages registered with unique url_paths, attendance default")

# ---------------------------------------------------------------- Test 2
print("Test 2: login gating preserved")
main_src = inspect.getsource(secured_dashboard.main)
assert "if not st.session_state.authenticated" in main_src
assert "login()" in main_src
assert main_src.index("login()") < main_src.index("st.navigation"), \
    "login gate must run before navigation"
print("  PASS: unauthenticated users hit login, never a page")

# ---------------------------------------------------------------- Test 3
print("Test 3: sidebar refresh clears caches; logout intact")
sidebar_src = inspect.getsource(auth.render_sidebar)
assert "st.cache_data.clear()" in sidebar_src, "refresh must clear caches"
assert "Log Out" in sidebar_src and "logout()" in sidebar_src
assert "School Attendance Live Feed" in sidebar_src, "app title must persist across pages"
print("  PASS: title, user info, refresh, logout all in sidebar")

# ---------------------------------------------------------------- Test 4
print("Test 4: page modules expose render entry points")
for mod in [choir_attendance, live_monitor, access_logs, choir_management]:
    assert callable(getattr(mod, "render", None)), f"{mod.__name__} missing render()"
print("  PASS: all render() entry points callable")

# ---------------------------------------------------------------- Test 5
print("Test 5: streamlit version supports st.navigation (>= 1.36)")
import streamlit
ver = tuple(int(x) for x in streamlit.__version__.split(".")[:2])
assert ver >= (1, 36), f"streamlit {streamlit.__version__} lacks st.navigation"
req = (Path(__file__).resolve().parent.parent / "requirements.txt").read_text()
assert "streamlit==" not in req, "pinned streamlit may predate st.navigation on deploy"
print(f"  PASS: streamlit {streamlit.__version__}; requirements unpinned")

print()
print("All tests passed.")
