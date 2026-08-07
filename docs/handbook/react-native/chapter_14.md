---
sidebar_position: 14
---

# 第14章 RN工程化、规范化与团队协作开发

> 规范不是束缚开发的枷锁，而是让团队跑得更快的高速公路护栏。

一个三人团队开发RN（React Native）项目，第一周代码风格统一、目录整洁、提交清晰。第二周有人开始用Tab缩进，有人用空格。第三周有人把接口调用写在了组件里，有人写在了工具函数里。第四周新来了一个同学，面对风格各异的代码库问了三个问题：这个文件的组件放哪个目录？接口请求在哪里统一管理？为什么同样的Button组件有三个不同版本？没有人能回答，因为没有人定过规范。一个月后，项目变成了一个谁都不敢轻易动的"屎山"——改一个按钮样式要翻五个文件，加一个页面要先研究半天目录结构，合并代码时冲突到怀疑人生。

这不是个例。我见过太多RN项目，技术选型很先进，功能开发很快速，但工程化层面一塌糊涂。没有代码规范，每个人的写法都是个人风格；没有分支策略，Git（分布式版本控制系统）提交信息像写日记；没有目录约定，文件放在哪全凭心情；没有自动化工具，环境切换靠手动改配置。项目初期觉得"规范太重影响效率"，到了中后期才发现"没有规范才是最大的效率杀手"。一个没有工程化的项目，技术债的增长曲线是指数级的——前三个月跑得飞快，六个月后每加一个功能都要付出成倍的成本。

我是怕浪猫，一个在RN工程化泥潭里摸爬滚打了多年的开发者。从最初一个人单打独斗写代码，到后来带十几个人的团队做企业级RN应用，我经历过规范缺失带来的所有痛苦。也正是因为踩过这些坑，我深刻认识到工程化不是大公司的专利，而是每个想长期迭代的项目都必须做的事。这一章我来系统讲解RN工程化的全套方案，从代码规范到Git协作流程，从自动化脚本到目录架构，从模块化拆分到团队协作机制，帮你建立一套可落地的工程化体系。

## 14.1 RN工程化体系搭建核心意义

### 14.1.1 个人开发与团队开发差异对比

个人开发和团队开发是两种完全不同的工程模式。个人开发追求的是"快"——怎么方便怎么来，配置写死在代码里、组件随手建在页面旁、提交信息写个"fix"就推上去。这些在个人项目里没问题，因为你自己知道每个文件的用途，你知道那个"fix"到底修了什么。但团队开发不一样，你的代码要让别人能看懂，你的修改要让别人能 review，你的结构要让新人能快速上手。

来看一组对比：

```
个人开发模式：
  - 代码风格：个人习惯，无需统一
  - 目录结构：随用随建，够用就行
  - Git提交：信息随意，能追溯即可
  - 环境配置：硬编码或手动切换
  - 依赖管理：按需安装，版本随意
  - 代码审查：自我检查

团队开发模式：
  - 代码风格：统一规范，工具强制
  - 目录结构：约定优先，分层清晰
  - Git提交：规范格式，关联需求
  - 环境配置：脚本管理，一键切换
  - 依赖管理：版本锁定，定期升级
  - 代码审查：PR（Pull Request）评审
```

差异的核心不在于技术，而在于协作。个人开发的代码是写给自己的，团队开发的代码是写给整个团队的。一份代码被阅读的次数远多于被编写的次数，工程化的核心目标就是降低阅读和维护成本。

> 工程化的本质不是引入多先进的工具，而是建立团队共识。工具只是共识的执行者。如果团队对目录结构没有共识，再好的脚手架也救不了混乱的项目。先统一认知，再统一工具，这个顺序不能反。

### 14.1.2 无规范项目的迭代痛点分析

我接手过一个"无规范"RN项目，团队五个人开发了半年。接手第一天的体验是这样的：项目根目录有四个`utils`文件夹——一个在`src/utils`，一个在`src/common/utils`，一个在`src/helpers`，还有一个直接在根目录叫`utils`。搜索一个`formatDate`函数，全局搜出来八处定义，实现各不相同。`package.json`里装了三个状态管理库——Redux、MobX、Zustand，因为不同的人引入了不同的库。最离谱的是，`node_modules`目录下的依赖版本和`package.json`里记录的不一致，因为有人直接在同事电脑上`npm install`了新版本却忘了提交`package-lock.json`。

这种项目的迭代痛点可以归纳为四类：

**代码层面**：风格不统一导致阅读成本高。同一个人的代码在不同时期风格都可能不同，更别说不同人之间。变量命名有驼峰有下划线，引号有单有双，缩进有Tab有空格。Review代码时，光区分格式差异就耗掉一半精力。更严重的是，风格不统一还会导致Git diff噪声过大——两个人改了同一行代码，但因为格式化规则不同，整个文件的diff全是格式变化，真正的逻辑修改反而被淹没了。我在一个项目里见过一次PR产生了3000行diff，实际逻辑改动只有20行，剩下的全是Prettier格式化差异，Review者看到这个diff直接放弃了评审。

**结构层面**：目录混乱导致定位困难。同一个功能的代码散落在不同目录，同一个目录下放着不相关的功能模块。新人上手需要花大量时间理解项目结构，而且往往需要靠问老成员才能搞清楚。

**协作层面**：分支管理混乱导致冲突频发。所有人都在`main`分支上开发，提交互相覆盖。有人习惯一次提交改二十个文件，有人一个标点符号改了就提交一次。合并代码时冲突到怀疑人生，解决冲突又引入新Bug。

**环境层面**：配置管理缺失导致环境不一致。开发环境的接口地址写死在代码里，切换到测试环境要手动改配置文件，经常有人忘记改就提交了。构建产物里混着开发环境的配置，上线后接口全部404。

### 14.1.3 工程化核心能力与建设目标

工程化不是一步到位的，它是一个循序渐进的建设过程。我把RN工程化的核心能力归纳为五个维度：

```
工程化五维能力模型：

  代码规范 ──── ESLint + Prettier + Git Hooks
       │
  目录架构 ──── 分层约定 + 模块聚合 + 命名规范
       │
  版本控制 ──── 分支策略 + 提交规范 + Code Review
       │
  自动工具 ──── 脚本封装 + 环境管理 + 模板生成
       │
  协作流程 ──── 需求拆分 + 接口同步 + 迭代复盘
```

每个维度的建设目标不同：代码规范解决"怎么写"的问题，目录架构解决"放哪里"的问题，版本控制解决"怎么改"的问题，自动工具解决"提效率"的问题，协作流程解决"怎么配合"的问题。五个维度相互支撑，缺一不可。

> 工程化的建设目标不是"完美"，而是"可预期"。一个好的工程化体系，应该让新人能在一天内上手开发，让Review者能聚焦逻辑而非格式，让合并代码变成常规操作而非冒险行为，让环境切换变成一条命令而非手动改文件。可预期性是工程效率的终极指标。

### 14.1.4 中小型项目工程化轻量化方案

不是所有项目都需要重型工程化。三五个人的团队、两三个月的项目周期，搞一套完整的CI/CD（Continuous Integration/Continuous Deployment，持续集成/持续部署）流水线反而是过度工程。中小型项目应该走轻量化路线，抓核心放边缘。

轻量化方案的核心是"三个一"：一套规范、一个脚本、一份约定。

一套规范指的是ESLint（代码检查工具）加Prettier（代码格式化工具）的配置。这是成本最低、收益最高的工程化措施。一个`.eslintrc.js`文件加一个`.prettierrc`文件，就能让全团队代码风格统一。配置文件提交到Git仓库，新人clone下来装好依赖就是统一风格，零沟通成本。

一个脚本指的是环境切换脚本。中小型项目通常有开发、测试、生产三个环境，用脚本管理环境变量切换，避免手动改配置文件。核心实现很简单：

