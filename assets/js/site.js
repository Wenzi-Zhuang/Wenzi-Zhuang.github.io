(function () {
  var page = document.querySelector('[data-language-page]');
  var toggle = document.querySelector('[data-language-toggle]');
  if (!page || !toggle) return;

  function setLanguage(language) {
    var english = language === 'en';
    page.querySelectorAll('[data-zh]').forEach(function (element) { element.hidden = english; });
    page.querySelectorAll('[data-en]').forEach(function (element) { element.hidden = !english; });
    toggle.textContent = english ? '中' : 'EN';
    toggle.setAttribute('aria-label', english ? '切换到中文' : 'Switch to English');
    document.documentElement.lang = english ? 'en' : 'zh-CN';
  }

  var language = 'zh';
  try { language = localStorage.getItem('homepage-language') || 'zh'; } catch (error) {}
  setLanguage(language);

  toggle.addEventListener('click', function () {
    var next = page.querySelector('[data-en]').hidden ? 'en' : 'zh';
    setLanguage(next);
    try { localStorage.setItem('homepage-language', next); } catch (error) {}
  });
}());
