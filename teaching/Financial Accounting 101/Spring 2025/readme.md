---
title: Zhuang, Wenzi
---

<link rel="stylesheet" href="/assets/css/course-ai.css">

<main class="course-ai" data-course-ai>
  <nav class="course-topbar" aria-label="课程导航">
    <a class="course-home" href="/teaching.html">← 返回课程列表</a>
    <div class="course-status" aria-label="服务连接状态">
      <span class="status-pill">DeepSeek · 待连接</span>
      <span class="status-pill">NAS 知识库 · 待连接</span>
    </div>
  </nav>

  <header class="course-hero">
    <p class="course-kicker">AI Course Studio</p>
    <h1 class="course-title">会计学</h1>
    <p class="course-intro">面向本科生的课程 AI 助教。未来将结合课程知识库与会计 Skills，辅助理解准则、分析业务、编制分录和巩固练习。</p>
  </header>

  <div class="course-layout">
    <section class="ai-panel" aria-labelledby="assistant-title">
      <div class="panel-heading">
        <h2 id="assistant-title">课程 AI 助教</h2>
        <span class="demo-label">前端预览</span>
      </div>
      <div class="chat-log" data-chat-log aria-live="polite">
        <div class="message message-assistant">你好，我是“会计学”课程助教。你可以提问会计要素、账务处理、报表关系或课程练习。</div>
      </div>
      <div class="suggestions" aria-label="示例问题">
        <button class="prompt-chip" type="button" data-prompt>解释权责发生制</button>
        <button class="prompt-chip" type="button" data-prompt>这项业务应该如何编制分录？</button>
        <button class="prompt-chip" type="button" data-prompt>给我一道资产负债表练习</button>
      </div>
      <form class="composer" data-chat-form>
        <textarea data-chat-input aria-label="输入课程问题" placeholder="输入问题，Enter 发送，Shift + Enter 换行"></textarea>
        <button class="send-button" type="submit">发送</button>
      </form>
    </section>

    <aside class="side-stack" aria-label="课程资源">
      <section class="side-card">
        <h2>课程知识库</h2>
        <p class="side-copy">未来从 NAS 检索与回答问题相关的课程资料。</p>
        <ul class="resource-list">
          <li class="resource-item"><strong>课程材料</strong><span>教学大纲、课件与课程要求</span></li>
          <li class="resource-item"><strong>会计准则</strong><span>准则条文、应用指南与解释</span></li>
          <li class="resource-item"><strong>例题与案例</strong><span>业务场景、会计分录与报表练习</span></li>
        </ul>
      </section>

      <section class="side-card">
        <h2>Accounting Skills</h2>
        <p class="side-copy">未来由 NAS 加载可复用的会计学习工作流。</p>
        <ul class="skill-list">
          <li class="skill-item"><strong>业务分析</strong><span>识别交易实质与受影响科目</span></li>
          <li class="skill-item"><strong>分录辅导</strong><span>分步骤解释确认与计量逻辑</span></li>
          <li class="skill-item"><strong>练习生成</strong><span>按知识点生成题目与反馈</span></li>
        </ul>
      </section>

      <section class="side-card">
        <h2>提交学习资料</h2>
        <p class="side-copy">选择希望补充到课程知识库的文件。</p>
        <label class="upload-zone">
          <strong>选择本地文件</strong>
          PDF、Word、图片或数据文件
          <input type="file" multiple data-file-input accept=".pdf,.doc,.docx,.txt,.md,.png,.jpg,.jpeg,.csv,.xlsx">
        </label>
        <ul class="file-list" data-file-list></ul>
        <p class="privacy-note">当前仅显示文件名，不会上传或保存；NAS 接入后再启用资料收集。</p>
      </section>
    </aside>
  </div>
</main>

<script src="/assets/js/course-ai.js" defer></script>
