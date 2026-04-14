from __future__ import annotations

import html
import re
from pathlib import Path


ROOT = Path(__file__).resolve().parent

DOCS = {
  "lecture": {
    "file": "论文深度讲解稿.md",
    "title": "论文深度讲解稿",
    "kicker": "Talk Script",
    "summary": "面向汇报、答辩预演和公开展示的主讲线。",
  },
  "method": {
    "file": "技术解释_对象与方法.md",
    "title": "技术解释一：对象、结构与方法",
    "kicker": "Technical Note 01",
    "summary": "解释对象层、曝光图构造、TSFB、TSHM 与 SECR。",
  },
  "protocol": {
    "file": "技术解释_理论与评估.md",
    "title": "技术解释二：理论、评估与边界",
    "kicker": "Technical Note 02",
    "summary": "解释命题边界、评估协议、失败判据与局限性。",
  },
}

QUICK_LINKS = [
  ("合并部署页", "index.html"),
  ("主讲稿 HTML", "论文深度讲解稿.html"),
  ("技术解释 HTML", "技术解释文档.html"),
  ("论文网站", "https://2711944586.github.io/paperpages/#/paper"),
  ("研究导图", "https://2711944586.github.io/mindmap/research_journey.html"),
]


def slugify(text: str, prefix: str) -> str:
  text = text.strip().lower()
  text = re.sub(r"[^\w\u4e00-\u9fff-]+", "-", text)
  text = re.sub(r"-{2,}", "-", text).strip("-")
  return f"{prefix}-{text or 'section'}"


def preserve_inline_math(text: str) -> tuple[str, dict[str, str]]:
  tokens: dict[str, str] = {}

  def stash(match: re.Match[str]) -> str:
    token = f"__MATHTOKEN{len(tokens)}__"
    tokens[token] = html.escape(match.group(0))
    return token

  protected = re.sub(r"\\\(.+?\\\)|(?<!\$)\$(?!\$).+?(?<!\$)\$(?!\$)", stash, text)
  return protected, tokens


def inline_format(text: str) -> str:
  protected, math_tokens = preserve_inline_math(text)
  escaped = html.escape(protected)
  escaped = re.sub(r"`([^`]+)`", r"<code>\1</code>", escaped)
  escaped = re.sub(r"\*\*([^*]+)\*\*", r"<strong>\1</strong>", escaped)
  escaped = re.sub(r"\*([^*]+)\*", r"<em>\1</em>", escaped)
  escaped = re.sub(r"\[([^\]]+)\]\(([^)]+)\)", r'<a href="\2">\1</a>', escaped)
  for token, value in math_tokens.items():
    escaped = escaped.replace(token, value)
  return escaped


