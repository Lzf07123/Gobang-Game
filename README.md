# 联机五子棋 (Online Gomoku)

**C 核心 + Python 后端 + Web 前端** 的双人联机五子棋。支持注册登录、JWT 鉴权、自动匹配、房间系统、观战、聊天、对局计时、棋谱回放、悔棋、再来一局、棋盘皮肤切换等功能。

---

## 快速启动

### Docker 部署（推荐）

```bash
# 1. 配置环境变量
cp .env.example .env
cp python-server/.env.example python-server/.env
# 编辑两个文件，确保 DB_PASSWORD 一致

# 2. 一键启动 (MySQL + 后端 + 前端)
docker compose -f docker-compose.yaml up --build

# 3. 浏览器访问 http://localhost:3000
```

### 手动启动（开发调试）

```bash
# 1. 编译 C 动态库
cd c-core && make clean && make all

# 2. 手动复制 libgobang.so 到 python-server/
cp libgobang.so ../python-server/

# 3. 安装 Python 依赖
cd ../python-server && pip install -r requirements.txt

# 4. 配置环境变量
cp .env.example .env     # 编辑 .env: DB_HOST=localhost, 填入本地 MySQL 信息

# 5. 启动后端 (HTTP + WebSocket, 默认 8080 端口)
python server.py

# 6. 新终端: 启动前端静态服务
cd ../public && python -m http.server 3000

# 7. 浏览器访问 http://localhost:3000
```

> **前端页面**: `public/index.html.example` 复制为 `index.html` 后使用，或直接由静态服务托管。

---

## 项目结构

```
gobang/
├── .env                        docker-compose 变量 (git 忽略)
├── .env.example                根目录环境变量模板
├── docker-compose.yaml         Docker 编排
├── CLAUDE.md                   Claude Code 配置
├── c-core/                     C 核心: 棋盘管理、五子连珠判定、禁手检测、局面评估
│   ├── board.c / board.h       棋盘状态、初始化、落子
│   ├── rules.c / rules.h       赢棋检测、禁手(三三/四四/长连)、获胜线提取
│   ├── evaluate.c / evaluate.h 局面评估函数（为 AI 预留）
│   ├── gobang.c / gobang.h     原始文件 + 总头文件
│   └── Makefile
├── python-server/              Python 后端: HTTP + WebSocket 服务
│   ├── .env                    应用配置 (git 忽略)
│   ├── .env.example            后端环境变量模板
│   ├── server.py               主服务 (aiohttp) — HTTP 认证 + WebSocket 对局
│   ├── auth.py                 注册/登录/JWT
│   ├── db.py                   MySQL 连接池 + 对局持久化
│   ├── game_engine.py          C 库 ctypes 封装（服务端真正使用 C 库判胜）
│   ├── test_db.py              数据库连通性测试
│   └── requirements.txt
├── docker/
│   ├── gobang-app/Dockerfile   前端容器
│   └── gobang-auth/Dockerfile  后端容器（多阶段: 编译 C + 运行 Python）
├── public/                     前端 (原生 HTML5)
│   ├── index.html.example      示例页面
│   ├── style.css               样式 + 主题 + 响应式
│   └── client.js               客户端逻辑
└── README.md
```

---

## 功能一览

| 功能 | 说明 |
|------|------|
| 用户注册/登录 | bcrypt 密码加密，JWT 令牌认证，用户名校验（中英文/数字/下划线 2-20 位） |
| 快速匹配 | FIFO 队列，自动分配对手，支持随时退出匹配 |
| 房间系统 | 创建/加入 4 位房间码，好友对战，一键复制房间码 |
| 房间浏览 | 实时查看等待中的房间列表，一键加入 |
| 观众模式 | 输入房间码观战，实时同步棋局 |
| 对局聊天 | 房内文本聊天，最大 100 条消息缓存 |
| 落子计时 | 每步 30 秒，超时判负 |
| 悔棋 | 每局每人 3 次，需对手同意，边界条件校验 |
| 再来一局 | 对局结束后 60 秒内双方可快速重开，自动交换黑白 |
| 终局高亮 | 五连子金色脉冲高亮，C 库提取获胜线坐标 |
| 棋盘皮肤 | 4 套主题：经典木纹 / 简约白 / 暗夜 / 竹林，偏好存 localStorage |
| 音效开关 | Web Audio 音效，一键静音，偏好持久化 |
| 棋谱回放 | 本地存储 + 服务端数据库双源，支持逐手回放 |
| 断线重连 | 指数退避策略，最多 8 次，状态提示 |
| 游戏持久化 | 进行中的游戏写入 MySQL `active_games` 表，崩溃后数据不丢 |
| 频率限制 | 基于 IP 滑动窗口限流（30次/分钟） |
| 服务端清理 | 定时清理过期连接、超时房间、断线用户 |

