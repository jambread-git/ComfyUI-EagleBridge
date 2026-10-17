# ComfyUI-EagleBridge

**Languages:** [English](README.md) · [简体中文](README.zh-CN.md) · [한국어](README.ko.md) · [日本語](README.ja.md)

---

## 功能简介

ComfyUI-EagleBridge 提供三个输出节点，可将 ComfyUI 生成的**图片、音频和视频**保存后直接登记到 Eagle 素材库：

- **Eagle Save Image** — 保存 `IMAGE`，发送到 Eagle，并可显示图片预览。
- **Eagle Save Audio** — 保存 `AUDIO`，发送到 Eagle，并可显示带进度条的音频播放器。
- **Eagle Save Video** — 保存 ComfyUI 原生 `VIDEO`，发送到 Eagle，并可显示带进度条的视频播放器。

插件还会尽量从上游工作流中提取生成信息，并写入 Eagle 的标签和注释。

> 非官方社区项目，与 Comfy Org 或 Eagle 官方无隶属或背书关系。

## 环境要求

- 较新的 ComfyUI 版本。
- Eagle 桌面版与 ComfyUI 运行在同一台电脑上。
- 执行节点时，Eagle 必须已启动并打开一个素材库。
- Eagle 本地 API 使用默认地址 `127.0.0.1:41595`。
- Python 依赖：`requests>=2.31.0`。
- 音频/视频编码能力取决于当前 ComfyUI 环境中的 PyAV、FFmpeg 和可用编解码器。

## 安装方法

1. 关闭 ComfyUI。
2. 将 `ComfyUI-EagleBridge` 文件夹复制到 `ComfyUI/custom_nodes/`。
3. 在 ComfyUI 使用的同一个 Python 环境中安装依赖：

   ```bash
   pip install -r ComfyUI/custom_nodes/ComfyUI-EagleBridge/requirements.txt
   ```

4. 启动 Eagle 并打开目标素材库。
5. 启动 ComfyUI。
6. 更新插件后如果界面仍是旧状态，请使用 `Ctrl+Shift+R` 强制刷新浏览器，并重新添加节点。

## Eagle 目标文件夹 ID

每个 Save 节点都使用 `eagle_folder_id` 文本输入框。

1. 在 Eagle 中右键点击要保存到的文件夹，然后选择 **复制链接 / Copy Link**。
2. 复制出来的链接类似：

   ```text
   http://localhost:41595/folder?id=MU2LXTTH4KVRF
   ```

3. 只复制 `id=` 后面的值，例如 `MU2LXTTH4KVRF`，然后粘贴到 `eagle_folder_id`。
4. `eagle_folder_id` 留空时保存到 **Eagle Library Root**。

文件夹 ID 会直接保存在工作流中。

## 记录运行时生成的提示词（`prompt_text`）

保存节点通常从工作流图中读取提示词文本（如 `CLIPTextEncode`）。
但有些节点只在运行时生成提示词——例如 `MOSSImageLayoutPrompt`
根据布局元素合成提示词——图中不存在字面文本，无法自动提取。

这类工作流请使用各保存节点新增的可选输入插口 `prompt`
（内部键名为 `prompt_text`，只有连接插口，没有文本框）：

1. 将生成提示词的节点的 STRING 输出（如 `MOSSImageLayoutPrompt` 的
   `prompt` 输出）连接到 `prompt_text`。
2. 连接的文本会作为正向提示词（音频/视频为 Prompt）写入 Eagle 备注，
   并覆盖自动提取结果。

普通工作流不连接 `prompt_text` 即可，行为完全不变。

## 通用文件名与子文件夹模板

### `file_name_template`

默认：`%datetime%_%rand%`

支持：

- `%date%` → `YYYYMMDD`
- `%time%` → `HHMMSS`
- `%datetime%` → `YYYYMMDD_HHMMSS`
- `%index%` → 批次序号
- `%rand%` → 短随机 ID

例如：`20260915_203128_ab12cd34.webp`

### `local_subfolder`

支持：

- `%date%` → `YYYY-MM-DD`
- `%time%` → `HH-MM-SS`
- `%datetime%` → `YYYY-MM-DD_HH-MM-SS`
- `%model%` → 首个检测到的模型名；检测失败时为 `UnknownModel`

生成目录始终限制在 ComfyUI 的 output/temp 目录内部。

## Eagle Save Image 使用说明

将任意 `IMAGE` 输出直接连接到 `image`。它本身就是输出节点，因此不需要再连接标准 Save Image。

### 主要选项

- **image** — ComfyUI `IMAGE`。
- **eagle_folder_id** — Eagle 目标文件夹。
- **file_name_template** — 文件名模板。
- **local_subfolder** — 本地保存子目录，默认 `EagleBridge/Image/%date%/`。
- **format** — `webp` / `png` / `jpg`。
- **quality** — 1–100，默认 95，用于有损 WebP/JPEG。
- **lossless_webp** — 开启后以无损 WebP 保存。
- **save_local_copy** — 开启时保留在 ComfyUI output；关闭时使用临时文件供 Eagle 导入。
- **preview** — 在节点中显示保存后的图片。
- **memo** — 可选备注，以 `Memo:` 追加到 Eagle 注释。
- **website** — 可选网址，保存到 Eagle 的 Website 字段。

