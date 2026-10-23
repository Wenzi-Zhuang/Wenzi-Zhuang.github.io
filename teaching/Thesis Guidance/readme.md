---
title: 毕业论文指导
---

<link rel="stylesheet" href="../../assets/css/course-ai.css?v=20261023-1">

<main class="thesis-workspace" data-thesis-ai>
  <header class="thesis-header">
    <a href="/teaching.html">← 返回教学</a>
    <div><span>本科毕业论文</span><h1>论文格式 AI 检查</h1></div>
    <span class="preview-badge">无需登录</span>
  </header>

  <section class="thesis-grid">
    <aside class="thesis-guide">
      <p class="eyebrow">Workflow</p>
      <h2>提交前检查</h2>
      <ol><li>上传 DOCX 原稿（推荐）或 PDF</li><li>粘贴学院格式要求</li><li>运行结构与格式检查</li><li>按优先级修改后重新检查</li></ol>
      <div class="privacy-note"><strong>隐私说明</strong><p>文件经 NAS 后端解析后发送必要文本给 DeepSeek，不发送姓名和学号。请勿上传含敏感个人信息的附件。</p></div>
    </aside>

    <section class="thesis-panel">
      <div class="thesis-intro"><span class="assistant-avatar">论</span><div><h2>毕业论文指导助手</h2><p>先做可验证的程序检查，再由 DeepSeek 根据你提供的学院要求给出修改清单。</p></div></div>
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
  </section>
</main>

<script src="../../assets/js/course-ai-config.js"></script>
<script src="../../assets/js/thesis-ai.js?v=20261023-1" defer></script>
