# 联机五子棋 (Online Gomoku)

**C 核心 + Python 后端 + Web 前端** 的双人联机五子棋。支持用户注册登录、JWT 鉴权、自动匹配对局、C 语言级别的棋盘逻辑和断线自动判负。

---

## 快速启动

### Docker 部署（推荐）

```bash
# 1. 配置环境变量
#    根目录 .env → docker-compose 用（DB_PASSWORD, DB_NAME, PORT, APPPORT）
cp .env.example .env
#    python_server/.env → 后端容器运行时使用, DB_HOST 需填服务名 gobang_db
cp python_server/.env.example python_server/.env
#    编辑两个文件, 确保 DB_PASSWORD 一致

# 2. 一键启动 (MySQL + 后端 + 前端)
docker compose up --build

# 3. 浏览器访问 http://localhost:3000
```

### 手动启动（开发调试）

```bash
# 1. 编译 C 动态库
cd c_core && make run    # 自动复制 libgobang.so 到 python_server/

# 2. 安装 Python 依赖
cd ../python_server && pip install -r requirements.txt

# 3. 配置环境变量
cp .env.example .env     # 编辑 .env: DB_HOST=localhost, 填入本地 MySQL 信息

# 4. 启动后端 (HTTP + WebSocket, 默认 8080 端口)
python server.py

# 5. 新终端: 启动前端静态服务
cd ../public && python -m http.server 3000

# 6. 浏览器访问 http://localhost:3000
```

---

## 项目结构

```
gobang/
├── .env                    docker-compose 变量 (git 忽略)
├── .env.example            根目录环境变量模板
├── docker-compose.yaml     Docker 编排 (app + auth + db 三容器)
├── c_core/                 C 核心: 15×15 棋盘、落子校验、五子连珠判定
│   ├── gobang.c
│   ├── gobang.h
│   └── Makefile
├── python_server/          Python 后端: HTTP + WebSocket 服务
│   ├── .env                应用配置 (git 忽略)
│   ├── .env.example        后端环境变量模板
│   ├── server.py           主服务 (aiohttp)
│   ├── auth.py             注册/登录/JWT
│   ├── db.py               MySQL 连接池
│   ├── game_engine.py      C 库 ctypes 封装 (单例)
│   ├── test_db.py          数据库连通性测试
│   └── requirements.txt
├── docker/
│   ├── gobangApp/
│   │   └── Dockerfile      前端容器 (Python http.server :3000)
│   └── gobangAuth/
│       └── Dockerfile      后端容器 (多阶段: 编译 C + 运行 Python)
├── public/                 前端 (无框架 HTML5)
│   ├── index.html
│   ├── style.css
│   └── client.js
└── README.md
```

---

## 环境变量

### 根目录 `.env` — docker-compose 变量注入

| 变量          | 默认值   | 说明                   |
| ------------- | -------- | ---------------------- |
| `DB_PASSWORD` | —        | MySQL root 密码 (必填) |
| `DB_NAME`     | `gobang` | MySQL 数据库名         |
| `AUTHPORT`    | `8080`   | 后端容器端口映射       |
| `APPPORT`     | `3000`   | 前端容器端口映射       |

根目录 `.env` 被 `docker-compose.yaml` 自动读取，用于 MySQL 容器初始化和端口映射。

### `python_server/.env` — 后端应用配置

| 变量          | 手动开发值                      | Docker 环境值   | 说明                 |
| ------------- | ------------------------------- | --------------- | -------------------- |
| `DB_HOST`     | `localhost`                     | `gobang_db`     | MySQL 地址           |
| `DB_PORT`     | `3306`                          | `3306`          | MySQL 端口           |
| `DB_USER`     | `root`                          | `root`          | 数据库用户名         |
| `DB_PASSWORD` | `your_password`                 | `your_password` | 数据库密码           |
| `DB_NAME`     | `gobang`                        | `gobang`        | 数据库名             |
| `JWT_SECRET`  | `your_jwt_secret_key_change_me` | 同上            | JWT 签名密钥 (HS256) |
| `PORT`        | `8080`                          | `8080`          | 服务监听端口         |

