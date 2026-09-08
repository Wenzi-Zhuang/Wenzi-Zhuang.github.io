---
title: Zhuang, Wenzi
---

<link rel="stylesheet" href="../../../assets/css/course-ai.css?v=20260908-3">

<main class="chat-workspace" data-course-ai data-course-name="会计学">
  <section class="login-gate" data-login-gate>
    <form class="login-card" data-login-form>
      <div class="assistant-avatar">会</div>
      <h2>登录课程助教</h2>
      <p>请输入管理员账号和密码。</p>
      <label>账号<input name="username" autocomplete="username" required></label>
      <label>密码<input name="password" type="password" autocomplete="current-password" required></label>
      <p class="form-error" data-login-error role="alert"></p>
      <button type="submit">登录</button>
    </form>
  </section>
  <aside class="chat-sidebar">
    <div class="sidebar-top">
      <a class="workspace-back" href="/teaching.html">← 返回课程列表</a>
      <h1>会计学</h1>
      <button class="new-chat-button" type="button" data-new-chat>＋ 新对话</button>
    </div>

    <nav class="feature-nav" aria-label="课程功能">
      <p class="sidebar-label">功能</p>
      <div class="feature-group">
        <button class="feature-button active" type="button" data-feature="课程须知" data-intro="请选择需要了解的课程内容。" aria-expanded="false">课程须知</button>
        <div class="feature-subnav">
          <button type="button" data-feature="教学大纲">教学大纲</button>
          <button type="button" data-feature="考核要求">考核要求</button>
          <button type="button" data-feature="会计与生活">会计与生活</button>
          <button type="button" data-feature="会计与职业发展">会计与职业发展</button>
        </div>
      </div>
      <button class="feature-button" type="button" data-feature="知识点学习">知识点学习</button>
      <button class="feature-button" type="button" data-feature="练习与测试">练习与测试</button>
      <button class="feature-button" type="button" data-feature="复习">复习</button>
      <button class="feature-button" type="button" data-feature="资料提交" data-upload-trigger>资料提交</button>
    </nav>

    <section class="chat-history" aria-label="对话记录">
      <p class="sidebar-label">对话记录</p>
      <button class="history-item active" type="button">欢迎使用课程助教</button>
      <p class="history-empty">更多对话将在后端接入后保存</p>
    </section>

    <div class="sidebar-footer"><span class="connection-dot"></span><span data-connection-state>正在连接课程服务器</span></div>
  </aside>

  <section class="chat-main">
    <header class="chat-header">
      <div><span class="mobile-course-name">会计学</span><strong data-chat-mode>课程须知</strong></div>
      <button class="preview-badge logout-button" type="button" data-logout hidden>退出登录</button>
    </header>

    <div class="conversation" data-chat-log aria-live="polite">
      <div class="welcome-block">
        <div class="assistant-avatar">会</div>
        <h2>会计学 AI 助教</h2>
        <p data-welcome-copy>请选择左侧功能，或直接输入你的会计问题。</p>
        <div class="starter-grid">
          <button type="button" data-prompt>解释权责发生制</button>
          <button type="button" data-prompt>这项业务应该如何编制分录？</button>
          <button type="button" data-prompt>给我一道资产负债表练习</button>
        </div>
      </div>
    </div>

    <div class="chat-composer-wrap">
      <ul class="file-list composer-files" data-file-list></ul>
      <form class="chat-composer" data-chat-form>
        <label class="attach-button" title="选择资料">＋<span class="sr-only">选择资料</span><input type="file" multiple data-file-input accept=".pdf,.doc,.docx,.txt,.md,.png,.jpg,.jpeg,.csv,.xlsx"></label>
        <textarea data-chat-input aria-label="输入课程问题" placeholder="输入问题，Enter 发送，Shift + Enter 换行"></textarea>
        <button class="round-send" type="submit" aria-label="发送">↑</button>
      </form>
      <p class="composer-note">回答由 NAS 课程资料库与 DeepSeek 生成；请核对重要会计判断。</p>
    </div>
  </section>
</main>

<script src="../../../assets/js/course-ai-config.js"></script>
<script src="../../../assets/js/course-ai.js?v=20260908-3" defer></script>
