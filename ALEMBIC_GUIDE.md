
# Alembic 数据库迁移使用指南

## 概述

Alembic 是 SQLAlchemy 的数据库迁移工具，用于管理数据库结构的版本控制和变更。

## 目录结构

```
dragonai-v2-local/
├── alembic/
│   ├── versions/          # 迁移脚本目录
│   ├── env.py            # 迁移环境配置
│   ├── script.py.mako    # 迁移脚本模板
│   └── README
├── alembic.ini           # Alembic 主配置文件
└── ALEMBIC_GUIDE.md      # 本文件
```

## 常用命令

### 1. 查看当前数据库版本

```powershell
.\venv\Scripts\Activate.ps1
alembic current
```

### 2. 查看迁移历史

```powershell
alembic history
```

### 3. 创建新的迁移（自动检测模型变化）

```powershell
alembic revision --autogenerate -m "描述本次变更"
```

示例：
```powershell
alembic revision --autogenerate -m "add avatar field to users"
alembic revision --autogenerate -m "create new table for analytics"
```

### 4. 执行迁移（升级到最新版本）

```powershell
alembic upgrade head
```

### 5. 回滚迁移

回滚到上一个版本：
```powershell
alembic downgrade -1
```

回滚到指定版本：
```powershell
alembic downgrade &lt;revision_id&gt;
```

### 6. 升级到指定版本

```powershell
alembic upgrade &lt;revision_id&gt;
```

## 迁移工作流程

### 当需要修改数据库结构时：

1. **修改模型文件**

   在 `app/models/` 目录下修改对应的模型文件。

2. **生成迁移脚本**

   ```powershell
   alembic revision --autogenerate -m "your change description"
   ```

3. **检查生成的脚本**

   在 `alembic/versions/` 目录下找到新生成的迁移文件，检查内容是否正确。

4. **执行迁移**

   ```powershell
   alembic upgrade head
   ```

## 配置说明

### alembic.ini

主配置文件，包含数据库连接 URL 等配置。

### alembic/env.py

迁移环境配置，已配置为：
- 从 `app.config.settings` 读取数据库 URL
- 使用 `app.core.database.Base` 作为目标元数据
- 导入所有模型：user, conversation, message

## 当前状态

- **当前版本**: c527ba0bc760 (initial migration)
- **已创建表**: users, conversations, messages
- **数据库**: PostgreSQL

## 注意事项

1. **自动生成的迁移脚本需要检查**：`--autogenerate` 不能检测所有变化，生成后请务必检查。

2. **数据迁移**：涉及数据迁移时，需要手动编写迁移脚本。

3. **生产环境**：在生产环境执行迁移前，先在测试环境验证。

4. **备份数据**：重要迁移前务必备份数据库。

## 示例

### 示例 1：添加新字段到用户表

1. 修改 `app/models/user.py`：
```python
class User(Base):
    __tablename__ = "users"
    
    id = Column(Integer, primary_key=True, index=True)
    username = Column(String(50), unique=True, index=True, nullable=False)
    email = Column(String(100), unique=True, index=True)
    # 新增字段
    avatar = Column(String(255), nullable=True)
```

2. 生成迁移：
```powershell
alembic revision --autogenerate -m "add avatar field to users"
```

3. 执行迁移：
```powershell
alembic upgrade head
```

### 示例 2：创建新表

1. 在 `app/models/` 目录下创建新模型文件
2. 在 `app/models/__init__.py` 中导入
3. 生成并执行迁移

## 故障排除

### 迁移冲突

如果遇到迁移冲突，可以：
1. 查看当前状态：`alembic current`
2. 查看历史：`alembic history`
3. 根据需要升级或降级到特定版本

### 自动检测失败

如果 `--autogenerate` 没有检测到变化：
1. 确保模型已在 `alembic/env.py` 中导入
2. 检查模型是否正确继承自 `Base`
3. 可以手动创建迁移：`alembic revision -m "manual change"`

