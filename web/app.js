// ============================================
// Kaysan AI — Web App v3.2 (2026)
// All issues fixed
// ============================================

const API = '';
let tg = null;
let tgUser = null;

// ============================================
// Telegram Mini App Detection
// ============================================
function initTelegram() {
  if (window.Telegram && window.Telegram.WebApp) {
    tg = window.Telegram.WebApp;
    tg.ready();
    tg.expand();
    tg.enableClosingConfirmation();

    if (tg.initDataUnsafe && tg.initDataUnsafe.user) {
      tgUser = tg.initDataUnsafe.user;
      applyTelegramTheme();
      verifyAndGreet();
    } else if (tg.initData) {
      fetch(`${API}/api/verify-user`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ init_data: tg.initData })
      }).then(r => r.json()).then(data => {
        if (data.ok) {
          tgUser = data.user;
          applyTelegramTheme();
          verifyAndGreet();
        }
      }).catch(() => {});
    }

    if (tg.colorScheme === 'dark') {
      document.documentElement.setAttribute('data-theme', 'dark');
    } else {
      document.documentElement.setAttribute('data-theme', 'light');
    }

    tg.MainButton.hide();
    tg.BackButton.onClick(() => tg.close());
  }
}

function applyTelegramTheme() {
  if (!tg) return;
  const colors = tg.themeParams;
  if (colors) {
    const root = document.documentElement;
    if (colors.bg_color) root.style.setProperty('--bg-primary', colors.bg_color);
    if (colors.secondary_bg_color) root.style.setProperty('--bg-secondary', colors.secondary_bg_color);
    if (colors.text_color) root.style.setProperty('--text-primary', colors.text_color);
    if (colors.hint_color) root.style.setProperty('--text-secondary', colors.hint_color);
    if (colors.button_color) root.style.setProperty('--accent', colors.button_color);
  }
}

function verifyAndGreet() {
  if (!tgUser) return;
  const name = tgUser.first_name || tgUser.username || 'کاربر';
  const greetEl = document.getElementById('user-greeting');
  const welcomeName = document.getElementById('welcome-name');
  if (greetEl) greetEl.textContent = `سلام ${name}`;
  if (welcomeName) welcomeName.textContent = name;
}

// ============================================
// State
// ============================================
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
let particlesEnabled = true;
let soundsEnabled = true;
let isRecording = false;
let mediaRecorder = null;
let audioChunks = [];
let voiceTimer = null;
let voiceSeconds = 0;

const PRESETS = {
  balanced:    { name: 'متعادل',     icon: '⚖️' },
  blunt:       { name: 'رک و راست',  icon: '🔪' },
  exaggerated: { name: 'اغراق‌آمیز', icon: '🎭' },
  friendly:    { name: 'کاربرپسند',  icon: '🤗' },
  professional:{ name: 'حرفه‌ای',    icon: '💼' },
  sarcastic:   { name: 'کنایه‌آمیز', icon: '😏' },
  caring:      { name: 'مهربان',     icon: '💕' },
  technical:   { name: 'فنی',        icon: '🔧' },
};

const EMOJIS = ['😀','😂','😍','🥰','😎','🤩','😭','🤔','😱','🥳','😴','🙄','👍','👎','❤️','🔥','⭐','🎉','💯','🙏','👋','💪','✌️','🤝','👀','💡','🚀','✨','🎯','🎨','💻','🤖','🧠','📚','🎵','🌙','☀️','🌈','🍕','☕','🎮','⚽','🏆','📷','✈️','🌍','📱','🔮','💎','🌟'];

// ============================================
// Markdown Parser (XSS-safe)
// ============================================
function renderMarkdown(text) {
  if (!text) return '';
  let html = text.replace(/&/g, '&amp;').replace(/</g, '&lt;').replace(/>/g, '&gt;');

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

  html = html.replace(/\[([^\]]+)\]\(([^)]+)\)/g, (match, text, url) => {
    if (url.startsWith('javascript:') || url.startsWith('data:')) return match;
    return `<a href="${url}" target="_blank" rel="noopener">${text}</a>`;
  });

  html = html.replace(/\n/g, '<br>');
  return html;
}

