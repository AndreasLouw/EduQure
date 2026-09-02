"""
Regression tests for selection-scoped widget keys in choir_management.py.

Bug class (same as the attendance date-overwrite): Streamlit widget state
persists in session_state under its key. When a widget's key already exists,
the widget's value= argument is IGNORED. Field widgets keyed without the
selected entity (person) carried the previously selected person's values into
the next selection, so "Update Person" wrote person A's name/surname/grade to
person B's record.

The fix scopes edit-field keys to the selected person id:
edit_name_<id> / edit_surname_<id> / edit_grade_<id>.

The FakeSessionState class replicates the exact Streamlit semantics the app
relies on: __getitem__/get return the stored value if the key exists,
otherwise the widget's value= argument is used and then stored.
"""
import inspect
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from client.tabs import choir_management


class FakeSessionState:
    """Mimics st.session_state: keys persist; value= only applies when absent."""
    def __init__(self):
        self._d = {}

    def __contains__(self, k):
        return k in self._d

    def get(self, k, default=None):
        return self._d.get(k, default)

    def __getitem__(self, k):
        return self._d[k]

    def __setitem__(self, k, v):
        self._d[k] = v

    def __delitem__(self, k):
        del self._d[k]

    def keys(self):
        return self._d.keys()


def render_edit_fields(st_state, person_id, person_data, key_naming):
    """
    Replicate render_persons_management's field rendering for the given person.
    key_naming(person_id) -> (name_key, surname_key) so both the old shared
    scheme and the new person-scoped scheme can be simulated.
    Returns the values the 'Update Person' handler would see.
    Mirrors the app: text_input(value=current, key=...) -- if key exists in
    session_state, its stored value wins over value=.
    """
    name_key, surname_key = key_naming(person_id)

    def text_input(label, value, key):
        if key in st_state:
            return st_state[key]
        st_state[key] = value
        return value

    new_name = text_input("Name", person_data["Name"], name_key)
    new_surname = text_input("Surname", person_data["Surname"], surname_key)
    return new_name, new_surname


OLD_KEYS = lambda pid: ("edit_name", "edit_surname")  # pre-fix shared keys
NEW_KEYS = lambda pid: (f"edit_name_{pid}", f"edit_surname_{pid}")  # fixed

# ---------------------------------------------------------------- Test 1
print("Test 1: OLD key scheme (shared keys) corrupts data -- reproduces bug")
st_state = FakeSessionState()

# Person A rendered first: fields initialize from A's record
name_a, surname_a = render_edit_fields(st_state, "id-A",
                                       {"Name": "John", "Surname": "Doe"}, OLD_KEYS)
assert (name_a, surname_a) == ("John", "Doe")

# User edits A's surname in the UI
st_state["edit_surname"] = "Smith"

# User now selects person B (old app used the SAME keys for everyone)
name_b, surname_b = render_edit_fields(st_state, "id-B",
                                       {"Name": "Jane", "Surname": "Roe"}, OLD_KEYS)
assert (name_b, surname_b) == ("John", "Smith"), (name_b, surname_b)
print("  PASS: reproduced -- B's form shows A's data entirely (John Smith); Update would write A's identity to B")

# ---------------------------------------------------------------- Test 2
print("Test 2: NEW key scheme (person-scoped) -- no cross-person leak")
st_state = FakeSessionState()

name_a, surname_a = render_edit_fields(st_state, "id-A",
                                       {"Name": "John", "Surname": "Doe"}, NEW_KEYS)
assert (name_a, surname_a) == ("John", "Doe")
st_state["edit_surname_id-A"] = "Smith"  # user edits A's surname

name_b, surname_b = render_edit_fields(st_state, "id-B",
                                       {"Name": "Jane", "Surname": "Roe"}, NEW_KEYS)
assert (name_b, surname_b) == ("Jane", "Roe"), (name_b, surname_b)
print("  PASS: B's form initializes from B's own record")

# Switching back to A still shows A's in-progress edit (per-person state)
name_a2, surname_a2 = render_edit_fields(st_state, "id-A",
                                         {"Name": "John", "Surname": "Doe"}, NEW_KEYS)
assert (name_a2, surname_a2) == ("John", "Smith")
print("  PASS: A's in-progress edit preserved; state is per-person, not global")

# ---------------------------------------------------------------- Test 3
print("Test 3: app source actually uses person-scoped edit keys")
import inspect
src = inspect.getsource(choir_management)
assert 'key=f"edit_name_{person_suffix}"' in src
assert 'key=f"edit_surname_{person_suffix}"' in src
assert 'key=f"edit_grade_{person_suffix}"' in src
assert 'key="edit_name"' not in src and 'key="edit_surname"' not in src \
       and 'key="edit_grade"' not in src
print("  PASS: shared edit keys removed from source")

print()
print("All tests passed.")
