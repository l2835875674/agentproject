/* 物理模块前端。负责人：物理模块开发者。 */

const resultEl = document.getElementById('result');
const inputEl = document.getElementById('input');

const DEMO_SPEC = {
  model: 'incline_conveyor',
  block: { mass: 1, initial_speed: 0 },
  incline: { angle: 37, length: 2, mu: 0.25 },
  conveyor: { length: 3, belt_speed: 2, direction: 'right', mu: 0.2 },
  environment: { g: 10 },
  validate_status: 'green'
};

document.getElementById('build').onclick = async () => {
  const text = inputEl.value.trim();
  if (!text) return;

  let view;
  try {
    const res = await fetch('/api/physics/build', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ text })
    });
    view = await res.json();
  } catch (e) {
    view = demoView();
  }
  renderBlocks(resultEl, view);
  bindSlider();
};

function demoView() {
  return {
    title: '确认卡',
    blocks: [
      { type: 'table', rows: [
        { k: '斜面', v: '37° · 长 2 m · μ = 0.25' },
        { k: '传送带', v: '长 3 m · v = 2 m/s · 向右 · μ = 0.2' },
        { k: '假设', v: '底端平滑连接，速度大小不变' }
      ]},
      { type: 'steps', items: [
        { text: '斜面：a₁ = 4 m/s²，v₁ = 4 m/s，t₁ = 1 s' },
        { text: '传送带：a₂ = −2 m/s²，1 s 后共速 2 m/s，位移 3 m' },
        { text: '热量：斜面 4 J + 传送带 2 J = 6 J' }
      ]},
      { type: 'canvas', spec: DEMO_SPEC }
    ]
  };
}

// 参数滑块：拖一下就重算（后端接入后改为调接口）
function bindSlider() {
  const box = document.createElement('div');
  box.className = 'card';
  box.style.marginTop = '18px';
  box.innerHTML =
    '<div class="muted">拖一下看看临界</div>' +
    '<div class="slider-row">' +
    '  <span>传送带速度</span>' +
    '  <input type="range" min="0" max="5" step="0.1" value="2" id="belt">' +
    '  <span class="val" id="belt-val">2.0 m/s</span>' +
    '</div>' +
    '<p class="muted" id="hint" style="margin:10px 0 0">共速点在传送带中段。</p>';
  resultEl.appendChild(box);

  const belt = box.querySelector('#belt');
  const val = box.querySelector('#belt-val');
  const hint = box.querySelector('#hint');

  belt.oninput = () => {
    const v = parseFloat(belt.value);
    val.textContent = v.toFixed(1) + ' m/s';
    const cv = resultEl.querySelector('canvas');
    if (cv) renderScene(cv, {
      incline: DEMO_SPEC.incline,
      conveyor: { ...DEMO_SPEC.conveyor, belt_speed: v }
    });
    hint.textContent = Math.abs(v - 2) < 0.05
      ? '刚好在传送带末端共速。'
      : (v > 2 ? '带速更高，共速点提前。' : '带速更低，物块先减速到较低速度再共速。');
  };
}