// ============================================
// Particles
// ============================================
let particleAnimFrame = null;

function initParticles() {
  const canvas = document.getElementById('particles');
  if (!canvas) return;
  const ctx = canvas.getContext('2d');
  const particles = [];

  function resize() {
    canvas.width = window.innerWidth;
    canvas.height = window.innerHeight;
  }
  resize();
  window.addEventListener('resize', resize);

  class Particle {
    constructor() { this.reset(); }
    reset() {
      this.x = Math.random() * canvas.width;
      this.y = Math.random() * canvas.height;
      this.size = Math.random() * 2 + 0.5;
      this.speedX = (Math.random() - 0.5) * 0.5;
      this.speedY = (Math.random() - 0.5) * 0.5;
      this.opacity = Math.random() * 0.5 + 0.1;
    }
    update() {
      this.x += this.speedX;
      this.y += this.speedY;
      if (this.x < 0 || this.x > canvas.width || this.y < 0 || this.y > canvas.height) this.reset();
    }
    draw() {
      ctx.beginPath();
      ctx.arc(this.x, this.y, this.size, 0, Math.PI * 2);
      ctx.fillStyle = `rgba(129, 140, 248, ${this.opacity})`;
      ctx.fill();
    }
  }

  for (let i = 0; i < 50; i++) particles.push(new Particle());

  function animate() {
    ctx.clearRect(0, 0, canvas.width, canvas.height);
    particles.forEach(p => { p.update(); p.draw(); });
    for (let i = 0; i < particles.length; i++) {
      for (let j = i + 1; j < particles.length; j++) {
        const dx = particles[i].x - particles[j].x;
        const dy = particles[i].y - particles[j].y;
        const dist = Math.sqrt(dx * dx + dy * dy);
        if (dist < 120) {
          ctx.beginPath();
          ctx.moveTo(particles[i].x, particles[i].y);
          ctx.lineTo(particles[j].x, particles[j].y);
          ctx.strokeStyle = `rgba(129, 140, 248, ${0.1 * (1 - dist / 120)})`;
          ctx.stroke();
        }
      }
    }
    particleAnimFrame = requestAnimationFrame(animate);
  }

  if (particlesEnabled) animate();

  window.toggleParticles = (on) => {
    particlesEnabled = on;
    if (on) { if (!particleAnimFrame) animate(); }
    else { cancelAnimationFrame(particleAnimFrame); particleAnimFrame = null; }
  };
}

// ============================================
// Sound Effects (shared AudioContext)
// ============================================
let _audioCtx = null;
function getAudioCtx() {
  if (!_audioCtx || _audioCtx.state === 'closed') {
    _audioCtx = new (window.AudioContext || window.webkitAudioContext)();
  }
  return _audioCtx;
}

function playSound(type) {
  if (!soundsEnabled) return;
  try {
    const ctx = getAudioCtx();
    const osc = ctx.createOscillator();
    const gain = ctx.createGain();
    osc.connect(gain);
    gain.connect(ctx.destination);
    gain.gain.value = 0.1;
    if (type === 'send') { osc.frequency.value = 800; osc.type = 'sine'; }
    else if (type === 'receive') { osc.frequency.value = 600; osc.type = 'sine'; }
    else if (type === 'error') { osc.frequency.value = 200; osc.type = 'sawtooth'; }
    gain.gain.exponentialRampToValueAtTime(0.001, ctx.currentTime + 0.15);
    osc.start(ctx.currentTime);
    osc.stop(ctx.currentTime + 0.15);
  } catch (e) {}
}

// ============================================
// Toast
// ============================================
function showToast(msg, duration = 3000) {
  const t = document.getElementById('toast');
  if (!t) return;
  t.textContent = msg;
  t.classList.remove('hidden');
  t.classList.add('show');
  setTimeout(() => { t.classList.remove('show'); t.classList.add('hidden'); }, duration);
}

