/* 阅读模块前端。负责人：阅读模块开发者。
   铁律：不写死后端地址，一律用相对路径 /api/... */

const chat = document.getElementById('chat');
const textEl = document.getElementById('text');
const chapterEl = document.getElementById('chapter-title');

const sessionId = 'demo-' + Date.now();
let lastSpan = '';

/* ---------- 小工具 ---------- */

function escapeHtml(s) {
  return String(s).replace(/[&<>]/g, c => ({ '&': '&amp;', '<': '&lt;', '>': '&gt;' }[c]));
}

function addBlock(html, cls) {
  const box = document.createElement('div');
  box.className = cls || 'card';
  box.innerHTML = html;
  chat.appendChild(box);
  chat.scrollTop = chat.scrollHeight;
  return box;
}

function addUser(text) {
  const p = document.createElement('div');
  p.style.textAlign = 'right';
  p.innerHTML = '<span style="display:inline-block;background:var(--c-primary);' +
    'color:#fff;padding:8px 14px;border-radius:10px;max-width:85%">' +
    escapeHtml(text) + '</span>';
  chat.appendChild(p);
  chat.scrollTop = chat.scrollHeight;
}

/* ---------- 选中文字 → 六个标签 ---------- */

textEl.addEventListener('mouseup', async () => {
  const span = window.getSelection().toString().trim();
  if (span.length < 5) return;
  lastSpan = span;

  let view;
  try {
    const res = await fetch('/api/read/select', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({
        session_id: sessionId,
        span,
        chapter_title: chapterEl.textContent
      })
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
  renderBlocks(chat, view);
  chat.scrollTop = chat.scrollHeight;
});

/* ---------- 点标签 → 跑一轮 agent ---------- */

document.addEventListener('chip:select', async e => {
  const type = e.detail.id;
  const label = e.detail.label;

  chat.innerHTML = '';
  addUser('我卡在：' + label);
  const box = addBlock('<div class="muted">思考中…</div>');

  try {
    const res = await fetch('/api/read/ask', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({
        session_id: sessionId,
        span: lastSpan,
        confusion_type: type,
        chapter_title: chapterEl.textContent
      })
    });
    const data = await res.json();
    box.innerHTML = '<div>' + escapeHtml(data.reply || '（没有回复）').replace(/\n/g, '<br>') + '</div>';

    if (data.tool_calls && data.tool_calls.length) {
      const names = data.tool_calls.map(t => t.name).join('、');
      const meta = document.createElement('div');
      meta.className = 'muted';
      meta.style.marginTop = '10px';
      meta.textContent = '本轮调用了工具：' + names;
      box.appendChild(meta);
    }
  } catch (err) {
    box.innerHTML = '<div class="muted">调用失败：' + escapeHtml(err.message) + '</div>';
  }
  chat.scrollTop = chat.scrollHeight;
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
    box.innerHTML =
      '<h3>本节理解体检</h3>' +
      '<p class="muted">（后端未连接，暂时看不到档案）</p>';
  }
  chat.appendChild(box);
  chat.scrollTop = chat.scrollHeight;
};
