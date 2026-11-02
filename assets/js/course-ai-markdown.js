(function () {
  'use strict';

  // Render a deliberately small Markdown subset with DOM nodes, never innerHTML.
  // AI replies and uploaded documents are untrusted text.
  function inline(parent, source) {
    var text = String(source || '');
    var buffer = '';
    function flush() {
      if (buffer) { parent.appendChild(document.createTextNode(buffer)); buffer = ''; }
    }
    for (var i = 0; i < text.length;) {
      var char = text[i];
      if (char === '\\' && i + 1 < text.length && /[\\`*_\[\]()>#+.!|~-]/.test(text[i + 1])) {
        buffer += text[i + 1]; i += 2; continue;
      }
      if (char === '\n') { flush(); parent.appendChild(document.createElement('br')); i++; continue; }
      if (char === '`') {
        var ticks = (text.slice(i).match(/^`+/) || ['`'])[0];
        var endCode = text.indexOf(ticks, i + ticks.length);
        if (endCode !== -1) {
          flush(); var code = document.createElement('code');
          code.textContent = text.slice(i + ticks.length, endCode).trim();
          parent.appendChild(code); i = endCode + ticks.length; continue;
        }
      }
      if (char === '[' && (i === 0 || text[i - 1] !== '!')) {
        var link = text.slice(i).match(/^\[([^\]\n]+)\]\((https?:\/\/[^\s)]+)\)/i);
        if (link) {
          try {
            var url = new URL(link[2]);
            if (url.protocol === 'http:' || url.protocol === 'https:') {
              flush(); var anchor = document.createElement('a');
              anchor.href = url.href; anchor.target = '_blank'; anchor.rel = 'noopener noreferrer';
              anchor.textContent = link[1]; parent.appendChild(anchor);
              i += link[0].length; continue;
            }
          } catch (_) { /* Keep an invalid link as literal text. */ }
        }
      }
      var marker = text.startsWith('**', i) ? '**' : text.startsWith('__', i) ? '__' :
        (char === '*' || char === '_') ? char : '';
      if (marker) {
        var close = text.indexOf(marker, i + marker.length);
        if (close > i + marker.length && !/^\s|\s$/.test(text.slice(i + marker.length, close))) {
          flush(); var emphasis = document.createElement(marker.length === 2 ? 'strong' : 'em');
          inline(emphasis, text.slice(i + marker.length, close)); parent.appendChild(emphasis);
          i = close + marker.length; continue;
        }
      }
      buffer += char; i++;
    }
    flush();
  }

  function listMarker(line) {
    var match = line.match(/^( {0,12})([-+*]|\d+[.)])\s+(.+)$/);
    return match && {indent: match[1].length, ordered: /^\d/.test(match[2]), text: match[3]};
  }
  function tableCells(line) {
    var content = line.trim().replace(/^\|/, '').replace(/\|$/, '');
    var cells = [], cell = '';
    for (var i = 0; i < content.length; i++) {
      if (content[i] === '\\' && content[i + 1] === '|') { cell += '|'; i++; }
      else if (content[i] === '|') { cells.push(cell); cell = ''; }
      else cell += content[i];
    }
    cells.push(cell);
    return cells.map(function (cell) {
      return cell.trim();
    });
  }
  function tableDivider(line) {
    return /^\|?\s*:?-{3,}:?\s*(\|\s*:?-{3,}:?\s*)+\|?$/.test(line.trim());
  }
  function blockStart(lines, index) {
    var line = lines[index] || '';
    return /^\s*(`{3,}|~{3,})/.test(line) || /^ {0,3}#{1,4}\s+/.test(line) ||
      /^ {0,3}>\s?/.test(line) || /^ {0,3}(?:-{3,}|\*{3,}|_{3,})\s*$/.test(line) ||
      !!listMarker(line) || (line.includes('|') && tableDivider(lines[index + 1] || ''));
  }

  function blocks(parent, lines) {
    for (var i = 0; i < lines.length;) {
      var line = lines[i];
      if (!line.trim()) { i++; continue; }
      var fence = line.match(/^\s*(`{3,}|~{3,})\s*([\w.+-]*)/);
      if (fence) {
        var codeLines = []; i++;
        while (i < lines.length && !new RegExp('^\\s*' + fence[1][0] + '{' + fence[1].length + ',}\\s*$').test(lines[i])) codeLines.push(lines[i++]);
        if (i < lines.length) i++;
        var pre = document.createElement('pre'), code = document.createElement('code');
        code.textContent = codeLines.join('\n'); pre.appendChild(code); parent.appendChild(pre); continue;
      }
      var heading = line.match(/^ {0,3}(#{1,4})\s+(.+?)\s*#*\s*$/);
      if (heading) {
        var h = document.createElement('h' + Math.min(heading[1].length + 2, 6));
        inline(h, heading[2]); parent.appendChild(h); i++; continue;
      }
      if (/^ {0,3}(?:-{3,}|\*{3,}|_{3,})\s*$/.test(line)) {
        parent.appendChild(document.createElement('hr')); i++; continue;
      }
      if (/^ {0,3}>\s?/.test(line)) {
        var quoteLines = [];
        while (i < lines.length && /^ {0,3}>\s?/.test(lines[i])) quoteLines.push(lines[i++].replace(/^ {0,3}>\s?/, ''));
        var quote = document.createElement('blockquote'); blocks(quote, quoteLines);
        parent.appendChild(quote); continue;
      }
      if (line.includes('|') && tableDivider(lines[i + 1] || '')) {
        var headers = tableCells(line), table = document.createElement('table');
        var thead = document.createElement('thead'), tbody = document.createElement('tbody'), tr = document.createElement('tr');
        headers.forEach(function (value) { var th = document.createElement('th'); inline(th, value); tr.appendChild(th); });
        thead.appendChild(tr); table.append(thead, tbody); i += 2;
        while (i < lines.length && lines[i].includes('|') && lines[i].trim()) {
          tr = document.createElement('tr');
          tableCells(lines[i++]).slice(0, headers.length).forEach(function (value) {
            var td = document.createElement('td'); inline(td, value); tr.appendChild(td);
          });
          tbody.appendChild(tr);
        }
        var scroll = document.createElement('div'); scroll.className = 'rich-table-scroll';
        scroll.appendChild(table); parent.appendChild(scroll); continue;
      }
      var first = listMarker(line);
      if (first) {
        var list = document.createElement(first.ordered ? 'ol' : 'ul');
        var base = first.indent;
        while (i < lines.length) {
          var marker = listMarker(lines[i]);
          if (!marker || marker.indent !== base || marker.ordered !== first.ordered) break;
          var li = document.createElement('li'); inline(li, marker.text); i++;
          var nested = [];
          while (i < lines.length) {
            var next = listMarker(lines[i]);
            if (next && next.indent > base) { nested.push(lines[i++].slice(base + 2)); continue; }
            if (!next && /^\s{2,}\S/.test(lines[i])) { nested.push(lines[i++].slice(base + 2)); continue; }
            break;
          }
          if (nested.length) blocks(li, nested);
          list.appendChild(li);
        }
        parent.appendChild(list); continue;
      }
      var paragraph = [line.trim()]; i++;
      while (i < lines.length && lines[i].trim() && !blockStart(lines, i)) paragraph.push(lines[i++].trim());
      var p = document.createElement('p'); inline(p, paragraph.join('\n'));
      parent.appendChild(p);
    }
  }

  function renderInto(target, source) {
    var fragment = document.createDocumentFragment();
    blocks(fragment, String(source || '').replace(/\r\n?/g, '\n').split('\n'));
    target.replaceChildren(fragment);
  }
  window.CourseAiMarkdown = {renderInto: renderInto};
}());
