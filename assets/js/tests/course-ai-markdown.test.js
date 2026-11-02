const test = require('node:test');
const assert = require('node:assert/strict');

class Node {
  constructor(tag, value = '') { this.tag = tag; this.value = value; this.children = []; }
  appendChild(child) { this.children.push(child); return child; }
  append(...children) { children.forEach(child => this.appendChild(child)); }
  replaceChildren(...children) { this.children = children.flatMap(child => child.tag === '#fragment' ? child.children : [child]); }
  set textContent(value) { this.children = [new Node('#text', String(value))]; }
  get textContent() { return this.tag === '#text' ? this.value : this.children.map(child => child.textContent).join(''); }
}
global.document = {
  createElement: tag => new Node(tag),
  createTextNode: value => new Node('#text', value),
  createDocumentFragment: () => new Node('#fragment')
};
global.window = {};
require('../course-ai-markdown.js');

function nodes(source) {
  const root = new Node('div');
  window.CourseAiMarkdown.renderInto(root, source);
  return root;
}
function descendants(root, tag) {
  return root.children.flatMap(child => [child, ...descendants(child, tag)]).filter(child => child.tag === tag);
}

test('turns reply structure into headings, paragraphs, emphasis and lists', () => {
  const root = nodes('## 核心观点\n\n先看 **证据**。\n\n1. 第一项\n2. 第二项');
  assert.equal(root.children[0].tag, 'h4');
  assert.equal(descendants(root, 'strong')[0].textContent, '证据');
  assert.deepEqual(descendants(root, 'li').map(item => item.textContent), ['第一项', '第二项']);
  assert.equal(root.textContent.includes('**'), false);
});

test('keeps raw HTML and dangerous links as text instead of markup', () => {
  const root = nodes('<script>alert(1)</script> [click](javascript:alert(1)) [资料](https://example.org/a)');
  assert.equal(descendants(root, 'script').length, 0);
  assert.equal(descendants(root, 'a').length, 1);
  assert.equal(descendants(root, 'a')[0].href, 'https://example.org/a');
  assert.match(root.textContent, /<script>/);
  assert.match(root.textContent, /javascript:/);
});

test('renders code fences and tables without interpreting their content', () => {
  const root = nodes('```python\nprint("<unsafe>")\n```\n\n| 指标 | 说明 |\n| --- | --- |\n| AIQ | 质量 |');
  assert.equal(descendants(root, 'pre')[0].textContent, 'print("<unsafe>")');
  assert.equal(descendants(root, 'table').length, 1);
  assert.deepEqual(descendants(root, 'th').map(item => item.textContent), ['指标', '说明']);
});

test('replaces streamed content rather than appending duplicate paragraphs', () => {
  const root = nodes('**分析');
  window.CourseAiMarkdown.renderInto(root, '**分析**\n\n结论。');
  assert.equal(descendants(root, 'strong')[0].textContent, '分析');
  assert.equal(descendants(root, 'p').length, 2);
});