```js
// scripts/switch-env.js
const fs = require('fs');
const env = process.argv[2]; // dev | staging | prod

const envConfig = {
  dev: { API_URL: 'http://localhost:3000', DEBUG: true },
  staging: { API_URL: 'https://staging.api.com', DEBUG: true },
  prod: { API_URL: 'https://api.com', DEBUG: false },
};

const config = envConfig[env];
if (!config) {
  console.error('用法: node scripts/switch-env.js [dev|staging|prod]');
  process.exit(1);
}

const content = Object.entries(config)
  .map(([k, v]) => `${k}=${JSON.stringify(v)}`)
  .join('\n');

fs.writeFileSync('.env', content);
console.log(`环境已切换到: ${env}`);
```

在`package.json`中配好快捷命令：

```json
{
  "scripts": {
    "env:dev": "node scripts/switch-env.js dev",
    "env:staging": "node scripts/switch-env.js staging",
    "env:prod": "node scripts/switch-env.js prod"
  }
}
```

一份约定指的是团队的目录结构约定。不需要复杂的框架约束，大家一致同意一个目录结构，写在README里就行。核心目录结构如下：

```
src/
  components/    # 公共组件
  pages/         # 页面组件
  services/      # 接口请求
  utils/         # 工具函数
  constants/     # 常量定义
  hooks/         # 自定义Hook
  navigation/    # 导航配置
  store/         # 状态管理
```

### 14.1.5 大型项目工程化完整架构设计

大型项目的工程化需要更完整的架构支撑。团队规模超过十人、模块超过二十个、迭代周期以年计时，轻量化方案就不够用了。大型项目的工程化架构需要覆盖从代码到部署的完整链路。

```
大型RN项目工程化架构全景：

  代码规范层 ─── ESLint + Prettier + TypeScript + Husky + lint-staged
       │
  架构分层层 ─── 模块化拆分 + Monorepo管理 + 依赖注入
       │
  版本控制层 ─── GitFlow分支策略 + Conventional Commits提交规范
       │
  自动化层   ─── 环境管理脚本 + 模板生成 + 代码生成器 + 清理工具
       │
  质量保障层 ─── 单元测试 + E2E测试 + Code Review + 静态分析
       │
  持续集成层 ─── CI流水线 + 自动构建 + 自动部署 + 灰度发布
       │
  协作管理层 ─── 需求管理 + 任务看板 + 接口文档 + 迭代复盘
```

大型项目与中小型项目的工程化差异，不在于有没有某个工具，而在于工具之间的联动。例如，`Husky`（Git Hook管理工具）配合`lint-staged`（暂存区检查工具），可以在`git commit`时自动检查暂存区代码是否符合规范，不符合则拒绝提交。这个机制把代码规范从事后检查变成了事前拦截，效果天差地别。

来看大型项目的完整目录架构设计：

```
my-app/
├── src/
│   ├── modules/              # 业务模块（按功能聚合）
│   │   ├── user/             # 用户模块
│   │   │   ├── pages/        # 模块页面
│   │   │   ├── components/   # 模块组件
│   │   │   ├── services/     # 模块接口
│   │   │   ├── hooks/        # 模块Hook
│   │   │   └── index.ts      # 模块导出
│   │   ├── order/            # 订单模块
│   │   └── product/          # 商品模块
│   ├── shared/               # 跨模块共享
│   │   ├── components/       # 全局组件
│   │   ├── utils/            # 工具函数
│   │   ├── constants/        # 全局常量
│   │   └── hooks/            # 全局Hook
│   ├── services/             # 全局API服务
│   ├── navigation/           # 导航配置
│   ├── store/                # 全局状态
│   └── App.tsx               # 应用入口
├── scripts/                  # 工程脚本
├── .eslintrc.js              # ESLint配置
├── .prettierrc               # Prettier配置
├── tsconfig.json             # TS配置
└── package.json
```

这种"模块内聚合、跨模块共享"的结构，既保证了业务模块的内聚性，又避免了公共代码的重复。模块内部的修改不会影响其他模块，新成员只需要理解自己负责的模块就能开始开发。

Monorepo（Monolithic Repository，单体仓库）是大型项目的另一个架构选择。当项目有多个RN应用共享同一套组件库或工具函数时，Monorepo可以让多个包在同一个仓库中管理，共享依赖和配置。常用的Monorepo管理工具有Nx和Turborepo。以Turborepo为例，项目结构如下：

```
monorepo/
├── apps/
│   ├── mobile/          # RN主应用
│   ├── tablet/          # RN平板应用
│   └── web/             # Web应用
├── packages/
│   ├── ui/              # 共享组件库
│   ├── utils/           # 共享工具函数
│   ├── types/           # 共享类型定义
│   └── config/          # 共享配置（ESLint/Prettier/TS）
├── turbo.json           # Turborepo配置
└── package.json
```

Monorepo的核心优势是代码复用和统一管理。多个应用共享同一套组件库，修改一处全应用生效。共享的ESLint和Prettier配置确保所有应用风格一致。但Monorepo也有代价：仓库体积大、CI流水线复杂、权限控制粒度粗。团队规模在十人以下、应用数量不超过两个时，单仓库加模块化拆分就够了，不需要上Monorepo。

> 大型项目的工程化不是锦上添花，而是生存必需。当代码量超过十万行、团队超过十个人时，没有工程化体系的项目会陷入"改一个Bug产出三个Bug"的死循环。工程化的投入不是成本，而是对技术债的预防性投资。越早投入，回报越大。

## 14.2 ESLint+Prettier代码规范约束

### 14.2.1 ESLint规则自定义与初始化配置

ESLint（代码检查工具）是RN工程化的第一道防线。它能在编码阶段就发现语法错误、风格问题和不规范写法，把问题拦截在提交之前。RN项目初始化时已经自带了基础的ESLint配置，但默认配置通常不够用，需要根据团队情况自定义。

初始化ESLint配置：

```bash
# 安装依赖
npm install --save-dev eslint @react-native-community/eslint-config

# 初始化配置文件
npx eslint --init
```

RN项目的ESLint配置文件通常长这样：

```js
// .eslintrc.js
module.exports = {
  root: true,
  extends: '@react-native-community',
  parser: '@typescript-eslint/parser',
  plugins: ['@typescript-eslint', 'react-hooks'],
  rules: {
    // 禁止未使用的变量
    'no-unused-vars': 'off',
    '@typescript-eslint/no-unused-vars': 'warn',
    // React Hooks规则
    'react-hooks/rules-of-hooks': 'error',
    'react-hooks/exhaustive-deps': 'warn',
    // 允许JSX使用任意扩展名
    'react/jsx-filename-extension': [
      1, { extensions: ['.js', '.jsx', '.ts', '.tsx'] }
    ],
    // 禁止console.log，允许console.warn
    'no-console': ['warn', { allow: ['warn', 'error'] }],
  },
};
```

这里有几个踩坑点需要注意。第一，`@typescript-eslint/parser`必须配置，否则ESLint无法解析TypeScript语法。第二，原生的`no-unused-vars`规则对TS文件不生效，需要用`@typescript-eslint/no-unused-vars`替代。第三，`react-hooks/rules-of-hooks`必须设为`error`级别，Hooks使用规则是React的硬性约束，违反会导致运行时崩溃。

自定义规则的关键原则是：规则要少而精，不要为了规范而规范。我曾经见过一个团队配了上百条ESLint规则，结果每次写代码满屏都是警告，开发者最后直接忽略了所有提示。好的规范应该是：`error`级别的规则必须遵守（违反就报错），`warn`级别的规则建议遵守（违反给提示但不阻断），不建议的规则不配。

### 14.2.2 Prettier格式化规则统一配置

ESLint关注的是代码质量（语法错误、不安全写法），Prettier（代码格式化工具）关注的是代码格式（缩进、引号、换行）。两者职责不同，配合使用才能全面覆盖代码规范。

Prettier的配置非常简单，一个`.prettierrc`文件搞定：

```json
{
  "singleQuote": true,
  "trailingComma": "all",
  "bracketSpacing": true,
  "jsxBracketSameLine": false,
  "tabWidth": 2,
  "semi": true,
  "printWidth": 80,
  "arrowParens": "always",
  "endOfLine": "lf"
}
```

每项配置的含义和选择理由：

