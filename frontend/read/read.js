/* 阅读模块前端。负责人：阅读模块开发者。
   铁律：不写死后端地址，一律用相对路径 /api/... */

const chat = document.getElementById('chat');
const textEl = document.getElementById('text');
const chapterEl = document.getElementById('chapter-title');

// 后端没启动时也能看到界面（双击 index.html 直接预览）
const DEMO_VIEW = {
  title: '第 3 章 · 认知负荷',
  blocks: [
    { type: 'header', text: '第 3 章 · 认知负荷' },
    { type: 'quote', text: '(这里显示你选中的那句话)' },
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

const sessionId = 'demo-' + Date.now();

textEl.addEventListener('mouseup', async () => {
  const span = window.getSelection().toString().trim();
  if (span.length < 5) return;

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
    view = JSON.parse(JSON.stringify(DEMO_VIEW));
    view.blocks[1].text = span;
  }
  renderBlocks(chat, view);
});

document.addEventListener('chip:select', e => {
  const box = document.createElement('div');
  box.className = 'card';
  box.innerHTML =
    '<div class="muted">你选了：' + e.detail.label + '</div>' +
    '<p style="margin:8px 0 0">（后端接入后，这里会显示分层支架的第一句——' +
    '它不会直接给答案。）</p>';
  chat.appendChild(box);
});

document.getElementById('end-session').onclick = () => {
  const box = document.createElement('div');
  box.className = 'card';
  box.innerHTML =
    '<h3>本节理解体检</h3>' +
    '<div class="muted">概念 4 个　·　能自释 1　·　半懂 2　·　未解决 1</div>' +
    '<p style="margin:10px 0 0">要不要花 2 分钟，把本节核心概念用自己的话说一遍？</p>';
  chat.appendChild(box);
};
