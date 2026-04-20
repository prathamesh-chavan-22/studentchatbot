const app = document.getElementById("app");

const styles = `
  body { margin: 0; font-family: Arial, sans-serif; background: #f6f8fb; }
  .wrap { max-width: 900px; margin: 24px auto; background: #fff; border-radius: 10px; box-shadow: 0 2px 12px rgba(0,0,0,.08); padding: 20px; }
  input, textarea { width: 100%; box-sizing: border-box; margin: 6px 0 12px; padding: 8px; border: 1px solid #d1d5db; border-radius: 8px; }
  button { border: 0; padding: 8px 10px; border-radius: 8px; background: #2563eb; color: #fff; cursor: pointer; margin-right: 6px; }
  table { width: 100%; border-collapse: collapse; margin-top: 16px; }
  th, td { border-bottom: 1px solid #e5e7eb; padding: 8px; text-align: left; vertical-align: top; }
  .danger { background: #dc2626; }
`;
document.head.appendChild(Object.assign(document.createElement("style"), { textContent: styles }));

async function api(path, options = {}) {
  const response = await fetch(path, {
    credentials: "include",
    headers: { "Content-Type": "application/json", ...(options.headers || {}) },
    ...options,
  });
  if (response.status === 204) return null;
  const data = await response.json().catch(() => ({}));
  if (!response.ok) {
    throw new Error(data.detail || "Request failed");
  }
  return data;
}

function loginView() {
  app.innerHTML = `
    <div class="wrap">
      <h2>Admin Login</h2>
      <label>Username</label>
      <input id="username" value="admin" />
      <label>Password</label>
      <input id="password" type="password" value="admin123" />
      <button id="login-btn">Login</button>
      <div id="error" style="color:#dc2626;margin-top:8px;"></div>
    </div>
  `;
  document.getElementById("login-btn").onclick = async () => {
    try {
      await api("/api/admin/login", {
        method: "POST",
        body: JSON.stringify({
          username: document.getElementById("username").value,
          password: document.getElementById("password").value,
        }),
      });
      await dashboardView();
    } catch (error) {
      document.getElementById("error").textContent = error.message;
    }
  };
}

async function dashboardView() {
  const items = await api("/api/admin/qna");
  app.innerHTML = `
    <div class="wrap">
      <div style="display:flex;justify-content:space-between;align-items:center;">
        <h2>Q&A Dashboard</h2>
        <div>
          <button id="refresh-btn">Refresh</button>
          <button id="logout-btn" class="danger">Logout</button>
        </div>
      </div>
      <h3>Add Q&A</h3>
      <label>Question</label>
      <input id="new-question" />
      <label>Answer</label>
      <textarea id="new-answer" rows="4"></textarea>
      <button id="add-btn">Add</button>
      <div id="err" style="color:#dc2626;margin-top:8px;"></div>
      <table>
        <thead><tr><th>ID</th><th>Question</th><th>Answer</th><th>Actions</th></tr></thead>
        <tbody id="rows"></tbody>
      </table>
    </div>
  `;
  const rows = document.getElementById("rows");
  rows.innerHTML = items
    .map(
      (item) => `
      <tr>
        <td>${item.id}</td>
        <td>${item.question}</td>
        <td>${item.answer}</td>
        <td><button class="danger" data-id="${item.id}">Delete</button></td>
      </tr>
    `
    )
    .join("");

  document.querySelectorAll("button.danger[data-id]").forEach((button) => {
    button.onclick = async () => {
      await api(`/api/admin/qna/${button.dataset.id}`, { method: "DELETE" });
      await dashboardView();
    };
  });

  document.getElementById("add-btn").onclick = async () => {
    try {
      await api("/api/admin/qna", {
        method: "POST",
        body: JSON.stringify({
          question: document.getElementById("new-question").value,
          answer: document.getElementById("new-answer").value,
        }),
      });
      await dashboardView();
    } catch (error) {
      document.getElementById("err").textContent = error.message;
    }
  };

  document.getElementById("refresh-btn").onclick = dashboardView;
  document.getElementById("logout-btn").onclick = async () => {
    await api("/api/admin/logout", { method: "POST" });
    loginView();
  };
}

async function bootstrap() {
  try {
    await api("/api/admin/me");
    await dashboardView();
  } catch {
    loginView();
  }
}

bootstrap();
