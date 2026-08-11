---
sidebar_position: 10
---

# 第10章 RN全栈开发：Node后端与数据库对接实战

你写了漂亮的RN（React Native）页面，组件拆得干净利落，Hooks用得行云流水，路由导航也搭得有模有样——然后呢？数据从哪来？用户注册信息存哪？列表分页怎么搞？筛选搜索谁来做？如果你只会写前端，那你的全栈之路就卡在了"会调API"这一步。能写出完整前后端闭环的开发者，和只会切页面的前端工程师，薪资差距至少是两倍起步。全栈能力不是锦上添花的加分项，而是从"干活的人"变成"解决问题的人"的分水岭。

我是怕浪猫，一个从前端一路杀到全栈、踩过无数后端坑的开发者。前面九章我们一直在RN客户端里打转，从环境搭建到组件化、从路由到状态管理，前端的基本功练得差不多了。从这章开始，我们要跨越那道坎——把Node后端、MySQL数据库、ORM模型映射、CRUD接口全部串起来，用一个完整的全栈闭环项目，带你真正理解数据从数据库到页面的完整链路。这章信息量很大，但我会用最实战的方式讲，每一节都有代码、有图表、有踩坑经验，跟着敲一遍你就全明白了。

> 前端决定上限，后端决定下限。只会写前端的人永远在别人的地基上盖楼，而掌握全栈的人，自己就是地基。

## 10.1 全栈架构与前后端分离思想

### 10.1.1 客户端-服务端-数据层链路解析

全栈开发的核心不是"什么都会写"，而是"理解数据在三层架构之间怎么流动"。很多前端开发者转全栈时最大的障碍不是语法，而是思维方式——前端习惯了"数据是接口给的"，而全栈开发者要理解"数据是怎么从数据库一步步走到页面上的"。先把三层架构的职责边界搞清楚，后面写代码才不会乱。

```
┌──────────────────────────────────────────────┐
│              客户端 (RN App)                   │
│  ┌─────────┐  ┌──────────┐  ┌─────────────┐  │
│  │  页面UI  │→ │ 状态管理  │→ │ 请求封装层   │  │
│  │ 渲染展示 │  │ Redux/Zustand│ │ Axios/Fetch │  │
│  └─────────┘  └──────────┘  └──────┬──────┘  │
└─────────────────────────────────┬────────────┘
                                  │ HTTP/HTTPS
                                  ▼
┌──────────────────────────────────────────────┐
│            服务端 (Node.js + Express)          │
│  ┌─────────┐  ┌──────────┐  ┌─────────────┐  │
│  │ 路由层   │→ │ 业务逻辑层│→ │  数据访问层  │  │
│  │ Router  │  │ Service  │  │ DAO/Model   │  │
│  └─────────┘  └──────────┘  └──────┬──────┘  │
└─────────────────────────────────┬────────────┘
                                  │ SQL/TCP
                                  ▼
┌──────────────────────────────────────────────┐
│            数据层 (MySQL)                      │
│  ┌─────────┐  ┌──────────┐  ┌─────────────┐  │
│  │  用户表  │  │  业务表   │  │  关联表     │  │
│  │ users   │  │ articles │  │ comments    │  │
│  └─────────┘  └──────────┘  └─────────────┘  │
└──────────────────────────────────────────────┘
```

三层架构的职责分工很明确。客户端负责UI渲染和用户交互，服务端负责业务逻辑处理和数据调度，数据层负责持久化存储。每一层只和相邻层通信，不允许跨层调用——比如客户端不能直接操作数据库，服务端路由层不应该直接写SQL查询语句。这个规则看似简单，但怕浪猫见过太多项目里路由层直接拼SQL字符串的，业务一复杂就维护不动了。

这种分层的好处是什么？解耦。客户端不关心数据怎么存的，服务端不关心页面怎么渲染的，数据库不关心谁来查的数据。每一层可以独立开发、独立测试、独立部署。前端开发者可以先用Mock数据开发页面，后端开发者可以用Postman测试接口，数据库管理员可以独立优化表结构，三方并行推进互不阻塞。

### 10.1.2 RN全栈项目完整数据流走向

理解了三层架构，再看一条完整的数据流是怎么走的。以"用户打开文章列表页"为例，从用户手指点击Tab到页面渲染出数据，中间经过了这些环节：

```
用户点击Tab → RN页面挂载 → useEffect触发 → 
调用API函数 → Axios发HTTP请求 → 
Express路由接收 → Controller解析参数 → 
Service执行业务逻辑 → ORM模型构造查询 → 
MySQL执行SQL返回结果 → ORM映射为JS对象 → 
Controller封装返回格式 → HTTP Response回到客户端 → 
Axios接收响应 → 状态管理更新 → 页面重新渲染
```

这条链路涉及14个环节，任何一个环节出问题都会导致"页面白屏"或"数据加载失败"。很多新手遇到问题只会看前端报错，完全不知道后端有没有收到请求、数据库有没有返回数据。全栈开发者的优势就在这里——你能顺着链路一步步排查，而不是在前端盲目猜。比如用Chrome DevTools的Network面板确认请求有没有发出，用Postman直接调接口确认后端有没有返回数据，用MySQL Workbench直接查数据库确认数据存不存在。三段排查一遍，bug无处遁形。

> 调试全栈bug的核心能力不是看报错信息，而是能在链路中二分定位问题出在哪一层。前端、网络、后端、数据库，四段排查一遍，bug无处遁形。

### 10.1.3 前后端分离开发规范与协作

前后端分离不是简单地把前端和后端代码放在两个仓库里，而是要从接口定义、数据格式、错误码规范三个维度建立协作标准。规范定得好，前后端协作就像齿轮啮合一样顺畅；规范定不好，每天的沟通成本比写代码的时间还长。

**接口定义规范。** 接口文档是前后端协作的契约。推荐用Apifox或Swagger管理，每个接口必须包含：请求方法、URL路径、请求参数（Query/Body/Path）、响应格式、错误码说明。接口定义应该在写代码之前完成，而不是写完代码再补文档。怕浪猫在实践中总结出的流程是：产品出需求 → 后端出接口文档 → 前端确认接口字段 → 双方并行开发 → 联调验收。这个流程的关键是"接口先行"，让前端不用等后端写完就能用Mock数据开发。

**数据格式规范。** 后端统一返回以下结构：

```json
{
  "code": 200,
  "message": "操作成功",
  "data": {
    "list": [],
    "total": 0,
    "page": 1,
    "pageSize": 10
  }
}
```

`code`为业务状态码，200表示成功，其他值表示不同类型的业务错误。`message`是给用户看的提示信息。`data`是实际数据，列表类型必须包含分页信息。前端拿到响应后，先判断`code`是否200，不是则直接弹出`message`提示。这个规范看似简单，但怕浪猫见过太多项目每个接口返回格式都不一样，前端写一堆`if/else`来处理不同格式，代码丑陋且容易出bug。

**错误码规范。** 统一规划错误码区间，让前端可以根据错误码做不同处理：

| 错误码区间 | 含义 | 示例 |
|-----------|------|------|
| 200 | 成功 | 200 |
| 400-499 | 客户端错误 | 401未登录、403无权限、404不存在 |
| 500-599 | 服务端错误 | 500服务器内部错误 |
| 1000-1999 | 业务错误 | 1001参数校验失败、1002重复操作 |
| 2000-2999 | 第三方服务错误 | 2001短信发送失败、2002支付异常 |

这套错误码体系的好处是：HTTP状态码和业务错误码分离。HTTP状态码反映网络层面的状态，业务错误码反映业务层面的状态。比如用户未登录时，HTTP状态码返回401，业务错误码也返回401，前端拦截器统一处理跳转登录页。而"参数校验失败"HTTP状态码返回400，业务错误码返回1001，前端弹出具体错误提示。

### 10.1.4 全栈开发常见问题与规避方案

全栈开发踩坑最多的不是技术问题，而是架构问题。下面这几个坑，怕浪猫全都踩过，每个坑都付出了惨痛的代价：

**坑一：前后端数据结构不一致。** 前端要的字段名是`userName`，后端返回的是`username`，大小写不一致导致前端渲染undefined。这种问题在联调时才会暴露，而且排查起来很费时间——因为前端代码看起来没毛病，后端代码看起来也没毛病，问题出在两边的命名约定不统一。规避方案：后端统一用驼峰命名，和前端保持一致，或者用ORM模型的字段映射功能统一转换。

