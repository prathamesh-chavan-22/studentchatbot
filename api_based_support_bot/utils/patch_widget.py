import re

with open('static/widget.js', 'r') as f:
    content = f.read()

styles_new = """
  const styles = `
    .chat-widget-container {
      position: fixed;
      right: 24px;
      bottom: 24px;
      display: flex;
      flex-direction: column;
      align-items: flex-end;
      gap: 16px;
      z-index: 99999;
      font-family: 'Inter', system-ui, -apple-system, sans-serif;
    }
    .chat-toggle {
      border: none;
      background: linear-gradient(135deg, #f97316 0%, #ea580c 100%);
      color: #fff;
      width: 64px;
      height: 64px;
      padding: 0;
      border-radius: 50%;
      display: flex;
      justify-content: center;
      align-items: center;
      cursor: pointer;
      box-shadow: 0 12px 28px rgba(234, 88, 12, 0.4);
      transition: all 0.3s cubic-bezier(0.34, 1.56, 0.64, 1);
    }
    .chat-toggle:hover {
      transform: scale(1.08) translateY(-4px);
      box-shadow: 0 16px 32px rgba(234, 88, 12, 0.5);
    }
    .chat-toggle svg {
      width: 32px;
      height: 32px;
      animation: float 3s ease-in-out infinite;
    }
    @keyframes float {
      0% { transform: translateY(0px) rotate(0deg); }
      50% { transform: translateY(-4px) rotate(2deg); }
      100% { transform: translateY(0px) rotate(0deg); }
    }
    .chat-tooltip {
      background: rgba(255, 255, 255, 0.95);
      backdrop-filter: blur(10px);
      -webkit-backdrop-filter: blur(10px);
      color: #1e293b;
      padding: 14px 20px;
      border-radius: 16px;
      font-size: 0.95rem;
      font-weight: 600;
      box-shadow: 0 10px 30px rgba(0, 0, 0, 0.12);
      border: 1px solid rgba(255, 255, 255, 0.6);
      position: absolute;
      bottom: 80px;
      right: 0;
      white-space: nowrap;
      opacity: 0;
      transform: translateY(15px) scale(0.95);
      pointer-events: none;
      transition: all 0.4s cubic-bezier(0.16, 1, 0.3, 1);
      transform-origin: bottom right;
    }
    .chat-tooltip::after {
      content: '';
      position: absolute;
      bottom: -6px;
      right: 26px;
      width: 14px;
      height: 14px;
      background: #ffffff;
      transform: rotate(45deg);
      box-shadow: 4px 4px 6px rgba(0, 0, 0, 0.04);
      border-right: 1px solid rgba(255,255,255,0.6);
      border-bottom: 1px solid rgba(255,255,255,0.6);
    }
    .chat-tooltip.visible {
      opacity: 1;
      transform: translateY(0) scale(1);
    }
    .chat-box {
      position: fixed;
      right: 24px;
      bottom: 100px;
      width: min(380px, calc(100vw - 48px));
      height: 600px;
      max-height: calc(100vh - 140px);
      background: rgba(255, 255, 255, 0.96);
      backdrop-filter: blur(20px);
      -webkit-backdrop-filter: blur(20px);
      border-radius: 20px;
      border: 1px solid rgba(255, 255, 255, 0.8);
      box-shadow: 0 24px 48px rgba(15, 23, 42, 0.16), 0 0 0 1px rgba(15, 23, 42, 0.05);
      display: flex;
      flex-direction: column;
      overflow: hidden;
      z-index: 99999;
      opacity: 0;
      transform: translateY(20px) scale(0.95);
      pointer-events: none;
      transition: all 0.3s cubic-bezier(0.16, 1, 0.3, 1);
      transform-origin: bottom right;
    }
    .chat-box:not(.fyjc-chat-hidden) {
      opacity: 1;
      transform: translateY(0) scale(1);
      pointer-events: auto;
    }
    .chat-box.fyjc-chat-hidden {
      display: flex;
    }
    .chat-header {
      background: linear-gradient(90deg, #0ea5e9 0%, #0284c7 100%);
      color: #fff;
      padding: 18px 20px;
      display: flex;
      justify-content: space-between;
      align-items: center;
      border-bottom: 1px solid rgba(255,255,255,0.1);
      flex-shrink: 0;
    }
    .chat-header-info {
      display: flex;
      flex-direction: column;
      align-items: flex-start;
      gap: 4px;
    }
    .chat-header-info strong {
      font-size: 1.1rem;
      font-weight: 700;
      letter-spacing: -0.01em;
      text-shadow: 0 1px 2px rgba(0,0,0,0.1);
    }
    .status-container {
      display: flex;
      align-items: center;
      gap: 6px;
      background: rgba(0,0,0,0.15);
      padding: 4px 10px;
      border-radius: 20px;
    }
    .status-indicator {
      width: 8px;
      height: 8px;
      border-radius: 50%;
      display: inline-block;
      transition: background-color 0.3s ease;
    }
    .status-online {
      background-color: #4ade80;
      box-shadow: 0 0 10px rgba(74, 222, 128, 0.8);
      animation: pulse-online 2s infinite;
    }
    .status-offline {
      background-color: #cbd5e1;
    }
    .status-text {
      font-size: 0.75rem;
      font-weight: 500;
      color: #f8fafc;
    }
    @keyframes pulse-online {
      0% { transform: scale(1); box-shadow: 0 0 0 0 rgba(74, 222, 128, 0.7); }
      70% { transform: scale(1.1); box-shadow: 0 0 0 6px rgba(74, 222, 128, 0); }
      100% { transform: scale(1); box-shadow: 0 0 0 0 rgba(74, 222, 128, 0); }
    }
    .header-actions {
      display: flex;
      gap: 12px;
      align-items: center;
    }
    .header-btn {
      border: none;
      background: rgba(255, 255, 255, 0.15);
      color: #fff;
      width: 32px;
      height: 32px;
      border-radius: 50%;
      display: flex;
      justify-content: center;
      align-items: center;
      cursor: pointer;
      transition: background 0.2s, transform 0.2s;
    }
    .header-btn:hover {
      background: rgba(255, 255, 255, 0.3);
      transform: scale(1.05);
    }
    .header-btn svg { width: 16px; height: 16px; }
    
    .chat-messages {
      flex: 1;
      padding: 20px;
      overflow-y: auto;
      background: #f8fafc;
      display: flex;
      flex-direction: column;
      gap: 16px;
      scroll-behavior: smooth;
    }
    .chat-messages::-webkit-scrollbar { width: 6px; }
    .chat-messages::-webkit-scrollbar-track { background: transparent; }
    .chat-messages::-webkit-scrollbar-thumb { background: #cbd5e1; border-radius: 10px; }
    .chat-messages::-webkit-scrollbar-thumb:hover { background: #94a3b8; }

    .bot-msg, .user-msg {
      max-width: 85%;
      padding: 12px 16px;
      border-radius: 16px;
      white-space: pre-wrap;
      font-size: 0.95rem;
      line-height: 1.5;
      animation: msg-entrance 0.4s cubic-bezier(0.16, 1, 0.3, 1) forwards;
      opacity: 0;
      box-shadow: 0 2px 5px rgba(0,0,0,0.02);
    }
    @keyframes msg-entrance {
      from { opacity: 0; transform: translateY(10px); }
      to { opacity: 1; transform: translateY(0); }
    }
    .bot-msg { 
      background: #ffffff; 
      color: #334155;
      align-self: flex-start; 
      border-bottom-left-radius: 4px;
      border: 1px solid #e2e8f0;
    }
    .user-msg { 
      background: linear-gradient(135deg, #0ea5e9 0%, #0284c7 100%); 
      color: #ffffff;
      align-self: flex-end; 
      border-bottom-right-radius: 4px;
      box-shadow: 0 4px 12px rgba(2, 132, 199, 0.15);
    }
    .bot-msg.temp {
      display: flex;
      align-items: center;
      gap: 4px;
      color: #64748b;
      background: transparent;
      border: none;
      box-shadow: none;
      padding: 8px 12px;
    }
    .typing-dot {
      width: 6px; height: 6px;
      background: #94a3b8;
      border-radius: 50%;
      animation: typing 1.4s infinite ease-in-out both;
    }
    .typing-dot:nth-child(1) { animation-delay: -0.32s; }
    .typing-dot:nth-child(2) { animation-delay: -0.16s; }
    @keyframes typing {
      0%, 80%, 100% { transform: scale(0); }
      40% { transform: scale(1); }
    }
    
    .chat-input-wrap {
      display: flex;
      gap: 12px;
      padding: 16px;
      background: #ffffff;
      align-items: center;
    }
    .chat-input-wrap input {
      flex: 1;
      padding: 14px 20px;
      border-radius: 24px;
      border: 1px solid #e2e8f0;
      background: #f8fafc;
      font-size: 0.95rem;
      transition: all 0.2s;
      outline: none;
    }
    .chat-input-wrap input:focus {
      border-color: #0ea5e9;
      background: #ffffff;
      box-shadow: 0 0 0 3px rgba(14, 165, 233, 0.1);
    }
    .chat-input-wrap input::placeholder { color: #94a3b8; }
    
    .send-btn {
      background: linear-gradient(135deg, #0ea5e9 0%, #0284c7 100%);
      color: #fff;
      border: none;
      border-radius: 50%;
      width: 48px;
      height: 48px;
      display: flex;
      justify-content: center;
      align-items: center;
      cursor: pointer;
      transition: transform 0.2s, box-shadow 0.2s;
      box-shadow: 0 4px 12px rgba(2, 132, 199, 0.2);
    }
    .send-btn:hover {
      transform: scale(1.05) rotate(-5deg);
      box-shadow: 0 6px 16px rgba(2, 132, 199, 0.3);
    }
    .send-btn:active { transform: scale(0.95); }
    .send-btn svg { width: 20px; height: 20px; margin-left: -2px; }
    
    .support-footer {
      font-size: 0.75rem;
      padding: 10px 16px;
      background: #f8fafc;
      border-top: 1px solid #f1f5f9;
      color: #64748b;
      text-align: center;
    }
    .support-footer a { color: #0284c7; text-decoration: none; font-weight: 600; transition: color 0.2s; }
    .support-footer a:hover { color: #f97316; }
  `;
"""

