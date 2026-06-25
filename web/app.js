// ============================================
// Kaysan AI — Web App (2026)
// ============================================

const API = '';

let chatHistory = [];
let conversations = [];
let currentConvId = null;
let personality = 'balanced';
let customPrompt = '';
let modelType = 'auto';
let lang = 'ku';
let voiceInputEnabled = false;
let voiceOutputEnabled = false;
let streamingEnabled = true;
let isRecording = false;
let recognition = null;

const TONE_LABELS = ['رک', 'ملایم', 'عادی', 'رسمی', 'پرانرژی'];
const VERBOSITY_LABELS = ['خیلی کوتاه', 'کوتاه', 'متعادل', 'مفصل'];
const HUMOR_LABELS = ['بدون', 'کم', 'متعادل', 'زیاد'];
const EMOJI_LABELS = ['بدون', 'کم', 'عادی', 'زیاد'];
const EMOTION_LABELS = ['آرام', 'عادی', 'گرم', 'پرانرژی'];

const PRESETS = {
  balanced:    { name: 'متعادل',     icon: '⚖️',  tone: 2, verbosity: 1, humor: 1, emoji: 1, emotion: 1 },
  blunt:       { name: 'رک و راست',  icon: '🔪',  tone: 0, verbosity: 0, humor: 0, emoji: 0, emotion: 0 },
  exaggerated: { name: 'اغراق‌آمیز', icon: '🎭',  tone: 4, verbosity: 3, humor: 3, emoji: 3, emotion: 3 },
  friendly:    { name: 'کاربرپسند',  icon: '🤗',  tone: 2, verbosity: 1, humor: 1, emoji: 1, emotion: 2 },
  professional:{ name: 'حرفه‌ای',    icon: '💼',  tone: 2, verbosity: 2, humor: 0, emoji: 0, emotion: 0 },
  sarcastic:   { name: 'کنایه‌آمیز', icon: '😏',  tone: 3, verbosity: 1, humor: 3, emoji: 0, emotion: 1 },
  caring:      { name: 'مهربان',     icon: '💕',  tone: 1, verbosity: 1, humor: 0, emoji: 1, emotion: 2 },
  technical:   { name: 'فنی',        icon: '🔧',  tone: 3, verbosity: 2, humor: 0, emoji: 0, emotion: 0 },
};