**坑二：接口版本管理混乱。** 第一版接口返回3个字段，产品需求变更后加了2个字段，老版本APP直接崩溃。因为老版本APP的渲染逻辑没有做防御性编程，拿到新字段后`parseInt(undefined)`导致NaN，后续计算全部出错。规避方案：接口路径加版本号`/api/v1/users`，新版本用`/api/v2/users`，老版本保持兼容。APP端要做好版本检测和强制更新机制。

**坑三：跨域问题。** 本地开发时前端跑在8081端口，后端跑在3000端口，浏览器直接报CORS（Cross-Origin Resource Sharing，跨域资源共享）错误。RN端虽然不存在浏览器同源策略限制，但Web调试时还是会遇到。规避方案：后端统一配置cors中间件，开发环境允许所有来源，生产环境严格限制白名单。

**坑四：数据库密码硬编码。** 数据库连接信息直接写在代码里，提交到Git仓库，结果被同事看到甚至泄露到公网。这不是小概率事件，怕浪猫在GitHub上搜索过，每天有大量包含数据库密码的提交。规避方案：用`.env`文件管理环境变量，`.gitignore`里排除`.env`，数据库密码只存在本地环境变量中。

> 全栈开发的坑，80%是规范问题，20%才是技术问题。先把规范定好，技术实现反而是最简单的部分。

### 10.1.5 企业全栈项目架构选型标准

技术选型要考虑团队能力、项目规模、维护成本三个维度。对于RN全栈项目，怕浪猫推荐的选型方案如下：

**后端框架：Express。** 虽然NestJS更现代化，但Express的学习成本最低，生态最成熟，社区资源最丰富。Express是Node.js最老牌的Web框架，npm上周下载量超过两千万，几乎所有Node.js开发者都会用。对于中小型项目，Express完全够用。如果你的项目有微服务需求或者团队对TypeScript依赖极强，再考虑NestJS。NestJS本身也是基于Express封装的，学习Express后迁移NestJS的成本很低。

**数据库：MySQL。** 关系型数据库的首选。PostgreSQL功能更强但运维成本更高，MongoDB适合非结构化数据但对事务支持较弱。MySQL在性能、稳定性、运维成本之间取得了最好的平衡。而且MySQL的社区资源和文档最丰富，遇到问题搜一下基本都能找到解决方案。

**ORM框架：Sequelize。** 虽然Prisma近年来很火，但Sequelize在Node.js生态中积累了最长时间的实践经验，对复杂查询和事务的支持更成熟。Sequelize支持钩子（Hooks）、作用域（Scopes）、事务（Transactions）等高级特性，在企业级项目中非常有用。而且Sequelize的模型定义方式和Mongoose很像，前端转全栈的开发者上手快。

| 选型维度 | Express | NestJS | Koa |
|---------|---------|--------|-----|
| 学习成本 | 低 | 高 | 中 |
| 生态丰富度 | 最高 | 中 | 中 |
| TypeScript支持 | 一般 | 原生 | 一般 |
| 适合团队 | 全栈入门到中级 | 大型后端团队 | 有经验的团队 |
| 社区活跃度 | 最高 | 高 | 中 |

选型的核心原则是：选择你团队最熟悉的技术栈，而不是最新的技术栈。新技术意味着踩坑没有前人经验可参考，而成熟技术意味着Stack Overflow上已经有无数人帮你踩过坑了。

## 10.2 Express后端服务快速搭建

### 10.2.1 Express框架初始化与环境配置

选型定了，开始搭后端。先创建项目并安装依赖：

```bash
mkdir rn-server && cd rn-server
npm init -y
npm install express cors dotenv morgan body-parser
npm install sequelize mysql2
npm install -D nodemon
```

各依赖的用途说明：`express`是Web框架，提供路由和中间件能力；`cors`处理跨域请求；`dotenv`读取环境变量文件；`morgan`记录HTTP请求日志，开发调试必备；`body-parser`解析请求体（虽然Express 4.16+内置了`express.json()`，但某些场景下body-parser仍然需要）；`sequelize`和`mysql2`是ORM和数据库驱动；`nodemon`是开发热重载工具，代码变更自动重启服务。

项目目录结构规划：

```
rn-server/
├── src/
│   ├── config/         # 配置文件
│   ├── routes/         # 路由定义
│   ├── controllers/    # 控制器
│   ├── services/       # 业务逻辑
│   ├── models/         # 数据模型
│   ├── middlewares/    # 中间件
│   ├── utils/          # 工具函数
│   └── app.js          # 入口文件
├── .env                # 环境变量
├── .gitignore
└── package.json
```

这个目录结构遵循了分层架构的设计思想，每一层有明确的职责。`routes`接收请求，`controllers`解析参数并调用`services`，`services`执行业务逻辑并调用`models`操作数据库。这种分层不是过度设计，而是当你的代码量超过2000行时，如果没有清晰的目录结构，找个函数都要全局搜索，效率极低。

在`package.json`中添加开发脚本：

```json
{
  "scripts": {
    "dev": "nodemon src/app.js",
    "start": "node src/app.js"
  }
}
```

入口文件`app.js`的基本骨架：

```javascript
const express = require('express');
const cors = require('cors');
const morgan = require('morgan');
require('dotenv').config();

const app = express();

// 中间件
app.use(cors());
app.use(express.json());
app.use(morgan('dev'));

// 路由挂载
app.use('/api/v1', require('./routes'));

// 全局错误处理
app.use((err, req, res, next) => {
  console.error(err.stack);
  res.status(500).json({
    code: 500,
    message: '服务器内部错误',
    data: null
  });
});

const PORT = process.env.PORT || 3000;
app.listen(PORT, () => {
  console.log(`Server running on port ${PORT}`);
});
```

`morgan('dev')`是开发环境的日志格式，会打印每个请求的方法、路径、状态码和响应时间，调试时非常方便。生产环境应该用`morgan('combined')`生成更详细的日志格式，配合日志收集系统使用。

`.env`文件配置数据库连接信息：

```bash
PORT=3000
DB_HOST=localhost
DB_PORT=3306
DB_USER=root
DB_PASSWORD=your_password
DB_NAME=rn_app
NODE_ENV=development
```

> 项目结构是后端架构的骨架。目录没规划好就写代码，后面越写越乱，重构成本远大于前期规划的时间投入。

### 10.2.2 后端路由模块化拆分与管理

业务一多，路由就会变成几百行的面条代码。怕浪猫见过一个项目把所有路由都写在`app.js`里，500多行代码全是`app.get`、`app.post`，找一个接口要滚动半天。模块化拆分是必须做的。Express的`Router`就是为此设计的。

先建一个统一的路由入口文件：

```javascript
// src/routes/index.js
const express = require('express');
const router = express.Router();

router.use('/users', require('./userRoutes'));
router.use('/articles', require('./articleRoutes'));
router.use('/comments', require('./commentRoutes'));

module.exports = router;
```

每个业务模块独立管理自己的路由：

```javascript
// src/routes/articleRoutes.js
const express = require('express');
const router = express.Router();
const articleController = require('../controllers/articleController');

router.get('/', articleController.list);
router.get('/:id', articleController.detail);
router.post('/', articleController.create);
router.put('/:id', articleController.update);
router.delete('/:id', articleController.remove);

module.exports = router;
```

这种拆分方式的好处是，新增业务模块只需要三步：创建`xxxRoutes.js`、在`index.js`中挂载、创建对应的controller。各模块之间互不影响，维护起来非常清晰。当某个模块需要修改时，只需要打开对应的路由文件，不用翻阅其他模块的代码。

RESTful（Representational State Transfer，表现层状态转移）风格的路由设计也值得注意。上面定义的路由遵循了RESTful规范：GET查询、POST新增、PUT更新、DELETE删除。这种风格的好处是路由路径统一、语义清晰，前端开发者看到HTTP方法就知道这个接口做什么操作。

### 10.2.3 全局跨域与请求头统一配置

跨域配置看起来简单，但生产环境踩坑的人不少。开发环境直接用`cors()`默认配置就行，但生产环境需要精确控制：

```javascript
// src/middlewares/corsConfig.js
const cors = require('cors');

const corsOptions = {
  origin: function (origin, callback) {
    const allowedOrigins = [
      'http://localhost:8081',
      'https://your-app.com'
    ];
    if (!origin || allowedOrigins.includes(origin)) {
      callback(null, true);
    } else {
      callback(new Error('Not allowed by CORS'));
    }
  },
  methods: ['GET', 'POST', 'PUT', 'DELETE'],
  allowedHeaders: ['Content-Type', 'Authorization'],
  credentials: true
};

module.exports = cors(corsOptions);
```

