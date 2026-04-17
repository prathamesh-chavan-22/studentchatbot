# Rule-Based Chatbot Design

## Goal
Build a new chatbot in a separate folder that answers only on exact question matches, otherwise returns the top 4 related questions for the user to choose from, and includes a password-protected admin dashboard to manage Q&A pairs.

## Scope
- New project folder: `rule_based_chatbot/`
- Backend API + chat UI
- Separate admin frontend app
- SQLite storage (starting empty)
- Admin login and authenticated CRUD for Q&A

Out of scope:
- Importing existing semantic bot Q&A data
- Embedding-based search
- Cross-service SSO

## Architecture
### 1) Backend (`rule_based_chatbot/backend`)
- Framework: FastAPI
- Responsibilities:
  - Serve chat API and chat page
  - Serve admin/auth APIs
  - Persist and query SQLite data
  - Enforce admin authentication

Core modules:
- `app/main.py`: app setup, routing, lifespan
- `app/db.py`: SQLite connection/session management
- `app/models.py`: SQLAlchemy models (`qna`, `admin_users`)
- `app/schemas.py`: request/response schemas
- `app/auth.py`: password hashing, login validation, session handling
- `app/chat_service.py`: exact-match + top-4 related suggestion logic
- `app/admin_routes.py`: protected CRUD endpoints
- `app/chat_routes.py`: chat and suggestion-selection endpoints

### 2) Admin Frontend (`rule_based_chatbot/admin`)
- Framework: Vite + vanilla JS
- Responsibilities:
  - Login form and session persistence via cookie
  - List/add/update/delete Q&A records
  - Basic validation and user feedback

### 3) Chat Frontend (`rule_based_chatbot/backend/templates/static`)
- Keep simple server-rendered HTML + JS for chat experience
- Uses backend APIs for ask/suggest/select flow

## Data Model
### Table: `qna`
- `id` INTEGER PRIMARY KEY AUTOINCREMENT
- `question` TEXT NOT NULL UNIQUE
- `answer` TEXT NOT NULL
- `created_at` DATETIME NOT NULL
- `updated_at` DATETIME NOT NULL

### Table: `admin_users`
- `id` INTEGER PRIMARY KEY AUTOINCREMENT
- `username` TEXT NOT NULL UNIQUE
- `password_hash` TEXT NOT NULL
- `created_at` DATETIME NOT NULL

## API Behavior
### Chat ask endpoint
Input: user message text.

Flow:
1. Normalize text (trim, collapse spaces, lowercase for matching key).
2. Exact lookup against `qna.question` (case-insensitive normalized compare).
3. If exact hit: return answer directly.
4. If no hit: compute related results and return top 4 suggestions.

Output shape:
- Exact hit:
  - `{ "type": "answer", "answer": "..." }`
- No hit:
  - `{ "type": "suggestions", "suggestions": [{ "id": 1, "question": "..." }, ...] }`

### Suggestion select endpoint
Input: selected `qna_id`.

Flow:
1. Lookup `qna` by id.
2. Return stored answer exactly as stored.

Output:
- `{ "type": "answer", "answer": "..." }`

### Admin auth endpoints
- `POST /api/admin/login` (username/password) -> sets secure session cookie
- `POST /api/admin/logout` -> clears cookie
- `GET /api/admin/me` -> current admin identity

### Admin Q&A endpoints (auth required)
- `GET /api/admin/qna` list
- `POST /api/admin/qna` create
- `PUT /api/admin/qna/{id}` update
- `DELETE /api/admin/qna/{id}` delete

## Related Question Ranking (No Embeddings)
Use lexical scoring to keep behavior deterministic and lightweight:
- Candidate retrieval from all rows
- Score formula combines:
  - token overlap ratio
  - character trigram overlap ratio
  - normalized Levenshtein similarity
- Rank descending and return first 4 unique questions.

If fewer than 4 exist, return available count.

## Security & Validation
- Password hashing via `bcrypt`/`passlib`
- Session auth via signed cookie token
- Admin routes require valid session
- Input validation for required fields and max lengths
- Duplicate question prevention via unique constraint

## Testing Plan
Backend tests:
1. Exact match returns answer payload.
2. Non-exact returns suggestions payload with max 4 items.
3. Suggestion selection returns stored answer exactly.
4. Admin endpoints reject unauthorized access.
5. Admin login success/failure.
6. CRUD lifecycle (create/list/update/delete).
7. Duplicate question creation fails cleanly.

Frontend smoke checks:
1. Admin login UI flow
2. Add and delete Q&A from dashboard

## Success Criteria
- New chatbot exists in `rule_based_chatbot/`
- Exact questions answer immediately
- Non-exact questions return top 4 suggestions
- Selecting a suggestion returns the stored answer as-is
- Admin dashboard can securely add and remove Q&A pairs
