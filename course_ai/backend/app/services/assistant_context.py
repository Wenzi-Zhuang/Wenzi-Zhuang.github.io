import re
from dataclasses import dataclass
from pathlib import Path

from docx import Document
from pypdf import PdfReader

from ..config import get_settings

ASSISTANTS = {
    "financial_accounting": "会计学",
    "empirical_methods": "实证方法与论文写作",
    "case_study": "案例论文",
    "empirical_study": "实证论文",
}
ASSISTANT_FOLDERS = {
    "financial_accounting": "financial_accounting",
    "empirical_methods": "academic_writing",
    "case_study": "case_study",
    "empirical_study": "empirical_study",
}
NUMBERED_COURSE_FOLDERS = {"financial_accounting", "academic_writing"}
TEXT_EXTENSIONS = {".md", ".txt", ".csv"}
DOCUMENT_EXTENSIONS = TEXT_EXTENSIONS | {".pdf", ".docx"}


@dataclass
class AssistantContext:
    assistant_id: str
    name: str
    requirements: str
    skills: str
    evidence: list[dict]


def ensure_library_structure() -> None:
    root = get_settings().assistant_library_root
    scopes = [root / "common", root / "case_study", root / "empirical_study"]
    for scope in scopes:
        for folder in ("knowledge", "skills", "requirements"):
            (scope / folder).mkdir(parents=True, exist_ok=True)
        readme = scope / "README.md"
        if not readme.exists():
            assistant_id = next((key for key, folder in ASSISTANT_FOLDERS.items() if folder == scope.name), None)
            label = "所有助手共享" if scope.name == "common" else ASSISTANTS[assistant_id]
            readme.write_text(
                f"# {label}\n\n"
                "- `knowledge/`：教材、讲义、规则与案例资料。\n"
                "- `skills/`：希望助手遵循的分析步骤和输出方式。\n"
                "- `requirements/`：课程口径、边界、格式和禁止事项。\n\n"
                "支持 MD、TXT、CSV、PDF、DOCX。新增或修改文件后无需覆盖此说明。\n",
                encoding="utf-8",
            )


def _read_file(path: Path) -> str:
    suffix = path.suffix.lower()
    try:
        if suffix in TEXT_EXTENSIONS:
            return path.read_text(encoding="utf-8", errors="ignore")
        if suffix == ".pdf":
            return "\n".join(page.extract_text() or "" for page in PdfReader(path).pages)
        if suffix == ".docx":
            return "\n".join(paragraph.text for paragraph in Document(path).paragraphs)
    except Exception:
        return ""
    return ""


def _all_text(folder: Path, max_chars: int) -> str:
    parts = []
    total = 0
    for path in (sorted(folder.rglob("*")) if folder.is_dir() else []):
        if not path.is_file() or path.suffix.lower() not in DOCUMENT_EXTENSIONS:
            continue
        text = _read_file(path).strip()
        if not text:
            continue
        room = max_chars - total
        if room <= 0:
            break
        fragment = text[:room]
        parts.append(f"[{path.name}]\n{fragment}")
        total += len(fragment)
    return "\n\n".join(parts)


def _category_folders(scope: Path, category: str) -> list[Path]:
    if scope.name in NUMBERED_COURSE_FOLDERS:
        if category == "knowledge":
            return [scope / "10_sources", scope / "20_knowledge_system"]
        if category == "skills":
            return [scope / "40_skills"]
        return [scope / "00_system"]
    return [scope / category]


def _terms(query: str) -> set[str]:
    return set(re.findall(r"[\u4e00-\u9fff]{2,}|[A-Za-z0-9_]{2,}", query.lower()))


def _knowledge_chunks(folder: Path) -> list[dict]:
    chunks = []
    for path in (sorted(folder.rglob("*")) if folder.is_dir() else []):
        if not path.is_file() or path.suffix.lower() not in DOCUMENT_EXTENSIONS:
            continue
        text = _read_file(path).strip()
        for index in range(0, len(text), 2200):
            chunk = text[index:index + 2600].strip()
            if chunk:
                chunks.append({"source": path.name, "path": str(path), "text": chunk})
    return chunks


def load_assistant_context(assistant_id: str, query: str) -> AssistantContext:
    if assistant_id not in ASSISTANTS:
        raise KeyError(assistant_id)
    root = get_settings().assistant_library_root
    scopes = [root / "common", root / ASSISTANT_FOLDERS[assistant_id]]
    requirements = "\n\n".join(
        _all_text(folder, 10000) for scope in scopes for folder in _category_folders(scope, "requirements")
    ).strip()
    skills = "\n\n".join(
        _all_text(folder, 10000) for scope in scopes for folder in _category_folders(scope, "skills")
    ).strip()
    terms = _terms(query)
    ranked = []
    for priority, scope in enumerate(scopes):
        for folder in _category_folders(scope, "knowledge"):
            for chunk in _knowledge_chunks(folder):
                haystack = chunk["text"].lower()
                score = sum(haystack.count(term) for term in terms) + priority * 0.05
                if score > priority * 0.05:
                    ranked.append((score, chunk))
    ranked.sort(key=lambda item: item[0], reverse=True)
    return AssistantContext(assistant_id, ASSISTANTS[assistant_id], requirements, skills, [item for _, item in ranked[:8]])


def build_system_messages(context: AssistantContext, mode: str) -> list[dict]:
    sources = "\n\n".join(f"[来源：{item['source']}]\n{item['text']}" for item in context.evidence)
    return [
        {"role": "system", "content": f"你是“{context.name}”专属AI助教。只能诚实说明你实际获得的资料，不得编造来源、学校规定或教师要求。不要代写可直接提交的作业或论文；应通过解释、提问、反馈和修改建议帮助学习。"},
        {"role": "system", "content": f"当前功能：{mode}\n\n公共及专属要求：\n{context.requirements or '尚未配置额外要求。'}\n\n公共及专属技能：\n{context.skills or '尚未配置额外技能。'}\n\n检索到的知识资料：\n{sources or '没有检索到相关的NAS知识资料，请明确说明回答基于一般知识。'}"},
    ]

