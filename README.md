# 🎓 Google Classroom Scraper & AI Assistant

เว็บแอปพลิเคชันดูดไฟล์เอกสาร สไลด์ประกอบการสอน และการบ้านจาก **Google Classroom** อัตโนมัติ พร้อมระบบตั้งเวลาซิงค์ (Scheduler) และระบบ **AI สรุปเนื้อหาเอกสาร** ช่วยเตรียมสอบ

---

## ✨ ฟีเจอร์หลัก (Key Features)

- **🔄 Automated Scraper & Downloader**: ดึงไฟล์เอกสาร สไลด์ PDF และไฟล์แนบจากทุกวิชาใน Google Classroom ลงเครื่องโดยอัตโนมัติ พร้อมระบบตรวจจับไฟล์ซ้ำ (Deduplication via SHA256)
- **🔐 Google OAuth 2.0 Web Flow**: ระบบเข้าสู่ระบบด้วยบัญชี Google (รองรับทั้งอีเมลส่วนตัวและอีเมลมหาวิทยาลัย) ใช้มาตรฐานความปลอดภัย PKCE และ Web-based redirect flow
- **⏰ Scheduled Sync**: ตั้งเวลาให้ระบบตรวจสอบและดาวน์โหลดไฟล์ใหม่ประจำวัน/ประจำสัปดาห์อัตโนมัติด้วย Cron-like Background Scheduler (APScheduler)
- **🤖 AI Document Summarizer**: สรุปเนื้อหาเอกสารการเรียนและสไลด์ PDF อัตโนมัติ รองรับ AI 3 ค่าย:
  - **Google Gemini** (Gemini 1.5 Flash)
  - **OpenAI** (GPT-4o / GPT-4o-mini)
  - **Ollama** (Local AI ไม่เสียค่าใช้จ่าย เช่น Llama 3)
- **📦 One-Click Export**: ส่งออกไฟล์ทั้งวิชาเป็นไฟล์ **ZIP** หรือรวมเนื้อหาเป็น **Markdown Text** เพื่อนำไปใช้อ่านทบทวนต่อใน **NotebookLM** หรือ ChatGPT ได้ทันที
- **💻 Responsive Dark Theme Dashboard**: หน้าแดชบอร์ดจัดการคอร์ส ไฟล์ และตารางเวลา สวยงาม ใช้งานง่าย โหลดไว ไม่ต้องใช้ JavaScript Framework ซับซ้อน

---

## 🛠️ สถาปัตยกรรมและเทคโนโลยี (Tech Stack)

| ส่วนประกอบ | เทคโนโลยีที่ใช้ | รายละเอียด |
|---|---|---|
| **Backend** | Python 3.10+ / FastAPI / Uvicorn | High-performance Asynchronous REST API |
| **Database** | SQLite + SQLAlchemy ORM | จัดเก็บประวัติคอร์ส, รายการไฟล์, Logs, และการตั้งเวลา |
| **Scheduler** | APScheduler | รันงานเบื้องหลัง (Background Task) สำหรับ Auto-sync |
| **Google APIs** | Google Classroom API v1, Drive API v3 | ดึงข้อมูลวิชา โพสต์ และดาวน์โหลดไฟล์เอกสาร |
| **Text & AI** | PyPDF2, Google Generative AI, OpenAI | ดึงข้อความจาก PDF และส่งให้ LLM วิเคราะห์สรุปเนื้อหา |
| **Frontend** | Vanilla HTML5, Modern CSS, JavaScript ES6 | ออกแบบด้วย Glassmorphism + Dark Mode, Font Awesome Icons |

---

## 📁 โครงสร้างโปรเจกต์ (Project Structure)

