(function () {
  document.querySelectorAll('[data-course-ai]').forEach(function (app) {
    var apiBase = String(window.COURSE_AI_API_BASE || '').replace(/\/$/, '');
    var assistantId = app.dataset.assistantId;
    var tokenKey = 'course-ai-device-token:' + assistantId;
    var token = localStorage.getItem(tokenKey) || '';
    localStorage.removeItem('course-ai-device-token');
    var form = app.querySelector('[data-chat-form]');
    var input = app.querySelector('[data-chat-input]');
    var log = app.querySelector('[data-chat-log]');
    var fileInput = app.querySelector('[data-file-input]');
    var fileList = app.querySelector('[data-file-list]');
    var mode = app.querySelector('[data-chat-mode]');
    var welcome = app.querySelector('.welcome-block');
    var errorBox = app.querySelector('[data-chat-error]');
    var threadList = app.querySelector('[data-thread-list]');
    var nameBadge = app.querySelector('[data-user-name]');
    var connection = app.querySelector('[data-connection-state]');
    var currentThread = '';
    var messages = [];
    var attachments = [];
    var user = null;
    var activeRequest = null;

    var gate = document.createElement('div');
    gate.className = 'auth-gate';
    gate.innerHTML = '<section class="auth-card"><a href="/teaching.html">← 返回教学</a><p class="auth-eyebrow">课程 AI 平台</p><h2></h2><p class="auth-description">每门课程需分别注册和登录；此浏览器再次进入本课程时会自动登录。</p>' +
      '<form data-login-form><label>学号 / 账号<input name="student_no" autocomplete="username" required></label><label>身份证后六位 / 口令<input name="id_last6" type="password" autocomplete="current-password" required></label><button type="submit">登录</button><button type="button" class="auth-link" data-show-register>首次进入本课程？注册</button></form>' +
      '<form data-register-form hidden><label>学号<input name="student_no" inputmode="numeric" pattern="[0-9]{5,20}" required></label><label>身份证后六位<input name="id_last6" type="password" inputmode="numeric" pattern="[0-9]{6}" maxlength="6" required></label><button type="submit">核对信息</button><button type="button" class="auth-link" data-show-login>返回登录</button></form>' +
      '<div data-register-confirm hidden><h3>请核对注册信息</h3><dl><dt>学号</dt><dd data-confirm-no></dd><dt>姓名</dt><dd data-confirm-name></dd><dt>班级</dt><dd data-confirm-class></dd><dt>身份证后六位</dt><dd data-confirm-last6></dd></dl><button type="button" data-confirm-register>确认注册</button><button type="button" class="auth-link" data-back-register>返回修改</button></div>' +
      '<p class="form-error" data-auth-error role="alert"></p></section>';
    gate.querySelector('h2').textContent = app.dataset.courseName || 'AI 互动';
    app.appendChild(gate);
    var loginForm = gate.querySelector('[data-login-form]');
    var registerForm = gate.querySelector('[data-register-form]');
    var confirmBox = gate.querySelector('[data-register-confirm]');
    var authError = gate.querySelector('[data-auth-error]');
    var preview = null;

    function showGate(view) {
      app.classList.remove('authenticated');
      gate.hidden = false;
      loginForm.hidden = view !== 'login';
      registerForm.hidden = view !== 'register';
      confirmBox.hidden = view !== 'confirm';
      authError.textContent = '';
    }
    function authHeaders() { return {Authorization: 'Bearer ' + token}; }
    async function requestJSON(path, options) {
      var response = await fetch(apiBase + path, options || {});
      var body = await response.json().catch(function () { return {}; });
      if (!response.ok) throw new Error(body.detail || '服务暂时不可用，请稍后重试');
      return body;
    }
    function jsonOptions(method, body, authorized) {
      var headers = {'Content-Type': 'application/json'};
      if (authorized) headers.Authorization = 'Bearer ' + token;
      return {method: method, headers: headers, body: JSON.stringify(body)};
    }
    function newId() {
      if (crypto.randomUUID) return crypto.randomUUID().replace(/-/g, '');
      return Array.from(crypto.getRandomValues(new Uint8Array(16))).map(function (item) { return item.toString(16).padStart(2, '0'); }).join('');
    }

    gate.querySelector('[data-show-register]').addEventListener('click', function () { showGate('register'); });
    gate.querySelector('[data-show-login]').addEventListener('click', function () { showGate('login'); });
    gate.querySelector('[data-back-register]').addEventListener('click', function () { showGate('register'); });
    registerForm.addEventListener('submit', async function (event) {
      event.preventDefault(); authError.textContent = '';
      var values = new FormData(registerForm);
      try {
        preview = await requestJSON('/api/auth/preview', jsonOptions('POST', {
          assistant_id: assistantId, student_no: String(values.get('student_no')).trim(), id_last6: String(values.get('id_last6')).trim()
        }));
        ['no', 'name', 'class', 'last6'].forEach(function (key) {
          gate.querySelector('[data-confirm-' + key + ']').textContent = preview[{no: 'student_no', name: 'name', class: 'class_name', last6: 'id_last6'}[key]];
        });
        showGate('confirm');
      } catch (error) { authError.textContent = error.message; }
    });
    gate.querySelector('[data-confirm-register]').addEventListener('click', async function () {
      if (!preview) return;
      try {
        await requestJSON('/api/auth/register', jsonOptions('POST', {
          assistant_id: assistantId, student_no: preview.student_no, id_last6: preview.id_last6
        }));
        loginForm.elements.student_no.value = preview.student_no;
        loginForm.elements.id_last6.value = '';
        preview = null;
        showGate('login');
        authError.textContent = '本课程注册成功，请登录。';
      } catch (error) { authError.textContent = error.message; }
    });
    loginForm.addEventListener('submit', async function (event) {
      event.preventDefault(); authError.textContent = '';
      var values = new FormData(loginForm);
      try {
        var result = await requestJSON('/api/auth/login', jsonOptions('POST', {
          assistant_id: assistantId, student_no: String(values.get('student_no')).trim(),
          id_last6: String(values.get('id_last6')).trim(), previous_token: token
        }));
        token = result.token;
        localStorage.setItem(tokenKey, token);
        loginForm.elements.id_last6.value = '';
        await enter(result);
      } catch (error) { authError.textContent = error.message; }
    });

    function appendMessage(text, role) {
      var item = document.createElement('div');
      item.className = 'message message-' + role;
      item.textContent = text;
      log.appendChild(item);
      log.scrollTop = log.scrollHeight;
      return item;
    }
    function appendProgress() {
      var item = document.createElement('div');
      item.className = 'message message-progress';
      item.setAttribute('role', 'status');
      var pulse = document.createElement('span');
      pulse.className = 'progress-pulse';
      pulse.setAttribute('aria-hidden', 'true');
      var label = document.createElement('span');
      label.className = 'progress-label';
      label.textContent = '搜索中';
      var timer = document.createElement('span');
      timer.className = 'progress-timer';
      timer.setAttribute('aria-hidden', 'true');
      timer.textContent = '0 秒';
      item.append(pulse, label, timer);
      log.appendChild(item);
      log.scrollTop = log.scrollHeight;
      var started = performance.now();
      var stopped = false;
      var interval = window.setInterval(function () {
        timer.textContent = Math.floor((performance.now() - started) / 1000) + ' 秒';
      }, 250);
      var transition = window.setTimeout(function () {
        label.textContent = '思考中';
      }, (3 + Math.floor(Math.random() * 4)) * 1000);
      return {
        stop: function () {
          if (stopped) return;
          stopped = true;
          window.clearInterval(interval);
          window.clearTimeout(transition);
          item.remove();
        }
      };
    }
    function cancelPending() {
      if (!activeRequest) return;
      activeRequest.cancelled = true;
      activeRequest.controller.abort();
      activeRequest.progress.stop();
      activeRequest = null;
      form.dataset.busy = 'false';
    }
    function clearLog() {
      log.querySelectorAll('.message, .source-list').forEach(function (item) { item.remove(); });
      welcome.hidden = false;
      errorBox.textContent = '';
    }
    function renderMessages() {
      clearLog();
      messages.forEach(function (item) { appendMessage(item.content, item.role); });
      welcome.hidden = messages.length > 0;
    }
    function resetChat() {
      cancelPending();
      currentThread = '';
      messages = [];
      attachments = [];
      fileList.innerHTML = '';
      input.value = '';
      renderMessages();
      threadList.querySelectorAll('.history-item').forEach(function (item) { item.classList.remove('active'); });
      input.focus();
    }
    async function openThread(id) {
      cancelPending();
      try {
        var item = await requestJSON('/api/assistants/' + assistantId + '/threads/' + id, {headers: authHeaders()});
        currentThread = id;
        messages = item.messages || [];
        attachments = [];
        fileList.innerHTML = '';
        renderMessages();
        threadList.querySelectorAll('.history-item').forEach(function (button) { button.classList.toggle('active', button.dataset.threadId === id); });
      } catch (error) { errorBox.textContent = error.message; }
    }
    async function loadThreads(openLatest) {
      var data = await requestJSON('/api/assistants/' + assistantId + '/threads', {headers: authHeaders()});
      threadList.innerHTML = '';
      if (!data.threads.length) {
        var empty = document.createElement('p'); empty.className = 'history-empty';
        empty.textContent = '暂无历史对话'; threadList.appendChild(empty);
      }
      data.threads.forEach(function (item) {
        var button = document.createElement('button');
        button.type = 'button'; button.className = 'history-item';
        button.dataset.threadId = item.id; button.textContent = item.title;
        button.addEventListener('click', function () { openThread(item.id); });
        threadList.appendChild(button);
      });
      if (openLatest && data.threads.length) await openThread(data.threads[0].id);
      else threadList.querySelectorAll('.history-item').forEach(function (item) { item.classList.toggle('active', item.dataset.threadId === currentThread); });
    }
    async function saveThread() {
      if (!currentThread) currentThread = newId();
      var title = (messages.find(function (item) { return item.role === 'user'; }) || {}).content || '新对话';
      await requestJSON('/api/assistants/' + assistantId + '/threads/' + currentThread,
        jsonOptions('PUT', {title: title.slice(0, 36), messages: messages.slice(-80)}, true));
      await loadThreads(false);
    }
    async function enter(profile) {
      user = profile;
      gate.hidden = true;
      app.classList.add('authenticated');
      nameBadge.textContent = profile.name;
      var logout = nameBadge.querySelector('button');
      if (!logout) {
        logout = document.createElement('button'); logout.type = 'button'; logout.textContent = '退出';
        logout.addEventListener('click', async function () {
          try { await requestJSON('/api/auth/logout', {method: 'POST', headers: authHeaders()}); } catch (_) {}
          token = ''; user = null; localStorage.removeItem(tokenKey);
          resetChat(); showGate('login');
        });
        nameBadge.appendChild(logout);
      }
      if (connection) connection.textContent = '已连接';
      resetChat();
      try { await loadThreads(true); } catch (error) { errorBox.textContent = '历史对话暂时无法载入：' + error.message; }
    }

    app.querySelector('[data-new-chat]').addEventListener('click', resetChat);
    app.querySelectorAll('[data-prompt]').forEach(function (button) {
      button.addEventListener('click', function () { input.value = button.textContent.trim(); input.focus(); });
    });
    app.querySelectorAll('[data-feature]').forEach(function (button) {
      button.addEventListener('click', function () {
        var group = button.closest('.feature-group');
        if (group && button.classList.contains('feature-button')) {
          var open = !group.classList.contains('open');
          app.querySelectorAll('.feature-group').forEach(function (item) { item.classList.remove('open'); });
          group.classList.toggle('open', open);
        }
        app.querySelectorAll('[data-feature]').forEach(function (item) { item.classList.remove('active'); });
        button.classList.add('active'); mode.textContent = button.dataset.feature;
        var copy = app.querySelector('[data-welcome-copy]');
        if (copy) copy.textContent = button.dataset.intro || '你可以直接输入问题开始互动。';
        if (button.hasAttribute('data-upload-trigger')) fileInput.click();
      });
    });
    fileInput.addEventListener('change', async function () {
      errorBox.textContent = '';
      for (var file of Array.from(fileInput.files)) {
        if (file.size > 500 * 1024) { errorBox.textContent = '文件过大，无法处理：单个文件不能超过 500 KB。'; continue; }
        var item = document.createElement('li'); item.textContent = file.name + ' · 正在处理'; fileList.appendChild(item);
        try {
          var payload = new FormData(); payload.append('file', file);
          var data = await requestJSON('/api/assistants/' + assistantId + '/files', {
            method: 'POST', headers: authHeaders(), body: payload
          });
          attachments.push(data); item.textContent = file.name + ' · 已就绪';
        } catch (error) { item.remove(); errorBox.textContent = error.message; }
      }
      fileInput.value = '';
    });
    form.addEventListener('submit', async function (event) {
      event.preventDefault();
      var question = input.value.trim();
      if (!question || form.dataset.busy === 'true' || !user) return;
      errorBox.textContent = ''; form.dataset.busy = 'true';
      var files = attachments.slice();
      var visibleQuestion = question + (files.length ? '\n\n附加文档：' + files.map(function (item) { return item.filename; }).join('、') : '');
      var extra = files.map(function (item) { return '[文档 ' + item.filename + ']\n' + item.text; }).join('\n\n').slice(0, 9000);
      var outgoing = messages.slice(-10).map(function (item) { return {role: item.role, content: item.content}; });
      outgoing.push({role: 'user', content: question + (extra ? '\n\n以下是我提交的文档摘录，请结合回答：\n' + extra : '')});
      while (outgoing.reduce(function (n, item) { return n + item.content.length; }, 0) > 15500 && outgoing.length > 1) outgoing.shift();
      welcome.hidden = true;
      appendMessage(visibleQuestion, 'user');
      var progress = appendProgress();
      var controller = new AbortController();
      var request = {cancelled: false, controller: controller, progress: progress};
      activeRequest = request;
      input.value = '';
      var answer = null;
      try {
        var response = await fetch(apiBase + '/api/assistants/' + assistantId + '/chat/stream',
          Object.assign(jsonOptions('POST', {messages: outgoing, mode: mode.textContent}, true), {signal: controller.signal}));
        if (request.cancelled) return;
        if (!response.ok) {
          var failure = await response.json().catch(function () { return {}; });
          throw new Error(failure.detail || '暂时无法回答，请稍后再试');
        }
        if (!response.body) throw new Error('暂时无法接收回答，请稍后再试');
        var reader = response.body.getReader(), decoder = new TextDecoder(), buffer = '', sources = [];
        var answerText = '';
        while (true) {
          var chunk = await reader.read(); if (chunk.done) break;
          if (request.cancelled) return;
          buffer += decoder.decode(chunk.value, {stream: true});
          var packets = buffer.split('\n\n'); buffer = packets.pop();
          packets.forEach(function (packet) {
            var eventName = (packet.match(/^event: (.+)$/m) || [])[1];
            var raw = (packet.match(/^data: (.+)$/m) || [])[1]; if (!raw) return;
            var data = JSON.parse(raw);
            if (eventName === 'token') {
              answerText += data.text || '';
              if (!answer && answerText.trim()) { progress.stop(); answer = appendMessage(answerText, 'assistant'); }
              else if (answer) answer.textContent = answerText;
            }
            if (eventName === 'meta') sources = data.sources || [];
            if (eventName === 'error') throw new Error(data.message);
            log.scrollTop = log.scrollHeight;
          });
        }
        if (!answer || !answer.textContent.trim()) throw new Error('AI 未返回回答，请稍后重试');
        messages.push({role: 'user', content: visibleQuestion}, {role: 'assistant', content: answer.textContent});
        attachments = []; fileList.innerHTML = '';
        if (sources.length) {
          var sourceBox = document.createElement('div'); sourceBox.className = 'source-list';
          sourceBox.textContent = 'NAS 资料来源：' + sources.map(function (item) { return item.title; }).join('；'); log.appendChild(sourceBox);
        }
        try { await saveThread(); } catch (saveError) { errorBox.textContent = '回答已生成，但历史记录保存失败：' + saveError.message; }
      } catch (error) {
        if (request.cancelled) return;
        progress.stop();
        if (answer) answer.textContent = '回答中断：' + (error.message || '暂时无法回答');
        else appendMessage(error.message || '暂时无法回答', 'assistant');
        if (!input.value.trim()) input.value = question;
      } finally {
        progress.stop();
        if (activeRequest === request) {
          activeRequest = null;
          form.dataset.busy = 'false';
          input.focus();
        }
      }
    });
    input.addEventListener('keydown', function (event) {
      if (event.key === 'Enter' && !event.shiftKey) { event.preventDefault(); form.requestSubmit(); }
    });

    showGate('login');
    if (token) requestJSON('/api/auth/me?assistant_id=' + encodeURIComponent(assistantId), {headers: authHeaders()})
      .then(enter).catch(function () { token = ''; localStorage.removeItem(tokenKey); showGate('login'); });
  });
}());
