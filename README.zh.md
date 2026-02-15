# 精灵图序列帧处理工具

用于处理精灵图（序列帧大图）的小工具：输入一张或多张包含 **M×N** 帧的大图，去底（纯色或 AI）后按网格切割成多张单帧图片。

## 功能说明

- **去底**：**纯色去底**（指定 `--bg` 与可选 `--tolerance`）或 **rembg AI 去底**（`--rembg`），复杂背景建议用 rembg。
- **按网格切割**：大图按 **M×N**（行×列）网格切割。一个数表示 **N×N**（如 `--grid 4`），两个数表示 **M×N**（如 `--grid 4 8`）。行优先顺序。
- **批量与通配**：可传入多个文件或 **通配符**（如 `raw/*.png`），同一套参数处理。
- **命令行**：可配置输入路径/通配、网格、去底方式、输出目录及预览 GIF。

## 环境要求

- **Python** 3.11+（rembg 需要；建议用项目 conda 环境）。
- **Pillow**（PIL）、**rembg** — 通过 `requirements.txt` 安装，或使用项目 **conda** 环境（推荐）。

## 环境：Conda（推荐）

项目使用 conda 环境，保证每次打开或运行项目时使用同一解释器。

**首次配置：**

```bash
conda env create -f environment.yml
```

**激活环境**（在运行项目的终端中执行；或在 Cursor 中依赖“选择 Python 解释器”/终端自动激活）：

```bash
conda activate process-frame-sheet
```

- **在 Cursor 中**：工作区已配置为使用 `process-frame-sheet` conda 环境，并在集成终端中自动激活。打开项目后直接运行即可。
- **不手动激活时**：可执行 `./run.sh` 代替 `python cli.py`，脚本会自动使用该 conda 环境。

## 使用方式

### 安装依赖（未使用 conda 时）

```bash
pip install -r requirements.txt
```

### 命令行示例

```bash
# 先激活 conda 环境（conda activate process-frame-sheet），然后：

# 纯色去底（需指定 --bg）
python cli.py sheet.png --grid 4 --bg "#FFFFFF" --output ./frames

# AI 去底（rembg），无需 --bg，效果通常更好
python cli.py sheet.png --grid 4 --rembg --output ./frames

# M×N 网格：4 行 8 列
python cli.py sheet.png --grid 4 8 --bg "#FFFFFF" --output ./frames

# 带容差（使用 --bg 时抗锯齿），0–255
python cli.py sheet.png --grid 4 --bg "#FFFFFF" --tolerance 10 --output ./frames

# 通配符：raw/ 下所有 PNG（通配符需加引号由脚本展开）
./run.sh "raw/*.png" --grid 4 -o ./frames --rembg

# 批量：多张图同一规格
python cli.py Idle.png Run.png Attack.png --grid 4 --rembg --output ./frames

# 可选：同时保存整张去底大图
python cli.py sheet.png --grid 4 --rembg --output ./frames --save-full
```

或使用包装脚本（无需先激活环境）：

```bash
./run.sh "raw/*.png" --grid 4 -o ./frames --rembg
./run.sh Idle.png Run.png --grid 4 --bg "#FFFFFF" --output ./frames
```

输出结构：每张输入图在输出目录下按 **原图文件名（无扩展名）** 生成子文件夹，帧图片命名为 **`原图名_序列号.png`**（如 `Idle_1.png`、`Idle_2.png` …），顺序为 **行优先**。同时在该文件夹内生成预览 **GIF**（如 `frames/Idle/Idle.gif`）。可通过 `--gif-duration` 设置每帧显示毫秒数（默认 100）。

示例：单张 `python cli.py Idle.png --grid 4 --rembg -o ./frames` → `frames/Idle/` 下帧图与 `Idle.gif`。通配 `./run.sh "raw/*.png" --grid 4 -o ./frames` 会展开 `raw/*.png` 并逐张处理。首次使用 `--rembg` 会下载模型，可能较慢。

## 项目结构

```text
ProcessFrameAnimationSheetImage/
├── README.md
├── README.zh.md
├── .cursor/
│   └── rules/
│       └── process-sprite-sheet.mdc
├── .vscode/
│   └── settings.json      # Python：process-frame-sheet conda 环境，终端自动激活
├── environment.yml        # Conda 环境定义（process-frame-sheet）
├── requirements.txt
├── run.sh                 # 使用 conda 环境运行 CLI（./run.sh ...）
├── src/
│   └── process_sheet.py   # 核心：去底 + 网格切割
└── cli.py                 # 命令行入口
```

- **输入**：文件路径（可多个）或 **通配符**（如 `raw/*.png`）。使用通配时在 shell 中加引号：`./run.sh "raw/*.png" --grid 4 -o ./frames`。
- **输出**：由 `--output` 指定根目录（如 `./frames`）。例如输入 `Idle.png` 时，帧与 GIF 写入 `frames/Idle/`：`Idle_1.png` … `Idle_N.png`、`Idle.gif`；使用 `--save-full` 时另存整张去底图为 `Idle_sheet.png`。

## 注意事项

- **去底**：**`--rembg`** 为 AI 去底（背景不纯时推荐），**`--bg HEX`** 为纯色去底，可配 **`--tolerance`**。
- **通配符**：输入可为通配（如 `raw/*.png`），需加引号让脚本接收并展开：`./run.sh "raw/*.png" --grid 4 -o ./frames`。
- **切割**：`--grid N` 为 N×N，`--grid R C` 为 R 行×C 列。帧顺序为 **行优先**。
- **输出格式**为 PNG。首次 `--rembg` 会下载模型；大批量注意内存。
