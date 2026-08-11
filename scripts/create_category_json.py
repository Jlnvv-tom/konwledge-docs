#!/usr/bin/env python3
"""
为 docs/book 和 docs/handbook 下所有子目录创建 _category_.json，
设置 collapsed: true 使侧边栏默认折叠。
跳过 browser-work 目录。
"""

import os
import json

BASE = "/Users/wujihuan/code/web_workplace/konwledge-docs/docs"
SKIP_DIRS = {"browser-work"}

# book 和 handbook 下子目录的中文名称映射
BOOK_LABELS = {
    "agent-tools": "AI Agent 工具",
    "browser-work": "浏览器工作原理",
    "cat": "猫的知识全书",
    "children": "育儿知识全书",
    "create-audio": "AI 语音与音乐",
    "create-image": "AI 绘画教程",
    "create-video": "AI 视频生成",
    "cross-border-e-commerce": "跨境电商实战",
    "english": "英语学习",
    "future": "互联网未来五年",
    "government": "政府与法治",
    "history": "大明通史",
    "programmer-english": "程序员英语",
    "short_play": "AI 漫剧与短剧",
    "skill-book": "技能之书",
}

HANDBOOK_LABELS = {
    "100_ economy": "经济活动100个核心知识点",
    "100_ economy_development": "中国经济问题100问",
    "100_ interview": "程序员面试100问",
    "100_academic": "AI/ML 研究机构",
    "100_book": "影响人类的100本经典",
    "100_company": "科技巨头与平台公司",
    "100_h5": "H5 前端面试100题",
    "100_location": "100个自然奇观",
    "100_manage": "管理思维模型",
    "100_people": "科技与互联网先驱",
    "agent-fed": "FDE 角色与职业",
    "agent-interview": "Agent 面试题",
    "ai-agent": "AI Agent 学习",
    "ai-agent-dev": "AI Agent 企业应用实战",
    "ai-agent-fullstack": "AI Agent 全栈开发",
    "ai-agent-product": "AI 产品经理特训营",
    "ai-agent-raw": "AI Agent 原生开发",
    "ai-multi-image-video": "AI 多模态生成",
    "ai-product": "产品经理课",
    "ai-sdd": "AI-SDD 实战",
    "ai-tools": "AI 提效工具",
    "canvas-tool": "Canvas 工程全书",
    "cdp": "CDP 学习",
    "economic-principles": "经济学原理",
    "electron": "Electron 学习",
    "fastapi": "FastAPI 学习",
    "go-expert-course": "Go 专家进阶营",
    "go-practice": "Go 实战训练营",
    "golang": "GoLang 学习",
    "langchain": "LangChain 学习",
    "mysql": "MySQL 学习",
    "net_company": "互联网公司图谱",
    "nextjs": "Next.js 开发实战",
    "python": "Python 学习",
    "python-crawler": "Python 高级爬虫",
    "python-llm": "LLM 开发实战",
    "python-mobile-crawler": "Python 移动端爬虫",
    "python-practice": "Python 实战训练营",
    "react-native": "React Native 跨端开发",
    "redis": "Redis 学习",
    "user-cognition": "认知偏差手册",
}


def create_category_json(dir_path, dir_name, label_map):
    """为目录创建 _category_.json"""
    cat_path = os.path.join(dir_path, "_category_.json")

    label = label_map.get(dir_name, dir_name)

    category_data = {
        "label": label,
        "position": 1,
        "collapsed": True,
    }

    with open(cat_path, "w", encoding="utf-8") as f:
        json.dump(category_data, f, ensure_ascii=False, indent=2)
        f.write("\n")

    print(f"  ✅ {dir_name} → _category_.json (label={label})")


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
            print(f"  ⏭️  跳过 {name}")
            continue
        create_category_json(dir_path, name, BOOK_LABELS)
        total += 1

    print("\n📂 处理 handbook 目录...")
    for name in sorted(os.listdir(handbook_dir)):
        dir_path = os.path.join(handbook_dir, name)
        if not os.path.isdir(dir_path):
            continue
        if name in SKIP_DIRS:
            print(f"  ⏭️  跳过 {name}")
            continue
        create_category_json(dir_path, name, HANDBOOK_LABELS)
        total += 1

    print(f"\n✨ 完成！共创建 {total} 个 _category_.json")


if __name__ == "__main__":
    main()
