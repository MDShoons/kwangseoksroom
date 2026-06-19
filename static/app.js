const $ = (sel) => document.querySelector(sel);
const $$ = (sel) => Array.from(document.querySelectorAll(sel));

$$('.nav').forEach(btn => {
  btn.addEventListener('click', () => {
    $$('.nav').forEach(b => b.classList.remove('active'));
    $$('.panel').forEach(p => p.classList.remove('active'));
    btn.classList.add('active');
    $('#' + btn.dataset.target).classList.add('active');
  });
});

function formatBytes(bytes) {
  if (!bytes) return '0 B';
  const units = ['B','KB','MB','GB'];
  const i = Math.min(Math.floor(Math.log(bytes) / Math.log(1024)), units.length - 1);
  return `${(bytes / Math.pow(1024, i)).toFixed(2)} ${units[i]}`;
}

function renderFiles(input, target) {
  const files = Array.from(input.files || []);
  const total = files.reduce((sum, f) => sum + f.size, 0);
  target.innerHTML = files.length
    ? `${files.length}개 선택 · 총 ${formatBytes(total)}<br>${files.map(f => `· ${f.name} (${formatBytes(f.size)})`).join('<br>')}`
    : '';
}

$('#trainFiles').addEventListener('change', e => renderFiles(e.target, $('#trainFileList')));

function setLoading(btn, isLoading, label) {
  btn.disabled = isLoading;
  btn.dataset.original = btn.dataset.original || btn.textContent;
  btn.textContent = isLoading ? label : btn.dataset.original;
}

function renderAudioCards(container, outputs, meta) {
  container.innerHTML = '';
  if (meta) {
    const pre = document.createElement('pre');
    pre.className = 'meta';
    pre.textContent = typeof meta === 'string' ? meta : JSON.stringify(meta, null, 2);
    container.appendChild(pre);
  }
  const tpl = $('#audioCardTemplate');
  outputs.forEach(item => {
    const node = tpl.content.cloneNode(true);
    node.querySelector('.audio-title').textContent = item.label || item.checkpoint;
    node.querySelector('audio').src = item.url;
    const a = node.querySelector('.download');
    a.href = item.url;
    a.download = item.download_name || 'output.wav';
    container.appendChild(node);
  });
}

async function postFiles(url, field, files) {
  const fd = new FormData();
  files.forEach(file => fd.append(field, file));
  const res = await fetch(url, { method: 'POST', body: fd });
  const data = await res.json().catch(() => ({}));
  if (!res.ok) throw new Error(data.detail || '처리 중 오류가 발생했습니다.');
  return data;
}

$('#trainBtn').addEventListener('click', async () => {
  const files = Array.from($('#trainFiles').files || []);
  if (!files.length) return alert('학습할 보컬 파일을 선택하세요.');
  if (files.length > 10) return alert('학습 파일은 최대 10개까지 가능합니다.');
  const total = files.reduce((sum, f) => sum + f.size, 0);
  if (total > 5 * 1024 ** 3) return alert('총 5GB 이하만 업로드할 수 있습니다.');
  const btn = $('#trainBtn');
  setLoading(btn, true, '학습 분석 중...');
  try {
    const data = await postFiles('/api/train', 'files', files);
    btn.dataset.original = '학습 결과 미리보기';
    btn.textContent = '학습 결과 미리보기';
    renderAudioCards($('#trainResult'), data.preview_outputs || [], {
      training_id: data.training_id,
      file_count: data.file_count,
      total_analyzed_seconds: data.total_analyzed_seconds,
      analysis: data.analysis,
      note: '체크포인트는 비교용 결과입니다. 실제 초대규모 반복학습은 검증손실 기반 체크포인트로 대체해야 합니다.'
    });
  } catch (err) {
    $('#trainResult').innerHTML = `<div class="error">${err.message}</div>`;
  } finally {
    setLoading(btn, false);
  }
});

$('#vocalBtn').addEventListener('click', async () => {
  const file = $('#vocalFile').files?.[0];
  if (!file) return alert('변환할 보컬 파일을 선택하세요.');
  if (file.size > 1024 ** 3) return alert('보컬변환 파일은 1GB 이하만 가능합니다.');
  const btn = $('#vocalBtn');
  setLoading(btn, true, '보컬 분석·변환 중...');
  try {
    const data = await postFiles('/api/convert-vocal', 'file', [file]);
    renderAudioCards($('#vocalResult'), data.outputs || [], data);
    $('#alignBtn').disabled = false;
  } catch (err) {
    $('#vocalResult').innerHTML = `<div class="error">${err.message}</div>`;
  } finally {
    setLoading(btn, false);
  }
});

$('#instBtn').addEventListener('click', async () => {
  const file = $('#instFile').files?.[0];
  if (!file) return alert('반주 파일을 선택하세요.');
  const btn = $('#instBtn');
  setLoading(btn, true, '반주 변환 중...');
  try {
    const data = await postFiles('/api/convert-instrumental', 'file', [file]);
    renderAudioCards($('#instResult'), data.outputs || [], data.note);
  } catch (err) {
    $('#instResult').innerHTML = `<div class="error">${err.message}</div>`;
  } finally {
    setLoading(btn, false);
  }
});

$('#alignBtn').addEventListener('click', () => {
  alert('프로토타입에서는 자리만 구현되어 있습니다. 실제 정렬은 보컬 onset/beat map 추출 후 time-stretch 엔진을 연결해야 합니다.');
});