def render_markdown(markdown_text: str, prefix: str) -> tuple[str, list[dict[str, str]]]:
  lines = markdown_text.splitlines()
  toc: list[dict[str, str]] = []
  parts: list[str] = []
  paragraph: list[str] = []
  quote_lines: list[str] = []
  list_items: list[str] = []
  list_kind: str | None = None
  in_code = False
  code_lines: list[str] = []
  in_math = False
  math_lines: list[str] = []

  def flush_paragraph() -> None:
    nonlocal paragraph
    if paragraph:
      parts.append(f"<p>{inline_format(' '.join(paragraph).strip())}</p>")
      paragraph = []

  def flush_quote() -> None:
    nonlocal quote_lines
    if quote_lines:
      quoted = " ".join(quote_lines).strip()
      parts.append(f"<blockquote>{inline_format(quoted)}</blockquote>")
      quote_lines = []

  def flush_list() -> None:
    nonlocal list_items, list_kind
    if list_items and list_kind:
      tag = "ol" if list_kind == "ol" else "ul"
      parts.append(f"<{tag}>" + "".join(f"<li>{item}</li>" for item in list_items) + f"</{tag}>")
    list_items = []
    list_kind = None

  def flush_code() -> None:
    nonlocal code_lines
    if code_lines:
      code = html.escape("\n".join(code_lines))
      parts.append(f"<pre><code>{code}</code></pre>")
      code_lines = []

  def flush_math() -> None:
    nonlocal math_lines
    if math_lines:
      formula = html.escape("\n".join(math_lines).strip())
      parts.append(f"<div class=\"math-block\">\\[{formula}\\]</div>")
      math_lines = []

  for raw_line in lines:
    line = raw_line.rstrip()

    if in_math:
      if line.strip() == "$$":
        in_math = False
        flush_math()
      else:
        math_lines.append(raw_line)
      continue

    if in_code:
      if line.startswith("```"):
        in_code = False
        flush_code()
      else:
        code_lines.append(raw_line)
      continue

    if line.startswith("```"):
      flush_paragraph()
      flush_quote()
      flush_list()
      in_code = True
      code_lines = []
      continue

    single_line_math = re.match(r"^\$\$\s*(.*?)\s*\$\$$", line.strip())
    if single_line_math:
      flush_paragraph()
      flush_quote()
      flush_list()
      formula = html.escape(single_line_math.group(1))
      parts.append(f"<div class=\"math-block\">\\[{formula}\\]</div>")
      continue

    if line.strip() == "$$":
      flush_paragraph()
      flush_quote()
      flush_list()
      in_math = True
      math_lines = []
      continue

    if not line.strip():
      flush_paragraph()
      flush_quote()
      flush_list()
      continue

    heading = re.match(r"^(#{1,6})\s+(.*)$", line)
    if heading:
      flush_paragraph()
      flush_quote()
      flush_list()
      level = len(heading.group(1))
      title = heading.group(2).strip()
      anchor = slugify(title, prefix)
      if level >= 2:
        toc.append({"level": str(level), "id": anchor, "title": title})
      parts.append(f'<h{level} id="{anchor}">{inline_format(title)}</h{level}>')
      continue

    quote = re.match(r"^>\s?(.*)$", line)
    if quote:
      flush_paragraph()
      flush_list()
      quote_lines.append(quote.group(1))
      continue

    unordered = re.match(r"^-\s+(.*)$", line)
    if unordered:
      flush_paragraph()
      flush_quote()
      if list_kind not in (None, "ul"):
        flush_list()
      list_kind = "ul"
      list_items.append(inline_format(unordered.group(1)))
      continue

    ordered = re.match(r"^\d+\.\s+(.*)$", line)
    if ordered:
      flush_paragraph()
      flush_quote()
      if list_kind not in (None, "ol"):
        flush_list()
      list_kind = "ol"
      list_items.append(inline_format(ordered.group(1)))
      continue

    flush_quote()
    paragraph.append(line.strip())

  flush_paragraph()
  flush_quote()
  flush_list()
  flush_code()
  flush_math()

  return "\n".join(parts), toc


def build_toc(entries: list[dict[str, str]]) -> str:
  if not entries:
    return ""
  links = []
  for entry in entries:
    level_class = "toc-sub" if entry["level"] == "3" else ""
    links.append(f'<a class="toc-link {level_class}" href="#{entry["id"]}">{html.escape(entry["title"])}</a>')
  return "\n".join(links)


def build_doc_section(key: str, meta: dict[str, str], body_html: str) -> str:
  return f"""
  <section class="doc-block" id="{key}">
    <div class="doc-header">
      <span class="doc-kicker">{html.escape(meta["kicker"])}</span>
      <h2>{html.escape(meta["title"])}</h2>
      <p>{html.escape(meta["summary"])}</p>
    </div>
    <article class="prose">
      {body_html}
    </article>
  </section>
  """