| 配置项 | 值 | 理由 |
|--------|------|------|
| singleQuote | true | 单引号是RN社区主流风格 |
| trailingComma | all | 多行结尾加逗号，减少Git diff |
| tabWidth | 2 | 2空格缩进，RN社区标准 |
| semi | true | 分号结尾，避免ASI陷阱 |
| printWidth | 80 | 行宽80字符，代码评审友好 |
| arrowParens | always | 箭头函数参数始终加括号 |
| endOfLine | lf | 统一使用LF换行符，避免跨平台问题 |

`trailingComma`设为`all`是一个值得注意的配置。多行数组、对象、参数列表的最后一项加上逗号，这样在末尾新增一项时，Git diff只显示新增的那一行，而不是同时显示上一行从"无逗号"变成"有逗号"。这是一个看似微小的配置，但对Code Review的效率提升非常明显。

### 14.2.3 代码规范冲突问题解决适配

ESLint和Prettier同时使用时，一定会遇到规则冲突。比如ESLint要求箭头函数体用大括号，Prettier可能把它格式化成没有大括号的简写形式。解决冲突的方案是安装`eslint-config-prettier`，它会关闭ESLint中所有与Prettier冲突的格式化规则。

```bash
# 安装冲突解决包
npm install --save-dev eslint-config-prettier eslint-plugin-prettier
```

然后在ESLint配置中添加Prettier集成：

```js
// .eslintrc.js
module.exports = {
  extends: [
    '@react-native-community',
    'plugin:@typescript-eslint/recommended',
    'plugin:prettier/recommended', // 放在最后，覆盖前面的格式化规则
  ],
  // ...其他配置
};
```

`plugin:prettier/recommended`这一行做了三件事：注册`prettier`插件、继承`prettier`规则、把Prettier的格式化问题报告为ESLint的`error`。这样只需要运行`eslint --fix`就能同时修复ESLint和Prettier的问题，不需要两个工具分别运行。

> 工具冲突的本质是职责边界不清晰。ESLint管代码质量，Prettier管代码格式，两个工具的交集区域就是冲突的高发地。解法很简单：让Prettier全权负责格式化，ESLint只管代码质量。`eslint-config-prettier`就是这条边界线的执行者。

### 14.2.4 保存自动格式化功能开启

手动运行格式化命令太低效了。真正的工程化应该做到"保存即格式化"——开发者按`Ctrl+S`（Windows）或`Cmd+S`（macOS）保存文件时，编辑器自动用Prettier格式化代码，同时ESLint自动修复可修复的问题。

VS Code（Visual Studio Code）的配置方式如下，在项目根目录创建`.vscode/settings.json`：

```json
{
  "editor.formatOnSave": true,
  "editor.defaultFormatter": "esbenp.prettier-vscode",
  "editor.codeActionsOnSave": {
    "source.fixAll.eslint": "explicit"
  },
  "[javascript]": {
    "editor.defaultFormatter": "esbenp.prettier-vscode"
  },
  "[typescript]": {
    "editor.defaultFormatter": "esbenp.prettier-vscode"
  },
  "[typescriptreact]": {
    "editor.defaultFormatter": "esbenp.prettier-vscode"
  }
}
```

这个配置要提交到Git仓库，确保所有人使用相同的编辑器配置。如果有人用WebStorm或其他IDE，也需要做类似配置。关键原则是：格式化配置由项目统一管理，而不是依赖个人编辑器设置。

### 14.2.5 团队统一代码规范落地标准

配置文件写好了，怎么确保团队所有人都遵守？仅靠自觉是不够的，必须有工具层面的强制保障。落地的标准流程是：编辑器自动格式化 -> Git Hook提交前检查 -> CI流水线最终校验。

Git Hook层面的强制检查通过`Husky`加`lint-staged`实现：

```bash
# 安装依赖
npm install --save-dev husky lint-staged

# 初始化Husky
npx husky init
```

在`package.json`中添加`lint-staged`配置：

```json
{
  "lint-staged": {
    "*.{js,jsx,ts,tsx}": [
      "eslint --fix",
      "prettier --write"
    ]
  }
}
```

创建`pre-commit` Hook：

```bash
# .husky/pre-commit
npx lint-staged
```

这套机制的工作流程是：开发者执行`git commit`时触发`pre-commit` Hook，`lint-staged`检查暂存区中的文件，对JS/TS文件运行ESLint和Prettier。如果检查不通过，提交被拒绝。开发者需要修复问题后重新提交。这样不合规的代码根本无法进入代码库。

> 规范落地的关键不是写多少文档，而是建立"不合规就不能提交"的强制机制。人都是惰性的，靠Code Review来把关格式问题既浪费精力又容易遗漏。把格式检查交给工具，让Review者把精力放在逻辑审查上，这才是工具和人类各自的正确用法。

**收藏清单：ESLint + Prettier 完整配置模板**

| 文件 | 作用 | 关键配置 |
|------|------|---------|
| .eslintrc.js | 代码质量检查 | extends RN社区配置 + TS插件 + Hooks规则 |
| .prettierrc | 代码格式化 | 单引号 + 2空格 + 80字符宽 + 尾逗号 |
| .vscode/settings.json | 编辑器集成 | 保存自动格式化 + ESLint自动修复 |
| .husky/pre-commit | 提交前拦截 | lint-staged检查暂存区文件 |
| package.json | 依赖和脚本 | husky + lint-staged + eslint + prettier |

## 14.3 Git版本控制与分支协作流程

### 14.3.1 Git基础提交与版本管理规范

Git（分布式版本控制系统）是团队协作的基础设施。但很多人对Git的使用停留在`git add`、`git commit`、`git push`三连击的水平，提交信息要么写"update"要么写"fix bug"，完全无法追溯每次提交做了什么。

规范的提交信息应该遵循Conventional Commits（约定式提交）格式：

```
<type>(<scope>): <subject>

<body>

<footer>
```

其中`type`是提交类型，常用类型如下：

| 类型 | 含义 | 示例 |
|------|------|------|
| feat | 新功能 | feat(auth): 添加指纹登录功能 |
| fix | 修复Bug | fix(home): 修复列表下拉刷新崩溃 |
| docs | 文档更新 | docs(readme): 更新安装说明 |
| style | 代码格式 | style(eslint): 统一缩进为2空格 |
| refactor | 重构 | refactor(api): 接口调用统一走service层 |
| perf | 性能优化 | perf(list): 虚拟列表优化长列表渲染 |
| test | 测试 | test(user): 添加用户模块单元测试 |
| chore | 构建/工具 | chore(deps): 升级react-native到0.74 |

用`commitlint`工具来强制校验提交信息格式：

```bash
# 安装依赖
npm install --save-dev @commitlint/config-conventional @commitlint/cli

# 创建配置文件
echo "module.exports = {extends: ['@commitlint/config-conventional']};" > commitlint.config.js
```

添加`commit-msg` Hook：

```bash
# .husky/commit-msg
npx --no-install commitlint --edit $1
```

这样如果提交信息不符合规范，Git会拒绝提交。比如`git commit -m "修改了登录页面"`会被拒绝，正确的写法是`git commit -m "feat(login): 优化登录页面表单校验逻辑"`。

### 14.3.2 GitFlow分支模型落地实战

GitFlow是一种成熟的分支管理模型，适合中大型团队协作。它的核心思路是用不同类型的分支承载不同的工作流，各分支各司其职、互不干扰。

```
GitFlow分支模型：

  main (生产分支)
    │
    │──── tag: v1.0.0 ──── tag: v1.1.0
    │            │              │
    │       release/1.0    release/1.1
    │            │              │
    develop (开发分支)
      │           │
      ├── feature/user-auth ──┤
      ├── feature/order-list ─┤
      └── feature/product-detail
```

分支类型说明：

- `main`：生产环境分支，只接受`release`和`hotfix`分支合并，每次合并打Tag
- `develop`：开发集成分支，所有`feature`分支最终合并到这里
- `feature/*`：功能分支，从`develop`拉出，开发完成后合并回`develop`
- `release/*`：发布分支，从`develop`拉出，用于发布前的准备工作
- `hotfix/*`：紧急修复分支，从`main`拉出，修复后同时合并到`main`和`develop`

实际落地时的操作流程：

