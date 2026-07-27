# Life OS 部署指南

## 依赖关系
- **Cloudflare Pages** 是唯一第三方部署依赖
- 前端框架：Astro 5（全静态/SSR）
- 数据库：Supabase Postgres
- CI/CD：GitHub Actions
- 托管：Cloudflare（仅域名解析 + DNS + Pages 托管）

---

## 第一步：初始化 GitHub 仓库

```bash
cd /e/LifeOS
git init
git remote add origin https://github.com/YOUR-USERNAME/life-os.git
git add .
git commit -m "feat: Life OS MVP scaffold"
git branch -M main
git push -u origin main
```

---

## 第二步：创建 Supabase 项目

1. 打开 https://supabase.com → 新建项目 `life-os`
2. 复制：`project URL` + `anon/public key`
3. 复制 `supabase/schema.sql` 到 Supabase SQL Editor 执行
4. 把 key 设为 Cloudflare Pages 环境变量 `PUBLIC_SUPABASE_URL` 和 `PUBLIC_SUPABASE_ANON_KEY`

---

## 第三步：Cloudflare Pages 连接

**方式 A：一键接入**
1. Cloudflare Dashboard → Pages → 新建项目 → 连接 GitHub
2. 选择 `life-os` 仓库，构建命令：`npm install && npm run build`
3. 输出目录：`dist`
4. 环境变量：加 `PUBLIC_SUPABASE_URL` 和 `PUBLIC_SUPABASE_ANON_KEY`

**方式 B：GitHub Actions（推荐）**
1. Cloudflare → API Tokens → 创建 `Cloudflare Pages Edit` token
2. GitHub → Settings → Secrets → 添加：
   - `CLOUDFLARE_API_TOKEN`
   - `CLOUDFLARE_ACCOUNT_ID`（Cloudflare 右上角 Account ID）
3. 提交到 main 自动触发

---

## 第四步：本地预览

```bash
cd /e/LifeOS
npm install
npm run dev
# 打开 http://localhost:4321
```

---

## 第五步：后续开发（V1 MVP）

1. 安装 Astro 依赖：`npm install @astrojs/cloudflare @supabase/supabase-js`
2. 创建 `/timeline` 路由，连接 Supabase moments 表
3. 创建 `/moments/new` 路由（Moment 创建表单）
4. 加入 `/friends` 路由
5. 加入 `/report` 年度统计（星际雷达图用 Canvas/SVG）

---

## 未使用的依赖
- ❌ Vercel（未使用）
- ❌ Netlify（未使用）
- ❌ Railway（未使用）
- ❌ Cloudflare Workers Standalone（未使用，仅 Pages 托管）