def page_template(title: str, subtitle: str, lead: str, quick_links_html: str, toc_html: str, content_html: str, stats_html: str) -> str:
  return f"""<!DOCTYPE html>
<html lang="zh-CN">
<head>
  <meta charset="UTF-8" />
  <meta name="viewport" content="width=device-width, initial-scale=1.0" />
  <title>{html.escape(title)}</title>
  <script>
    window.MathJax = {{
      tex: {{
        inlineMath: [["$", "$"], ["\\\\(", "\\\\)"]],
        displayMath: [["$$", "$$"], ["\\\\[", "\\\\]"]],
      }},
      svg: {{
        fontCache: "global",
      }},
    }};
  </script>
  <script defer src="https://cdn.jsdelivr.net/npm/mathjax@3/es5/tex-svg.js"></script>
  <link rel="preconnect" href="https://fonts.googleapis.com" />
  <link rel="preconnect" href="https://fonts.gstatic.com" crossorigin />
  <link href="https://fonts.googleapis.com/css2?family=Manrope:wght@400;500;600;700;800&family=Noto+Serif+SC:wght@400;600;700&display=swap" rel="stylesheet" />
  <style>
    :root {{
      --bg: #f2ece0;
      --bg-strong: #faf5eb;
      --surface: rgba(255, 251, 245, 0.86);
      --surface-strong: rgba(255, 255, 255, 0.92);
      --line: rgba(68, 52, 36, 0.12);
      --line-strong: rgba(68, 52, 36, 0.24);
      --text: #221a13;
      --text-muted: #61584d;
      --text-soft: #867a6d;
      --accent: #9a5930;
      --accent-deep: #6d3716;
      --accent-alt: #214f4b;
      --shadow: 0 24px 70px rgba(67, 44, 23, 0.1);
      --radius-xl: 28px;
      --radius-lg: 20px;
      --radius-md: 14px;
    }}

    * {{
      box-sizing: border-box;
    }}

    html {{
      scroll-behavior: smooth;
    }}

    body {{
      margin: 0;
      color: var(--text);
      background:
        radial-gradient(circle at 10% 0%, rgba(154, 89, 48, 0.14), transparent 28%),
        radial-gradient(circle at 100% 10%, rgba(33, 79, 75, 0.12), transparent 26%),
        linear-gradient(180deg, #f7f0e4 0%, #f2ece0 54%, #faf5eb 100%);
      font-family: "Manrope", "Segoe UI", "PingFang SC", "Microsoft YaHei", sans-serif;
    }}

    a {{
      color: inherit;
    }}

    .page-shell {{
      max-width: 1440px;
      margin: 0 auto;
      padding: 28px 24px 64px;
    }}

    .topbar {{
      position: sticky;
      top: 0;
      z-index: 40;
      display: flex;
      align-items: center;
      justify-content: space-between;
      gap: 16px;
      margin-bottom: 24px;
      padding: 16px 18px;
      border: 1px solid var(--line);
      border-radius: 999px;
      background: rgba(247, 240, 228, 0.78);
      backdrop-filter: blur(18px);
      box-shadow: var(--shadow);
    }}

    .brand {{
      display: grid;
      gap: 4px;
    }}

    .brand-kicker {{
      color: var(--accent-alt);
      font-size: 11px;
      letter-spacing: 0.18em;
      text-transform: uppercase;
    }}

    .brand-title {{
      font-family: "Noto Serif SC", Georgia, serif;
      font-size: 24px;
      line-height: 1.1;
    }}

    .top-actions {{
      display: flex;
      flex-wrap: wrap;
      gap: 10px;
      justify-content: flex-end;
    }}

    .top-link,
    .theme-toggle {{
      display: inline-flex;
      align-items: center;
      gap: 8px;
      padding: 10px 14px;
      border-radius: 999px;
      border: 1px solid var(--line);
      background: rgba(255, 255, 255, 0.72);
      color: var(--text-muted);
      text-decoration: none;
      font-size: 13px;
      cursor: pointer;
      transition: transform 0.2s ease, border-color 0.2s ease, color 0.2s ease;
    }}

    .top-link:hover,
    .theme-toggle:hover {{
      transform: translateY(-1px);
      border-color: rgba(154, 89, 48, 0.24);
      color: var(--accent-deep);
    }}

    .hero {{
      display: grid;
      grid-template-columns: minmax(0, 1.2fr) minmax(320px, 0.8fr);
      gap: 20px;
      margin-bottom: 22px;
    }}

    .hero-main,
    .hero-side,
    .content-area,
    .toc-panel {{
      border: 1px solid var(--line);
      border-radius: var(--radius-xl);
      background: var(--surface);
      box-shadow: var(--shadow);
    }}

    .hero-main,
    .hero-side,
    .toc-panel {{
      padding: 24px;
    }}

    .hero-main h1 {{
      margin: 0;
      font-family: "Noto Serif SC", Georgia, serif;
      font-size: clamp(34px, 4.6vw, 60px);
      line-height: 1.04;
    }}

    .hero-main p {{
      margin: 14px 0 0;
      max-width: 60rem;
      color: var(--text-muted);
      line-height: 1.85;
    }}

    .hero-kicker {{
      margin: 0 0 12px;
      color: var(--accent-alt);
      font-size: 12px;
      letter-spacing: 0.18em;
      text-transform: uppercase;
    }}

    .stat-grid {{
      display: grid;
      gap: 12px;
    }}

    .stat-card {{
      padding: 16px 18px;
      border-radius: 18px;
      border: 1px solid var(--line);
      background: rgba(255, 255, 255, 0.74);
    }}

    .stat-label {{
      color: var(--text-soft);
      font-size: 11px;
      letter-spacing: 0.16em;
      text-transform: uppercase;
    }}

    .stat-value {{
      margin-top: 8px;
      color: var(--accent-deep);
      font-size: 28px;
      font-weight: 800;
      line-height: 1;
    }}

    .stat-note {{
      margin-top: 8px;
      color: var(--text-muted);
      font-size: 13px;
      line-height: 1.7;
    }}

    .quick-links {{
      display: flex;
      flex-wrap: wrap;
      gap: 10px;
      margin-top: 18px;
    }}

    .quick-link {{
      display: inline-flex;
      align-items: center;
      gap: 8px;
      padding: 11px 15px;
      border-radius: 999px;
      background: linear-gradient(90deg, rgba(154, 89, 48, 0.96), rgba(109, 55, 22, 0.96));
      color: #fffdf8;
      text-decoration: none;
      font-size: 13px;
      transition: transform 0.2s ease, box-shadow 0.2s ease;
    }}

    .quick-link.alt {{
      background: rgba(33, 79, 75, 0.1);
      color: var(--accent-alt);
    }}

    .quick-link:hover {{
      transform: translateY(-1px);
      box-shadow: 0 16px 34px rgba(109, 55, 22, 0.16);
    }}

    .layout {{
      display: grid;
      grid-template-columns: minmax(0, 1fr) 300px;
      gap: 20px;
      align-items: start;
    }}

    .content-area {{
      padding: 28px;
    }}

    .doc-block + .doc-block {{
      margin-top: 34px;
      padding-top: 34px;
      border-top: 1px solid rgba(68, 52, 36, 0.08);
    }}

    .doc-header {{
      margin-bottom: 18px;
    }}

    .doc-kicker {{
      display: inline-flex;
      align-items: center;
      gap: 8px;
      margin-bottom: 10px;
      color: var(--accent);
      font-size: 12px;
      letter-spacing: 0.14em;
      text-transform: uppercase;
    }}

    .doc-kicker::before {{
      content: "";
      width: 26px;
      height: 1px;
      background: currentColor;
    }}

    .doc-header h2 {{
      margin: 0;
      font-family: "Noto Serif SC", Georgia, serif;
      font-size: 30px;
      line-height: 1.15;
    }}

    .doc-header p {{
      margin: 10px 0 0;
      color: var(--text-muted);
      line-height: 1.8;
    }}

    .toc-panel {{
      position: sticky;
      top: 102px;
    }}

    .toc-panel h3 {{
      margin: 0 0 14px;
      font-size: 15px;
    }}

    .toc-links {{
      display: grid;
      gap: 8px;
    }}

    .toc-link {{
      padding: 10px 12px;
      border-radius: 14px;
      border: 1px solid transparent;
      color: var(--text-muted);
      text-decoration: none;
      font-size: 13px;
      line-height: 1.5;
      transition: background 0.2s ease, border-color 0.2s ease, color 0.2s ease;
    }}

    .toc-link:hover,
    .toc-link.active {{
      border-color: rgba(154, 89, 48, 0.22);
      background: rgba(255, 248, 239, 0.86);
      color: var(--accent-deep);
    }}

    .toc-sub {{
      margin-left: 14px;
      font-size: 12px;
    }}

    .prose {{
      color: var(--text);
      line-height: 1.85;
    }}

    .prose h1,
    .prose h2,
    .prose h3 {{
      font-family: "Noto Serif SC", Georgia, serif;
      scroll-margin-top: 120px;
    }}

    .prose h1 {{
      margin: 0 0 22px;
      font-size: 38px;
      line-height: 1.12;
    }}

    .prose h2 {{
      margin: 28px 0 12px;
      font-size: 28px;
      line-height: 1.18;
    }}

    .prose h3 {{
      margin: 22px 0 10px;
      font-size: 20px;
      line-height: 1.28;
    }}

    .prose p {{
      margin: 0 0 14px;
      color: var(--text-muted);
    }}

    .prose ul,
    .prose ol {{
      margin: 0 0 18px;
      padding-left: 1.3rem;
      color: var(--text-muted);
    }}

    .prose li + li {{
      margin-top: 8px;
    }}

    .prose blockquote {{
      margin: 0 0 18px;
      padding: 16px 18px;
      border-left: 3px solid rgba(154, 89, 48, 0.32);
      border-radius: 0 16px 16px 0;
      background: rgba(255, 248, 239, 0.78);
      color: var(--text);
    }}

    .prose pre {{
      margin: 0 0 18px;
      padding: 16px;
      overflow-x: auto;
      border-radius: 18px;
      background: #271d17;
      color: #f9efe5;
    }}

    .prose code {{
      padding: 0.18em 0.42em;
      border-radius: 8px;
      background: rgba(33, 79, 75, 0.09);
      color: var(--accent-alt);
      font-family: "SFMono-Regular", Consolas, monospace;
      font-size: 0.92em;
    }}

    .prose pre code {{
      padding: 0;
      background: transparent;
      color: inherit;
    }}

    .math-block {{
      margin: 0 0 20px;
      padding: 16px 18px;
      overflow-x: auto;
      border-radius: 18px;
      border: 1px solid rgba(33, 79, 75, 0.16);
      background: linear-gradient(180deg, rgba(240, 247, 245, 0.94), rgba(232, 241, 238, 0.88));
      color: var(--accent-alt);
    }}

    .prose mjx-container {{
      max-width: 100%;
    }}

    .prose mjx-container[jax="SVG"] {{
      overflow-x: auto;
      overflow-y: hidden;
    }}

    .math-block mjx-container {{
      margin: 0 !important;
    }}

    .footer {{
      margin-top: 28px;
      color: var(--text-soft);
      font-size: 12px;
      text-align: center;
    }}

    @media (max-width: 1080px) {{
      .hero,
      .layout {{
        grid-template-columns: 1fr;
      }}

      .toc-panel {{
        position: static;
      }}
    }}

    @media (max-width: 720px) {{
      .page-shell {{
        padding: 18px 14px 48px;
      }}

      .topbar {{
        border-radius: 22px;
      }}

      .content-area,
      .hero-main,
      .hero-side,
      .toc-panel {{
        padding: 20px;
      }}
    }}

    body[data-theme="night"] {{
      --bg: #131211;
      --bg-strong: #1c1a18;
      --surface: rgba(27, 24, 22, 0.86);
      --surface-strong: rgba(32, 29, 26, 0.94);
      --line: rgba(255, 240, 223, 0.1);
      --line-strong: rgba(255, 240, 223, 0.2);
      --text: #f5eee6;
      --text-muted: #c9bdb0;
      --text-soft: #988b7f;
      --shadow: 0 20px 60px rgba(0, 0, 0, 0.34);
    }}
  </style>
</head>
<body>
  <div class="page-shell">
    <header class="topbar">
      <div class="brand">
        <div class="brand-kicker">Showtime HTML</div>
        <div class="brand-title">{html.escape(title)}</div>
      </div>
      <div class="top-actions">
        <a class="top-link" href="index.html">合并页</a>
        <a class="top-link" href="论文深度讲解稿.html">主讲稿</a>
        <a class="top-link" href="技术解释文档.html">技术解释</a>
        <button class="theme-toggle" id="themeToggle" type="button">主题切换</button>
      </div>
    </header>

    <section class="hero">
      <article class="hero-main">
        <p class="hero-kicker">{html.escape(subtitle)}</p>
        <h1>{html.escape(title)}</h1>
        <p>{html.escape(lead)}</p>
        <div class="quick-links">
          {quick_links_html}
        </div>
      </article>
      <aside class="hero-side">
        <div class="stat-grid">
          {stats_html}
        </div>
      </aside>
    </section>

    <section class="layout">
      <main class="content-area">
        {content_html}
      </main>
      <aside class="toc-panel">
        <h3>目录导航</h3>
        <div class="toc-links">
          {toc_html}
        </div>
      </aside>
    </section>

    <div class="footer">静态构建页由 <code>build_showtime_site.py</code> 生成，可直接部署到 GitHub Pages。</div>
  </div>

  <script>
    const key = "showtime-theme";
    const toggle = document.getElementById("themeToggle");
    const saved = localStorage.getItem(key);
    if (saved === "night") document.body.dataset.theme = "night";
    toggle.addEventListener("click", () => {{
      document.body.dataset.theme = document.body.dataset.theme === "night" ? "" : "night";
      localStorage.setItem(key, document.body.dataset.theme === "night" ? "night" : "day");
    }});

    const links = Array.from(document.querySelectorAll(".toc-link"));
    const sections = links
      .map((link) => document.querySelector(link.getAttribute("href")))
      .filter(Boolean);
    const observer = new IntersectionObserver((entries) => {{
      const visible = entries.filter((entry) => entry.isIntersecting).sort((a, b) => b.intersectionRatio - a.intersectionRatio)[0];
      if (!visible) return;
      links.forEach((link) => {{
        link.classList.toggle("active", link.getAttribute("href") === `#${{visible.target.id}}`);
      }});
    }}, {{ rootMargin: "-30% 0px -55% 0px", threshold: [0.1, 0.3, 0.6] }});
    sections.forEach((section) => observer.observe(section));
  </script>
</body>
</html>
"""


