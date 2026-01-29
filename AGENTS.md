# AGENTS.md - Chinese Identity Generator CLI

## Project Overview
A Python CLI tool for generating realistic Chinese virtual identity information.
This is a Chinese-focused tool that generates authentic Chinese names, addresses,
ID cards, phone numbers, and other identity data.

## Agent Guidelines

### Language Requirement
**必须使用中文回答所有问题。** 无论用户使用什么语言提问，都应使用中文回复。

### Documentation Maintenance
**每次代码变更后必须评估文档更新需求：**
1. 在完成任何代码修改后，立即评估相关文档（README.md、AGENTS.md等）是否需要同步更新
2. 评估维度包括但不限于：
   - 新增/删除的功能特性
   - API 接口的变化
   - 字段或格式的增减
   - 使用示例的更新
   - 项目结构的变更
3. 如果评估结果为需要更新，**必须立即执行文档更新**，不得拖延
4. 文档与代码保持同步是强制要求

## Core Stack
- Python 3.8+
- Faker library (for base data generation)
- Click library for CLI interface (with group commands and subcommands)
- Pydantic v2 for data validation and models
- Rich library for beautiful terminal UI
- Tabulate for table formatting

## Project Structure
```
.
├── src/
│   └── identity_gen/           # Main package
│       ├── __init__.py         # Package init, exports main classes, version 0.3.0
│       ├── cli.py              # CLI entry point with Click group + 3 subcommands
│       ├── generator.py        # Identity generation logic with Chinese-specific providers
│       ├── china_data.py       # Chinese administrative divisions, names, companies, jobs data
│       ├── models.py           # Pydantic data models (Identity, IdentityConfig, enums)
│       ├── formatters.py       # Output format handlers (JSON, CSV, TABLE, RAW, SQL, Markdown, YAML, vCard)
│       └── data/               # JSON data files
│           ├── names.json      # 300+ Chinese surnames and given names
│           ├── jobs.json       # 390+ job titles with categories and age ranges
│           ├── companies.json  # Company types and name words
│           ├── ethnicities.json # 56 Chinese ethnic groups with population ratios
│           ├── education.json  # Education levels (9) and majors (80+)
│           ├── political.json  # 13 political statuses with age constraints
│           ├── marital.json    # 4 marital statuses with age-dependent probabilities
│           └── medical.json    # Blood types with distribution
├── tests/                      # Test suite (pytest)
│   ├── test_cli.py
│   ├── test_generator.py
│   ├── test_models.py
│   └── test_formatters.py
├── AGENTS.md                   # This file - agent guidelines
├── README.md                   # User documentation (Chinese)
├── pyproject.toml              # Project configuration, dependencies, tool settings
├── requirements.txt            # Runtime dependencies
└── run.py                      # Direct execution script
```

## Key Modules

### cli.py
- Uses `@click.group(invoke_without_command=True)` for main command
- Rich library for beautiful terminal output (logo, panels, styled text)
- Three subcommands: `fields`, `locales`, `preview`
- Supports both file output (default) and stdout (`--stdout` flag)
- Smart format detection from file extension
- Comprehensive logging with verbose mode

### generator.py
- `IdentityGenerator` class - main generation engine
- Chinese-specific generation methods:
  - `generate_chinese_id_card()` - Valid Chinese ID with GB 11643-1999 checksum
  - `generate_chinese_phone()` - Realistic Chinese mobile numbers (all carriers)
  - `generate_chinese_name()` - Authentic Chinese names with gender support
  - `generate_chinese_email()` - China-specific email domains
  - `generate_chinese_company()` - Realistic Chinese company names
  - `generate_chinese_job_title()` - Common Chinese job titles
  - `generate_chinese_username()` - Chinese-style usernames
  - `generate_height()` / `generate_weight()` - BMI-based height/weight
  - `generate_bank_card()` - Valid UnionPay card with Luhn checksum
  - `generate_wechat_id()` - Realistic WeChat ID patterns
  - `generate_qq_number()` - Length-distributed QQ numbers
  - `generate_license_plate()` - Chinese license plates (including new energy)
