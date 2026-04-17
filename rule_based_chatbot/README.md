# Rule Based Chatbot

This project is a new chatbot variant based on the semantic bot codebase, with rule-based behavior:

- exact question match -> direct answer
- non-exact match -> top 4 related questions
- user selects one suggestion -> stored answer returned as-is
- password-protected admin dashboard to add/remove/update Q&A pairs

## Backend

```bash
cd backend
pip install -r requirements.txt
python -m app.main
```

Backend runs at `http://localhost:8002`.

Default admin credentials:
- username: `admin`
- password: `admin123`

Set env vars to change:
- `ADMIN_USERNAME`
- `ADMIN_PASSWORD`
- `SESSION_SECRET`
- `DATABASE_URL`

## Admin Dashboard

```bash
cd admin
npm install
npm run dev
```

Open the Vite URL (usually `http://localhost:5173`).