html_new = """
  const html = `
    <div class="chat-widget-container">
      <div id="chat-tooltip" class="chat-tooltip">Hey there I can help you</div>
      <button id="chat-toggle" class="chat-toggle" aria-label="Open Chat">
        <svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
          <path d="M12 2a2 2 0 0 1 2 2c0 .74-.4 1.39-1 1.73V7h1a7 7 0 0 1 7 7h1a1 1 0 0 1 1 1v3a1 1 0 0 1-1 1h-1v1a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2v-1H2a1 1 0 0 1-1-1v-3a1 1 0 0 1 1-1h1a7 7 0 0 1 7-7h1V5.73c-.6-.34-1-.99-1-1.73a2 2 0 0 1 2-2z"/>
          <path d="M9 14h.01"/>
          <path d="M15 14h.01"/>
          <path d="M10 18h4"/>
        </svg>
      </button>
    </div>
    <section id="chat-box" class="chat-box fyjc-chat-hidden">
      <div class="chat-header">
        <div class="chat-header-info">
          <strong>FYJC Assistant</strong>
          <div class="status-container">
            <span id="status-dot" class="status-indicator status-offline"></span>
            <span id="status-text" class="status-text">Connecting...</span>
          </div>
        </div>
        <div class="header-actions">
          <button id="clear-chat" class="header-btn" title="Clear Chat" aria-label="Clear Chat">
            <svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
              <polyline points="3 6 5 6 21 6"></polyline>
              <path d="M19 6v14a2 2 0 0 1-2 2H7a2 2 0 0 1-2-2V6m3 0V4a2 2 0 0 1 2-2h4a2 2 0 0 1 2 2v2"></path>
            </svg>
          </button>
          <button id="chat-close" class="header-btn" title="Close" aria-label="Close Chat">
            <svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
              <line x1="18" y1="6" x2="6" y2="18"></line>
              <line x1="6" y1="6" x2="18" y2="18"></line>
            </svg>
          </button>
        </div>
      </div>
      <div id="chat-messages" class="chat-messages"></div>
      <form id="chat-form" class="chat-input-wrap">
        <input id="chat-input" type="text" placeholder="Type your question..." required autocomplete="off" />
        <button type="submit" class="send-btn" aria-label="Send Message">
          <svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
            <line x1="22" y1="2" x2="11" y2="13"></line>
            <polygon points="22 2 15 22 11 13 2 9 22 2"></polygon>
          </svg>
        </button>
      </form>
      <div class="support-footer">
        Questions? Email: <a href="mailto:support@mahafyjcadmissions.in">support@mahafyjcadmissions.in</a>
      </div>
    </section>
  `;
"""

