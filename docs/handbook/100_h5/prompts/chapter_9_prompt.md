# Chapter 9 Writing Prompt

## 写作任务

以技术手册风格，以IP「怕浪猫」的名义写一篇关于「微前端架构」的文章。

## 核心要求

1. 字数控制：6000-8000 字
2. 不使用任何 emoji 或图标符号
3. 段落短小，每段不超过 5-6 行
4. 段落之间不使用 --- 分隔线
5. 专有缩写首次出现需全称英文解释：缩写（Full English Name）
6. 多用表格、流程图（ASCII）、架构图解释核心原理
7. 每个知识点配核心关键代码示例（不超过 30 行）
8. 代码示例标注来源（qiankun 官方文档 / Webpack 官方文档等）
9. 文章结尾附总结表格

## IP 名称规范

- 自我介绍用"我是怕浪猫"
- 第一人称交替使用"我"和"怕浪猫"
- 禁止用"小编"

## 文章结构

#### 第9章：微前端架构

9.1 微前端的定义与解决的问题
- 将巨石前端应用拆分为可独立开发/部署/运行的子应用
- 解决：代码库膨胀、构建慢、部署耦合、团队协作冲突、技术栈演进困难
- 类比微服务理念下沉到前端
- 微前端 vs 微服务对比表
- 适用场景与不适用场景
- 核心代码：微前端基本架构示意图

9.2 主流微前端方案对比：iframe / single-spa / qiankun / Module Federation / Web Components
- iframe：隔离好但体验差
- single-spa：路由级集成，需改造子应用，无隔离
- qiankun：基于 single-spa，增加 JS/CSS 沙箱，接入成本中等
- Module Federation（Webpack 5 原生模块共享）：编译时集成，粒度更细
- Web Components：天然隔离，生态不成熟
- 五种方案全维度对比表格（隔离性/接入成本/性能/技术栈无关性/成熟度）
- 选型决策流程图
- 核心代码：各方案最小化示例

9.3 qiankun 的 JS 沙箱实现原理
- 快照沙箱（Legacy Sandbox）：激活前快照 window，卸载时恢复
- Proxy 沙箱（Proxy Sandbox）：为每个子应用创建 fake window（Proxy 代理）
- 子应用对 window 的操作被拦截记录，卸载时直接丢弃 fake window
- 两种沙箱机制对比表
- Proxy 沙箱工作原理流程图
- 核心代码：简化版 Proxy 沙箱实现

9.4 微前端中的样式隔离方案
- Shadow DOM（最强隔离但样式穿透困难）
- CSS Modules / Scoped CSS（编译时作用域）
- CSS-in-JS（运行时作用域）
- 动态加载/卸载 CSS（qiankun 的 strictStyleIsolation）
- CSS 前缀（postcss-prefix-selector）
- Tailwind / UnoCSS 的 prefix 配置
- 方案对比表格（隔离强度/侵入性/兼容性）
- 核心代码：Shadow DOM 隔离、CSS Modules 配置、动态 CSS 加载/卸载

9.5 微前端的公共依赖与资源共享
- externals + CDN（React/Vue 全局变量）
- Module Federation 的 shared 配置（自动共享依赖，版本协商）
- 微应用间状态共享（全局 Store / CustomEvent / postMessage）
- 版本冲突注意（React 16 vs 17 不能共享实例）
- 资源共享方案对比表
- 核心代码：externals 配置、Module Federation shared 配置、全局状态共享

9.6 微前端的路由方案
- 基座应用注册子应用路由前缀（/app1/*）
- 激活条件匹配时加载子应用
- 子应用路由为相对路径（/app1/pageA）
- History 模式 vs Hash 模式
- 基座负责全局导航/布局，子应用负责内部路由
- 路由级 vs 应用级拆分
- 路由架构图
- 核心代码：基座路由注册、子应用路由配置

9.7 微前端的通信方案
- Props 传递（基座 -> 子应用初始化参数）
- 全局状态库（Redux / Zustand 共享 Store）
- CustomEvent（window.dispatchEvent(new CustomEvent(...))）
- postMessage（iframe 隔离场景）
- 发布/订阅模式（全局 EventBus）
- 生命周期与内存泄漏（子应用卸载时清理监听）
- 方案对比表
- 核心代码：Props 传递、CustomEvent 通讯、EventBus 实现

9.8 微前端的部署方案与 CI/CD
- 基座 + 子应用独立部署到不同 CDN 路径
- 子应用入口 manifest（JSON 描述入口 JS/CSS）
- 基座动态加载子应用入口
- 版本管理（灰度发布、AB 测试、回滚）
- Nginx 路由分发策略
- CDN 缓存策略
- 部署架构图
- 核心代码：manifest.json 格式、Nginx 路由配置、动态加载脚本

9.9 qiankun 子应用接入完整流程
- 子应用导出 bootstrap/mount/unmount 生命周期函数
- export const __POWERED_BY_QIANKUN__ 环境判断
- 打包为 UMD（Universal Module Definition）格式
- public-path 动态修改资源路径
- 基座 registerMicroApps 注册 + start() 启动
- 跨域配置（CORS 允许基座域名）
- 接入流程图
- 核心代码：子应用完整配置（main.js 导出生命周期、webpack UMD 配置、public-path.js）、基座注册

9.10 Module Federation 与 qiankun 的对比与选择
- MF（Module Federation）：Webpack 5 原生、编译时集成、依赖共享、粒度细（组件级）、强绑定 Webpack
- qiankun：运行时集成、技术栈无关、沙箱隔离、粒度粗（应用级）、接入成本低
- 对比表格（集成方式/粒度/隔离/技术栈依赖/依赖共享/适用场景）
- 新项目用 MF，跨技术栈/旧系统迁移用 qiankun
- 核心代码：Module Federation 配置示例（host + remote）

## 互动/收藏/涨粉模块

**开头3秒钩子：**
"微前端不是银弹，但5种方案对比完，你一定能找到适合自己的那一种"
后跟IP自我介绍："我是怕浪猫，一个在微前端架构上踩过无数坑的前端工程师"

**金句（至少3个）：**
> 微前端的本质不是技术问题，是组织协作问题——技术方案只是组织架构在代码层的映射

**收藏触发结构：**
- 对比型："5种微前端方案全维度对比表"
- 步骤型："qiankun接入完整流程7步法"

**结尾CTA：**
1. 收藏引导："这篇微前端方案对比指南，收藏起来做技术选型时直接参考"
2. 互动引导："你的项目用的哪种微前端方案？评论区交流"
3. 追更引导："关注怕浪猫，下期讲用户体验与业务价值" + "系列进度 9/10"

**下章预告：**
"最后一篇拆解骨架屏、SEO、无障碍、错误监控、大文件上传、性能监控看板，从技术到业务的闭环。"

####
