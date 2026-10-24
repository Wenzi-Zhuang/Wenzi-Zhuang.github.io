# NAS AI 助手资料库结构

后端首次启动时会在 `/volume1/courses/ai_assistants` 自动创建以下目录。只创建缺失目录和说明文件，不覆盖已有内容。

```text
ai_assistants/
├── common/                         # 四个助手共同使用
│   ├── knowledge/                  # 通用知识、校级制度、共同参考资料
│   ├── skills/                     # 通用分析与教学技能
│   ├── requirements/               # 通用回答要求、边界与禁止事项
│   └── README.md
└── assistants/
    ├── financial_accounting/       # 会计学
    │   ├── knowledge/
    │   ├── skills/
    │   └── requirements/
    ├── empirical_methods/          # 实证方法与论文写作
    │   ├── knowledge/
    │   ├── skills/
    │   └── requirements/
    ├── case_thesis/                # 案例论文
    │   ├── knowledge/
    │   ├── skills/
    │   └── requirements/
    └── empirical_thesis/           # 实证论文
        ├── knowledge/
        ├── skills/
        └── requirements/
```

## 放置规则

- `knowledge/`：教材、课程讲义、案例、论文规范和参考资料。
- `skills/`：让助手执行某种工作的方法，例如“案例分析步骤”“研究设计评估框架”“分录检查流程”。
- `requirements/`：必须遵守的规则，例如课程口径、输出格式、不得代写、必须引用来源。
- `common/` 内容会自动与当前助手的专属内容合并；专属内容应写得更具体。
- 支持 `.md`、`.txt`、`.csv`、`.pdf`、`.docx`。
- 文件名应具有可读性，因为回答引用来源时会显示文件名。
- 不要放入其他学生论文、未公开答案、密码或 API Key。

新增或修改资料后无需重建容器；下一次提问会读取最新文件。资料很多时再升级为预构建向量索引。

## 推荐的最小内容

每个助手先准备三个 Markdown 文件：

```text
requirements/assistant_rules.md
skills/answer_workflow.md
knowledge/core_material.md
```

示例 `requirements/assistant_rules.md`：

```markdown
# 回答要求
- 优先使用本目录与 common 中的资料。
- 没有可靠来源时明确说明。
- 不代写可直接提交的论文或作业。
- 给出可执行的修改建议和检查步骤。
```
