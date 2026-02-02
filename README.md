# Identity Generator CLI

> [!WARNING]
>
> 1. 本项目全部由AI生成。
> 2. 本项目生成数据仅供学习使用，请勿用于其他用途。

一个专注于中文虚拟身份信息生成的 Python CLI 工具。基于 [Faker](https://faker.readthedocs.io/) 库，支持多种输出格式和自定义选项。

## 功能特性

- **中文身份生成**: 专门生成逼真的中文身份信息（姓名、地址、身份证号等）
- **身份证图片生成**: 生成逼真的身份证图片，包含自动生成的虚拟人像
- **多种输出格式**: JSON、CSV、表格、纯文本、SQL、Markdown、YAML、vCard
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
- Pillow >= 9.0.0（身份证图片生成）
- numpy >= 1.20.0（身份证图片生成）

## 使用方法

### 基本用法

```bash
# 生成一个默认身份（自动保存为 CSV 和身份证图片）
identity-gen
# 输出: identities_20260128_154644.csv
# 身份证图片: idcards/identities_20260128_154644_0000.png

# 生成 5 个身份（同时生成 5 张身份证图片）
identity-gen --count 5

# 只生成文本数据，不生成身份证图片
identity-gen --count 5 --no-idcard

# 输出为 JSON（通过后缀名或 --format）
identity-gen --output data.json --count 10
identity-gen --format json --count 10

# 输出到终端（用于管道或调试，不生成图片）
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
  -f, --format [json|csv|table|raw|sql|markdown|yaml|vcard]  输出格式 (优先级: --format > 文件后缀 > 默认csv)
  -o, --output PATH       输出文件路径 (根据后缀自动检测格式)
  --stdout                输出到终端而不是文件
  -i, --include TEXT      包含的字段 (可多次使用)
  -e, --exclude TEXT      排除的字段 (可多次使用)
  -s, --seed INTEGER      随机种子（用于可复现结果）
  -v, --verbose           显示详细日志
  --idcard / --no-idcard  是否同时生成身份证图片 (默认: 启用)
  --idcard-dir TEXT       身份证图片输出目录 (默认: idcards)
  --idcard-no-avatar      生成不带头像的身份证图片
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

# 生成身份证图片
identity-gen generate-idcard --count 5
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

#### 个人信息（10个）
- `name` - 全名
- `first_name` - 名
- `last_name` - 姓
- `gender` - 性别（男/女）
- `birthdate` - 出生日期
- `ssn` - 身份证号（18位，符合GB 11643-1999标准）
- `ethnicity` - 民族（56个民族，按人口比例分布）
- `blood_type` - 血型（A/B/AB/O型 + RH阴性/阳性）
- `height` - 身高（厘米，基于性别正态分布）
- `weight` - 体重（公斤，基于BMI计算）

#### 联系方式（7个）
- `email` - 邮箱地址（按市场份额分布，支持QQ邮箱与手机号关联）
- `phone` - 电话号码（11位，按运营商市场份额分布）
- `address` - 街道地址（完整的省市区街道信息）
- `city` - 城市
- `state` - 省份
- `zipcode` - 邮编（6位）
- `country` - 国家

#### 职业信息（4个）
- `company` - 公司名称
- `job_title` - 职位
- `education` - 学历（9个级别，按年龄限制）
- `major` - 专业（80+个专业）

#### 账户信息（4个）
- `username` - 用户名
- `password` - 密码（12位，包含大小写、数字和特殊字符）
- `wechat_id` - 微信号
- `qq_number` - QQ号（按长度分布）

#### 社会信息（3个）
- `political_status` - 政治面貌（13种，按年龄限制）
- `marital_status` - 婚姻状况（4种，按年龄分布）
- `religion` - 宗教信仰（按中国人口比例分布）

#### 财务信息（3个）
- `bank_card` - 银行卡号（银联卡，符合Luhn算法）
- `license_plate` - 车牌号（普通/新能源车牌）
- `social_credit_code` - 统一社会信用代码（18位，符合GB 32100-2015）

#### 数字身份（2个）
- `ip_address` - IP地址（IPv4，包含中国运营商常用段）
- `mac_address` - MAC地址（使用中国厂商OUI前缀）

#### 生辰信息（2个）
- `zodiac_sign` - 星座（根据出生日期计算）
- `chinese_zodiac` - 生肖（根据出生年份计算）

#### 其他信息（3个）
- `emergency_contact` - 紧急联系人（姓名及关系）
- `emergency_phone` - 紧急联系电话
- `hobbies` - 兴趣爱好（1-5个，分类随机）

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

### SQL 格式

```sql
INSERT INTO identities (name, email, phone) VALUES ('张三', 'zhangsan@example.com', '13800138000');
```

### Markdown 格式

```markdown
| name | email | phone |
| --- | --- | --- |
| 张三 | zhangsan@example.com | 13800138000 |
```

### YAML 格式

```yaml
- identity_1:
    name: "张三"
    email: "zhangsan@example.com"
    phone: "13800138000"
```

### vCard 格式

```vcard
BEGIN:VCARD
VERSION:3.0
N:张;三;;;
FN:张三
EMAIL:zhangsan@example.com
TEL:13800138000
END:VCARD
```

## 身份证图片生成

工具现在**默认**会在生成文本身份信息的同时，自动生成对应的身份证图片。

### 默认行为

当你运行主命令时，会同时生成：
1. **文本数据文件**（CSV/JSON等格式）
2. **身份证图片**（PNG格式，保存到 `idcards/` 目录）

```bash
# 生成身份数据 + 身份证图片（默认行为）
identity-gen --count 5
# 输出：
# - identities_20260128_154644.csv
# - idcards/identities_20260128_154644_0000.png
# - idcards/identities_20260128_154644_0001.png
# - ...
```

### 控制身份证图片生成

```bash
# 禁用身份证图片生成
identity-gen --count 5 --no-idcard

# 指定身份证图片输出目录
identity-gen --count 5 --idcard-dir ./my_idcards

# 生成不带头像的身份证图片
identity-gen --count 5 --idcard-no-avatar

# 组合使用
identity-gen --count 10 --idcard-dir ./photos --idcard-no-avatar
```

### 独立的身份证图片生成命令

如果你只想生成身份证图片而不需要文本数据：

```bash
# 只生成身份证图片
identity-gen generate-idcard --count 5

# 指定输出目录
identity-gen generate-idcard --count 10 --output-dir ./my_idcards

# 生成不带头像的身份证图片
identity-gen generate-idcard --count 3 --no-avatar

# 使用随机种子确保可复现
identity-gen generate-idcard --count 5 --seed 42

# 自定义文件名格式
identity-gen generate-idcard --count 3 --filename-pattern "{ssn}.png"
```

### 命令行选项（主命令）

```bash
identity-gen [OPTIONS]

身份证图片相关选项:
  --idcard / --no-idcard      是否同时生成身份证图片 (默认: 启用)
  --idcard-dir TEXT           身份证图片输出目录 (默认: idcards)
  --idcard-no-avatar          生成不带头像的身份证图片
```

### 命令行选项（独立命令）

```bash
identity-gen generate-idcard [OPTIONS]

选项:
  -n, --count INTEGER          生成数量 [默认: 1]
  -o, --output-dir TEXT        输出目录 [默认: idcards]
  --include-avatar             包含头像（默认启用）
  --no-avatar                  不包含头像
  -s, --seed INTEGER           随机种子
  -f, --filename-pattern TEXT  文件名模式 [默认: {name}_idcard.png]
                               可用占位符: {name}, {ssn}, {index}
  --help                       显示帮助信息
```

### 身份证图片说明

生成的身份证图片使用**真实身份证模板**，包括：
- **真实模板背景**：使用标准身份证底板图片
- **真实字体**：黑体、方正黑体、OCR-B等标准字体
- **标准布局**：严格按照身份证规范排布文字和头像位置
- **自动头像**：使用 Pillow 生成的虚拟人像（可禁用）
- **完整信息**：姓名、性别、民族、出生日期、住址、身份证号

头像生成特点：
- 支持男性和女性特征
- 包含肤色、发色、服装颜色的随机组合
- 添加噪点纹理增加真实感
- 完全离线生成，不依赖外部头像图片

### API 使用

```python
from identity_gen import IdentityGenerator, IdentityConfig
from identity_gen import IDCardImageGenerator, generate_idcard_image

# 创建配置并生成身份
config = IdentityConfig(locale="zh_CN", count=1)
generator = IdentityGenerator(config)
identity = generator.generate()

# 生成单张身份证图片
idcard_generator = IDCardImageGenerator()
img = idcard_generator.generate(
    identity=identity,
    output_path="idcard.png",
    include_avatar=True
)

# 或使用便捷函数
img = generate_idcard_image(identity, output_path="idcard.png")
```

## 开发

### 项目结构

```
identity-gen/
├── src/
│   └── identity_gen/
│       ├── __init__.py              # 包初始化，导出主要类
│       ├── cli.py                   # CLI 入口，支持子命令
│       ├── generator.py             # 身份生成逻辑
│       ├── idcard_image_generator.py # 身份证图片生成
│       ├── china_data.py            # 中文行政区划、姓名、公司数据
│       ├── models.py                # Pydantic 数据模型
│       ├── formatters.py            # 输出格式化（JSON/CSV/TABLE/RAW/SQL/Markdown/YAML/vCard）
│       └── data/                    # 数据文件
│           ├── assets/              # 身份证图片资源
│           │   ├── empty.png        # 身份证模板背景
│           │   ├── hei.ttf          # 黑体字体
│           │   ├── fzhei.ttf        # 方正黑体字体
│           │   ├── ocrb10bt.ttf     # OCR-B字体（身份证号）
│           │   └── avatar/          # 头像资源目录
│           ├── names.json           # 姓名数据（300+姓氏）
│           ├── jobs.json            # 职位数据（390+职位）
│           ├── companies.json       # 公司数据
│           ├── ethnicities.json     # 56个民族数据
│           ├── education.json       # 学历和专业数据
│           ├── political.json       # 政治面貌数据
│           ├── marital.json         # 婚姻状况数据
│           └── medical.json         # 血型数据
├── tests/                           # 测试套件
├── pyproject.toml                   # 项目配置
├── requirements.txt                 # 依赖
├── AGENTS.md                        # 开发指南
└── README.md                        # 本文档
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

- **v0.5.0** - 当前版本，新增身份证图片生成功能
  - 新增身份证图片生成：使用 `identity-gen generate-idcard` 命令生成逼真的身份证图片
  - 自动生成虚拟人像：使用 Pillow 绘制，支持男/女性别特征，不依赖外部图片资源
  - 新增 `IDCardImageGenerator` 类和 `generate_idcard_image()` 便捷函数
  - 支持批量生成身份证图片，可自定义文件名格式
  - 新增依赖：Pillow >= 9.0.0, numpy >= 1.20.0

- **v0.4.0** - 全面升级
  - 新增9个数据字段：星座、生肖、IP地址、MAC地址、统一社会信用代码、紧急联系人、紧急联系电话、兴趣爱好、宗教信仰
  - 优化数据关联性：手机号与QQ邮箱关联、姓名与紧急联系人关系关联、出生日期与星座生肖关联
  - 改进数据真实性：邮箱域名按市场份额分布、宗教信仰按中国人口比例分布
  - 代码质量提升：添加完整的类型提示、改进文档字符串、优化函数结构
  - 新增企业统一社会信用代码生成（符合GB 32100-2015标准）
  - 新增MAC地址生成（使用中国厂商OUI前缀）
  
- **v0.3.1** - 优化数据真实性
  - 添加基于2020年人口普查的姓氏频率分布
  - 运营商市场份额分布
- **v0.3.0** - 新增10个中国特有身份信息字段，支持8种输出格式
  - 新增字段：民族、学历、专业、政治面貌、婚姻状况、血型、身高、体重、银行卡号、微信号、QQ号、车牌号
  - 新增格式：SQL、Markdown、YAML、vCard
  - 扩展姓名数据库至300+姓氏
- **v0.2.0** - 专注于中文身份信息生成
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
