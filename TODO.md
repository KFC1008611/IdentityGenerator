# 项目待办事项列表

## 当前阶段：已完成所有计划任务 ✅

- [x] **testcov-1**: 补齐测试覆盖并清理测试告警 ✅
  - 基线采集：定位当前覆盖率缺口与 warning 来源（已完成）
  - 新增测试：`test_model_config.py`、`test_model_manager.py`、`test_cli_model_commands.py`、`test_china_data_edge_cases.py`
  - 扩展测试：`test_idcard_image_generator.py`（增加后端与辅助函数分支）
  - 全量验证：`pytest -W error` 通过，186 passed，0 warning
  - 覆盖率：总覆盖率提升至 83%

- [x] **testcov-100**: 持续补齐测试直至覆盖率 100% ✅
  - 新增/扩展测试：`test_generator_edge_cases.py`、`test_formatters_edge_cases.py`、`test_idcard_image_generator.py`、`test_cli_model_commands.py`、`test_model_config.py`、`test_model_manager.py`、`test_web.py`、`test_china_data_edge_cases.py`
  - 清理不可达防御分支并标注极端防御路径（最小化 `pragma: no cover`）
  - 全量验证：`pytest -W error` 通过，250 passed，0 warning
  - 覆盖率结果：TOTAL 100%

- [x] **web-download-1**: Web 移除 table 格式并增加下载按钮 ✅
  - Web 格式下拉不再提供 table
  - 生成结果新增下载按钮，按当前格式导出文件

- [x] **web-idcard-2**: Web 页面增加身份证图片特殊选项与生成方式选择 ✅
  - 新增身份证图片开关、头像生成方式下拉、输出目录输入
  - 生成后支持展示身份证图片文件路径预览
  - 增加对应 Web 测试并通过

- [x] **web-1**: 新增 Flask Web 图形界面并接入 `--server` 入口 ✅
  - 主命令新增 `--server` / `--server-host` / `--server-port` 选项
  - 新增字段多选、生成后预览、格式化结果展示能力
  - 补充 CLI 与 Web 路由测试，更新 README 使用说明

- [x] **id-1**: 为批量身份生成增加关键字段去重机制 ✅
  - 在 `generate_batch` 中对身份证号、手机号、邮箱、用户名、银行卡号等字段进行去重重试
  - 新增对应单元测试，验证批量生成关键字段唯一性

- [x] **fix-addr-1**: 修复身份证住址固定 11 字切分导致的异常换行 ✅
  - 改为按实际渲染宽度分行（最多两行），避免出现不自然断行

- [x] **fix-avatar-1**: 修复身份证头像方向、裁剪与尺寸不一致问题 ✅
  - 对外部图片读取增加 EXIF 方向矫正，避免头像歪斜
  - 调整头像缩放裁剪策略并统一前景归一化排版，减少头部被裁剪与大小不一

- [x] **test-idcard-1**: 增加身份证排版与头像归一化回归测试 ✅
  - 新增 tests/test_idcard_image_generator.py

- [x] **prompt-3**: 进一步优化提示词构图并同步个人信息增强差异 ✅

- [x] **prompt-2**: 优化提示词限定人物位置避免头部裁剪 ✅

- [x] **prompt-1**: 优化 Ark 头像提示词以避免内容拦截 ✅

- [x] **config-ark-2**: 写入 ARK_API_KEY 到本地配置（避免提交） ✅

- [x] **config-ark-1**: 更新 Ark 模型与 API 配置到 Doubao-Seedream-4.5 ✅

- [x] **bug-ark-1**: 定位 Ark 后端未生效的根因（响应结构/接口/回退逻辑） ✅
- [x] **bug-ark-2**: 修复 Ark 生成并确保不错误回退到 random_face ✅
- [x] **doc-ark-1**: 更新必要文档或配置提示（如有行为变化） ✅（无需额外文档）

- [x] **feat-1**: 接入火山方舟 SDK 进行头像生成（配置与客户端封装） ✅
- [x] **feat-2**: 按性别与年龄构建证件照提示词并接入生成流程 ✅
- [x] **doc-2**: 更新文档与示例配置说明（含 config.py.example） ✅

## 最新完成

- [x] **fix-test-formatter-1**: 修复 tabulate 参数兼容导致的测试失败 ✅
  - `format_table` 增加对 `maxcolwidths` 的兼容回退（旧版本 tabulate 不支持时自动降级）
  - 已通过 `tests/test_formatters.py`、`tests/test_formatters_extended.py` 与全量 `pytest`

