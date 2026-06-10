<div align="center">

# 🔗 区块链产品溯源系统
### Blockchain Product Traceability System

<p align="center">
  <img src="https://img.shields.io/badge/Python-3.9+-blue.svg" alt="Python">
  <img src="https://img.shields.io/badge/Flask-2.3+-green.svg" alt="Flask">
  <img src="https://img.shields.io/badge/Blockchain-PoW-orange.svg" alt="Blockchain">
  <img src="https://img.shields.io/badge/License-MIT-yellow.svg" alt="License">
  <img src="https://img.shields.io/badge/Status-Active-success.svg" alt="Status">
</p>

<p align="center">
  基于区块链技术的企业级产品溯源管理系统<br>
  支持多角色协作、智能合约、防伪验证的完整供应链解决方案
</p>

[功能特性](#-核心功能) • [快速开始](#-快速开始) • [技术架构](#-技术架构) • [项目展示](#-项目展示) • [文档](#-文档)

</div>

---

## 📋 目录

- [项目简介](#-项目简介)
- [核心功能](#-核心功能)
- [技术架构](#-技术架构)
- [快速开始](#-快速开始)
- [项目展示](#-项目展示)
- [系统架构](#-系统架构)
- [API 文档](#-api-文档)
- [演示账号](#-演示账号)
- [项目结构](#-项目结构)
- [开发计划](#-开发计划)
- [贡献指南](#-贡献指南)
- [许可证](#-许可证)

---

## 🎯 项目简介

本项目是一个基于 **区块链技术** 的产品溯源管理系统，采用自主实现的 **PoW (Proof of Work)** 共识算法，为企业提供从生产到消费的全链路可追溯解决方案。

### 🌟 项目亮点

- 🔐 **区块链加密** - SHA256 哈希算法保证数据不可篡改
- 🎨 **多角色支持** - 生产商、经销商、消费者、监管者、管理员五大角色
- 📊 **数据可视化** - 实时供应链网络拓扑图、质量热力图
- 🤖 **智能合约** - 自动化供应链规则执行
- 🔍 **防伪验证** - 多层哈希加密 + 二维码扫描
- 📈 **高级分析** - AI 风险评估、碳足迹追踪、库存预测

---

## ✨ 核心功能

<table>
<tr>
<td width="50%">

### 🏭 供应链管理
- ✅ 产品注册与批次管理
- ✅ 所有权转移与追踪
- ✅ 质检记录上链
- ✅ 物流信息追踪
- ✅ 采购请求管理
- ✅ 产品召回系统

</td>
<td width="50%">

### 🔒 区块链功能
- ✅ 自主 PoW 区块链
- ✅ 区块链浏览器
- ✅ 链完整性验证
- ✅ 智能合约引擎
- ✅ 产品认证证书
- ✅ 防伪验证码生成

</td>
</tr>
<tr>
<td width="50%">

### 📊 数据分析
- ✅ 供应链网络可视化
- ✅ 质量热力图
- ✅ 风险评估模型
- ✅ 碳足迹追踪
- ✅ 库存智能预测
- ✅ 批次质量统计

</td>
<td width="50%">

### 👥 用户体验
- ✅ 角色权限管理
- ✅ 实时消息通知
- ✅ 产品收藏/关注
- ✅ 产品对比分析
- ✅ 二维码扫描
- ✅ 多语言支持

</td>
</tr>
</table>

---

## 🔧 技术架构

### 核心技术栈

```
前端技术
├── Bootstrap 5      # UI 框架
├── jQuery           # JavaScript 库
├── Chart.js         # 数据可视化
└── Cytoscape.js     # 网络图可视化

后端技术
├── Python 3.9+      # 编程语言
├── Flask 2.3+       # Web 框架
├── SQLite           # 数据库
└── Jinja2           # 模板引擎

区块链技术
├── SHA256           # 哈希算法
├── PoW              # 工作量证明
├── Merkle Tree      # 默克尔树
└── Smart Contract   # 智能合约

安全加密
├── Werkzeug         # 密码哈希
├── hashlib          # 加密库
└── QRCode           # 二维码生成
```

### 系统特性

- 🚀 **高性能** - 异步任务处理、消息队列优化
- 🔒 **高安全** - 多层加密、权限验证、SQL 注入防护
- 📱 **响应式** - 适配桌面、平板、移动端
- 🌐 **可扩展** - 模块化设计、插件化架构
- 📊 **数据驱动** - 完整的日志系统、审计追踪

---

## 🚀 快速开始

### 环境要求

```bash
Python 3.9+
pip (Python 包管理器)
```

### 安装步骤

#### 1️⃣ 克隆项目

```bash
git clone https://github.com/lpzams/blockchain-traceability-system.git
cd blockchain-traceability-system
```

#### 2️⃣ 安装依赖

```bash
pip install -r requirements.txt
```

#### 3️⃣ 初始化数据库

```bash
python scripts/init_db.py
```

> 💡 提示：运行时输入 `y` 创建演示数据

#### 4️⃣ 启动应用

```bash
python app.py
```

#### 5️⃣ 访问系统

在浏览器中打开：
```
http://localhost:5000
```

---

## 🖼️ 项目展示

### 主界面
> 系统首页展示了清晰的功能导航和角色选择

### 区块链浏览器
> 实时查看区块链数据，验证区块哈希和链完整性

### 产品溯源追踪
> 完整的产品生命周期追踪，从生产到消费全流程可视化

### 供应链网络图
> 基于 Cytoscape.js 的交互式供应链网络拓扑图

### 数据分析仪表盘
> 质量热力图、风险评估、碳足迹追踪等高级分析功能

### 智能合约执行
> 自动化供应链规则，支持条件触发和状态验证

---

## 🏗️ 系统架构

```
┌─────────────────────────────────────────────────────────────┐
│                       用户层 (User Layer)                      │
│  生产商 | 经销商 | 消费者 | 监管者 | 管理员                     │
└─────────────────────────────────────────────────────────────┘
                              ↓
┌─────────────────────────────────────────────────────────────┐
│                    表现层 (Presentation)                       │
│         Flask Routes | Jinja2 Templates | REST API           │
└─────────────────────────────────────────────────────────────┘
                              ↓
┌─────────────────────────────────────────────────────────────┐
│                     业务层 (Business Logic)                    │
│   服务层 | 智能合约 | 消息队列 | 通知系统 | 分析引擎           │
└─────────────────────────────────────────────────────────────┘
                              ↓
┌─────────────────────────────────────────────────────────────┐
│                     数据层 (Data Layer)                        │
│      区块链模块 | 数据库模块 | 溯源模块 | 特性模块              │
└─────────────────────────────────────────────────────────────┘
                              ↓
┌─────────────────────────────────────────────────────────────┐
│                    存储层 (Storage Layer)                      │
│           SQLite 数据库 | 区块链账本 | 文件系统                │
└─────────────────────────────────────────────────────────────┘
```

---

## 📡 API 文档

### 认证接口

| 方法 | 路径 | 描述 |
|------|------|------|
| POST | `/auth/login` | 用户登录 |
| POST | `/auth/register` | 用户注册 |
| GET | `/auth/logout` | 用户登出 |

### 产品接口

| 方法 | 路径 | 描述 |
|------|------|------|
| POST | `/manufacturer/register_product` | 注册产品 |
| POST | `/manufacturer/transfer` | 转移所有权 |
| GET | `/consumer/trace/<product_id>` | 产品溯源 |
| POST | `/manufacturer/quality_check` | 质检记录 |

### 区块链接口

| 方法 | 路径 | 描述 |
|------|------|------|
| GET | `/blockchain_explorer` | 区块链浏览器 |
| GET | `/features/certificate/<product_id>` | 获取产品证书 |
| POST | `/features/verify` | 防伪验证 |
| GET | `/features/chain_integrity/<product_id>` | 链完整性验证 |

> 📖 完整 API 文档请查看 [API.md](docs/API.md)

---

## 👤 演示账号

系统提供五种角色的演示账号：

| 👤 用户名 | 🔑 密码 | 🎭 角色 | 📝 权限说明 |
|-----------|---------|---------|-------------|
| `admin` | `1` | 管理员 | 系统管理、用户管理、数据管理 |
| `manufacturer1` | `123456` | 生产商 | 产品注册、质检、转移 |
| `distributor1` | `123456` | 经销商 | 采购、物流、转售 |
| `consumer1` | `123456` | 消费者 | 溯源查询、防伪验证、评价 |
| `regulator1` | `123456` | 监管者 | 审计、监督、报告 |

---

## 📁 项目结构

```
blockchain-traceability-system/
│
├── 📄 app.py                          # 应用入口文件
├── 📄 requirements.txt                # Python 依赖列表
├── 📄 README.md                       # 项目说明文档
├── 📄 .gitignore                      # Git 忽略配置
│
├── 📂 config/                         # 配置模块
│   ├── config.py                      # 环境配置
│   └── settings.py                    # 系统设置
│
├── 📂 models/                         # 数据模型层
│   ├── database.py                    # 数据库操作
│   ├── blockchain.py                  # 区块链核心
│   ├── blockchain_features.py         # 区块链高级功能
│   ├── blockchain_explorer.py         # 区块链浏览器
│   ├── traceability.py                # 溯源模块
│   └── advanced_analytics.py          # 高级分析
│
├── 📂 routes/                         # 路由控制层
│   ├── auth.py                        # 认证路由
│   ├── manufacturer.py                # 生产商路由
│   ├── distributor.py                 # 经销商路由
│   ├── consumer.py                    # 消费者路由
│   ├── admin.py                       # 管理员路由
│   ├── regulator.py                   # 监管者路由
│   ├── blockchain_features.py         # 区块链功能路由
│   ├── analytics.py                   # 分析路由
│   └── chat.py                        # 聊天路由
│
├── 📂 services/                       # 业务服务层
│   ├── smart_contract.py              # 智能合约引擎
│   ├── message_queue.py               # 消息队列
│   ├── notifications.py               # 通知系统
│   ├── async_processor.py             # 异步处理器
│   ├── blockchain_audit.py            # 区块链审计
│   ├── product_features.py            # 产品功能服务
│   ├── qrcode_service.py              # 二维码服务
│   ├── recall_system.py               # 召回系统
│   ├── alert_system.py                # 告警系统
│   ├── analytics.py                   # 分析服务
│   ├── carbon_tracking.py             # 碳足迹追踪
│   └── inventory_forecast.py          # 库存预测
│
├── 📂 templates/                      # 前端模板
│   ├── base.html                      # 基础模板
│   ├── login.html                     # 登录页面
│   ├── 📂 manufacturer/               # 生产商页面
│   ├── 📂 distributor/                # 经销商页面
│   ├── 📂 consumer/                   # 消费者页面
│   ├── 📂 admin/                      # 管理员页面
│   ├── 📂 regulator/                  # 监管者页面
│   ├── 📂 features/                   # 功能页面
│   └── 📂 analytics/                  # 分析页面
│
├── 📂 static/                         # 静态资源
│   ├── 📂 css/                        # 样式文件
│   ├── 📂 js/                         # JavaScript 文件
│   └── 📂 images/                     # 图片资源
│
├── 📂 scripts/                        # 工具脚本
│   └── init_db.py                     # 数据库初始化脚本
│
├── 📂 data/                           # 数据存储
│   └── blockchain.db                  # SQLite 数据库
│
└── 📂 docs/                           # 文档目录
    └── technical_report.md            # 技术报告
```

---

## 🎨 高级功能使用

### 1️⃣ 产品认证证书

输入产品 ID，生成带有 SHA256 加密签名的不可篡改认证证书

```bash
访问路径: /features/certificate/<product_id>
示例: /features/certificate/001
```

### 2️⃣ 防伪验证码

多层哈希加密生成唯一防伪码，支持二维码扫描验证

```bash
访问路径: /features/anti_counterfeit/<product_id>
示例: /features/anti_counterfeit/002
```

### 3️⃣ 链完整性验证

自动检测产品溯源链的连续性和完整性，识别潜在风险

```bash
访问路径: /features/chain_integrity/<product_id>
示例: /features/chain_integrity/003
```

### 4️⃣ 批次管理分析

批次质量统计、风险评估、合格率分析

```bash
访问路径: /features/batch_management/<batch_number>
示例: /features/batch_management/001
```

### 5️⃣ 智能合约

自动执行供应链交易规则，支持条件触发

```bash
访问路径: /features/smart_contracts
```

---

## 📊 数据示例

### 演示批次号

| 批次号 | 产品名称 | 生产商 | 状态 |
|--------|----------|--------|------|
| `001` | 西湖龙井茶叶 | 茶叶公司 | ✅ 已上链 |
| `002` | 有机绿茶 | 茶叶公司 | ✅ 已上链 |
| `003` | 铁观音 | 茶叶公司 | ✅ 已上链 |
| `004` | 有机大米 | 粮食公司 | ✅ 已上链 |
| `005` | 黑芝麻 | 粮食公司 | ✅ 已上链 |

---

## 📈 开发计划

### ✅ 已完成功能

- [x] 基础用户认证系统
- [x] 多角色权限管理
- [x] 区块链核心功能
- [x] 产品溯源追踪
- [x] 区块链浏览器
- [x] 智能合约引擎
- [x] 防伪验证系统
- [x] 数据分析仪表盘
- [x] 消息通知系统
- [x] 产品召回系统

### 🚧 进行中

- [ ] 移动端 App 开发
- [ ] 与长安链 ChainMaker 集成
- [ ] 机器学习风险预测模型优化
- [ ] 国际化多语言支持

### 📝 未来规划

- [ ] 支持 NFT 数字资产
- [ ] 集成 IPFS 分布式存储
- [ ] 跨链互操作性
- [ ] 零知识证明隐私保护
- [ ] 联盟链部署方案

---

## 🤝 贡献指南

我们欢迎所有形式的贡献！

### 如何贡献

1. **Fork** 本仓库
2. 创建您的特性分支 (`git checkout -b feature/AmazingFeature`)
3. 提交您的更改 (`git commit -m 'Add some AmazingFeature'`)
4. 推送到分支 (`git push origin feature/AmazingFeature`)
5. 打开一个 **Pull Request**

### 代码规范

- 遵循 PEP 8 Python 代码规范
- 添加必要的注释和文档字符串
- 编写单元测试覆盖新功能
- 确保所有测试通过

---

## 📞 联系方式

- **项目作者**: 泽泽
- **GitHub**: [@lpzams](https://github.com/lpzams)
- **项目主页**: [blockchain-traceability-system](https://github.com/lpzams/blockchain-traceability-system)

---

## 📄 许可证

本项目采用 **MIT** 许可证 - 详见 [LICENSE](LICENSE) 文件

```
MIT License

Copyright (c) 2026 泽泽

Permission is hereby granted, free of charge, to any person obtaining a copy
of this software and associated documentation files (the "Software")...
```

---

## 🙏 致谢

感谢以下开源项目：

- [Flask](https://flask.palletsprojects.com/) - Web 框架
- [Bootstrap](https://getbootstrap.com/) - UI 框架
- [Chart.js](https://www.chartjs.org/) - 数据可视化
- [Cytoscape.js](https://js.cytoscape.org/) - 网络图可视化
- [SQLite](https://www.sqlite.org/) - 数据库

---

## 📚 相关文档

- [📖 英文文档](README_EN.md)
- [🔧 技术报告](docs/technical_report.md)
- [🚀 快速启动指南](快速启动.md)
- [📋 项目说明](CLAUDE.md)

---

<div align="center">

### ⭐ 如果这个项目对您有帮助，请给一个星标！

**Made with ❤️ by 泽泽**

**© 2026 Blockchain Traceability System. All Rights Reserved.**

</div>