- Gender consistency across name and ID card
- Address bundle generation (province-city-district-street)
- Age-appropriate generation for education, political status, marital status

### china_data.py
- Complete Chinese administrative divisions (国家统计局行政区划代码)
- Province-City-District mappings for all 34 provinces
- Area codes for ID card generation
- Chinese surnames, male names, female names (loaded from JSON)
- Company types and name words (loaded from JSON)
- Job titles data (loaded from JSON)

### models.py
- `Identity` - Pydantic model with 28 optional fields
- `IdentityConfig` - Configuration with validation
  - Locale validation (only zh_CN allowed)
  - Count validation (1-10,000)
  - Field include/exclude validation against IdentityField enum
- `OutputFormat` enum - json, csv, table, raw, sql, markdown, yaml, vcard
- `IdentityField` enum - all 28 valid field names

### formatters.py
- `IdentityFormatter` class with static methods
- `format_json()` - Pretty-printed JSON with unicode support
- `format_csv()` - Standard CSV with proper encoding
- `format_table()` - Grid table using tabulate
- `format_raw()` - Simple text format
- `format_sql()` - SQL INSERT statements
- `format_markdown()` - Markdown table format
- `format_yaml()` - YAML format
- `format_vcard()` - vCard 3.0 format
- `write_output()` - File or stdout output

## Code Conventions

### Type Hints
- Use type hints throughout (function params, return types)
- Use `Optional[X]` for nullable values
- Use `Set[str]`, `List[X]`, `Dict[str, X]` for collections

### Style Guide
- Follow PEP 8
- Maximum line length: 100 characters (Black config)
- Use docstrings for all public functions/classes (Google style)
- Prefer composition over inheritance

### Error Handling
- Use custom exceptions for domain errors
- Never suppress exceptions without logging
- Provide user-friendly error messages in CLI
- Exit with appropriate status codes (sys.exit(1) on error)
- Use try/except in CLI commands with verbose traceback option

### Pydantic Patterns
- Use `@field_validator` for custom validation (v2 syntax)
- Use `Field()` for descriptions and defaults
- Use `model_dump()` instead of deprecated `dict()` (v2)
- Validate enums against allowed values

### CLI Design Patterns
- Use Click decorators for commands
- Use `@click.pass_context` for shared state
- Support both interactive and non-interactive modes
- Provide meaningful error messages
- Support multiple output formats (JSON, CSV, TABLE, RAW, SQL, Markdown, YAML, vCard)
- Include --help descriptions for all commands and options
- Use Rich `Console` and `Text` for styled output
- Log to terminal, write data to file (separate concerns)

### Testing Requirements
- Write unit tests for generators
- Test CLI commands using Click's test runner (CliRunner)
- Mock Faker to ensure reproducible tests
- Maintain >80% code coverage (configured in pyproject.toml)

### Anti-Patterns (NEVER DO)
- NEVER use bare except clauses
- NEVER print directly; use logging or Click's echo
- NEVER hardcode locale strings; use Faker's localization (though zh_CN is forced)
- NEVER expose sensitive data in error messages
- NEVER use Pydantic v1 syntax (dict(), __root__, etc.)
- NEVER use `as any`, `@ts-ignore`, `@ts-expect-error` (type safety is required)

## Dependencies
Runtime:
- click>=8.0.0
- faker>=18.0.0
- pydantic>=2.0.0
- tabulate>=0.9.0
- rich>=13.0.0

Dev (optional):
- pytest>=7.0.0
- pytest-cov>=4.0.0
- black>=23.0.0
- flake8>=6.0.0
- mypy>=1.0.0

## CLI Commands Reference

