# StarPupil

Ai-based stock investment tools

# 项目语言：

- python 3.12.7
- html

# 项目结构

StarPupil/
  ├── backend/                      # 后端
  │   ├── app/
  │   │   ├── __init__.py
  │   │   ├── main.py               # FastAPI应用主入口
  │   │   ├── config.py             # 配置文件
  │   │   ├── database.py           # 数据库连接
  │   │   ├── models.py             # 数据库模型
  │   │   ├── schemas.py            # Pydantic模型
  │   │   ├── routers/              # 路由模块
  │   │   │   ├── __init__.py
  │   │   │   ├── auth.py           # 认证相关
  │   │   │   ├── stocks.py         # 数据相关
  │   │   │   ├── news.py           # 新闻相关
  │   │   │   ├── signals.py        # 信号相关
  │   │   │   └── strategy.py       # 策略设置相关
  │   │   ├── services/             # 业务逻辑层
  │   │   │   ├── __init__.py
  │   │   │   ├── data_fetcher.py       # 数据获取
  │   │   │   ├── analyzer.py           # 数据分析
  │   │   │   ├── strategy_engine.py    # 策略引擎
  │   │   │   └── ai_service.py         # AI服务封装
  │   │   ├── tasks/                # 定时任务
  │   │   │   ├── __init__.py
  │   │   │   └── scheduler.py      # 任务调度
  │   │   └── utils/                # 工具函数
  │   │       ├── __init__.py
  │   │       ├── indicators.py     # 技术指标计算
  │   │       └── notifier.py       # 通知功能
  │   ├── requirements.txt
  │   └── Dockerfile
  ├── frontend/
  │   ├── public/
  │   ├── src/
  │   │   ├── views/
  │   │   │   ├── Login.vue
  │   │   │   ├── Dashboard.vue
  │   │   │   ├── StockDetail.vue
  │   │   │   ├── StrategyConfig.vue
  │   │   │   └── SignalHistory.vue
  │   │   ├── components/
  │   │   │   ├── StockChart.vue
  │   │   │   └── NewsList.vue
  │   │   ├── router/
  │   │   ├── store/
  │   │   ├── App.vue
  │   │   └── main.js
  │   ├── package.json
  │   └── Dockerfile
  ├── docker-compose.yml
  ├── logs/                 # 日志记录
  │   |
  │   └── server.log        # 服务器日志
  └── README.md


# 开发任务进度表

标注：✅-已完成；♿-阶段性完成，待后续补充；
预计开发时长：1个月（2026-02-23前）

## 阶段一：后端基础框架和数据库

### 任务1.1：创建项目目录结构，初始化git，创建虚拟环境

- ✅[2026-01-27] 创建stock_ai_tool目录和子目录
- ✅[2026-01-27] 初始化git仓库
- ✅[2026-01-27] 创建Python虚拟环境，安装fastapi, sqlalchemy等基础包

### 任务1.2：编写配置文件（config.py）和环境变量示例

- ♿[2026-01-29] 创建配置类，从环境变量读取配置（如数据库URL，AI API密钥等）
- ♿[2026-01-29] 创建.env.example文件，列出需要的环境变量

### 任务1.3：设计数据库模型（models.py）和数据库连接（database.py）

- ♿[2026-01-29] 创建数据库连接和会话管理模块database.py
- ♿[2026-01-29] 使用SQLAlchemy定义stock、新闻、信号等模型modles.py

### 任务1.4：创建Pydantic模型（schemas.py）用于请求和响应

- ♿[2026-01-29] 定义API接口中使用的数据模型，如stock数据返回模型、信号模型等

### 任务1.5：编写FastAPI主应用（main.py）并测试运行

- ♿[2026-01-29] 在main.py中创建FastAPI应用实例
- ♿[2026-01-29] 配置中间件
- ♿[2026-01-29] 配置路由
- ♿[2026-01-29] 编写一个简单的测试接口

## 阶段二：数据获取服务

### 任务2.1：实现数据获取服务（data_fetcher.py），使用akshare获取stock数据

- ✅[2026-01-29] 安装akshare库
- 编写函数获取stock列表、日线数据等
  - ♿[2026-02-02] 获取stocks列表；
  - ♿[2026-02-03] 获取StockFinancialIndicator记录；
  - ♿[2026-02-04] 获取历史日线数据；
  - 获取实时行情；
