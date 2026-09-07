---
title: Zhuang, Wenzi
---

<link rel="stylesheet" href="/assets/css/course-ai.css">

<main class="site-shell course-ai" data-course-ai>
  <header class="site-header">
    <a class="site-brand" href="/" aria-label="返回首页"><span class="brand-mark">WZ</span><span><strong>庄汶资</strong><small>Wenzi Zhuang</small></span></a>
    <nav class="site-nav" aria-label="主要导航"><a href="/">首页</a><a href="/research.html">研究</a><a class="active" href="/teaching.html">教学</a></nav>
  </header>

  <nav class="course-topbar" aria-label="课程导航">
    <a class="course-home" href="/teaching.html">← 返回课程列表</a>
    <div class="course-status" aria-label="服务连接状态">
      <span class="status-pill">DeepSeek · 待连接</span>
      <span class="status-pill">NAS 知识库 · 待连接</span>
    </div>
  </nav>

  <header class="course-hero">
    <p class="course-kicker">AI Course Studio</p>
    <h1 class="course-title">实证方法与论文写作</h1>
    <p class="course-intro">面向本科生的课程 AI 助教。未来将结合课程知识库与研究 Skills，辅助选题、研究设计、文献阅读和论文表达。</p>
  </header>

  <div class="course-layout">
    <section class="ai-panel" aria-labelledby="assistant-title">
      <div class="panel-heading">
        <h2 id="assistant-title">课程 AI 助教</h2>
        <span class="demo-label">前端预览</span>
      </div>
      <div class="chat-log" data-chat-log aria-live="polite">
        <div class="message message-assistant">你好，我是“实证方法与论文写作”课程助教。你可以从研究问题、变量设计或论文结构开始提问。</div>
      </div>
      <div class="suggestions" aria-label="示例问题">
        <button class="prompt-chip" type="button" data-prompt>如何把兴趣转化为研究问题？</button>
        <button class="prompt-chip" type="button" data-prompt>解释双重差分的基本逻辑</button>
        <button class="prompt-chip" type="button" data-prompt>帮我检查论文结构</button>
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
          <li class="resource-item"><strong>研究文献</strong><span>论文、阅读笔记与参考书目</span></li>
          <li class="resource-item"><strong>案例与模板</strong><span>研究设计、变量定义与写作示例</span></li>
        </ul>
      </section>

      <section class="side-card">
        <h2>Research Skills</h2>
        <p class="side-copy">未来由 NAS 加载可复用的研究工作流。</p>
        <ul class="skill-list">
          <li class="skill-item"><strong>研究设计诊断</strong><span>识别研究问题与识别策略</span></li>
          <li class="skill-item"><strong>文献阅读助手</strong><span>梳理论点、方法与研究贡献</span></li>
          <li class="skill-item"><strong>论文表达检查</strong><span>检查结构、逻辑与学术表达</span></li>
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

  <footer class="site-footer"><span>© 2026 Wenzi Zhuang</span><span>AI Course Studio · Frontend Preview</span></footer>
</main>

<script src="/assets/js/course-ai.js" defer></script>