### Main Command (generate)
```bash
identity-gen [OPTIONS]
  -l, --locale TEXT       # Locale (default: zh_CN, only zh_CN supported)
  -n, --count INTEGER     # Number to generate (default: 1, max: 10000)
  -f, --format [json|csv|table|raw|sql|markdown|yaml|vcard]  # Output format
  -o, --output PATH       # Output file path
  --stdout                # Output to stdout instead of file
  -i, --include TEXT      # Fields to include (multiple)
  -e, --exclude TEXT      # Fields to exclude (multiple)
  -s, --seed INTEGER      # Random seed for reproducibility
  -v, --verbose           # Enable verbose logging
```

### Subcommands
```bash
identity-gen fields       # List all available identity fields
identity-gen locales      # List supported locales (zh_CN only)
identity-gen preview      # Generate and display a sample identity
```

## Available Identity Fields (28 total)

### Personal (9)
- `name` - Full name (GivenName Surname format)
- `first_name` - Given name (名)
- `last_name` - Surname (姓)
- `birthdate` - Date of birth
- `ssn` - Chinese ID card number (18 digits with checksum)
- `ethnicity` - Ethnicity (56 ethnic groups with population ratios)
- `blood_type` - Blood type (A/B/AB/O + RH negative/positive)
- `height` - Height in cm (gender-based normal distribution)
- `weight` - Weight in kg (BMI-based calculation)

### Contact (7)
- `email` - Email address (China-specific domains)
- `phone` - Mobile phone number
- `address` - Full street address
- `city` - City name
- `state` - Province name
- `zipcode` - Postal code (6 digits)
- `country` - Country (always "中国")

### Professional (4)
- `company` - Company name
- `job_title` - Job title
- `education` - Education level (9 levels from primary to PhD)
- `major` - College major (80+ majors for higher education)

### Account (4)
- `username` - Username
- `password` - Password (12 chars, mixed case + digits + special)
- `wechat_id` - WeChat ID (realistic patterns)
- `qq_number` - QQ number (length-distributed)

### Social (2)
- `political_status` - Political status (13 statuses with age constraints)
- `marital_status` - Marital status (4 statuses with age-dependent probabilities)

### Finance (2)
- `bank_card` - Bank card number (UnionPay with Luhn checksum)
- `license_plate` - License plate (standard and new energy vehicles)

## Output Formats

1. **JSON** - Pretty-printed array of objects
2. **CSV** - Standard CSV with headers
3. **TABLE** - Grid table for terminal display
4. **RAW** - Simple text format with separators
5. **SQL** - SQL INSERT statements
6. **Markdown** - Markdown table format
7. **YAML** - YAML format
8. **vCard** - vCard 3.0 format

## Chinese Data Sources

- Administrative divisions: 国家统计局行政区划代码
- Names: Common Chinese surnames and given names
- Phone: All major Chinese carriers (移动, 联通, 电信, 虚拟运营商)
- Email: Popular Chinese email providers (QQ, 163, 126, etc.)
- ID Cards: GB 11643-1999 standard with valid checksum calculation

## Version
Current version: 0.3.1

## Recent Improvements (v0.3.1)
1. **数据真实性优化**
   - 姓氏生成：使用2020年中国人口普查的真实频率数据
     - 前5大姓（王、李、张、刘、陈）占比约30.8%
     - 前100大姓占比约85%
     - 添加 `get_weighted_surname()` 函数实现加权随机选择
   - 手机号生成：按运营商市场份额分布
     - 中国移动：~58%（ prefixes: 134-139, 147, 150-152, etc.）
     - 中国联通：~26%（ prefixes: 130-132, 145, 155-156, etc.）
     - 中国电信：~15%（ prefixes: 133, 149, 153, 173, etc.）
     - 虚拟运营商：~1%

2. **代码质量改进**
   - 为所有公共函数添加完整的 Google Style 文档字符串
   - 添加详细的参数说明、返回值说明和示例
   - 补充类型提示，提高代码可维护性
   - 添加关键算法的注释说明（如身份证号码校验算法）

3. **文档更新**
   - 同步版本号到 0.3.1
   - 更新 README.md 版本历史
   - 添加改进记录到 AGENTS.md