```bash
# 1. 从develop创建功能分支
git checkout develop
git pull origin develop
git checkout -b feature/user-auth

# 2. 在功能分支上开发，完成后提交
git add .
git commit -m "feat(auth): 实现用户认证模块"

# 3. 开发完成后，推送到远程
git push origin feature/user-auth

# 4. 创建Pull Request，合并到develop
# 在Git平台（GitHub/GitLab）上创建PR，Review通过后合并

# 5. 合并后删除本地和远程功能分支
git branch -d feature/user-auth
git push origin --delete feature/user-auth
```

> GitFlow不是唯一选择，但它是最稳的选择。小型团队可以简化为"main + feature"两分支模型，中型团队用标准GitFlow，大型团队在GitFlow基础上加上`epic`分支管理大需求。选哪种取决于团队规模和迭代节奏，但不管选哪种，核心原则不变：生产分支只接受经过Review的代码合并，永远不直接在生产分支上开发。

### 14.3.3 功能分支开发与合并流程

功能分支是日常开发的主战场。一个功能从创建分支到最终合并，要经历"创建分支 -> 开发提交 -> 拉取最新 -> 解决冲突 -> 发起PR -> 代码评审 -> 合并分支"七个步骤。

其中最容易出问题的是"拉取最新"和"解决冲突"两步。很多开发者习惯于一头扎进开发，写了好几天才想起来同步`develop`的最新代码，结果冲突量大到难以解决。正确的做法是每天至少同步一次`develop`的更新：

```bash
# 每天上班第一件事：同步develop最新代码
git checkout develop
git pull origin develop
git checkout feature/user-auth

# 用rebase而非merge同步，保持提交历史线性
git rebase develop

# 如果有冲突，解决后继续
git add .
git rebase --continue

# 强制推送rebase后的分支
git push origin feature/user-auth --force-with-lease
```

这里有一个关键选择：`rebase`还是`merge`？`rebase`会把你的功能分支提交"嫁接"到`develop`最新提交之后，提交历史是线性的、干净的。`merge`会产生一个合并提交，历史是分叉的。团队统一选一种方式即可，我个人推荐`rebase`，因为线性历史更容易追踪和回溯。

`--force-with-lease`比`--force`更安全，它会检查远程分支是否被别人更新过，如果被更新了会拒绝强制推送，避免覆盖别人的提交。

### 14.3.4 代码冲突解决与规避方案

代码冲突是团队协作中不可避免的问题。虽然不可能完全消除冲突，但可以通过合理的规范和工具大幅减少冲突频率和冲突量。

**冲突规避原则一：文件职责单一。** 一个文件只负责一个功能。如果两个人同时修改同一个文件，冲突概率极高。把大文件拆成小文件，每个人负责自己的文件，冲突自然减少。

**冲突规避原则二：频繁同步。** 功能分支不要"憋大招"，每天同步`develop`的更新，小步快跑。冲突越小越容易解决，冲突越大越容易出错。

**冲突规避原则三：分工明确。** 同一功能模块不要两个人同时改。如果必须多人协作，先拆分任务，每人负责不同的文件。

冲突解决时的操作规范：

```bash
# 合并时遇到冲突，先查看冲突文件
git status

# 冲突标记格式：
# <<<<<<< HEAD
# 你的修改
# =======
# 别人的修改
# >>>>>>> develop

# 解决冲突：手动编辑文件，保留正确的代码
# 删除冲突标记 <<<<<<< ======= >>>>>>>

# 解决后标记为已解决
git add <冲突文件>

# 继续合并或rebase
git rebase --continue  # 或 git merge --continue

# 验证解决结果
git diff --cached
```

解决冲突时有一个关键原则：不要盲目选择"我的"或"别人的"，要理解两边修改的意图，合并出正确的代码。我见过太多人解决冲突时直接选"accept current change"或"accept incoming change"，结果丢掉了另一边的功能。解决冲突后一定要跑一遍相关功能的测试，确认两边的修改都保留了。

还有一个高阶技巧：对于频繁冲突的文件，考虑从结构上降低冲突概率。比如一个大的配置文件拆成多个小文件，一个大的样式文件拆成按组件拆分的独立文件。文件越小，两个人同时修改同一文件的概率越低。这就像数据库的行级锁比表级锁效率高一样——粒度越细，并发冲突越少。

> 冲突解决是Code Review的前哨战。一个冲突解决得对不对，不能靠"代码能跑"来判断，而要靠"两边修改的意图是否都保留了"来判断。如果冲突解决后功能缺失了，等到测试发现时排查成本会十倍增长。

### 14.3.5 版本迭代与标签管理规范

版本号管理是发布流程的重要环节。语义化版本（Semantic Versioning，SemVer）是业界通用的版本号规范，格式为`MAJOR.MINOR.PATCH`：

- `MAJOR`：不兼容的API修改（大版本升级）
- `MINOR`：向下兼容的新功能（小版本升级）
- `PATCH`：向下兼容的Bug修复（补丁版本）

每次发布时在`main`分支上打Tag：

```bash
# 发布v1.2.0
git checkout main
git tag -a v1.2.0 -m "release: v1.2.0 用户认证模块上线"

# 推送Tag到远程
git push origin v1.2.0

# 查看所有Tag
git tag -l --sort=-v:refname
```

对于RN应用，版本号还需要和`package.json`中的`version`字段以及原生端的版本配置保持同步。可以写一个脚本自动统一版本号：

```js
// scripts/bump-version.js
const fs = require('fs');
const { execSync } = require('child_process');

const version = process.argv[2];
if (!version) {
  console.error('用法: node scripts/bump-version.js 1.2.0');
  process.exit(1);
}

// 更新 package.json
const pkg = JSON.parse(fs.readFileSync('package.json', 'utf8'));
pkg.version = version;
fs.writeFileSync('package.json', JSON.stringify(pkg, null, 2) + '\n');

// 更新 Android build.gradle
const gradle = fs.readFileSync('android/app/build.gradle', 'utf8');
const updated = gradle
  .replace(/versionCode \d+/, `versionCode ${100 * version.split('.').reduce((a, b) => a * 100 + +b, 0)}`)
  .replace(/versionName "[^"]+"/, `versionName "${version}"`);
fs.writeFileSync('android/app/build.gradle', updated);

// Git提交和打Tag
execSync(`git add -A && git commit -m "chore: bump version to ${version}"`);
execSync(`git tag -a v${version} -m "release v${version}"`);
console.log(`版本已更新到 ${version} 并打Tag`);
```

## 14.4 自动化脚本与工程提效工具

### 14.4.1 package.json自定义脚本开发

`package.json`的`scripts`字段是工程提效的第一站。好的脚本设计能让团队所有人用统一的命令完成复杂的操作，避免"每个人记一套自己的命令"的混乱。

一个规范化RN项目的`scripts`配置：

```json
{
  "scripts": {
    "start": "react-native start",
    "android": "react-native run-android",
    "ios": "react-native run-ios",
    "lint": "eslint src --ext .js,.jsx,.ts,.tsx",
    "lint:fix": "eslint src --ext .js,.jsx,.ts,.tsx --fix",
    "format": "prettier --write \"src/**/*.{js,jsx,ts,tsx,json,md}\"",
    "type-check": "tsc --noEmit",
    "test": "jest",
    "test:coverage": "jest --coverage",
    "env:dev": "node scripts/switch-env.js dev",
    "env:staging": "node scripts/switch-env.js staging",
    "env:prod": "node scripts/switch-env.js prod",
    "clean": "react-native clean",
    "clear-cache": "rm -rf $TMPDIR/metro-* && watchman watch-del-all",
    "pod-install": "cd ios && pod install && cd ..",
    "bump": "node scripts/bump-version.js"
  }
}
```

脚本设计的原则是：命名统一、职责单一、可组合。命名用`namespace:action`格式（如`env:dev`、`test:coverage`），一看就知道是哪个领域的什么操作。每个脚本只做一件事，需要组合操作时用`&&`连接：

```json
{
  "scripts": {
    "precommit": "npm run lint:fix && npm run format && npm run type-check",
    "fresh-start": "npm run clean && npm run env:dev && npm start"
  }
}
```

### 14.4.2 环境变量一键切换脚本封装