// ============================================
// Settings
// ============================================
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
    particlesEnabled = s.particlesEnabled !== false;
    soundsEnabled = s.soundsEnabled !== false;
  } catch (e) {}
}

function saveSettings() {
  localStorage.setItem('kay_settings', JSON.stringify({
    personality, customPrompt, modelType, lang,
    voiceInputEnabled, voiceOutputEnabled, streamingEnabled,
    particlesEnabled, soundsEnabled,
  }));
}

// ============================================
// Conversations
// ============================================
function loadConversations() {
  try { conversations = JSON.parse(localStorage.getItem('kay_conversations') || '[]'); }
  catch (e) { conversations = []; }
}

function saveConversations() {
  localStorage.setItem('kay_conversations', JSON.stringify(conversations));
}

function newConversation() {
  currentConvId = Date.now().toString();
  chatHistory = [];
  conversations.unshift({ id: currentConvId, title: 'مکالمه جدید', messages: [], time: new Date().toISOString() });
  saveConversations();
  renderConversations();
  showWelcome();
}

function renderConversations() {
  const list = document.getElementById('conversations-list');
  if (!list) return;
  if (conversations.length === 0) {
    list.innerHTML = '<div class="conv-empty">هنوز مکالمه‌ای ندارید</div>';
    return;
  }
  list.innerHTML = conversations.map(c => `
    <div class="conv-item ${c.id === currentConvId ? 'active' : ''}" data-id="${c.id}">
      <div class="conv-title">${c.title}</div>
      <div class="conv-time">${new Date(c.time).toLocaleDateString('fa')}</div>
    </div>
  `).join('');

  list.querySelectorAll('.conv-item').forEach(el => {
    el.addEventListener('click', () => {
      const conv = conversations.find(c => c.id === el.dataset.id);
      if (conv) {
        currentConvId = conv.id;
        chatHistory = conv.messages || [];
        renderMessages();
        closeAllSidebars();
      }
    });
  });
}

function renderMessages() {
  const mg = document.getElementById('messages');
  if (!mg) return;
  mg.innerHTML = '';
  if (chatHistory.length === 0) { showWelcome(); return; }
  hideWelcome();
  chatHistory.forEach(msg => {
    addMessage(msg.role === 'assistant' ? 'bot' : 'user', msg.content);
  });
}

// ============================================
// Messages
// ============================================
function showWelcome() {
  const ws = document.getElementById('welcome-screen');
  const mg = document.getElementById('messages');
  if (ws) ws.style.display = 'flex';
  if (mg) mg.innerHTML = '';
}

function hideWelcome() {
  const ws = document.getElementById('welcome-screen');
  if (ws) ws.style.display = 'none';
}

function addMessage(role, content, streaming = false) {
  hideWelcome();
  const messages = document.getElementById('messages');
  if (!messages) return null;
  const id = 'msg-' + Date.now() + '-' + Math.random().toString(36).slice(2, 6);
  const time = new Date().toLocaleTimeString('fa', { hour: '2-digit', minute: '2-digit' });
  const avatar = role === 'bot' ? '<img src="/logo.png" alt="Kaysan">' : (tgUser && tgUser.photo_url ? `<img src="${tgUser.photo_url}" alt="User">` : '👤');

  const html = `
    <div class="msg ${role}" id="${id}">
      <div class="msg-avatar">${avatar}</div>
      <div>
        <div class="msg-bubble">${streaming ? '<div class="streaming-text"></div>' : renderMarkdown(content)}</div>
        <div class="msg-time">${time}</div>
        <div class="msg-actions">
          <button class="msg-action" data-action="copy" data-target="${id}">📋 کپی</button>
          <button class="msg-action" data-action="speak" data-target="${id}">🔊 صدا</button>
        </div>
      </div>
    </div>
  `;
  messages.insertAdjacentHTML('beforeend', html);
  messages.scrollTop = messages.scrollHeight;

  const msgEl = document.getElementById(id);
  if (msgEl) {
    msgEl.querySelectorAll('.msg-action').forEach(btn => {
      btn.addEventListener('click', () => {
        if (btn.dataset.action === 'copy') copyMessage(btn.dataset.target);
        if (btn.dataset.action === 'speak') speakMessage(btn.dataset.target);
      });
    });
  }
  return id;
}

