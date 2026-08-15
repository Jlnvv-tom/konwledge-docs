#!/usr/bin/env python3
"""为新添加的三个系列目录补齐 sidebar 配置：
1. 创建 _category_.json
2. 给 index.md / contents.md / chapter_N.md 添加 sidebar_position
"""
import os
import re
import json

BASE = os.path.join(os.path.dirname(__file__), '..', 'docs', 'life-encyclopedia')

# 三个新系列：目录名 -> (label, position)
NEW_SERIES = {
    'doctor-of-economics': ('经济学博士通关路', 9),
    'doctor-of-computer-science': ('计算机科学博士通关路', 10),
    'civil-service-examination': ('考公全景手册', 11),
}

def ensure_frontmatter(filepath, position, pagination_label=None):
    """给 md 文件添加 frontmatter sidebar_position"""
    with open(filepath, 'r', encoding='utf-8') as f:
        content = f.read()

    # 已有 frontmatter
    if content.startswith('---'):
        m = re.match(r'^---\n(.*?)\n---\n', content, re.DOTALL)
        if m:
            fm = m.group(1)
            rest = content[m.end():]
            # 已有 sidebar_position 则更新
            if re.search(r'^sidebar_position:', fm, re.MULTILINE):
                fm = re.sub(r'^sidebar_position:.*$', f'sidebar_position: {position}', fm, flags=re.MULTILINE)
            else:
                fm += f'\nsidebar_position: {position}'
            new_content = f'---\n{fm}\n---\n{rest}'
        else:
            new_content = f'---\nsidebar_position: {position}\n---\n\n{content}'
    else:
        # 无 frontmatter，创建
        new_content = f'---\nsidebar_position: {position}\n---\n\n{content}'

    with open(filepath, 'w', encoding='utf-8') as f:
        f.write(new_content)

for dirname, (label, position) in NEW_SERIES.items():
    d = os.path.join(BASE, dirname)
    if not os.path.isdir(d):
        print(f"❌ {dirname} 目录不存在")
        continue

    # 1. 创建 _category_.json
    cat_path = os.path.join(d, '_category_.json')
    if not os.path.exists(cat_path):
        with open(cat_path, 'w', encoding='utf-8') as f:
            json.dump({"label": label, "position": position, "collapsed": True}, f, ensure_ascii=False, indent=2)
        print(f"✅ {dirname}: 创建 _category_.json (label={label}, position={position})")
    else:
        print(f"⚠️  {dirname}: _category_.json 已存在，跳过")

    # 2. 处理文件
    # index.md -> 0
    if os.path.exists(os.path.join(d, 'index.md')):
        ensure_frontmatter(os.path.join(d, 'index.md'), 0)
        print(f"✅ {dirname}/index.md → sidebar_position: 0")

    # contents.md -> 99（最后）
    if os.path.exists(os.path.join(d, 'contents.md')):
        ensure_frontmatter(os.path.join(d, 'contents.md'), 99)
        print(f"✅ {dirname}/contents.md → sidebar_position: 99")

    # chapter_N.md -> N
    chapter_files = [f for f in os.listdir(d) if re.match(r'chapter_(\d+)\.md$', f)]
    for f in chapter_files:
        num = int(re.match(r'chapter_(\d+)\.md$', f).group(1))
        ensure_frontmatter(os.path.join(d, f), num)
    print(f"✅ {dirname}: {len(chapter_files)} 个 chapter 文件已设置 sidebar_position")

print("\n完成！")
