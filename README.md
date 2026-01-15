# 元数据管理系统

> 纯AI打造的一站式元数据管理平台，轻松掌控您的数据资产

## 📋 项目简介

元数据管理系统是一个功能强大的企业级元数据管理平台，支持多种主流数据库的元数据抽取、管理和展示。系统采用现代化的Web界面，提供直观的用户体验，帮助企业更好地理解和治理数据资产。

![Uploading image.png…]()


## ✨ 核心特性

### 数据源管理
- 支持多种数据库类型：MySQL、PostgreSQL、SQL Server、Oracle

- 集中管理数据源连接

- 实时测试连接状态

- 安全的密码存储

  ![dashbord](D:\python\py_opencode\metadata_manager - v1.0\pic\dashbord.jpg)

### 元数据抽取
- **全量抽取**：抽取数据源中的所有表元数据

- **增量抽取**：只抽取新增或变更的表元数据，提升效率

- **仅结构抽取**：快速获取表结构信息，无需统计数据

- 自动获取表结构、字段信息、统计数据

- 支持表间关联关系（外键）抽取

  ![etl_his](D:\python\py_opencode\metadata_manager - v1.0\pic\etl_his.jpg)

### 元数据浏览
- 直观的表格展示

- 表详情查看：字段名、类型、长度、注释等完整信息

- 支持按数据源筛选

- 实时搜索和过滤

- 表统计信息（行数、数据大小）

  ![image-20260115105010383](C:\Users\Administrator\AppData\Roaming\Typora\typora-user-images\image-20260115105010383.png)

  ![image-20260115105100118](C:\Users\Administrator\AppData\Roaming\Typora\typora-user-images\image-20260115105100118.png)

### ETL任务管理
- 可视化任务创建和配置

- 灵活的调度方式：
  - 时间间隔调度（分钟、小时、天、周）
  - CRON表达式调度
  - 手动执行
  
- 任务类型：全量抽取、增量抽取、仅结构抽取

- 任务状态管理和执行历史追踪

  ![etl](D:\python\py_opencode\metadata_manager - v1.0\pic\etl.jpg)

### 用户权限管理
- 多角色支持：
  - **管理员**：完整的系统管理权限
  - **普通用户**：数据查看和管理权限
  - **只读用户**：仅查看权限
  
- 个人信息管理

- 密码修改功能

- 操作权限控制

  ![user](D:\python\py_opencode\metadata_manager - v1.0\pic\user.jpg)

### 数据统计分析
- 资源概览仪表板
- 数据源、表、字段数量统计
- 数据量统计和可视化
- 抽取历史记录

## 🏗️ 系统架构

```
元数据管理系统
│
├── 前端层
│   ├── HTML5 + Bootstrap 5
│   ├── JavaScript (ES6+)
│   └── Font Awesome 图标库
│
├── 后端层
│   └── Flask Web 框架
│       ├── RESTful API
│       ├── 用户认证与授权
│       └── 业务逻辑处理
│
├── 数据访问层
│   ├── SQLAlchemy ORM
│   └── 元数据库
│
└── 元数据抽取层
    ├── 抽取器基类 (MetadataExtractorBase)
    ├── MySQL 抽取器
    ├── PostgreSQL 抽取器
    ├── SQL Server 抽取器
    └── Oracle 抽取器
```

## 🚀 快速开始

### 环境要求

- Python 3.8+
- pip 包管理器
- SQLite（默认）或其他支持的数据库

### 安装步骤

1. **克隆仓库**
```bash
git clone https://github.com/yourusername/metadata-manager.git
cd metadata-manager
```

2. **安装依赖**
```bash
pip install -r requirements.txt
```

3. **初始化数据库**
```bash
python app.py
```

系统首次启动时会自动创建所需的数据库表。

4. **访问系统**
```
http://localhost:5000
```

5. **登录系统**
```
默认管理员账号：
用户名：admin
密码：admin123
```

⚠️ **安全提醒**：首次登录后请立即修改默认密码！

## 📦 安装依赖

```bash
pip install -r requirements.txt
```

主要依赖：
- Flask 2.3.3
- SQLAlchemy 2.0.21
- PyMySQL 1.1.0
- python-dotenv 1.0.0
- Werkzeug 2.3.7

## 📖 使用指南

### 1. 添加数据源

1. 登录系统后，点击"数据源管理"
2. 点击"添加数据源"按钮
3. 填写数据源信息：
   - 数据源名称
   - 数据库类型
   - 主机地址
   - 端口号
   - 用户名
   - 密码
   - 数据库名
4. 点击"测试连接"验证配置
5. 点击"保存"完成添加

### 2. 创建ETL任务

1. 点击"ETL任务"菜单
2. 点击"添加任务"按钮
3. 配置任务信息：
   - 任务名称
   - 任务类型（全量抽取、增量抽取、仅结构抽取）
   - 选择数据源
   - 调度规则（时间间隔、CRON表达式、手动执行）
   - 任务描述
4. 保存任务

### 3. 执行元数据抽取

- **手动执行**：在任务列表中点击"执行"按钮
- **定时执行**：配置调度规则后，系统会自动执行
- **查看结果**：在"抽取历史"中查看执行结果