function updateStreamingMessage(id, text) {
  const el = document.querySelector(`#${id} .streaming-text`);
  if (el) el.innerHTML = renderMarkdown(text);
  const msgs = document.getElementById('messages');
  if (msgs) msgs.scrollTop = msgs.scrollHeight;
}

function copyMessage(id) {
  const el = document.querySelector(`#${id} .msg-bubble`);
  if (el) {
    navigator.clipboard.writeText(el.textContent);
    showToast('کپی شد!');
  }
}

function speakMessage(id) {
  const el = document.querySelector(`#${id} .msg-bubble`);
  if (el && 'speechSynthesis' in window) {
    const utter = new SpeechSynthesisUtterance(el.textContent);
    utter.lang = lang === 'ku' ? 'ckb' : lang === 'fa' ? 'fa' : 'en';
    speechSynthesis.speak(utter);
  }
}

// ============================================
// Chat
// ============================================
async function sendMessage(text) {
  if (!text.trim()) return;
  playSound('send');

  addMessage('user', text);
  chatHistory.push({ role: 'user', content: text });

  const input = document.getElementById('msg-input');
  if (input) { input.value = ''; input.style.height = 'auto'; }
  document.getElementById('send-btn').disabled = true;

  const typing = document.getElementById('typing-indicator');
  if (typing) typing.classList.remove('hidden');

  try {
    const body = {
      message: text,
      model_type: modelType,
      personality: personality,
      custom_prompt: customPrompt,
      stream: streamingEnabled,
    };
    if (tg && tg.initData) body.init_data = tg.initData;

    const msgId = addMessage('bot', '', true);

    if (streamingEnabled) {
      const res = await fetch(`${API}/api/chat`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(body),
      });

      if (!res.ok) {
        const err = await res.json().catch(() => ({}));
        throw new Error(err.error || 'Request failed');
      }

      const reader = res.body.getReader();
      const decoder = new TextDecoder();
      let full = '';

      while (true) {
        const { done, value } = await reader.read();
        if (done) break;
        const chunk = decoder.decode(value);
        const lines = chunk.split('\n');
        for (const line of lines) {
          if (line.startsWith('data: ')) {
            try {
              const data = JSON.parse(line.slice(6));
              if (data.error) throw new Error(data.error);
              if (data.done) break;
              full += data.text;
              updateStreamingMessage(msgId, full);
            } catch (e) {
              if (e.message !== 'Unexpected end of JSON input') throw e;
            }
          }
        }
      }

      chatHistory.push({ role: 'assistant', content: full });
    } else {
      const res = await fetch(`${API}/api/chat`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(body),
      });

      if (!res.ok) {
        const err = await res.json().catch(() => ({}));
        throw new Error(err.error || 'Request failed');
      }

      const data = await res.json();
      const bubble = document.querySelector(`#${msgId} .msg-bubble`);
      if (bubble) bubble.innerHTML = renderMarkdown(data.response);
      chatHistory.push({ role: 'assistant', content: data.response });
    }

    playSound('receive');
  } catch (e) {
    playSound('error');
    showToast(`خطا: ${e.message}`);
  } finally {
    if (typing) typing.classList.add('hidden');
    if (currentConvId) {
      const conv = conversations.find(c => c.id === currentConvId);
      if (conv) {
        conv.messages = chatHistory;
        if (chatHistory.length === 1) conv.title = text.substring(0, 30);
        saveConversations();
      }
    }
  }
}

// ============================================
// Voice Input (actually sends audio)
// ============================================
function initVoice() {
  const voiceBtn = document.getElementById('voice-btn');
  if (!voiceBtn) return;

  voiceBtn.addEventListener('click', () => {
    if (isRecording) stopRecording();
    else startRecording();
  });
}