- 处理获取的数据，转换为数据库模型
  - ♿[2026-02-02] stocks列表写入数据库；
  - ♿[2026-02-03] StockFinancialIndicator记录写入数据库；
  - ♿[2026-02-04] 历史日线数据写入数据库；
  - 实时行情数据写入 `stock_realtime_quotes` 表

### 任务2.2：实现新闻数据获取（可以在data_fetcher.py中，或单独一个模块）

- 编写函数获取stock相关新闻

### 任务2.3：编写数据存储逻辑，将获取的数据存入数据库（注意去重）

- 将数据获取和存储结合，确保数据不重复插入

## 阶段三：数据分析服务

### 任务3.1：实现技术指标计算（utils/indicators.py）

- 实现RSI、MACD、移动平均线等常用技术指标的计算

### 任务3.2：实现AI服务（ai_service.py），调用大模型API进行新闻情感分析

- 封装调用DeepSeek等AI API的函数，分析新闻情感

### 任务3.3：实现数据分析器（analyzer.py），整合技术指标和情感分析

- 编写分析器，对stock数据计算技术指标，对新闻进行情感分析

## 阶段四：策略引擎和信号生成

### 任务4.1：实现策略引擎（strategy_engine.py），至少实现一个简单策略（如RSI超买超卖）

- 定义策略基类，实现具体策略

### 任务4.2：实现信号生成，并将信号存入数据库

- 根据策略引擎的输出，生成信号并保存

## 阶段五：定时任务调度

### 任务5.1：实现定时任务调度器（tasks/scheduler.py），使用APScheduler

- 创建调度器，添加定时任务

### 任务5.2：配置定时任务，如每日收盘后运行分析，或每隔一段时间运行

- 定义任务函数，如每日任务、实时任务等

## 阶段六：后端API接口

### 任务6.1：实现stock数据相关接口（routers/stocks.py）

- 获取stock列表、获取stock历史数据等

### 任务6.2：实现新闻相关接口（routers/news.py）

- 获取stock新闻、新闻情感分析结果等

### 任务6.3：实现信号相关接口（routers/signals.py）

- 获取信号列表、获取某个stock的信号等

### 任务6.4：实现策略配置接口（routers/strategy.py）

- 获取当前策略配置、更新策略配置等

### 任务6.5：实现认证相关接口（routers/auth.py，可先留空）

- 可以暂时不做，但保留文件

## 阶段七：前端基础框架和页面

### 任务7.1：创建Vue3项目，配置路由（router）和状态管理（store）

- 使用Vite创建Vue3项目，安装vue-router和pinia

### 任务7.2：实现登录页面（Login.vue，可先做静态页面）

- 简单的登录表单，暂时不实现真实登录，可跳过认证

### 任务7.3：实现仪表盘页面（Dashboard.vue），展示概览信息

- 展示最近的信号、关注的stock等

### 任务7.4：实现stock详情页面（StockDetail.vue），展示图表和指标

- 使用echarts绘制K线图和技术指标

### 任务7.5：实现策略配置页面（StrategyConfig.vue）

- 表单，用于调整策略参数

### 任务7.6：实现信号历史页面（SignalHistory.vue）

- 表格展示历史信号

## 阶段八：前后端联调

### 任务8.1：配置前端代理，连接后端API

- 修改vite配置，将API请求代理到后端

### 任务8.2：调试各个页面，确保数据正确显示

- 逐个页面测试，调整API调用和数据展示

### 任务8.3：调整样式和交互

- 使用Element Plus等UI库，美化界面

## 阶段九：通知功能和其他工具

### 任务9.1：实现通知功能（utils/notifier.py），如邮件、钉钉等

- ✅[2026-01-28] 配置邮箱实现程序化发送通知
- 当生成信号时，发送通知

### 任务9.2：编写日志配置

- 配置日志格式和级别，记录运行日志

### 任务9.3：编写Dockerfile和docker-compose.yml，实现容器化部署

- 分别编写后端和前端的Dockerfile，以及docker-compose整合

### 任务9.4：编写README.md，包括项目介绍和运行说明

- 项目介绍、如何运行、配置说明等
