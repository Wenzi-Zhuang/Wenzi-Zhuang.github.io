(function () {
  var app = document.querySelector('[data-thesis-ai]'); if (!app) return;
  var apiBase = String(window.COURSE_AI_API_BASE || '').replace(/\/$/, '');
  var thesisForm = app.querySelector('[data-thesis-form]');
  var fileInput = app.querySelector('[data-thesis-file]');
  var fileName = app.querySelector('[data-file-name]');
  var checkError = app.querySelector('[data-check-error]');
  var result = app.querySelector('[data-thesis-result]');
  var chatForm = app.querySelector('[data-thesis-chat-form]');
  var chatInput = app.querySelector('[data-thesis-chat-input]');
  var chatLog = app.querySelector('[data-thesis-chat-log]');
  var chatError = app.querySelector('[data-chat-error]');
  var conversation = [];

  app.querySelectorAll('[data-thesis-tab]').forEach(function (button) {
    button.addEventListener('click', function () {
      app.querySelectorAll('[data-thesis-tab]').forEach(function (item) { item.classList.toggle('active', item === button); });
      app.querySelectorAll('[data-thesis-section]').forEach(function (section) { section.hidden = section.dataset.thesisSection !== button.dataset.thesisTab; });
    });
  });

  function appendChat(text, role) {
    var message = document.createElement('div'); message.className = 'thesis-message thesis-message-' + role;
    message.textContent = text; chatLog.appendChild(message); chatLog.scrollTop = chatLog.scrollHeight; return message;
  }

  app.querySelectorAll('[data-thesis-prompt]').forEach(function (button) {
    button.addEventListener('click', function () { chatInput.value = button.textContent.trim(); chatInput.focus(); });
  });

  chatForm.addEventListener('submit', async function (event) {
    event.preventDefault();
    var question = chatInput.value.trim(); if (!question || chatForm.dataset.busy === 'true') return;
    chatError.textContent = ''; chatForm.dataset.busy = 'true'; chatInput.value = '';
    var welcome = chatLog.querySelector('.thesis-chat-welcome'); if (welcome) welcome.hidden = true;
    appendChat(question, 'user'); conversation.push({role: 'user', content: question});
    conversation = conversation.slice(-11);
    var answer = appendChat('', 'assistant');
    try {
      if (apiBase.indexOf('YOUR_') !== -1) throw new Error('论文指导服务器域名尚未配置');
      var requirements = app.querySelector('[data-chat-requirements]').value.trim();
      var response = await fetch(apiBase + '/api/thesis/chat/stream', {
        method: 'POST', headers: {'Content-Type': 'application/json'},
        body: JSON.stringify({messages: conversation, requirements: requirements})
      });
      if (!response.ok) { var failure = await response.json(); throw new Error(failure.detail || '回答失败'); }
      var reader = response.body.getReader(), decoder = new TextDecoder(), buffer = '';
      while (true) {
        var chunk = await reader.read(); if (chunk.done) break;
        buffer += decoder.decode(chunk.value, {stream: true});
        var packets = buffer.split('\n\n'); buffer = packets.pop();
        packets.forEach(function (packet) {
          var eventName = (packet.match(/^event: (.+)$/m) || [])[1];
          var raw = (packet.match(/^data: (.+)$/m) || [])[1]; if (!raw) return;
          var data = JSON.parse(raw);
          if (eventName === 'token') answer.textContent += data.text;
          if (eventName === 'error') throw new Error(data.message);
          chatLog.scrollTop = chatLog.scrollHeight;
        });
      }
      conversation.push({role: 'assistant', content: answer.textContent}); conversation = conversation.slice(-12);
    } catch (error) {
      answer.remove(); conversation.pop(); chatError.textContent = error.message || '论文指导服务暂时不可用';
    } finally { chatForm.dataset.busy = 'false'; chatInput.focus(); }
  });

  chatInput.addEventListener('keydown', function (event) {
    if (event.key === 'Enter' && !event.shiftKey) { event.preventDefault(); chatForm.requestSubmit(); }
  });

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
