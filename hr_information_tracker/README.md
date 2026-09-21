# HR Employee Chatbot — Full Stack Application

A full-stack AI-powered HR portal where employees can log in and interact with a chatbot to view and update their HR records. Built with **React**, **FastAPI**, **GROQ AI**, and **Supabase**.

---

## 🏗️ Architecture

```
React Frontend (Vite)
        │  JWT + REST
        ▼
FastAPI Backend
        │
        ├── Auth (bcrypt + JWT)
        │
        └── Supervisor Agent (GROQ llama-3.3-70b)
                │
                ├── Details Agent ←→ Supabase (read/update own; read subordinates)
                └── Service Agent ←→ Supabase (add new employees)
```

---

## 📁 Project Structure

```
Antigravity/
├── frontend/               # React + Vite
│   └── src/
│       ├── pages/
│       │   ├── LoginPage.jsx   # Login (light blue + orange theme)
│       │   └── ChatPage.jsx    # AI chatbot interface
│       └── components/
│           ├── Sidebar.jsx     # Employee info + quick actions
│           └── ChatMessage.jsx # Message bubble with tool trace
│
├── backend/                # Python FastAPI
│   ├── main.py             # API routes
│   ├── auth.py             # JWT + bcrypt
│   ├── config.py           # Settings + GROQ key management
│   ├── supabase_client.py  # Supabase singleton
│   ├── models.py           # Pydantic models
│   ├── agents/
│   │   ├── supervisor.py   # Orchestrator agent
│   │   ├── details_agent.py  # Read/update details
│   │   └── service_agent.py  # Add new employees
│   └── tools/
│       ├── dispatch.py     # Type-safe tool call dispatch
│       ├── read_tools.py   # Read-only Supabase operations
│       └── write_tools.py  # Write operations + rule enforcement
│
├── rules.md                # Business access rules
├── database_steps.md       # Supabase setup guide
└── README.md               # This file
```

---

## 🚀 Quick Start

### 1. Set up Supabase
Follow [database_steps.md](./database_steps.md) to create your tables and seed data.

### 2. Configure the Backend

```bash
cd backend
cp .env.example .env   # ⚠️ One-time setup only — skip if backend/.env already exists
```

> **⚠️ Do not re-run this command** once you have filled in your real credentials.
> It will overwrite your `.env` with the placeholder template again.

Then open `backend/.env` and fill in your real values:
```env
SUPABASE_URL=https://your-real-project.supabase.co
SUPABASE_SERVICE_KEY=your-real-service-role-key
JWT_SECRET=any-long-random-string
```

Install dependencies:
```bash
pip install -r requirements.txt
```

Start the backend:
```bash
# From the project root (Antigravity/)
uvicorn backend.main:app --reload --port 8000
```

### 3. Start the Frontend

```bash
cd frontend
npm install
npm run dev
```

Open [http://localhost:5173](http://localhost:5173).

---

## 🔑 Setting the GROQ API Key

The GROQ API key is configured at runtime through the web UI — **not stored in any file**.

1. Start the app and log in.
2. A yellow banner will appear at the top: "Set your GROQ API Key".
3. Enter your key (get one free at [console.groq.com](https://console.groq.com)).
4. Click **Save Key**.

The key resets on server restart. You can also set it via API:
```bash
curl -X POST http://localhost:8000/auth/configure-key \
  -H "Content-Type: application/json" \
  -d '{"groq_api_key": "gsk_..."}'
```

---

## 👥 Access Levels

| Level | Role | Can View | Can Update | Can Add |
|---|---|---|---|---|
| Level 1 | Staff | Own details | Own details | Nothing |
| Level 2 | Manager | Own + all Level 1 | Own details only | Level 1 Staff |
| Level 3 | Boss | Own + Level 1 + Level 2 | Own details only | Level 1 Staff + Level 2 Manager |

See [rules.md](./rules.md) for the full rule set.

---

## 🧪 Test Credentials

After seeding the database (see `database_steps.md`):

| Employee ID | Password | Role |
|---|---|---|
| `EMP001` | `password123` | Level 1 Staff |
| `EMP002` | `password123` | Level 2 Manager |
| `EMP003` | `password123` | Level 3 Boss |

---

## 💬 Example Chat Interactions

- _"Show me my details"_ → Displays your HR profile
- _"Update my address to 25 Park Lane, Delhi"_ → Updates your address (confirmation required)
- _"List all staff under me"_ → (Level 2/3) Shows subordinate list
- _"Add a new staff member named John Doe, 9876543210, 10 Oak Road"_ → (Level 2/3) Creates new employee
- _"Add a new manager named Jane Smith..."_ → (Level 3 only) Creates manager account

---

## 🔧 API Endpoints

| Method | Path | Description |
|---|---|---|
| POST | `/auth/login` | Login → JWT |
| POST | `/auth/configure-key` | Set GROQ key |
| GET | `/auth/key-status` | Check if GROQ key is set |
| GET | `/auth/me` | Get own profile |
| POST | `/chat/message` | Send chat message |
| GET | `/chat/history` | Get session history |
| DELETE | `/chat/history` | Clear session |
| GET | `/health` | Health check |

Swagger UI: [http://localhost:8000/docs](http://localhost:8000/docs)
