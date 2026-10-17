# ComfyUI-EagleBridge

![Version](https://img.shields.io/badge/version-1.2.2-2ea44f?style=flat-square)
![License](https://img.shields.io/badge/license-GPL--3.0-blue?style=flat-square)
![ComfyUI](https://img.shields.io/badge/ComfyUI-custom%20nodes-6f42c1?style=flat-square)

ComfyUI-EagleBridge adds three output nodes that save generated **images, audio, and video** from ComfyUI and register them directly in an **Eagle** library.

Published on the **Comfy Registry** as `eagle-bridge`, so it can be discovered and installed from **ComfyUI Manager**.


> Unofficial community project. This project is not affiliated with or endorsed by Comfy Org or Eagle.

**Languages:** [English](README.md) · [简体中文](README.zh-CN.md) · [한국어](README.ko.md) · [日本語](README.ja.md)

---

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

## Recording prompts built at runtime (`prompt_text`)

The Save nodes normally read the prompt text from the workflow graph
(`CLIPTextEncode` and similar text nodes). Some nodes compose the prompt only
at runtime — for example `MOSSImageLayoutPrompt` builds it from layout
elements — so no literal text exists in the graph and it cannot be
auto-extracted.

For those workflows, every Save node now has an optional input socket
named `prompt` (internally `prompt_text`) — no text box, just a plug:

1. Connect the STRING output of the node that builds the prompt
   (e.g. `MOSSImageLayoutPrompt` → `prompt`) into `prompt_text`.
2. The connected text is recorded as the Positive Prompt (or Prompt for
   audio/video) in the Eagle annotation, overriding auto-extraction.

Leave `prompt_text` unconnected for normal workflows — nothing changes.

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