// ============================================
// Markdown Parser (simple, no deps)
// ============================================
function renderMarkdown(text) {
  if (!text) return '';
  let html = text
    .replace(/&/g, '&amp;')
    .replace(/</g, '&lt;')
    .replace(/>/g, '&gt;');

  html = html.replace(/```(\w*)\n([\s\S]*?)```/g, (_, lang, code) => {
    return `<pre><code class="lang-${lang || 'text'}">${code.trim()}</code></pre>`;
  });

  html = html.replace(/`([^`]+)`/g, '<code>$1</code>');
  html = html.replace(/\*\*(.+?)\*\*/g, '<strong>$1</strong>');
  html = html.replace(/\*(.+?)\*/g, '<em>$1</em>');
  html = html.replace(/^### (.+)$/gm, '<h3>$1</h3>');
  html = html.replace(/^## (.+)$/gm, '<h2>$1</h2>');
  html = html.replace(/^# (.+)$/gm, '<h1>$1</h1>');
  html = html.replace(/^> (.+)$/gm, '<blockquote>$1</blockquote>');
  html = html.replace(/^- (.+)$/gm, '<li>$1</li>');
  html = html.replace(/^(\d+)\. (.+)$/gm, '<li>$2</li>');

  html = html.replace(/(<li>.*<\/li>)/gs, (match) => {
    if (match.includes('<li>')) return '<ul>' + match + '</ul>';
    return match;
  });

  html = html.replace(/\[([^\]]+)\]\(([^)]+)\)/g, '<a href="$2" target="_blank" rel="noopener">$1</a>');

  html = html.replace(/\n/g, '<br>');

  return html;
}

// ============================================
// Init
// ============================================
document.addEventListener('DOMContentLoaded', () => {
  loadSettings();
  initSidebar();
  initHistoryPanel();
  initSettingsPanel();
  initChat();
  initTheme();
  initModelSelect();
  initVoice();
  initKeyboardShortcuts();
  updateBadge();
  detectSystemTheme();
  renderConversations();
});

function loadSettings() {
  try {
    const s = JSON.parse(localStorage.getItem('kay_settings') || '{}');
    personality = s.personality || 'balanced';
    customPrompt = s.customPrompt || '';
    modelType = s.modelType || 'auto';
    lang = s.lang || 'ku';
    voiceInputEnabled = s.voiceInputEnabled || false;
    voiceOutputEnabled = s.voiceOutputEnabled || false;
    streamingEnabled = s.streamingEnabled !== false;
    conversations = s.conversations || [];
    currentConvId = s.currentConvId || null;
    if (currentConvId) {
      const conv = conversations.find(c => c.id === currentConvId);
      if (conv) chatHistory = conv.messages;
    }
  } catch {}
}

function saveSettings() {
  if (currentConvId) {
    const conv = conversations.find(c => c.id === currentConvId);
    if (conv) {
      conv.messages = chatHistory;
      conv.updatedAt = Date.now();
    }
  }
  localStorage.setItem('kay_settings', JSON.stringify({
    personality, customPrompt, modelType, lang,
    voiceInputEnabled, voiceOutputEnabled, streamingEnabled,
    conversations, currentConvId,
  }));
}

function detectSystemTheme() {
  if (!localStorage.getItem('kay_theme')) {
    const prefersDark = window.matchMedia('(prefers-color-scheme: dark)').matches;
    applyTheme(prefersDark ? 'dark' : 'light');
  }
}

// ============================================
// Sidebar (Personality)
// ============================================
function initSidebar() {
  const panel = document.getElementById('personality-panel');
  const backdrop = document.getElementById('sidebar-backdrop');
  const toggleBtn = document.getElementById('personality-toggle');
  const closeBtn = document.getElementById('sidebar-close');
  const saveBtn = document.getElementById('save-btn');
  const resetBtn = document.getElementById('reset-btn');
  const presetList = document.getElementById('preset-list');

  function open() {
    closeAllSidebars();
    panel.classList.add('open');
    backdrop.classList.add('visible');
    syncSlidersToPreset(personality);
    document.getElementById('custom-prompt').value = customPrompt;
  }

  function close() {
    panel.classList.remove('open');
    backdrop.classList.remove('visible');
  }

  toggleBtn.onclick = open;
  closeBtn.onclick = close;
  backdrop.onclick = closeAllSidebars;

  Object.entries(PRESETS).forEach(([key, p]) => {
    const el = document.createElement('div');
    el.className = `preset-item${personality === key ? ' active' : ''}`;
    el.dataset.key = key;
    el.innerHTML = `<span class="preset-icon">${p.icon}</span><span class="preset-name">${p.name}</span>`;
    el.onclick = () => {
      personality = key;
      document.querySelectorAll('.preset-item').forEach(x => x.classList.remove('active'));
      el.classList.add('active');
      syncSlidersToPreset(key);
    };
    presetList.appendChild(el);
  });

  const sliders = [
    { id: 's-tone', labels: TONE_LABELS, valId: 'val-tone' },
    { id: 's-verbosity', labels: VERBOSITY_LABELS, valId: 'val-verbosity' },
    { id: 's-humor', labels: HUMOR_LABELS, valId: 'val-humor' },
    { id: 's-emoji', labels: EMOJI_LABELS, valId: 'val-emoji' },
    { id: 's-emotion', labels: EMOTION_LABELS, valId: 'val-emotion' },
  ];

  sliders.forEach(({ id, labels, valId }) => {
    const slider = document.getElementById(id);
    const valEl = document.getElementById(valId);
    slider.oninput = () => {
      valEl.textContent = labels[slider.value];
    };
  });

  saveBtn.onclick = () => {
    customPrompt = document.getElementById('custom-prompt').value;
    saveSettings();
    updateBadge();
    toast('تنظیمات ذخیره شد ✓');
    close();
  };

  resetBtn.onclick = () => {
    personality = 'balanced';
    customPrompt = '';
    syncSlidersToPreset('balanced');
    document.getElementById('custom-prompt').value = '';
    document.querySelectorAll('.preset-item').forEach(x => {
      x.classList.toggle('active', x.dataset.key === 'balanced');
    });
    toast('بازنشانی شد');
  };
}

function syncSlidersToPreset(key) {
  const p = PRESETS[key] || PRESETS.balanced;
  const map = {
    's-tone': { val: p.tone, labels: TONE_LABELS, valId: 'val-tone' },
    's-verbosity': { val: p.verbosity, labels: VERBOSITY_LABELS, valId: 'val-verbosity' },
    's-humor': { val: p.humor, labels: HUMOR_LABELS, valId: 'val-humor' },
    's-emoji': { val: p.emoji, labels: EMOJI_LABELS, valId: 'val-emoji' },
    's-emotion': { val: p.emotion, labels: EMOTION_LABELS, valId: 'val-emotion' },
  };
  Object.entries(map).forEach(([id, { val, labels, valId }]) => {
    document.getElementById(id).value = val;
    document.getElementById(valId).textContent = labels[val];
  });
}

function updateBadge() {
  const badge = document.getElementById('personality-badge');
  const p = PRESETS[personality] || PRESETS.balanced;
  badge.textContent = `${p.icon} ${p.name}`;
}

// ============================================
// History Panel
// ============================================
function initHistoryPanel() {
  const panel = document.getElementById('history-panel');
  const backdrop = document.getElementById('sidebar-backdrop');
  const toggleBtn = document.getElementById('history-btn');
  const closeBtn = document.getElementById('history-close');

  toggleBtn.onclick = () => {
    closeAllSidebars();
    renderConversations();
    panel.classList.add('open');
    backdrop.classList.add('visible');
  };

  closeBtn.onclick = () => {
    panel.classList.remove('open');
    backdrop.classList.remove('visible');
  };
}

function renderConversations() {
  const list = document.getElementById('conversations-list');
  list.innerHTML = '';

  if (conversations.length === 0) {
    list.innerHTML = '<p style="color:var(--c-text-3);text-align:center;padding:20px;font-size:13px;">هنوز مکالمه‌ای ندارید</p>';
    return;
  }

  const sorted = [...conversations].sort((a, b) => (b.updatedAt || b.createdAt) - (a.updatedAt || a.createdAt));

  sorted.forEach(conv => {
    const el = document.createElement('div');
    el.className = `conv-item${conv.id === currentConvId ? ' active' : ''}`;
    const firstMsg = conv.messages[0]?.content || 'مکالمه جدید';
    const title = firstMsg.substring(0, 40) + (firstMsg.length > 40 ? '...' : '');
    const date = new Date(conv.updatedAt || conv.createdAt).toLocaleDateString('fa-IR');
    el.innerHTML = `
      <span class="conv-icon">💬</span>
      <div class="conv-info">
        <div class="conv-title">${title}</div>
        <div class="conv-date">${date}</div>
      </div>
      <button class="conv-delete" data-id="${conv.id}" aria-label="حذف">✕</button>
    `;
    el.onclick = (e) => {
      if (e.target.closest('.conv-delete')) return;
      switchConversation(conv.id);
    };
    el.querySelector('.conv-delete').onclick = (e) => {
      e.stopPropagation();
      deleteConversation(conv.id);
    };
    list.appendChild(el);
  });
}

function newConversation() {
  currentConvId = 'conv_' + Date.now();
  chatHistory = [];
  conversations.push({
    id: currentConvId,
    messages: [],
    createdAt: Date.now(),
    updatedAt: Date.now(),
  });
  saveSettings();
  clearMessages();
  showWelcome();
  renderConversations();
  toast('مکالمه جدید ✨');
}

function switchConversation(id) {
  currentConvId = id;
  const conv = conversations.find(c => c.id === id);
  chatHistory = conv ? conv.messages : [];
  saveSettings();
  clearMessages();
  if (chatHistory.length > 0) {
    hideWelcome();
    chatHistory.forEach(m => addMsg(m.role, m.content, false));
    scrollToBottom();
  } else {
    showWelcome();
  }
  closeAllSidebars();
  renderConversations();
}

function deleteConversation(id) {
  conversations = conversations.filter(c => c.id !== id);
  if (currentConvId === id) {
    currentConvId = null;
    chatHistory = [];
    clearMessages();
    showWelcome();
  }
  saveSettings();
  renderConversations();
  toast('مکالمه حذف شد');
}

function clearAllConversations() {
  if (!confirm('آیا مطمئنید؟ همه مکالمات حذف خواهند شد.')) return;
  conversations = [];
  currentConvId = null;
  chatHistory = [];
  saveSettings();
  clearMessages();
  showWelcome();
  renderConversations();
  closeAllSidebars();
  toast('همه مکالمات حذف شد');
}

// ============================================
// Settings Panel
// ============================================
function initSettingsPanel() {
  const panel = document.getElementById('settings-panel');
  const backdrop = document.getElementById('sidebar-backdrop');
  const toggleBtn = document.getElementById('settings-btn');
  const closeBtn = document.getElementById('settings-close');

  toggleBtn.onclick = () => {
    closeAllSidebars();
    panel.classList.add('open');
    backdrop.classList.add('visible');
  };

  closeBtn.onclick = () => {
    panel.classList.remove('open');
    backdrop.classList.remove('visible');
  };

  document.querySelectorAll('.lang-btn').forEach(btn => {
    btn.classList.toggle('active', btn.dataset.lang === lang);
    btn.onclick = () => {
      lang = btn.dataset.lang;
      document.querySelectorAll('.lang-btn').forEach(b => b.classList.remove('active'));
      btn.classList.add('active');
      saveSettings();
      toast('زبان تغییر کرد');
    };
  });

  document.getElementById('voice-input-toggle').checked = voiceInputEnabled;
  document.getElementById('voice-output-toggle').checked = voiceOutputEnabled;
  document.getElementById('streaming-toggle').checked = streamingEnabled;

  document.getElementById('voice-input-toggle').onchange = (e) => {
    voiceInputEnabled = e.target.checked;
    saveSettings();
    updateVoiceBtn();
  };

  document.getElementById('voice-output-toggle').onchange = (e) => {
    voiceOutputEnabled = e.target.checked;
    saveSettings();
  };

  document.getElementById('streaming-toggle').onchange = (e) => {
    streamingEnabled = e.target.checked;
    saveSettings();
  };

  document.getElementById('clear-all-btn').onclick = clearAllConversations;
}

function closeAllSidebars() {
  document.getElementById('personality-panel').classList.remove('open');
  document.getElementById('history-panel').classList.remove('open');
  document.getElementById('settings-panel').classList.remove('open');
  document.getElementById('sidebar-backdrop').classList.remove('visible');
}

// ============================================
// Chat
// ============================================
function initChat() {
  const input = document.getElementById('msg-input');
  const sendBtn = document.getElementById('send-btn');

  input.addEventListener('input', () => {
    input.style.height = 'auto';
    input.style.height = Math.min(input.scrollHeight, 120) + 'px';
    sendBtn.disabled = !input.value.trim();
  });

  input.addEventListener('keydown', (e) => {
    if (e.key === 'Enter' && !e.shiftKey) {
      e.preventDefault();
      if (input.value.trim()) send();
    }
  });

  sendBtn.onclick = () => { if (input.value.trim()) send(); };

  document.querySelectorAll('.quick-card').forEach(btn => {
    btn.onclick = () => {
      input.value = btn.dataset.msg;
      input.dispatchEvent(new Event('input'));
      send();
    };
  });

  document.getElementById('new-chat-btn').onclick = newConversation;

  if (chatHistory.length > 0) {
    hideWelcome();
    chatHistory.forEach(m => addMsg(m.role, m.content, false));
    scrollToBottom();
  }

  async function send() {
    const text = input.value.trim();
    if (!text) return;

    input.value = '';
    input.style.height = 'auto';
    sendBtn.disabled = true;

    hideWelcome();
    addMsg('user', text);
    chatHistory.push({ role: 'user', content: text });

    if (!currentConvId) {
      currentConvId = 'conv_' + Date.now();
      conversations.push({
        id: currentConvId,
        messages: [],
        createdAt: Date.now(),
        updatedAt: Date.now(),
      });
    }

    showTyping();
    scrollToBottom();

    try {
      if (streamingEnabled) {
        await sendStreaming(text);
      } else {
        await sendRegular(text);
      }
    } catch {
      hideTyping();
      addMsg('bot', 'خطا در اتصال. دوباره تلاش کنید.');
    }

    saveSettings();
    scrollToBottom();
  }

  async function sendRegular(text) {
    const res = await fetch(`${API}/api/chat`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(buildPayload(text)),
    });

    const data = await res.json();
    hideTyping();

    if (data.error) {
      addMsg('bot', `خطا: ${data.error}`);
    } else {
      addMsg('bot', data.reply);
      chatHistory.push({ role: 'assistant', content: data.reply });
      if (voiceOutputEnabled) speak(data.reply);
    }
  }

  async function sendStreaming(text) {
    const res = await fetch(`${API}/api/chat/stream`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(buildPayload(text)),
    });

    if (!res.ok) {
      hideTyping();
      const data = await res.json().catch(() => ({}));
      addMsg('bot', `خطا: ${data.error || res.statusText}`);
      return;
    }

    const botMsgEl = createBotMsgElement();
    hideTyping();

    const reader = res.body.getReader();
    const decoder = new TextDecoder();
    let fullText = '';
    let buffer = '';

    while (true) {
      const { done, value } = await reader.read();
      if (done) break;

      buffer += decoder.decode(value, { stream: true });
      const lines = buffer.split('\n');
      buffer = lines.pop() || '';

      for (const line of lines) {
        if (!line.startsWith('data: ')) continue;
        const dataStr = line.slice(6);
        if (dataStr === '[DONE]') continue;

        try {
          const data = JSON.parse(dataStr);
          if (data.chunk) {
            fullText += data.chunk;
            botMsgEl.querySelector('.msg-content').innerHTML = renderMarkdown(fullText);
            scrollToBottom();
          }
          if (data.done) {
            chatHistory.push({ role: 'assistant', content: fullText });
            if (voiceOutputEnabled) speak(fullText);
          }
        } catch {}
      }
    }
  }

  function buildPayload(text) {
    const p = PRESETS[personality] || PRESETS.balanced;
    return {
      message: text,
      lang,
      history: chatHistory.slice(-10),
      model_type: modelType,
      personality,
      custom_prompt: customPrompt,
      tone: parseInt(document.getElementById('s-tone').value),
      verbosity: parseInt(document.getElementById('s-verbosity').value),
      humor: parseInt(document.getElementById('s-humor').value),
      emoji: parseInt(document.getElementById('s-emoji').value),
      emotion: parseInt(document.getElementById('s-emotion').value),
    };
  }
}

function addMsg(role, text, animate = true) {
  const container = document.getElementById('messages');
  const el = document.createElement('div');
  el.className = `msg ${role}`;
  if (!animate) el.style.animation = 'none';

  const avatar = document.createElement('div');
  avatar.className = 'msg-avatar';
  avatar.textContent = role === 'user' ? '👤' : '🧠';

  const body = document.createElement('div');
  body.className = 'msg-body';

  const content = document.createElement('div');
  content.className = 'msg-content';

  if (role === 'bot') {
    content.innerHTML = renderMarkdown(text);
  } else {
    content.textContent = text;
  }

  body.appendChild(content);

  if (role === 'bot') {
    const actions = document.createElement('div');
    actions.className = 'msg-actions';
    actions.innerHTML = `
      <button class="msg-action-btn copy-btn" title="کپی" aria-label="کپی">📋</button>
      <button class="msg-action-btn regenerate-btn" title="بازسازی" aria-label="بازسازی">🔄</button>
    `;
    actions.querySelector('.copy-btn').onclick = () => {
      navigator.clipboard.writeText(text).then(() => toast('کپی شد ✓'));
    };
    actions.querySelector('.regenerate-btn').onclick = () => regenerateLast();
    body.appendChild(actions);
  }

  el.appendChild(avatar);
  el.appendChild(body);
  container.appendChild(el);
}

function createBotMsgElement() {
  const container = document.getElementById('messages');
  const el = document.createElement('div');
  el.className = 'msg bot';

  const avatar = document.createElement('div');
  avatar.className = 'msg-avatar';
  avatar.textContent = '🧠';

  const body = document.createElement('div');
  body.className = 'msg-body';

  const content = document.createElement('div');
  content.className = 'msg-content';
  content.textContent = '...';

  body.appendChild(content);
  el.appendChild(avatar);
  el.appendChild(body);
  container.appendChild(el);

  return el;
}

async function regenerateLast() {
  if (chatHistory.length < 2) return;

  const lastUserMsg = chatHistory[chatHistory.length - 2];
  if (!lastUserMsg || lastUserMsg.role !== 'user') return;

  chatHistory.pop();
  const container = document.getElementById('messages');
  const lastBot = container.querySelector('.msg.bot:last-of-type');
  if (lastBot) lastBot.remove();

  showTyping();
  scrollToBottom();

  try {
    const res = await fetch(`${API}/api/chat`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({
        message: lastUserMsg.content,
        lang,
        history: chatHistory.slice(-10),
        model_type: modelType,
        personality,
        custom_prompt: customPrompt,
      }),
    });
    const data = await res.json();
    hideTyping();

    if (data.error) {
      addMsg('bot', `خطا: ${data.error}`);
    } else {
      addMsg('bot', data.reply);
      chatHistory.push({ role: 'assistant', content: data.reply });
    }
    saveSettings();
    scrollToBottom();
  } catch {
    hideTyping();
    addMsg('bot', 'خطا در بازسازی پاسخ.');
  }
}

function clearMessages() {
  document.getElementById('messages').innerHTML = '';
}

function showWelcome() {
  document.getElementById('welcome-screen').classList.remove('hidden');
}

function hideWelcome() {
  document.getElementById('welcome-screen').classList.add('hidden');
}

function showTyping() {
  document.getElementById('typing-indicator').classList.remove('hidden');
}

function hideTyping() {
  document.getElementById('typing-indicator').classList.add('hidden');
}

function scrollToBottom() {
  const area = document.getElementById('chat-area');
  requestAnimationFrame(() => {
    area.scrollTop = area.scrollHeight;
  });
}

// ============================================
// Theme
// ============================================
function initTheme() {
  const saved = localStorage.getItem('kay_theme') || 'dark';
  applyTheme(saved);

  document.getElementById('theme-toggle').onclick = () => {
    const current = document.body.classList.contains('light') ? 'light' : 'dark';
    const next = current === 'dark' ? 'light' : 'dark';
    applyTheme(next);
    localStorage.setItem('kay_theme', next);
  };
}

function applyTheme(theme) {
  document.body.classList.toggle('light', theme === 'light');
  document.getElementById('theme-icon').textContent = theme === 'dark' ? '🌙' : '☀️';
}

// ============================================
// Model
// ============================================
function initModelSelect() {
  const sel = document.getElementById('model-select');
  sel.value = modelType;
  sel.onchange = () => {
    modelType = sel.value;
    saveSettings();
  };
}

// ============================================
// Voice
// ============================================
function initVoice() {
  const voiceBtn = document.getElementById('voice-btn');
  updateVoiceBtn();

  voiceBtn.onclick = () => {
    if (!voiceInputEnabled) {
      toast('ورودی صوتی غیرفعال است. از تنظیمات فعال کنید.');
      return;
    }
    toggleRecording();
  };

  if ('webkitSpeechRecognition' in window || 'SpeechRecognition' in window) {
    const SpeechRecognition = window.SpeechRecognition || window.webkitSpeechRecognition;
    recognition = new SpeechRecognition();
    recognition.continuous = false;
    recognition.interimResults = false;
    recognition.lang = lang === 'ku' ? 'ar-IQ' : lang === 'fa' ? 'fa-IR' : 'en-US';

    recognition.onresult = (event) => {
      const text = event.results[0][0].transcript;
      document.getElementById('msg-input').value = text;
      document.getElementById('msg-input').dispatchEvent(new Event('input'));
    };

    recognition.onend = () => {
      isRecording = false;
      document.getElementById('voice-btn').classList.remove('recording');
    };

    recognition.onerror = () => {
      isRecording = false;
      document.getElementById('voice-btn').classList.remove('recording');
    };
  }
}

function updateVoiceBtn() {
  const voiceBtn = document.getElementById('voice-btn');
  voiceBtn.style.display = voiceInputEnabled ? 'flex' : 'none';
}

function toggleRecording() {
  if (!recognition) {
    toast('مرورگر شما از تبدیل گفتار پشتیبانی نمی‌کند.');
    return;
  }

  if (isRecording) {
    recognition.stop();
    isRecording = false;
    document.getElementById('voice-btn').classList.remove('recording');
  } else {
    recognition.lang = lang === 'ku' ? 'ar-IQ' : lang === 'fa' ? 'fa-IR' : 'en-US';
    recognition.start();
    isRecording = true;
    document.getElementById('voice-btn').classList.add('recording');
  }
}

function speak(text) {
  if (!voiceOutputEnabled || !('speechSynthesis' in window)) return;
  window.speechSynthesis.cancel();
  const utterance = new SpeechSynthesisUtterance(text.replace(/[#*_`>\[\]]/g, ''));
  utterance.lang = lang === 'ku' ? 'ar-IQ' : lang === 'fa' ? 'fa-IR' : 'en-US';
  utterance.rate = 1;
  window.speechSynthesis.speak(utterance);
}