RN原生请求不存在跨域问题，因为RN用的是HTTP Client而不是浏览器的XMLHttpRequest或Fetch API，没有同源策略限制。但如果你需要在Web端调试或后续做H5版本，这个配置就有用了。`credentials: true`允许携带Cookie，如果你用的是Token认证方案，可以不开。

请求头统一配置还包括响应格式设置。在所有路由之前加一个中间件，统一设置`Content-Type`：

```javascript
app.use((req, res, next) => {
  res.setHeader('Content-Type', 'application/json; charset=utf-8');
  next();
});
```

这个配置确保所有响应都是JSON格式，避免某些路由忘记设置Content-Type导致前端解析失败。虽然`express.json()`中间件会自动设置请求体的解析格式，但响应头的Content-Type还是需要手动指定的。

### 10.2.4 后端统一返回结果封装规范

每个接口都手写`res.json({code, message, data})`太繁琐了，而且容易写错。比如有的开发者偶尔忘记写`code`字段，有的把`message`拼成`msg`，前端处理起来就很头疼。封装一个统一的响应工具类：

```javascript
// src/utils/response.js
class ResponseUtil {
  success(data = null, message = '操作成功') {
    return { code: 200, message, data };
  }

  fail(message = '操作失败', code = 400) {
    return { code, message, data: null };
  }

  paginate(list, total, page, pageSize) {
    return {
      code: 200,
      message: '操作成功',
      data: { list, total, page: Number(page), pageSize: Number(pageSize) }
    };
  }
}

module.exports = new ResponseUtil();
```

在controller中使用：

```javascript
// src/controllers/articleController.js
const response = require('../utils/response');
const articleService = require('../services/articleService');

exports.list = async (req, res, next) => {
  try {
    const { page = 1, pageSize = 10 } = req.query;
    const result = await articleService.getList({ page, pageSize });
    res.json(response.paginate(
      result.list, result.total, page, pageSize
    ));
  } catch (error) {
    next(error);
  }
};
```

这样所有接口的返回格式就统一了。前端拿到响应后，只需要判断`code === 200`就能确定请求是否成功，不需要每个接口都写不同的判断逻辑。而且当需要修改返回格式时（比如加一个`timestamp`字段），只需要改`ResponseUtil`一个地方，所有接口自动生效。

> 统一返回格式看似小事，但它决定了前端请求封装的简洁程度。格式不统一，前端的错误处理代码就会散落在各个页面里，维护噩梦。

### 10.2.5 全局异常捕获与错误处理

Express的错误处理有一个容易踩的坑：异步函数抛出的异常不会被默认的错误处理中间件捕获。在Express 4.x中，异步路由函数如果抛出异常，这个异常不会被Express捕获，会导致请求挂起直到超时。必须用`try/catch`包裹，或者用`express-async-errors`这个包。

安装`express-async-errors`：

```bash
npm install express-async-errors
```

在`app.js`入口文件顶部引入，注意必须在其他中间件之前引入：

```javascript
require('express-async-errors');
const express = require('express');
// ... 其他引入
```

然后定义全局错误处理中间件。这个中间件必须放在所有路由之后，Express要求错误处理中间件有四个参数（err, req, res, next）：

```javascript
// src/middlewares/errorHandler.js
module.exports = (err, req, res, next) => {
  console.error(`[ERROR] ${new Date().toISOString()}`);
  console.error(err.stack);

  // 参数校验错误
  if (err.name === 'ValidationError') {
    return res.status(400).json({
      code: 1001,
      message: err.message,
      data: null
    });
  }

  // 唯一约束冲突
  if (err.name === 'SequelizeUniqueConstraintError') {
    return res.status(409).json({
      code: 1002,
      message: '数据已存在，不能重复操作',
      data: null
    });
  }

  // 兜底处理
  return res.status(500).json({
    code: 500,
    message: '服务器内部错误',
    data: null
  });
};
```

这个错误处理中间件做了三件事：打印错误日志用于调试、识别特定类型的错误并返回对应的业务错误码、兜底处理所有未捕获的错误。Sequelize抛出的`UniqueConstraintError`表示违反了唯一约束，通常是因为重复插入数据（比如注册时用户名已存在），需要返回明确的业务提示而不是笼统的500错误。

在生产环境中，错误日志应该写入文件或发送到日志收集系统（如ELK），而不是只打印到控制台。因为控制台日志在服务重启后会丢失，而文件日志可以持久化保存，方便事后排查问题。

## 10.3 MySQL数据库与表结构设计

### 10.3.1 数据库安装与链接环境配置

MySQL安装这里不展开讲，Mac推荐用Homebrew安装（`brew install mysql`），Windows推荐用MySQL Installer。安装完成后，创建数据库和开发用户：

```sql
CREATE DATABASE rn_app CHARACTER SET utf8mb4 
  COLLATE utf8mb4_unicode_ci;

CREATE USER 'rn_dev'@'localhost' IDENTIFIED BY 'dev_password';
GRANT ALL PRIVILEGES ON rn_app.* TO 'rn_dev'@'localhost';
FLUSH PRIVILEGES;
```

注意字符集必须用`utf8mb4`而不是`utf8`。MySQL的`utf8`是阉割版，最多只支持3字节字符，存emoji时会报错。`utf8mb4`才是真正的UTF-8编码，支持4字节字符包括emoji和部分生僻汉字。`COLLATE utf8mb4_unicode_ci`指定排序规则为unicode不区分大小写，这意味着查询时`WHERE name = 'ABC'`能匹配到`abc`，如果不希望不区分大小写可以用`utf8mb4_bin`。

数据库连接配置用Sequelize来管理。先创建一个数据库连接实例：

```javascript
// src/config/database.js
const { Sequelize } = require('sequelize');

const sequelize = new Sequelize(
  process.env.DB_NAME,
  process.env.DB_USER,
  process.env.DB_PASSWORD,
  {
    host: process.env.DB_HOST,
    port: process.env.DB_PORT,
    dialect: 'mysql',
    pool: {
      max: 10,
      min: 2,
      acquire: 30000,
      idle: 10000
    },
    define: {
      timestamps: true,
      underscored: true,
      paranoid: true
    },
    logging: process.env.NODE_ENV === 'development' 
      ? console.log : false
  }
);

module.exports = sequelize;
```

连接池配置很重要。`max`是最大连接数，根据数据库服务器的配置来定，一般10-20就够了。`min`是最小空闲连接数，保持2个连接常驻避免频繁建立连接。`acquire`是获取连接的超时时间（30秒），超时后报错。`idle`是连接空闲多久后释放（10秒）。`logging`在开发环境下打印SQL语句方便调试，生产环境关掉避免日志膨胀。

`define`中的全局配置影响所有模型：`timestamps: true`让所有模型自动包含`created_at`、`updated_at`时间戳字段，`underscored: true`把驼峰字段名自动转换为蛇形命名，`paranoid: true`启用软删除——删除操作不会真的删数据，而是设置`deleted_at`字段。这三个配置在企业级项目中几乎是必选的。

### 10.3.2 数据表字段设计规范与原则

数据库表设计有一套经验法则，怕浪猫总结如下：

**主键用自增整数。** 不要用UUID做主键，因为InnoDB引擎的聚簇索引要求主键有序，UUID作为主键会导致频繁的页分裂，写入性能差。如果需要对外暴露ID，用业务字段加唯一索引。自增整数的另一个好处是占用空间小（BIGINT 8字节 vs UUID 36字节），索引效率更高。

**时间字段标配三件套。** `created_at`记录创建时间，`updated_at`记录更新时间，`deleted_at`用于软删除。Sequelize会自动维护这三个字段，不需要手动赋值。这三个字段在排查问题时非常有用——"这条数据是什么时候创建的？""什么时候被修改过？""被删了但想恢复"——都能通过时间字段定位。

**字段命名用蛇形（snake_case）。** 数据库字段用`user_name`，JS对象用`userName`，通过ORM的字段映射自动转换。不要在数据库里用驼峰命名，SQL语句里写驼峰字段名需要加反引号，容易出错。而且不同数据库对大小写的处理不一致，Linux上MySQL默认区分表名大小写，Windows上不区分，用蛇形命名可以避免跨平台问题。

**避免使用数据库关键字。** 不要用`order`、`group`、`type`、`status`等作为字段名，它们是SQL（Structured Query Language，结构化查询语言）保留字。可以用`order_status`、`user_type`代替。如果一定要用保留字，必须加反引号包裹，但这会让SQL语句很难阅读。