前面提到过简单的环境切换脚本，但实际项目中的环境管理更复杂。开发环境需要开启调试工具、Mock数据开关；测试环境需要接入测试服接口、关闭调试工具；生产环境需要关闭所有调试、开启性能监控。

用`react-native-config`库来管理多环境配置：

```bash
npm install react-native-config
```

创建多环境配置文件：

```bash
# .env.dev
API_URL=http://localhost:3000
ENV_NAME=development
ENABLE_DEVTOOLS=true
ENABLE_MOCK=false

# .env.staging
API_URL=https://staging.api.com
ENV_NAME=staging
ENABLE_DEVTOOLS=true
ENABLE_MOCK=false

# .env.prod
API_URL=https://api.com
ENV_NAME=production
ENABLE_DEVTOOLS=false
ENABLE_MOCK=false
```

在代码中通过`react-native-config`读取配置：

```js
import Config from 'react-native-config';

const apiClient = axios.create({
  baseURL: Config.API_URL,
  timeout: 10000,
});

if (Config.ENABLE_DEVTOOLS === 'true') {
  // 开启Flipper或Reactotron调试工具
  require('./config/devtools');
}
```

配合前面的`switch-env.js`脚本，切换环境只需要一条命令：

```bash
npm run env:staging  # 一键切换到测试环境
```

这里有一个踩坑点：`.env`文件必须加入`.gitignore`，不要把环境配置提交到仓库。但可以提交`.env.example`作为模板，列出所有需要的环境变量名但不填值：

```bash
# .env.example（提交到仓库）
API_URL=
ENV_NAME=
ENABLE_DEVTOOLS=
ENABLE_MOCK=
```

> 环境管理最怕的不是配置复杂，而是配置泄漏。生产环境的密钥、接口地址如果通过Git仓库泄漏，后果不堪设想。环境配置和代码分离是工程化的底线原则，任何"先写死后面再改"的想法都是安全隐患。

### 14.4.3 项目模板快速生成脚本开发

团队开发中有很多重复性的创建工作：新建一个页面要创建组件文件、样式文件、接口文件、类型定义文件；新建一个组件要创建组件文件、测试文件、样式文件。手动创建既低效又容易不一致。

写一个模板生成脚本来解决这个问题：

```js
// scripts/generate.js
const fs = require('fs');
const path = require('path');

const type = process.argv[2];  // page | component
const name = process.argv[3];  // 组件/页面名

const templates = {
  page: (n) => ({
    [`${n}.tsx`]: `import React from 'react';\nimport { View, Text } from 'react-native';\nimport styles from './${n}.style';\n\nexport default function ${n}() {\n  return (\n    <View style={styles.container}>\n      <Text>${n}</Text>\n    </View>\n  );\n}`,
    [`${n}.style.ts`]: `import { StyleSheet } from 'react-native';\n\nconst styles = StyleSheet.create({\n  container: { flex: 1 },\n});\n\nexport default styles;`,
  }),
  component: (n) => ({
    [`${n}.tsx`]: `import React from 'react';\nimport { View } from 'react-native';\n\ninterface ${n}Props {\n  // props here\n}\n\nexport function ${n}(props: ${n}Props) {\n  return <View />;\n}`,
  }),
};

const files = templates[type]?.(name);
if (!files) {
  console.error('用法: node scripts/generate.js [page|component] [Name]');
  process.exit(1);
}

const dir = type === 'page' ? `src/pages/${name}` : `src/components/${name}`;
fs.mkdirSync(dir, { recursive: true });

Object.entries(files).forEach(([file, content]) => {
  fs.writeFileSync(path.join(dir, file), content);
});
console.log(`${type} '${name}' 已生成到 ${dir}/`);
```

在`package.json`中添加命令：

```json
{
  "scripts": {
    "gen:page": "node scripts/generate.js page",
    "gen:comp": "node scripts/generate.js component"
  }
}
```

使用方式：

```bash
# 生成一个新页面
npm run gen:page -- UserProfile

# 生成一个新组件
npm run gen:comp -- SearchBar
```

一键生成文件结构和模板代码，所有人创建的文件结构一致，减少了很多不必要的差异。

### 14.4.4 冗余文件清理自动化实现

RN项目迭代过程中会积累大量冗余文件：未使用的组件、过时的工具函数、废弃的页面、临时调试文件。这些垃圾文件不仅增加项目体积，还会干扰搜索和定位。手动清理既容易遗漏又容易误删，需要自动化工具来辅助。

一个简单的冗余文件检测脚本：

```js
// scripts/check-unused.js
const fs = require('fs');
const path = require('path');
const { execSync } = require('child_process');

// 获取src下所有文件
const srcDir = path.resolve(__dirname, '../src');
const allFiles = execSync(`find ${srcDir} -name "*.tsx" -o -name "*.ts"`)
  .toString().trim().split('\n');

// 检查每个文件是否被其他文件import引用
const unused = allFiles.filter(file => {
  const basename = path.basename(file, path.extname(file));
  // 排除index文件（通常作为模块入口被引用）
  if (basename === 'index') return false;
  // 搜索文件名在项目中被引用的次数
  const escapedName = basename.replace(/[.*+?^${}()|[\]\\]/g, '\\$&');
  const result = execSync(
    `grep -r "${escapedName}" ${srcDir} --include="*.ts" --include="*.tsx" -l`
  ).toString().trim().split('\n');
  // 如果只在自身文件中出现，则未被引用
  return result.length === 1 && result[0] === file;
});

console.log(`发现 ${unused.length} 个可能未使用的文件:`);
unused.forEach(f => console.log(`  ${path.relative(path.resolve(__dirname, '..'), f)}`));
```

这个脚本不是百分百准确（动态import、字符串拼接的路径名无法检测），但能帮你快速定位到大量明显的冗余文件。人工确认后再删除，比逐个文件排查高效得多。

> 自动化的本质是把人的重复劳动交给机器。开发者最值钱的是注意力和创造力，把这些浪费在"创建文件模板""检查文件是否使用"这种机械操作上是巨大的浪费。每写一个自动化脚本，就是在为团队的未来节省时间。

### 14.4.5 本地开发自动化提效方案

除了脚本工具，本地开发还有很多自动化提效方案。Metro配置优化是其中重要的一环。Metro是RN的打包工具，合理配置能大幅提升开发体验。

```js
// metro.config.js
const { getDefaultConfig } = require('metro-config');

module.exports = (async () => {
  const defaultConfig = await getDefaultConfig();
  return {
    ...defaultConfig,
    resolver: {
      ...defaultConfig.resolver,
      // 配置路径别名，避免深层级../../../引用
      extraNodeModules: {
        '@components': path.resolve(__dirname, 'src/components'),
        '@pages': path.resolve(__dirname, 'src/pages'),
        '@utils': path.resolve(__dirname, 'src/utils'),
        '@services': path.resolve(__dirname, 'src/services'),
        '@assets': path.resolve(__dirname, 'src/assets'),
        '@constants': path.resolve(__dirname, 'src/constants'),
      },
    },
    server: {
      ...defaultConfig.server,
      // 开启端口复用，避免重启时端口占用
      port: 8081,
    },
  };
})();
```

配合`tsconfig.json`的路径映射：

```json
{
  "compilerOptions": {
    "baseUrl": ".",
    "paths": {
      "@components/*": ["src/components/*"],
      "@pages/*": ["src/pages/*"],
      "@utils/*": ["src/utils/*"],
      "@services/*": ["src/services/*"],
      "@assets/*": ["src/assets/*"],
      "@constants/*": ["src/constants/*"]
    }
  }
}
```

配置好路径别名后，import语句从：

```js
import { Button } from '../../../../components/Button';
```

变成：

```js
import { Button } from '@components/Button';
```

文件移动位置时import路径不变，引用关系更稳定，搜索更方便。

除了路径别名，还可以配置`alias`在Babel层面做模块解析，确保Metro和Babel的路径解析行为一致。在`babel.config.js`中添加：

```js
// babel.config.js
module.exports = {
  presets: ['module:metro-react-native-babel-preset'],
  plugins: [
    [
      'module-resolver',
      {
        root: ['./src'],
        alias: {
          '@components': './src/components',
          '@pages': './src/pages',
          '@utils': './src/utils',
          '@services': './src/services',
        },
      },
    ],
  ],
};
```

需要安装`babel-plugin-module-resolver`。配置好Babel和Metro的路径解析后，编辑器跳转、自动补全、TypeScript类型检查都能正确工作，开发体验显著提升。路径别名是"投入十分钟、收益每一天"的提效方案。

## 14.5 项目模块化与目录架构规范

### 14.5.1 页面、组件、工具分层规范

分层是目录架构的基础。好的分层让每个文件都知道自己该放在哪里，每个新人都能快速找到想找的代码。RN项目的经典分层是"页面层 - 组件层 - 工具层"三层结构。

```
分层架构与职责边界：

  ┌─────────────────────────────────┐
  │         Pages（页面层）          │
  │   路由页面、业务逻辑编排          │
  │   可以调用 Components 和 Utils   │
  ├─────────────────────────────────┤
  │       Components（组件层）       │
  │   UI展示、用户交互               │
  │   不包含业务逻辑，只接收props     │
  ├─────────────────────────────────┤
  │        Utils（工具层）           │
  │   纯函数、无副作用               │
  │   可被任何层调用                 │
  ├─────────────────────────────────┤
  │       Services（服务层）         │
  │   接口请求、数据转换              │
  │   只被 Pages 层调用              │
  └─────────────────────────────────┘