def build_quick_links() -> str:
  links = []
  for label, href in QUICK_LINKS:
    cls = "quick-link alt" if href.startswith("http") else "quick-link"
    links.append(f'<a class="{cls}" href="{href}">{html.escape(label)}</a>')
  return "\n".join(links)


def build_stats(items: list[tuple[str, str, str]]) -> str:
  cards = []
  for label, value, note in items:
    cards.append(
      f"""
      <div class="stat-card">
        <div class="stat-label">{html.escape(label)}</div>
        <div class="stat-value">{html.escape(value)}</div>
        <div class="stat-note">{html.escape(note)}</div>
      </div>
      """
    )
  return "\n".join(cards)


def load_doc(key: str) -> tuple[str, list[dict[str, str]]]:
  meta = DOCS[key]
  markdown_text = (ROOT / meta["file"]).read_text(encoding="utf-8")
  return render_markdown(markdown_text, key)


def render_page(filename: str, title: str, subtitle: str, lead: str, doc_keys: list[str], stat_items: list[tuple[str, str, str]]) -> None:
  rendered_docs = []
  combined_toc = []
  for key in doc_keys:
    body_html, toc = load_doc(key)
    rendered_docs.append(build_doc_section(key, DOCS[key], body_html))
    combined_toc.append({"level": "2", "id": key, "title": DOCS[key]["title"]})
    combined_toc.extend(toc)

  html_text = page_template(
    title=title,
    subtitle=subtitle,
    lead=lead,
    quick_links_html=build_quick_links(),
    toc_html=build_toc(combined_toc),
    content_html="\n".join(rendered_docs),
    stats_html=build_stats(stat_items),
  )
  (ROOT / filename).write_text(html_text, encoding="utf-8")
  print(f"[OK] {filename}")