| 设计原则 | 正确示例 | 错误示例 | 原因 |
|---------|---------|---------|------|
| 主键命名 | id | user_id | 统一用id，关联时用表名_id |
| 时间字段 | created_at | createTime | 数据库用蛇形，ORM自动转换 |
| 布尔字段 | is_deleted | deleted | 用is_前缀明确语义 |
| 状态字段 | order_status | status | 避免SQL保留字 |
| 外键命名 | user_id | uid | 完整表名_id，见名知意 |

### 10.3.3 主键、索引、唯一约束设计

索引设计是数据库性能优化的核心。不是所有字段都该加索引，索引过多会影响写入性能。理解索引的本质——B+树数据结构——有助于你做出正确的索引设计决策。

**主键索引（聚簇索引）。** InnoDB引擎的表默认有主键聚簇索引，数据物理上按主键顺序存储。所以主键选自增整数，插入时顺序写入，性能最优。聚簇索引的叶子节点直接存储数据行，通过主键查询时只需要一次IO就能拿到完整数据。

**唯一索引。** 用于保证字段值不重复，比如用户名、邮箱、手机号。唯一索引既保证数据完整性，又加速查询。唯一索引在写入时会做唯一性检查，如果违反约束会抛出错误，需要在应用层捕获并处理。

**联合索引。** 多个字段组合成一个索引，遵循最左前缀原则。比如`(user_id, status)`联合索引，可以加速`WHERE user_id = 1`和`WHERE user_id = 1 AND status = 1`，但不能加速`WHERE status = 1`。联合索引的字段顺序很重要，应该把区分度高的字段放在前面。

```sql
-- 用户表示例
CREATE TABLE users (
  id BIGINT UNSIGNED AUTO_INCREMENT PRIMARY KEY,
  username VARCHAR(50) NOT NULL,
  email VARCHAR(100) NOT NULL,
  phone VARCHAR(20),
  password_hash VARCHAR(255) NOT NULL,
  nickname VARCHAR(50),
  avatar VARCHAR(255),
  gender TINYINT DEFAULT 0,
  created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
  updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP 
    ON UPDATE CURRENT_TIMESTAMP,
  deleted_at TIMESTAMP NULL,
  UNIQUE INDEX uk_username (username),
  UNIQUE INDEX uk_email (email),
  INDEX idx_phone (phone)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;
```

索引命名也有规范：唯一索引用`uk_`前缀（Unique Key），普通索引用`idx_`前缀。这样看到索引名就知道它的类型，方便DBA做索引优化分析。

> 索引不是越多越好。每加一个索引，写入时就要多维护一棵B+树。只在查询频繁的字段上加索引，写多读少的表要克制加索引的冲动。

### 10.3.4 用户、业务核心数据表设计

以一个内容管理场景为例，设计用户表、文章表、评论表三张核心表。先理清业务关系：一个用户可以发多篇文章，一篇文章可以有多个评论，一个评论属于一个用户和一篇文章。这是典型的"一对多"关系链。

用户表上面已经建好了，来看文章表：

```sql
CREATE TABLE articles (
  id BIGINT UNSIGNED AUTO_INCREMENT PRIMARY KEY,
  user_id BIGINT UNSIGNED NOT NULL,
  title VARCHAR(200) NOT NULL,
  content TEXT,
  cover_image VARCHAR(255),
  status TINYINT DEFAULT 0 COMMENT '0草稿 1发布 2下架',
  view_count INT UNSIGNED DEFAULT 0,
  like_count INT UNSIGNED DEFAULT 0,
  created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
  updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP 
    ON UPDATE CURRENT_TIMESTAMP,
  deleted_at TIMESTAMP NULL,
  INDEX idx_user_id (user_id),
  INDEX idx_status (status),
  INDEX idx_created_at (created_at)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;
```

几个设计细节说明：`status`字段用TINYINT而不是VARCHAR，数值类型比较速度更快且占用空间更小（1字节 vs 字符串存储）。`view_count`和`like_count`用INT UNSIGNED，无符号整数，避免负数。`content`用TEXT类型，最大支持65535字节，如果文章内容超长可以改用MEDIUMTEXT（16MB）或LONGTEXT（4GB）。

`COMMENT`注释非常重要。三个月后你回来看表结构，如果不写注释，你绝对想不起来`status`的1是发布还是下架。数据库字段的COMMENT是给开发者看的，不是给用户看的，写清楚每个枚举值的含义。

评论表设计：

```sql
CREATE TABLE comments (
  id BIGINT UNSIGNED AUTO_INCREMENT PRIMARY KEY,
  article_id BIGINT UNSIGNED NOT NULL,
  user_id BIGINT UNSIGNED NOT NULL,
  content VARCHAR(500) NOT NULL,
  parent_id BIGINT UNSIGNED DEFAULT NULL,
  created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
  updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP 
    ON UPDATE CURRENT_TIMESTAMP,
  deleted_at TIMESTAMP NULL,
  INDEX idx_article_id (article_id),
  INDEX idx_user_id (user_id),
  INDEX idx_parent_id (parent_id)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;
```

`parent_id`用于实现评论的嵌套回复结构。`parent_id`为NULL表示是一级评论，有值表示是对某条评论的回复。这种设计叫做"邻接表模型"，是树形结构在关系型数据库中最常见的存储方式。查询时可以通过自连接（Self Join）来获取评论的层级关系。

### 10.3.5 一对多表关联关系设计实战

上面三张表的关联关系是典型的"一对多"：用户对文章是一对多，文章对评论是一对多，用户对评论也是一对多。

关联关系在数据库层面的实现靠外键约束。但在实际生产项目中，怕浪猫建议不要在数据库层面加外键约束，而是在应用层通过ORM的关联关系来维护。原因是外键约束会影响写入性能（每次插入都要检查引用完整性），而且数据迁移和分库分表时外键会带来巨大麻烦。阿里巴巴Java开发手册中也明确禁止使用外键约束。

关联关系图：

```
┌──────────┐    1:N    ┌──────────┐    1:N    ┌──────────┐
│  users   │──────────→│ articles │──────────→│ comments │
│          │           │          │           │          │
│ id (PK)  │           │ id (PK)  │           │ id (PK)  │
│ username │           │ user_id  │←──┐       │ article_id│
│ email    │           │ title    │   │       │ user_id  │←──┐
└──────────┘           │ content  │   │       │ content  │   │
                       └──────────┘   │       │ parent_id│   │
                                      │       └──────────┘   │
                                      └──────────────────────┘
```

不加外键约束不代表不维护数据完整性，而是把校验逻辑放在应用层。ORM的关联关系配置就是做这件事的——查询时自动JOIN，插入时自动填充关联ID。应用层的校验更灵活，可以添加自定义的校验逻辑，比如"不允许删除有文章的用户"这种业务规则。

> 数据库设计的核心不是范式有多标准，而是在性能、可维护性、数据完整性之间找到平衡点。过度设计比设计不足更危险。

## 10.4 Sequelize ORM模型映射开发

### 10.4.1 ORM框架安装与数据库链接

ORM（Object Relational Mapping，对象关系映射）框架的核心价值是：让你用JS对象操作数据库，而不是写SQL字符串。写SQL字符串的问题是：没有类型检查、容易拼写错误、拼接参数容易引发SQL注入、不同数据库的SQL方言不兼容。ORM框架通过模型映射解决了这些问题。

Sequelize是Node.js生态中最成熟的ORM框架。安装已经在前面完成了，这里直接看怎么建立模型和数据库的映射。Sequelize的连接配置也已经写好了，现在验证连接是否成功：

```javascript
// 测试连接
async function testConnection() {
  try {
    await sequelize.authenticate();
    console.log('数据库连接成功');
  } catch (error) {
    console.error('数据库连接失败:', error.message);
    process.exit(1);
  }
}

testConnection();
```

`authenticate()`方法会执行一个简单的`SELECT 1+1`查询来测试连接是否正常。如果连接失败，进程直接退出，避免后续代码在连接不可用的情况下继续执行导致更多错误。

### 10.4.2 数据模型创建与字段映射配置

为前面设计的三张表创建对应的Sequelize模型。先定义用户模型：

