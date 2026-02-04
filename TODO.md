# 项目待办事项列表

## 当前阶段：已完成所有计划任务 ✅

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

**最后更新**: 2024-02-02
**当前负责人**: Sisyphus
**状态**: 所有计划任务已完成 ✅
