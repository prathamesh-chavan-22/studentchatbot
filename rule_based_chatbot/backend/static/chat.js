const chat = document.getElementById("chat");
const form = document.getElementById("chat-form");
const messageInput = document.getElementById("message");

function addMessage(text, role = "bot") {
  const node = document.createElement("div");
  node.className = `msg ${role}`;
  node.textContent = text;
  chat.appendChild(node);
  chat.scrollTop = chat.scrollHeight;
}

function addSuggestions(suggestions) {
  const wrapper = document.createElement("div");
  wrapper.className = "msg bot";
  const title = document.createElement("div");
  title.textContent = "I couldn't find an exact match. Please select one related question:";
  wrapper.appendChild(title);

  const list = document.createElement("div");
  list.className = "suggestions";
  suggestions.forEach((item) => {
    const button = document.createElement("button");
    button.type = "button";
    button.className = "suggestion-btn";
    button.textContent = item.question;
    button.onclick = async () => {
      const res = await fetch("/api/chat/select", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ qna_id: item.id }),
      });
      const data = await res.json();
      addMessage(item.question, "user");
      addMessage(data.answer, "bot");
      wrapper.remove();
    };
    list.appendChild(button);
  });
  wrapper.appendChild(list);
  chat.appendChild(wrapper);
  chat.scrollTop = chat.scrollHeight;
}

form.addEventListener("submit", async (event) => {
  event.preventDefault();
  const text = messageInput.value.trim();
  if (!text) return;

  addMessage(text, "user");
  messageInput.value = "";

  const response = await fetch("/api/chat/ask", {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ message: text }),
  });
  const data = await response.json();
  if (data.type === "answer") {
    addMessage(data.answer, "bot");
  } else {
    addSuggestions(data.suggestions || []);
  }
});

addMessage("Ask an exact question. If not exact, I'll give top 4 related questions.", "bot");
