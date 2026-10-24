---
title: 实证论文指导
---

<link rel="stylesheet" href="../../assets/css/course-ai.css?v=20261025-4">

<main class="chat-workspace" data-course-ai data-course-name="实证论文" data-assistant-id="empirical_study">
  <aside class="chat-sidebar">
    <div class="sidebar-top">
      <a class="workspace-back" href="/teaching.html">← 返回教学</a>
      <h1>实证论文指导</h1>
      <button class="new-chat-button" type="button" data-new-chat>＋ 新对话</button>
    </div>
    <nav class="feature-nav" aria-label="论文指导功能">
      <p class="sidebar-label">论文指导</p>
      <button class="feature-button active" type="button" data-feature="论文互动指导" data-intro="可以讨论研究问题、假设、变量、识别策略和结果解释。">AI 互动问答</button>
    </nav>
    <section class="chat-history" aria-label="历史对话">
      <p class="sidebar-label">历史对话</p>
      <div data-thread-list></div>
    </section>
    <div class="sidebar-footer"><span class="connection-dot"></span><span data-connection-state>正在连接课程服务器</span></div>
  </aside>
  <section class="chat-main">
    <header class="chat-header">
      <div><span class="mobile-course-name">本科 / 硕士 · 论文指导</span><strong data-chat-mode>论文互动指导</strong></div>
      <span class="user-badge" data-user-name></span>
    </header>
    <div class="conversation" data-chat-log aria-live="polite">
      <div class="welcome-block">
        <div class="assistant-avatar">实</div>
        <h2>实证论文 AI 助手</h2>
        <p data-welcome-copy>可以讨论研究问题、假设、变量、识别策略和结果解释。</p>
        <div class="starter-grid">
          <button type="button" data-prompt>如何把研究问题转化为可检验假设？</button>
          <button type="button" data-prompt>如何判断识别策略是否可信？</button>
          <button type="button" data-prompt>如何解释实证结果而不过度推断？</button>
        </div>
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
      <p class="composer-note">每平台每小时最多 50 问、每天 150 问；每天最多 10 个文档，单个 500 KB、累计 1500 KB。文档摘录会随问题发送给 DeepSeek，请先移除敏感信息。</p>
    </div>
  </section>
</main>

<script src="../../assets/js/course-ai-config.js?v=20261025-4"></script>
<script src="../../assets/js/course-ai.js?v=20261025-4" defer></script>