---

## 环境变量

### 根目录 `.env` — docker-compose 变量注入

| 变量          | 默认值   | 说明                   |
| ------------- | -------- | ---------------------- |
| `DB_PASSWORD` | —        | MySQL root 密码 (必填) |
| `DB_NAME`     | `gobang` | MySQL 数据库名         |
| `AUTHPORT`    | `8080`   | 后端容器端口映射       |
| `APPPORT`     | `3000`   | 前端容器端口映射       |

### `python-server/.env` — 后端应用配置

| 变量          | 手动开发值   | Docker 环境值 | 说明                 |
| ------------- | ------------ | ------------- | -------------------- |
| `DB_HOST`     | `localhost`  | `gobang-db`   | MySQL 地址           |
| `DB_PORT`     | `3306`       | `3306`        | MySQL 端口           |
| `DB_USER`     | `root`       | `root`        | 数据库用户名         |
| `DB_PASSWORD` | `your_pass`  | `your_pass`   | 数据库密码           |
| `DB_NAME`     | `gobang`     | `gobang`      | 数据库名             |
| `DB_POOL_SIZE`| `10`         | `10`          | MySQL 连接池大小     |
| `JWT_SECRET`  | _自动生成_   | 同上          | JWT 签名密钥 (HS256) |
| `PORT`        | `8080`       | `8080`        | 服务监听端口         |

> **JWT 密钥**: 如果 `.env` 中 `JWT_SECRET` 为空或为默认值，服务器启动时会自动生成 64 位随机密钥。生产环境务必手动配置固定值。

---

## 技术架构

| 层          | 技术                     | 职责 |
| ----------- | ------------------------ | ---- |
| C 核心      | ANSI C (`-shared -fPIC`) | 棋盘状态、落子校验、四方向五子连珠判定、禁手检测、局面评估 |
| Python 后端 | aiohttp + WebSocket      | HTTP 认证、WebSocket 对局通信、房间管理、聊天、计时、多局并发 |
| 前端        | 原生 HTML5 + CSS3 + JS   | Canvas 棋盘绘制、4 套皮肤、WebSocket 通信、动画音效、棋谱存储 |
| 数据库      | MySQL                    | 用户账号、对局记录、活跃游戏持久化 |

### 关键设计

- **C 库判胜**: 服务端通过 `game_engine.py` 调用 C 库 `check_winner()` + `get_win_line()` 判定胜负并提取五连子坐标，每个房间独立维护 Python 棋盘状态，调用前 `set_board_state()` 同步。
- **消息认证**: WebSocket 连接后发送 `{type:"auth", token}` 完成认证，避免 Token 泄露到 URL 日志。
- **频率限制**: 基于 IP 的滑动窗口限流（30次/60秒），保护注册登录接口。
- **断线重连**: 客户端指数退避重连（1s → 2s → 4s → ... → 10s max，最多 8 次），服务端断线后对手自动获胜。
- **游戏持久化**: 对局进行中将棋盘状态写入 `active_games` 表，服务器崩溃后可恢复。
- **并发控制**: 线程池按 CPU 核心数自动缩放，等待队列 O(1) 操作，最大连接数 500、最大房间数 1000。
- **定期清理**: 后台任务每 60 秒清理过期认证连接、超时房间、IP 限流记录。

---

## HTTP API