### 4. 浏览元数据

1. 点击"元数据浏览"菜单
2. 选择要查看的数据源
3. 查看表列表和统计信息
4. 点击"查看"按钮查看表的详细信息（字段、类型、长度、注释等）

### 5. 用户管理（仅管理员）

1. 点击"用户管理"菜单
2. 查看所有用户列表
3. 添加新用户、编辑用户信息、删除用户
4. 管理用户角色和状态

### 6. 修改个人信息

所有用户都可以修改自己的个人信息和密码：
1. 点击用户名，选择"个人资料"
2. 修改邮箱和姓名
3. 在个人中心修改密码

## 🔧 配置说明

### 环境变量

创建 `.env` 文件（可选）：

```env
# 数据库配置
DATABASE_URL=sqlite:///metadata.db

# 会话密钥（生产环境请修改）
SECRET_KEY=your-secret-key-here

# 运行配置
FLASK_ENV=development
FLASK_DEBUG=False
```

### 数据库支持

默认使用 SQLite，生产环境建议使用 MySQL ：

```python
# MySQL
DATABASE_URL=mysql+pymysql://username:password@localhost:3306/database_name

# PostgreSQL
DATABASE_URL=postgresql://username:password@localhost:5432/database_name
```

## 🎯 抽取类型说明

| 抽取类型 | 说明 | 适用场景 |
|---------|------|---------|
| 全量抽取 | 抽取所有表的完整元数据 | 首次初始化、完全同步 |
| 增量抽取 | 只抽取新增或变更的表 | 定期同步、提升效率 |
| 仅结构抽取 | 只抽取表结构，不统计行数和数据量 | 快速预览、结构比对 |

## 👥 用户角色说明

| 角色 | 权限 | 说明 |
|-----|------|------|
| 管理员 (admin) | 完整权限 | 可以管理所有用户、数据源、ETL任务 |
| 普通用户 (user) | 管理权限 | 可以创建和管理数据源、ETL任务，查看元数据 |
| 只读用户 (viewer) | 查看权限 | 只能查看元数据，不能创建或修改 |

## 🔒 安全建议

1. **修改默认密码**：首次登录后立即修改管理员密码
2. **配置 HTTPS**：生产环境必须使用 HTTPS
3. **使用强密码**：所有账户使用强密码
4. **定期备份**：定期备份元数据库
5. **限制访问**：配置防火墙规则，限制系统访问
6. **日志监控**：定期检查系统日志



## 🛠️ 开发指南

### 项目结构

```
metadata-manager/
├── app.py                 # 应用入口
├── api.py                 # API 路由和业务逻辑
├── auth.py                # 用户认证和授权
├── models.py              # 数据模型
├── db_config.py           # 数据库配置
├── extractor_base.py      # 元数据抽取器基类
├── db_manager.py          # 数据库管理器
├── config.py              # 配置管理
├── exceptions.py          # 自定义异常
├── templates/             # HTML 模板
│   ├── index.html
│   ├── login.html
│   ├── dashboard.html
│   ├── data_sources.html
│   ├── etl.html
│   ├── metadata.html
│   ├── history.html
│   ├── users.html
│   └── table_details.html
├── static/                # 静态资源
│   ├── css/
│   │   └── style.css
│   └── js/
│       └── main.js
├── metadata.db           # SQLite 数据库（默认）
├── requirements.txt       # Python 依赖
└── README.md             # 项目文档
```

### 启动开发服务器

```bash
python app.py
```

访问：http://localhost:5000

### 添加新功能

1. 在 `models.py` 中定义数据模型
2. 在 `api.py` 中添加 API 路由
3. 在 `templates/` 中创建 HTML 模板
4. 在 `static/js/` 中添加前端逻辑

## 🧪 测试

```bash
# 运行测试（如果存在）
python -m pytest tests/
```

## 📝 更新日志

### v1.0.0 (2026-01)
- ✨ 初始版本发布
- 🎉 支持多种数据库元数据抽取
- 👥 完整的用户权限管理
- 📊 数据可视化仪表板
- 🔄 ETL任务调度功能

## 🤝 贡献指南

欢迎提交 Issue 和 Pull Request！

1. Fork 本仓库
2. 创建特性分支 (`git checkout -b feature/AmazingFeature`)
3. 提交更改 (`git commit -m 'Add some AmazingFeature'`)
4. 推送到分支 (`git push origin feature/AmazingFeature`)
5. 开启 Pull Request

## 📄 许可证

本项目采用 MIT 许可证 - 详见 [LICENSE](LICENSE) 文件

## 📧 联系方式

- **邮箱**：changchunyouxiang@qq.com
- **项目地址**：https://github.com/yourusername/metadata-manager

## 🙏 致谢

感谢所有为本项目做出贡献的开发者！

特别感谢以下开源项目：
- [Flask](https://flask.palletsprojects.com/)
- [Bootstrap](https://getbootstrap.com/)
- [SQLAlchemy](https://www.sqlalchemy.org/)
- [Font Awesome](https://fontawesome.com/)

---

<p align="center">
  <b>2026 元数据管理系统 纯AI打造</b>
</p>
