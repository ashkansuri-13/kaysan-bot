// ============================================
// Kaysan AI — Web App v4.0 (2026)
// 10 Amazing Features
// ============================================

const API = '';
let tg = null, tgUser = null;
let ws = null, wsReconnectTimer = null;

// ============================================
// Telegram
// ============================================
function initTelegram() {
  if (window.Telegram && window.Telegram.WebApp) {
    tg = window.Telegram.WebApp;
    tg.ready(); tg.expand(); tg.enableClosingConfirmation();
    if (tg.initDataUnsafe && tg.initDataUnsafe.user) { tgUser = tg.initDataUnsafe.user; applyTelegramTheme(); verifyAndGreet(); }
    else if (tg.initData) { fetch(`${API}/api/verify-user`, { method: 'POST', headers: {'Content-Type':'application/json'}, body: JSON.stringify({init_data:tg.initData}) }).then(r=>r.json()).then(d=>{if(d.ok){tgUser=d.user;applyTelegramTheme();verifyAndGreet();}}).catch(()=>{}); }
    if (tg.colorScheme === 'dark') document.documentElement.setAttribute('data-theme','dark');
    tg.MainButton.hide(); tg.BackButton.onClick(() => tg.close());
  }
}
function applyTelegramTheme() { if(!tg) return; const c=tg.themeParams; if(c){const r=document.documentElement; if(c.bg_color) r.style.setProperty('--bg-primary',c.bg_color); if(c.secondary_bg_color) r.style.setProperty('--bg-secondary',c.secondary_bg_color); if(c.text_color) r.style.setProperty('--text-primary',c.text_color); if(c.hint_color) r.style.setProperty('--text-secondary',c.hint_color); if(c.button_color) r.style.setProperty('--accent',c.button_color);} }
function verifyAndGreet() { if(!tgUser) return; const n=tgUser.first_name||tgUser.username||'کاربر'; const g=document.getElementById('user-greeting'); const w=document.getElementById('welcome-name'); if(g) g.textContent=`سلام ${n}`; if(w) w.textContent=n; }

// ============================================
// State
// ============================================
let chatHistory=[], conversations=[], currentConvId=null;
let personality='balanced', customPrompt='', modelType='auto', lang='ku';
let voiceInputEnabled=false, voiceOutputEnabled=false, streamingEnabled=true;
let particlesEnabled=true, soundsEnabled=true;
let isRecording=false, mediaRecorder=null, audioChunks=[], voiceTimer=null, voiceSeconds=0;
let useWebSocket=true;

const PRESETS={balanced:{name:'متعادل',icon:'⚖️'},blunt:{name:'رک و راست',icon:'🔪'},exaggerated:{name:'اغراق‌آمیز',icon:'🎭'},friendly:{name:'کاربرپسند',icon:'🤗'},professional:{name:'حرفه‌ای',icon:'💼'},sarcastic:{name:'کنایه‌آمیز',icon:'😏'},caring:{name:'مهربان',icon:'💕'},technical:{name:'فنی',icon:'🔧'}};
const EMOJIS=['😀','😂','😍','🥰','😎','🤩','😭','🤔','😱','🥳','😴','🙄','👍','👎','❤️','🔥','⭐','🎉','💯','🙏','👋','💪','✌️','🤝','👀','💡','🚀','✨','🎯','🎨','💻','🤖','🧠','📚','🎵','🌙','☀️','🌈','🍕','☕','🎮','⚽','🏆','📷','✈️','🌍','📱','🔮','💎','🌟'];

