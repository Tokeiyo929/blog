# unity_tool# 博客系统 - 动态加载版

一个现代化的静态博客系统，支持 Markdown 动态解析和文章自动管理。

## ✨ 特性

- 🚀 **动态加载** - 文章列表自动从配置文件加载
- 📝 **Markdown 支持** - 使用 Markdown 编写，自动转换为精美的 HTML
- 🎨 **代码高亮** - 支持多种编程语言的语法高亮
- 📱 **响应式设计** - 完美适配桌面和移动设备
- 🌍 **多语言支持** - 内置中文、英文、日文支持
- 🔧 **自动管理** - Python 工具自动管理文章和配置
- 🎯 **零依赖部署** - 纯静态文件，可部署到任何静态托管服务

## 📁 项目结构

```
博客目录/
├── index.html              # 博客首页（动态加载文章列表）
├── posts-config.json       # 文章配置文件（自动生成）
├── create_post.py          # 文章管理工具
├── run_server.py           # 本地开发服务器
├── post1.html              # 文章页面
├── post1.md                # Markdown 源文件
├── post2.html
├── post2.md
├── ...
├── README.md               # 项目说明（本文件）
├── 快速开始.md             # 快速开始指南
└── 博客文章配置说明.md     # 详细配置说明
```

## 🚀 快速开始

### 1. 启动本地服务器

```bash
python run_server.py
```

在浏览器中访问 `http://localhost:8000`

### 2. 查看现有文章

```bash
python create_post.py
# 选择 3 - 查看所有文章列表
```

### 3. 创建新文章

准备一个 Markdown 文件，然后运行：

```bash
python create_post.py
# 选择 1 - 从 Markdown 文件生成/更新文章
# 输入你的 Markdown 文件路径
```

### 4. 查看效果

刷新浏览器，新文章会自动显示在首页！

## 📖 详细文档

- [快速开始.md](快速开始.md) - 新手入门指南
- [博客文章配置说明.md](博客文章配置说明.md) - 详细配置和使用说明

## 🛠️ 功能说明

### 博客首页 (index.html)

- 自动从 `posts-config.json` 加载文章列表
- 动态生成文章卡片
- 支持多语言切换
- 响应式布局

### 文章管理工具 (create_post.py)

提供4个主要功能：

1. **生成/更新文章** - 从 Markdown 文件生成 HTML 页面
2. **删除文章** - 删除文章文件和配置
3. **查看文章列表** - 显示所有文章及状态
4. **同步文章** - 扫描并同步所有文章到配置文件

### 文章页面 (post*.html)

- 动态加载 Markdown 内容
- 自动代码高亮
- 复制代码功能
- 响应式设计
- 深色模式支持

## 📝 Markdown 格式

### 带元数据（推荐）

```markdown
---
title: 文章标题
category: 分类
date: 2025年12月08日
cover_image: https://images.unsplash.com/photo-xxx
excerpt: 文章摘要
tags: 标签1, 标签2, 标签3
---

# 正文标题

文章内容...
```

### 简化格式

```markdown
# 文章标题

文章内容...
```

## 🎯 使用场景

### 个人博客
- 技术文章分享
- 学习笔记记录
- 项目文档

### 团队文档
- 技术文档
- 开发规范
- API 文档

### 教程网站
- 编程教程
- 技术指南
- 学习资源

## 🔧 技术栈

### 前端
- HTML5 / CSS3
- JavaScript (ES6+)
- [Marked.js](https://marked.js.org/) - Markdown 解析
- [Prism.js](https://prismjs.com/) - 代码高亮
- [Font Awesome](https://fontawesome.com/) - 图标库

### 后端工具
- Python 3.x
- JSON 配置管理

## 📦 部署

### GitHub Pages

1. 将所有文件推送到 GitHub 仓库
2. 在仓库设置中启用 GitHub Pages
3. 选择主分支作为源
4. 访问 `https://你的用户名.github.io/仓库名`

### Netlify / Vercel

1. 连接 GitHub 仓库
2. 无需构建命令
3. 发布目录设置为根目录
4. 自动部署

### 其他静态托管

将所有文件上传到任何支持静态文件的托管服务即可。

## 🎨 自定义

### 修改样式

编辑 `index.html` 中的 `<style>` 标签，修改 CSS 变量：

```css
:root {
    --primary-color: #4a6fa5;
    --secondary-color: #166088;
    --accent-color: #32a852;
    /* ... */
}
```

### 修改文章模板

编辑 `create_post.py` 中的 `create_post_html` 函数。

### 添加新语言

1. 创建语言文件：`lang.语言代码.json`
2. 在 `index.html` 中添加语言按钮

## 🔍 常见问题

### Q: 文章没有显示？
**A:** 检查 `posts-config.json` 格式，运行同步工具（选项4）

### Q: 代码高亮不工作？
**A:** 确保网络连接正常，CDN 资源能够加载

### Q: 如何修改文章顺序？
**A:** 编辑 `posts-config.json`，调整数组顺序

### Q: 配置文件丢失了？
**A:** 运行 `python create_post.py` 选择选项4重建

更多问题请查看 [博客文章配置说明.md](博客文章配置说明.md)

## 📋 待办事项

- [ ] 添加搜索功能
- [ ] 支持文章分类筛选
- [ ] 添加评论系统集成
- [ ] 支持 RSS 订阅
- [ ] 添加文章统计功能
- [ ] 支持草稿功能
- [ ] 添加图片压缩工具

## 🤝 贡献

欢迎提交 Issue 和 Pull Request！

## 📄 许可证

MIT License

## 🙏 致谢

- [Marked.js](https://marked.js.org/) - Markdown 解析器
- [Prism.js](https://prismjs.com/) - 代码高亮
- [Font Awesome](https://fontawesome.com/) - 图标
- [Unsplash](https://unsplash.com/) - 示例图片

## 📞 联系方式

如有问题或建议，欢迎通过以下方式联系：

- 📧 Email: contact@blogworld.com
- 🐛 Issues: 在 GitHub 仓库提交 Issue
- 💬 讨论: 在 GitHub Discussions 中讨论

---

**开始你的博客之旅吧！** 🚀

查看 [快速开始.md](快速开始.md) 了解详细使用方法。

