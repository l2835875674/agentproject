/* 阅读模块前端。负责人：阅读模块开发者。
   铁律：不写死后端地址，一律用相对路径 /api/... */

const chat = document.getElementById('chat');
const textEl = document.getElementById('text');
const chapterEl = document.getElementById('chapter-title');
const composer = document.getElementById('composer');
const sendBtn = document.getElementById('send');

const sessionId = 'demo-' + Date.now();

/* 会话状态 */
let lastSpan = '';                       // 最近一次选中的原文
let lastType = null;                     // 最近一次点的困惑标签
let history = [];                        // 多轮追问的对话记录
let busy = false;

/* ---------- 小工具 ---------- */

function escapeHtml(s) {
  return String(s).replace(/[&<>]/g, c => ({ '&': '&amp;', '<': '&lt;', '>': '&gt;' }[c]));
}

function scrollDown() { chat.scrollTop = chat.scrollHeight; }

function addBubble(text, mine) {
  const wrap = document.createElement('div');
  wrap.style.textAlign = mine ? 'right' : 'left';
  const span = document.createElement('span');
  span.style.display = 'inline-block';
  span.style.padding = '9px 14px';
  span.style.borderRadius = '10px';
  span.style.maxWidth = '88%';
  span.style.textAlign = 'left';
  span.style.whiteSpace = 'pre-wrap';
  span.style.lineHeight = '1.7';
  if (mine) {
    span.style.background = 'var(--c-primary)';
    span.style.color = '#fff';
  } else {
    span.style.background = 'var(--c-bg)';
    span.style.border = '1px solid var(--c-border)';
  }
  span.textContent = text;
  wrap.appendChild(span);
  chat.appendChild(wrap);
  scrollDown();
  return wrap;
}

let controller = null;

function setBusy(v) {
  busy = v;
  composer.disabled = v;
  sendBtn.textContent = v ? '停止' : '发送';
  sendBtn.disabled = false;     // 忙碌时按钮变「停止」，仍然可点
}

/* ---------- 选中文字 → 六个标签 ---------- */

textEl.addEventListener('mouseup', async () => {
  const span = window.getSelection().toString().trim();
  if (span.length < 5) return;
  lastSpan = span;
  lastType = null;

  let view;
  try {
    const res = await fetch('/api/read/select', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ session_id: sessionId, span, chapter_title: chapterEl.textContent })
    });
    view = await res.json();
  } catch (e) {
    view = {
      title: chapterEl.textContent,
      blocks: [
        { type: 'quote', text: span },
        { type: 'chips', label: '你觉得哪里卡住了？', items: [
          { id: 'term', label: '术语不认识' },
          { id: 'syntax', label: '句子结构绕' },
          { id: 'logic_jump', label: '缺前提，逻辑跳了' },
          { id: 'background', label: '缺背景知识' },
          { id: 'tone', label: '语气/限定拿不准' },
          { id: 'cant_say', label: '我好像懂了但说不出来' }
        ]}
      ]
    };
  }
  chat.innerHTML = '';
  history = [];
  renderBlocks(chat, view);
  const tip = document.createElement('p');
  tip.className = 'muted';
  tip.style.marginTop = '12px';
  tip.textContent = '选一个标签，或者直接在下面打字问。';
  chat.appendChild(tip);
  scrollDown();
});

/* ---------- 统一的提问入口 ---------- */

async function ask({ type = null, text = null }) {
  if (busy) return;

  const shown = text || (type ? '我卡在：' + labelOf(type) : '');
  chat.querySelectorAll('.muted').forEach(n => {
    if (n.textContent.includes('选一个标签')) n.remove();
  });
  if (shown) addBubble(shown, true);

  setBusy(true);

  const status = document.createElement('div');
  status.className = 'muted';
  status.textContent = '连接中…';
  chat.appendChild(status);
  scrollDown();

  let bubbleText = null;     // 正在流式写入的气泡里的 <span>
  let answer = '';           // 累积的正文
  let failed = false;
  const toolNames = [];

  function ensureBubble() {
    if (bubbleText) return;
    const wrap = addBubble('', false);
    bubbleText = wrap.querySelector('span');
    status.remove();
  }

  controller = new AbortController();

  try {
    const res = await fetch('/api/read/ask_stream', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      signal: controller.signal,
      body: JSON.stringify({
        session_id: sessionId,
        span: lastSpan,
        confusion_type: type,
        chapter_title: chapterEl.textContent,
        message: text,
        history,
        reasoning_effort: prefs.reasoning_effort || null,
        system_prompt: prefs.system_prompt || null
      })
    });
    if (!res.ok || !res.body) throw new Error('HTTP ' + res.status);

    const reader = res.body.getReader();
    const decoder = new TextDecoder('utf-8');
    let buf = '';

    while (true) {
      const { done, value } = await reader.read();
      if (done) break;
      buf += decoder.decode(value, { stream: true });

      const parts = buf.split('\n\n');
      buf = parts.pop();

      for (const part of parts) {
        const line = part.trim();
        if (!line.startsWith('data:')) continue;
        let ev;
        try { ev = JSON.parse(line.slice(5).trim()); } catch (e) { continue; }

        if (ev.type === 'status') {
          if (!bubbleText) status.textContent = ev.text;
        } else if (ev.type === 'delta') {
          ensureBubble();
          answer += ev.text;
          bubbleText.textContent = answer;
          scrollDown();
        } else if (ev.type === 'tool') {
          toolNames.push(ev.name);
          if (!bubbleText) status.textContent = '查了一下你的档案…';
        } else if (ev.type === 'error') {
          status.remove();
          addBubble('出错了：' + ev.message, false);
          failed = true;
        } else if (ev.type === 'done') {
          // 收尾
        }
      }
    }

    status.remove();
    if (!failed && !bubbleText) addBubble('（没有回复）', false);
    if (failed) { setBusy(false); scrollDown(); return; }

    if (toolNames.length) {
      const meta = document.createElement('div');
      meta.className = 'muted';
      meta.style.marginTop = '-6px';
      meta.textContent = '本轮调用了工具：' + toolNames.join('、');
      chat.appendChild(meta);
    }

    history.push({ role: 'user', content: shown || '（继续追问）' });
    history.push({ role: 'assistant', content: answer });
  } catch (err) {
    status.remove();
    if (err.name === 'AbortError') {
      const tip = document.createElement('div');
      tip.className = 'muted';
      tip.textContent = answer ? '（已停止）' : '（已取消）';
      if (bubbleText) chat.appendChild(tip);
      else addBubble('（已取消）', false);
    } else {
      addBubble('调用失败：' + err.message, false);
    }
  } finally {
    controller = null;
    setBusy(false);
    scrollDown();
  }
}