// ============================================
// Markdown (XSS-safe)
// ============================================
function renderMarkdown(t) {
  if(!t) return '';
  let h=t.replace(/&/g,'&amp;').replace(/</g,'&lt;').replace(/>/g,'&gt;');
  h=h.replace(/```(\w*)\n([\s\S]*?)```/g,(_,l,c)=>`<pre><code class="lang-${l||'text'}">${c.trim()}</code></pre>`);
  h=h.replace(/`([^`]+)`/g,'<code>$1</code>');
  h=h.replace(/\*\*(.+?)\*\*/g,'<strong>$1</strong>');
  h=h.replace(/\*(.+?)\*/g,'<em>$1</em>');
  h=h.replace(/^### (.+)$/gm,'<h3>$1</h3>');
  h=h.replace(/^## (.+)$/gm,'<h2>$1</h2>');
  h=h.replace(/^# (.+)$/gm,'<h1>$1</h1>');
  h=h.replace(/^> (.+)$/gm,'<blockquote>$1</blockquote>');
  h=h.replace(/^- (.+)$/gm,'<li>$1</li>');
  h=h.replace(/\[([^\]]+)\]\(([^)]+)\)/g,(m,t,u)=>(u.startsWith('javascript:')||u.startsWith('data:'))?m:`<a href="${u}" target="_blank" rel="noopener">${t}</a>`);
  h=h.replace(/\n/g,'<br>');
  return h;
}

// ============================================
// Particles
// ============================================
let particleAnimFrame=null;
function initParticles() {
  const c=document.getElementById('particles'); if(!c) return;
  const ctx=c.getContext('2d'); const ps=[];
  function resize(){c.width=innerWidth;c.height=innerHeight;} resize();
  addEventListener('resize',resize);
  class P{constructor(){this.reset();}reset(){this.x=Math.random()*c.width;this.y=Math.random()*c.height;this.s=Math.random()*2+0.5;this.vx=(Math.random()-0.5)*0.5;this.vy=(Math.random()-0.5)*0.5;this.o=Math.random()*0.5+0.1;}update(){this.x+=this.vx;this.y+=this.vy;if(this.x<0||this.x>c.width||this.y<0||this.y>c.height)this.reset();}draw(){ctx.beginPath();ctx.arc(this.x,this.y,this.s,0,Math.PI*2);ctx.fillStyle=`rgba(129,140,248,${this.o})`;ctx.fill();}}
  for(let i=0;i<50;i++)ps.push(new P());
  function animate(){ctx.clearRect(0,0,c.width,c.height);ps.forEach(p=>{p.update();p.draw();});for(let i=0;i<ps.length;i++)for(let j=i+1;j<ps.length;j++){const dx=ps[i].x-ps[j].x,dy=ps[i].y-ps[j].y,d=Math.sqrt(dx*dx+dy*dy);if(d<120){ctx.beginPath();ctx.moveTo(ps[i].x,ps[i].y);ctx.lineTo(ps[j].x,ps[j].y);ctx.strokeStyle=`rgba(129,140,248,${0.1*(1-d/120)})`;ctx.stroke();}}particleAnimFrame=requestAnimationFrame(animate);}
  if(particlesEnabled) animate();
  window.toggleParticles=(on)=>{particlesEnabled=on;if(on){if(!particleAnimFrame)animate();}else{cancelAnimationFrame(particleAnimFrame);particleAnimFrame=null;}};
}

// ============================================
// Sound
// ============================================
let _audioCtx=null;
function getAudioCtx(){if(!_audioCtx||_audioCtx.state==='closed')_audioCtx=new(window.AudioContext||window.webkitAudioContext)();return _audioCtx;}
function playSound(t){if(!soundsEnabled)return;try{const c=getAudioCtx(),o=c.createOscillator(),g=c.createGain();o.connect(g);g.connect(c.destination);g.gain.value=0.1;if(t==='send'){o.frequency.value=800;o.type='sine';}else if(t==='receive'){o.frequency.value=600;o.type='sine';}else if(t==='error'){o.frequency.value=200;o.type='sawtooth';}g.gain.exponentialRampToValueAtTime(0.001,c.currentTime+0.15);o.start(c.currentTime);o.stop(c.currentTime+0.15);}catch(e){}}

// ============================================
// Toast
// ============================================
function showToast(m,d=3000){const t=document.getElementById('toast');if(!t)return;t.textContent=m;t.classList.remove('hidden');t.classList.add('show');setTimeout(()=>{t.classList.remove('show');t.classList.add('hidden');},d);}

// ============================================
// Settings
// ============================================
function loadSettings(){try{const s=JSON.parse(localStorage.getItem('kay_settings')||'{}');personality=s.personality||'balanced';customPrompt=s.customPrompt||'';modelType=s.modelType||'auto';lang=s.lang||'ku';voiceInputEnabled=s.voiceInputEnabled||false;voiceOutputEnabled=s.voiceOutputEnabled||false;streamingEnabled=s.streamingEnabled!==false;particlesEnabled=s.particlesEnabled!==false;soundsEnabled=s.soundsEnabled!==false;}catch(e){}}
function saveSettings(){localStorage.setItem('kay_settings',JSON.stringify({personality,customPrompt,modelType,lang,voiceInputEnabled,voiceOutputEnabled,streamingEnabled,particlesEnabled,soundsEnabled}));}

// ============================================
// Conversations
// ============================================
function loadConversations(){try{conversations=JSON.parse(localStorage.getItem('kay_conversations')||'[]');}catch(e){conversations=[];}}
function saveConversations(){localStorage.setItem('kay_conversations',JSON.stringify(conversations));}
function newConversation(){currentConvId=Date.now().toString();chatHistory=[];conversations.unshift({id:currentConvId,title:'مکالمه جدید',messages:[],time:new Date().toISOString()});saveConversations();renderConversations();showWelcome();}
function renderConversations(){const l=document.getElementById('conversations-list');if(!l)return;if(conversations.length===0){l.innerHTML='<div class="conv-empty">هنوز مکالمه‌ای ندارید</div>';return;}l.innerHTML=conversations.map(c=>`<div class="conv-item ${c.id===currentConvId?'active':''}" data-id="${c.id}"><div class="conv-title">${c.title}</div><div class="conv-time">${new Date(c.time).toLocaleDateString('fa')}</div></div>`).join('');l.querySelectorAll('.conv-item').forEach(el=>{el.addEventListener('click',()=>{const conv=conversations.find(c=>c.id===el.dataset.id);if(conv){currentConvId=conv.id;chatHistory=conv.messages||[];renderMessages();closeAllSidebars();}});});}
function renderMessages(){const m=document.getElementById('messages');if(!m)return;m.innerHTML='';if(chatHistory.length===0){showWelcome();return;}hideWelcome();chatHistory.forEach(msg=>{addMessage(msg.role==='assistant'?'bot':'user',msg.content);});}

// ============================================
// Messages
// ============================================
function showWelcome(){const w=document.getElementById('welcome-screen'),m=document.getElementById('messages');if(w)w.style.display='flex';if(m)m.innerHTML='';}
function hideWelcome(){const w=document.getElementById('welcome-screen');if(w)w.style.display='none';}
function addMessage(role,content,streaming=false) {
  hideWelcome();const m=document.getElementById('messages');if(!m)return null;
  const id='msg-'+Date.now()+'-'+Math.random().toString(36).slice(2,6);
  const time=new Date().toLocaleTimeString('fa',{hour:'2-digit',minute:'2-digit'});
  const avatar=role==='bot'?'<img src="/logo.png" alt="Kaysan">':(tgUser&&tgUser.photo_url?`<img src="${tgUser.photo_url}" alt="User">`:'👤');
  const html=`<div class="msg ${role}" id="${id}"><div class="msg-avatar">${avatar}</div><div><div class="msg-bubble">${streaming?'<div class="streaming-text"></div>':renderMarkdown(content)}</div><div class="msg-time">${time}</div><div class="msg-actions"><button class="msg-action" data-action="copy" data-target="${id}">📋 کپی</button><button class="msg-action" data-action="speak" data-target="${id}">🔊 صدا</button></div></div></div>`;
  m.insertAdjacentHTML('beforeend',html);m.scrollTop=m.scrollHeight;
  const el=document.getElementById(id);
  if(el)el.querySelectorAll('.msg-action').forEach(b=>{b.addEventListener('click',()=>{if(b.dataset.action==='copy')copyMessage(b.dataset.target);if(b.dataset.action==='speak')speakMessage(b.dataset.target);});});
  return id;
}
function updateStreamingMessage(id,t){const e=document.querySelector(`#${id} .streaming-text`);if(e)e.innerHTML=renderMarkdown(t);const m=document.getElementById('messages');if(m)m.scrollTop=m.scrollHeight;}
function copyMessage(id){const e=document.querySelector(`#${id} .msg-bubble`);if(e){navigator.clipboard.writeText(e.textContent);showToast('کپی شد!');}}
function speakMessage(id){const e=document.querySelector(`#${id} .msg-bubble`);if(e&&'speechSynthesis' in window){const u=new SpeechSynthesisUtterance(e.textContent);u.lang=lang==='ku'?'ckb':lang==='fa'?'fa':'en';speechSynthesis.speak(u);}}

