import io
import re

from docx import Document
from pypdf import PdfReader

from .deepseek import stream_answer

THESIS_SYSTEM_PROMPT = """你是严谨的毕业论文格式审查助手，适用于本科和硕士论文。你只检查格式、结构和写作规范，不评价或代写研究结论。必须区分程序已经验证的事实、用户提供的学校要求和无法从文本判断的项目。不得编造页码、字体、行距、学校规定或检查结果；证据不足时明确要求人工核对。"""


def _cm(value):
    return round(value.cm, 2) if value is not None else None


def _docx_report(content: bytes) -> tuple[str, list[dict]]:
    try:
        document = Document(io.BytesIO(content))
    except Exception as exc:
        raise ValueError("DOCX 文件损坏或无法读取") from exc

    paragraphs = [p.text.strip() for p in document.paragraphs if p.text.strip()]
    text = "\n".join(paragraphs)
    issues = []
    if len(text) < 1000:
        issues.append({"level": "warning", "item": "正文长度", "detail": "可提取正文过短，请确认论文内容完整且不是图片扫描件。"})
    if not re.search(r"摘\s*要", text[:5000]):
        issues.append({"level": "error", "item": "中文摘要", "detail": "未识别到“摘要”部分。"})
    if not re.search(r"关键词", text[:7000]):
        issues.append({"level": "error", "item": "关键词", "detail": "未识别到“关键词”。"})
    if not re.search(r"参考文献", text[-12000:]):
        issues.append({"level": "error", "item": "参考文献", "detail": "文末未识别到“参考文献”。"})

    heading_count = sum(1 for p in document.paragraphs if p.style and "Heading" in p.style.name)
    if heading_count == 0:
        heading_count = sum(1 for p in paragraphs if re.match(r"^(第[一二三四五六七八九十]+章|[一二三四五六七八九十]+、|\d+(?:\.\d+)*\s+)", p))
    if heading_count < 3:
        issues.append({"level": "warning", "item": "标题层级", "detail": "识别到的章节标题较少，请检查标题编号与样式。"})

    margins = []
    for index, section in enumerate(document.sections, 1):
        item = {"section": index, "top": _cm(section.top_margin), "bottom": _cm(section.bottom_margin),
                "left": _cm(section.left_margin), "right": _cm(section.right_margin)}
        margins.append(item)
        if any(value is not None and (value < 1.5 or value > 4.0) for value in item.values() if isinstance(value, float)):
            issues.append({"level": "warning", "item": f"第{index}节页边距", "detail": f"检测值为上{item['top']}、下{item['bottom']}、左{item['left']}、右{item['right']}厘米，请对照学校模板。"})

    return text, issues + [{"level": "info", "item": "文档概况", "detail": f"识别到 {len(paragraphs)} 个非空段落、{heading_count} 个标题、{len(document.sections)} 个分节。"}]


def _pdf_report(content: bytes) -> tuple[str, list[dict]]:
    try:
        reader = PdfReader(io.BytesIO(content))
        pages = [(page.extract_text() or "").strip() for page in reader.pages]
    except Exception as exc:
        raise ValueError("PDF 文件损坏、加密或无法读取") from exc
    text = "\n".join(pages)
    issues = [{"level": "info", "item": "文档概况", "detail": f"PDF 共 {len(pages)} 页。PDF 只能检查内容结构，字体、行距和页边距请提交 DOCX 检查。"}]
    if len(text) < 1000:
        issues.append({"level": "warning", "item": "文本提取", "detail": "可提取文字过少，文件可能是扫描件。"})
    for label, pattern in (("中文摘要", r"摘\s*要"), ("关键词", r"关键词"), ("参考文献", r"参考文献")):
        if not re.search(pattern, text):
            issues.append({"level": "error", "item": label, "detail": f"未识别到“{label}”部分。"})
    return text, issues


async def inspect_thesis(content: bytes, suffix: str, requirements: str) -> dict:
    text, checks = _docx_report(content) if suffix == ".docx" else _pdf_report(content)
    requirement_text = requirements.strip() or "未提供学校专用格式规范，请按通用毕业论文结构审阅，并明确哪些项目无法确定。"
    prompt = f"""请检查下面毕业论文是否满足格式与结构要求。只能依据给出的论文文字、格式要求和程序检查结果，不得编造页码、字体或学校规定。

格式要求：
{requirement_text[:6000]}

程序检查结果：
{checks}

论文文字（最多前30000字）：
{text[:30000]}

请按以下结构回答：
1. 总体结论（通过/需要修改/无法完整判断）
2. 必须修改
3. 建议修改
4. 无法自动判断、需人工核对的项目
5. 修改优先级清单
"""
    analysis = "".join([part async for part in stream_answer(
        prompt, "毕业论文格式审查", [], system_prompt=THESIS_SYSTEM_PROMPT
    )])
    return {"status": "completed", "checks": checks, "analysis": analysis,
            "limitations": "AI 检查不能替代学院最终审核；未提供的学校模板要求不会被推断。"}