function labelOf(id) {
  const map = {
    term: '术语不认识', syntax: '句子结构绕', logic_jump: '缺前提，逻辑跳了',
    background: '缺背景知识', tone: '语气/限定拿不准', cant_say: '我好像懂了但说不出来'
  };
  return map[id] || id;
}

/* 点标签 */
document.addEventListener('chip:select', e => {
  lastType = e.detail.id;
  ask({ type: lastType });
});

/* 打字发送 */
function send() {
  const text = composer.value.trim();
  if (!text || busy) return;
  composer.value = '';
  composer.style.height = 'auto';
  ask({ type: null, text });
}

sendBtn.onclick = () => {
  if (busy) { if (controller) controller.abort(); return; }
  send();
};

composer.addEventListener('keydown', e => {
  if (e.key === 'Enter' && !e.shiftKey) {
    e.preventDefault();
    send();
  }
});

composer.addEventListener('input', () => {
  composer.style.height = 'auto';
  composer.style.height = Math.min(composer.scrollHeight, 120) + 'px';
});

/* ---------- 结束本节 ---------- */

document.getElementById('end-session').onclick = async () => {
  let data = null;
  try {
    const res = await fetch('/api/read/archive/' + encodeURIComponent(sessionId));
    data = await res.json();
  } catch (e) { /* 后端没起来就看兜底 */ }

  const box = document.createElement('div');
  box.className = 'card';

  if (data && data.summary) {
    const c = data.summary.concept_counts;
    box.innerHTML =
      '<h3>本节理解体检</h3>' +
      '<div class="muted">能自释 ' + c.mastered + ' · 半懂 ' + c.shaky +
      ' · 未解决 ' + c.unresolved + '</div>' +
      '<p style="margin:10px 0 0">要不要花 2 分钟，把本节核心概念用自己的话说一遍？</p>';
  } else {
    box.innerHTML = '<h3>本节理解体检</h3><p class="muted">（后端未连接）</p>';
  }
  chat.appendChild(box);
  scrollDown();
};

/* ---------- 设置面板 ---------- */

const SETTINGS_KEY = 'read.settings.v1';
const mask = document.getElementById('settings-mask');
const effortSel = document.getElementById('set-effort');
const promptBox = document.getElementById('set-prompt');

let prefs = loadPrefs();
let defaultPrompt = '';
let defaultsLoaded = false;

function loadPrefs() {
  try { return JSON.parse(localStorage.getItem(SETTINGS_KEY)) || {}; }
  catch (e) { return {}; }
}

function savePrefs(p) {
  prefs = p;
  localStorage.setItem(SETTINGS_KEY, JSON.stringify(p));
}

async function ensureDefaults() {
  if (defaultsLoaded) return;
  try {
    const res = await fetch('/api/read/settings');
    defaultPrompt = (await res.json()).system_prompt || '';
    defaultsLoaded = true;
  } catch (e) {
    defaultPrompt = '';
  }
}

document.getElementById('open-settings').onclick = async () => {
  await ensureDefaults();
  effortSel.value = prefs.reasoning_effort || 'off';
  promptBox.value = prefs.system_prompt || defaultPrompt;
  mask.hidden = false;
  promptBox.focus();
};

document.getElementById('close-settings').onclick = () => { mask.hidden = true; };

mask.addEventListener('click', e => {
  if (e.target === mask) mask.hidden = true;
});

document.getElementById('save-settings').onclick = () => {
  const prompt = promptBox.value.trim();
  savePrefs({
    reasoning_effort: effortSel.value,
    // 与默认一致就不存，永远跟随后端最新版
    system_prompt: prompt === defaultPrompt.trim() ? '' : prompt
  });
  mask.hidden = true;
  addBubble('设置已保存。', false);
};

document.getElementById('reset-settings').onclick = async () => {
  await ensureDefaults();
  savePrefs({});
  effortSel.value = 'off';
  promptBox.value = defaultPrompt;
};

document.addEventListener('keydown', e => {
  if (e.key === 'Escape' && !mask.hidden) mask.hidden = true;
});