```text
webscraping-classroom/
├── app/
│   ├── api/                     # REST API Endpoints
│   │   ├── routes_auth.py       # ระบบ Login / Callback / Logout
│   │   ├── routes_courses.py    # จัดการคอร์สและสั่ง Sync รายวิชา
│   │   ├── routes_files.py      # รายการไฟล์และดาวน์โหลด
│   │   ├── routes_schedule.py   # จัดการตารางเวลาซิงค์
│   │   ├── routes_ai.py         # จัดการ AI Settings และสั่งสรุปเนื้อหา
│   │   └── routes_export.py     # ส่งออก ZIP และรวมเนื้อหาข้อความ
│   ├── auth/
│   │   └── google_oauth.py      # Core OAuth 2.0 (PKCE, Token Refresh, Callback)
│   ├── scraper/
│   │   ├── classroom_api.py     # เชื่อมต่อ Google Classroom ดึงโพสต์และลิงก์
│   │   ├── drive_downloader.py  # เชื่อมต่อ Google Drive ดาวน์โหลดไฟล์
│   │   └── dedup.py             # ตรวจสอบไฟล์ซ้ำด้วย Hash
│   ├── scheduler/
│   │   └── job_manager.py       # จัดการ Cron jobs สำหรับการซิงค์ไฟล์
│   ├── summarizer/
│   │   ├── text_extractor.py    # สกัดข้อความจาก PDF / TXT / MD
│   │   └── ai_client.py         # เชื่อมต่อ Gemini, OpenAI, Ollama
│   ├── static/                  # Web Dashboard UI
│   │   ├── index.html           # โครงสร้างหน้าเว็บ
│   │   ├── style.css            # ธีม Dark Mode & CSS Variables
│   │   └── app.js               # Frontend Logic & API Calling
│   ├── config.py                # Pydantic Settings & Environment Loader
│   ├── database.py              # SQLite Schema & DB Session
│   └── main.py                  # จุดเริ่มต้นรัน FastAPI & Mount Static Files
├── credentials/                 # (Gitignored) ไฟล์รับรองความปลอดภัย
│   ├── client_secret.json       # OAuth 2.0 Client Secret จาก Google Cloud
│   └── token.json               # User Access & Refresh Token (สร้างอัตโนมัติ)
├── data/                        # โฟลเดอร์เก็บฐานข้อมูล SQLite (classroom.db)
├── downloads/                   # โฟลเดอร์จัดเก็บไฟล์ที่ดาวน์โหลดมาตามชื่อวิชา
│   └── exports/                 # โฟลเดอร์เก็บไฟล์ ZIP ที่ Export
├── .env.example                 # ตัวอย่างการตั้งค่า Environment Variables
├── .gitignore                   # กำหนดไฟล์ที่ไม่ต้องติดตามใน Git
├── requirements.txt             # รายการ Python Packages ที่ต้องติดตั้ง
└── README.md                    # เอกสารคู่มือการใช้งานโปรเจกต์
```

---

## 🚀 ขั้นตอนการติดตั้งและเริ่มต้นใช้งาน (Getting Started)

### 1. โคลนโปรเจกต์และสร้าง Virtual Environment

```bash
# 1. เข้าสู่โฟลเดอร์โปรเจกต์
cd "webscraping classroom"

# 2. สร้าง Virtual Environment (แนะนำ)
python -m venv .venv

# 3. เปิดใช้งาน Environment
# บน Windows PowerShell:
.venv\Scripts\Activate.ps1
# บน macOS / Linux:
source .venv/bin/activate
```

### 2. ติดตั้ง Dependencies

```bash
pip install -r requirements.txt
```

### 3. เตรียม Google Cloud OAuth Credentials

