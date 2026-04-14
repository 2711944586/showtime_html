# showtime_html

论文讲解稿与技术解释稿的静态展示站，当前目录就是部署根目录。

## 在线地址

- 合并页: `https://2711944586.github.io/showtime_html/`
- 主讲稿: `https://2711944586.github.io/showtime_html/论文深度讲解稿.html`
- 技术解释: `https://2711944586.github.io/showtime_html/技术解释文档.html`

## 文件

- `论文深度讲解稿.md`: 主讲稿源文件
- `技术解释_对象与方法.md`: 技术解释一
- `技术解释_理论与评估.md`: 技术解释二
- `build_showtime_site.py`: 构建脚本
- `index.html`: 合并部署页

## 本地更新

```powershell
python build_showtime_site.py
```

构建后会更新：

- `index.html`
- `论文深度讲解稿.html`
- `技术解释文档.html`

## 静态部署

工作流文件: `.github/workflows/deploy-showtime.yml`

```powershell
python build_showtime_site.py
git add .
git commit -m "Update showtime pages"
git push origin main
```

推送后：

1. 打开 `https://github.com/2711944586/showtime_html/actions`
2. 等待部署工作流完成
3. 打开上面的 Pages 地址

## 当前内容

1. 主讲稿、对象与方法、理论与评估三部分已经拆开维护。
2. 页面会把 Markdown 渲染成统一风格的 HTML，并支持公式渲染。
3. `index.html` 用于公开展示，另外两页用于单独引用和讲解。
