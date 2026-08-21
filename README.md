# PaddleOCR Desktop

面向 Windows 与 macOS 的离线 OCR 桌面程序。使用者可以打开或拖入图片，在原图检测框旁逐行核对识别文字、置信度和坐标。安装包包含 Python 解释器、运行依赖以及 PP-OCRv5 Mobile ONNX 权重，不需要安装 Python、Docker，也不需要在首次运行时下载模型。

界面使用 LGPLv3 授权的 PySide6/Qt 动态库。安装包保留独立 Qt 库，并附带第三方声明及 LGPL/GPL 许可证文本，详见 `THIRD_PARTY_NOTICES.md`。

## 版本说明（0.1.0）

本版本提供面向 Windows 和 macOS 的完整离线 OCR 工作流：使用 PySide6 构建桌面界面，安装包内置 PP-OCRv5 Mobile 检测与识别权重，首次启动无需连接任何模型服务。程序支持识别任务取消、任意时刻关闭、右侧加载状态，以及诊断日志复制、导出和目录访问，适合在普通用户环境中部署、核对结果和定位问题。

## 功能

- 拖放或鼠标选择 PNG、JPEG、BMP、TIFF、WebP 图片；
- 左侧原图与检测框、右侧识别文字/置信度/坐标对照；
- 点击右侧某行，会在原图中高亮对应区域；
- OCR 在后台线程运行，模型加载和推理期间界面仍可操作；
- 识别过程中可点击“取消任务”；任务会在当前推理步骤结束后安全停止；
- 窗口可随时关闭；即使模型正在加载或推理也不会阻止退出；
- 安装包包含 PaddleX 所需的运行时依赖元数据；
- “日志”菜单可随时复制诊断信息、导出 ZIP 日志包或打开日志目录；日志自动轮转且不主动记录 OCR 文本；
- 安装包内置中文 PP-OCRv5 Mobile 检测与识别权重，使用 PaddleOCR 的 `onnxruntime` 推理引擎；
- 复制全文，导出 UTF-8 TXT 或含坐标与置信度的 JSON；
- 自动应用 EXIF 方向；超大图片等比缩至最长边 3800 像素，再把检测框映射回原图坐标；
- 应用窗口、Windows 安装程序和 macOS 应用包使用统一的 OCR 图标。

> PaddleOCR 的 `max_side_limit` 为 4000。程序预留 200 像素安全余量，因而不会再出现 `Resized image size ... exceeds max_side_limit of 4000`。图片只在本机处理；临时推理图片用完即删除。

## 使用方法

1. 点击“打开图片”，或把图片拖入窗口；
2. 点击“开始识别”；
3. 在右侧选择识别行，左侧会高亮相应检测框；
4. 复制全文，或导出 TXT/JSON 结果。

识别任务运行期间可以点击“取消任务”。该操作会在当前原生推理步骤返回后安全停止；如果希望立即退出，可以直接关闭窗口。

## 模型与离线运行

程序使用 PaddleOCR 3.x 管线和 ONNX Runtime，显式加载安装包内的以下模型：

- `PP-OCRv5_mobile_det_onnx`：文字区域检测；
- `PP-OCRv5_mobile_rec_onnx`：中英文文字识别。

模型总大小约 21 MB，位于 `assets/models/`。`assets/models/SHA256SUMS` 记录了四个模型及配置文件的校验值。运行时不会访问 Hugging Face、ModelScope、AIStudio 或 BOS；Windows 和 macOS 使用相同权重。

## 日志与故障反馈

“日志”菜单提供三项操作：

- “复制诊断信息”：复制系统、依赖版本和最近日志；
- “导出日志包”：生成包含系统信息及轮转日志的 ZIP；
- “打开日志目录”：直接打开持久化日志文件所在文件夹。

默认日志位置：