```

分层的关键原则是**依赖方向只能向下**。页面层可以调用组件层和工具层，组件层只能调用工具层，工具层不依赖任何上层。如果组件层需要调用接口，不是直接调service，而是通过回调或事件把请求委托给页面层处理。这样保证了组件的纯展示性，也让组件可以在不同页面复用而不产生副作用依赖。

来看一个反例和正例的对比：

```js
// 反例：组件内直接调用接口，耦合业务逻辑
function UserAvatar({ userId }) {
  const [avatar, setAvatar] = useState(null);
  useEffect(() => {
    // 组件直接依赖了具体的API，无法复用到其他场景
    fetchUserAvatar(userId).then(setAvatar);
  }, [userId]);
  return <Image source={{ uri: avatar }} />;
}

// 正例：组件只负责展示，数据由父组件传入
function UserAvatar({ uri }) {
  return <Image source={{ uri }} />;
}
// 页面层负责数据获取
function UserPage() {
  const [uri, setUri] = useState(null);
  useEffect(() => { fetchUserAvatar(userId).then(setUri); }, []);
  return <UserAvatar uri={uri} />;
}
```

### 14.5.2 业务模块拆分与目录聚合

当项目变大时，按"页面/组件/工具"横向分层会导致同一个功能的文件散落在不同目录。用户相关的页面在`pages/`，用户相关的组件在`components/`，用户相关的接口在`services/`——改一个用户功能要翻三个目录。这时候需要按业务模块纵向聚合。

```
按功能聚合的目录结构：

  src/modules/
    user/                  # 用户模块
      pages/               # 用户相关页面
        Login.tsx
        Profile.tsx
      components/           # 用户相关组件
        UserAvatar.tsx
        UserCard.tsx
      services/             # 用户相关接口
        userApi.ts
      hooks/                # 用户相关Hook
        useUser.ts
      types.ts              # 用户类型定义
      index.ts              # 模块统一导出
    order/                  # 订单模块
      pages/
      components/
      services/
      hooks/
      types.ts
      index.ts
```

每个模块是一个自包含的单元，模块内部的修改不影响其他模块。模块通过`index.ts`对外暴露API，其他模块只通过`index.ts`访问，不直接引用模块内部文件：

```js
// src/modules/user/index.ts
export { default as LoginPage } from './pages/Login';
export { default as ProfilePage } from './pages/Profile';
export { UserAvatar } from './components/UserAvatar';
export { useUser } from './hooks/useUser';
export type { UserInfo } from './types';
```

其他模块引用方式：

```js
// 正确：通过模块入口引用
import { UserAvatar, useUser } from '@modules/user';

// 错误：直接引用模块内部文件
import UserAvatar from '@modules/user/components/UserAvatar';
```

这种约束可以用ESLint的`no-restricted-imports`规则来强制：

```js
// .eslintrc.js
module.exports = {
  rules: {
    'no-restricted-imports': ['error', {
      patterns: ['@modules/*/!(index)'],
    }],
  },
};
```

模块间的数据流也应该规范化。一个模块的页面需要调用另一个模块的接口时，不要直接import另一个模块的service文件，而是通过模块导出的Hook或回调来访问。比如用户模块需要获取订单列表，不应该直接import订单模块的`orderApi`，而是通过订单模块导出的`useOrderList` Hook来获取。这样模块间的依赖只通过公共接口，内部实现可以自由变更而不影响其他模块。这和面向对象编程中"依赖抽象不依赖具体实现"的原则是一致的。

> 模块化的核心不是"怎么拆"，而是"怎么封边界"。拆分文件容易，定义清楚模块之间的访问边界才是难点。好的边界设计让模块可以独立开发、独立测试、独立替换，就像乐高积木一样，每个积木块都是一个完整的功能单元。

### 14.5.3 静态资源、常量统一管理

静态资源和常量的管理看似小事，但直接影响代码的可维护性。图片散落在各处、常量硬编码在代码里、颜色值到处都是魔法数字——这些问题在项目初期不明显，但在迭代几个月后会成为维护噩梦。

静态资源统一管理：

```
src/assets/
  images/         # 图片资源
    icons/        # 图标
    backgrounds/  # 背景图
    logos/        # Logo
  fonts/          # 字体文件
  animations/     # Lottie动画JSON文件
```

配合一个资源索引文件统一导出：

```ts
// src/assets/index.ts
const images = {
  logo: require('./images/logos/logo.png'),
  loginBg: require('./images/backgrounds/login-bg.png'),
  avatarDefault: require('./images/icons/avatar-default.png'),
};

const icons = {
  home: require('./images/icons/home.png'),
  search: require('./images/icons/search.png'),
  profile: require('./images/icons/profile.png'),
};

export { images, icons };
```

使用时统一引用：

```ts
import { images, icons } from '@assets';

<Image source={images.logo} />
<Image source={icons.home} />
```

常量统一管理：

```ts
// src/constants/index.ts
export const COLORS = {
  primary: '#1890FF',
  secondary: '#52C41A',
  danger: '#FF4D4F',
  warning: '#FAAD14',
  textPrimary: '#333333',
  textSecondary: '#666666',
  textHint: '#999999',
  background: '#F5F5F5',
  border: '#E8E8E8',
} as const;

export const SPACING = {
  xs: 4,
  sm: 8,
  md: 16,
  lg: 24,
  xl: 32,
} as const;

export const API = {
  TIMEOUT: 10000,
  RETRY_COUNT: 3,
  PAGE_SIZE: 20,
} as const;

export const STORAGE_KEYS = {
  TOKEN: 'user_token',
  USER_INFO: 'user_info',
  THEME: 'app_theme',
} as const;
```

用`as const`断言让TypeScript推断出字面量类型而非宽泛的`string`和`number`，使用时有类型提示和拼写检查。

主题配置也应该统一管理。RN项目通常会有亮色和暗色两种主题，颜色值不应该散落在各个组件的样式文件里，而是集中到主题配置中：

```ts
// src/theme/colors.ts
export const lightTheme = {
  primary: '#1890FF',
  background: '#FFFFFF',
  text: '#333333',
  border: '#E8E8E8',
};

export const darkTheme = {
  primary: '#096DD9',
  background: '#1F1F1F',
  text: '#E8E8E8',
  border: '#434343',
};
```

组件中通过主题Context获取颜色，而不是直接引用颜色值。这样切换主题时只需要切换Context的值，所有组件自动响应。这也体现了常量统一管理的核心思想：值定义在一处，使用在多处，修改时只改一处。

### 14.5.4 接口API模块化拆分规范

接口管理是RN项目工程化的重要环节。接口散落在各个页面文件里、URL硬编码、没有统一的请求/响应类型定义——这些问题会导致接口修改时需要全局搜索，极易遗漏。

规范的API模块化拆分结构：

```
src/services/
  request.ts          # 封装axios/fetch，统一拦截器
  types.ts            # 公共API类型定义
  user/
    userApi.ts        # 用户相关接口
    userTypes.ts      # 用户接口类型
  order/
    orderApi.ts       # 订单相关接口
    orderTypes.ts     # 订单接口类型
  index.ts            # 统一导出