// ============================================
// Keyboard Shortcuts
// ============================================
function initKeyboardShortcuts() {
  const overlay = document.getElementById('keyboard-shortcuts');

  document.addEventListener('keydown', (e) => {
    if (e.key === 'Escape') {
      closeAllSidebars();
      overlay.classList.add('hidden');
    }

    if (e.ctrlKey || e.metaKey) {
      if (e.key === 'k') {
        e.preventDefault();
        document.getElementById('msg-input').focus();
      }
      if (e.key === '/') {
        e.preventDefault();
        overlay.classList.toggle('hidden');
      }
      if (e.key === 'n') {
        e.preventDefault();
        newConversation();
      }
      if (e.shiftKey && e.key === 'C') {
        e.preventDefault();
        copyLastBotMessage();
      }
    }
  });

  document.getElementById('close-shortcuts').onclick = () => {
    overlay.classList.add('hidden');
  };

  overlay.onclick = (e) => {
    if (e.target === overlay) overlay.classList.add('hidden');
  };
}

function copyLastBotMessage() {
  const msgs = document.querySelectorAll('.msg.bot .msg-content');
  if (msgs.length === 0) {
    toast('پاسخی برای کپی وجود ندارد');
    return;
  }
  const last = msgs[msgs.length - 1];
  navigator.clipboard.writeText(last.textContent).then(() => toast('آخرین پاسخ کپی شد ✓'));
}

// ============================================
// Toast
// ============================================
function toast(msg, isError = false) {
  const el = document.getElementById('toast');
  el.textContent = msg;
  el.className = isError ? 'toast error' : 'toast';
  el.classList.remove('hidden');
  requestAnimationFrame(() => el.classList.add('show'));
  setTimeout(() => {
    el.classList.remove('show');
    setTimeout(() => el.classList.add('hidden'), 300);
  }, 2000);
}