function startRecording() {
  if (!('MediaRecorder' in window)) { showToast('ورودی صوتی پشتیبانی نمی‌شود'); return; }

  navigator.mediaDevices.getUserMedia({ audio: true }).then(stream => {
    isRecording = true;
    audioChunks = [];
    voiceSeconds = 0;

    const mimeType = MediaRecorder.isTypeSupported('audio/webm;codecs=opus') ? 'audio/webm;codecs=opus' : 'audio/webm';
    mediaRecorder = new MediaRecorder(stream, { mimeType });

    mediaRecorder.ondataavailable = e => {
      if (e.data.size > 0) audioChunks.push(e.data);
    };
    mediaRecorder.onstop = () => {
      stream.getTracks().forEach(t => t.stop());
      isRecording = false;
      document.getElementById('voice-btn')?.classList.remove('recording');
    };

    mediaRecorder.start();
    document.getElementById('voice-btn')?.classList.add('recording');

    const overlay = document.getElementById('voice-overlay');
    if (overlay) overlay.classList.remove('hidden');

    const waveform = document.getElementById('voice-waveform');
    if (waveform) {
      waveform.innerHTML = Array(20).fill(0).map((_, i) =>
        `<div class="bar" style="animation-delay:${i * 0.05}s"></div>`
      ).join('');
    }

    voiceTimer = setInterval(() => {
      voiceSeconds++;
      const m = Math.floor(voiceSeconds / 60).toString().padStart(2, '0');
      const s = (voiceSeconds % 60).toString().padStart(2, '0');
      const timerEl = document.getElementById('voice-timer');
      if (timerEl) timerEl.textContent = `${m}:${s}`;
    }, 1000);
  }).catch(() => showToast('اجازه دسترسی به میکروفون داده نشد'));
}

function stopRecording() {
  if (mediaRecorder && mediaRecorder.state !== 'inactive') {
    mediaRecorder.stop();
  }
  clearInterval(voiceTimer);
  const overlay = document.getElementById('voice-overlay');
  if (overlay) overlay.classList.add('hidden');
}

async function sendVoiceMessage() {
  if (audioChunks.length === 0) { stopRecording(); return; }

  const blob = new Blob(audioChunks, { type: mediaRecorder?.mimeType || 'audio/webm' });
  stopRecording();

  const typing = document.getElementById('typing-indicator');
  if (typing) typing.classList.remove('hidden');

  try {
    const formData = new FormData();
    formData.append('audio', blob, 'voice.webm');

    const res = await fetch(`${API}/api/voice`, {
      method: 'POST',
      body: formData,
    });

    if (!res.ok) {
      const err = await res.json().catch(() => ({}));
      throw new Error(err.error || 'Voice processing failed');
    }

    const data = await res.json();
    if (data.text) {
      showToast(`متن: ${data.text.substring(0, 50)}...`);
      sendMessage(data.text);
    }
  } catch (e) {
    showToast(`خطا در پردازش صدا: ${e.message}`);
  } finally {
    if (typing) typing.classList.add('hidden');
  }
}

// ============================================
// Image Generation
// ============================================
async function generateImage() {
  const input = document.getElementById('msg-input');
  const prompt = input?.value?.trim();
  if (!prompt) { showToast('لطفاً توضیح تصویر را بنویسید'); return; }

  input.value = '';
  document.getElementById('send-btn').disabled = true;

  const typing = document.getElementById('typing-indicator');
  if (typing) typing.classList.remove('hidden');

  try {
    const res = await fetch(`${API}/api/image`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ prompt }),
    });

    if (!res.ok) {
      const err = await res.json().catch(() => ({}));
      throw new Error(err.error || 'Image generation failed');
    }

    const data = await res.json();
    if (data.url) {
      addMessage('bot', `![${prompt}](${data.url})`);
    }
  } catch (e) {
    showToast(`خطا: ${e.message}`);
  } finally {
    if (typing) typing.classList.add('hidden');
  }
}

