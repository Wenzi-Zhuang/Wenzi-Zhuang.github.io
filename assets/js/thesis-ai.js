(function () {
  var app = document.querySelector('[data-thesis-ai]'); if (!app) return;
  var apiBase = String(window.COURSE_AI_API_BASE || '').replace(/\/$/, '');
  var thesisForm = app.querySelector('[data-thesis-form]');
  var fileInput = app.querySelector('[data-thesis-file]');
  var fileName = app.querySelector('[data-file-name]');
  var checkError = app.querySelector('[data-check-error]');
  var result = app.querySelector('[data-thesis-result]');

  fileInput.addEventListener('change', function () { fileName.textContent = fileInput.files[0] ? fileInput.files[0].name : '选择或拖入论文文件'; });
  thesisForm.addEventListener('submit', async function (event) {
    event.preventDefault(); checkError.textContent = ''; result.hidden = true;
    var submit = thesisForm.querySelector('[type="submit"]'); submit.disabled = true; submit.textContent = '正在检查，请稍候…';
    try {
      var payload = new FormData(thesisForm);
      if (apiBase.indexOf('YOUR_') !== -1) throw new Error('论文检查服务器域名尚未配置');
      var response = await fetch(apiBase + '/api/thesis/check', {method: 'POST', body: payload});
      var body = await response.json();
      if (!response.ok) throw new Error(body.detail || '检查失败');
      var summary = app.querySelector('[data-check-summary]'); summary.innerHTML = '';
      body.checks.forEach(function (item) {
        var row = document.createElement('div'); row.className = 'check-item check-' + item.level;
        var title = document.createElement('strong'); title.textContent = item.item;
        var detail = document.createElement('p'); detail.textContent = item.detail;
        row.appendChild(title); row.appendChild(detail); summary.appendChild(row);
      });
      app.querySelector('[data-analysis]').textContent = body.analysis;
      app.querySelector('[data-limitations]').textContent = body.limitations;
      result.hidden = false; result.scrollIntoView({behavior: 'smooth', block: 'start'});
    } catch (error) { checkError.textContent = error.message || '检查服务暂时不可用'; }
    finally { submit.disabled = false; submit.textContent = '开始检查'; }
  });
}());