def main() -> None:
  render_page(
    filename="论文深度讲解稿.html",
    title="推荐曝光结构外部性审计：论文深度讲解稿",
    subtitle="Talk Script",
    lead="主讲页聚焦论文主命题、对象层重写、方法链与解释边界，结果图表在实验完成后按既定版式接入。",
    doc_keys=["lecture"],
    stat_items=[
      ("页面类型", "主讲稿", "面向汇报、预演和公开展示。"),
      ("论文版本", "最新原稿已同步", "对象层、方法链与评估协议全部对齐。"),
      ("配套资料", "2 份技术解释", "对象结构与理论评估分开补充。"),
    ],
  )

  render_page(
    filename="技术解释文档.html",
    title="推荐曝光结构外部性审计：技术解释手册",
    subtitle="Technical Companion",
    lead="技术解释页把对象层、方法链、理论命题与评估协议拆开讲，适合统一研究口径、答疑和对外说明。",
    doc_keys=["method", "protocol"],
    stat_items=[
      ("页面类型", "技术解释", "适合方法与评估口径统一。"),
      ("技术文档", "2 份", "对象结构与理论评估分别展开。"),
      ("部署方式", "静态单页", "可直接托管到 GitHub Pages。"),
    ],
  )

  render_page(
    filename="index.html",
    title="推荐曝光结构外部性审计",
    subtitle="Unified Single Page",
    lead="部署页把主讲稿、技术解释一和技术解释二合并到同一套静态前端中，便于公开展示、内部汇报和统一引用。",
    doc_keys=["lecture", "method", "protocol"],
    stat_items=[
      ("主讲稿", "1 份", "负责汇报节奏、开场口径与收束句。"),
      ("技术解释", "2 份", "分别覆盖对象方法与理论评估。"),
      ("部署入口", "单页合并", "GitHub Pages 直接访问 index.html。"),
    ],
  )


if __name__ == "__main__":
  main()