// ============================================
// Emoji Picker
// ============================================
function initEmojiPicker() {
  const btn = document.getElementById('emoji-btn');
  const picker = document.getElementById('emoji-picker');
  const grid = document.getElementById('emoji-grid');
  const search = document.getElementById('emoji-search-input');
  const input = document.getElementById('msg-input');

  if (!btn || !picker || !grid) return;

  function renderEmojis(filter = '') {
    const filtered = EMOJIS.filter(e => !filter || e.includes(filter));
    grid.innerHTML = filtered.map(e => `<div class="emoji-item" data-emoji="${e}">${e}</div>`).join('');
    grid.querySelectorAll('.emoji-item').forEach(el => {
      el.addEventListener('click', () => {
        input.value += el.dataset.emoji;
        input.focus();
        picker.classList.add('hidden');
      });
    });
  }

  renderEmojis();
  btn.addEventListener('click', (e) => {
    e.stopPropagation();
    picker.classList.toggle('hidden');
  });
  if (search) search.addEventListener('input', () => renderEmojis(search.value));
  document.addEventListener('click', (e) => {
    if (!picker.contains(e.target) && e.target !== btn) picker.classList.add('hidden');
  });
}

// ============================================
// Theme
// ============================================
function initTheme() {
  const toggle = document.getElementById('theme-toggle');
  if (!toggle) return;
  toggle.addEventListener('click', () => {
    const current = document.documentElement.getAttribute('data-theme');
    const next = current === 'dark' ? 'light' : 'dark';
    document.documentElement.setAttribute('data-theme', next);
    localStorage.setItem('kay_theme', next);
    if (tg) tg.switchHeaderTheme(next);
  });
  const saved = localStorage.getItem('kay_theme');
  if (saved) document.documentElement.setAttribute('data-theme', saved);
}

