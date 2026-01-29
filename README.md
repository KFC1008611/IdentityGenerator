# Identity Generator CLI

> [!WARNING]
>
> 1. 本项目全部由AI生成。
> 2. 本项目生成数据仅供学习使用，请勿用于其他用途。

一个专注于中文虚拟身份信息生成的 Python CLI 工具。基于 [Faker](https://faker.readthedocs.io/) 库，支持多种输出格式和自定义选项。

## 功能特性

- **中文身份生成**: 专门生成逼真的中文身份信息（姓名、地址、身份证号等）
- **多种输出格式**: JSON、CSV、表格、纯文本
- **批量生成**: 单次可生成 1-10,000 个身份
- **字段定制**: 选择包含或排除特定字段
- **可重复生成**: 支持随机种子，确保结果可复现
- **文件输出**: 支持输出到文件或标准输出
- **美观界面**: 使用 Rich 库提供精美的终端输出

## 安装

### 从源码安装

```bash
# 克隆仓库
git clone https://github.com/example/identity-gen.git
cd identity-gen

# 创建虚拟环境（推荐）
python -m venv venv
source venv/bin/activate  # Linux/Mac
# 或: venv\Scripts\activate  # Windows

# 安装依赖
pip install -r requirements.txt

# 安装包（开发模式）
pip install -e .
```

### 依赖要求

- Python 3.8+
- click >= 8.0.0
- faker >= 18.0.0
- pydantic >= 2.0.0
- tabulate >= 0.9.0
- rich >= 13.0.0

## 使用方法

### 基本用法

```bash
# 生成一个默认身份（自动保存为 CSV）
identity-gen
# 输出: identities_20260128_154644.csv

# 生成 5 个身份
identity-gen --count 5

# 输出为 JSON（通过后缀名或 --format）
identity-gen --output data.json --count 10
identity-gen --format json --count 10

# 输出到终端（用于管道或调试）
identity-gen --count 5 --stdout

# 指定输出文件名（自动检测格式）
identity-gen --count 10 --output my_data.json   # JSON 格式
identity-gen --count 10 --output my_data.csv    # CSV 格式
```

### 快捷命令

```bash
# 使用 igen 快捷命令（与 identity-gen 完全等价）
igen --count 10
igen --format json --count 5
```

### 命令行选项

```bash
identity-gen [OPTIONS]

选项:
  -l, --locale TEXT       语言环境 (默认: zh_CN)
  -n, --count INTEGER     生成数量 (默认: 1)
  -f, --format [json|csv|table|raw]  输出格式 (优先级: --format > 文件后缀 > 默认csv)
  -o, --output PATH       输出文件路径 (根据后缀自动检测格式)
  --stdout                输出到终端而不是文件
  -i, --include TEXT      包含的字段 (可多次使用)
  -e, --exclude TEXT      排除的字段 (可多次使用)
  -s, --seed INTEGER      随机种子（用于可复现结果）
  -v, --verbose           显示详细日志
  --help                  显示帮助信息
```

### 子命令

```bash
# 查看所有可用字段
identity-gen fields

# 查看支持的语言环境（当前仅支持中文）
identity-gen locales

# 预览示例身份
identity-gen preview
```

### 输出行为

**重要**: 工具默认将生成的数据保存到文件，而不是终端输出。终端只显示日志信息。

**格式优先级**:
1. `--format` 参数（最高优先级）
2. 文件后缀名自动检测
3. 默认 CSV 格式

```bash
# 默认行为：CSV 格式，自动生成文件名（如 identities_20260128_154644.csv）
identity-gen --count 10

# 通过文件后缀名自动检测格式
identity-gen --count 10 --output data.json     # 自动使用 JSON 格式
identity-gen --count 10 --output report.csv    # 自动使用 CSV 格式

# --format 参数覆盖文件后缀名
identity-gen --count 10 --output report.csv --format json  # 使用 JSON 格式

# 输出到终端（用于管道或查看）
identity-gen --count 5 --stdout

# 查看生成的文件
ls identities_*.csv
```

#### 自定义字段

```bash
# 只生成姓名和邮箱
identity-gen --include name --include email --count 5

# 排除敏感信息
identity-gen --exclude ssn --exclude password --count 10
```

#### 批量生成并保存

```bash
# 生成 100 个身份（默认 CSV 格式）
identity-gen --count 100

# 生成 100 个身份并保存为指定 CSV 文件
identity-gen --count 100 --output identities.csv

# 生成 JSON 格式数据（通过后缀名自动检测）
identity-gen --count 50 --output data.json

# 生成 JSON 格式数据（通过 --format 指定）
identity-gen --count 50 --format json --output data.txt  # 后缀是 txt，但格式是 JSON

# 生成多种格式
identity-gen --count 100 --output users.json    # JSON
identity-gen --count 100 --output users.csv     # CSV
identity-gen --count 100 --output users.txt     # CSV（无法识别的后缀，使用默认）
```

#### 可复现生成

```bash
# 使用相同的种子生成相同的数据
identity-gen --seed 42 --count 5
# 再次运行会得到相同结果
identity-gen --seed 42 --count 5
```

### 可用字段

#### 个人信息
- `name` - 全名
- `first_name` - 名
- `last_name` - 姓
- `birthdate` - 出生日期
- `ssn` - 身份证号

#### 联系方式
- `email` - 邮箱地址
- `phone` - 电话号码
- `address` - 街道地址
- `city` - 城市
- `state` - 省份
- `zipcode` - 邮编
- `country` - 国家

#### 职业信息
- `company` - 公司名称
- `job_title` - 职位

#### 账户信息
- `username` - 用户名
- `password` - 密码（12位，包含大小写、数字和特殊字符）

### 语言环境

当前版本专注于中文身份信息生成：
- `zh_CN` - 中文（中国）

查看支持的语言环境：
```bash
identity-gen locales
```

## 输出示例

**注意**: 以下示例使用 `--stdout` 参数在终端显示。实际使用时，数据会自动保存到文件。

### 表格格式

```
+----------+------------------+----------------------------+
| name     | email            | phone                      |
+==========+==================+============================+
| 张三     | zhangsan@example.com | 13800138000               |
+----------+------------------+----------------------------+
```

### JSON 格式

```json
[
  {
    "name": "张三",
    "email": "zhangsan@example.com",
    "phone": "13800138000",
    "address": "北京市朝阳区建国路88号",
    "city": "北京",
    "country": "中国"
  }
]
```

### CSV 格式

```csv
name,email,phone
张三,zhangsan@example.com,13800138000
```

## 开发

### 项目结构

```
identity-gen/
├── src/
│   └── identity_gen/
│       ├── __init__.py       # 包初始化
│       ├── cli.py            # CLI 入口
│       ├── generator.py      # 身份生成逻辑
│       ├── china_data.py     # 中文数据提供者
│       ├── models.py         # Pydantic 数据模型
│       └── formatters.py     # 输出格式化
├── tests/                    # 测试套件
├── pyproject.toml            # 项目配置
├── requirements.txt          # 依赖
└── README.md                 # 本文档
```

### 运行测试

```bash
# 安装开发依赖
pip install -e ".[dev]"

# 运行测试
pytest

# 带覆盖率报告
pytest --cov=identity_gen --cov-report=html
```

### 代码规范

项目遵循以下规范：
- **PEP 8**: Python 代码风格
- **Black**: 代码格式化（行长度 100）
- **MyPy**: 类型检查
- **Pydantic**: 数据验证

```bash
# 格式化代码
black src/

# 类型检查
mypy src/identity_gen

# 代码检查
flake8 src/
```

## API 使用

除了 CLI，你也可以在 Python 代码中直接使用：

```python
from identity_gen import IdentityGenerator, IdentityConfig

# 创建配置
config = IdentityConfig(
    locale="zh_CN",
    count=5,
    include_fields=["name", "email", "phone"]
)

# 创建生成器
generator = IdentityGenerator(config)

# 生成身份
identities = generator.generate_batch()

# 使用数据
for identity in identities:
    print(f"{identity.name}: {identity.email}")
```

## 版本历史

- **v0.2.0** - 当前版本，专注于中文身份信息生成
- **v0.1.0** - 初始版本

## 许可证

MIT License - 详见 [LICENSE](LICENSE) 文件

## 贡献

欢迎提交 Issue 和 Pull Request！

1. Fork 项目
2. 创建功能分支 (`git checkout -b feature/AmazingFeature`)
3. 提交更改 (`git commit -m 'Add some AmazingFeature'`)
4. 推送到分支 (`git push origin feature/AmazingFeature`)
5. 创建 Pull Request

## 致谢

- [Faker](https://faker.readthedocs.io/) - 虚假数据生成库
- [Click](https://click.palletsprojects.com/) - Python CLI 框架
- [Rich](https://rich.readthedocs.io/) - 终端格式化库
- [Tabulate](https://github.com/astanin/python-tabulate) - 表格格式化