| 方法 | 路径 | 说明 |
|------|------|------|
| POST | `/register` | 用户注册 |
| POST | `/login` | 用户登录，返回 JWT |
| GET | `/health` | 健康检查 |
| GET | `/api/rooms` | 获取等待中的房间列表 |
| GET | `/api/games` | 获取用户对局历史 (`?username=`) |
| GET | `/api/games/{id}` | 获取对局棋谱详情 |
| GET | `/api/profile` | 获取用户统计 (`?username=`) |

## WebSocket 协议

### 客户端 → 服务端

| type            | 字段                       | 说明                    |
| --------------- | -------------------------- | ----------------------- |
| `auth`          | `token`                    | 认证（连接后第一条消息）|
| `match`         | —                          | 请求匹配对局            |
| `cancel_match`  | —                          | 取消匹配排队            |
| `create_room`   | —                          | 创建房间                |
| `join_room`     | `room_id`, `as_spectator`  | 加入房间 / 观众模式     |
| `leave_room`    | —                          | 离开当前房间            |
| `move`          | `x`, `y`                   | 落子 (0-14)             |
| `chat`          | `message`                  | 发送聊天消息（最长200） |
| `request_undo`  | —                          | 请求悔棋                |
| `undo_response` | `accept`                   | 同意/拒绝悔棋           |
| `resign`        | —                          | 认输                    |
| `rematch`       | —                          | 请求再来一局            |

### 服务端 → 客户端

| type               | 字段                                          | 说明                    |
| ------------------ | --------------------------------------------- | ----------------------- |
| `auth_ok`          | `username`                                    | 认证成功                |
| `waiting`          | `message`                                     | 等待对手中              |
| `match_cancelled`  | `message`                                     | 匹配已取消              |
| `start`            | `color`, `message`, `room_id`, `usernames`    | 对局开始                |
| `move`             | `x`, `y`, `color`                             | 落子通知                |
| `turn`             | `color`                                       | 轮到谁落子              |
| `timer`            | `remaining`                                   | 倒计时更新（秒）        |
| `game_over`        | `winner`, `reason`, `moves`, `win_line`       | 对局结束 + 五连高亮坐标 |
| `error`            | `error`                                       | 错误消息                |
| `room_created`     | `room_id`                                     | 房间创建成功            |
| `room_joined`      | `room_id`, `players`, `state`, `as_spectator` | 加入房间成功            |
| `player_joined`    | `username`                                    | 玩家加入房间            |
| `player_left`      | `username`                                    | 玩家离开房间            |
| `spectator_count`  | `count`, `username`                           | 观众人数变更            |
| `room_closed`      | `message`                                     | 房间关闭                |
| `chat`             | `username`, `message`                         | 聊天消息                |
| `request_undo`     | `from`                                        | 对手请求悔棋            |
| `undo_response`    | `accepted`, `message`                         | 悔棋请求结果            |
| `undo`             | `board`, `moves`                              | 棋盘状态回退            |
| `rematch_request`  | `from`                                        | 对手邀请再来一局        |
| `rematch_waiting`  | `message`                                     | 等待对方确认再来一局    |

---

## 常见问题

**同一台电脑测试联机？**
打开两个浏览器窗口（普通 + 无痕），分别注册账号，各自登录后一方创建房间、另一方输入房间码加入。

**MySQL 连接失败？**
- 手动运行: 检查 MySQL 服务是否启动，`DB_HOST` 是否为 `localhost`，密码是否正确
- Docker 运行: 确保 `python-server/.env` 中 `DB_HOST=gobang-db`

**C 动态库加载失败？**
```bash
cd c-core && make clean && make all
cp libgobang.so ../python-server/
```

**端口被占用？**
修改 `python-server/.env` 中的 `PORT` 值，同时更新 `public/index.html` 中 `<meta name="api-port">` 保持一致。

---

## 环境要求

- GCC 或 Clang（编译 C 动态库）
- Python 3.8+
- MySQL 8.0+
- 现代浏览器（支持 Canvas、WebSocket、Web Audio API）
- Docker & Docker Compose（可选）