// ============================================
// Sentiment Display
// ============================================
function showSentiment(s){if(!s)return;const b=document.getElementById('sentiment-badge');if(b){b.textContent=`${s.emoji} ${s.label==='positive'?'مثبت':s.label==='negative'?'منفی':'خنثی'}`;b.style.display='inline-block';setTimeout(()=>{b.style.display='none';},3000);}}

// ============================================
// WebSocket
// ============================================
function initWebSocket() {
  const proto = location.protocol === 'https:' ? 'wss:' : 'ws:';
  const url = `${proto}//${location.host}/ws`;
  try {
    ws = new WebSocket(url);
    ws.onopen = () => { log('WS connected'); useWebSocket = true; };
    ws.onclose = () => { useWebSocket = false; wsReconnectTimer = setTimeout(initWebSocket, 5000); };
    ws.onerror = () => { useWebSocket = false; };
    ws.onmessage = (e) => {
      try {
        const data = JSON.parse(e.data);
        if (data.error && data.done) { playSound('error'); showToast(`خطا: ${data.error}`); return; }
        if (data.sentiment) showSentiment(data.sentiment);
        if (data.done) {
          if (data.full) chatHistory.push({role:'assistant',content:data.full});
          playSound('receive');
          const typing = document.getElementById('typing-indicator');
          if (typing) typing.classList.add('hidden');
          return;
        }
        if (data.text) {
          const lastBot = document.querySelector('.msg.bot:last-child .streaming-text');
          if (lastBot) { lastBot._full = (lastBot._full||'') + data.text; lastBot.innerHTML = renderMarkdown(lastBot._full); }
          const msgs = document.getElementById('messages');
          if (msgs) msgs.scrollTop = msgs.scrollHeight;
        }
      } catch(e) {}
    };
  } catch(e) { useWebSocket = false; }
}

