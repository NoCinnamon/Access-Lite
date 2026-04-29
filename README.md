# Access-Lite

Face-recognition attendance system with:
- a Python recognition engine (`backend/vision/face-recognition-frame.py`)
- a Node/Express dashboard API (`backend/api/app.js`)
- MongoDB logging and member sync
- CSV attendance exports by date

## Features

- Detects known members from images in `known_faces/`
- Tracks red-list faces from `red_list/` with optional alert sound/email
- Writes attendance events to:
  - MongoDB collection: `Attendance-Logs`
  - daily CSV files: `CSVs/attendence_YYYY-MM-DD.csv`
- Syncs member metadata between `known_faces/`, `data/members.csv`, and MongoDB `members`
- Admin login/profile API (JWT-based)

## Tech Stack

- Python: `face_recognition`, `opencv-python`, `pymongo`, `python-dotenv`
- Node.js: `express`, `mongodb`, `jsonwebtoken`, `bcryptjs`, `nodemailer`
- Database: MongoDB Atlas/local MongoDB

## Project Structure

- `backend/vision/face-recognition-frame.py` - camera recognition, event logging, red-list logic
- `backend/api/app.js` - web server, admin auth, dashboard APIs, Python process toggle
- `frontend/index.html` - dashboard UI
- `frontend/login.html` - admin login UI
- `data/members.csv` - member registry (faceKey/name/memberID/contact/notes)
- `data/camera_alert_settings.json` - red-list sound toggle
- `known_faces/` - authorized member images (`DisplayName-MemberID.jpg`)
- `red_list/` - alert faces
- `CSVs/` - generated daily attendance exports

## Prerequisites

- Python 3.10+ recommended
- Node.js 18+ recommended
- MongoDB connection URI
- Webcam connected to your machine

## Setup

1) Install Python dependencies:

```bash
pip install -r requirements.txt
```

2) Install Node dependencies:

```bash
cd backend/api
npm install
```

3) Create a `.env` file in the project root:

```env
# Required (Node + Python)
MONGO_URI=mongodb+srv://<user>:<pass>@<cluster>/<dbname>?retryWrites=true&w=majority
# Optional alias used by Node
MONGO_URL=

# Required for admin JWT (use a strong value)
JWT_SECRET=replace_me

# Optional: allow first-time admin self-registration, then set back to false
ALLOW_ADMIN_REGISTER=false

# Optional: python executable override used by /api/toggle-camera
PYTHON_EXEC=python3

# Optional: red-list email alert protection and mail settings
RED_LIST_ALERT_SECRET=replace_with_shared_secret
SMTP_HOST=
SMTP_PORT=587
SMTP_SECURE=false
SMTP_USER=
SMTP_PASS=
SMTP_FROM=
```

## Running the App

1) Start the Node server:

```bash
cd backend/api
npm start
```

2) Open:
- `http://localhost:8001` (login page)

3) Start/stop camera recognition from the dashboard (calls `POST /api/toggle-camera`).

## Direct Python Run (optional)

You can also run recognition directly:

```bash
python3 backend/vision/face-recognition-frame.py
```

Press `q` in the OpenCV window to quit.

## Data Notes

- File naming convention for `known_faces/`:
  - `DisplayName-MemberID.jpg` (recommended)
  - legacy names without `-` are still supported
- `data/members.csv` is auto-synced from known-face files; contact/notes are preserved.
- `encoding_database.pkl` caches known face encodings for faster startup.

## Common Endpoints

- `GET /api/logs` - returns attendance logs
- `POST /api/toggle-camera` - starts/stops Python recognition process
- `POST /api/admin/register` - create admin (only when `ALLOW_ADMIN_REGISTER=true`)
- `POST /api/admin/login` - admin login
- `GET /api/admin/me` - current admin profile
- `PUT /api/admin/profile` - update admin contact info

## Troubleshooting

- **Mongo connection fails**: verify `.env` URI and network access.
- **No faces detected**: use clear, front-facing images with one person per file.
- **`face_recognition` install issues**: ensure system build tools are installed, then reinstall dependencies.
- **Camera does not open**: close other apps using webcam and retry.

## Security Notes

- Do not commit `.env` or private credentials.
- Keep `ALLOW_ADMIN_REGISTER=false` in normal operation.
- Rotate `JWT_SECRET` and `RED_LIST_ALERT_SECRET` for production use.
