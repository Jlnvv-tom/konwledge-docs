#!/usr/bin/env python3
"""为缺少 sidebar_position 的文章自动添加序号。
按文件名中的数字提取排序值，没有数字的按文件名字母顺序。
"""
import os
import re
import glob

DOCS_DIR = os.path.join(os.path.dirname(__file__), '..', 'docs')

def extract_number(filename):
    """从文件名中提取数字，如 chapter_10.md -> 10, 01_intro.md -> 1"""
    # 找所有数字段，取第一个
    nums = re.findall(r'(\d+)', filename)
    if nums:
        return int(nums[0])
    return None

def has_sidebar_position(filepath):
    """检查文件是否已有 sidebar_position"""
    try:
        with open(filepath, 'r', encoding='utf-8') as f:
            content = f.read(500)  # 只读前500字符，frontmatter 在开头
        return 'sidebar_position' in content
    except:
        return False

def add_sidebar_position(filepath, position):
    """在 frontmatter 中添加 sidebar_position"""
    with open(filepath, 'r', encoding='utf-8') as f:
        content = f.read()
    
    if content.startswith('---'):
        # 有 frontmatter，在 --- 之间插入
        end_idx = content.index('---', 3)
        frontmatter = content[:end_idx]
        rest = content[end_idx:]
        # 在 frontmatter 末尾添加
        new_content = frontmatter + f'sidebar_position: {position}\n' + rest
    else:
        # 没有 frontmatter，创建一个
        new_content = f'---\nsidebar_position: {position}\n---\n\n' + content
    
    with open(filepath, 'w', encoding='utf-8') as f:
        f.write(new_content)

# 收集所有需要处理的目录
dirs_to_process = set()
for ext in ['*.md', '*.mdx']:
    for f in glob.glob(os.path.join(DOCS_DIR, '**', ext), recursive=True):
        basename = os.path.basename(f)
        if basename.startswith('index.'):
            continue
        if not has_sidebar_position(f):
            dirs_to_process.add(os.path.dirname(f))

fixed_count = 0
for d in sorted(dirs_to_process):
    # 收集该目录下所有缺少 sidebar_position 的文件
    files = []
    for ext in ['*.md', '*.mdx']:
        for f in glob.glob(os.path.join(d, ext)):
            basename = os.path.basename(f)
            if basename.startswith('index.'):
                continue
            if not has_sidebar_position(f):
                files.append(f)
    
    if not files:
        continue
    
    # 按文件名中的数字排序，无数字的按文件名
    def sort_key(f):
        num = extract_number(os.path.basename(f))
        if num is not None:
            return (0, num, os.path.basename(f))
        return (1, 0, os.path.basename(f))
    
    files.sort(key=sort_key)
    
    # 分配 position
    # 如果有数字，用数字本身；否则用递增序号
    for i, f in enumerate(files):
        num = extract_number(os.path.basename(f))
        if num is not None:
            pos = num
        else:
            pos = i + 1
        add_sidebar_position(f, pos)
        fixed_count += 1
    
    print(f"  {d}: {len(files)} files fixed")

print(f"\nTotal: {fixed_count} files fixed")
