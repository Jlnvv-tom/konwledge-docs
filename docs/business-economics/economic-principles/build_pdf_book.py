#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
经济学原理 — Markdown → PDF 书籍生成器
将 10 章 Markdown 文件合并为一本格式规范的 PDF 书籍。

修复记录：
- 代码块字体从 Courier 改为 STHeiti（支持中文+框线+箭头字符）
- 框线图形（流程图）改用 STHeiti 字体渲染
- 添加文档目录结构输出
"""

import os
import re
import sys

# 导入 CJK 字体设置
SKILL_SCRIPTS = os.path.expanduser("~/.qclaw/skills/pdf/scripts")
sys.path.insert(0, SKILL_SCRIPTS)
from setup_chinese_pdf import setup_chinese_pdf

from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import ParagraphStyle
from reportlab.lib.enums import TA_CENTER, TA_LEFT, TA_JUSTIFY
from reportlab.lib.units import mm, cm
from reportlab.lib import colors
from reportlab.platypus import (
    SimpleDocTemplate, BaseDocTemplate, PageTemplate, Frame,
    Paragraph, Spacer, PageBreak,
    Table, TableStyle, KeepTogether, Image, Flowable
)
from reportlab.pdfgen import canvas

# ── 1. 初始化中文字体 ──
cn_font, styles = setup_chinese_pdf()

# ── 2. 目录路径 ──
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
OUTPUT_PDF = os.path.join(BASE_DIR, "经济学原理.pdf")

# ── 3. 自定义段落样式 ──
title_style = ParagraphStyle(
    'BookTitle', parent=styles['Title'],
    fontSize=28, leading=40, alignment=TA_CENTER,
    spaceBefore=80*mm, spaceAfter=20*mm,
    textColor=colors.HexColor('#1a1a2e'),
)

subtitle_style = ParagraphStyle(
    'BookSubtitle', parent=styles['Normal'],
    fontSize=14, leading=20, alignment=TA_CENTER,
    spaceAfter=10*mm, textColor=colors.HexColor('#555555'),
)

chapter_title_style = ParagraphStyle(
    'ChapterTitle', parent=styles['Title'],
    fontSize=22, leading=32, alignment=TA_CENTER,
    spaceBefore=30*mm, spaceAfter=15*mm,
    textColor=colors.HexColor('#1a1a2e'),
    fontName=cn_font,
)

h2_style = ParagraphStyle(
    'H2', parent=styles['Heading2'],
    fontSize=16, leading=24, alignment=TA_LEFT,
    spaceBefore=12*mm, spaceAfter=6*mm,
    textColor=colors.HexColor('#16213e'),
    fontName=cn_font,
)

h3_style = ParagraphStyle(
    'H3', parent=styles['Heading3'],
    fontSize=13, leading=20, alignment=TA_LEFT,
    spaceBefore=8*mm, spaceAfter=4*mm,
    textColor=colors.HexColor('#0f3460'),
    fontName=cn_font,
)

body_style = ParagraphStyle(
    'Body', parent=styles['Normal'],
    fontSize=10.5, leading=18, alignment=TA_JUSTIFY,
    spaceAfter=3*mm, firstLineIndent=21,  # 2字符缩进
    textColor=colors.HexColor('#1a1a1a'),
    fontName=cn_font,
)

body_no_indent_style = ParagraphStyle(
    'BodyNoIndent', parent=body_style,
    firstLineIndent=0,
)

# 代码块样式：使用 cn_font (STHeiti) 而非 Courier
# STHeiti 同时支持中文、框线字符(┌─┐│└┘)、箭头字符(▼►◀▶)
code_style = ParagraphStyle(
    'Code', parent=styles['Normal'],
    fontSize=8.5, leading=13, alignment=TA_LEFT,
    leftIndent=8*mm, rightIndent=5*mm,
    spaceBefore=3*mm, spaceAfter=3*mm,
    backColor=colors.HexColor('#f5f5f5'),
    borderWidth=0.5, borderColor=colors.HexColor('#dddddd'),
    borderPadding=6,
    fontName=cn_font,  # 关键修复：用中文字体渲染代码块
    textColor=colors.HexColor('#2d2d2d'),
)

blockquote_style = ParagraphStyle(
    'Blockquote', parent=body_style,
    leftIndent=15*mm, rightIndent=10*mm,
    fontSize=10, leading=16,
    textColor=colors.HexColor('#555555'),
    firstLineIndent=0,
    spaceBefore=3*mm, spaceAfter=3*mm,
    backColor=colors.HexColor('#f9f9f9'),
    borderWidth=0, borderPadding=6,
)

table_header_style = ParagraphStyle(
    'TableHeader', parent=styles['Normal'],
    fontSize=9.5, leading=14, alignment=TA_CENTER,
    textColor=colors.white, fontName=cn_font,
)

table_cell_style = ParagraphStyle(
    'TableCell', parent=styles['Normal'],
    fontSize=9.5, leading=14, alignment=TA_LEFT,
    textColor=colors.HexColor('#333333'), fontName=cn_font,
)

toc_entry_style = ParagraphStyle(
    'TOCEntry', parent=styles['Normal'],
    fontSize=11, leading=20, alignment=TA_LEFT,
    leftIndent=10*mm, fontName=cn_font,
    textColor=colors.HexColor('#333333'),
)

toc_chapter_style = ParagraphStyle(
    'TOCChapter', parent=styles['Normal'],
    fontSize=13, leading=24, alignment=TA_LEFT,
    leftIndent=5*mm, fontName=cn_font,
    textColor=colors.HexColor('#1a1a2e'),
    spaceBefore=5*mm,
)


# ── 4. 书签 Flowable ──
# 用于在 PDF 侧边栏生成可点击的目录树
_bookmark_counter = [0]

class BookmarkFlowable(Flowable):
    """一个零高度 Flowable，在渲染时插入 PDF 书签（outline entry）"""
    def __init__(self, title, level=0, key=None):
        Flowable.__init__(self)
        self.title = title
        self.level = level  # 0=章, 1=节, 2=小节
        _bookmark_counter[0] += 1
        self.key = key or f'bm_{_bookmark_counter[0]}'
        self.width = 0
        self.height = 0

    def wrap(self, availWidth, availHeight):
        return (0, 0)

    def draw(self):
        self.canv.bookmarkPage(self.key)
        self.canv.addOutlineEntry(self.title, self.key, level=self.level, closed=(self.level > 0))


# ── 6. Markdown 预处理函数 ──
def strip_front_matter(md_text):
    """移除 Docusaurus front matter (--- ... ---)"""
    if md_text.startswith('---'):
        end = md_text.find('---', 3)
        if end != -1:
            md_text = md_text[end + 3:].lstrip('\n')
    return md_text


def clean_md_for_book(md_text):
    """清理 Markdown 中不需要的 Docusaurus 专用语法"""
    # 移除 Docusaurus import 语句
    md_text = re.sub(r'^import\s+.*$', '', md_text, flags=re.MULTILINE)
    # 移除 Docusaurus JSX 组件 <DocCatalogCards .../> 等
    md_text = re.sub(r'<DocCatalogCards\s*/?>', '', md_text)
    md_text = re.sub(r'<div\s+className="[^"]*">\s*</div>', '', md_text)
    # 移除 MDX 特有语法
    md_text = re.sub(r'^pagination_label:.*$', '', md_text, flags=re.MULTILINE)
    return md_text


# ── 7. Markdown → ReportLab Flowables 转换 ──
def escape_html(text):
    """转义 HTML 特殊字符"""
    text = text.replace('&', '&amp;')
    text = text.replace('<', '&lt;')
    text = text.replace('>', '&gt;')
    return text


def inline_md_to_reportlab(text):
    """将行内 Markdown 格式转换为 ReportLab Paragraph 支持的 XML 标记"""
    # 先转义 HTML
    text = escape_html(text)
    # 粗体 **text** → <b>text</b>
    text = re.sub(r'\*\*(.+?)\*\*', r'<b>\1</b>', text)
    # 斜体 *text* → <i>text</i>
    text = re.sub(r'(?<!\*)\*(?!\*)(.+?)(?<!\*)\*(?!\*)', r'<i>\1</i>', text)
    # 行内代码 `code` → <font face="cn_font">code</font> (用中文字体确保兼容)
    text = re.sub(r'`([^`]+)`', rf'<font face="{cn_font}" size="9">\1</font>', text)
    # 链接 [text](url) → <a href="url">text</a>
    text = re.sub(r'\[([^\]]+)\]\(([^)]+)\)', r'<a href="\2">\1</a>', text)
    return text


def parse_table(lines, start_idx):
    """解析 Markdown 表格，返回 (table_data, end_idx)"""
    rows = []
    i = start_idx
    while i < len(lines) and '|' in lines[i].strip():
        line = lines[i].strip()
        if line.startswith('|'):
            line = line[1:]
        if line.endswith('|'):
            line = line[:-1]
        cells = [c.strip() for c in line.split('|')]
        rows.append(cells)
        i += 1

    if len(rows) < 2:
        return None, start_idx

    # 第二行是分隔符 (|---|---|)
    header = rows[0]
    data_rows = rows[2:]  # 跳过分隔行

    # 构建 Paragraph cells
    table_data = []
    table_data.append([Paragraph(inline_md_to_reportlab(c), table_header_style) for c in header])
    for row in data_rows:
        table_data.append([Paragraph(inline_md_to_reportlab(c), table_cell_style) for c in row])

    return table_data, i - 1


def md_to_flowables(md_text, chapter_num=None):
    """将 Markdown 文本转换为 ReportLab Flowable 列表，并在标题处插入 PDF 书签"""
    flowables = []
    lines = md_text.split('\n')
    i = 0

    while i < len(lines):
        line = lines[i]
        stripped = line.strip()

        # 跳过空行
        if not stripped:
            i += 1
            continue

        # H1 标题
        if stripped.startswith('# ') and not stripped.startswith('## '):
            title_text = stripped[2:].strip()
            if chapter_num is not None and (title_text.startswith(f'第{chapter_num}章') or re.match(r'^第.+章', title_text) or chapter_num == 1):
                flowables.append(PageBreak())
                # 插入章级书签 (level 0)
                flowables.append(BookmarkFlowable(title_text, level=0))
                flowables.append(Paragraph(inline_md_to_reportlab(title_text), chapter_title_style))
                flowables.append(Spacer(1, 8*mm))
            else:
                flowables.append(BookmarkFlowable(title_text, level=0))
                flowables.append(Paragraph(inline_md_to_reportlab(title_text), chapter_title_style))
                flowables.append(Spacer(1, 8*mm))
            i += 1
            continue

        # H2 标题
        if stripped.startswith('## '):
            title_text = stripped[3:].strip()
            # 插入节级书签 (level 1)
            flowables.append(BookmarkFlowable(title_text, level=1))
            flowables.append(Spacer(1, 4*mm))
            flowables.append(Paragraph(inline_md_to_reportlab(title_text), h2_style))
            flowables.append(Spacer(1, 2*mm))
            i += 1
            continue

        # H3 标题
        if stripped.startswith('### '):
            title_text = stripped[4:].strip()
            # 插入小节级书签 (level 2)
            flowables.append(BookmarkFlowable(title_text, level=2))
            flowables.append(Paragraph(inline_md_to_reportlab(title_text), h3_style))
            i += 1
            continue

        # H4 标题
        if stripped.startswith('#### '):
            title_text = stripped[5:].strip()
            h4_style = ParagraphStyle(
                'H4', parent=h3_style,
                fontSize=11.5, leading=18,
                spaceBefore=5*mm, spaceAfter=2*mm,
            )
            flowables.append(Paragraph(inline_md_to_reportlab(title_text), h4_style))
            i += 1
            continue

        # 代码块
        if stripped.startswith('```'):
            code_lines = []
            i += 1
            while i < len(lines) and not lines[i].strip().startswith('```'):
                code_lines.append(lines[i])
                i += 1
            i += 1  # 跳过结束的 ```
            code_text = '\n'.join(code_lines)
            # 将代码块转换为 Paragraph，保留换行
            code_html = escape_html(code_text).replace('\n', '<br/>')
            # 保留空格（用 &nbsp; 替代，但 reportlab 的 &nbsp; 需要特殊处理）
            code_html = code_html.replace('  ', '&nbsp;&nbsp;')
            code_html = code_html.replace('\t', '&nbsp;&nbsp;&nbsp;&nbsp;')
            flowables.append(Paragraph(code_html, code_style))
            continue

        # 表格
        if '|' in stripped and i + 1 < len(lines) and re.match(r'^[\s\|:-]+$', lines[i + 1].strip()):
            table_data, new_idx = parse_table(lines, i)
            if table_data:
                num_cols = len(table_data[0])
                page_width = A4[0] - 25*mm - 25*mm
                col_width = page_width / num_cols
                col_widths = [col_width] * num_cols

                t = Table(table_data, colWidths=col_widths, repeatRows=1)
                t.setStyle(TableStyle([
                    ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#2E4057')),
                    ('TEXTCOLOR', (0, 0), (-1, 0), colors.white),
                    ('ALIGN', (0, 0), (-1, 0), 'CENTER'),
                    ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
                    ('GRID', (0, 0), (-1, -1), 0.5, colors.HexColor('#cccccc')),
                    ('ROWBACKGROUNDS', (0, 1), (-1, -1), [colors.white, colors.HexColor('#f8f9fa')]),
                    ('TOPPADDING', (0, 0), (-1, -1), 5),
                    ('BOTTOMPADDING', (0, 0), (-1, -1), 5),
                    ('LEFTPADDING', (0, 0), (-1, -1), 6),
                    ('RIGHTPADDING', (0, 0), (-1, -1), 6),
                ]))
                flowables.append(Spacer(1, 3*mm))
                flowables.append(t)
                flowables.append(Spacer(1, 3*mm))
                i = new_idx + 1
                continue

        # 引用块
        if stripped.startswith('>'):
            quote_lines = []
            while i < len(lines) and lines[i].strip().startswith('>'):
                quote_text = lines[i].strip()[1:].strip()
                if quote_text:
                    quote_lines.append(quote_text)
                i += 1
            quote_text = ' '.join(quote_lines)
            flowables.append(Paragraph(inline_md_to_reportlab(quote_text), blockquote_style))
            continue

        # 有序列表
        if re.match(r'^\d+\.\s', stripped):
            while i < len(lines) and re.match(r'^\d+\.\s', lines[i].strip()):
                item_text = re.sub(r'^\d+\.\s', '', lines[i].strip())
                i += 1
                while i < len(lines) and lines[i].strip() and not re.match(r'^\d+\.\s', lines[i].strip()) and not lines[i].strip().startswith('#') and not lines[i].strip().startswith('-'):
                    item_text += ' ' + lines[i].strip()
                    i += 1
                list_style = ParagraphStyle(
                    'ListOL', parent=body_style,
                    leftIndent=15*mm, firstLineIndent=0,
                )
                # 提取序号
                match = re.match(r'^(\d+)\.\s', lines[i - (len(item_text.split()) if False else 1)].strip() if False else '')
                # 更简单的方式：直接用文本中的序号
                pass
            # 重新解析有序列表（上面的逻辑有问题，重写）
            flowables.pop()  # 移除可能错误添加的内容
            # 回退到原始位置重新处理
            # 实际上上面逻辑太复杂了，用简单方式重写
            pass

        # 有序列表 (简化重写)
        if re.match(r'^\d+\.\s', stripped):
            idx_counter = 0
            while i < len(lines) and re.match(r'^\d+\.\s', lines[i].strip()):
                idx_counter += 1
                item_text = re.sub(r'^\d+\.\s*', '', lines[i].strip())
                i += 1
                # 合并续行
                while i < len(lines) and lines[i].strip() and \
                      not re.match(r'^\d+\.\s', lines[i].strip()) and \
                      not lines[i].strip().startswith('#') and \
                      not lines[i].strip().startswith('- ') and \
                      not lines[i].strip().startswith('* ') and \
                      not lines[i].strip().startswith('```') and \
                      not lines[i].strip().startswith('>') and \
                      '|' not in lines[i].strip():
                    item_text += ' ' + lines[i].strip()
                    i += 1
                list_style = ParagraphStyle(
                    'ListOL', parent=body_style,
                    leftIndent=15*mm, firstLineIndent=0,
                )
                flowables.append(Paragraph(f'{idx_counter}. {inline_md_to_reportlab(item_text)}', list_style))
            continue

        # 无序列表
        if stripped.startswith('- ') or stripped.startswith('* '):
            while i < len(lines) and (lines[i].strip().startswith('- ') or lines[i].strip().startswith('* ')):
                item_text = lines[i].strip()[2:]
                i += 1
                # 处理缩进的子项
                while i < len(lines) and lines[i].strip().startswith('  - '):
                    sub_text = lines[i].strip()[4:]
                    i += 1
                    sub_style = ParagraphStyle(
                        'ListULSub', parent=body_style,
                        leftIndent=25*mm, firstLineIndent=0,
                    )
                    flowables.append(Paragraph(f'• {inline_md_to_reportlab(sub_text)}', sub_style))
                list_style = ParagraphStyle(
                    'ListUL', parent=body_style,
                    leftIndent=12*mm, firstLineIndent=0,
                )
                flowables.append(Paragraph(f'• {inline_md_to_reportlab(item_text)}', list_style))
            continue

        # 普通段落（可能是多行）
        para_lines = [stripped]
        i += 1
        while i < len(lines):
            next_line = lines[i].strip()
            if not next_line:
                break
            if next_line.startswith('#') or next_line.startswith('```') or next_line.startswith('>'):
                break
            if next_line.startswith('- ') or next_line.startswith('* '):
                break
            if re.match(r'^\d+\.\s', next_line):
                break
            if '|' in next_line and i + 1 < len(lines) and re.match(r'^[\s\|:-]+$', lines[i + 1].strip()):
                break
            para_lines.append(next_line)
            i += 1

        para_text = ' '.join(para_lines)
        flowables.append(Paragraph(inline_md_to_reportlab(para_text), body_style))

    return flowables


# ── 8. 页码和页眉回调 ──
_total_pages = [0]

def on_page_callback(canv, doc):
    """每页渲染时调用，绘制页码和页眉"""
    page_num = canv.getPageNumber()
    # 封面页不显示页码
    if page_num > 1:
        canv.setFont(cn_font, 9)
        canv.setFillColor(colors.HexColor('#888888'))
        canv.drawCentredString(A4[0] / 2, 15*mm, f'— {page_num} —')

    # 页眉（从第 3 页开始，即目录之后）
    if page_num >= 3:
        canv.setFont(cn_font, 8)
        canv.setFillColor(colors.HexColor('#aaaaaa'))
        canv.drawString(25*mm, A4[1] - 12*mm, '经济学原理')
        canv.drawRightString(A4[0] - 25*mm, A4[1] - 12*mm, '经济学思维实验室')
        # 页眉线
        canv.setStrokeColor(colors.HexColor('#dddddd'))
        canv.setLineWidth(0.3)
        canv.line(25*mm, A4[1] - 14*mm, A4[0] - 25*mm, A4[1] - 14*mm)


# ── 9. 章节信息 ──
CHAPTERS = [
    (1, 'chapter_1.md',  '第1章 经济学最根本的问题'),
    (2, 'chapter_2.md',  '第2章 市场如何运行——供给与需求'),
    (3, 'chapter_3.md',  '第3章 弹性——对价格变化的敏感程度'),
    (4, 'chapter_4.md',  '第4章 消费者如何决策——效用与偏好'),
    (5, 'chapter_5.md',  '第5章 企业与生产——成本与产量'),
    (6, 'chapter_6.md',  '第6章 市场结构——从完全竞争到垄断'),
    (7, 'chapter_7.md',  '第7章 劳动力市场——工资从何而来'),
    (8, 'chapter_8.md',  '第8章 宏观经济指标——读懂 GDP 与通胀'),
    (9, 'chapter_9.md',  '第9章 宏观调控——货币与财政政策'),
    (10, 'chapter_10.md', '第10章 国际贸易与全球化'),
]


# ── 10. 构建目录页 ──
def build_toc():
    """构建目录页"""
    flowables = []
    flowables.append(PageBreak())
    # 目录页书签
    flowables.append(BookmarkFlowable('目录', level=0))
    flowables.append(Paragraph('目 录', ParagraphStyle(
        'TOCTitle', parent=styles['Title'],
        fontSize=22, leading=32, alignment=TA_CENTER,
        spaceBefore=20*mm, spaceAfter=15*mm,
        textColor=colors.HexColor('#1a1a2e'),
        fontName=cn_font,
    )))
    flowables.append(Spacer(1, 10*mm))

    for num, _, title in CHAPTERS:
        flowables.append(Paragraph(title, toc_chapter_style))

    return flowables


# ── 11. 构建封面 ──
def build_cover():
    """构建封面页"""
    flowables = []
    # 封面书签
    flowables.append(BookmarkFlowable('封面', level=0))
    flowables.append(Spacer(1, 60*mm))
    flowables.append(Paragraph('经济学原理', title_style))
    flowables.append(Spacer(1, 10*mm))
    flowables.append(Paragraph('经济学思维实验室', subtitle_style))
    flowables.append(Spacer(1, 5*mm))
    flowables.append(Paragraph('从基础概念到前沿实践的完整知识图谱', subtitle_style))
    flowables.append(Spacer(1, 40*mm))

    # 装饰线
    line_table = Table([['']], colWidths=[60*mm], rowHeights=[2])
    line_table.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, -1), colors.HexColor('#1a1a2e')),
    ]))
    flowables.append(line_table)
    flowables.append(Spacer(1, 8*mm))
    flowables.append(Paragraph('10 章 · 100 题 · 全方位覆盖', subtitle_style))

    return flowables


# ── 12. 输出文档目录结构 ──
def print_doc_structure():
    """输出文档的目录结构"""
    print("\n" + "=" * 70)
    print("📚 文档目录结构")
    print("=" * 70)
    print()
    print("经济学原理.pdf")
    print("├── 封面")
    print("│   └── 经济学原理")
    print("│       └── 经济学思维实验室")
    print("├── 目录")
    for num, _, title in CHAPTERS:
        # 读取每章的 H2 标题作为子目录
        filepath = os.path.join(BASE_DIR, CHAPTERS[num-1][1])
        with open(filepath, 'r', encoding='utf-8') as f:
            md_raw = f.read()
        md_clean = strip_front_matter(md_raw)
        md_clean = clean_md_for_book(md_clean)

        # 提取 H2 标题
        h2_titles = []
        for line in md_clean.split('\n'):
            if line.strip().startswith('## ') and not line.strip().startswith('### '):
                h2_titles.append(line.strip()[3:].strip())

        is_last = (num == len(CHAPTERS))
        prefix = "└──" if is_last else "├──"
        print(f"{prefix} {title}")
        for j, h2 in enumerate(h2_titles):
            h2_last = (j == len(h2_titles) - 1)
            h2_prefix = "    └── " if is_last else "│   └── " if h2_last else "│   ├── "
            if is_last:
                h2_prefix = "    ├── " if not h2_last else "    └── "
            print(f"{h2_prefix}{h2}")
    print()
    print("=" * 70)
    print()


# ── 13. 主流程 ──
def main():
    print(f"开始生成 PDF: {OUTPUT_PDF}")

    # 输出文档目录结构
    print_doc_structure()

    # 使用 BaseDocTemplate 以正确支持 PDF 书签
    doc = BaseDocTemplate(
        OUTPUT_PDF,
        pagesize=A4,
        leftMargin=25*mm,
        rightMargin=25*mm,
        topMargin=22*mm,
        bottomMargin=22*mm,
        title='经济学原理',
        author='经济学思维实验室',
        subject='Economics Principles',
    )

    # 定义页面模板，使用 on_page 回调绘制页码和页眉
    frame = Frame(
        doc.leftMargin, doc.bottomMargin,
        doc.width, doc.height,
        id='normal', showBoundary=0
    )
    template = PageTemplate(id='main', frames=[frame], onPage=on_page_callback)
    doc.addPageTemplates([template])

    story = []

    # 封面
    print("  构建封面...")
    story.extend(build_cover())

    # 目录
    print("  构建目录...")
    story.extend(build_toc())

    # 各章节
    for num, filename, display_title in CHAPTERS:
        print(f"  处理 {display_title} ({filename})...")
        filepath = os.path.join(BASE_DIR, filename)

        with open(filepath, 'r', encoding='utf-8') as f:
            md_raw = f.read()

        # 清理 Markdown
        md_clean = strip_front_matter(md_raw)
        md_clean = clean_md_for_book(md_clean)

        # 转换为 Flowables
        chapter_flowables = md_to_flowables(md_clean, chapter_num=num)
        story.extend(chapter_flowables)

    # 构建 PDF
    print("  构建 PDF...")
    doc.build(story)

    file_size = os.path.getsize(OUTPUT_PDF) / (1024 * 1024)
    print(f"\n✅ PDF 生成完成!")
    print(f"   文件: {OUTPUT_PDF}")
    print(f"   大小: {file_size:.2f} MB")


if __name__ == '__main__':
    main()
