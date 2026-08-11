#!/usr/bin/env python3
"""
将 docs/book 和 docs/handbook 下所有子目录的 index.md 转换为卡片导航页 index.mdx。
保留原标题作为页面标题，用 DocCatalogCards 组件渲染卡片列表。

跳过 browser-work 目录（文章还没生成好）。
"""

import os
import shutil

BASE = "/Users/wujihuan/code/web_workplace/konwledge-docs/docs"
SKIP_DIRS = {"browser-work"}


def get_first_h1(filepath):
    """从 markdown 文件中提取第一个 H1 标题"""
    with open(filepath, "r", encoding="utf-8") as f:
        for line in f:
            if line.startswith("# "):
                return line.strip("# \n")
    return None


def get_description(filepath):
    """提取 H1 后的第一段作为描述"""
    with open(filepath, "r", encoding="utf-8") as f:
        lines = f.readlines()

    found_h1 = False
    desc_lines = []
    for line in lines:
        if line.startswith("# "):
            found_h1 = True
            continue
        if found_h1:
            stripped = line.strip()
            if stripped.startswith("#"):
                break
            if stripped.startswith(">"):
                desc_lines.append(stripped.lstrip("> ").strip())
            elif stripped and not stripped.startswith("---") and not stripped.startswith("|"):
                if not desc_lines and stripped:
                    desc_lines.append(stripped)
                elif desc_lines:
                    break

    return " ".join(desc_lines)[:200] if desc_lines else None


def process_directory(dir_path, dir_name):
    """处理单个目录：将 index.md 转换为 index.mdx 卡片导航页"""
    index_md = os.path.join(dir_path, "index.md")
    index_mdx = os.path.join(dir_path, "index.mdx")

    if not os.path.exists(index_md):
        print(f"  ⚠️  跳过 {dir_name}（无 index.md）")
        return False

    # 提取标题和描述
    title = get_first_h1(index_md) or dir_name
    description = get_description(index_md)

    # 备份原始 index.md
    backup_path = os.path.join(dir_path, "index.original.md")
    if not os.path.exists(backup_path):
        shutil.copy2(index_md, backup_path)

    # 生成新的 index.mdx
    content = f"""---
sidebar_position: 0
pagination_label: 目录
---

import DocCatalogCards from '@site/src/components/DocCatalogCards';

# {title}

"""
    if description:
        content += f"> {description}\n\n"

    content += """<div className="margin-top--lg">
  <DocCatalogCards />
</div>
"""

    # 检查是否已经有 index.mdx
    if os.path.exists(index_mdx):
        print(f"  ℹ️  {dir_name} 已有 index.mdx，将覆盖")

    with open(index_mdx, "w", encoding="utf-8") as f:
        f.write(content)

    # 删除旧的 index.md（避免冲突）
    os.remove(index_md)

    print(f"  ✅ {dir_name} → index.mdx")
    return True


def main():
    book_dir = os.path.join(BASE, "book")
    handbook_dir = os.path.join(BASE, "handbook")

    total = 0

    print("📂 处理 book 目录...")
    for name in sorted(os.listdir(book_dir)):
        dir_path = os.path.join(book_dir, name)
        if not os.path.isdir(dir_path):
            continue
        if name in SKIP_DIRS:
            print(f"  ⏭️  跳过 {name}（指定跳过）")
            continue
        if process_directory(dir_path, name):
            total += 1

    print("\n📂 处理 handbook 目录...")
    for name in sorted(os.listdir(handbook_dir)):
        dir_path = os.path.join(handbook_dir, name)
        if not os.path.isdir(dir_path):
            continue
        if name in SKIP_DIRS:
            print(f"  ⏭️  跳过 {name}（指定跳过）")
            continue
        if process_directory(dir_path, name):
            total += 1

    print(f"\n✨ 完成！共转换 {total} 个目录")


if __name__ == "__main__":
    main()