1. ไปที่ [Google Cloud Console](https://console.cloud.google.com/)
2. สร้างโปรเจกต์ใหม่ (หรือใช้โปรเจกต์เดิม)
3. ไปที่ **APIs & Services > Library** แล้วกดเปิดใช้งาน (Enable):
   - **Google Classroom API**
   - **Google Drive API**
4. ไปที่ **APIs & Services > OAuth consent screen**:
   - เลือกประเภท **External**
   - ตั้งชื่อแอป และใส่อีเมลติดต่อ
   - ในแท็บ **Test users** เพิ่มอีเมล Google ที่จะใช้ล็อกอิน (เช่น อีเมลนักศึกษา หรือ Gmail ส่วนตัว)
5. ไปที่ **APIs & Services > Credentials**:
   - กด **Create Credentials > OAuth client ID**
   - Application type: เลือก **Web application** (หรือ **Desktop app**)
   - หากเลือก Web application ให้เพิ่ม **Authorized redirect URIs**:
     ```
     http://127.0.0.1:8000/api/auth/callback
     ```
   - ดาวน์โหลดไฟล์ JSON และนำมาวางไว้ที่:
     ```
     credentials/client_secret.json
     ```

### 4. รันเซิร์ฟเวอร์ (Start the Server)

```bash
python -m app.main
```
หรือใช้ Uvicorn:
```bash
uvicorn app.main:app --host 127.0.0.1 --port 8000 --reload
```

### 5. เปิดใช้งาน Dashboard

เปิดเว็บเบราว์เซอร์แล้วไปที่:
👉 **[http://127.0.0.1:8000](http://127.0.0.1:8000)**

1. กดปุ่ม **Authorize Access** เพื่อล็อกอินด้วยบัญชี Google
2. เลือกวิชาที่ต้องการ และกด **Track** เพื่อเปิดการติดตาม
3. กดปุ่ม **Sync Now** เพื่อเริ่มดาวน์โหลดไฟล์เอกสาร
4. ไปที่แท็บ **Files** เพื่อเปิดดู ดาวน์โหลด หรือกดให้ **AI Summarize** สรุปเนื้อหาได้ทันที

---

## 📡 API Endpoints (Swagger UI)

คุณสามารถเปิดดู Interactive API Documentation ได้ที่:
👉 **`http://127.0.0.1:8000/docs`**

| Method | Endpoint | คำอธิบาย |
|---|---|---|
| `GET` | `/api/auth/status` | ตรวจสอบสถานะการเชื่อมต่อ Google |
| `GET` | `/api/auth/login` | เริ่มกระบวนการ Login (Redirect ไป Google Consent) |
| `GET` | `/api/auth/callback` | Callback URL รับ Authorization Code |
| `POST` | `/api/auth/logout` | ออกจากระบบและล้าง Token |
| `GET` | `/api/courses` | รายชื่อวิชาทั้งหมดใน Google Classroom |
| `POST` | `/api/courses/{id}/track` | เปิด/ปิดการติดตามวิชา |
| `POST` | `/api/courses/{id}/sync` | สั่ง Sync ดาวน์โหลดไฟล์ของวิชาทันที |
| `GET` | `/api/files` | รายการไฟล์ที่ดาวน์โหลดแล้วทั้งหมด |
| `GET` | `/api/files/{id}/download` | ดาวน์โหลดไฟล์ตรงจากเครื่อง |
| `POST` | `/api/ai/summarize` | สั่งให้ AI สรุปเนื้อหาไฟล์ที่ระบุ |
| `GET` | `/api/export/{course_id}/zip` | ส่งออกไฟล์ทั้งวิชาเป็นไฟล์ ZIP |

---

## 💡 หมายเหตุและการแก้ปัญหา (FAQ / Troubleshooting)

- **ปัญหา Token หมดอายุ (Token Expired)**:
  ในสถานะ Testing Mode ของ Google Cloud OAuth ตัว Refresh Token จะมีอายุ 7 วัน หากไม่ได้เข้าใช้นานจน Token หมดอายุ หน้าเว็บจะแจ้งเตือน ให้กดปุ่ม **Authorize Access** เพื่อต่ออายุ Token ใหม่ได้ทันที
- **ปัญหา Google แจ้งเตือน "Google hasn't verified this app"**:
  เนื่องจากเป็นแอปที่พัฒนาขึ้นเองและอยู่ใน Testing Mode ให้กดคลิก **Advanced > Go to Classroom Scraper (unsafe)** เพื่อดำเนินการต่อ
- **การตั้งค่า AI Provider**:
  สามารถเข้าไปที่แท็บ **AI Settings** ในหน้าเว็บเพื่อใส่ Gemini API Key หรือ OpenAI API Key หรือเลือกเชื่อมต่อกับ Ollama ที่รันอยู่ในเครื่องได้โดยตรง
