(function(){const a=document.createElement("link").relList;if(a&&a.supports&&a.supports("modulepreload"))return;for(const t of document.querySelectorAll('link[rel="modulepreload"]'))d(t);new MutationObserver(t=>{for(const n of t)if(n.type==="childList")for(const s of n.addedNodes)s.tagName==="LINK"&&s.rel==="modulepreload"&&d(s)}).observe(document,{childList:!0,subtree:!0});function e(t){const n={};return t.integrity&&(n.integrity=t.integrity),t.referrerPolicy&&(n.referrerPolicy=t.referrerPolicy),t.crossOrigin==="use-credentials"?n.credentials="include":t.crossOrigin==="anonymous"?n.credentials="omit":n.credentials="same-origin",n}function d(t){if(t.ep)return;t.ep=!0;const n=e(t);fetch(t.href,n)}})();const l=document.getElementById("app"),u=`
  body { margin: 0; font-family: Arial, sans-serif; background: #f6f8fb; }
  .wrap { max-width: 900px; margin: 24px auto; background: #fff; border-radius: 10px; box-shadow: 0 2px 12px rgba(0,0,0,.08); padding: 20px; }
  input, textarea { width: 100%; box-sizing: border-box; margin: 6px 0 12px; padding: 8px; border: 1px solid #d1d5db; border-radius: 8px; }
  button { border: 0; padding: 8px 10px; border-radius: 8px; background: #2563eb; color: #fff; cursor: pointer; margin-right: 6px; }
  table { width: 100%; border-collapse: collapse; margin-top: 16px; }
  th, td { border-bottom: 1px solid #e5e7eb; padding: 8px; text-align: left; vertical-align: top; }
  .danger { background: #dc2626; }
`;document.head.appendChild(Object.assign(document.createElement("style"),{textContent:u}));async function r(o,a={}){const e=await fetch(o,{credentials:"include",headers:{"Content-Type":"application/json",...a.headers||{}},...a});if(e.status===204)return null;const d=await e.json().catch(()=>({}));if(!e.ok)throw new Error(d.detail||"Request failed");return d}function c(){l.innerHTML=`
    <div class="wrap">
      <h2>Admin Login</h2>
      <label>Username</label>
      <input id="username" value="admin" />
      <label>Password</label>
      <input id="password" type="password" value="admin123" />
      <button id="login-btn">Login</button>
      <div id="error" style="color:#dc2626;margin-top:8px;"></div>
    </div>
  `,document.getElementById("login-btn").onclick=async()=>{try{await r("/api/admin/login",{method:"POST",body:JSON.stringify({username:document.getElementById("username").value,password:document.getElementById("password").value})}),await i()}catch(o){document.getElementById("error").textContent=o.message}}}async function i(){const o=await r("/api/admin/qna");l.innerHTML=`
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
  `;const a=document.getElementById("rows");a.innerHTML=o.map(e=>`
      <tr>
        <td>${e.id}</td>
        <td>${e.question}</td>
        <td>${e.answer}</td>
        <td><button class="danger" data-id="${e.id}">Delete</button></td>
      </tr>
    `).join(""),document.querySelectorAll("button.danger[data-id]").forEach(e=>{e.onclick=async()=>{await r(`/api/admin/qna/${e.dataset.id}`,{method:"DELETE"}),await i()}}),document.getElementById("add-btn").onclick=async()=>{try{await r("/api/admin/qna",{method:"POST",body:JSON.stringify({question:document.getElementById("new-question").value,answer:document.getElementById("new-answer").value})}),await i()}catch(e){document.getElementById("err").textContent=e.message}},document.getElementById("refresh-btn").onclick=i,document.getElementById("logout-btn").onclick=async()=>{await r("/api/admin/logout",{method:"POST"}),c()}}async function p(){try{await r("/api/admin/me"),await i()}catch{c()}}p();
