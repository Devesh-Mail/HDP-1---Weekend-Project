# Supabase Database Setup Guide

## Overview

This guide walks you through creating your Supabase project and setting up all four tables required for the HR Employee Chatbot. Follow each step carefully.

---

## Step 1 — Create a Supabase Project

1. Go to [https://supabase.com](https://supabase.com) and sign in (or create a free account).
2. Click **"New Project"**.
3. Fill in:
   - **Project Name**: `hr-chatbot` (or any name you prefer)
   - **Database Password**: Choose a strong password and **save it** — you'll need it later.
   - **Region**: Choose the region closest to you.
4. Click **"Create new project"** and wait ~2 minutes for provisioning.

---

## Step 2 — Get Your Connection Credentials

Once the project is ready:
1. In the left sidebar, click **"Project Settings"** → **"API"**.
2. Copy and save:
   - **Project URL** (looks like `https://xxxxxxxxxxxx.supabase.co`)
   - **anon/public key** (under "Project API Keys")
3. You'll enter these into the backend `config.py` or `.env` file.

---

## Step 3 — Open the SQL Editor

1. In the left sidebar, click **"SQL Editor"**.
2. Click **"+ New query"**.
3. Paste and run each SQL block below one at a time.

---

## Step 4 — Create the Tables

### Table 1: `login`
Stores employee credentials and their access level.

```sql
CREATE TABLE login (
    employee_id TEXT PRIMARY KEY,
    password    TEXT NOT NULL,
    status      TEXT NOT NULL CHECK (status IN ('level1', 'level2', 'level3'))
);
```

### Table 2: `level1_staff`
Stores details for Level 1 Staff employees.

```sql
CREATE TABLE level1_staff (
    staff_id        TEXT PRIMARY KEY,
    employee_id     TEXT NOT NULL UNIQUE REFERENCES login(employee_id),
    name            TEXT NOT NULL,
    contact_number  BIGINT NOT NULL UNIQUE,
    current_address TEXT NOT NULL
);
```

### Table 3: `level2_manager`
Stores details for Level 2 Manager employees.

```sql
CREATE TABLE level2_manager (
    manager_id      TEXT PRIMARY KEY,
    employee_id     TEXT NOT NULL UNIQUE REFERENCES login(employee_id),
    name            TEXT NOT NULL,
    contact_number  BIGINT NOT NULL UNIQUE,
    office_number   BIGINT NOT NULL UNIQUE,
    current_address TEXT NOT NULL
);
```

### Table 4: `level3_boss`
Stores details for Level 3 Boss employees.

```sql
CREATE TABLE level3_boss (
    boss_id         TEXT PRIMARY KEY,
    employee_id     TEXT NOT NULL UNIQUE REFERENCES login(employee_id),
    name            TEXT NOT NULL,
    current_address TEXT NOT NULL
);
```

---

## Step 5 — Disable Row Level Security (for development)

By default Supabase enables RLS (Row Level Security) which will block all reads/writes. For now, run the following to allow the backend to access the tables freely (using the service role key):

```sql
ALTER TABLE login DISABLE ROW LEVEL SECURITY;
ALTER TABLE level1_staff DISABLE ROW LEVEL SECURITY;
ALTER TABLE level2_manager DISABLE ROW LEVEL SECURITY;
ALTER TABLE level3_boss DISABLE ROW LEVEL SECURITY;
```

> ⚠️ For production, you should re-enable RLS and configure policies. The backend uses a service role key that bypasses RLS anyway, but this keeps things consistent.

---

## Step 6 — Seed Test Data

Run this to add sample accounts for testing all three levels:

```sql
-- Login accounts (passwords are bcrypt hashes of 'password123')
-- You can generate your own hashes at: https://bcrypt-generator.com
INSERT INTO login (employee_id, password, status) VALUES
    ('EMP001', '$2b$12$LQv3c1yqBWVHxkd0LHAkCOYz6TtxMaGBIsAZ8L4HKjMdnYqSP6bSa', 'level1'),
    ('EMP002', '$2b$12$LQv3c1yqBWVHxkd0LHAkCOYz6TtxMaGBIsAZ8L4HKjMdnYqSP6bSa', 'level2'),
    ('EMP003', '$2b$12$LQv3c1yqBWVHxkd0LHAkCOYz6TtxMaGBIsAZ8L4HKjMdnYqSP6bSa', 'level3');

-- Level 1 Staff
INSERT INTO level1_staff (staff_id, employee_id, name, contact_number, current_address) VALUES
    ('STF001', 'EMP001', 'Alice Johnson', 9876543210, '12 Oak Street, Chennai');

-- Level 2 Manager
INSERT INTO level2_manager (manager_id, employee_id, name, contact_number, office_number, current_address) VALUES
    ('MGR001', 'EMP002', 'Bob Smith', 9123456780, 101, '45 Palm Avenue, Bangalore');

-- Level 3 Boss
INSERT INTO level3_boss (boss_id, employee_id, name, current_address) VALUES
    ('BSS001', 'EMP003', 'Carol White', '7 Elite Tower, Mumbai');
```

> **Test credentials** (all use password: `password123`):
> - Level 1 Staff: `EMP001`
> - Level 2 Manager: `EMP002`
> - Level 3 Boss: `EMP003`

---

## Step 7 — Get the Service Role Key

The backend uses the **service role key** (not the anon key) to bypass RLS and make admin-level calls:

1. Go to **Project Settings** → **API**.
2. Under **"Project API Keys"**, copy the **`service_role`** key.
3. Add it to your backend `.env` file as `SUPABASE_SERVICE_ROLE_KEY`.

> ⚠️ Never expose the service role key in the frontend. Keep it on the server only.

---

## Step 8 — Configure the Backend `.env`

Create a file at `backend/.env` with:

```env
SUPABASE_URL=https://xxxxxxxxxxxx.supabase.co
SUPABASE_SERVICE_KEY=your_service_role_key_here
JWT_SECRET=your_random_secret_string_here
```

The GROQ API key is set at runtime through the app UI — you do not need to put it in `.env`.

---

## Table Reference Summary

| Table | Primary Key | FK to login | Level |
|---|---|---|---|
| `login` | `employee_id` | — | All |
| `level1_staff` | `staff_id` | `employee_id` | Level 1 |
| `level2_manager` | `manager_id` | `employee_id` | Level 2 |
| `level3_boss` | `boss_id` | `employee_id` | Level 3 |