// ============================================
// Chat
// ============================================
async function sendMessage(text) {
  if(!text.trim())return;
  playSound('send');
  addMessage('user',text);
  chatHistory.push({role:'user',content:text});
  const input=document.getElementById('msg-input');
  if(input){input.value='';input.style.height='auto';}
  document.getElementById('send-btn').disabled=true;
  const typing=document.getElementById('typing-indicator');
  if(typing)typing.classList.remove('hidden');

  if(useWebSocket && ws && ws.readyState===WebSocket.OPEN) {
    addMessage('bot','',true);
    ws.send(JSON.stringify({message:text,model_type:modelType,personality,personality}));
    return;
  }

  try {
    const body={message:text,model_type:modelType,personality,custom_prompt:customPrompt,stream:streamingEnabled};
    if(tg&&tg.initData)body.init_data=tg.initData;
    const msgId=addMessage('bot','',true);

    if(streamingEnabled) {
      const res=await fetch(`${API}/api/chat`,{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify(body)});
      if(!res.ok){const err=await res.json().catch(()=>({}));throw new Error(err.error||'Request failed');}
      const reader=res.body.getReader(),decoder=new TextDecoder();let full='';
      while(true){const{done,value}=await reader.read();if(done)break;const chunk=decoder.decode(value);for(const line of chunk.split('\n')){if(line.startsWith('data: ')){try{const d=JSON.parse(line.slice(6));if(d.error)throw new Error(d.error);if(d.sentiment)showSentiment(d.sentiment);if(d.done)break;full+=d.text;updateStreamingMessage(msgId,full);}catch(e){if(e.message!=='Unexpected end of JSON input')throw e;}}}}
      chatHistory.push({role:'assistant',content:full});
    } else {
      const res=await fetch(`${API}/api/chat`,{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify(body)});
      if(!res.ok){const err=await res.json().catch(()=>({}));throw new Error(err.error||'Request failed');}
      const data=await res.json();
      if(data.sentiment)showSentiment(data.sentiment);
      const bubble=document.querySelector(`#${msgId} .msg-bubble`);
      if(bubble)bubble.innerHTML=renderMarkdown(data.response);
      chatHistory.push({role:'assistant',content:data.response});
    }
    playSound('receive');
  } catch(e) {
    playSound('error');
    showToast(`خطا: ${e.message}`);
  } finally {
    if(typing)typing.classList.add('hidden');
    if(currentConvId){const conv=conversations.find(c=>c.id===currentConvId);if(conv){conv.messages=chatHistory;if(chatHistory.length===1)conv.title=text.substring(0,30);saveConversations();}}
  }
}