```

接口定义规范：

```ts
// src/services/user/userTypes.ts
export interface LoginParams {
  username: string;
  password: string;
}

export interface LoginResult {
  token: string;
  userInfo: UserInfo;
}

// src/services/user/userApi.ts
import { request } from '../request';
import type { LoginParams, LoginResult } from './userTypes';

export const userApi = {
  login: (params: LoginParams) =>
    request.post<LoginResult>('/auth/login', params),

  getProfile: () =>
    request.get<UserInfo>('/user/profile'),

  updateProfile: (data: Partial<UserInfo>) =>
    request.put<UserInfo>('/user/profile', data),
};
```

```ts
// src/services/index.ts
export { userApi } from './user/userApi';
export { orderApi } from './order/orderApi';
export type { LoginParams, LoginResult } from './user/userTypes';
export type { OrderInfo } from './order/orderTypes';
```

页面中使用：

```ts
import { userApi } from '@services';

const handleLogin = async () => {
  const result = await userApi.login({ username, password });
  // result 有完整的类型提示
  saveToken(result.token);
  navigation.navigate('Home');
};
```

这种规范的好处是：接口修改时只需要改一个文件，类型变更会自动传播到所有调用处，URL集中管理不会散落各处。还有一个容易被忽视的细节：接口请求函数的命名应该统一规范，推荐使用`动词+名词`格式，如`getUserList`、`createOrder`、`updateProfile`、`deleteAddress`。这样看到函数名就知道这个接口做什么操作，不需要去看具体实现。避免使用`fetchData`、`requestData`这种无意义命名——每个接口都叫`fetchData`，调试时搜索都搜不到。

### 14.5.5 大型项目目录架构最优实践

把前面所有规范整合起来，形成一个完整的大型项目目录架构：

```
my-app/
├── src/
│   ├── modules/               # 业务模块（按功能聚合）
│   │   ├── user/
│   │   │   ├── pages/
│   │   │   ├── components/
│   │   │   ├── services/
│   │   │   ├── hooks/
│   │   │   ├── types.ts
│   │   │   └── index.ts
│   │   ├── order/
│   │   └── product/
│   ├── shared/                # 跨模块共享资源
│   │   ├── components/        # 全局公共组件
│   │   │   ├── Button/
│   │   │   ├── Input/
│   │   │   └── Loading/
│   │   ├── hooks/             # 全局Hook
│   │   ├── utils/             # 工具函数
│   │   └── constants/         # 全局常量
│   ├── services/              # 全局API服务
│   │   ├── request.ts         # 请求封装
│   │   └── interceptor.ts     # 拦截器
│   ├── navigation/            # 导航配置
│   │   ├── AppNavigator.tsx
│   │   └── routes.ts
│   ├── store/                 # 全局状态管理
│   │   ├── index.ts
│   │   └── slices/
│   ├── assets/                # 静态资源
│   │   ├── images/
│   │   ├── fonts/
│   │   └── animations/
│   ├── theme/                 # 主题配置
│   │   ├── colors.ts
│   │   ├── spacing.ts
│   │   └── index.ts
│   ├── types/                 # 全局类型定义
│   │   └── common.ts
│   └── App.tsx                # 应用入口
├── scripts/                   # 工程脚本
│   ├── switch-env.js
│   ├── generate.js
│   ├── bump-version.js
│   └── check-unused.js
├── .vscode/                   # 编辑器配置
│   └── settings.json
├── .husky/                    # Git Hooks
│   ├── pre-commit
│   └── commit-msg
├── .eslintrc.js              # ESLint配置
├── .prettierrc               # Prettier配置
├── .env.example              # 环境变量模板
├── tsconfig.json             # TypeScript配置
├── metro.config.js           # Metro配置
└── package.json
```

> 目录架构不是一开始就设计完美的，而是随着项目演进不断调整的。但调整的前提是有一个清晰的初始架构。初始架构的价值不在于它多完美，而在于它给了所有人一个共同的起点。从这个起点出发，团队可以有条不紊地演进架构，而不是在混乱中挣扎。

## 14.6 团队协作规范与迭代复盘

### 14.6.1 组件开发与提交评审规范

代码评审（Code Review）是团队协作中质量保障的核心环节。但很多团队的Code Review流于形式——Review者看一眼"代码能跑"就Approve，或者只挑格式问题不看业务逻辑。有效的Code Review需要明确的评审标准和流程。

Code Review的评审清单：

```
代码评审核心检查项：

  功能正确性
    - 逻辑是否正确实现需求
    - 边界条件是否处理
    - 错误场景是否有兜底

  代码可读性
    - 命名是否清晰达意
    - 复杂逻辑是否有注释
    - 函数是否过长需要拆分

  性能安全
    - 是否有内存泄漏风险
    - 列表是否使用了key属性
    - 敏感信息是否硬编码

  架构一致性
    - 分层是否正确（组件不调接口）
    - 模块边界是否遵守
    - 是否复用了已有组件
```

Pull Request的模板设计：

```markdown
## PR 描述

### 变更类型
- [ ] 新功能
- [ ] Bug修复
- [ ] 重构
- [ ] 其他

### 变更说明
<!-- 简述本次修改的内容和原因 -->

### 关联需求
<!-- 关联的Jira/Issue链接 -->

### 自检清单
- [ ] 代码通过ESLint检查
- [ ] 已添加必要的类型定义
- [ ] 已处理错误场景
- [ ] 已更新相关文档
```

PR的规模控制也很重要。一个PR改几十个文件、上千行代码，Review者根本看不过来。合理的PR规模应该在400行以内，超过的话应该拆分成多个PR。如果一个大功能确实需要上千行代码，可以按模块拆分PR——先合基础设施，再合业务逻辑，最后合UI层。

Review者的心态也很关键。我在团队里推行过一个原则：Review时假设这段代码会在线上出Bug，你会怎么审查？带着这个心态去看代码，你会发现很多"看起来没问题"的代码其实暗藏隐患。比如未处理的Promise rejection、可能为null的引用、没有loading状态的异步操作、列表没有key属性的渲染。这些在功能测试时可能不会暴露，但在线上高并发或异常场景下就会爆雷。

### 14.6.2 接口文档同步与协作标准

前后端协作中，接口文档是双方的契约。但实际开发中，接口文档和实际实现不一致是最常见的问题。后端改了接口忘了更新文档，前端按文档写完发现接口对不上，联调时互相甩锅。

接口文档同步的核心原则是"文档先行"——在写代码之前先定好接口契约，双方都按契约开发。推荐使用Apifox或YApi等接口管理平台，接口定义由后端维护，前端实时查看。

接口定义规范示例：

```ts
// 接口契约定义
/**
 * 用户登录接口
 * @method POST
 * @url /auth/login
 * @request Content-Type: application/json
 *
 * @param {string} username - 用户名
 * @param {string} password - 密码（MD5加密）
 *
 * @response 200
 * @returns {Object} result
 * @returns {string} result.token - 认证令牌
 * @returns {Object} result.userInfo - 用户信息
 * @returns {number} result.userInfo.id - 用户ID
 * @returns {string} result.userInfo.name - 用户名
 * @returns {string} result.userInfo.avatar - 头像URL
 *
 * @response 400
 * @returns {Object} error
 * @returns {number} error.code - 错误码
 * @returns {string} error.message - 错误信息
 */
```

前后端协作流程标准化：

```
需求评审 → 接口设计 → 接口评审 → 前后端并行开发 → 联调 → 测试

  接口设计阶段：后端定义接口契约，输出接口文档
  接口评审阶段：前后端共同评审接口，确认字段和逻辑
  并行开发阶段：前端按文档Mock数据开发，后端按文档实现
  联调阶段：前端切换到真实接口，排查差异