// ============================================
// Init
// ============================================
document.addEventListener('DOMContentLoaded', () => {
  initTelegram();
  loadSettings();
  loadConversations();
  initParticles();
  initTheme();
  initVoice();
  initEmojiPicker();

  setTimeout(() => {
    const ls = document.getElementById('loading-screen');
    if (ls) ls.classList.add('hidden');
  }, 1500);

  renderConversations();
  verifyAndGreet();

  const input = document.getElementById('msg-input');
  const sendBtn = document.getElementById('send-btn');

  if (input) {
    input.addEventListener('input', () => {
      input.style.height = 'auto';
      input.style.height = Math.min(input.scrollHeight, 120) + 'px';
      sendBtn.disabled = !input.value.trim();
    });
    input.addEventListener('keydown', (e) => {
      if (e.key === 'Enter' && !e.shiftKey) {
        e.preventDefault();
        if (input.value.trim()) sendMessage(input.value);
      }
    });
  }

  if (sendBtn) sendBtn.addEventListener('click', () => {
    if (input.value.trim()) sendMessage(input.value);
  });

  document.querySelectorAll('.quick-card').forEach(btn => {
    btn.addEventListener('click', () => sendMessage(btn.dataset.msg));
  });

  document.getElementById('new-chat-btn')?.addEventListener('click', newConversation);
  document.getElementById('history-btn')?.addEventListener('click', () => {
    document.getElementById('history-panel')?.classList.toggle('open');
    document.getElementById('sidebar-backdrop')?.classList.toggle('active');
  });
  document.getElementById('personality-toggle')?.addEventListener('click', () => {
    document.getElementById('personality-panel')?.classList.toggle('open');
    document.getElementById('sidebar-backdrop')?.classList.toggle('active');
  });
  document.getElementById('settings-btn')?.addEventListener('click', () => {
    document.getElementById('settings-panel')?.classList.toggle('open');
    document.getElementById('sidebar-backdrop')?.classList.toggle('active');
  });

  document.querySelectorAll('.sidebar-close, #history-close, #settings-close').forEach(btn => {
    btn?.addEventListener('click', closeAllSidebars);
  });
  document.getElementById('sidebar-backdrop')?.addEventListener('click', closeAllSidebars);

  document.querySelectorAll('.lang-btn').forEach(btn => {
    btn.addEventListener('click', () => {
      document.querySelectorAll('.lang-btn').forEach(b => b.classList.remove('active'));
      btn.classList.add('active');
      lang = btn.dataset.lang;
      saveSettings();
    });
  });

  document.getElementById('save-btn')?.addEventListener('click', () => {
    customPrompt = document.getElementById('custom-prompt')?.value || '';
    saveSettings();
    showToast('تنظیمات ذخیره شد!');
    closeAllSidebars();
  });

  document.getElementById('reset-btn')?.addEventListener('click', () => {
    personality = 'balanced';
    customPrompt = '';
    saveSettings();
    showToast('بازنشانی شد');
  });

  document.getElementById('clear-all-btn')?.addEventListener('click', () => {
    if (confirm('همه مکالمات پاک شوند؟')) {
      conversations = [];
      saveConversations();
      newConversation();
      showToast('پاک شد');
    }
  });

  document.getElementById('voice-cancel')?.addEventListener('click', stopRecording);
  document.getElementById('voice-send')?.addEventListener('click', sendVoiceMessage);

  document.getElementById('image-btn')?.addEventListener('click', generateImage);

  document.getElementById('model-select')?.addEventListener('change', (e) => {
    modelType = e.target.value;
    saveSettings();
  });

  document.getElementById('streaming-toggle')?.addEventListener('change', (e) => {
    streamingEnabled = e.target.checked;
    saveSettings();
  });

  document.getElementById('voice-input-toggle')?.addEventListener('change', (e) => {
    voiceInputEnabled = e.target.checked;
    saveSettings();
  });

  document.getElementById('voice-output-toggle')?.addEventListener('change', (e) => {
    voiceOutputEnabled = e.target.checked;
    saveSettings();
  });

  document.getElementById('particles-toggle')?.addEventListener('change', (e) => {
    particlesEnabled = e.target.checked;
    saveSettings();
    if (window.toggleParticles) window.toggleParticles(particlesEnabled);
  });

  document.getElementById('sounds-toggle')?.addEventListener('change', (e) => {
    soundsEnabled = e.target.checked;
    saveSettings();
  });

  const presetList = document.getElementById('preset-list');
  if (presetList) {
    presetList.innerHTML = Object.entries(PRESETS).map(([key, p]) => `
      <div class="preset-card ${personality === key ? 'active' : ''}" data-preset="${key}">
        <div class="preset-icon">${p.icon}</div>
        <div class="preset-name">${p.name}</div>
      </div>
    `).join('');
    presetList.querySelectorAll('.preset-card').forEach(card => {
      card.addEventListener('click', () => {
        presetList.querySelectorAll('.preset-card').forEach(c => c.classList.remove('active'));
        card.classList.add('active');
        personality = card.dataset.preset;
        saveSettings();
        showToast(`شخصیت: ${PRESETS[personality].name}`);
      });
    });
  }

  const badge = document.getElementById('personality-badge');
  if (badge && PRESETS[personality]) {
    badge.textContent = `${PRESETS[personality].icon} ${PRESETS[personality].name}`;
  }

  const modelSelect = document.getElementById('model-select');
  if (modelSelect) modelSelect.value = modelType;

  const streamingToggle = document.getElementById('streaming-toggle');
  if (streamingToggle) streamingToggle.checked = streamingEnabled;

  const voiceInputToggle = document.getElementById('voice-input-toggle');
  if (voiceInputToggle) voiceInputToggle.checked = voiceInputEnabled;

  const voiceOutputToggle = document.getElementById('voice-output-toggle');
  if (voiceOutputToggle) voiceOutputToggle.checked = voiceOutputEnabled;
});

function closeAllSidebars() {
  document.querySelectorAll('.sidebar').forEach(s => s.classList.remove('open'));
  document.getElementById('sidebar-backdrop')?.classList.remove('active');
}
