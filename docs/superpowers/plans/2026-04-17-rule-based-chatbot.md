# Rule-Based Chatbot Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Build a new `rule_based_chatbot` project with exact-match-first chat behavior, top-4 related suggestions on non-exact inputs, and a password-protected admin dashboard for Q&A management.

**Architecture:** The solution uses a FastAPI backend with SQLite for persistence and auth-protected admin APIs. Chat UI is server-rendered in backend templates/static while admin UI is a separate Vite frontend calling backend APIs. Matching is deterministic: exact match first, otherwise lexical similarity ranking for top-4 suggestions.

**Tech Stack:** Python, FastAPI, SQLAlchemy, SQLite, passlib/bcrypt, Jinja2, pytest, Node.js, Vite, vanilla JavaScript

---

### Task 1: Scaffold new project structure

**Files:**
- Create: `rule_based_chatbot/backend/app/main.py`
- Create: `rule_based_chatbot/backend/app/__init__.py`
- Create: `rule_based_chatbot/backend/templates/index.html`
- Create: `rule_based_chatbot/backend/static/chat.js`
- Create: `rule_based_chatbot/backend/requirements.txt`
- Create: `rule_based_chatbot/backend/tests/test_chat_api.py`
- Create: `rule_based_chatbot/admin/package.json`
- Create: `rule_based_chatbot/admin/index.html`
- Create: `rule_based_chatbot/admin/src/main.js`

- [ ] **Step 1: Write failing backend smoke test**
```python
def test_health_endpoint(client):
    resp = client.get("/health")
    assert resp.status_code == 200
```

- [ ] **Step 2: Run test to verify it fails**
Run: `cd rule_based_chatbot/backend && pytest -q tests/test_chat_api.py::test_health_endpoint`
Expected: FAIL (app not created yet)

- [ ] **Step 3: Add minimal FastAPI app + health route**
```python
from fastapi import FastAPI
app = FastAPI()
@app.get("/health")
def health():
    return {"status": "ok"}
```

- [ ] **Step 4: Run test to verify it passes**
Run: `cd rule_based_chatbot/backend && pytest -q tests/test_chat_api.py::test_health_endpoint`
Expected: PASS

### Task 2: Implement SQLite models and DB setup

**Files:**
- Create: `rule_based_chatbot/backend/app/db.py`
- Create: `rule_based_chatbot/backend/app/models.py`
- Create: `rule_based_chatbot/backend/tests/test_db.py`

- [ ] **Step 1: Write failing DB tests for qna/admin_users tables**
```python
def test_tables_exist(engine):
    ...
```

- [ ] **Step 2: Run DB tests and confirm failure**
Run: `cd rule_based_chatbot/backend && pytest -q tests/test_db.py`
Expected: FAIL (tables missing)

- [ ] **Step 3: Implement SQLAlchemy engine, session, and table models**
```python
class QnA(Base): ...
class AdminUser(Base): ...
```

- [ ] **Step 4: Re-run DB tests**
Run: `cd rule_based_chatbot/backend && pytest -q tests/test_db.py`
Expected: PASS

### Task 3: Build exact-match + top-4 suggestion chat APIs

**Files:**
- Create: `rule_based_chatbot/backend/app/chat_service.py`
- Create: `rule_based_chatbot/backend/app/chat_routes.py`
- Modify: `rule_based_chatbot/backend/app/main.py`
- Test: `rule_based_chatbot/backend/tests/test_chat_api.py`

- [ ] **Step 1: Write failing tests for exact hit and non-exact suggestions**
```python
def test_exact_match_returns_answer(...): ...
def test_non_exact_returns_top4(...): ...
def test_select_suggestion_returns_stored_answer(...): ...
```

- [ ] **Step 2: Run focused tests and confirm failure**
Run: `cd rule_based_chatbot/backend && pytest -q tests/test_chat_api.py -k "exact_match or non_exact or select"`
Expected: FAIL

- [ ] **Step 3: Implement chat service and routes**
```python
# POST /api/chat/ask
# POST /api/chat/select
```

- [ ] **Step 4: Re-run focused tests**
Run: `cd rule_based_chatbot/backend && pytest -q tests/test_chat_api.py -k "exact_match or non_exact or select"`
Expected: PASS

### Task 4: Implement admin authentication and protected CRUD APIs

**Files:**
- Create: `rule_based_chatbot/backend/app/auth.py`
- Create: `rule_based_chatbot/backend/app/admin_routes.py`
- Modify: `rule_based_chatbot/backend/app/main.py`
- Test: `rule_based_chatbot/backend/tests/test_admin_api.py`

- [ ] **Step 1: Write failing auth/authorization CRUD tests**
```python
def test_admin_routes_require_auth(...): ...
def test_login_success_and_failure(...): ...
def test_qna_crud(...): ...
```

- [ ] **Step 2: Run tests and confirm failure**
Run: `cd rule_based_chatbot/backend && pytest -q tests/test_admin_api.py`
Expected: FAIL

- [ ] **Step 3: Implement login/logout/me + protected CRUD endpoints**
```python
# POST /api/admin/login, /logout
# GET /api/admin/me
# GET/POST/PUT/DELETE /api/admin/qna
```

- [ ] **Step 4: Re-run admin tests**
Run: `cd rule_based_chatbot/backend && pytest -q tests/test_admin_api.py`
Expected: PASS

### Task 5: Build separate admin frontend app

**Files:**
- Modify: `rule_based_chatbot/admin/package.json`
- Modify: `rule_based_chatbot/admin/src/main.js`
- Create: `rule_based_chatbot/admin/src/api.js`
- Create: `rule_based_chatbot/admin/src/styles.css`

- [ ] **Step 1: Write minimal frontend smoke checklist in code comments/tests**
```javascript
// login -> fetch list -> add row -> delete row
```

- [ ] **Step 2: Run frontend build to ensure baseline fails until wired**
Run: `cd rule_based_chatbot/admin && npm run build`
Expected: PASS after implementation

- [ ] **Step 3: Implement login screen and Q&A CRUD dashboard**
```javascript
// renderLogin(), renderDashboard(), createQna(), deleteQna()
```

- [ ] **Step 4: Re-run frontend build**
Run: `cd rule_based_chatbot/admin && npm run build`
Expected: PASS

### Task 6: Wire chat UI and finalize integration

**Files:**
- Modify: `rule_based_chatbot/backend/templates/index.html`
- Modify: `rule_based_chatbot/backend/static/chat.js`
- Modify: `rule_based_chatbot/backend/app/main.py`
- Test: `rule_based_chatbot/backend/tests/test_chat_api.py`

- [ ] **Step 1: Add tests for end-to-end ask->suggest->select API behavior**
```python
def test_ask_then_select_flow(...): ...
```

- [ ] **Step 2: Run integration tests and confirm baseline**
Run: `cd rule_based_chatbot/backend && pytest -q tests/test_chat_api.py -k ask_then_select`
Expected: FAIL before full wiring

- [ ] **Step 3: Implement UI workflow**
```javascript
// showSuggestionButtons(); submitSelection(id)
```

- [ ] **Step 4: Run full backend tests**
Run: `cd rule_based_chatbot/backend && pytest -q`
Expected: PASS

- [ ] **Step 5: Run full frontend build**
Run: `cd rule_based_chatbot/admin && npm install && npm run build`
Expected: PASS
