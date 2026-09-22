# ComfyUI-EagleBridge

![Version](https://img.shields.io/badge/version-1.2.1-2ea44f?style=flat-square)
![License](https://img.shields.io/badge/license-GPL--3.0-blue?style=flat-square)
![ComfyUI](https://img.shields.io/badge/ComfyUI-custom%20nodes-6f42c1?style=flat-square)

ComfyUI-EagleBridge adds three output nodes that save generated **images, audio, and video** from ComfyUI and register them directly in an **Eagle** library.

Published on the **Comfy Registry** as `eagle-bridge`, so it can be discovered and installed from **ComfyUI Manager**.


> Unofficial community project. This project is not affiliated with or endorsed by Comfy Org or Eagle.

**Languages:** [English](#english) · [简体中文](#简体中文) · [한국어](#한국어) · [日本語](#日本語)

---

# English

## What this extension does

ComfyUI-EagleBridge provides three Eagle save nodes, plus the bundled Video Preview utility node:

- **Eagle Save Image** — saves an `IMAGE`, sends it to Eagle, can show an image preview, and passes the original `IMAGE` through its output.
- **Eagle Save Audio** — saves an `AUDIO`, sends it to Eagle, and can show an audio player with a seek bar.
- **Eagle Save Video** — saves a native ComfyUI `VIDEO`, sends it to Eagle, and can show a video player with a seek bar.

The extension also tries to extract useful generation metadata from the upstream workflow and writes it into Eagle as tags/annotations.

## Requirements

- A recent ComfyUI installation.
- Eagle desktop application running on the same computer.
- An Eagle library must be open while the nodes are executed.
- Eagle's local API must be available at the default address `127.0.0.1:41595`.
- Eagle API requests do not use an application-level timeout; a save waits for Eagle to respond.
- Python dependency: `requests>=2.31.0`.
- Audio/video encoding support depends on the PyAV/FFmpeg/codec support available in your ComfyUI environment.

## Installation

**ComfyUI Manager:** search for `ComfyUI-EagleBridge` or `eagle-bridge` and install it directly.

**Manual installation:**

1. Stop ComfyUI.
2. Copy the `ComfyUI-EagleBridge` folder into `ComfyUI/custom_nodes/`.
3. Install the requirements in the same Python environment used by ComfyUI:

   ```bash
   pip install -r ComfyUI/custom_nodes/ComfyUI-EagleBridge/requirements.txt
   ```

4. Start Eagle and open the library you want to use.
5. Start ComfyUI.
6. If the UI looks stale after updating the extension, hard-refresh the browser (`Ctrl+Shift+R`) and re-add the node.

## Eagle destination folder ID

Every Save node contains an `eagle_folder_id` text field.

1. In Eagle, right-click the folder you want to save into and choose **Copy Link**.
2. The copied link will look like this:

   ```text
   http://localhost:41595/folder?id=MU2LXTTH4KVRF
   ```

3. Copy only the value after `id=` — in this example, `MU2LXTTH4KVRF` — and paste it into `eagle_folder_id`.
4. Leave `eagle_folder_id` blank to save to **Eagle Library Root**.

The folder ID is stored directly in the workflow.

## Common filename and folder templates

### `file_name_template`

Default:

```text
%datetime%_%rand%
```

Supported tokens:

- `%date%` → `YYYYMMDD`
- `%time%` → `HHMMSS`
- `%datetime%` → `YYYYMMDD_HHMMSS`
- `%index%` → batch index
- `%rand%` → short random ID

Example filename:

```text
20260915_203128_ab12cd34.webp
```

### `local_subfolder`

Supported tokens:

- `%date%` → `YYYY-MM-DD`
- `%time%` → `HH-MM-SS`
- `%datetime%` → `YYYY-MM-DD_HH-MM-SS`
- `%model%` → first detected model name, or `UnknownModel` if no model can be detected

The folder is always kept inside ComfyUI's output/temp directory.

## Eagle Save Image

### How to connect it

Connect any ComfyUI `IMAGE` output directly to the `image` input. The node also passes the original `IMAGE` through its right-side output so it can continue into downstream nodes. It remains an output node, so you do not need a separate standard Save Image node just to save to Eagle.

### Inputs

- **image** — ComfyUI `IMAGE` input. The original value is passed through as the node's `IMAGE` output.
- **eagle_folder_id** — Eagle destination folder.
- **file_name_template** — output filename template.
- **local_subfolder** — local ComfyUI output subfolder. Default: `EagleBridge/Image/%date%/`.
- **format** — `webp`, `png`, or `jpg`.
- **quality** — 1–100. Used for lossy WebP/JPEG. Default: 95.
- **lossless_webp** — when enabled, WebP is saved losslessly and `quality` is not used as the lossy quality setting.
- **save_local_copy** — when enabled, keep the file in ComfyUI output. When disabled, a temporary file is used so Eagle can import it.
- **preview** — show the saved image in the ComfyUI node UI.
- **memo** — optional personal note appended to the Eagle annotation under `Memo:`.
- **website** — optional URL stored in Eagle's website field.

### Eagle metadata

When available, the annotation is written in this order:

```text
Positive Prompt:
...

Negative Prompt:
...

Model: ...
Size: ...
Seed: ...
Steps: ...
CFG: ...
Sampler: ...
Scheduler: ...

Memo:
...
```

Unavailable fields are omitted. Eagle tags use the first detected model name only.

### Embedded metadata

- **PNG**: ComfyUI prompt/workflow metadata is embedded when ComfyUI metadata saving is enabled.
- **WebP**: ComfyUI-style EXIF metadata is embedded when metadata saving is enabled.
- **JPEG**: workflow metadata is currently not embedded by this extension.

## Eagle Save Audio

### How to connect it

Connect a ComfyUI `AUDIO` output directly to `audio`. The node passes the original `AUDIO` through its output, so it can remain part of a larger workflow.

### Inputs

- **audio** — ComfyUI `AUDIO` input.
- **eagle_folder_id** — Eagle destination folder.
- **file_name_template** — output filename template.
- **local_subfolder** — default: `EagleBridge/Audio/%date%/`.
- **format** — `wav`, `flac`, `mp3`, or `opus`.
- **bitrate** — `64k`, `96k`, `128k`, `192k`, `256k`, or `320k`. Used by MP3/Opus. WAV and FLAC are lossless and ignore this setting.
- **save_local_copy** — keep the encoded audio in ComfyUI output, or use a temporary file when disabled.
- **preview** — show the built-in HTML5 audio player with play/pause and seek controls.
- **memo** — appended to Eagle annotation under `Memo:`.
- **website** — optional Eagle website URL.

### Prompt and lyrics extraction

For audio/music workflows, the node searches upstream inputs for prompt-like fields including:

`caption`, `prompt`, `tags`, `sample_query`, `description`

Lyrics are searched from:

`lyrics`, `lyric`

This makes the node useful with ACE-Step-style music workflows and other nodes that use similar field names. If a field cannot be found, it is simply omitted.

### Eagle metadata

Typical annotation:

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

Duration is rounded for readability. Eagle tags use the first detected model name.

### Notes

- WAV is written as 16-bit PCM.
- Opus may require sample-rate conversion; the extension uses `torchaudio` when conversion is needed and available.
- Audio files do **not** currently receive embedded ComfyUI workflow metadata inside the audio container; generation details are stored in Eagle annotations/tags.

## Eagle Save Video

### How to connect it

Connect a native ComfyUI `VIDEO` output directly to `video`. This is intended for current ComfyUI video workflows that expose the native `VIDEO` socket. The node passes the original `VIDEO` through its output.

### Inputs

- **video** — native ComfyUI `VIDEO` input.
- **eagle_folder_id** — Eagle destination folder.
- **file_name_template** — output filename template.
- **local_subfolder** — default: `EagleBridge/Video/%date%/`.
- **format** — `mp4`, `webm`, or `mkv`.
- **codec** — `auto`, `h264`, or `av1`.
- **save_local_copy** — keep the encoded video in ComfyUI output, or use a temporary file when disabled.
- **preview** — show an in-node video player with play/pause and seek controls.
- **memo** — appended to Eagle annotation under `Memo:`.
- **website** — optional Eagle website URL.

### Codec note

`webm + h264` is rejected because that combination is not supported by this node. Actual codec availability also depends on the ComfyUI/PyAV/FFmpeg environment.

### Prompt and primary-model extraction

Video workflows often do not use the same text-conditioning path as a standard image KSampler. The node therefore searches common upstream fields such as:

`prompt`, `positive_prompt`, `positive_text`, `prompt_text`, `text_prompt`, `caption`, `description`, `text`

It also looks for negative-prompt fields when available.

For the model name, the node tries to select the **primary video generation model** and demote support components such as VAE, Qwen/CLIP/T5 text encoders, and LoRAs. This is useful for workflows such as MiniMax H3, Wan, and LTX where several model-like files may be present upstream.

### Eagle metadata

Typical annotation:

```text
Prompt:
...

Negative Prompt:
...

Model: ...
Size: 960x544
Duration: 5.17 sec
FPS: 24
Seed: ...
Steps: ...
CFG: ...
Sampler: ...
Scheduler: ...

Memo:
...
```

Unavailable fields are omitted. Duration and FPS are rounded for readability. Eagle tags contain the selected primary model name.

### Embedded workflow metadata

The node passes ComfyUI prompt/extra metadata to ComfyUI's native `VIDEO.save_to()` API when metadata saving is enabled. Whether/how this is embedded depends on the selected container, codec, and ComfyUI implementation.

## Troubleshooting

- **Player/preview does not appear after updating:** restart ComfyUI, hard-refresh the browser (`Ctrl+Shift+R`), then remove and re-add the node.
- **Eagle says a file is duplicated although the filename changed:** Eagle can detect identical file content independently of the filename. Generate different content (for example, change the seed) to test.
- **MP3/Opus/video encoding fails:** codec support depends on the PyAV/FFmpeg stack in the ComfyUI environment.
- **Prompt/model is missing:** metadata extraction is best-effort. Custom workflows may use field names or graph structures not currently recognized.
- **Remote ComfyUI warning:** these nodes can cause ComfyUI's backend to write local files and send their paths to Eagle's local API. Be careful when exposing ComfyUI to untrusted remote users.

## License

GNU General Public License v3.0. See `LICENSE`.

---

# 简体中文

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

# 한국어

## 개요

ComfyUI-EagleBridge는 ComfyUI에서 생성한 **이미지, 오디오, 비디오**를 저장한 뒤 Eagle 라이브러리에 바로 등록하는 세 개의 출력 노드를 제공합니다.

- **Eagle Save Image** — `IMAGE` 저장 + Eagle 등록 + 이미지 미리보기.
- **Eagle Save Audio** — `AUDIO` 저장 + Eagle 등록 + 재생/탐색 가능한 오디오 플레이어.
- **Eagle Save Video** — ComfyUI 네이티브 `VIDEO` 저장 + Eagle 등록 + 재생/탐색 가능한 비디오 플레이어.

상류 워크플로에서 생성 메타데이터를 가능한 범위에서 찾아 Eagle 태그/주석에도 기록합니다.

> 비공식 커뮤니티 프로젝트이며 Comfy Org 또는 Eagle의 공식 프로젝트/승인 제품이 아닙니다.

## 요구 사항

- 최신 계열의 ComfyUI.
- 같은 PC에서 실행 중인 Eagle 데스크톱 앱.
- 노드 실행 시 Eagle 라이브러리가 열려 있어야 합니다.
- Eagle 로컬 API 기본 주소: `127.0.0.1:41595`.
- Python 의존성: `requests>=2.31.0`.
- 오디오/비디오 인코딩은 ComfyUI 환경의 PyAV/FFmpeg/코덱 지원에 따라 달라집니다.

## 설치

1. ComfyUI를 종료합니다.
2. `ComfyUI-EagleBridge` 폴더를 `ComfyUI/custom_nodes/`에 복사합니다.
3. ComfyUI가 사용하는 동일한 Python 환경에서 다음을 실행합니다.

   ```bash
   pip install -r ComfyUI/custom_nodes/ComfyUI-EagleBridge/requirements.txt
   ```

4. Eagle을 실행하고 대상 라이브러리를 엽니다.
5. ComfyUI를 시작합니다.
6. 업데이트 후 UI가 이전 상태로 보이면 `Ctrl+Shift+R`로 강력 새로고침하고 노드를 다시 추가합니다.

## Eagle 대상 폴더 ID

각 Save 노드는 `eagle_folder_id` 텍스트 입력을 사용합니다.

1. Eagle에서 저장할 폴더를 마우스 오른쪽 버튼으로 클릭하고 **링크 복사 / Copy Link**를 선택합니다.
2. 복사된 링크는 다음과 같은 형태입니다:

   ```text
   http://localhost:41595/folder?id=MU2LXTTH4KVRF
   ```

3. `id=` 뒤의 값만 복사합니다. 이 예에서는 `MU2LXTTH4KVRF`이며, 이를 `eagle_folder_id`에 붙여 넣습니다.
4. `eagle_folder_id`를 비워 두면 **Eagle Library Root**에 저장됩니다.

폴더 ID는 워크플로에 직접 저장됩니다.

## 공통 파일명/폴더 템플릿

`file_name_template` 기본값은 `%datetime%_%rand%`입니다.

- `%date%` → `YYYYMMDD`
- `%time%` → `HHMMSS`
- `%datetime%` → `YYYYMMDD_HHMMSS`
- `%index%` → 배치 인덱스
- `%rand%` → 짧은 랜덤 ID

`local_subfolder`에서는 다음 형식입니다.

- `%date%` → `YYYY-MM-DD`
- `%time%` → `HH-MM-SS`
- `%datetime%` → `YYYY-MM-DD_HH-MM-SS`
- `%model%` → 첫 번째로 감지된 모델명, 감지 실패 시 `UnknownModel`

## Eagle Save Image 사용법

ComfyUI의 `IMAGE` 출력을 `image`에 직접 연결합니다. 이 노드 자체가 출력 노드이므로 별도의 표준 Save Image가 필요하지 않습니다.

- **format**: `webp` / `png` / `jpg`
- **quality**: 1–100, 기본 95. 손실 WebP/JPEG에 사용됩니다.
- **lossless_webp**: 무손실 WebP 저장.
- **local_subfolder**: 기본 `EagleBridge/Image/%date%/`.
- **save_local_copy**: 켜면 ComfyUI output에 파일을 유지하고, 끄면 Eagle 가져오기를 위한 임시 파일을 사용합니다.
- **preview**: 노드에 이미지 미리보기를 표시합니다.
- **memo**: Eagle 주석 마지막에 `Memo:`로 추가됩니다.
- **website**: Eagle Website 필드에 저장할 선택 URL입니다.

가능한 경우 Eagle 주석에는 Positive Prompt, Negative Prompt, Model, Size, Seed, Steps, CFG, Sampler, Scheduler 순으로 기록됩니다. 없는 정보는 생략됩니다. 태그에는 첫 번째로 감지한 모델명만 사용합니다.

PNG와 WebP는 ComfyUI 메타데이터 저장이 활성화되어 있을 때 prompt/workflow 계열 정보를 파일에 기록합니다. JPEG에는 현재 워크플로 메타데이터를 삽입하지 않습니다.

## Eagle Save Audio 사용법

`AUDIO` 출력을 `audio`에 연결합니다. 원본 `AUDIO`가 출력으로 그대로 전달되어 후속 노드에 연결할 수 있습니다.

- **format**: `wav` / `flac` / `mp3` / `opus`
- **bitrate**: 64k–320k. MP3/Opus에서 사용되며 WAV/FLAC에서는 무시됩니다.
- **local_subfolder**: 기본 `EagleBridge/Audio/%date%/`.
- **preview**: 재생/일시정지/탐색 가능한 오디오 플레이어 표시.
- **save_local_copy / memo / website**: 이미지 노드와 같은 의미입니다.

음악 Prompt는 `caption`, `prompt`, `tags`, `sample_query`, `description` 등을 검색하고, 가사는 `lyrics`, `lyric`을 검색합니다. ACE-Step 계열처럼 비슷한 입력 이름을 사용하는 음악 워크플로에서 유용합니다.

주석 예시:

```text
Prompt:
...

Lyrics:
...

Model: ...
Duration: 30 sec
Sample Rate: 48000 Hz
Channels: 2
```

WAV는 16-bit PCM으로 저장합니다. Opus의 샘플레이트 변환이 필요한 경우 사용 가능한 `torchaudio`를 활용합니다. 현재 오디오 컨테이너 자체에는 전체 ComfyUI 워크플로 메타데이터를 삽입하지 않습니다.

## Eagle Save Video 사용법

ComfyUI의 네이티브 `VIDEO` 출력을 `video`에 연결합니다. 원본 `VIDEO`는 출력으로 그대로 전달됩니다.

- **format**: `mp4` / `webm` / `mkv`
- **codec**: `auto` / `h264` / `av1`
- **local_subfolder**: 기본 `EagleBridge/Video/%date%/`.
- **preview**: 재생/일시정지/탐색 가능한 비디오 플레이어 표시.
- **save_local_copy / memo / website**: 다른 Save 노드와 같은 의미입니다.

`webm + h264` 조합은 이 노드에서 거부됩니다. 실제 코덱 사용 가능 여부는 ComfyUI/PyAV/FFmpeg 환경에 따라 달라집니다.

비디오 Prompt는 `prompt`, `positive_prompt`, `positive_text`, `prompt_text`, `text_prompt`, `caption`, `description`, `text` 등 자주 쓰이는 필드를 상류에서 검색합니다. Negative Prompt도 가능한 경우 별도로 찾습니다.

모델명은 VAE, Qwen/CLIP/T5 텍스트 인코더, LoRA 같은 보조 요소보다 **주요 비디오 생성 모델**을 우선 선택합니다. MiniMax H3, Wan, LTX처럼 여러 모델 파일이 동시에 존재하는 워크플로에서 Eagle의 Model/Tag를 깔끔하게 만들기 위한 기능입니다.

주석에는 가능한 경우 Prompt, Negative Prompt, Model, Size, Duration, FPS, Seed, Steps, CFG, Sampler, Scheduler가 들어갑니다. Duration/FPS는 읽기 쉽게 반올림됩니다.

## 문제 해결

- **업데이트 후 플레이어가 안 보임:** ComfyUI 재시작 → `Ctrl+Shift+R` → 노드 삭제 후 재추가 순서로 확인하세요.
- **파일명이 다른데 중복으로 표시됨:** Eagle은 파일명과 별개로 동일 콘텐츠를 중복으로 감지할 수 있습니다.
- **MP3/Opus/비디오 인코딩 실패:** ComfyUI 환경의 PyAV/FFmpeg/코덱 지원을 확인하세요.
- **Prompt/Model 누락:** 메타데이터 추출은 최선형(best-effort)이며 일부 커스텀 워크플로 구조는 아직 인식하지 못할 수 있습니다.
- **원격 ComfyUI 사용 시 주의:** 이 노드는 ComfyUI 백엔드에서 로컬 파일을 쓰고 Eagle 로컬 API를 호출합니다. 신뢰할 수 없는 사용자가 워크플로를 실행할 수 있게 공개하지 마세요.

## 라이선스

GNU General Public License v3.0. 자세한 내용은 `LICENSE`를 참조하세요.

---

# 日本語

## 概要

ComfyUI-EagleBridge は、ComfyUIで生成した**画像・音声・動画**を保存し、そのまま Eagle ライブラリへ登録するための3つの出力ノードを提供します。

- **Eagle Save Image** — `IMAGE` を保存してEagleへ登録。画像プレビュー対応。元の `IMAGE` を右側の出力へそのまま渡せます。
- **Eagle Save Audio** — `AUDIO` を保存してEagleへ登録。再生ボタン・シークバー付きプレイヤー対応。
- **Eagle Save Video** — ComfyUIネイティブ `VIDEO` を保存してEagleへ登録。再生ボタン・シークバー付きプレイヤー対応。

さらに、上流ワークフローから取得できる生成情報を自動で抽出し、Eagleのタグとアノテーションへ整理して記録します。

> 非公式のコミュニティプロジェクトです。Comfy OrgおよびEagle公式とは提携・公認関係にありません。

## 必要環境

- 比較的新しいComfyUI。
- ComfyUIと同じPCで起動しているEagleデスクトップアプリ。
- ノード実行時にEagleでライブラリを開いていること。
- EagleローカルAPIの既定アドレス `127.0.0.1:41595` が利用できること。
- Eagle API呼び出しにはアプリ側のタイムアウトを設けず、Eagleから応答が返るまで待機します。
- Python依存パッケージ：`requests>=2.31.0`。
- 音声・動画のエンコード可否は、ComfyUI環境側のPyAV / FFmpeg / コーデック対応状況にも依存します。

## インストール

**ComfyUI Manager:** `ComfyUI-EagleBridge` または `eagle-bridge` で検索して、そのままインストールできます。

**手動インストール:**

1. ComfyUIを完全に終了します。
2. `ComfyUI-EagleBridge` フォルダを `ComfyUI/custom_nodes/` に配置します。
3. ComfyUIが使用している同じPython環境で依存パッケージをインストールします。

   ```bash
   pip install -r ComfyUI/custom_nodes/ComfyUI-EagleBridge/requirements.txt
   ```

4. Eagleを起動し、保存先として使うライブラリを開きます。
5. ComfyUIを起動します。
6. アップデート後に古いUIが残っている場合は、ブラウザで `Ctrl+Shift+R` を行い、対象ノードを一度削除して追加し直してください。

## Eagle保存先フォルダID

各Saveノードは `eagle_folder_id` のテキスト入力方式です。

1. Eagleで保存したいフォルダを右クリックし、**「リンクをコピー」** を選びます。
2. コピーされたリンクは次のような形式です。

   ```text
   http://localhost:41595/folder?id=MU2LXTTH4KVRF
   ```

3. `id=` の後ろにある文字列だけをコピーします。この例では `MU2LXTTH4KVRF` です。
4. そのIDを `eagle_folder_id` に貼り付けます。
5. `eagle_folder_id` を空欄にすると **Eagle Library Root** へ保存します。

フォルダIDはワークフローへ直接保存されます。

## 共通：ファイル名テンプレート

### `file_name_template`

初期値：

```text
%datetime%_%rand%
```

使える置換：

- `%date%` → `YYYYMMDD`
- `%time%` → `HHMMSS`
- `%datetime%` → `YYYYMMDD_HHMMSS`
- `%index%` → バッチ番号
- `%rand%` → 短いランダムID

例：

```text
20260915_203128_ab12cd34.webp
```

## 共通：ローカル保存フォルダテンプレート

`local_subfolder` では次の置換を使えます。

- `%date%` → `YYYY-MM-DD`
- `%time%` → `HH-MM-SS`
- `%datetime%` → `YYYY-MM-DD_HH-MM-SS`
- `%model%` → 最初に検出したモデル名。検出できない場合は `UnknownModel`

保存先は必ずComfyUIのoutput/tempディレクトリ配下に制限されます。

---

## Eagle Save Image

### 基本的な使い方

画像生成側の `IMAGE` 出力を、そのまま `image` 入力へ接続します。

保存後も元の `IMAGE` を右側の `image` 出力へそのまま渡すため、必要なら後続ノードへ接続できます。`Eagle Save Image` 自体も `OUTPUT_NODE` のままなので、EagleBridgeで保存するだけなら通常の `Save Image` ノードを別に置く必要はありません。

### 各項目

- **image** — ComfyUIの `IMAGE` 入力。
- **eagle_folder_id** — Eagle内の保存先フォルダ。
- **file_name_template** — ファイル名テンプレート。初期値 `%datetime%_%rand%`。
- **local_subfolder** — ComfyUI側のローカル保存先。初期値 `EagleBridge/Image/%date%/`。
- **format** — `webp` / `png` / `jpg`。
- **quality** — 1～100。初期値95。主に非可逆WebP/JPEGの品質に使用します。
- **lossless_webp** — ONならWebPをロスレス保存します。
- **save_local_copy** — ONならComfyUI output側にもファイルを残します。OFFならEagleへ取り込むための一時ファイルをtemp側に作ります。
- **preview** — ONならノード内に保存画像のプレビューを表示します。
- **memo** — 任意のメモ。Eagleアノテーション末尾へ `Memo:` として追加します。
- **website** — 任意のURL。EagleアイテムのWebsite欄へ登録します。

### Eagleへ登録される情報

取得できる場合、アノテーションは概ね次の順で整理されます。

```text
Positive Prompt:
...

Negative Prompt:
...

Model: ...
Size: ...
Seed: ...
Steps: ...
CFG: ...
Sampler: ...
Scheduler: ...

Memo:
...
```

取得できなかった項目は表示しません。

Eagleの**タグは最初に検出したモデル名1つだけ**を使用します。

### 画像ファイル内部のメタデータ

- **PNG** — ComfyUI側でメタデータ保存が無効化されていなければ、prompt / workflow系情報を埋め込みます。
- **WebP** — ComfyUI互換を意識したEXIF形式でprompt / extra情報を埋め込みます。
- **JPEG** — 現在、EagleBridgeからComfyUIワークフローメタデータは埋め込みません。

---

## Eagle Save Audio

### 基本的な使い方

音声生成側の `AUDIO` 出力を `audio` へ直接接続します。

保存後も元の `AUDIO` をそのまま出力するため、必要なら後続ノードへ接続できます。

### 各項目

- **audio** — ComfyUI `AUDIO`。
- **eagle_folder_id** — Eagle保存先。
- **file_name_template** — ファイル名テンプレート。
- **local_subfolder** — 初期値 `EagleBridge/Audio/%date%/`。
- **format** — `wav` / `flac` / `mp3` / `opus`。
- **bitrate** — `64k` / `96k` / `128k` / `192k` / `256k` / `320k`。MP3 / Opusで使用します。WAV / FLACはロスレスのため、この値を無視します。
- **save_local_copy** — ONならoutputへ保存。OFFなら一時ファイルを使用します。
- **preview** — ONならノード内に再生ボタン・シークバー付き音声プレイヤーを表示します。
- **memo** — Eagleアノテーションへ追記する任意メモ。
- **website** — Eagle Website欄へ保存する任意URL。

### PromptとLyricsの自動取得

音楽生成系は通常の画像ワークフローと構造が異なるため、上流から次のようなフィールド名を探します。

Prompt候補：

```text
caption
prompt
tags
sample_query
description
```

Lyrics候補：

```text
lyrics
lyric
```

ACE-Step系をはじめ、同様のフィールド名を使う音楽生成ノードで利用できます。見つからなかった項目は表示しません。

### Eagleアノテーション例

```text
Prompt:
Upbeat Japanese city-pop ...

Lyrics:
夜風に揺れる街の灯り
...

Model: acestep_v1.5_xl_sft_bf16
Duration: 30 sec
Sample Rate: 48000 Hz
Channels: 2

Memo:
...
```

Durationは読みやすいように小数を整理します。

Eagleタグは最初に検出したモデル名を使用します。

### 音声形式について

- WAVは16-bit PCMとして保存します。
- MP3 / Opusでは `bitrate` が有効です。
- FLAC / WAVでは `bitrate` を無視します。
- Opusで対応サンプルレートへの変換が必要な場合、利用可能なら `torchaudio` を使用します。
- 現在、音声ファイル内部へComfyUIの完全なワークフローメタデータは埋め込みません。PromptやモデルなどはEagleのアノテーション/タグ側で管理します。

---

## Eagle Save Video

### 基本的な使い方

動画生成側が出しているComfyUIネイティブの `VIDEO` 出力を `video` に直接接続します。

保存後も元の `VIDEO` をそのまま出力するため、後続ノードへ接続できます。

### 各項目

- **video** — ComfyUIネイティブ `VIDEO` 入力。
- **eagle_folder_id** — Eagle保存先。
- **file_name_template** — ファイル名テンプレート。
- **local_subfolder** — 初期値 `EagleBridge/Video/%date%/`。
- **format** — `mp4` / `webm` / `mkv`。
- **codec** — `auto` / `h264` / `av1`。
- **save_local_copy** — ONならComfyUI outputへ保存。OFFならtempを使用します。
- **preview** — ONならノード内に再生ボタン・シークバー付き動画プレイヤーを表示します。
- **memo** — Eagleアノテーションへ追記するメモ。
- **website** — Eagle Website欄へ保存する任意URL。

### format / codecについて

`webm + h264` の組み合わせはこのノードではエラーにします。

また、選択したコーデックを実際に使えるかどうかは、ComfyUI側のPyAV / FFmpeg / コーデック構成にも依存します。

### Video Promptの自動取得

動画ワークフローは標準KSamplerのPositive Prompt経路を通らないことがあるため、上流から以下のような名前を追加で探索します。

```text
prompt
positive_prompt
positive_text
prompt_text
text_prompt
caption
description
text
```

Negative Promptについても、対応するフィールドが見つかった場合のみ記録します。

### メイン動画モデルの自動選択

MiniMax H3 / Wan / LTXなどでは、上流に

- メイン動画生成モデル
- VAE
- Qwen / CLIP / T5などのテキスト・ビジョン系モデル
- LoRA等

が同時に存在する場合があります。

EagleBridgeは、それらをすべて `Model:` に並べるのではなく、**実際の動画生成に使われている可能性が高いメインモデルを優先**します。VAEやテキストエンコーダ等の補助モデルは優先度を下げます。

たとえばMiniMax H3のワークフローで複数モデルが見つかっても、Eagle側では次のように主要モデルだけを表示できることを狙っています。

```text
Model: minimax_h3_fl2v_turbo_4step_v1.2_768p_comfyui_bf16
```

### Eagleアノテーション例

```text
Prompt:
A cinematic 5-second shot ...

Model: minimax_h3_fl2v_turbo_4step_v1.2_768p_comfyui_bf16
Size: 960x544
Duration: 5.17 sec
FPS: 24
```

通常のSampler情報を取得できるワークフローでは、さらにSeed / Steps / CFG / Sampler / Schedulerも追加します。

DurationとFPSは `5.167 sec → 5.17 sec`、`24.000 → 24` のように読みやすく整形します。

### 動画ファイル内部のメタデータ

ComfyUI側でメタデータ保存が有効な場合、EagleBridgeはComfyUIネイティブ `VIDEO.save_to()` にprompt / extra情報を渡します。実際にどのようにコンテナへ格納されるかは、ComfyUI本体・コンテナ形式・コーデック側の実装に依存します。

---

## トラブルシューティング

### Eagleのfolder IDが分からない

1. Eagleで保存したいフォルダを右クリックします。
2. **「リンクをコピー」** を選びます。
3. コピーされたリンクを確認します。たとえば：

   ```text
   http://localhost:41595/folder?id=MU2LXTTH4KVRF
   ```

4. `id=` の後ろにある `MU2LXTTH4KVRF` のような文字列だけを `eagle_folder_id` に貼り付けます。
5. `eagle_folder_id` を空欄にするとEagle Library Rootへ保存します。

### アップデートしたのに古いノード表示のまま

ComfyUIを完全終了して再起動し、ブラウザで `Ctrl+Shift+R` を行ってください。それでも変わらない場合はワークフロー上の古いノードを削除し、新しく追加し直してください。

### プレイヤーが表示されない

Audio / Videoの `preview` がONになっていることを確認します。アップデート直後なら、ComfyUI再起動とブラウザのハードリフレッシュも行ってください。

### ファイル名は違うのにEagleが重複と判定する

Eagleはファイル名ではなく、同じ内容のファイルを重複として検出する場合があります。テスト時はSeedなどを変えて別の内容を生成してください。

### Prompt / Modelが出ない

自動抽出はbest-effort（可能な範囲で探索）です。カスタムノード固有のフィールド名や特殊な接続構造では取得できない場合があります。

### MP3 / Opus / Videoのエンコードに失敗する

ComfyUI環境に入っているPyAV / FFmpeg / codecの対応状況を確認してください。形式やcodecを変更すると動作する場合があります。

### セキュリティ上の注意

この拡張はComfyUIバックエンドからローカルファイルを作成し、EagleのローカルAPIへファイルパスを送信します。ComfyUIをインターネットへ公開している場合、信頼できないユーザーにワークフロー実行権限を与えないよう注意してください。

## ライセンス

GNU General Public License v3.0。詳細は `LICENSE` を参照してください。
