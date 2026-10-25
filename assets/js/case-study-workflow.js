(function () {
  var app = document.querySelector('[data-course-ai][data-assistant-id="case_study"]');
  if (!app) return;
  var main = app.querySelector('.chat-main');
  var workflow = app.querySelector('[data-case-workflow]');
  var log = app.querySelector('[data-chat-log]');
  var composer = app.querySelector('.chat-composer-wrap');
  var paperInput = app.querySelector('[data-case-paper]');
  var evaluationInput = app.querySelector('[data-case-evaluation]');
  var apiBase = String(window.COURSE_AI_API_BASE || '').replace(/\/$/, '');
  var titles = {format: '格式检查', content: '内容检查', submit: '论文提交'};
  var descriptions = {
    format: '依据本科毕业论文写作规范第三部分，逐项检查 Word 文档。不能由程序可靠确认的版面项目会标注“复核”，不会被算作通过。',
    content: '依据案例论文选题指南和本科论文结构规范检查；请同时提交填写完整的案例类毕业论文自评表。',
    submit: '校验当前版本是否完成前两项检查、核对文件名后，保存至 NAS 并生成教师初审草稿。'
  };

  function section(tab) {
    main.classList.toggle('case-mode', tab !== 'chat');
    workflow.hidden = tab === 'chat';
    log.hidden = tab !== 'chat';
    composer.hidden = tab !== 'chat';
    if (tab === 'chat') return;
    workflow.querySelector('[data-case-title]').textContent = titles[tab];
    workflow.querySelector('[data-case-description]').textContent = descriptions[tab];
    workflow.querySelectorAll('[data-case-panel]').forEach(function (panel) {
      panel.hidden = panel.dataset.casePanel !== tab;
    });
    workflow.scrollTop = 0;
  }

  app.querySelectorAll('[data-case-tab]').forEach(function (button) {
    button.addEventListener('click', function () { section(button.dataset.caseTab); });
  });
  section('chat');

  function textNode(tag, value, className) {
    var node = document.createElement(tag);
    node.textContent = value;
    if (className) node.className = className;
    return node;
  }

  function file(input, label) {
    if (!input.files || !input.files[0]) throw new Error('请先选择' + label + '。');
    if (input.files[0].size > 1024 * 1024) throw new Error('文件过大，无法处理：单个文档不能超过 1 MB。');
    if (!/\.docx$/i.test(input.files[0].name)) throw new Error(label + '须为 Word .docx 文档。');
    return input.files[0];
  }

  async function post(path, body) {
    var token = localStorage.getItem('course-ai-device-token:case_study');
    if (!token) throw new Error('请先登录案例论文平台。');
    var response = await fetch(apiBase + path, {
      method: 'POST', headers: {Authorization: 'Bearer ' + token}, body: body
    });
    var data = await response.json().catch(function () { return {}; });
    if (!response.ok) throw new Error(data.detail || '暂时无法处理，请稍后重试。');
    return data;
  }

  function resetResults() {
    workflow.querySelectorAll('[data-case-result]').forEach(function (target) { target.replaceChildren(); });
  }
  paperInput.addEventListener('change', resetResults);
  evaluationInput.addEventListener('change', function () {
    workflow.querySelector('[data-case-result="content"]').replaceChildren();
    workflow.querySelector('[data-case-result="submit"]').replaceChildren();
  });

  function renderFormat(target, data) {
    var counts = data.summary || {};
    target.appendChild(textNode('h3', '逐项格式检查结果'));
    target.appendChild(textNode('p', '已检查 ' + (data.items || []).length + ' 项：通过 ' + (counts['通过'] || 0) + '，需修改 ' + (counts['需修改'] || 0) + '，待人工复核 ' + (counts['复核'] || 0) + '。', 'case-summary'));
    target.appendChild(textNode('p', data.notice || '', 'case-caution'));
    var list = document.createElement('ol'); list.className = 'case-check-list';
    (data.items || []).forEach(function (item) {
      var li = document.createElement('li');
      var head = textNode('div', item.code + '　' + item.requirement);
      var badge = textNode('span', item.status, 'case-status case-status-' + item.status);
      head.appendChild(badge); li.appendChild(head);
      li.appendChild(textNode('p', item.evidence)); list.appendChild(li);
    });
    target.appendChild(list);
    target.appendChild(textNode('h3', 'AI 文字核查补充'));
    target.appendChild(textNode('div', data.ai_notes || '', 'case-review-text'));
  }

  function renderContent(target, data) {
    target.appendChild(textNode('h3', '内容检查结果'));
    target.appendChild(textNode('p', data.notice || '', 'case-caution'));
    var list = document.createElement('ul'); list.className = 'case-structure-list';
    (data.structure || []).forEach(function (item) {
      list.appendChild(textNode('li', (item.found ? '已定位' : '未定位') + ' · ' + item.name + ' — ' + item.note));
    });
    target.appendChild(list);
    target.appendChild(textNode('h3', 'AI 初步意见'));
    target.appendChild(textNode('div', data.ai_review || '', 'case-review-text'));
  }

  function renderSubmit(target, data) {
    target.appendChild(textNode('h3', data.message || '提交成功'));
    target.appendChild(textNode('p', '提交编号：' + data.submission_id, 'case-summary'));
    target.appendChild(textNode('p', '可以关闭此页面。NAS 会继续初审并保存教师邮箱草稿，不依赖你的电脑或教师网页登录。', 'case-caution'));
    var status = textNode('p', '初审排队中；邮箱草稿待处理。', 'case-summary');
    target.appendChild(status);
    var checks = 0;
    async function refresh() {
      if (++checks > 24) return;
      try {
        var token = localStorage.getItem('course-ai-device-token:case_study');
        if (!token) return;
        var response = await fetch(apiBase + '/api/case-study/submissions/' + data.submission_id,
          {headers: {Authorization: 'Bearer ' + token}});
        if (!response.ok) return;
        var state = await response.json();
        var reviewLabel = {pending: '初审排队中', processing: '初审中', retry: '初审稍后重试',
          done: '初审草稿已生成', failed: '初审未完成，请联系教师'}[state.review_status] || '初审状态待确认';
        var mailLabel = {pending: '邮箱草稿待处理', processing: '正在保存邮箱草稿', retry: '邮箱草稿稍后重试',
          awaiting_configuration: '教师邮箱尚未配置，草稿保存在 NAS', saved: '已保存到教师 DUFE 草稿箱',
          failed: '邮箱草稿未保存，请联系教师'}[state.mail_status] || '邮箱状态待确认';
        status.textContent = reviewLabel + '；' + mailLabel + '。';
        if (state.review_status !== 'failed' && state.mail_status !== 'saved' && state.mail_status !== 'failed')
          window.setTimeout(refresh, 5000);
      } catch (_) { window.setTimeout(refresh, 5000); }
    }
    window.setTimeout(refresh, 5000);
  }

  workflow.querySelectorAll('[data-case-action]').forEach(function (button) {
    button.addEventListener('click', async function () {
      var action = button.dataset.caseAction;
      var target = workflow.querySelector('[data-case-result="' + action + '"]');
      target.replaceChildren();
      try {
        var body = new FormData();
        body.append('file', file(paperInput, '清洁版论文'));
        if (action !== 'format') body.append('self_eval', file(evaluationInput, '案例类毕业论文自评表'));
        if (action === 'submit') {
          var revision = app.querySelector('[data-case-revision]');
          var explanation = app.querySelector('[data-case-explanation]');
          if (revision.files[0]) body.append('revision', file(revision, '修订模式论文'));
          if (explanation.files[0]) body.append('explanation', file(explanation, '修改说明'));
          body.append('email', app.querySelector('[data-case-email]').value.trim());
        }
        button.disabled = true;
        target.appendChild(textNode('p', '正在检查与处理，请稍候…', 'case-working'));
        var data = await post('/api/case-study/' + ({format: 'format-check', content: 'content-check', submit: 'submit'}[action]), body);
        target.replaceChildren();
        if (action === 'format') renderFormat(target, data);
        if (action === 'content') renderContent(target, data);
        if (action === 'submit') renderSubmit(target, data);
      } catch (error) {
        target.replaceChildren(textNode('p', error.message || '暂时无法处理，请稍后重试。', 'case-error'));
      } finally { button.disabled = false; }
    });
  });
}());
