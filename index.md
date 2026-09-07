<button id="language-toggle" type="button" aria-label="Switch to English" aria-controls="content-zh content-en">English</button>

<section id="content-zh" lang="zh-CN">
  <h2>庄汶资</h2>

  <p><a href="teaching.md">教学</a> &#8195;&#8195; <a href="https://papers.ssrn.com/sol3/cf_dev/AbsByAuth.cfm?per_id=4592798">SSRN</a> &#8195;&#8195; <a href="https://kjxy.dufe.edu.cn/content_82157.html">东北财经大学个人主页</a></p>

  <p>东北财经大学会计学院副教授。本科毕业于中央财经大学，博士毕业于中国人民大学。主要研究领域为财务会计与审计，重点关注会计准则、计量、行为与信息的经济后果。已在同行评审期刊发表多篇论文。2022年获普华永道“3535”最佳论文奖。</p>

  <h3>联系方式</h3>
  <ul>
    <li>电子邮箱：<a href="mailto:zhuangwenzi@dufe.edu.cn">zhuangwenzi@dufe.edu.cn</a></li>
    <li>办公时间：请通过电子邮件预约。</li>
    <li>办公室：师道斋101室</li>
  </ul>
</section>

<section id="content-en" lang="en" hidden>
  <h2>Zhuang, Wenzi</h2>

  <p><a href="teaching.md">Teaching</a> &#8195;&#8195; <a href="https://papers.ssrn.com/sol3/cf_dev/AbsByAuth.cfm?per_id=4592798">SSRN</a> &#8195;&#8195; <a href="https://kjxy.dufe.edu.cn/content_82157.html">DUFE Personal Website</a></p>

  <p>Zhuang Wenzi is an associate professor of accounting at Dongbei University of Finance and Economics (DUFE). He holds an undergraduate degree from Central University of Finance and Economics and master's and Ph.D. degrees from Renmin University of China. Before joining DUFE in 2024, he taught at Sun Yat-sen University. His research focuses on financial accounting and auditing, particularly the real effects of accounting standards, measurement, behavior, and information. He has published several articles in peer-reviewed journals. In 2022, he received the PwC 3535 Best Paper Award.</p>

  <h3>Contact Information</h3>
  <ul>
    <li>Email: <a href="mailto:zhuangwenzi@dufe.edu.cn">zhuangwenzi@dufe.edu.cn</a></li>
    <li>Office hours: Please email for an appointment.</li>
  </ul>
</section>

<style>
  #language-toggle {
    float: right;
    margin: 0 0 1rem 1rem;
    padding: 0.3rem 0.75rem;
    color: inherit;
    font: inherit;
    background: transparent;
    border: 1px solid #d0d7de;
    border-radius: 6px;
    cursor: pointer;
  }

  #language-toggle:hover {
    background: #f6f8fa;
  }
</style>

<script>
  (function () {
    var toggle = document.getElementById('language-toggle');
    var contentZh = document.getElementById('content-zh');
    var contentEn = document.getElementById('content-en');

    function setLanguage(language) {
      var showEnglish = language === 'en';
      contentZh.hidden = showEnglish;
      contentEn.hidden = !showEnglish;
      toggle.textContent = showEnglish ? '中文' : 'English';
      toggle.setAttribute('aria-label', showEnglish ? '切换到中文' : 'Switch to English');
      toggle.setAttribute('aria-pressed', String(showEnglish));
      document.documentElement.lang = showEnglish ? 'en' : 'zh-CN';
    }

    var language = 'zh';
    try {
      language = localStorage.getItem('homepage-language') || 'zh';
    } catch (error) {}
    setLanguage(language);

    toggle.addEventListener('click', function () {
      var nextLanguage = contentEn.hidden ? 'en' : 'zh';
      setLanguage(nextLanguage);
      try {
        localStorage.setItem('homepage-language', nextLanguage);
      } catch (error) {}
    });
  }());
</script>
