---
title: 案例论文指导
---

<link rel="stylesheet" href="../../assets/css/course-ai.css?v=20261024-1">

<main class="thesis-workspace" data-thesis-ai data-assistant-id="case_study">
  <header class="thesis-header">
    <a href="/teaching.html">← 返回教学</a>
    <div><span>本科 / 硕士 · 毕业论文指导</span><h1>案例论文 AI 指导</h1></div>
    <span class="preview-badge">无需登录</span>
  </header>

  <section class="thesis-grid">
    <aside class="thesis-guide">
      <p class="eyebrow">Workflow</p>
      <h2>论文指导</h2>
      <nav class="thesis-tools" aria-label="论文指导功能">
        <button class="active" type="button" data-thesis-tab="chat">AI 互动问答</button>
        <button type="button" data-thesis-tab="check">论文格式检查</button>
      </nav>
      <ol><li>先粘贴学院格式要求</li><li>随时向 AI 助手提问</li><li>上传 DOCX 或 PDF 检查</li><li>修改后重新运行检查</li></ol>
      <div class="privacy-note"><strong>隐私说明</strong><p>文件由 NAS 后端解析，提取的论文正文（最多前 30000 字）会发送给 DeepSeek。系统不会额外附加姓名或学号，但文件正文中若含有这些信息，也可能随正文发送。提交前请移除敏感个人信息。</p></div>
    </aside>

    <section class="thesis-panel" data-thesis-section="check" hidden>
      <div class="thesis-intro"><span class="assistant-avatar">案</span><div><h2>案例论文格式检查</h2><p>先做可验证的程序检查，再由 DeepSeek 根据你提供的学院要求给出修改清单。</p></div></div>
      <form data-thesis-form>
        <label class="drop-zone" data-drop-zone>
          <input type="file" name="file" accept=".docx,.pdf" required data-thesis-file>
          <strong data-file-name>选择或拖入论文文件</strong><span>支持 DOCX、PDF，推荐 DOCX；最大 50MB</span>
        </label>
        <label class="requirements-field"><span>学院或学校格式要求</span><textarea name="requirements" rows="7" placeholder="粘贴格式规范，例如纸张、页边距、字体、行距、摘要、标题编号、参考文献格式……"></textarea></label>
        <p class="form-error" data-check-error role="alert"></p>
        <button class="check-button" type="submit">开始检查</button>
      </form>
      <section class="thesis-result" data-thesis-result hidden aria-live="polite">
        <h2>检查结果</h2>
        <div class="check-summary" data-check-summary></div>
        <div class="analysis-copy" data-analysis></div>
        <p class="result-limitation" data-limitations></p>
      </section>
    </section>

    <section class="thesis-panel thesis-chat-panel" data-thesis-section="chat">
      <div class="thesis-intro"><span class="assistant-avatar">案</span><div><h2>案例论文 AI 助手</h2><p>可以询问案例选择、案例分析框架、证据组织、格式规范和修改方法；助手不会代写研究结论。</p></div></div>
      <label class="requirements-field compact"><span>学院或学校格式要求（可选，会作为本次对话依据）</span><textarea rows="4" data-chat-requirements placeholder="粘贴学校论文格式要求；未提供时，助手会明确说明无法判断学校专用规定。"></textarea></label>
      <div class="thesis-chat-log" data-thesis-chat-log aria-live="polite">
        <div class="thesis-chat-welcome">
          <p>你好，我可以协助你梳理案例论文的结构、论证与格式要求。</p>
          <div class="thesis-starters">
            <button type="button" data-thesis-prompt>如何选择有研究价值的案例？</button>
            <button type="button" data-thesis-prompt>案例论文的分析框架如何组织？</button>
            <button type="button" data-thesis-prompt>案例证据与研究结论如何对应？</button>
          </div>
        </div>
      </div>
      <form class="thesis-chat-form" data-thesis-chat-form>
        <textarea data-thesis-chat-input rows="2" maxlength="8000" placeholder="输入你的论文问题，Enter 发送，Shift + Enter 换行" required></textarea>
        <button type="submit" aria-label="发送">↑</button>
      </form>
      <p class="form-error" data-chat-error role="alert"></p>
      <p class="composer-note">AI 建议仅供修改参考，最终格式以学院正式文件和教师审核为准。</p>
    </section>
  </section>
</main>

<script src="../../assets/js/course-ai-config.js?v=20261025-1"></script>
<script src="../../assets/js/thesis-ai.js?v=20261024-1" defer></script>
