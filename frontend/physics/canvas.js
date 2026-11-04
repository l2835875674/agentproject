/* Canvas 2D 渲染器。只认 SceneSpec，不知道任何业务逻辑。
   负责人：物理模块开发者。 */

function renderScene(cv, spec) {
  const ctx = cv.getContext('2d');
  const W = cv.width, H = cv.height;
  const g = spec && spec.incline ? spec.incline : { angle: 37, length: 2 };
  const belt = spec && spec.conveyor ? spec.conveyor : { length: 3, belt_speed: 2 };

  ctx.clearRect(0, 0, W, H);
  ctx.fillStyle = '#FFFFFF';
  ctx.fillRect(0, 0, W, H);

  const groundY = H - 70;
  const slopeTopX = 90, slopeTopY = 70;
  const slopeBotX = 290;

  // 地面
  ctx.strokeStyle = '#E3E7EF';
  ctx.lineWidth = 2;
  ctx.beginPath();
  ctx.moveTo(40, groundY);
  ctx.lineTo(W - 40, groundY);
  ctx.stroke();

  // 斜面
  ctx.strokeStyle = '#1F3564';
  ctx.lineWidth = 3;
  ctx.beginPath();
  ctx.moveTo(slopeTopX, slopeTopY);
  ctx.lineTo(slopeBotX, groundY);
  ctx.lineTo(slopeTopX, groundY);
  ctx.closePath();
  ctx.stroke();
  ctx.fillStyle = 'rgba(31,53,100,.05)';
  ctx.fill();

  // 角度标注
  ctx.fillStyle = '#6B7280';
  ctx.font = '13px 微软雅黑';
  ctx.fillText(g.angle + '°', slopeBotX - 46, groundY - 10);

  // 传送带
  const beltX = slopeBotX + 20;
  const beltY = groundY - 16;
  const beltW = Math.min(360, W - beltX - 70);
  ctx.fillStyle = '#EDF1F8';
  ctx.strokeStyle = '#1F3564';
  ctx.lineWidth = 2;
  ctx.beginPath();
  ctx.roundRect(beltX, beltY, beltW, 32, 6);
  ctx.fill();
  ctx.stroke();

  // 传送方向箭头
  ctx.strokeStyle = '#1F3564';
  ctx.lineWidth = 2;
  const dir = belt.direction === 'left' ? -1 : 1;
  for (let i = 1; i <= 3; i++) {
    const x = beltX + (beltW / 4) * i;
    ctx.beginPath();
    ctx.moveTo(x - 6 * dir, beltY + 10);
    ctx.lineTo(x + 4 * dir, beltY + 16);
    ctx.lineTo(x - 6 * dir, beltY + 22);
    ctx.stroke();
  }

  // 传送带速度标注
  ctx.fillStyle = '#1F3564';
  ctx.font = '13px 微软雅黑';
  ctx.fillText('v带 = ' + belt.belt_speed + ' m/s', beltX + 8, beltY - 10);

  // 物块
  ctx.fillStyle = '#C9A227';
  ctx.fillRect(slopeTopX + 6, slopeTopY - 18, 26, 22);
  ctx.strokeStyle = '#8A6D12';
  ctx.lineWidth = 2;
  ctx.strokeRect(slopeTopX + 6, slopeTopY - 18, 26, 22);

  // 标题
  ctx.fillStyle = '#2E2E2E';
  ctx.font = 'bold 14px 微软雅黑';
  ctx.fillText('斜面 → 水平传送带', 40, 32);
}

window.renderScene = renderScene;
