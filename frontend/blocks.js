/* ==========================================================
   blocks.js —— 通用渲染器（两个领域共用）
   输入 docs/interface.md 定义的 blocks，输出 DOM。
   加新的 block 类型 = 在这里加一个 case，必须全员约定。
   ========================================================== */

function el(tag, cls, text) {
  const n = document.createElement(tag);
  if (cls) n.className = cls;
  if (text != null) n.textContent = text;
  return n;
}

function renderBlocks(container, view) {
  container.innerHTML = '';
  if (view.title) {
    const h = el('h2');
    h.textContent = view.title;
    container.appendChild(h);
  }
  (view.blocks || []).forEach(b => container.appendChild(renderBlock(b)));
}

function renderBlock(b) {
  switch (b.type) {
    case 'header': {
      const h = el('h3', null, b.text);
      h.style.marginTop = '4px';
      return h;
    }
    case 'text':
      return el('p', null, b.text);

    case 'quote': {
      const d = el('div');
      d.style.borderLeft = '3px solid var(--c-primary)';
      d.style.background = 'var(--c-primary-soft)';
      d.style.padding = '10px 14px';
      d.style.borderRadius = 'var(--r-sm)';
      d.style.fontStyle = 'italic';
      d.textContent = b.text;
      return d;
    }
    case 'chips': {
      const wrap = el('div');
      if (b.label) wrap.appendChild(el('div', 'muted', b.label));
      const row = el('div');
      row.style.display = 'flex';
      row.style.flexWrap = 'wrap';
      row.style.gap = '8px';
      row.style.marginTop = '8px';
      (b.items || []).forEach(item => {
        const c = el('span', 'chip', item.label);
        c.dataset.id = item.id;
        c.onclick = () => {
          [...row.children].forEach(x => x.classList.remove('active'));
          c.classList.add('active');
          document.dispatchEvent(new CustomEvent('chip:select', { detail: item }));
        };
        row.appendChild(c);
      });
      wrap.appendChild(row);
      return wrap;
    }
    case 'buttons': {
      const row = el('div');
      row.style.display = 'flex';
      row.style.gap = '10px';
      row.style.marginTop = '10px';
      (b.items || []).forEach(item => {
        const btn = el('button', item.id === 'tell' ? 'btn ghost' : 'btn', item.label);
        btn.onclick = () =>
          document.dispatchEvent(new CustomEvent('button:click', { detail: item }));
        row.appendChild(btn);
      });
      return row;
    }
    case 'table': {
      const t = el('table');
      t.style.width = '100%';
      t.style.borderCollapse = 'collapse';
      (b.rows || []).forEach(r => {
        const tr = el('tr');
        const k = el('td', null, r.k);
        const v = el('td', null, r.v);
        k.style.padding = '8px 0';
        k.style.color = 'var(--c-muted)';
        k.style.width = '40%';
        v.style.padding = '8px 0';
        tr.appendChild(k); tr.appendChild(v);
        t.appendChild(tr);
      });
      return t;
    }
    case 'steps': {
      const ol = el('ol');
      (b.items || []).forEach(s => {
        const li = el('li');
        li.innerHTML = '<span style="font-family:Consolas,monospace">' + s.text + '</span>';
        ol.appendChild(li);
      });
      return ol;
    }
    case 'canvas': {
      const box = el('div', 'card');
      box.style.padding = '0';
      box.style.overflow = 'hidden';
      const cv = el('canvas');
      cv.width = 720; cv.height = 300;
      cv.style.width = '100%';
      box.appendChild(cv);
      // 交给物理模块的渲染器
      if (window.renderScene) setTimeout(() => window.renderScene(cv, b.spec), 0);
      return box;
    }
    case 'card': {
      const c = el('div', 'card');
      c.appendChild(el('h3', null, b.title));
      if (b.subtitle) c.appendChild(el('div', 'muted', b.subtitle));
      (b.rows || []).forEach(r => {
        const line = el('div');
        line.style.marginTop = '6px';
        line.innerHTML = '<span class="muted">' + r.k + '：</span>' +
                         '<span>' + (r.v || '—') + '</span>';
        c.appendChild(line);
      });
      return c;
    }
    default:
      return el('div', 'muted', '[未知 block: ' + b.type + ']');
  }
}

window.renderBlocks = renderBlocks;
