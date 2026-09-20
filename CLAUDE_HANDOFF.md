# 🎓 Google Classroom Scraper — Complete Project Handoff

> **วัตถุประสงค์ของเอกสาร**: ไฟล์นี้สรุปทุกอย่างเกี่ยวกับโปรเจกต์ "Google Classroom Scraper" เพื่อให้ AI ตัวถัดไป (Claude Code) สามารถเข้าใจและทำงานต่อได้ทันที โดยไม่ต้องถามอะไรเพิ่มเติม

---

## 📋 สารบัญ

1. [ภาพรวมโปรเจกต์](#1-ภาพรวมโปรเจกต์)
2. [Tech Stack & Dependencies](#2-tech-stack--dependencies)
3. [โครงสร้างไฟล์ทั้งหมด](#3-โครงสร้างไฟล์ทั้งหมด)
4. [สถาปัตยกรรมระบบ](#4-สถาปัตยกรรมระบบ)
5. [รายละเอียดแต่ละ Module](#5-รายละเอียดแต่ละ-module)
6. [Database Schema](#6-database-schema)
7. [API Endpoints ทั้งหมด](#7-api-endpoints-ทั้งหมด)
8. [Frontend (Static Web UI)](#8-frontend-static-web-ui)
9. [ระบบ Authentication (OAuth 2.0)](#9-ระบบ-authentication-oauth-20)
10. [Known Issues & Bugs ที่ยังไม่ได้แก้](#10-known-issues--bugs-ที่ยังไม่ได้แก้)
11. [แผนอัปสเกลในอนาคต](#11-แผนอัปสเกลในอนาคต)
12. [วิธีรันโปรเจกต์](#12-วิธีรันโปรเจกต์)
13. [ข้อมูลเจ้าของโปรเจกต์](#13-ข้อมูลเจ้าของโปรเจกต์)

---

## 1. ภาพรวมโปรเจกต์

### แอปนี้คืออะไร?
เว็บแอปพลิเคชัน **ดูดไฟล์จาก Google Classroom อัตโนมัติ** พร้อมระบบ AI สรุปเนื้อหาเอกสาร
ออกแบบมาให้นักศึกษามหาวิทยาลัยสามารถ:
- ดึงไฟล์จากรายวิชาใน Google Classroom ทั้งหมดลงเครื่องตัวเองอัตโนมัติ
- ตั้งเวลาซิงค์ไฟล์ใหม่แบบ Cron Schedule
- ใช้ AI (Gemini / OpenAI / Ollama) สรุปเนื้อหาเอกสารเตรียมสอบ
- Export ไฟล์ทั้งวิชาเป็น ZIP หรือ Markdown รวมเพื่อโยนเข้า NotebookLM / ChatGPT

### สถานะปัจจุบัน
- **โค้ดเสร็จสมบูรณ์ 100%** ทั้ง Backend (Python FastAPI) และ Frontend (Vanilla HTML/CSS/JS)
- **ยังมี Bug ที่ต้องแก้** ในส่วน OAuth login flow (ดูหัวข้อ Known Issues)
- ยังไม่เคยซิงค์ไฟล์สำเร็จจริงเพราะ Auth ยังไม่ผ่านบนเบราว์เซอร์แบบปกติ (ต้อง workaround ด้วยการก๊อปลิงก์จาก server log)

---

## 2. Tech Stack & Dependencies

### Backend
| เทคโนโลยี | เวอร์ชัน | ใช้ทำอะไร |
|---|---|---|
| Python | 3.x | ภาษาหลัก |
| FastAPI | 0.111.0 | Web Framework (REST API) |
| Uvicorn | 0.30.1 | ASGI Server |
| SQLAlchemy | 2.0.30 | ORM สำหรับ SQLite |
| APScheduler | 3.10.4 | Background Job Scheduler (Cron) |
| google-api-python-client | 2.131.0 | Google Classroom API & Drive API |
| google-auth-oauthlib | 1.2.0 | OAuth 2.0 Authentication |
| Pydantic | 2.7.2 | Data Validation |
| pydantic-settings | 2.2.1 | .env Config Loader |
| PyPDF2 | (ใน code แต่ขาดใน requirements.txt) | PDF Text Extraction |
| google-generativeai | (ใน code แต่ขาดใน requirements.txt) | Gemini AI Summarization |
| openai | (ใน code แต่ขาดใน requirements.txt) | OpenAI API Summarization |
| requests | (built-in) | HTTP Client (Ollama) |

### Frontend
- **Vanilla HTML + CSS + JavaScript** (ไม่มี framework)
- **Font Awesome** (CDN) สำหรับไอคอน
- Dark Theme UI ออกแบบด้วย CSS Variables

### Database
- **SQLite** (ไฟล์ `data/classroom.db`) — ใช้ผ่าน SQLAlchemy ORM

### requirements.txt (ปัจจุบัน)
```
fastapi==0.111.0
uvicorn==0.30.1
sqlalchemy==2.0.30
google-api-python-client==2.131.0
google-auth-httplib2==0.2.0
google-auth-oauthlib==1.2.0
apscheduler==3.10.4
python-dotenv==1.0.1
pydantic==2.7.2
pydantic-settings==2.2.1
jinja2==3.1.4
aiofiles==23.2.1
```

> **หมายเหตุ**: ยังขาด `PyPDF2`, `google-generativeai`, `openai` ใน requirements.txt (ใช้งานจริงต้องเพิ่ม)

---

## 3. โครงสร้างไฟล์ทั้งหมด

```
webscraping classroom/
├── .env.example                    # ตัวอย่างไฟล์ config
├── .gitignore
├── requirements.txt                # Python dependencies
├── migrate_db.py                   # Database migration script
│
├── credentials/                    # (gitignored) OAuth credentials
│   ├── client_secret.json          # Google OAuth Client Secret
│   └── token.json                  # User's OAuth token (auto-generated)
│
├── data/                           # SQLite database directory
│   └── classroom.db                # Main database file
│
├── downloads/                      # Downloaded files organized by course
│   ├── {course_name}/
│   │   └── {YYYY-MM-DD}/
│   │       └── filename.pdf
│   └── exports/                    # ZIP/MD export files
│
└── app/                            # Main application package
    ├── __init__.py
    ├── main.py                     # FastAPI app entry point + lifespan
    ├── config.py                   # Pydantic Settings (.env loader)
    ├── database.py                 # SQLAlchemy models + engine setup
    │
    ├── auth/                       # Google OAuth 2.0
    │   ├── __init__.py
    │   └── google_oauth.py         # OAuth flow (InstalledAppFlow)
    │
    ├── scraper/                    # Google API integration
    │   ├── __init__.py
    │   ├── classroom_api.py        # Classroom API client (courses, coursework, announcements)
    │   ├── drive_downloader.py     # Drive API file downloader
    │   └── dedup.py                # File deduplication (SHA-256 + Drive modified time)
    │
    ├── scheduler/                  # Background job scheduling
    │   ├── __init__.py
    │   └── job_manager.py          # APScheduler + sync logic
    │
    ├── summarizer/                 # AI document summarization
    │   ├── __init__.py
    │   ├── ai_client.py            # Multi-provider AI (Gemini/OpenAI/Ollama)
    │   └── text_extractor.py       # PDF & text file extraction
    │
    ├── api/                        # FastAPI route modules
    │   ├── __init__.py
    │   ├── routes_auth.py          # GET /api/auth/status, GET /api/auth/login
    │   ├── routes_courses.py       # CRUD courses + sync triggers
    │   ├── routes_files.py         # List/download files
    │   ├── routes_schedule.py      # CRUD schedules
    │   ├── routes_ai.py            # AI settings + summarization
    │   └── routes_export.py        # Export ZIP/Markdown
    │
    └── static/                     # Frontend web UI
        ├── index.html              # Main SPA page
        ├── style.css               # Dark theme CSS
        └── app.js                  # Frontend logic (vanilla JS)
```

---

## 4. สถาปัตยกรรมระบบ

```
┌─────────────────────────────────────────────────────┐
│                  Chrome Browser                      │
│  ┌───────────────────────────────────────────────┐   │
│  │  Frontend (index.html + app.js + style.css)   │   │
│  │  - Tab: Courses (list + track + sync)         │   │
│  │  - Tab: Files (download + AI summarize)       │   │
│  │  - Tab: Schedule (cron setup)                 │   │
│  │  - Tab: AI Settings (provider config)         │   │
│  └────────────────┬──────────────────────────────┘   │
│                   │ fetch() API calls                │
└───────────────────┼──────────────────────────────────┘
                    │
                    ▼
┌─────────────────────────────────────────────────────┐
│            FastAPI Backend (port 8000)                │
│  ┌─────────────┐  ┌──────────────┐  ┌────────────┐  │
│  │ routes_auth │  │routes_courses│  │routes_files │  │
│  │ routes_ai   │  │routes_sched  │  │routes_export│  │
│  └──────┬──────┘  └──────┬───────┘  └─────┬──────┘  │
│         │                │                │          │
│  ┌──────▼──────┐  ┌──────▼───────┐  ┌─────▼──────┐  │
│  │google_oauth │  │classroom_api │  │drive_downl  │  │
│  │(OAuth flow) │  │(Classroom v1)│  │(Drive v3)   │  │
│  └─────────────┘  └──────────────┘  └────────────┘  │
│         │                                            │
│  ┌──────▼──────────────────────────────────────────┐ │
│  │  SQLite (data/classroom.db) via SQLAlchemy      │ │
│  │  Tables: courses, downloaded_files, schedules,  │ │
│  │          sync_logs, user_settings               │ │
│  └─────────────────────────────────────────────────┘ │
│         │                                            │
│  ┌──────▼──────┐  ┌──────────────┐                   │
│  │ APScheduler │  │ AISummarizer │                   │
│  │ (cron jobs) │  │ (Gemini/GPT) │                   │
│  └─────────────┘  └──────────────┘                   │
└─────────────────────────────────────────────────────┘
                    │
                    ▼
        ┌──────────────────────┐
        │  Google APIs         │
        │  - Classroom API v1  │
        │  - Drive API v3      │
        └──────────────────────┘
```

---

## 5. รายละเอียดแต่ละ Module

### 5.1 `app/main.py` — Entry Point
- สร้าง FastAPI app พร้อม lifespan handler
- เรียก `init_db()` เมื่อเริ่มต้น (สร้างตารางอัตโนมัติ)
- เรียก `start_scheduler()` เพื่อเริ่ม APScheduler
- Mount static files จาก `app/static/`
- Redirect `/` → `/static/index.html`
- รันด้วย: `python -m app.main`

### 5.2 `app/config.py` — Configuration
- ใช้ `pydantic-settings` โหลดค่าจาก `.env`
- ตัวแปร: `GOOGLE_CLIENT_ID`, `GOOGLE_CLIENT_SECRET`, `GOOGLE_PROJECT_ID`, `DATABASE_URL`, `HOST`, `PORT`

### 5.3 `app/database.py` — Database Models (SQLAlchemy ORM)
- **5 ตาราง**: `Course`, `DownloadedFile`, `Schedule`, `SyncLog`, `UserSettings`
- สร้าง engine จาก `DATABASE_URL` (default: SQLite)
- `get_db()` เป็น dependency injection สำหรับ FastAPI routes

### 5.4 `app/auth/google_oauth.py` — Google OAuth 2.0
- ใช้ `InstalledAppFlow.from_client_secrets_file()` + `run_local_server(port=0)`
- เก็บ token ที่ `credentials/token.json`
- ต้องมี `credentials/client_secret.json` (ดาวน์โหลดจาก Google Cloud Console)
- **สำคัญ**: ตั้ง `OAUTHLIB_RELAX_TOKEN_SCOPE=1` เพื่อแก้ปัญหา "Scope has changed" error
- Google OAuth Scopes ที่ใช้:
  - `classroom.courses.readonly`
  - `classroom.coursework.me.readonly`
  - `classroom.announcements.readonly`
  - `drive.readonly`

### 5.5 `app/scraper/classroom_api.py` — Google Classroom API Client
- Class `ClassroomClient` ใช้ Classroom API v1
- Methods:
  - `list_courses()` — ดึงรายวิชาทั้งหมด (pagination)
  - `get_coursework(course_id)` — ดึง assignments ทั้งหมด
  - `get_announcements(course_id)` — ดึงประกาศทั้งหมด
  - `extract_materials_from_item(item)` — แกะ Drive file links จาก coursework/announcements
  - `get_all_materials(course_id)` — รวม materials จากทุก source

### 5.6 `app/scraper/drive_downloader.py` — Google Drive Downloader
- Class `DriveDownloader` ใช้ Drive API v3
- รองรับ:
  - ไฟล์ทั่วไป (PDF, DOCX, PPTX) → download ตรง
  - Google Workspace files → export (Docs→PDF, Sheets→XLSX, Slides→PDF)
- จัดเก็บไฟล์ตาม: `downloads/{course_name}/{YYYY-MM-DD}/{filename}`
- มีระบบ `_get_unique_path()` ป้องกันไฟล์ชื่อซ้ำ (ต่อ `_1`, `_2`)

### 5.7 `app/scraper/dedup.py` — File Deduplication
- Class `FileDeduplicator`
- ตรวจซ้ำ 2 ชั้น:
  1. เช็ค `drive_file_id` ในฐานข้อมูล
  2. เปรียบเทียบ `drive_modified_at` — ถ้าไฟล์บน Drive ใหม่กว่า → โหลดใหม่
- คำนวณ SHA-256 hash ของไฟล์ที่โหลดมาเก็บไว้

### 5.8 `app/scheduler/job_manager.py` — Background Job Scheduler
- ใช้ APScheduler `AsyncIOScheduler` + `SQLAlchemyJobStore`
- `sync_course(course_id)` — ฟังก์ชันหลักที่ทำงานเมื่อถึงเวลา
  - ดึง materials → เช็คซ้ำ → โหลดไฟล์ใหม่ → บันทึก DB
  - สร้าง SyncLog ทุกครั้งที่รัน
- `schedule_course_sync(course_id, cron_expr)` — ตั้ง cron job
- `load_schedules_from_db()` — โหลด schedules จาก DB เมื่อเริ่มต้น

### 5.9 `app/summarizer/` — AI Document Summarization
- **`text_extractor.py`**: แกะข้อความจาก PDF (PyPDF2), TXT, MD, CSV
- **`ai_client.py`**: Class `AISummarizer` รองรับ 3 providers:
  - `gemini` — Google Gemini 1.5 Flash
  - `openai` — GPT-4o Mini
  - `ollama` — Local LLM (llama3)
- Prompt: สรุปเนื้อหาเป็น Markdown พร้อม key concepts, formulas, definitions

---

## 6. Database Schema

```sql
-- ตารางรายวิชา
CREATE TABLE courses (
    id TEXT PRIMARY KEY,              -- Google Classroom course ID
    name TEXT,
    section TEXT,
    is_tracked BOOLEAN DEFAULT FALSE, -- ผู้ใช้เลือกติดตามหรือไม่
    last_synced DATETIME
);

-- ตารางไฟล์ที่โหลดแล้ว
CREATE TABLE downloaded_files (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    course_id TEXT REFERENCES courses(id),
    drive_file_id TEXT UNIQUE,        -- Google Drive file ID (ป้องกันซ้ำ)
    filename TEXT,
    file_path TEXT,                   -- path บนเครื่อง
    sha256_hash TEXT,                 -- hash สำหรับเช็คซ้ำ
    mime_type TEXT,
    file_size INTEGER,
    drive_modified_at DATETIME,       -- เวลาแก้ไขล่าสุดบน Drive
    downloaded_at DATETIME,
    summary_text TEXT                 -- AI summary (nullable)
);

-- ตาราง Cron Schedules
CREATE TABLE schedules (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    course_id TEXT REFERENCES courses(id),
    cron_expression TEXT,             -- เช่น "0 9 * * 1" = ทุกจันทร์ 9 โมง
    is_auto_detected BOOLEAN DEFAULT FALSE,
    is_active BOOLEAN DEFAULT TRUE,
    next_run DATETIME
);

-- ตาราง Sync Logs
CREATE TABLE sync_logs (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    course_id TEXT REFERENCES courses(id),
    started_at DATETIME,
    finished_at DATETIME,
    files_found INTEGER DEFAULT 0,
    files_downloaded INTEGER DEFAULT 0,
    files_skipped INTEGER DEFAULT 0,
    status TEXT,                      -- "success" / "error" / "running"
    error_message TEXT
);

-- ตารางเก็บ Settings (Key-Value)
CREATE TABLE user_settings (
    key TEXT PRIMARY KEY,             -- เช่น "ai_provider", "ai_gemini_key"
    value TEXT
);
```

**Relationships:**
- `Course` 1→N `DownloadedFile`
- `Course` 1→N `Schedule`
- `Course` 1→N `SyncLog`

---

## 7. API Endpoints ทั้งหมด

### Auth
| Method | Path | Description |
|---|---|---|
| `GET` | `/api/auth/status` | เช็คว่าล็อกอิน Google แล้วหรือยัง |
| `GET` | `/api/auth/login` | เริ่ม OAuth flow (blocking call - ปัญหาหลัก!) |

### Courses
| Method | Path | Description |
|---|---|---|
| `GET` | `/api/courses/` | ดึงรายวิชาทั้งหมด (merge Classroom API + DB) |
| `POST` | `/api/courses/{id}/track?name=...` | Toggle tracking on/off |
| `POST` | `/api/courses/{id}/sync` | สั่ง sync ไฟล์วิชานั้น (background) |
| `POST` | `/api/courses/sync/all` | สั่ง sync ทุกวิชาที่ track อยู่ |

### Files
| Method | Path | Description |
|---|---|---|
| `GET` | `/api/files/?course_id=...&limit=50&offset=0` | ดึงรายการไฟล์ที่โหลดแล้ว |
| `GET` | `/api/files/{id}/download` | ดาวน์โหลดไฟล์จากเครื่อง |

### Schedule
| Method | Path | Description |
|---|---|---|
| `GET` | `/api/schedule/` | ดึง schedules ทั้งหมด |
| `POST` | `/api/schedule/` | สร้าง/อัปเดต schedule (body: `{course_id, cron_expression}`) |
| `DELETE` | `/api/schedule/{course_id}` | ลบ schedule |

### AI
| Method | Path | Description |
|---|---|---|
| `GET` | `/api/ai/settings` | ดึง AI settings ปัจจุบัน |
| `POST` | `/api/ai/settings` | บันทึก AI settings (body: `{provider, api_key, endpoint}`) |
| `POST` | `/api/ai/summarize/{file_id}` | สั่งสรุปไฟล์ (background) |
| `GET` | `/api/ai/summary/{file_id}` | ดึงผลสรุป AI |

### Export
| Method | Path | Description |
|---|---|---|
| `GET` | `/api/export/{course_id}/zip` | Export ไฟล์ทั้งวิชาเป็น ZIP |
| `GET` | `/api/export/{course_id}/text` | Export ข้อความทั้งวิชาเป็น Markdown |

### Other
| Method | Path | Description |
|---|---|---|
| `GET` | `/` | Redirect → `/static/index.html` |
| `GET` | `/api/health` | Health check |

---

## 8. Frontend (Static Web UI)

### โครงสร้าง UI
- **Sidebar**: Navigation แบบแถบด้านซ้าย (Courses, Files, Schedule, AI Settings)
- **Main Area**: Tab-based SPA (Single Page Application) ไม่ใช้ Router
- **Login Modal**: ปรากฏเมื่อยังไม่ได้ล็อกอิน Google
- **Theme**: Dark mode พื้นหลังสีเข้ม (#0f1419)

### Tab ทั้งหมด
1. **Courses** — แสดงรายวิชาเป็น Card Grid, ปุ่ม Track/Sync/Export (ZIP + Text)
2. **Files** — ตาราง (Table) ของไฟล์ที่โหลดแล้ว, ปุ่ม Download + AI Summarize
3. **Schedule** — แสดง Active Schedules + Form สร้าง Cron Schedule ใหม่
4. **AI Settings** — เลือก Provider (Gemini/OpenAI/Ollama), ใส่ API Key

### การทำงานของ Login Flow (app.js) — แก้แล้ว (redirect flow)
```
1. Page Load → showLoginOutcome() อ่าน ?auth / ?auth_error จาก URL แล้วล้าง query ทิ้ง
2. fetch('/api/auth/status')
3. ถ้า authenticated=false → แสดง Login Modal
4. User กด "Authorize Access" → window.location.href = '/api/auth/login' (redirect ทั้งหน้า)
5. Google → /api/auth/callback → redirect กลับมา /static/index.html?auth=success
6. Page Load รอบใหม่ → authenticated=true → ซ่อน Modal + โหลด Courses
```

### หมายเหตุ
- ไม่ใช้ `window.open()` แล้ว จึงไม่โดน Pop-up blocker
- ไม่มี polling `/api/auth/status` แบบวนไม่รู้จบอีกต่อไป (เช็คครั้งเดียวตอนโหลดหน้า)
- Error จาก login จะแสดงในกล่อง `#login-error` ในโมดัล (ใส่ด้วย `textContent` กัน XSS)

---

## 9. ระบบ Authentication (OAuth 2.0)

### การทำงานปัจจุบัน (Web Application redirect flow)
1. ผู้ใช้ดาวน์โหลด `client_secret.json` จาก Google Cloud Console มาใส่ใน `credentials/`
   (รองรับทั้ง client แบบ `web` และ `installed` — โค้ดอ่านได้ทั้งสองแบบ)
2. กดปุ่ม Login → เบราว์เซอร์ redirect ไป `GET /api/auth/login`
   - สร้าง authorization URL ด้วย `google_auth_oauthlib.flow.Flow` (ไม่ block)
   - เก็บ `state` + PKCE `code_verifier` ไว้ใน memory (อายุ 10 นาที, ใช้ได้ครั้งเดียว)
   - ตอบกลับเป็น HTTP 302 ไป Google consent screen ทันที (~8ms)
3. ผู้ใช้ล็อกอิน/ให้สิทธิ์ที่ Google
4. Google redirect กลับมา `GET /api/auth/callback?code=...&state=...`
   - ตรวจ `state` ว่าเป็นตัวที่แอปออกให้จริง (กัน CSRF)
   - แลก code เป็น token ด้วย `code_verifier` เดิม แล้วเซฟ `credentials/token.json`
   - redirect กลับ `/static/index.html?auth=success`
5. `get_credentials()` ไม่เปิดเบราว์เซอร์และไม่ block อีกต่อไป — ถ้ายังไม่ล็อกอิน
   จะ raise `NotAuthenticatedError` (API ตอบ 401 ให้ frontend แสดงโมดัลล็อกอิน)

### Redirect URI
- ค่า default มาจาก `HOST`/`PORT` → `http://127.0.0.1:8000/api/auth/callback`
- override ได้ด้วย `OAUTH_REDIRECT_URI` ใน `.env`
- Server จะ log ค่านี้ตอน startup
- ถ้าเปลี่ยน OAuth client เป็น type **Web application** ต้องเอาค่านี้ไปใส่ใน
  "Authorized redirect URIs" ให้ตรงเป๊ะ (client แบบ Desktop ใช้ loopback ได้เลยไม่ต้องลงทะเบียน)

### Endpoints
| Method | Path | ทำอะไร |
|---|---|---|
| `GET` | `/api/auth/login` | 302 ไป Google consent screen |
| `GET` | `/api/auth/callback` | รับ code → แลก token → 302 กลับหน้าแอป |
| `GET` | `/api/auth/status` | เช็คสถานะ (คืน `redirect_uri`, `client_type` ด้วย) |
| `POST` | `/api/auth/logout` | ลบ `token.json` เพื่อเริ่มล็อกอินใหม่ |

### Google Cloud Console Setup
- **Project**: dash-496611
- **OAuth Client ID**: Desktop App type
- **Consent Screen**: External, Testing mode
- **Test Users** ที่เพิ่มแล้ว:
  - `bossboss27.b3@gmail.com` (อีเมลส่วนตัว)
  - `phakin.m@kkumail.com` (อีเมลมหาวิทยาลัย KKU)

### ปัญหา Critical: OAuth Login Flow
**Error: "Scope has changed"** — เกิดขึ้นเมื่อ Google return scopes ที่ต่างจากที่ request (Google ชอบเพิ่ม scope เอง)
- แก้ชั่วคราวด้วย `os.environ["OAUTHLIB_RELAX_TOKEN_SCOPE"] = "1"` (เพิ่มแล้วใน google_oauth.py)
- ถ้ายัง error ให้ลบ `credentials/token.json` แล้วล็อกอินใหม่

**~~ปัญหาหลัก — Login Flow ทำงานไม่ถูกต้องบน Web App~~ (แก้แล้ว)**
เดิมใช้ `InstalledAppFlow.run_local_server(port=0)` ซึ่งเป็น blocking call ทำให้ FastAPI
worker ค้างและต้อง workaround ด้วยการก๊อป URL จาก server log
ตอนนี้เปลี่ยนเป็น redirect flow เรียบร้อยแล้ว — ไม่ต้อง workaround อีกต่อไป

---

## 10. Known Issues & Bugs ที่ยังไม่ได้แก้

### 🔴 Critical (ต้องแก้ก่อนใช้งานได้)

1. ~~**OAuth Login Flow ใช้งานจริงไม่ได้**~~ — ✅ แก้แล้ว
   - เปลี่ยนเป็น redirect-based Web OAuth flow (`Flow` + `/api/auth/callback`)
   - `/api/auth/login` ตอบ 302 ภายใน ~8ms ไม่ block worker แล้ว
   - ดูรายละเอียดที่หัวข้อ 9

2. **requirements.txt ไม่ครบ**
   - ขาด: `PyPDF2`, `google-generativeai`, `openai`
   - แก้: เพิ่ม dependencies ที่ขาด

### 🟡 Warning (ควรแก้)

3. ~~**Frontend poll `/api/auth/status` ทุก 3 วินาทีไม่มี limit**~~ — ✅ แก้แล้ว
   - redirect flow ไม่ต้อง poll อีกต่อไป เอา `setInterval` ออกหมดแล้ว
   - เช็คสถานะครั้งเดียวตอนโหลดหน้า

4. **`google.generativeai` package deprecated**
   - Library เตือนว่าต้องเปลี่ยนไปใช้ `google.genai`
   - แก้: migrate ไปใช้ package ใหม่

5. **ไม่มี Rate Limiting**
   - ถ้าหลายคนใช้พร้อมกัน อาจโดน Google API quota limit

### 🟢 Minor / Nice-to-have

6. ยังไม่มี favicon — Browser แสดง 404 error สำหรับ `/favicon.ico`
7. File download path ใช้ relative path — อาจมีปัญหาถ้ารันจากตำแหน่งอื่น
8. ไม่มี Unit Tests
9. ไม่มี Error handling UI — Frontend ไม่แสดง error message ให้ user เห็นชัดเจน

---

## 11. แผนอัปสเกลในอนาคต

### Phase 1: แก้ Auth Flow (จำเป็นเร่งด่วน)
- เปลี่ยนเป็น Web Application OAuth → redirect-based login
- ทำให้ใช้งานบนเบราว์เซอร์ได้จริงโดยไม่ต้องก๊อปลิงก์จาก server log

### Phase 2: Multi-user Support (เป้าหมายเจ้าของ)
- เพิ่มระบบ Login / Register (ใช้ Google Account ตรง)
- แต่ละ user มี token แยก (ตอนนี้ share token เดียว)
- เก็บ token ใน DB แทน file system
- จำกัดโควต้าการโหลดต่อ user

### Phase 3: Deploy เป็น SaaS
- เปลี่ยน SQLite → PostgreSQL
- Deploy บน Railway / Render / Google Cloud Run
- ใช้ Cloud Storage แทน local filesystem สำหรับเก็บไฟล์
- เพิ่ม Celery/Redis สำหรับ background job

### Phase 4: แผนสำรอง (Web Scraping ด้วย Playwright)
- ถ้าไม่อยากผ่าน Google API verification process
- ใช้ Playwright/Selenium จำลองเบราว์เซอร์ล็อกอินเข้า Classroom โดยตรง
- ข้อดี: ไม่ต้องง้อ Google API key, ใครมีรหัสนักศึกษาก็ใช้ได้
- ข้อเสีย: ช้ากว่า, ต้อง maintain เมื่อ Google เปลี่ยน UI, อาจโดน CAPTCHA

---

## 12. วิธีรันโปรเจกต์

### Prerequisites
1. Python 3.9+
2. `client_secret.json` จาก Google Cloud Console ใส่ใน `credentials/`

### Steps
```bash
# 1. ติดตั้ง dependencies
cd "webscraping classroom"
pip install -r requirements.txt
pip install PyPDF2 google-generativeai openai  # dependencies ที่ขาด

# 2. (Optional) ตั้ง .env
cp .env.example .env
# แก้ค่าตามต้องการ

# 3. รัน server
python -m app.main
# Server จะรันที่ http://127.0.0.1:8000

# 4. เปิดเบราว์เซอร์ไปที่ http://127.0.0.1:8000
```

### วิธี Login
1. รัน server ด้วย `python -m app.main`
2. เปิด `http://127.0.0.1:8000` ในเบราว์เซอร์
3. กดปุ่ม "Authorize Access" → หน้าจะ redirect ไป Google เอง
4. ล็อกอินด้วยอีเมลที่เพิ่มเป็น Test User
5. กด Advanced → Go to Classroom Scraper → ให้สิทธิ์ทั้งหมด → Continue
6. Google จะ redirect กลับมาที่แอปเอง แล้วโหลดรายวิชาให้ทันที

> ไม่ต้องก๊อป URL จาก server log อีกต่อไป
> ถ้าเจอ error `redirect_uri_mismatch` ให้ดูค่า redirect URI ที่ server log ตอน startup
> แล้วเอาไปใส่ใน Google Cloud Console (เฉพาะกรณีที่ OAuth client เป็น type Web application)
> ถ้าอยากล็อกอินใหม่ด้วยบัญชีอื่น: `curl -X POST http://127.0.0.1:8000/api/auth/logout`

---

## 13. ข้อมูลเจ้าของโปรเจกต์

- **ชื่อ**: Phakin (Boss)
- **มหาวิทยาลัย**: มหาวิทยาลัยขอนแก่น (KKU)
- **อีเมลมหาลัย**: `phakin.m@kkumail.com`
- **อีเมลส่วนตัว**: `bossboss27.b3@gmail.com`
- **Google Cloud Project**: `dash-496611`
- **OAuth Client ID**: `1072641264455-3ra653rs5ggf8hn9v6814dl1ff82lf11.apps.googleusercontent.com`
- **ตำแหน่งโปรเจกต์บนเครื่อง**: `C:\Users\Lenovo\webscraping classroom`
- **OS**: Windows 11

---

## 📝 สรุปสิ่งที่ต้องทำต่อ (Priority Order)

| # | Priority | Task | รายละเอียด |
|---|---|---|---|
| 1 | ✅ | ~~แก้ OAuth Login Flow~~ | **เสร็จแล้ว** — redirect flow + `/api/auth/callback` |
| 2 | 🔴 | เพิ่ม missing dependencies | เพิ่ม PyPDF2, google-generativeai, openai ใน requirements.txt |
| 3 | 🟡 | ทดสอบ Sync ไฟล์จริง | ยังไม่เคย sync สำเร็จเพราะ auth ยังไม่ผ่านบน UI ปกติ |
| 4 | 🟡 | แก้ deprecated google.generativeai | ย้ายไปใช้ google.genai package |
| 5 | ✅ | ~~จำกัด auth polling~~ | **เสร็จแล้ว** — เอา polling ออก ไม่ต้องใช้กับ redirect flow |
| 6 | 🟢 | เพิ่ม Error handling UI | แสดง error message ชัดเจนใน Frontend |
| 7 | 🟢 | เพิ่ม favicon | แก้ 404 error |
| 8 | 🟢 | เขียน Unit Tests | ยังไม่มี test เลย |

---

> **สถานะล่าสุด (2026-09-02)**: OAuth Login Flow แก้เสร็จแล้ว — เปลี่ยนจาก
> `InstalledAppFlow.run_local_server()` (blocking) เป็น redirect-based Web OAuth flow
> ผู้ใช้กดปุ่มเดียวแล้ว redirect ไป Google และกลับมาที่แอปเอง ไม่ต้องก๊อปลิงก์จาก server log
>
> ไฟล์ที่แก้:
> - `app/auth/google_oauth.py` — เขียนใหม่ด้วย `Flow` + state/PKCE store, `get_credentials()` ไม่ block แล้ว
> - `app/api/routes_auth.py` — `/login` (302), `/callback` (แลก token), `/logout`
> - `app/api/routes_courses.py` — ตอบ 401 เมื่อยังไม่ล็อกอิน + rebuild API client หลังล็อกอินใหม่
> - `app/static/app.js` — ปุ่ม login เป็น full redirect, เอา polling ออก, แสดง error
> - `app/static/index.html` + `style.css` — กล่องข้อความ error ในโมดัล
> - `app/config.py` + `.env.example` — เพิ่ม `OAUTH_REDIRECT_URI`
> - `app/main.py` — log redirect URI ตอน startup
>
> **สิ่งที่ยังต้องทำต่อ**: ทดสอบ sync ไฟล์จริงหลังล็อกอิน, เพิ่ม `PyPDF2` /
> `google-generativeai` / `openai` ใน requirements.txt, migrate ไป `google.genai`
