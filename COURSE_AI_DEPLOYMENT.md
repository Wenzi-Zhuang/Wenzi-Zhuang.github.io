# 会计学 AI 平台部署

当前仓库包含 GitHub Pages 课程界面，以及部署在群晖 NAS 上的 FastAPI、PostgreSQL、课程资料检索和 DeepSeek 安全代理。浏览器只持有可撤销的随机设备令牌，不会接触 DeepSeek 密钥。

## 1. NAS 准备

安装 Container Manager，并确认课程资料在 `/volume1/courses/financial_accounting`。复制本仓库到 NAS（例如 `/volume1/docker/course_ai/app`），在仓库根目录执行：

```bash
cp .env.example .env
```

填写 `.env`。生成设备令牌密钥：

```bash
openssl rand -hex 32
```

将输出写入 `DEVICE_TOKEN_SECRET`；将 DeepSeek 密钥只写入 NAS 上的 `.env`。

DeepSeek 密钥必须直接在 NAS 的 `.env` 中填写，不能放进 GitHub Pages 或浏览器表单：

```env
DEEPSEEK_API_KEY=sk-你的真实密钥
DEEPSEEK_BASE_URL=https://api.deepseek.com
DEEPSEEK_MODEL=deepseek-chat
```

保存后执行 `docker compose up -d --build`。访问 `http://127.0.0.1:8000/health`，确认 `deepseek_configured` 为 `true`。论文格式检查和论文互动问答都通过 NAS 后端调用 DeepSeek，浏览器不会收到密钥。

也可以在 NAS 的项目根目录运行安全输入界面（输入的密钥不会显示）：

```bash
python3 course_ai/backend/scripts/configure_deepseek.py
docker compose up -d --build
```

现在也提供浏览器配置界面。先在 NAS `.env` 中填写随机设置码：

```bash
openssl rand -hex 16
```

把输出写成 `SETUP_CODE=生成的随机值`，启动容器后打开：

```text
https://你的课程API域名/setup/deepseek
```

在页面输入设置码和 DeepSeek API Key。密钥会保存到 NAS 的 `/volume1/docker/course_ai/config/deepseek.json`，权限为 `600`，不会返回 GitHub Pages。配置成功后应立即妥善保存设置码；不要把设置码或 API Key 发到聊天中。

## 四套助手资料库

Docker 会把 NAS 的 `/volume1/courses/ai_assistants` 挂载为助手资料库。首次启动自动创建公共目录和四套专属目录，结构与填充规则见 `NAS_ASSISTANT_LIBRARY.md`。页面与目录映射如下：

| 页面 | assistant_id | NAS 专属目录 |
| --- | --- | --- |
| 会计学 | `financial_accounting` | `assistants/financial_accounting` |
| 实证方法与论文写作 | `empirical_methods` | `assistants/empirical_methods` |
| 案例论文 | `case_thesis` | `assistants/case_thesis` |
| 实证论文 | `empirical_thesis` | `assistants/empirical_thesis` |

所有页面还会读取 `common/knowledge`、`common/skills` 和 `common/requirements`。新增或更新资料文件后，不需要修改前端代码。

## 2. 启动与初始化

```bash
docker compose up -d --build
docker compose exec backend python scripts/import_students.py /volume1/courses/financial_accounting/00_course_rules/students.csv
docker compose exec backend python scripts/ingest_course_library.py
curl http://127.0.0.1:8000/health
```

学生 CSV 表头必须是 `student_no,name,password`，导入后密码只以 Argon2 哈希保存。毕业论文指导页面按当前需求无需登录，但仍只允许来自个人主页域名的浏览器调用。索引脚本只扫描明确允许公开教学的目录，不扫描教师批改、考试答案、学生提交与归档目录。首次导入前仍应检查允许目录里没有仅限教师的文件。

## 3. IPv6、域名与 DSM 反向代理

1. 给课程 API 子域名添加 `AAAA` 记录，值为 NAS 的公网 IPv6；路由器只放行入站 TCP 443 到 NAS。
2. 在 DSM“登录门户 → 高级 → 反向代理服务器”新建规则：来源 `HTTPS / api.your-domain.example / 443`，目的地 `HTTP / 127.0.0.1 / 8000`。
3. 给该域名申请 Let's Encrypt 证书并绑定反向代理规则。不要开放 5000、5001、8000 或 5432。
4. 在 `.env` 设置 `PUBLIC_API_BASE`，并把 `assets/js/course-ai-config.js` 中域名改成相同 HTTPS 地址。
5. `.env` 的 `FRONTEND_ORIGIN` 保持精确的 `https://wenzi-zhuang.github.io`，不能写 `*`。

修改 `.env` 后运行 `docker compose up -d --build`。修改 GitHub Pages 配置脚本后提交并推送本仓库。

## 4. 外网验收

分别从家庭网络、关闭 Wi-Fi 的手机、校园网测试课程页面和 `https://课程API域名/health`。部分网络只有 IPv4；如果 IPv6-only 地址无法访问，应增加 Cloudflare Tunnel 或双栈 VPS 代理，而不是公开 NAS 管理端口。

## 当前范围

已完成第一阶段主链路和第二阶段基础 lexical RAG：健康检查、PostgreSQL、学生名单导入、首次设备验证、令牌撤销、DeepSeek 流式问答、毕业论文互动问答与格式检查、受权限约束的课程资料索引及真实来源显示。知识地图、专项测试、错题本、复习分析和文件版本提交仍需后续阶段实现；前端对应入口目前仅作为导航，不会伪造数据。