`server.py` 通过 `load_dotenv("python_server/.env")` 加载该文件。Docker 构建时会将该文件一起打包进镜像。

---

## 技术架构

| 层          | 技术                     | 职责                                                                 |
| ----------- | ------------------------ | -------------------------------------------------------------------- |
| C 核心      | ANSI C (`-shared -fPIC`) | 15×15 棋盘状态、落子校验、横/竖/斜四方向五子连珠判定                 |
| Python 后端 | aiohttp + WebSocket      | HTTP 注册/登录、WebSocket 对局通信、ctypes 桥接 C 库、MySQL 用户存储 |
| 前端        | 原生 HTML5 + CSS3 + JS   | Canvas 绘制棋盘、WebSocket 通信、用户交互                            |
| 数据库      | MySQL                    | 用户账号与密码哈希存储                                               |

### 关键设计

- **C 库单例**: 使用静态二维数组管理棋盘，无动态内存分配。Python 侧 `GameEngine` 为单例模式，确保全局只有一份棋盘状态。
- **线程池隔离 DB**: 数据库查询通过 `ThreadPoolExecutor` 委派到独立线程，不阻塞 aiohttp 事件循环。
- **断线即负**: WebSocket 断开时对手自动获胜，房间清理并重置棋盘。
- **FIFO 匹配**: 等待队列先进先出，匹配后随机分配黑白棋。
- **前端端口发现**: `<meta name="api-port" content="8080">` 元标签指定后端地址，前后端分离部署时只需修改该值。

---

## WebSocket 协议

### 客户端 → 服务端

| type    | 字段     | 说明                 |
| ------- | -------- | -------------------- |
| `match` | —        | 请求匹配对局         |
| `move`  | `x`, `y` | 落子 (行列坐标 0-14) |

### 服务端 → 客户端

| type        | 字段                            | 说明                |
| ----------- | ------------------------------- | ------------------- |
| `start`     | `color` (1=黑, 2=白), `message` | 对局开始            |
| `move`      | `x`, `y`, `color`               | 落子通知            |
| `turn`      | `color`                         | 轮到谁              |
| `game_over` | `winner`                        | 游戏结束 (胜方描述) |
| `waiting`   | `message`                       | 等待对手中          |
| `error`     | `error`                         | 错误消息            |

### 登录流程

```
浏览器                          Python 服务器                   MySQL
  │                                │                            │
  ├── POST /register ────────────→ │ bcrypt 加密                 │
  │←──── 成功/失败 ────────────────│── INSERT INTO users ──────→ │
  │                                │                            │
  ├── POST /login ───────────────→ │ 验证密码 + JWT (2h)        │
  │←── {token, username} ──────────│── SELECT FROM users ──────→│
  │                                │                            │
  ├── WS /ws?token=JWT ──────────→ │ 鉴权 → 匹配 / 对局         │
  │   {type:"match"}              │ FIFO 队列 → 创建房间         │
  │   {type:"move",x,y}           │ ctypes 调 C 库落子 + 判胜   │
  │←── {type:"move/turn/          │                            │
  │      game_over/error}          │                            │
```

---

## 常见问题

**同一台电脑测试联机？**
打开两个浏览器窗口（普通 + 无痕/隐私），分别注册账号，各自登录后点击"开始匹配"。

**MySQL 连接失败？**

- 手动运行: 检查 MySQL 服务是否启动，`DB_HOST` 是否为 `localhost`，密码是否正确
- Docker 运行: 确保 `python_server/.env` 中 `DB_HOST=gobang_db`（Docker 内部服务名），`DB_USER=root`

**C 动态库加载失败？**

```bash
cd c_core && make && cp libgobang.so ../python_server/
```

**端口被占用？**
修改 `python_server/.env` 中的 `PORT` 值，同时更新 `public/index.html` 中 `<meta name="api-port">` 保持一致。

---

## 环境要求

- GCC 或 Clang（编译 C 动态库）
- Python 3.8+
- MySQL 8.0+
- 现代浏览器
- Docker & Docker Compose（可选，容器化部署）
