(function () {
  document.querySelectorAll('[data-course-ai]').forEach(function (app) {
    var apiBase = String(window.COURSE_AI_API_BASE || '').replace(/\/$/, '');
    var form = app.querySelector('[data-chat-form]');
    var input = app.querySelector('[data-chat-input]');
    var log = app.querySelector('[data-chat-log]');
    var fileInput = app.querySelector('[data-file-input]');
    var fileList = app.querySelector('[data-file-list]');
    var mode = app.querySelector('[data-chat-mode]');
    var welcomeCopy = app.querySelector('[data-welcome-copy]');
    var welcome = app.querySelector('.welcome-block');
    var gate = app.querySelector('[data-login-gate]');
    var loginForm = app.querySelector('[data-login-form]');
    var loginError = app.querySelector('[data-login-error]');
    var logout = app.querySelector('[data-logout]');
    var connection = app.querySelector('[data-connection-state]');
    var tokenKey = 'course-ai-preview-login:' + (app.dataset.courseName || 'course');
    var token = '';
    try { token = sessionStorage.getItem(tokenKey) || ''; } catch (error) {}

    function api(path, options) {
      options = options || {};
      options.headers = Object.assign({'Content-Type': 'application/json'}, options.headers || {});
      if (token) options.headers.Authorization = 'Bearer ' + token;
      return fetch(apiBase + path, options);
    }

    function appendMessage(text, role) {
      var message = document.createElement('div');
      message.className = 'message message-' + role;
      message.textContent = text;
      log.appendChild(message);
      log.scrollTop = log.scrollHeight;
      return message;
    }

    function setAuthenticated(ok) {
      gate.hidden = ok;
      logout.hidden = !ok;
      if (connection) connection.textContent = ok ? '课程助教已登录' : '需要登录';
      app.classList.toggle('is-authenticated', ok);
    }

    async function checkSession() {
      setAuthenticated(token === 'admin');
    }

    loginForm.addEventListener('submit', function (event) {
      event.preventDefault();
      loginError.textContent = '';
      var submit = loginForm.querySelector('[type="submit"]');
      submit.disabled = true;
      var data = Object.fromEntries(new FormData(loginForm).entries());
      if (data.username !== 'admin' || data.password !== 'admin') {
        loginError.textContent = '账号或密码错误。'; submit.disabled = false; return;
      }
      token = 'admin';
      try { sessionStorage.setItem(tokenKey, token); } catch (error) {}
      loginForm.reset(); setAuthenticated(true); input.focus(); submit.disabled = false;
    });

    logout.addEventListener('click', function () {
      token = '';
      try { sessionStorage.removeItem(tokenKey); } catch (error) {}
      setAuthenticated(false);
    });

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
              group.classList.remove('open');
              var trigger = group.querySelector('.feature-button');
              if (trigger) trigger.setAttribute('aria-expanded', 'false');
            });
            if (shouldOpen) {
              selectedGroup.classList.add('open');
              button.setAttribute('aria-expanded', 'true');
            }
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
      welcome.hidden = false; input.value = ''; input.focus();
    });

    form.addEventListener('submit', async function (event) {
      event.preventDefault();
      var question = input.value.trim(); if (!question || form.dataset.busy === 'true') return;
      appendMessage(question, 'user'); welcome.hidden = true; input.value = ''; form.dataset.busy = 'true';
      var answer = appendMessage('', 'assistant');
      try {
        var response = await api('/api/chat/stream', {method: 'POST', body: JSON.stringify({question: question, skill: mode.textContent})});
        if (response.status === 401) { setAuthenticated(false); throw new Error('设备验证已失效，请重新验证'); }
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
        var sourceBox = document.createElement('div'); sourceBox.className = 'source-list';
        sourceBox.textContent = sources.length ? '课程来源：' + sources.map(function (s) { return s.title + (s.locator ? '（' + s.locator + '）' : ''); }).join('；') : '以下内容主要依据一般会计知识，而非课程指定材料。';
        log.appendChild(sourceBox);
      } catch (error) { answer.textContent = error.message || '回答服务暂时不可用，请稍后重试。'; }
      finally { form.dataset.busy = 'false'; input.focus(); }
    });

    input.addEventListener('keydown', function (event) {
      if (event.key === 'Enter' && !event.shiftKey) { event.preventDefault(); form.requestSubmit(); }
    });
    fileInput.addEventListener('change', function () {
      fileList.innerHTML = '';
      Array.prototype.slice.call(fileInput.files, 0, 5).forEach(function (file) {
        var item = document.createElement('li'); item.textContent = file.name + ' · 提交接口将在第五阶段开放'; fileList.appendChild(item);
      });
    });
    checkSession();
  });
}());
