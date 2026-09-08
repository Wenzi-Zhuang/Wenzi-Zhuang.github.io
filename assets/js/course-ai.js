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
    var tokenKey = 'course-ai-device-token';
    var token = '';
    try { token = localStorage.getItem(tokenKey) || ''; } catch (error) {}

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
      connection.textContent = ok ? 'NAS 课程资料库已连接' : '需要设备验证';
      app.classList.toggle('is-authenticated', ok);
    }

    async function checkSession() {
      if (!token || apiBase.indexOf('YOUR_') !== -1) return setAuthenticated(false);
      try {
        var response = await api('/api/auth/me');
        if (!response.ok) throw new Error();
        setAuthenticated(true);
      } catch (error) {
        token = '';
        try { localStorage.removeItem(tokenKey); } catch (storageError) {}
        setAuthenticated(false);
      }
    }

    loginForm.addEventListener('submit', async function (event) {
      event.preventDefault();
      loginError.textContent = '';
      var submit = loginForm.querySelector('[type="submit"]');
      submit.disabled = true;
      if (apiBase.indexOf('YOUR_') !== -1) {
        loginError.textContent = '课程服务器域名尚未配置。'; submit.disabled = false; return;
      }
      var data = Object.fromEntries(new FormData(loginForm).entries());
      data.platform = navigator.platform || '';
      data.language = navigator.language || '';
      data.timezone = Intl.DateTimeFormat().resolvedOptions().timeZone || '';
      try {
        var response = await api('/api/auth/register-device', {method: 'POST', body: JSON.stringify(data)});
        var result = await response.json();
        if (!response.ok) throw new Error(result.detail || '验证失败');
        token = result.device_token;
        localStorage.setItem(tokenKey, token);
        loginForm.reset(); setAuthenticated(true); input.focus();
      } catch (error) { loginError.textContent = error.message || '无法连接课程服务器'; }
      finally { submit.disabled = false; }
    });

    logout.addEventListener('click', async function () {
      try { await api('/api/auth/logout', {method: 'POST'}); } catch (error) {}
      token = ''; localStorage.removeItem(tokenKey); setAuthenticated(false);
    });

    app.querySelectorAll('[data-prompt]').forEach(function (button) {
      button.addEventListener('click', function () { input.value = button.textContent.trim(); input.focus(); });
    });
    app.querySelectorAll('[data-feature]').forEach(function (button) {
      button.addEventListener('click', function () {
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