```

> 接口文档不是"写完就完"的产物，而是"持续维护"的契约。任何接口变更必须先改文档，再改代码。这个顺序不能反——先改代码后补文档，文档永远滞后于实现，最后文档就失去了可信度，前后端协作又回到了"口口相传"的原始状态。

### 14.6.3 版本迭代任务拆分与排期

版本迭代的任务拆分直接影响了开发效率和质量。任务拆得太粗，一个人扛一个"大模块"，风险集中、进度不可控；拆得太细，沟通协调成本激增、碎片化严重。合理的拆分粒度是：一个任务1-3天能完成，有明确的交付物。

任务拆分的方法论：

```
需求拆分维度：

  按页面拆：一个完整页面为一个任务
  按功能拆：一个独立功能为一个任务
  按层级拆：接口层、页面层、组件层分别拆分

  拆分原则：
  - 每个任务有明确的验收标准
  - 任务之间依赖关系清晰
  - 单个任务不超过3天
  - 任务可独立测试
```

排期时需要考虑的关键因素：

- 接口依赖：前端依赖后端接口的任务，先用Mock数据开发，联调时间单列
- 设计依赖：依赖设计稿的任务，设计稿评审通过后才能开始
- 技术风险：新技术方案或复杂逻辑需要预留调研时间
- 测试时间：每个迭代预留20%的时间给测试和Bug修复

### 14.6.4 线上问题复盘与规范迭代

线上问题是工程化体系最好的试金石。每次线上问题都不是孤立的Bug，而是工程化体系中某个环节缺失的体现。做好线上问题复盘，能推动工程化体系持续进化。

线上问题复盘的标准流程：

```
问题发现 → 紧急修复 → 根因分析 → 规范改进 → 落地验证

  问题发现：记录问题现象、影响范围、发现时间
  紧急修复：止血优先，先恢复服务再查根因
  根因分析：5 Why分析法，追到根本原因
  规范改进：制定防范措施，更新规范文档
  落地验证：在下一个迭代中执行改进措施
```

复盘文档模板：

```markdown
## 线上问题复盘 - [问题标题]

### 基本信息
- 发生时间：2024-XX-XX
- 影响范围：XX用户，XX功能不可用
- 持续时间：XX分钟
- 严重级别：P0/P1/P2

### 问题现象
<!-- 描述用户看到的现象和报错信息 -->

### 根因分析
1. 为什么会出现这个问题？
2. 为什么测试阶段没发现？
3. 为什么现有的规范没有防范住？

### 改进措施
- [ ] 代码层面：XX修复
- [ ] 规范层面：新增XX检查规则
- [ ] 流程层面：新增XX测试用例
- [ ] 监控层面：新增XX告警

### 责任与追踪
- 改进措施负责人：XXX
- 完成截止时间：XXXX-XX-XX
```

> 每一个线上问题都是工程化体系的"体检报告"。问题的根因不在于"谁写错了代码"，而在于"什么机制让错误代码得以上线"。复盘的目的不是追责，而是完善机制。如果一个同样的Bug能出现两次，说明复盘的改进措施没有真正落地。

### 14.6.5 工程化体系持续优化思路

工程化不是一次性工程，而是持续演进的过程。随着团队规模变化、项目复杂度增长、技术栈升级，工程化体系也需要随之调整。

持续优化的思路：

**定期审计。** 每季度对工程化体系做一次全面审计：ESLint规则是否还适用？目录结构是否需要调整？自动化脚本是否覆盖了最新的重复操作？团队协作流程是否有新的痛点？审计的结果形成改进计划，在后续迭代中逐步落地。

**指标驱动。** 用数据衡量工程化效果：编译时间、构建成功率、Bug修复平均时间、新成员上手时间、代码冲突频率等。指标恶化的地方就是需要优化的地方。

**技术雷达。** 关注RN社区的新工具和新方案，定期评估是否引入。但引入新工具的原则是"解决实际痛点"而非"追求新技术"。每个新工具的引入都应该明确回答：它解决了什么问题？引入成本是多少？团队是否能接受？

分享一个实际案例：我们团队曾经在每次迭代结束时花两天时间手动整理变更日志（Changelog），漏记和错记频繁。后来引入了`changesets`工具，在开发阶段就记录变更，发布时自动生成Changelog。两天的工作量缩短到了半小时，这就是工具提效的典型案例。但同样的工具放到一个两周一迭代的小项目里，可能引入和配置的成本就超过了节省的时间，反而得不偿失。工具选型永远要结合团队和项目的实际情况。

```
工程化体系演进路线图：

  初期（1-3月）：ESLint + Prettier + 目录规范 + 环境脚本
        ↓
  中期（3-6月）：GitFlow + Commitlint + 模块化拆分 + 模板生成
        ↓
  成熟期（6-12月）：CI/CD + 自动化测试 + 代码质量分析 + 灰度发布
        ↓
  精进期（12月+）：Monorepo + 微前端 + 性能监控 + 智能化工具
```

工程化的终极目标不是"工具多先进"，而是"团队跑得快且稳"。每一项工程化措施都应该能回答：它让团队更快了吗？它让代码更稳了吗？如果答案是否定的，那这个措施就是过度工程化，该砍就砍。

有一个容易踩的坑："工具链膨胀"。我见过一个团队引入了十几个开发工具——ESLint、Prettier、Stylelint、Commitlint、Husky、lint-staged、Semantic Release、Changesets、Danger、CodeOwner——每个工具单独看都有价值，但组合在一起后，开发者每次提交代码要等30秒的Hook检查，CI流水线跑15分钟，新成员配置开发环境要半天。工具链本身成了效率瓶颈。正确的做法是定期评估每个工具的投入产出比，移除那些"看起来高级但实际没用"的工具。精简工具链和精简代码一样重要，少即是多。

本章涉及的关键技术点和官方文档链接：

- ESLint官方文档：https://eslint.org/docs/latest/
- Prettier官方文档：https://prettier.io/docs/en/
- Husky官方文档：https://typicode.github.io/husky/
- Conventional Commits规范：https://www.conventionalcommits.org/
- GitFlow原始文章：https://nvie.com/posts/a-successful-git-branching-model/
- react-native-config文档：https://github.com/luggit/react-native-config
- Metro配置文档：https://metrobundler.dev/docs/configuration/
- commitlint文档：https://commitlint.js.org/
- lint-staged文档：https://github.com/okonet/lint-staged

**收藏清单：RN工程化落地工具链速查**

| 工具 | 用途 | 配置文件 | 关键收益 |
|------|------|---------|---------|
| ESLint | 代码质量检查 | .eslintrc.js | 编码阶段拦截错误 |
| Prettier | 代码格式化 | .prettierrc | 统一代码风格 |
| Husky | Git Hook管理 | .husky/ | 提交前自动检查 |
| lint-staged | 暂存区检查 | package.json | 只检查变更文件 |
| commitlint | 提交信息校验 | commitlint.config.js | 规范化提交记录 |
| react-native-config | 环境变量管理 | .env.* | 多环境配置切换 |
| Metro | 打包工具配置 | metro.config.js | 路径别名与构建优化 |

**系列进度 14/16**

怕浪猫说：工程化不是写文档，不是配工具，不是走流程——工程化是让团队从"个人英雄主义"走向"集体协作主义"的系统工程。一个人可以靠技术能力写出好代码，但一个团队只能靠工程化体系持续产出好代码。这一章讲的所有规范、工具、流程，本质上都是在回答一个问题：怎么让十个人写出像一个人一样整齐的代码。答案不是要求每个人都变成同一个人，而是建立一套所有人都能遵守的规则和工具链。下一章我们要进入性能优化的深水区，从渲染性能到启动速度，从内存管理到包体积优化，让你的RN应用不仅代码写得好，跑起来也飞快。跟着怕浪猫，16章从零到一拿下RN全栈开发，我们下一章见。

下一章预告：第15章《RN性能优化：渲染调优与启动加速实战》将深入讲解RN性能优化的全套方案，包括组件渲染优化（memo、useMemo、useCallback的正确用法）、列表性能调优（FlatList虚拟化原理与优化技巧）、启动速度优化（Bundle拆分、懒加载、预热渲染）、内存泄漏排查与修复、包体积分析与瘦身策略，以及性能监控工具的使用。从"能跑"到"跑得快"，完成RN应用从功能完备到体验流畅的关键升级。