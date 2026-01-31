# supabase_client.py

## Purpose

This utility module provides a **centralized Supabase client initialization** for the Streamlit dashboard. It handles credential loading from multiple sources (environment variables or Streamlit secrets) and caches the client instance for performance.

## Key Functions

### `get_secret(key_name)`

**Purpose:** Retrieves secrets from Streamlit secrets or environment variables

**Parameters:**
- `key_name` - Name of the secret to retrieve (e.g., "SUPABASE_URL")

**Returns:**
- Secret value as string
- `None` if not found

**Priority Order:**
1. Streamlit secrets (for cloud deployment)
2. Environment variables (for local development)

**Example:**
```python
url = get_secret("SUPABASE_URL")
# Checks st.secrets["SUPABASE_URL"] first
# Falls back to os.environ.get("SUPABASE_URL")
```

---

### `init_supabase()`

**Purpose:** Initializes and caches the Supabase client instance

**Decorator:** `@st.cache_resource`
- Ensures only one client is created per session
- Improves performance by avoiding repeated initialization

**Returns:**
- Supabase client instance

**Error Handling:**
- Displays error message if credentials are missing
- Stops app execution with `st.stop()` if initialization fails

**Example:**
```python
client = init_supabase()
# Client is cached and reused across page reruns
```

---

### `get_supabase()`

**Purpose:** Public interface to get the Supabase client

**Returns:**
- Cached Supabase client instance

**Usage:**
```python
from client.utils.supabase_client import get_supabase

supabase = get_supabase()
response = supabase.table("persons").select("*").execute()
```

## Configuration

### Environment Variables (.env)

```env
SUPABASE_URL=https://yourproject.supabase.co
SUPABASE_KEY=your.anon.key.here
```

### Streamlit Secrets (.streamlit/secrets.toml)

For Streamlit Cloud deployment:

```toml
SUPABASE_URL = "https://yourproject.supabase.co"
SUPABASE_KEY = "your.anon.key.here"
```

## Caching Strategy

The `@st.cache_resource` decorator ensures:

1. **Single Instance:** Only one Supabase client is created
2. **Persistent Connection:** Client survives page reruns
3. **Performance:** Avoids repeated initialization overhead

**Cache Clearing:**
```python
# If you need to refresh the client (e.g., credentials changed)
st.cache_resource.clear()
```

## Error Messages

| Error | Cause | Solution |
|-------|-------|----------|
| "Supabase URL and Key not found" | Missing .env or secrets | Create .env with credentials |
| No error but data won't load | Wrong credentials | Verify URL and key in Supabase dashboard |

## Security Best Practices

### ✅ DO
- Use anon/public key (not service_role key)
- Store credentials in .env (local) or secrets.toml (cloud)
- Add .env to .gitignore
- Enable Row Level Security (RLS) in Supabase

### ❌ DON'T
- Hardcode credentials in this file
- Commit .env or secrets.toml to Git
- Use service_role key in client code
- Share credentials publicly

## Usage Examples

### Basic Query

```python
from client.utils.supabase_client import get_supabase

def get_all_users():
    supabase = get_supabase()
    response = supabase.table("persons").select("*").execute()
    return response.data
```

### Insert Data

```python
def add_person(name, surname, card_uid):
    supabase = get_supabase()
    data = {
        "name": name,
        "surname": surname,
        "card_uid": card_uid
    }
    supabase.table("persons").insert(data).execute()
```

### Update Data

```python
def update_person(person_id, new_grade):
    supabase = get_supabase()
    supabase.table("persons").update({"grade": new_grade}).eq("id", person_id).execute()
```

### Delete Data

```python
def delete_person(person_id):
    supabase = get_supabase()
    supabase.table("persons").delete().eq("id", person_id).execute()
```

## Troubleshooting

### Client Not Initializing

**Symptoms:**
- Error message "Supabase URL and Key not found"
- App stops on load

**Solutions:**
1. Check .env file exists in `client/` directory
2. Verify variable names: `SUPABASE_URL` and `SUPABASE_KEY`
3. Ensure no extra spaces or quotes in .env
4. For Streamlit Cloud, check secrets in app settings

### Connection Errors

**Symptoms:**
- "Connection refused" or network errors
- Long timeout before error

**Solutions:**
1. Verify Supabase project is not paused
2. Check internet connectivity
3. Verify SUPABASE_URL is correct
4. Test URL in browser (should show Supabase page)

### Authentication Errors

**Symptoms:**
- 401 Unauthorized errors
- RLS policy violations

**Solutions:**
1. Verify SUPABASE_KEY is the anon key (not service_role)
2. Check RLS policies allow operation for anonymous users
3. Ensure tables have proper RLS policies enabled

## Dependencies

```python
import streamlit as st
import os
from dotenv import load_dotenv
from supabase import create_client
```

**Required Packages:**
- `streamlit` - Web framework
- `python-dotenv` - Environment variable loading
- `supabase` - Supabase Python client

Install via:
```bash
pip install streamlit python-dotenv supabase
```

## Integration with Other Modules

This module is imported by:

- **auth.py** - For authentication operations
- **choir_attendance.py** - For attendance queries
- **live_monitor.py** - For real-time monitoring
- **access_logs.py** - For historical log viewing

**Import Pattern:**
```python
from client.utils.supabase_client import get_supabase

supabase = get_supabase()
# Use supabase client...
```

## Performance Considerations

**Why Caching Matters:**
- Supabase client initialization involves SSL handshake
- Creating new client on every query would be slow
- `@st.cache_resource` reuses single instance

**Cache Lifecycle:**
- Created on first call to `init_supabase()`
- Persists for entire Streamlit session
- Survives page reruns and tab switches
- Cleared only on:
  - App restart
  - Manual `st.cache_resource.clear()`
  - Streamlit server restart

## Testing

### Test Connection

```python
# Run in Streamlit app or Python script
from client.utils.supabase_client import get_supabase

try:
    supabase = get_supabase()
    print("✅ Supabase client initialized")
    
    # Test query
    response = supabase.table("persons").select("id").limit(1).execute()
    print(f"✅ Database connection successful: {len(response.data)} rows")
except Exception as e:
    print(f"❌ Error: {e}")
```

## Related Files

- [auth.py](auth.md) - Uses this for authentication
- [choir_attendance.py](choir_attendance.md) - Uses this for data queries
- [../README.md](../README.md) - Client directory overview
- [../../README.md](../../README.md) - Project root documentation