// ============================================
// File Upload
// ============================================
function initFileUpload() {
  const uploadBtn = document.getElementById('upload-btn');
  const fileInput = document.getElementById('file-input');
  if (!uploadBtn || !fileInput) return;

  uploadBtn.addEventListener('click', () => fileInput.click());
  fileInput.addEventListener('change', async (e) => {
    const file = e.target.files[0];
    if (!file) return;
    fileInput.value = '';

    const formData = new FormData();
    formData.append('file', file);

    try {
      showToast(`در حال آپلود ${file.name}...`);
      const res = await fetch(`${API}/api/upload`, { method: 'POST', body: formData });
      if (!res.ok) throw new Error('Upload failed');
      const data = await res.json();

      if (data.type === 'image') {
        addMessage('user', `![${file.name}](${data.data_url})`);
        sendMessage(`این تصویر رو تحلیل کن: ${file.name}`);
      } else {
        addMessage('user', `📎 ${file.name} (${(file.size/1024).toFixed(1)}KB)`);
        sendMessage(`فایل ${file.name} رو بررسی کن`);
      }
    } catch (e) {
      showToast(`خطا در آپلود: ${e.message}`);
    }
  });
}

// ============================================
// Voice
// ============================================
function initVoice() {
  const v=document.getElementById('voice-btn');
  if(v) v.addEventListener('click',()=>{if(isRecording)stopRecording();else startRecording();});
}
function startRecording(){if(!('MediaRecorder' in window)){showToast('ورودی صوتی پشتیبانی نمی‌شود');return;}navigator.mediaDevices.getUserMedia({audio:true}).then(stream=>{isRecording=true;audioChunks=[];voiceSeconds=0;const mt=MediaRecorder.isTypeSupported('audio/webm;codecs=opus')?'audio/webm;codecs=opus':'audio/webm';mediaRecorder=new MediaRecorder(stream,{mimeType:mt});mediaRecorder.ondataavailable=e=>{if(e.data.size>0)audioChunks.push(e.data);};mediaRecorder.onstop=()=>{stream.getTracks().forEach(t=>t.stop());isRecording=false;document.getElementById('voice-btn')?.classList.remove('recording');};mediaRecorder.start();document.getElementById('voice-btn')?.classList.add('recording');const o=document.getElementById('voice-overlay');if(o)o.classList.remove('hidden');const w=document.getElementById('voice-waveform');if(w)w.innerHTML=Array(20).fill(0).map((_,i)=>`<div class="bar" style="animation-delay:${i*0.05}s"></div>`).join('');voiceTimer=setInterval(()=>{voiceSeconds++;const m=Math.floor(voiceSeconds/60).toString().padStart(2,'0'),s=(voiceSeconds%60).toString().padStart(2,'0');const t=document.getElementById('voice-timer');if(t)t.textContent=`${m}:${s}`;},1000);}).catch(()=>showToast('اجازه دسترسی به میکروفون داده نشد'));}
function stopRecording(){if(mediaRecorder&&mediaRecorder.state!=='inactive')mediaRecorder.stop();clearInterval(voiceTimer);const o=document.getElementById('voice-overlay');if(o)o.classList.add('hidden');}
async function sendVoiceMessage(){if(audioChunks.length===0){stopRecording();return;}const blob=new Blob(audioChunks,{type:mediaRecorder?.mimeType||'audio/webm'});stopRecording();const typing=document.getElementById('typing-indicator');if(typing)typing.classList.remove('hidden');try{const fd=new FormData();fd.append('audio',blob,'voice.webm');const res=await fetch(`${API}/api/voice`,{method:'POST',body:fd});if(!res.ok){const err=await res.json().catch(()=>({}));throw new Error(err.error||'Failed');}const data=await res.json();if(data.text){showToast(`متن: ${data.text.substring(0,50)}...`);sendMessage(data.text);}}catch(e){showToast(`خطا: ${e.message}`);}finally{if(typing)typing.classList.add('hidden');}}