```javascript
// src/models/user.js
const { DataTypes } = require('sequelize');
const sequelize = require('../config/database');

const User = sequelize.define('User', {
  id: { type: DataTypes.BIGINT.UNSIGNED, primaryKey: true, autoIncrement: true },
  username: { type: DataTypes.STRING(50), allowNull: false, unique: true },
  email: { type: DataTypes.STRING(100), allowNull: false, unique: true, validate: { isEmail: true } },
  phone: { type: DataTypes.STRING(20), allowNull: true },
  passwordHash: { type: DataTypes.STRING(255), allowNull: false, field: 'password_hash' },
  nickname: { type: DataTypes.STRING(50), allowNull: true },
  avatar: { type: DataTypes.STRING(255), allowNull: true },
  gender: { type: DataTypes.TINYINT, defaultValue: 0, comment: '0未知 1男 2女' }
}, { tableName: 'users', underscored: true, paranoid: true });

module.exports = User;
```

注意`field: 'password_hash'`这个配置——JS属性名是`passwordHash`（驼峰），数据库字段名是`password_hash`（蛇形），`field`指定了映射关系。配合全局的`underscored: true`，Sequelize会自动处理大部分字段名的转换，但显式写出`field`更清晰，特别是对于自定义命名字段。

`validate`配置项提供了字段级别的校验。`isEmail: true`会在写入前校验邮箱格式，不合法会抛出`ValidationError`。Sequelize内置了丰富的校验器，包括`isEmail`、`isNumeric`、`isDate`、`len`（长度范围）、`min`/`max`（数值范围）等。

文章模型：

```javascript
// src/models/article.js
const { DataTypes } = require('sequelize');
const sequelize = require('../config/database');

const Article = sequelize.define('Article', {
  id: { type: DataTypes.BIGINT.UNSIGNED, primaryKey: true, autoIncrement: true },
  userId: { type: DataTypes.BIGINT.UNSIGNED, allowNull: false, field: 'user_id' },
  title: { type: DataTypes.STRING(200), allowNull: false, validate: { len: [1, 200] } },
  content: { type: DataTypes.TEXT, allowNull: true },
  coverImage: { type: DataTypes.STRING(255), field: 'cover_image' },
  status: { type: DataTypes.TINYINT, defaultValue: 0, validate: { isIn: [[0, 1, 2]] } },
  viewCount: { type: DataTypes.INTEGER.UNSIGNED, defaultValue: 0, field: 'view_count' },
  likeCount: { type: DataTypes.INTEGER.UNSIGNED, defaultValue: 0, field: 'like_count' }
}, { tableName: 'articles', underscored: true, paranoid: true });

module.exports = Article;
```

`isIn: [[0, 1, 2]]`校验status字段只能是0、1或2，传入其他值会抛出校验错误。这个校验在写入和更新时都会触发，确保数据合法性。

### 10.4.3 模型同步与数据表自动生成

模型定义好后，需要和数据库表同步。Sequelize提供了`sync()`方法：

```javascript
// src/models/index.js
const sequelize = require('../config/database');
const User = require('./user');
const Article = require('./article');
const Comment = require('./comment');

// 建立关联关系
User.hasMany(Article, { foreignKey: 'user_id', as: 'articles' });
Article.belongsTo(User, { foreignKey: 'user_id', as: 'author' });

Article.hasMany(Comment, { foreignKey: 'article_id', as: 'comments' });
Comment.belongsTo(Article, { foreignKey: 'article_id', as: 'article' });

User.hasMany(Comment, { foreignKey: 'user_id', as: 'comments' });
Comment.belongsTo(User, { foreignKey: 'user_id', as: 'commenter' });

// 同步模型到数据库
if (process.env.NODE_ENV === 'development') {
  sequelize.sync({ alter: true })
    .then(() => console.log('模型同步完成'))
    .catch(err => console.error('模型同步失败:', err));
}

module.exports = { sequelize, User, Article, Comment };
```

`sync({ alter: true })`会对比模型和现有表结构的差异，自动执行ALTER TABLE。这在开发阶段很方便，但生产环境绝对不要用——`alter`操作可能锁表，导致线上服务不可用。生产环境应该用Sequelize的Migration迁移工具来管理表结构变更，每次变更生成一个迁移文件，可以在回滚时撤销变更。

`hasMany`和`belongsTo`是Sequelize定义关联关系的方法。`User.hasMany(Article)`表示一个用户有多篇文章，`Article.belongsTo(User)`表示一篇文章属于一个用户。这两个方法是成对出现的——定义了一对多关系时，"一"的那端用`hasMany`，"多"的那端用`belongsTo`。`as`别名很重要，查询时通过别名来指定要JOIN的关联数据，不同的别名可以指向同一个模型的不同关联关系。

```
模型关联关系配置：

User ──hasMany──→ Article ──hasMany──→ Comment
  ↑                  ↑                    │
  └─────hasMany──────┴───belongsTo────────┘

查询时：
User.findAll({ include: [{ model: Article, as: 'articles' }] })
→ 自动JOIN articles表，返回嵌套数据
```

> 模型同步是一把双刃剑。开发阶段用起来很爽，但生产环境一定要用Migration管理表结构。别问我怎么知道的，线上锁表半小时的教训足够刻骨铭心。

### 10.4.4 模型关联关系绑定与配置

关联关系上面已经定义了，这里深入讲一下查询时怎么利用关联关系。Sequelize的`include`选项是实现关联查询的核心，它对应SQL的JOIN操作。

**一对一查询（belongsTo）。** 查询文章详情时同时返回作者信息：

```javascript
const article = await Article.findByPk(id, {
  include: [{
    model: User,
    as: 'author',
    attributes: ['id', 'username', 'nickname', 'avatar']
  }]
});
// 返回结果中 article.author 就是用户对象
```

`attributes`指定只返回需要的字段，不返回密码等敏感信息。这不仅是安全问题，也是性能问题——返回不必要的大字段会增加网络传输和内存消耗。

**一对多查询（hasMany）。** 查询文章列表时同时返回每篇文章的评论数：

```javascript
const articles = await Article.findAll({
  include: [{
    model: Comment,
    as: 'comments',
    attributes: []
  }],
  attributes: {
    include: [
      [sequelize.fn('COUNT', sequelize.col('comments.id')), 'commentCount']
    ]
  },
  group: ['Article.id'],
  raw: true
});
```

`raw: true`返回纯JS对象而不是Sequelize模型实例，性能更好且使用更方便。当你不需要调用模型实例方法时，始终用`raw: true`。

**嵌套查询的性能陷阱。** 查询用户列表，每个用户包含其文章，每篇文章包含评论：

```javascript
// 危险：可能产生巨大的JOIN结果集
const users = await User.findAll({
  include: [{
    model: Article,
    as: 'articles',
    include: [{ model: Comment, as: 'comments' }]
  }]
});
```

嵌套查询很方便，但要小心N+1查询问题。N+1问题是指：查询N条主记录后，又对每条主记录发一次查询获取关联数据，总共N+1次查询。如果你先查用户列表（1次），再循环查每个用户的文章（N次），就是N+1次查询。用`include`可以一次性JOIN查出来，但要确保关联字段上有索引，否则JOIN性能很差。

### 10.4.5 ORM通用查询方法封装

在每个Service里都写Sequelize查询代码会重复很多。封装一个通用的查询基类，把常用的CRUD操作提取出来：

```javascript
// src/services/baseService.js
class BaseService {
  constructor(model) { this.model = model; }

  async findById(id, include = []) {
    return this.model.findByPk(id, { include, raw: true });
  }

  async findMany({ where = {}, include = [], order = [], page = 1, pageSize = 10 }) {
    const offset = (page - 1) * pageSize;
    const { rows, count } = await this.model.findAndCountAll({
      where, include, order, limit: Number(pageSize), offset, raw: true, distinct: true
    });
    return { list: rows, total: count };
  }

  async create(data) { return this.model.create(data); }
  async update(id, data) { const [n] = await this.model.update(data, { where: { id } }); return n > 0; }
  async delete(id) { return this.model.destroy({ where: { id } }); }
}
module.exports = BaseService;
```

`findAndCountAll`是Sequelize提供的分页查询方法，它执行两次SQL——一次COUNT计算总数，一次SELECT查询当前页数据。`distinct: true`在有include关联查询时很重要，避免因为JOIN产生重复行导致COUNT不准确。

各个业务Service继承基类，只需写自己的特殊逻辑：

```javascript
// src/services/articleService.js
const BaseService = require('./baseService');
const Article = require('../models/article');
const { Op } = require('sequelize');

class ArticleService extends BaseService {
  constructor() { super(Article); }

  async getPublishedList(params) {
    return this.findMany({
      where: { status: 1, ...(params.keyword ? {
        [Op.or]: [{ title: { [Op.like]: `%${params.keyword}%` } },
                  { content: { [Op.like]: `%${params.keyword}%` } }]
      } : {}) },
      include: [{ model: User, as: 'author', attributes: ['id', 'username', 'nickname'] }],
      order: [['created_at', 'DESC']], page: params.page, pageSize: params.pageSize
    });
  }
}
module.exports = new ArticleService();
```