# Replace styles
content = re.sub(r'  const styles = `.*?  `;\n', styles_new + '\n', content, flags=re.DOTALL)
# Replace HTML
content = re.sub(r'  const html = `.*?  `;\n', html_new + '\n', content, flags=re.DOTALL)

# Replace typing indicator text with dots
content = content.replace("typingDiv.textContent = 'Typing...';", "typingDiv.innerHTML = '<div class=\"typing-dot\"></div><div class=\"typing-dot\"></div><div class=\"typing-dot\"></div>';")

# Add confirmation to clear-chat
old_clear = """    document.getElementById('clear-chat').addEventListener('click', () => {
      messages.innerHTML = '';
      chatHistory = [];
      sessionStorage.removeItem(CHAT_KEY);
      addMessage(config.welcomeMsg, 'bot-msg');
    });"""

new_clear = """    document.getElementById('clear-chat').addEventListener('click', () => {
      if (confirm('Are you sure you want to clear the chat history?')) {
        messages.innerHTML = '';
        chatHistory = [];
        sessionStorage.removeItem(CHAT_KEY);
        addMessage(config.welcomeMsg, 'bot-msg');
      }
    });"""

content = content.replace(old_clear, new_clear)

with open('static/widget.js', 'w') as f:
    f.write(content)