// ============================================
// Emoji
// ============================================
function initEmojiPicker(){const b=document.getElementById('emoji-btn'),p=document.getElementById('emoji-picker'),g=document.getElementById('emoji-grid'),s=document.getElementById('emoji-search-input'),i=document.getElementById('msg-input');if(!b||!p||!g)return;function render(f=''){const fs=EMOJIS.filter(e=>!f||e.includes(f));g.innerHTML=fs.map(e=>`<div class="emoji-item" data-emoji="${e}">${e}</div>`).join('');g.querySelectorAll('.emoji-item').forEach(el=>{el.addEventListener('click',()=>{i.value+=el.dataset.emoji;i.focus();p.classList.add('hidden');});});}render();b.addEventListener('click',e=>{e.stopPropagation();p.classList.toggle('hidden');});if(s)s.addEventListener('input',()=>render(s.value));document.addEventListener('click',e=>{if(!p.contains(e.target)&&e.target!==b)p.classList.add('hidden');});}

// ============================================
// Theme
// ============================================
function initTheme(){const t=document.getElementById('theme-toggle');if(!t)return;t.addEventListener('click',()=>{const c=document.documentElement.getAttribute('data-theme'),n=c==='dark'?'light':'dark';document.documentElement.setAttribute('data-theme',n);localStorage.setItem('kay_theme',n);if(tg)tg.switchHeaderTheme(n);});const s=localStorage.getItem('kay_theme');if(s)document.documentElement.setAttribute('data-theme',s);}

// ============================================
// Service Worker
// ============================================
function initServiceWorker(){if('serviceWorker' in navigator){navigator.serviceWorker.register('/sw.js').then(()=>log('SW registered')).catch(()=>{});}}
function log(m){console.log('[Kaysan]',m);}