通用封装的好处是：所有模型的基本CRUD操作写法统一，新人接手项目时只需要看一遍`BaseService`就能理解查询逻辑。特殊业务逻辑在子类中扩展，不污染基类。这就是面向对象编程中"继承"的经典应用场景。

> 代码重复是技术债的起点。当你发现自己在第三个文件里写几乎相同的查询代码时，就该停下来提取公共方法了。

## 10.5 前后端全套CRUD接口联调

### 10.5.1 后端分页查询接口开发

CRUD（Create Read Update Delete，创建读取更新删除）是后端接口的基本功。先从查询列表接口开始，这是最常用也是最复杂的接口——因为它要处理分页、筛选、排序、关联查询多种需求的组合。

```javascript
// src/controllers/articleController.js
const response = require('../utils/response');
const articleService = require('../services/articleService');
const { Op } = require('sequelize');

exports.list = async (req, res, next) => {
  try {
    const { page = 1, pageSize = 10, status, keyword } = req.query;
    const where = {};
    if (status !== undefined && status !== '') where.status = Number(status);
    if (keyword) {
      where[Op.or] = [{ title: { [Op.like]: `%${keyword}%` } },
                      { content: { [Op.like]: `%${keyword}%` } }];
    }
    const result = await articleService.findMany({
      where, include: [{ model: User, as: 'author', attributes: ['id', 'username', 'nickname'] }],
      order: [['created_at', 'DESC']], page, pageSize
    });
    res.json(response.paginate(result.list, result.total, page, pageSize));
  } catch (error) { next(error); }
};
```

分页查询有几个关键参数：`page`当前页码，`pageSize`每页条数，`where`查询条件，`order`排序规则，`include`关联查询。这些参数组合起来构成了一个灵活的查询接口。注意`req.query`中的参数都是字符串类型，`Number(status)`做了类型转换，否则字符串"0"和数字0在条件判断中行为不同。

前端调用时传参示例：

```
GET /api/v1/articles?page=1&pageSize=10&status=1&keyword=React
```

### 10.5.2 新增数据接口与参数校验

新增接口需要做参数校验，不能信任前端传来的任何数据。前端校验可以被绕过（直接用curl调接口），所以后端必须有独立的校验逻辑。推荐用`express-validator`做校验：

```bash
npm install express-validator
```

定义校验规则：

```javascript
// src/validators/articleValidator.js
const { body } = require('express-validator');

const createArticleRules = [
  body('title')
    .notEmpty().withMessage('标题不能为空')
    .isLength({ max: 200 }).withMessage('标题不超过200字'),
  body('content')
    .optional()
    .isLength({ max: 65535 }).withMessage('内容过长'),
  body('userId')
    .notEmpty().withMessage('用户ID不能为空')
    .isInt({ min: 1 }).withMessage('用户ID格式错误'),
  body('status')
    .optional()
    .isIn([0, 1, 2]).withMessage('状态值非法')
];

module.exports = { createArticleRules };
```

校验中间件：

```javascript
// src/middlewares/validate.js
const { validationResult } = require('express-validator');

module.exports = (req, res, next) => {
  const errors = validationResult(req);
  if (!errors.isEmpty()) {
    return res.status(400).json({
      code: 1001,
      message: errors.array()[0].msg,
      data: null
    });
  }
  next();
};
```

在路由中应用校验中间件：

```javascript
// src/routes/articleRoutes.js
const express = require('express');
const router = express.Router();
const articleController = require('../controllers/articleController');
const { createArticleRules } = require('../validators/articleValidator');
const { validate } = require('../middlewares/validate');

router.get('/', articleController.list);
router.post('/', createArticleRules, validate, articleController.create);
router.put('/:id', createArticleRules, validate, articleController.update);

module.exports = router;
```

Controller中的创建逻辑：

```javascript
exports.create = async (req, res, next) => {
  try {
    const { title, content, userId, coverImage, status } = req.body;
    const article = await articleService.create({
      title, content, userId, 
      coverImage, status: status || 0
    });
    res.json(response.success(article, '创建成功'));
  } catch (error) {
    next(error);
  }
};
```

> 参数校验是后端的底线。前端校验是为了用户体验，后端校验是为了数据安全。任何绕过前端直接调用API的请求，后端都必须能拦截非法参数。

### 10.5.3 编辑更新数据接口实现

编辑接口和新增接口类似，区别是要先查询记录是否存在，再执行更新。很多开发者会忘记检查记录是否存在，直接执行`update`，结果是返回"成功"但数据实际没变化，用户一头雾水：

```javascript
exports.update = async (req, res, next) => {
  try {
    const { id } = req.params;
    const { title, content, coverImage, status } = req.body;
    
    const article = await articleService.findById(id);
    if (!article) {
      return res.json(response.fail('文章不存在', 404));
    }

    const updated = await articleService.update(id, {
      title, content, coverImage, status
    });

    if (!updated) {
      return res.json(response.fail('更新失败，数据未变化', 500));
    }

    res.json(response.success(null, '更新成功'));
  } catch (error) {
    next(error);
  }
};
```

这里有一个设计决策：更新时是全量更新还是部分更新？上面的代码用的是部分更新——只更新传入的字段，未传入的字段保持不变。Sequelize的`update`方法默认就是部分更新，只有传入的字段才会被写入数据库。如果你想做全量更新（未传入的字段设为默认值），需要在`update`时显式传入所有字段。

### 10.5.4 单条与批量删除接口开发

删除接口要区分软删除和硬删除。Sequelize配置了`paranoid: true`后，`destroy`方法默认执行软删除——只设置`deleted_at`字段，不真正删数据。软删除的好处是数据可以恢复，误删了还能找回来。坏处是数据量会持续增长，需要定期清理。

单条删除：

```javascript
exports.remove = async (req, res, next) => {
  try {
    const { id } = req.params;
    const deleted = await articleService.delete(id);
    if (!deleted) {
      return res.json(response.fail('文章不存在', 404));
    }
    res.json(response.success(null, '删除成功'));
  } catch (error) {
    next(error);
  }
};
```

批量删除接口接收一个ID数组：

```javascript
exports.batchRemove = async (req, res, next) => {
  try {
    const { ids } = req.body;
    if (!Array.isArray(ids) || ids.length === 0) {
      return res.json(response.fail('请选择要删除的数据', 400));
    }
    if (ids.length > 100) {
      return res.json(response.fail('单次最多删除100条', 400));
    }

    const deletedCount = await Article.destroy({
      where: { id: { [Op.in]: ids } }
    });

    res.json(response.success(
      { deletedCount }, 
      `成功删除${deletedCount}条数据`
    ));
  } catch (error) {
    next(error);
  }
};
```

批量删除用`Op.in`操作符，一条SQL语句删除多条记录。限制单次批量删除的最大数量为100条，防止恶意请求一次性删除大量数据导致数据库压力过大。这是一个安全防护措施，很多开发者会忽略这个细节。

如果需要恢复软删除的数据，Sequelize提供了`restore`方法：

```javascript
await Article.restore({ where: { id } });
```

如果需要真正删除数据（硬删除），传入`force: true`：

```javascript
await Article.destroy({ where: { id }, force: true });
```

### 10.5.5 前端请求对接与页面渲染

后端接口全部就绪后，回到RN前端对接。先封装一个请求工具类。这个工具类是前端所有API调用的基础，它的设计质量直接影响整个前端的数据处理逻辑：

```javascript
// src/utils/request.js
import axios from 'axios';
import { Alert } from 'react-native';

const instance = axios.create({
  baseURL: 'http://localhost:3000/api/v1',
  timeout: 10000,
  headers: { 'Content-Type': 'application/json' }
});

// 请求拦截器：自动添加Token
instance.interceptors.request.use(config => {
  const token = global.token;
  if (token) config.headers.Authorization = `Bearer ${token}`;
  return config;
}, error => Promise.reject(error));

// 响应拦截器：统一处理错误
instance.interceptors.response.use(response => {
  const { code, message, data } = response.data;
  if (code === 200) return data;
  if (code === 401) global.token = null;  // Token过期
  Alert.alert('提示', message);
  return Promise.reject(new Error(message));
}, error => {
  const msg = error.response?.data?.message || error.message;
  Alert.alert('网络错误', msg);
  return Promise.reject(error);
});
export default instance;
```

