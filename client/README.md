# Client Directory

This directory contains the **Streamlit-based web dashboard** for the EduQure school access control and attendance management system. The dashboard provides real-time monitoring, attendance tracking, and administrative controls.

## 📂 Directory Structure

```
client/
├── secured_dashboard.py       # Main Streamlit application entry point
├── requirements.txt           # Python package dependencies
├── .env                       # Environment variables (DO NOT COMMIT)
├── .env.example              # Template for environment variables
├── .streamlit/               # Streamlit configuration
│   └── config.toml           # UI theme and server settings
├── tabs/                     # Dashboard tab modules
│   ├── __init__.py           # Tab module initialization
│   ├── choir_attendance.py   # Choir practice attendance tracking
│   ├── live_monitor.py       # Real-time access monitoring
│   └── access_logs.py        # Historical access log viewing
└── utils/                    # Utility modules
    ├── __init__.py           # Utils initialization
    ├── supabase_client.py    # Supabase database client
    └── auth.py               # Authentication and session management
```

## 🎯 Purpose

The client dashboard provides:

1. **Authentication**: Secure login for administrators using Supabase Auth
2. **Live Monitoring**: Real-time view of who's entering/exiting the school
3. **Choir Attendance**: Specialized attendance tracking for choir practices with:
   - Automatic attendance from card scans
   - Manual attendance override (for forgotten cards)
   - Excuse tracking
   - Yearly attendance reports
4. **Access Logs**: Historical view of all access events
5. **Data Management**: CRUD operations for persons, practice dates, and attendance records

## 🚀 Getting Started

### 1. Prerequisites

- **Python 3.8+** installed
- **Supabase Account** with a configured project
- **Access to Supabase credentials** (URL and anon key)

### 2. Install Dependencies

Navigate to the client directory and install required packages:

```bash
cd client
pip install -r requirements.txt
```

**Packages installed:**
- `streamlit` - Web framework for the dashboard
- `supabase` - Python client for Supabase
- `python-dotenv` - Environment variable management
- `pandas` - Data manipulation and display

### 3. Configure Environment

1. Copy the example environment file:
   ```bash
   copy .env.example .env   # Windows
   # or
   cp .env.example .env     # Linux/Mac
   ```

2. Edit `.env` with your Supabase credentials:
   ```env
   SUPABASE_URL=https://yourproject.supabase.co
   SUPABASE_KEY=your.anon.key.here
   ```

### 4. Run the Dashboard

From the project root directory:

```bash
python -m streamlit run client/secured_dashboard.py
```

Or from the client directory:

```bash
streamlit run secured_dashboard.py
```

The dashboard will open in your browser at `http://localhost:8501`

## 🔐 Authentication

The dashboard uses **Supabase Authentication** for secure access:

1. **Login Screen**: First-time users see a login form
2. **Email/Password**: Enter credentials configured in Supabase Auth
3. **Session Management**: Sessions persist in Streamlit's session state
4. **Logout**: Available via sidebar button

### Setting Up Users in Supabase

1. Go to **Authentication → Users** in Supabase dashboard
2. Click **Add User** or **Invite User**
3. Set email and password (or send invite email)
4. Users can login with these credentials

## 📊 Dashboard Features

### 🎵 Choir Attendance Tab

The main feature for tracking choir practice attendance:

#### Today's Attendance Subtab
- **Practice Date Selection**: Choose from scheduled practice dates
- **Automatic Tracking**: Students who scan their cards are marked present
- **Manual Attendance**: Checkbox for students who forgot their cards
- **Excuse Tracking**: Checkbox for students who submitted excuses
- **Mutual Exclusivity**: Attendance and excuse checkboxes are mutually exclusive
- **Real-time Updates**: Changes save immediately to database

#### Yearly Report Subtab
- **Attendance Overview**: View all choir members and their attendance across the year
- **Practice Dates**: Columns for each practice date
- **Status Indicators**:
  - ✅ Present (via card scan)
  - 📝 Manual Attendance (no card scan)
  - ❌ Excuse
  - (blank) Absent
- **Add Practice Dates**: Create new scheduled practice dates
- **Statistics**: Attendance percentages and trends

### ⚠️ Live Monitor Tab

Real-time monitoring of access events:

- **Latest Entries**: Shows most recent card scans
- **Person Details**: Name, surname, card UID
- **Status**: Access granted/denied
- **Timestamp**: Exact time of access attempt
- **Auto-refresh**: Updates in real-time

### 🔒 Access Logs Tab

Historical access log viewing:

- **Date Range Filtering**: Select start and end dates
- **Full History**: View all access events
- **Export Capability**: Download data as CSV
- **Detailed Information**: All log fields including person info

## 🗄️ Database Schema

The dashboard interacts with these Supabase tables:

### Tables Used

1. **`persons`**
   - `id` (uuid, primary key)
   - `name` (text)
   - `surname` (text)
   - `card_uid` (text, unique)
   - `grade` (text)
   - `is_choir` (boolean)
   - `choir_year` (integer)

2. **`attendance_logs`**
   - `id` (uuid, primary key)
   - `card_uid` (text)
   - `status` (boolean) - access granted/denied
   - `timestamp` (timestamptz)
   - `person_id` (uuid, foreign key → persons)