// ============================================
// Init
// ============================================
document.addEventListener('DOMContentLoaded',()=>{
  initTelegram();loadSettings();loadConversations();initParticles();initTheme();initVoice();initEmojiPicker();initFileUpload();initServiceWorker();initWebSocket();

  setTimeout(()=>{const l=document.getElementById('loading-screen');if(l)l.classList.add('hidden');},1500);
  renderConversations();verifyAndGreet();

  const input=document.getElementById('msg-input'),sendBtn=document.getElementById('send-btn');
  if(input){input.addEventListener('input',()=>{input.style.height='auto';input.style.height=Math.min(input.scrollHeight,120)+'px';sendBtn.disabled=!input.value.trim();});input.addEventListener('keydown',e=>{if(e.key==='Enter'&&!e.shiftKey){e.preventDefault();if(input.value.trim())sendMessage(input.value);}});}
  if(sendBtn)sendBtn.addEventListener('click',()=>{if(input.value.trim())sendMessage(input.value);});

  document.querySelectorAll('.quick-card').forEach(b=>{b.addEventListener('click',()=>sendMessage(b.dataset.msg));});
  document.getElementById('new-chat-btn')?.addEventListener('click',newConversation);
  document.getElementById('history-btn')?.addEventListener('click',()=>{document.getElementById('history-panel')?.classList.toggle('open');document.getElementById('sidebar-backdrop')?.classList.toggle('active');});
  document.getElementById('personality-toggle')?.addEventListener('click',()=>{document.getElementById('personality-panel')?.classList.toggle('open');document.getElementById('sidebar-backdrop')?.classList.toggle('active');});
  document.getElementById('settings-btn')?.addEventListener('click',()=>{document.getElementById('settings-panel')?.classList.toggle('open');document.getElementById('sidebar-backdrop')?.classList.toggle('active');});

  document.querySelectorAll('.sidebar-close,#history-close,#settings-close').forEach(b=>{b?.addEventListener('click',closeAllSidebars);});
  document.getElementById('sidebar-backdrop')?.addEventListener('click',closeAllSidebars);

  document.querySelectorAll('.lang-btn').forEach(b=>{b.addEventListener('click',()=>{document.querySelectorAll('.lang-btn').forEach(x=>x.classList.remove('active'));b.classList.add('active');lang=b.dataset.lang;saveSettings();});});

  document.getElementById('save-btn')?.addEventListener('click',()=>{customPrompt=document.getElementById('custom-prompt')?.value||'';saveSettings();showToast('ذخیره شد!');closeAllSidebars();});
  document.getElementById('reset-btn')?.addEventListener('click',()=>{personality='balanced';customPrompt='';saveSettings();showToast('بازنشانی شد');});
  document.getElementById('clear-all-btn')?.addEventListener('click',()=>{if(confirm('همه پاک شوند؟')){conversations=[];saveConversations();newConversation();showToast('پاک شد');}});

  document.getElementById('voice-cancel')?.addEventListener('click',stopRecording);
  document.getElementById('voice-send')?.addEventListener('click',sendVoiceMessage);
  document.getElementById('image-btn')?.addEventListener('click',()=>{const i=document.getElementById('msg-input');const p=i?.value?.trim();if(!p){showToast('توضیح تصویر رو بنویسید');return;}i.value='';sendMessage(`تصویر بساز: ${p}`);});

  document.getElementById('model-select')?.addEventListener('change',e=>{modelType=e.target.value;saveSettings();});
  document.getElementById('streaming-toggle')?.addEventListener('change',e=>{streamingEnabled=e.target.checked;saveSettings();});
  document.getElementById('voice-input-toggle')?.addEventListener('change',e=>{voiceInputEnabled=e.target.checked;saveSettings();});
  document.getElementById('voice-output-toggle')?.addEventListener('change',e=>{voiceOutputEnabled=e.target.checked;saveSettings();});
  document.getElementById('particles-toggle')?.addEventListener('change',e=>{particlesEnabled=e.target.checked;saveSettings();if(window.toggleParticles)window.toggleParticles(particlesEnabled);});
  document.getElementById('sounds-toggle')?.addEventListener('change',e=>{soundsEnabled=e.target.checked;saveSettings();});

  const pl=document.getElementById('preset-list');
  if(pl){pl.innerHTML=Object.entries(PRESETS).map(([k,p])=>`<div class="preset-card ${personality===k?'active':''}" data-preset="${k}"><div class="preset-icon">${p.icon}</div><div class="preset-name">${p.name}</div></div>`).join('');pl.querySelectorAll('.preset-card').forEach(c=>{c.addEventListener('click',()=>{pl.querySelectorAll('.preset-card').forEach(x=>x.classList.remove('active'));c.classList.add('active');personality=c.dataset.preset;saveSettings();showToast(`شخصیت: ${PRESETS[personality].name}`);});});}

  const badge=document.getElementById('personality-badge');
  if(badge&&PRESETS[personality])badge.textContent=`${PRESETS[personality].icon} ${PRESETS[personality].name}`;
  const ms=document.getElementById('model-select');if(ms)ms.value=modelType;
  const st=document.getElementById('streaming-toggle');if(st)st.checked=streamingEnabled;
  const vi=document.getElementById('voice-input-toggle');if(vi)vi.checked=voiceInputEnabled;
  const vo=document.getElementById('voice-output-toggle');if(vo)vo.checked=voiceOutputEnabled;
});

function closeAllSidebars(){document.querySelectorAll('.sidebar').forEach(s=>s.classList.remove('open'));document.getElementById('sidebar-backdrop')?.classList.remove('active');}
