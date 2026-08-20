# PaddleOCR Desktop

面向 Windows 与 macOS 的 PySide6 桌面程序。安装包包含 Python 解释器和全部运行依赖，使用者无需安装 Python、Docker 或命令行工具。

界面使用 LGPLv3 授权的 PySide6/Qt 动态库。安装包保留独立 Qt 库，并附带第三方声明及 LGPL/GPL 许可证文本，详见 `THIRD_PARTY_NOTICES.md`。

## 已实现

- 拖放或鼠标选择 PNG、JPEG、BMP、TIFF、WebP 图片；
- 左侧原图与检测框、右侧识别文字/置信度/坐标对照；
- 点击右侧某行，会在原图中高亮对应区域；
- OCR 在后台线程运行，模型加载和推理不会卡死界面；
- 识别过程中可点击“取消任务”；任务会在当前推理步骤结束后安全停止；
- 窗口可随时关闭；即使模型正在下载或推理也不会阻止退出；
- 打包时按 PaddleX 官方规范收集运行时依赖元数据，避免安装版误报缺少 OCR 依赖；
- “日志”菜单可随时复制诊断信息、导出 ZIP 日志包或打开日志目录；日志自动轮转且不主动记录 OCR 文本；
- 安装包内置中文 PP-OCRv5 Mobile 检测与识别权重，使用 PaddleOCR 的 `onnxruntime` 推理引擎；
- 复制全文，导出 UTF-8 TXT 或含坐标与置信度的 JSON；
- 自动应用 EXIF 方向；超大图片等比缩至最长边 3800 像素，再把检测框映射回原图坐标。
- 应用窗口、Windows 安装程序和 macOS 应用包使用统一的 OCR 图标。

> PaddleOCR 的 `max_side_limit` 为 4000。程序预留 200 像素安全余量，因而不会再出现 `Resized image size ... exceeds max_side_limit of 4000`。图片只在本机处理；临时推理图片用完即删除。

## 开发运行

推荐 Python 3.12。PP-OCRv5 Mobile ONNX 检测与识别模型已经随项目和安装包分发，首次识别不会访问 Hugging Face、ModelScope、AIStudio 或 BOS，可直接离线运行。

```bash
python3.12 -m venv .venv
source .venv/bin/activate        # Windows: .venv\Scripts\activate
python -m pip install -e .
paddleocr-desktop
```

## 构建可安装软件

PyInstaller 不能跨系统构建：Windows 安装包必须在 Windows 上生成，macOS DMG 必须在 macOS 上生成。构建机使用 Python 3.12；最终安装软件不需要 Python。

### Windows 10/11 x64

安装 Python 3.12 与 Inno Setup 6，然后在 PowerShell 运行：

```powershell
powershell -ExecutionPolicy Bypass -File scripts/build-windows.ps1
```

结果：`dist-installer/PaddleOCR-Desktop-Setup-0.1.0-x64.exe`。
若 Inno Setup 未安装可选的 `ChineseSimplified.isl`，构建脚本会自动使用内置英文安装界面，不会中断安装包生成。

### macOS

安装 Python 3.12 与 Homebrew 版 `create-dmg/create-dmg` 后运行：

```bash
brew install python@3.12 create-dmg
```

不要使用 `npm install -g create-dmg` 安装的同名工具；它的命令参数不同。构建脚本通过 PATH 调用 `create-dmg`，并在构建前验证当前命令是否为兼容的 1.x 版本，然后运行：

```bash
bash scripts/build-macos.sh
```

构建脚本会忽略用户目录中失效或配置错误的 pip 镜像，统一从官方
`https://pypi.org/simple` 安装构建依赖。若此前因镜像返回 403 而失败，直接重新运行脚本即可。

结果：`dist-installer/PaddleOCR-Desktop-0.1.0.dmg`。双击后会打开 Finder 安装窗口，以 128px 大图标展示应用和 Applications 快捷入口，可将应用拖到 Applications 完成安装。构建脚本会自动挂载成品，校验应用、Applications 链接和 Finder 布局数据，然后卸载测试卷。Apple Silicon 与 Intel 版本需分别在相应架构的 macOS 构建。公开分发前应使用 Apple Developer ID 签名并公证；未签名版本可用于内部测试，但 Gatekeeper 会提示风险。

### 自动构建

仓库内的 GitHub Actions 工作流支持手动触发或推送 `v*` 标签，分别输出 Windows、Apple Silicon macOS、Intel macOS 三个构建产物。

## 模型与离线部署

安装包包含完整桌面运行环境和约 21 MB 的 PP-OCRv5 Mobile ONNX 权重，首次启动无需下载模型。

## 使用提示

OCR 结果可能存在漏字、错字或版面关系错误。图片清晰度、裁剪、倾斜、压缩和复杂布局都会影响准确率，重要内容请对照原图复核。