请求拦截器在每次请求前自动添加Token，响应拦截器统一处理业务错误码。这样在页面中调用API时就不用每次都写错误处理逻辑了。`timeout: 10000`设置10秒超时，移动网络环境下可能需要调大这个值。

封装具体的API调用函数：

```javascript
// src/api/article.js
import request from '../utils/request';

export const getArticleList = (params) => {
  return request.get('/articles', { params });
};

export const createArticle = (data) => {
  return request.post('/articles', data);
};

export const updateArticle = (id, data) => {
  return request.put(`/articles/${id}`, data);
};

export const deleteArticle = (id) => {
  return request.delete(`/articles/${id}`);
};

export const batchDeleteArticles = (ids) => {
  return request.delete('/articles/batch', { data: { ids } });
};
```

在页面中使用：

```javascript
// src/pages/ArticleListPage.js（核心逻辑）
const [list, setList] = useState([]);
const [loading, setLoading] = useState(false);
const [page, setPage] = useState(1);
const [hasMore, setHasMore] = useState(true);

const loadData = useCallback(async (pageNum = 1) => {
  if (loading) return;
  setLoading(true);
  try {
    const result = await getArticleList({ page: pageNum, pageSize: 10 });
    setList(prev => pageNum === 1 ? result.list : [...prev, ...result.list]);
    setHasMore(result.list.length === 10);
    setPage(pageNum);
  } finally { setLoading(false); }
}, [loading]);

useEffect(() => { loadData(); }, []);
```

```javascript
// src/pages/ArticleListPage.js（渲染部分）
const renderItem = ({ item }) => (
  <View style={{ padding: 16, borderBottomWidth: 0.5 }}>
    <Text style={{ fontSize: 16, fontWeight: 'bold' }}>{item.title}</Text>
    <Text style={{ color: '#999', marginTop: 4 }}>
      {item.author?.nickname} - {item.viewCount}浏览
    </Text>
  </View>
);

return (
  <FlatList data={list} renderItem={renderItem} keyExtractor={item => String(item.id)}
    refreshControl={<RefreshControl refreshing={loading && page === 1} onRefresh={() => loadData(1)} />}
    onEndReached={() => hasMore && loadData(page + 1)} onEndReachedThreshold={0.3}
  />
);

`FlatList`的下拉刷新和上拉加载更多逻辑是RN列表页面的标配。`onEndReachedThreshold`设为0.3表示列表滚动到距离底部30%时触发加载下一页，这样用户在看完最后一条之前就开始加载了，体验更流畅。`keyExtractor`用`String(item.id)`而不是直接用`item.id`，因为FlatList要求key是字符串类型。

> 前后端联调最容易被忽略的细节是加载状态管理。用户体验的差距往往不在功能是否实现，而在于loading动画是否及时显示、错误提示是否友好、空状态是否有引导。

## 10.6 分页、筛选、排序全栈实战

### 10.6.1 后端通用分页工具类封装

分页是后端接口的高频需求。虽然`BaseService`中已经封装了基本的分页查询，但面对复杂场景还需要增强。下面是一个更完善的分页工具类，它处理了参数校验、排序白名单、边界值保护等细节：

```javascript
// src/utils/pagination.js
const ALLOWED_SORT_FIELDS = ['created_at', 'updated_at', 'view_count', 'like_count'];

class PaginationUtil {
  parseParams(query) {
    const page = Math.max(1, parseInt(query.page) || 1);
    const pageSize = Math.min(100, Math.max(1, parseInt(query.pageSize) || 10));
    const sortField = ALLOWED_SORT_FIELDS.includes(query.sortField) ? query.sortField : 'created_at';
    const sortOrder = query.sortOrder === 'asc' ? 'ASC' : 'DESC';
    return { page, pageSize, offset: (page - 1) * pageSize, limit: pageSize, order: [[sortField, sortOrder]] };
  }

  buildResponse(rows, count, page, pageSize) {
    const totalPages = Math.ceil(count / pageSize);
    return { list: rows, total: count, page, pageSize, totalPages, hasNext: page < totalPages };
  }
}
module.exports = new PaginationUtil();
```

`pageSize`做了上限100的限制，防止前端传`pageSize=10000`一次性查太多数据导致内存溢出。`sortField`做了白名单校验，只允许预定义的排序字段，防止SQL注入。`sortOrder`只允许`asc`和`desc`两个值，其他值默认降序。

在Controller中使用：

```javascript
const pagination = require('../utils/pagination');

exports.list = async (req, res, next) => {
  try {
    const params = pagination.parseParams(req.query);
    const where = articleService.buildWhere(req.query);
    const result = await articleService.findMany({ where, ...params });
    res.json(response.success(
      pagination.buildResponse(
        result.list, result.total, params.page, params.pageSize
      )
    ));
  } catch (error) {
    next(error);
  }
};
```

### 10.6.2 前端分页参数传递与处理

前端分页有两种模式：页码分页和游标分页。页码分页就是传统的`page + pageSize`模式，可以跳转到任意页。游标分页用最后一条记录的ID作为下次查询的起点，只能往下翻不能跳页。

页码分页适合管理后台，用户可以直接跳转到第N页。游标分页适合信息流场景，无限滚动加载，不存在数据重复或遗漏的问题。而且游标分页的性能优于页码分页——`OFFSET 10000`会让数据库扫描前10000条记录再丢弃，非常浪费；游标分页用`WHERE id < lastId`直接定位，不管翻到第几页性能都一样。

RN信息流页面用游标分页的示例：

```javascript
const [cursor, setCursor] = useState(null);
const [list, setList] = useState([]);

const loadData = async (isRefresh = false) => {
  const params = { pageSize: 10 };
  if (cursor && !isRefresh) {
    params.lastId = cursor;
  }
  const result = await getArticleList(params);
  setList(prev => 
    isRefresh ? result.list : [...prev, ...result.list]
  );
  if (result.list.length > 0) {
    setCursor(result.list[result.list.length - 1].id);
  }
  setHasMore(result.list.length === 10);
};
```

后端游标分页的实现：

```javascript
const where = { status: 1 };
if (lastId) {
  where.id = { [Op.lt]: Number(lastId) };
}
const result = await Article.findAndCountAll({
  where,
  order: [['id', 'DESC']],
  limit: Number(pageSize)
});
```

游标分页的局限性在于：不能跳转到指定页码，不能向前翻页。如果你的产品需要"跳转到第5页"这种功能，就只能用页码分页。有些APP的做法是首页用游标分页（信息流），搜索结果页用页码分页（可跳页），根据场景选择合适的方案。

> 分页方式的选择不是技术问题，而是业务问题。管理后台需要"跳转到第X页"，用页码分页；信息流需要"无限往下刷"，用游标分页。选错了方案，后面性能优化再怎么做都是白费。

### 10.6.3 关键词模糊搜索筛选实现

模糊搜索是列表筛选的核心功能。Sequelize的`Op.like`对应SQL的`LIKE`操作：

```javascript
const { Op } = require('sequelize');

if (keyword) {
  where[Op.or] = [
    { title: { [Op.like]: `%${keyword}%` } },
    { content: { [Op.like]: `%${keyword}%` } }
  ];
}
```

`Op.or`表示OR条件，标题或内容匹配关键词都能查到。`%keyword%`表示关键词可以在任意位置出现——前缀`%`表示前面有任意字符，后缀`%`表示后面有任意字符。

但`LIKE '%keyword%'`有个性能问题：它无法走索引，会触发全表扫描。原因是B+树索引是按字段值排序的，`%keyword`这种前缀模糊匹配无法利用索引的有序性。当数据量超过10万行时，模糊搜索的查询时间可能从毫秒级飙升到秒级。

解决方案有两个：

**方案一：前缀匹配。** 用`LIKE 'keyword%'`，这样可以走索引。但只能匹配以关键词开头的数据，用户体验差。适合搜索用户名、标签等有明确前缀的场景。

**方案二：全文索引。** MySQL的`FULLTEXT`索引支持中文分词（需要ngram插件），查询性能远优于`LIKE`：

```sql
-- 添加全文索引
ALTER TABLE articles ADD FULLTEXT INDEX ft_title_content 
  (title, content) WITH PARSER ngram;