- Windows：`%LOCALAPPDATA%\AtomNLP\PaddleOCR Desktop\logs\paddleocr-desktop.log`；
- macOS：`~/Library/Application Support/AtomNLP/PaddleOCR Desktop/logs/paddleocr-desktop.log`。

日志自动轮转，不主动记录 OCR 识别文字。程序异常时，请优先导出日志包；如果弹窗仍可操作，也可以点击“复制完整日志”。

## 开发运行

推荐 Python 3.12。PP-OCRv5 Mobile ONNX 检测与识别模型已经随项目和安装包分发，首次识别不会访问 Hugging Face、ModelScope、AIStudio 或 BOS，可直接离线运行。

```bash
python3.12 -m venv .venv
source .venv/bin/activate        # Windows: .venv\Scripts\activate
python -m pip install -e .
paddleocr-desktop
```

运行测试：

```bash
python -m pip install pytest
python -m pytest
```

## 构建可安装软件

PyInstaller 不能跨系统构建：Windows 安装包必须在 Windows 上生成，macOS DMG 必须在 macOS 上生成。构建机使用 Python 3.12；最终安装软件不需要 Python。

### Windows 10/11 x64

安装 Python 3.12 与 Inno Setup 6，然后在 PowerShell 运行：

```powershell
winget install --id Python.Python.3.12 -e
winget install --id JRSoftware.InnoSetup -e
```

关闭并重新打开 PowerShell，在项目目录运行：

```powershell
powershell -ExecutionPolicy Bypass -File scripts/build-windows.ps1
```

结果：`dist-installer/PaddleOCR-Desktop-Setup-0.1.0-x64.exe`。构建脚本会运行测试、生成应用图标，并将内置模型加入安装目录。若 Inno Setup 未安装可选的 `ChineseSimplified.isl`，脚本会自动使用内置英文安装界面，不会中断安装包生成。

### macOS

安装 Python 3.12 与 Homebrew 版 `create-dmg/create-dmg` 后运行：

```bash
brew install python@3.12 create-dmg
```

不要使用 `npm install -g create-dmg` 安装的同名工具；它的命令参数不同。构建脚本通过 PATH 调用 `create-dmg`，并在构建前验证当前命令是否为兼容的 1.x 版本，然后运行：

```bash
bash scripts/build-macos.sh
```

构建脚本统一从官方 `https://pypi.org/simple` 安装构建依赖。

结果：`dist-installer/PaddleOCR-Desktop-0.1.0.dmg`。双击后会打开 Finder 安装窗口，以 128px 大图标展示应用和 Applications 快捷入口，可将应用拖到 Applications 完成安装。构建脚本会运行测试、生成 `.icns` 图标、制作 DMG，并挂载成品校验应用、Applications 链接和 Finder 布局数据。Apple Silicon 与 Intel 版本需分别在相应架构的 macOS 构建。公开分发前应使用 Apple Developer ID 签名并公证；未签名版本可用于内部测试，但 Gatekeeper 会提示风险。

### 自动构建

仓库内的 GitHub Actions 工作流支持手动触发或推送 `v*` 标签，分别输出 Windows、Apple Silicon macOS、Intel macOS 三个构建产物。

## 技术栈与授权

- GUI：PySide6 / Qt 6；
- OCR：PaddleOCR 3.x / PaddleX；
- 推理：ONNX Runtime CPU；
- 打包：PyInstaller；
- Windows 安装器：Inno Setup 6；
- macOS 安装器：`create-dmg`。

界面使用 LGPLv3 授权的 PySide6。安装目录保留独立 Qt 动态库，并随包提供 LGPL/GPL 正文。PP-OCRv5 模型及 PaddleOCR 的 Apache 2.0 许可证也随包分发。完整声明见 `THIRD_PARTY_NOTICES.md` 和 `licenses/`。

## 使用提示

OCR 结果可能存在漏字、错字或版面关系错误。图片清晰度、裁剪、倾斜、压缩和复杂布局都会影响准确率，重要内容请对照原图复核。
