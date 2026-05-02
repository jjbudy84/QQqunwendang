# 部署给评委查看

这个项目是 Flask 后端加 `preview.html` 前端，不能只用 GitHub Pages。推荐部署到 Render。

## 1. 上传到 GitHub

在项目目录运行：

```powershell
git init
git add .
git commit -m "Prepare app for deployment"
```

然后在 GitHub 新建一个仓库，按 GitHub 页面提示执行：

```powershell
git remote add origin https://github.com/你的用户名/你的仓库名.git
git branch -M main
git push -u origin main
```

注意：`.env` 已经被 `.gitignore` 忽略，不要把真实 API Key 上传到 GitHub。

## 2. 在 Render 部署

1. 打开 https://render.com
2. 登录后选择 New + -> Blueprint
3. 连接刚才的 GitHub 仓库
4. Render 会读取 `render.yaml`
5. 在环境变量里填写 `DEEPSEEK_API_KEY`
6. 点击 Deploy

部署完成后，Render 会给你一个类似下面的链接：

```text
https://pet-care-rag.onrender.com
```

把这个链接发给评委即可。

## 3. 如果不用 Blueprint

也可以选择 New + -> Web Service，手动填写：

```text
Build Command: pip install -r requirements.txt
Start Command: gunicorn app:app --bind 0.0.0.0:$PORT
```

环境变量至少填写：

```text
AI_PROVIDER=deepseek
DEEPSEEK_API_KEY=你的 DeepSeek Key
DEEPSEEK_BASE_URL=https://api.deepseek.com
DEEPSEEK_MODEL=deepseek-v4-flash
FLASK_DEBUG=0
```

## 4. 重要提醒

Render 免费服务的本地文件存储可能会在重启后丢失，所以评委现场测试上传资料可以用，但长期保存上传文件和索引不稳定。比赛展示一般够用；如果要长期稳定保存，需要接数据库或云存储。
