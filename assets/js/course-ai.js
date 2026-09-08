(function () {
  document.querySelectorAll('[data-course-ai]').forEach(function (app) {
    var form = app.querySelector('[data-chat-form]');
    var input = app.querySelector('[data-chat-input]');
    var log = app.querySelector('[data-chat-log]');
    var fileInput = app.querySelector('[data-file-input]');
    var fileList = app.querySelector('[data-file-list]');
    var mode = app.querySelector('[data-chat-mode]');
    var welcomeCopy = app.querySelector('[data-welcome-copy]');
    var welcome = app.querySelector('.welcome-block');

    function appendMessage(text, role) {
      var message = document.createElement('div');
      message.className = 'message message-' + role;
      message.textContent = text;
      log.appendChild(message);
      log.scrollTop = log.scrollHeight;
    }

    app.querySelectorAll('[data-prompt]').forEach(function (button) {
      button.addEventListener('click', function () {
        input.value = button.textContent.trim();
        input.focus();
      });
    });

    app.querySelectorAll('[data-feature]').forEach(function (button) {
      button.addEventListener('click', function () {
        app.querySelectorAll('[data-feature]').forEach(function (item) {
          item.classList.remove('active');
        });
        button.classList.add('active');
        mode.textContent = button.dataset.feature;
        welcomeCopy.textContent = button.dataset.intro || '已切换至“' + button.dataset.feature + '”。你可以直接输入问题开始互动。';
        if (button.hasAttribute('data-upload-trigger')) fileInput.click();
      });
    });

    app.querySelector('[data-new-chat]').addEventListener('click', function () {
      log.querySelectorAll('.message').forEach(function (message) { message.remove(); });
      welcome.hidden = false;
      input.value = '';
      input.focus();
    });

    form.addEventListener('submit', function (event) {
      event.preventDefault();
      var question = input.value.trim();
      if (!question) return;

      appendMessage(question, 'user');
      welcome.hidden = true;
      input.value = '';
      window.setTimeout(function () {
        appendMessage('问题已在前端收到。DeepSeek 与 NAS 知识库尚未连接，完成后我会在这里返回基于课程资料的回答。', 'assistant');
      }, 280);
    });

    input.addEventListener('keydown', function (event) {
      if (event.key === 'Enter' && !event.shiftKey) {
        event.preventDefault();
        form.requestSubmit();
      }
    });

    fileInput.addEventListener('change', function () {
      fileList.innerHTML = '';
      Array.prototype.slice.call(fileInput.files, 0, 5).forEach(function (file) {
        var item = document.createElement('li');
        item.textContent = file.name + ' · 待连接 NAS 后上传';
        fileList.appendChild(item);
      });
    });
  });
}());