- [x] **data-1**: 统一辅助生成 JSON 目录并清理散落数据 ✅
  - 将 `area_codes.json` 迁移到 `src/identity_gen/data/area_codes.json`
  - 新增 `geo_data.json` 承载省/市/区县/街道等地理基础数据
  - 新增 `generation_rules.json` 承载手机号/邮箱/车牌/社信码等生成规则
  - `china_data.py` / `generator.py` 改为从 JSON 加载规则，移除大量硬编码数据

- [x] **fix-2**: 修复抠图高光误删除问题 ✅
  - 调整透明背景算法避免人脸高光被抠掉

## 最新完成

- [x] **cli-3**: CLI 每次运行询问头像生成方式 ✅
  - 选择 AI 模型 / random_face / 备用剪影 / 不生成头像
  - 将选择传递到身份证头像生成流程

### 已完成功能（2024-02-02）

#### 高优先级
- [x] **test-1**: 测试 model_config 模块功能 ✅
  - 验证模型配置加载/保存 ✅
  - 测试模型列表获取 ✅
  - 测试模型下载状态检测 ✅

- [x] **test-2**: 测试 model_manager 模块功能 ✅
  - 验证模型下载功能 ✅
  - 测试管道加载 ✅
  - 测试图片生成功能 ✅

- [x] **test-3**: 测试 AvatarGenerator 多后端切换 ✅
  - 测试 auto 后端选择逻辑 ✅
  - 验证 fallback 机制 ✅
  - 确保 seed 控制正常工作 ✅

- [x] **test-4**: 测试 IDCardImageGenerator 集成 ✅
  - 完整身份证生成流程 ✅
  - 头像与身份证信息匹配 ✅
  - 输出图片验证 ✅

#### CLI 开发
- [x] **cli-1**: 编写 CLI 模型配置命令 ✅
  - 添加 `model configure` 子命令 ✅
  - 实现交互式模型选择 ✅
  - 自动下载确认 ✅

- [x] **cli-2**: 添加模型管理命令行工具 ✅
  - 添加 `model list` 命令 ✅
  - 添加 `model download` 命令 ✅
  - 添加 `model delete` 命令 ✅
  - 添加 `model status` 命令 ✅

#### 依赖和文档
- [x] **dep-1**: 更新 pyproject.toml 添加 diffusers 依赖 ✅
  - 添加 `diffusers>=0.21.0` ✅
  - 添加 `torch>=2.0.0` ✅
  - 添加 `huggingface-hub>=0.16.0` ✅
  - 添加 `accelerate>=0.20.0` ✅
  - 添加 `safetensors>=0.3.0` ✅

- [x] **doc-1**: 更新 README 使用文档 ✅
  - 添加 diffusers 安装说明 ✅
  - 添加模型配置教程 ✅
  - 更新 AI 模型管理命令文档 ✅

#### 用户反馈修复
- [x] **cleanup-1**: 清理 test_output 目录下的旧头像文件 ✅
  - 删除了遗留的卡通人脸图片 ✅

- [x] **fix-1**: 修复 random_face 生成的蓝色滤镜问题 ✅
  - 将 BGR 格式转换为 RGB 格式 ✅
  - 确保颜色通道顺序正确 ✅

- [x] **auto-config**: 实现零配置自动检测+交互式选择 ✅
  - 首次运行时自动检测模型 ✅
  - 自动弹出交互式模型选择菜单 ✅
  - 选择后自动下载并使用 ✅
  - 支持非交互模式自动选择推荐模型 ✅
  - 后续运行直接调用已下载模型 ✅

## 核心模块完成状态

### 2024-02-02
- [x] **完成**: 创建 model_config.py 模块
  - 支持多模型配置（tiny-sd, small-sd, realistic-vision）
  - 自动下载检测
  - 配置持久化到 ~/.identity_gen/

- [x] **完成**: 创建 model_manager.py 模块
  - 模型下载管理（从 Hugging Face）
  - 管道缓存
  - 图片生成功能

- [x] **完成**: 重构 idcard_image_generator.py
  - 集成 diffusers 支持（零配置自动检测）
  - 保持 random_face 兼容（修复蓝色滤镜）
  - 实现三级 fallback 机制（diffusers → random_face → silhouette）

## 技术债务

- [ ] 考虑添加模型版本管理
- [ ] 优化模型缓存策略
- [ ] 添加生成进度显示
- [ ] 支持更多模型格式（如 Safetensors）

---

**最后更新**: 2026-02-06
**当前负责人**: Sisyphus
**状态**: 所有计划任务已完成 ✅
