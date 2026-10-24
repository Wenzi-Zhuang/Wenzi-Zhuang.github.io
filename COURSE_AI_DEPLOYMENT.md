# 课程 AI 平台部署与验收

四个 GitHub Pages 互动页调用 NAS 上的 FastAPI 后端；DeepSeek 密钥仅在 NAS 私有配置中。现有线上入口由 Tailscale Funnel 代理到 NAS 的 `127.0.0.1:8000`，无需开放路由器端口、DSM 管理端口或数据库端口。

## 发布顺序

1. 先备份 NAS 的 `/volume1/docker/course-ai` 项目、PostgreSQL 数据和 `/volume1/courses`。尤其不要用代码包覆盖 `.env`、`config/`、`data/postgres/`、课程资料或学生目录。
2. 将本仓库 `course_ai/backend/app/` 的改动上传到 NAS `/volume1/docker/course-ai/backend/app/`，保留目录结构。新后端必须先于网页发布；否则新网页无法注册登录。
3. 在 NAS 项目目录执行 `docker compose -f compose.yml build backend` 和 `docker compose -f compose.yml up -d --no-deps backend`。DSM Container Manager 的普通“构建/运行”操作未必重新生成镜像，应核对镜像时间与实际接口。
4. 检查 `https://wz-nas.tail29329a.ts.net/health` 返回数据库和课程目录 `ok`。无令牌访问聊天、文档与历史接口应为 `401`；旧 `/api/thesis/check` 应为 `404`。
5. 首次初始化教师账号：在自己的设备打开 `https://wz-nas.tail29329a.ts.net/setup/admin`，输入 NAS `.env` 中的 `SETUP_CODE`，设置至少 12 位的新口令。账号名固定为 `admin`。聊天中曾出现的 `140210` 不能作为正式教师口令。初始化只允许一次；之后的重置需在 NAS 私有环境中处理。
6. 再将前端提交推送 GitHub Pages。分别检查四页的登录、注册、自动登录、历史对话、文件及用量提示。不要用真实身份证资料做公开验收。

## 学生名单与隐私

后端首次启动会在每门课程的 `access/roster.json` 写入两名测试学生：`2011310411` 邓伦、`2013420430` 于洋，班级暂为“待填写”。四门平台分别有自己的名单。教师登录任一平台后，可在左侧“本平台学生名单”更新学号、姓名、班级；不需要在后台预录身份证后六位。

首次注册要求学生输入学号和身份证后六位，展示核对信息后由学生确认。一个学号全平台只能注册一次，后六位只作为 Argon2 哈希保存在 PostgreSQL；不会写入 GitHub 或课程名单。因为名单没有预存身份校验值，系统**无法证明注册者就是本人**：知道学号的人可以抢先注册。正式使用前应考虑增加学校身份核验或一次性邀请码。

网页无法读取 MAC 地址。系统使用浏览器保存的随机设备令牌自动登录；每个学号最多 5 个有效令牌。同一浏览器登录其他账号时，前一个令牌会撤销。不同浏览器资料、无痕窗口和清理浏览器数据会被视为不同设备。令牌哈希与设备摘要保存在数据库和课程目录 `access/students/<学号>/devices.json`。

对话保存在对应课程的 `access/students/<学号>/threads/<对话ID>.json`，每个文件不超过 200 KiB，最多 50 个对话。文档仅在内存中提取文字，不保存原文件；摘录随该次提问送到 DeepSeek，也不写入历史记录。四个平台各自对每名学生实施滚动 1 小时 50 问、北京时间自然日 150 问，以及每天 10 个文档、单个 500 KiB、累计 1500 KiB；全站另有防滥用保护。支持 PDF、DOCX、TXT、MD、CSV。

## 资料库

公共与专属知识、技能、要求的目录见 [NAS_ASSISTANT_LIBRARY.md](NAS_ASSISTANT_LIBRARY.md)。`access/` 只存名单与学生数据，不参与知识库检索，不应公开分享。新增资料无需重建镜像。

## 回滚与备份

若新镜像启动失败，先查看 NAS 后端日志，再从发布前备份恢复旧代码和镜像；不要恢复或覆盖较新的学生数据。PostgreSQL 与课程目录在同一台 NAS 上，当前没有跨设备热备或自动故障切换。正式开放前应配置 NAS 的异机/异地备份，并演练从备份恢复数据库、`config/`、`access/` 和课程资料。
