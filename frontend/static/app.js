const resultBox = document.querySelector('#resultBox');
const audioPanel = document.querySelector('#audioPanel');
const audioPlayer = document.querySelector('#audioPlayer');
const downloadAudio = document.querySelector('#downloadAudio');
const downloadProfile = document.querySelector('#downloadProfile');
const jobIdInput = document.querySelector('#jobIdInput');

function showResult(data) {
  resultBox.textContent = typeof data === 'string' ? data : JSON.stringify(data, null, 2);
}

function formToData(form) {
  const data = new FormData();
  for (const el of form.elements) {
    if (!el.name) continue;
    if (el.type === 'file') {
      for (const file of el.files) data.append(el.name, file);
    } else if (el.type === 'checkbox') {
      data.append(el.name, el.checked ? 'true' : 'false');
    } else {
      data.append(el.name, el.value);
    }
  }
  return data;
}

async function postForm(url, formData) {
  const res = await fetch(url, { method: 'POST', body: formData });
  const text = await res.text();
  let data;
  try { data = JSON.parse(text); } catch { data = { raw: text }; }
  if (!res.ok) {
    const message = data.detail || data.message || '요청 처리 중 오류가 발생했습니다.';
    throw new Error(message);
  }
  return data;
}

document.querySelector('#trainForm').addEventListener('submit', async (event) => {
  event.preventDefault();
  const btn = event.currentTarget.querySelector('button');
  btn.disabled = true;
  showResult('스타일 프로파일을 생성하는 중입니다...');
  audioPanel.classList.add('hidden');
  try {
    const data = await postForm('/api/train', formToData(event.currentTarget));
    showResult(data);
    jobIdInput.value = data.job_id;
    downloadProfile.href = data.style_profile_url;
  } catch (err) {
    showResult({ ok: false, error: err.message });
  } finally {
    btn.disabled = false;
  }
});

document.querySelector('#coverForm').addEventListener('submit', async (event) => {
  event.preventDefault();
  const btn = event.currentTarget.querySelector('button');
  btn.disabled = true;
  showResult('연구용 보컬 가이드를 생성하는 중입니다...');
  try {
    const form = event.currentTarget;
    const jobId = encodeURIComponent(form.job_id.value.trim());
    const data = await postForm(`/api/cover/${jobId}`, formToData(form));
    showResult(data);
    audioPanel.classList.remove('hidden');
    audioPlayer.src = data.audio_url;
    downloadAudio.href = data.audio_url;
    downloadProfile.href = `/api/jobs/${jobId}/style-profile`;
  } catch (err) {
    showResult({ ok: false, error: err.message });
  } finally {
    btn.disabled = false;
  }
});