### Eagle 注释

可获取时按以下顺序写入：Positive Prompt、Negative Prompt、Model、Size、Seed、Steps、CFG、Sampler、Scheduler、Memo。无法获取的项目会自动省略。Eagle 标签只使用首个检测到的模型名。

### 文件内元数据

- PNG：在 ComfyUI 允许保存元数据时嵌入 prompt/workflow 信息。
- WebP：在允许保存元数据时嵌入 ComfyUI 风格 EXIF 信息。
- JPEG：当前插件不会嵌入工作流元数据。

## Eagle Save Audio 使用说明

将 `AUDIO` 输出直接连接到 `audio`。节点会原样透传 `AUDIO` 输出，便于继续连接后续节点。

### 主要选项

- **format** — `wav` / `flac` / `mp3` / `opus`。
- **bitrate** — `64k`～`320k`。仅 MP3/Opus 使用；WAV/FLAC 为无损格式，会忽略此项。
- **local_subfolder** — 默认 `EagleBridge/Audio/%date%/`。
- **save_local_copy** — 是否保留本地输出文件。
- **preview** — 显示可播放、暂停和拖动进度的音频播放器。
- **memo / website** — 写入 Eagle 的备注/网址字段。

### Prompt 与歌词自动提取

Prompt 会尝试从 `caption`、`prompt`、`tags`、`sample_query`、`description` 等字段中寻找；歌词会从 `lyrics`、`lyric` 中寻找。因此适合 ACE-Step 风格音乐工作流及采用类似字段名的自定义节点。

典型 Eagle 注释：

```text
Prompt:
...

Lyrics:
...

Model: ...
Duration: 30 sec
Sample Rate: 48000 Hz
Channels: 2

Memo:
...
```

时长会自动进行便于阅读的四舍五入。WAV 使用 16-bit PCM。Opus 在必要时会尝试使用 `torchaudio` 进行采样率转换。音频容器本身目前不会嵌入完整 ComfyUI 工作流，生成信息主要保存于 Eagle 注释/标签中。

## Eagle Save Video 使用说明

将 ComfyUI 原生 `VIDEO` 输出直接连接到 `video`。节点会透传原始 `VIDEO`，并可直接作为工作流中的输出保存节点使用。

### 主要选项

- **format** — `mp4` / `webm` / `mkv`。
- **codec** — `auto` / `h264` / `av1`。
- **local_subfolder** — 默认 `EagleBridge/Video/%date%/`。
- **save_local_copy** — 是否保留本地视频。
- **preview** — 显示带播放/暂停和进度条的视频播放器。
- **memo / website** — 写入 Eagle 的备注/网址字段。

`webm + h264` 会被拒绝。实际可用的编码器仍取决于 ComfyUI/PyAV/FFmpeg 环境。

### Prompt 与主视频模型识别

视频工作流未必经过标准图片 KSampler 的文本路径，因此节点还会搜索 `prompt`、`positive_prompt`、`positive_text`、`prompt_text`、`text_prompt`、`caption`、`description`、`text` 等常见字段，并在存在时尝试获取 Negative Prompt。

模型方面会优先选出**主要视频生成模型**，并降低 VAE、Qwen/CLIP/T5 文本编码器、LoRA 等辅助组件的优先级。对于 MiniMax H3、Wan、LTX 等包含多个模型文件的工作流，可减少 Eagle 中 `Model:` 出现一长串辅助模型的问题。

典型 Eagle 注释：

```text
Prompt:
...

Model: ...
Size: 960x544
Duration: 5.17 sec
FPS: 24
```

若能获取 Seed、Steps、CFG、Sampler、Scheduler 等信息也会追加。Duration/FPS 会自动简化显示。

## 常见问题

- **不知道 folder ID：** 在 Eagle 中右键点击目标文件夹，选择 **复制链接 / Copy Link**。例如 `http://localhost:41595/folder?id=MU2LXTTH4KVRF`，将 `id=` 后面的 `MU2LXTTH4KVRF` 粘贴到 `eagle_folder_id`。
- **更新后播放器不显示：** 重启 ComfyUI，使用 `Ctrl+Shift+R`，并删除后重新添加节点。
- **文件名不同但 Eagle 提示重复：** Eagle 可根据文件内容判断重复，与文件名无关。
- **MP3/Opus/视频编码失败：** 请检查当前 ComfyUI 环境的 PyAV/FFmpeg/codec 支持。
- **Prompt/Model 没有显示：** 自动提取属于尽力识别；某些自定义工作流可能使用尚未支持的字段名或连接结构。
- **远程访问安全：** 这些节点会让 ComfyUI 后端写入本地文件并调用 Eagle 本地 API。请勿将可执行工作流的 ComfyUI 实例暴露给不可信用户。

## 许可证

GNU General Public License v3.0。详见 `LICENSE`。

---

