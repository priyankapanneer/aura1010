# AURA Local Setup & Run Guide

## Prerequisites

- **Python**: 3.11+ (verified: Python 3.11.7)
- **Node.js**: 18+ (verified: Node v25.4.0, npm 11.7.0)
- **Docker & Docker Compose**: Optional (for production PostgreSQL deployment)

---

## 1. Quickstart (Local Development with SQLite Fallback)

### Backend Setup:
```bash
# 1. Navigate to backend directory or root
cd backend

# 2. Activate virtual environment
# Windows:
..\.venv\Scripts\activate
# Linux/Mac:
source ../.venv/bin/activate

# 3. Install dependencies
pip install -r requirements.txt

# 4. Start the FastAPI server
uvicorn app.main:app --reload --port 8000
```
Backend API docs will be accessible at: `http://localhost:8000/docs`

### Frontend Setup:
```bash
# 1. In a separate terminal, navigate to frontend
cd frontend

# 2. Install dependencies
npm install

# 3. Launch Vite dev server
npm run dev
```
Frontend will be accessible at: `http://localhost:5173`

---

## 2. Docker Compose (Production-Like PostgreSQL)

```bash
# From workspace root
docker compose up --build
```
This launches:
- `aura_postgres` on port 5432
- `aura_backend` on port 8000
- `aura_frontend` on port 5173

---

## 3. Running Automated Tests

```bash
# Backend unit & integration tests
pytest backend/tests -v

# Frontend tests
cd frontend
npm test
```