3. **`choir_practice_dates`**
   - `id` (uuid, primary key)
   - `practice_date` (date, unique)
   - `year` (integer)

4. **`manual_choir_attendance`**
   - `id` (uuid, primary key)
   - `person_id` (uuid, foreign key → persons)
   - `practice_date_id` (uuid, foreign key → choir_practice_dates)
   - `present` (boolean) - manual attendance override
   - `excuse` (boolean) - excuse submitted
   - `created_at` (timestamptz)

## 🔧 File Descriptions

See individual file READMEs for detailed documentation:

- [secured_dashboard.py](secured_dashboard.md) - Main application entry point
- [requirements.txt](requirements.md) - Package dependencies
- [.streamlit/config.toml](.streamlit/config.md) - Streamlit configuration
- [tabs/choir_attendance.py](tabs/choir_attendance.md) - Choir attendance module
- [tabs/live_monitor.py](tabs/live_monitor.md) - Live monitoring module
- [tabs/access_logs.py](tabs/access_logs.md) - Access logs module
- [utils/supabase_client.py](utils/supabase_client.md) - Database client
- [utils/auth.py](utils/auth.md) - Authentication module

## 🐛 Troubleshooting

### "Supabase URL and Key not found"
- Verify `.env` file exists in the client directory
- Check that variable names match exactly: `SUPABASE_URL` and `SUPABASE_KEY`
- Ensure no extra spaces or quotes in the `.env` file

### Login Fails
- Verify user exists in Supabase Authentication dashboard
- Check email and password are correct
- Review Supabase logs for authentication errors

### Data Not Loading
- Check Supabase Row Level Security (RLS) policies
- Verify anon key has proper permissions
- Review browser console for JavaScript errors
- Check Streamlit terminal output for Python errors

### Checkboxes Not Saving
- Verify `manual_choir_attendance` table exists
- Check foreign key constraints (person_id, practice_date_id must be valid)
- Review RLS policies on the table

### Page Keeps Reloading
- This is expected when checkboxes change (Streamlit behavior)
- The UI uses fragments to minimize reloads
- Data is saved before reload occurs

## 🎨 Customization

### Changing Theme

Edit `.streamlit/config.toml` to customize colors and appearance:

```toml
[theme]
primaryColor = "#1E88E5"        # Accent color
backgroundColor = "#FFFFFF"      # Main background
secondaryBackgroundColor = "#F0F2F6"  # Sidebar/widgets
textColor = "#262730"           # Text color
font = "sans serif"             # Font family
```

### Adding New Tabs

1. Create a new file in `tabs/` (e.g., `tabs/new_feature.py`)
2. Create a `render()` function in the new file
3. Import and call it in `secured_dashboard.py`:

```python
from client.tabs import new_feature

# In the main section:
tab4 = st.tabs(["🎵 Choir Attendance", "⚠️ Live Monitor", "🔒 Access Logs", "🆕 New Feature"])
with tab4:
    new_feature.render()
```

## 📖 Usage Examples

### Viewing Today's Choir Attendance

1. Login to the dashboard
2. Navigate to **🎵 Choir Attendance** tab
3. Select **Today's Attendance** subtab
4. Choose today's date from the dropdown
5. View attendance list with automatic detections
6. Manually mark students who forgot cards
7. Mark excuses as needed

### Generating Yearly Report

1. Go to **🎵 Choir Attendance** → **Yearly Report**
2. Select the year from dropdown
3. View attendance matrix
4. Use horizontal scroll for many practice dates
5. Export to Excel/CSV if needed (use browser's copy function)

### Monitoring Live Access

1. Go to **⚠️ Live Monitor** tab
2. View real-time access events
3. Click **Refresh Data** to manually update
4. Check who's entering/exiting the school

## 🔐 Security Considerations

- **Never commit `.env`**: Always add to `.gitignore`
- **Use Anon Key**: Don't use service_role key in client code
- **RLS Policies**: Implement proper Row Level Security in Supabase
- **HTTPS Only**: Deploy on HTTPS in production (Streamlit Cloud, AWS, etc.)
- **Session Timeout**: Implement session expiry for added security
- **Input Validation**: All user inputs are validated before database operations

## 🚀 Deployment

### Streamlit Cloud (Free)

1. Push code to GitHub (without `.env`)
2. Go to [share.streamlit.io](https://share.streamlit.io)
3. Connect your repository
4. Set secrets in app settings (equivalent to `.env`)
5. Deploy!

### Docker (Self-Hosted)

```dockerfile
FROM python:3.10-slim
WORKDIR /app
COPY client/requirements.txt .
RUN pip install -r requirements.txt
COPY client/ ./client/
ENV SUPABASE_URL=your_url
ENV SUPABASE_KEY=your_key
CMD ["streamlit", "run", "client/secured_dashboard.py", "--server.port=8501"]
```

Build and run:
```bash
docker build -t eduqure-dashboard .
docker run -p 8501:8501 eduqure-dashboard
```

## 🛠️ Future Enhancements

- [ ] Add parent/student view (read-only dashboard)
- [ ] SMS notifications for attendance alerts
- [ ] Export reports to PDF
- [ ] Multi-language support
- [ ] Dark mode toggle
- [ ] Advanced analytics and charts
- [ ] Bulk import of students from CSV
- [ ] Attendance QR code generation for parents
