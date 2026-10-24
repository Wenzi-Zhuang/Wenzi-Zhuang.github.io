(function () {
  document.querySelectorAll('[data-course-ai]').forEach(function (app) {
    var apiBase = String(window.COURSE_AI_API_BASE || '').replace(/\/$/, '');
    var assistantId = app.dataset.assistantId;
    var form = app.querySelector('[data-chat-form]');
    var input = app.querySelector('[data-chat-input]');
    var log = app.querySelector('[data-chat-log]');
    var fileInput = app.querySelector('[data-file-input]');
    var fileList = app.querySelector('[data-file-list]');
    var mode = app.querySelector('[data-chat-mode]');
    var welcomeCopy = app.querySelector('[data-welcome-copy]');
    var welcome = app.querySelector('.welcome-block');
    var connection = app.querySelector('[data-connection-state]');
    var conversation = [];
    if (connection) connection.textContent = 'DeepSeek / NAS 公共与专属知识库';

    function appendMessage(text, role) {
      var message = document.createElement('div'); message.className = 'message message-' + role;
      message.textContent = text; log.appendChild(message); log.scrollTop = log.scrollHeight; return message;
    }
    app.querySelectorAll('[data-prompt]').forEach(function (button) {
      button.addEventListener('click', function () { input.value = button.textContent.trim(); input.focus(); });
    });
    app.querySelectorAll('[data-feature]').forEach(function (button) {
      button.addEventListener('click', function () {
        if (button.classList.contains('feature-button')) {
          var selectedGroup = button.closest('.feature-group');
          if (selectedGroup) {
            var shouldOpen = !selectedGroup.classList.contains('open');
            app.querySelectorAll('.feature-group').forEach(function (group) {
              group.classList.remove('open'); var trigger = group.querySelector('.feature-button');
              if (trigger) trigger.setAttribute('aria-expanded', 'false');
            });
            if (shouldOpen) { selectedGroup.classList.add('open'); button.setAttribute('aria-expanded', 'true'); }
          }
        }
        app.querySelectorAll('[data-feature]').forEach(function (item) { item.classList.remove('active'); });
        button.classList.add('active'); mode.textContent = button.dataset.feature;
        welcomeCopy.textContent = button.dataset.intro || '已切换至“' + button.dataset.feature + '”。你可以直接输入问题开始互动。';
        if (button.hasAttribute('data-upload-trigger')) fileInput.click();
      });
    });
    app.querySelector('[data-new-chat]').addEventListener('click', function () {
      log.querySelectorAll('.message, .source-list').forEach(function (message) { message.remove(); });
      conversation = []; welcome.hidden = false; input.value = ''; input.focus();
    });

    form.addEventListener('submit', async function (event) {
      event.preventDefault();
      var question = input.value.trim(); if (!question || form.dataset.busy === 'true') return;
      if (!assistantId) return appendMessage('页面尚未配置 AI 助手 ID。', 'assistant');
      appendMessage(question, 'user'); welcome.hidden = true; input.value = ''; form.dataset.busy = 'true';
      conversation.push({role: 'user', content: question}); conversation = conversation.slice(-11);
      var answer = appendMessage('', 'assistant');
      try {
        if (apiBase.indexOf('YOUR_') !== -1) throw new Error('NAS API 域名尚未配置');
        var response = await fetch(apiBase + '/api/assistants/' + encodeURIComponent(assistantId) + '/chat/stream', {
          method: 'POST', headers: {'Content-Type': 'application/json'},
          body: JSON.stringify({messages: conversation, mode: mode.textContent})
        });
        if (!response.ok) { var failure = await response.json(); throw new Error(failure.detail || '回答失败'); }
        var reader = response.body.getReader(), decoder = new TextDecoder(), buffer = '', sources = [];
        while (true) {
          var chunk = await reader.read(); if (chunk.done) break;
          buffer += decoder.decode(chunk.value, {stream: true});
          var packets = buffer.split('\n\n'); buffer = packets.pop();
          packets.forEach(function (packet) {
            var eventName = (packet.match(/^event: (.+)$/m) || [])[1];
            var raw = (packet.match(/^data: (.+)$/m) || [])[1]; if (!raw) return;
            var data = JSON.parse(raw);
            if (eventName === 'token') answer.textContent += data.text;
            if (eventName === 'meta') sources = data.sources || [];
            if (eventName === 'error') throw new Error(data.message);
            log.scrollTop = log.scrollHeight;
          });
        }
        conversation.push({role: 'assistant', content: answer.textContent}); conversation = conversation.slice(-12);
        var sourceBox = document.createElement('div'); sourceBox.className = 'source-list';
        sourceBox.textContent = sources.length ? 'NAS 资料来源：' + sources.map(function (source) { return source.title; }).join('；') : '本次未检索到匹配的 NAS 专属资料，回答主要依据一般知识。';
        log.appendChild(sourceBox);
      } catch (error) { answer.textContent = error.message || '回答服务暂时不可用，请稍后重试。'; conversation.pop(); }
      finally { form.dataset.busy = 'false'; input.focus(); }
    });
    input.addEventListener('keydown', function (event) {
      if (event.key === 'Enter' && !event.shiftKey) { event.preventDefault(); form.requestSubmit(); }
    });
    fileInput.addEventListener('change', function () {
      fileList.innerHTML = '';
      Array.prototype.slice.call(fileInput.files, 0, 5).forEach(function (file) {
        var item = document.createElement('li'); item.textContent = file.name + ' · 文件互动将在后续阶段接入'; fileList.appendChild(item);
      });
    });
  });
}());