```

Sequelize中使用全文搜索：

```javascript
where = sequelize.literal(
  `MATCH(title, content) AGAINST('${keyword}' IN NATURAL MODE)`
);
```

全文索引的原理是对文本进行分词，建立倒排索引。查询时不是扫描每行数据，而是直接在索引中查找包含关键词的记录，效率远高于`LIKE`。但全文索引的缺点是占用更多存储空间，且对中文分词的准确度取决于ngram的分词粒度。

### 10.6.4 状态、时间条件筛选开发

状态筛选是精确匹配，直接用等值查询：

```javascript
if (status !== undefined && status !== '') {
  where.status = Number(status);
}
```

注意`status !== ''`这个判断——前端传空字符串表示"不筛选"，后端需要跳过这个条件。如果直接`where.status = ''`，Sequelize会生成`WHERE status = ''`，因为status是TINYINT类型，空字符串会被MySQL隐式转换为0，导致查询到所有status为0的记录，这是不对的。

时间范围筛选用`Op.between`或`Op.gte`/`Op.lte`：

```javascript
if (startDate && endDate) {
  where.created_at = {
    [Op.between]: [new Date(startDate), new Date(endDate)]
  };
} else if (startDate) {
  where.created_at = { [Op.gte]: new Date(startDate) };
} else if (endDate) {
  where.created_at = { [Op.lte]: new Date(endDate) };
}
```

时间筛选有一个常见的坑：前端传的日期是"2024-01-01"这种不带时间的格式，MySQL会把"2024-01-01"解释为"2024-01-01 00:00:00"。所以如果用户想筛选1月1日的数据，`endDate`应该设为"2024-01-02"才能包含1月1日全天。这个细节需要在和前端约定接口文档时就确认好。

把所有筛选条件组合起来，Controller会变得比较长。怕浪猫建议把筛选条件构建逻辑提取到Service层，保持Controller精简：

```javascript
// src/services/articleService.js
class ArticleService extends BaseService {
  buildWhereClause(query) {
    const where = {};
    const { status, keyword, startDate, endDate, userId } = query;

    if (status !== undefined && status !== '') {
      where.status = Number(status);
    }
    if (userId) {
      where.userId = Number(userId);
    }
    if (keyword) {
      where[Op.or] = [
        { title: { [Op.like]: `%${keyword}%` } },
        { content: { [Op.like]: `%${keyword}%` } }
      ];
    }
    if (startDate || endDate) {
      where.createdAt = {};
      if (startDate) where.createdAt[Op.gte] = new Date(startDate);
      if (endDate) where.createdAt[Op.lte] = new Date(endDate);
    }

    return where;
  }
}
```

### 10.6.5 前后端联动数据排序方案

排序功能看似简单，但联动起来有几个坑。先看后端怎么支持动态排序。分页工具中已经支持了`sortField`和`sortOrder`，但需要做白名单校验，防止恶意参数：

```javascript
const ALLOWED_SORT_FIELDS = [
  'created_at', 'updated_at', 'view_count', 'like_count'
];

parseParams(query) {
  const sortField = ALLOWED_SORT_FIELDS.includes(query.sortField)
    ? query.sortField : 'created_at';
  const sortOrder = query.sortOrder === 'asc' ? 'ASC' : 'DESC';
  return { 
    page: Math.max(1, parseInt(query.page) || 1),
    pageSize: Math.min(100, Math.max(1, parseInt(query.pageSize) || 10)),
    order: [[sortField, sortOrder]]
  };
}
```

白名单校验是必须的。如果不校验，攻击者可以传`sortField=1; DROP TABLE users--`这种恶意参数。虽然Sequelize的`order`参数使用参数化查询不容易被注入，但养成白名单校验的习惯很重要，因为你不能保证所有ORM在所有场景下都能防住SQL注入。

前端排序UI的实现，用一组排序选项让用户切换：

```javascript
const SORT_OPTIONS = [
  { label: '最新发布', value: 'created_at:DESC' },
  { label: '最早发布', value: 'created_at:ASC' },
  { label: '最多浏览', value: 'view_count:DESC' },
  { label: '最多点赞', value: 'like_count:DESC' }
];

const [sortValue, setSortValue] = useState('created_at:DESC');

const handleSortChange = (value) => {
  setSortValue(value);
  const [sortField, sortOrder] = value.split(':');
  setFilters(prev => ({ ...prev, sortField, sortOrder, page: 1 }));
};
```

当用户切换排序方式时，前端重置页码为1，带上新的排序参数重新请求。这样列表展示的就是按新排序规则的第一页数据。如果不重置页码，可能出现"第3页按最新排序"这种无意义的请求。

综合筛选、排序、分页的前端状态管理：

```javascript
const [filters, setFilters] = useState({
  keyword: '', status: '', startDate: '', endDate: '',
  sortField: 'created_at', sortOrder: 'DESC', page: 1, pageSize: 10
});

const loadData = async () => {
  setLoading(true);
  try {
    const result = await getArticleList(filters);
    setList(result.list);
    setTotal(result.total);
  } finally { setLoading(false); }
};

// 筛选条件变化时重新加载
useEffect(() => { loadData(); },
  [filters.keyword, filters.status, filters.startDate, filters.endDate,
   filters.sortField, filters.sortOrder]);
```

这里有一个细节：`useEffect`的依赖数组没有包含`filters.page`和`filters.pageSize`。因为翻页时不需要重新触发`useEffect`，而是在`loadData`函数内部手动调用。如果把`page`放进依赖数组，每次翻页都会重新渲染整个组件，影响性能。更好的做法是用`useCallback`包裹`loadData`，并在翻页时手动调用。

> 筛选、排序、分页是列表页的三驾马车。它们组合起来的复杂度是指数级的——筛选条件的排列组合、排序方向的切换、分页状态的重置，每一个边界情况都需要仔细测试。宁可多写测试用例，也不要靠"应该没问题"来安慰自己。

到这里，一个完整的全栈CRUD闭环就打通了。从RN前端发起请求，到Express后端接收处理，到Sequelize ORM操作MySQL数据库，再原路返回数据渲染到页面——这条链路上的每一环你都走了一遍。回顾一下全栈数据流的完整链路：

```
RN页面 → useEffect → API函数 → Axios请求 → 
Express路由 → Controller → Service → Sequelize模型 → 
MySQL查询 → ORM映射 → Controller封装 → HTTP响应 → 
Axios拦截器 → setState → 页面渲染
```

这章的内容量很大，从后端搭建到数据库设计到前后端联调，涉及的知识点非常多。建议跟着代码自己敲一遍，不要只看不写。全栈开发的关键不是理解概念，而是把概念变成手指的肌肉记忆。当你能不查文档就写出一个完整的CRUD接口时，你就真正具备了全栈开发能力。

**收藏清单：全栈开发核心知识点速查**

| 知识点 | 关键内容 | 文件位置 |
|--------|---------|---------|
| Express初始化 | 入口文件 + 中间件 + 路由挂载 | src/app.js |
| 路由模块化 | Router拆分 + RESTful风格 | src/routes/ |
| 统一响应 | success/fail/paginate三件套 | src/utils/response.js |
| 错误处理 | 异步异常捕获 + 分类处理 | src/middlewares/errorHandler.js |
| 数据库配置 | 连接池 + 全局模型选项 | src/config/database.js |
| 模型定义 | 字段映射 + 校验器 + 软删除 | src/models/ |
| 关联关系 | hasMany/belongsTo + as别名 | src/models/index.js |
| 通用Service | CRUD基类 + 业务子类 | src/services/ |
| 分页工具 | 参数校验 + 排序白名单 | src/utils/pagination.js |
| 前端请求 | 拦截器 + 统一错误处理 | src/utils/request.js |

本章涉及的关键技术点和官方文档链接：

- Express官方文档：https://expressjs.com/
- Sequelize官方文档：https://sequelize.org/docs/v6/
- MySQL官方文档：https://dev.mysql.com/doc/
- express-validator文档：https://express-validator.github.io/
- axios官方文档：https://axios-http.com/docs/intro

**系列进度 10/16**

怕浪猫说：全栈开发的门槛不在技术广度，而在链路深度。能独立打通前端、后端、数据库三层的人，才是真正意义上的全栈工程师。这章帮你把链路串起来了，下一章我们要给这条链路加上认证和权限的护栏，让你的项目具备企业级的安全能力。跟着怕浪猫，16章从零到一拿下RN全栈开发，我们下一章见。

下一章预告：第11章《RN全栈开发：JWT认证与权限控制实战》将深入讲解用户注册登录流程、JWT（JSON Web Token，JSON网络令牌）令牌签发与验证、密码加密存储、路由权限拦截、动态权限菜单实现，以及Token刷新机制和单点登录方案。从"能跑通数据"到"能管住权限"，完成全栈项目安全架构的关键一跃。