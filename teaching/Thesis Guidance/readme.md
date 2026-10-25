---
title: 案例论文指导
---

<link rel="stylesheet" href="../../assets/css/course-ai.css?v=20261025-unified-chat">

<main class="chat-workspace" data-course-ai data-course-name="案例论文" data-assistant-id="case_study">
  <aside class="chat-sidebar">
    <div class="sidebar-top">
      <a class="workspace-back" href="/teaching.html">← 返回教学</a>
      <h1>案例论文指导</h1>
      <button class="new-chat-button" type="button" data-new-chat>＋ 新对话</button>
    </div>
    <nav class="feature-nav" aria-label="论文指导功能">
      <p class="sidebar-label">论文指导</p>
      <button class="feature-button active" type="button" data-feature="论文互动指导" data-case-tab="chat" data-intro="可以讨论案例选择、分析框架、证据组织和论文表达。">AI 互动问答</button>
      <button class="feature-button" type="button" data-feature="格式检查" data-case-tab="format">格式检查</button>
      <button class="feature-button" type="button" data-feature="内容检查" data-case-tab="content">内容检查</button>
      <button class="feature-button" type="button" data-feature="论文提交" data-case-tab="submit">论文提交</button>
    </nav>
    <section class="chat-history" aria-label="历史对话">
      <p class="sidebar-label">历史对话</p>
      <div data-thread-list></div>
    </section>
    <div class="sidebar-footer"><span class="connection-dot"></span><span data-connection-state>正在连接</span></div>
  </aside>
  <section class="chat-main">
    <header class="chat-header">
      <div><span class="mobile-course-name">本科 / 硕士 · 论文指导</span><strong data-chat-mode>论文互动指导</strong></div>
      <span class="user-badge" data-user-name></span>
    </header>
    <div class="conversation" data-chat-log aria-live="polite">
      <div class="welcome-block">
        <div class="assistant-avatar">案</div>
        <h2>案例论文 AI 助手</h2>
        <p data-welcome-copy>可以讨论案例选择、分析框架、证据组织和论文表达。</p>
        <div class="starter-grid">
          <button type="button" data-prompt>如何选择有研究价值的案例？</button>
          <button type="button" data-prompt>案例证据与研究结论如何对应？</button>
          <button type="button" data-prompt>怎样改进案例论文的论证结构？</button>
        </div>
      </div>
    </div>
    <div class="case-workflow" data-case-workflow hidden>
      <div class="case-workflow-inner">
        <p class="case-step-label">案例论文 · 本科毕业论文</p>
        <h2 data-case-title>格式检查</h2>
        <p class="case-workflow-lead" data-case-description>依据本科毕业论文写作规范第三部分，逐项检查 Word 文档。不能由程序可靠确认的版面项目会标注“复核”，不会被算作通过。</p>
        <div class="case-file-grid">
          <label>清洁版论文 Word（必选）<input type="file" accept=".docx" data-case-paper></label>
          <label>案例类毕业论文自评表（内容检查和提交必选）<input type="file" accept=".docx" data-case-evaluation></label>
        </div>
        <p class="case-file-note">文件只在正式提交后保存在 NAS。请选择 Word .docx 文档；如文件超过处理上限，系统会给出提示。</p>
        <section class="case-panel" data-case-panel="format">
          <button type="button" class="case-primary" data-case-action="format">开始逐项格式检查</button>
          <div class="case-result" data-case-result="format" aria-live="polite"></div>
        </section>
        <section class="case-panel" data-case-panel="content" hidden>
          <button type="button" class="case-primary" data-case-action="content">开始内容检查</button>
          <div class="case-result" data-case-result="content" aria-live="polite"></div>
        </section>
        <section class="case-panel" data-case-panel="submit" hidden>
          <p class="case-submit-note">必须先对当前版本完成格式检查、内容检查。正式提交至少包含清洁版论文和自评表；其他文件按需附上。</p>
          <div class="case-file-grid">
            <label>修订模式论文（选填）<input type="file" accept=".docx" data-case-revision></label>
            <label>修改说明（选填）<input type="file" accept=".docx" data-case-explanation></label>
            <label>学生邮箱（选填）<input type="email" autocomplete="email" data-case-email placeholder="name@example.com"></label>
          </div>
          <p class="case-file-note">文件名须为“姓名+学号+清洁版论文/修订模式论文/自评表/修改说明.docx”，可用“+”“_”或空格分隔。</p>
          <button type="button" class="case-primary" data-case-action="submit">校验并提交论文</button>
          <div class="case-result" data-case-result="submit" aria-live="polite"></div>
        </section>
      </div>
    </div>
    <div class="chat-composer-wrap">
      <ul class="file-list composer-files" data-file-list></ul>
      <form class="chat-composer" data-chat-form>
        <label class="attach-button" title="选择文档">＋<span class="sr-only">选择文档</span><input type="file" multiple data-file-input accept=".pdf,.docx,.txt,.md,.csv"></label>
        <textarea data-chat-input aria-label="输入论文问题" placeholder="输入论文问题，Enter 发送，Shift + Enter 换行" required></textarea>
        <button class="round-send" type="submit" aria-label="发送">↑</button>
      </form>
      <p class="form-error" data-chat-error role="alert"></p>
      <p class="composer-note">文档摘录会随问题发送给 DeepSeek，请先移除敏感信息。</p>
    </div>
  </section>
</main>

<script src="../../assets/js/course-ai-config.js?v=20261025-4"></script>
<script src="../../assets/js/course-ai.js?v=20261025-quiet-status" defer></script>
<script src="../../assets/js/case-study-workflow.js?v=20261025-1" defer></script>
