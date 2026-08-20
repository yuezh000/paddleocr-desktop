# PaddleOCR 病历识别桌面版

面向 Windows 与 macOS 的 PyQt6 桌面程序。安装包包含 Python 解释器和全部运行依赖，使用者无需安装 Python、Docker 或命令行工具。

## 已实现

- 拖放或鼠标选择 PNG、JPEG、BMP、TIFF、WebP 图片；
- 左侧原图与检测框、右侧识别文字/置信度/坐标对照；
- 点击右侧某行，会在原图中高亮对应区域；
- OCR 在后台线程运行，模型加载和推理不会卡死界面；
- 中文 PP-OCRv5，使用 PaddleOCR 官方 `onnxruntime` 推理引擎；
- 复制全文，导出 UTF-8 TXT 或含坐标与置信度的 JSON；
- 自动应用 EXIF 方向；超大图片等比缩至最长边 3800 像素，再把检测框映射回原图坐标。

> PaddleOCR 的 `max_side_limit` 为 4000。程序预留 200 像素安全余量，因而不会再出现 `Resized image size ... exceeds max_side_limit of 4000`。图片只在本机处理；临时推理图片用完即删除。

## 开发运行

推荐 Python 3.11。首次识别会从百度 BOS 下载官方模型并保存在当前用户的 PaddleX 缓存中。

```bash
python3.11 -m venv .venv
source .venv/bin/activate        # Windows: .venv\Scripts\activate
python -m pip install -e .
paddleocr-desktop
```

## 构建可安装软件

PyInstaller 不能跨系统构建：Windows 安装包必须在 Windows 上生成，macOS DMG 必须在 macOS 上生成。构建机需要 Python 3.11；最终安装软件不需要 Python。

### Windows 10/11 x64

安装 Python 3.11 与 Inno Setup 6，然后在 PowerShell 运行：

```powershell
powershell -ExecutionPolicy Bypass -File scripts/build-windows.ps1
```

结果：`dist-installer/PaddleOCR-Medical-Setup-0.1.0-x64.exe`。

### macOS

安装 Python 3.11 与 `create-dmg`（`brew install create-dmg`）后运行：

```bash
bash scripts/build-macos.sh
```

结果：`dist-installer/PaddleOCR-Medical-0.1.0.dmg`。Apple Silicon 与 Intel 版本需分别在相应架构的 macOS 构建。公开分发前应使用 Apple Developer ID 签名并公证；未签名版本可用于内部测试，但 Gatekeeper 会提示风险。

### 自动构建

仓库内的 GitHub Actions 工作流支持手动触发或推送 `v*` 标签，分别输出 Windows、Apple Silicon macOS、Intel macOS 三个构建产物。

## 模型与离线部署

安装包包含完整桌面运行环境，但为了控制安装包体积，OCR 模型默认在第一次识别时下载。完成一次识别后，模型会留在用户缓存中，后续可离线运行。若需要完全离线的首启安装包，可在目标构建机先下载模型，再把模型目录作为 PyInstaller data 一并封装。

## 医疗数据提示

OCR 结果应由专业人员复核，不应直接作为诊断或处方依据。图片清晰度、裁剪、倾斜、压缩和表格布局都会影响准确率。
