# ComfyUI-EagleBridge

**Languages:** [English](README.md) · [简体中文](README.zh-CN.md) · [한국어](README.ko.md) · [日本語](README.ja.md)

---

## 개요

ComfyUI-EagleBridge는 ComfyUI에서 생성한 **이미지, 오디오, 비디오**를 저장한 뒤 Eagle 라이브러리에 바로 등록하는 세 개의 출력 노드(함께 포함된 Video Preview 미리보기 유틸리티 노드도 제공)를 제공합니다.

- **Eagle Save Image** — `IMAGE` 저장 + Eagle 등록 + 이미지 미리보기, 원본 `IMAGE`는 출력 그대로 통과.
- **Eagle Save Audio** — `AUDIO` 저장 + Eagle 등록 + 재생/탐색 가능한 오디오 플레이어.
- **Eagle Save Video** — ComfyUI 네이티브 `VIDEO` 저장 + Eagle 등록 + 재생/탐색 가능한 비디오 플레이어.

저장 시 상류 워크플로에서 생성 메타데이터(프롬프트, 모델, 크기, 시드, 스텝, CFG, 샘플러 등)를 가능한 범위에서 찾아 Eagle 태그/주석에 기록합니다. 프롬프트를 실행 중에만 합성하는 워크플로(`MOSSImageLayoutPrompt` 등)에는 선택형 `prompt` 입력 소켓으로 정확한 텍스트를 남길 수 있습니다.

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

## 런타임에 생성되는 프롬프트 기록 (`prompt_text`)

Save 노드는 일반적으로 워크플로 그래프에서 프롬프트 텍스트를 읽습니다
(`CLIPTextEncode` 등). 그러나 일부 노드는 실행 시에만 프롬프트를 생성합니다.
예를 들어 `MOSSImageLayoutPrompt`는 레이아웃 요소로 프롬프트를 조합하므로
그래프에 텍스트가 존재하지 않아 자동 추출이 불가능합니다.

이런 워크플로를 위해 모든 Save 노드에 `prompt`라는 선택 입력 소켓
(내부 키는 `prompt_text`, 텍스트 상자가 아닌 연결 플러그만 표시됩니다)이
추가되었습니다:

1. 프롬프트를 생성하는 노드의 STRING 출력
   (예: `MOSSImageLayoutPrompt` → `prompt`)을 `prompt` 소켓에 연결합니다.
2. 연결된 텍스트가 Eagle 주석의 Positive Prompt(오디오/영상은 Prompt)로
   기록되며 자동 추출 결과를 덮어씁니다.

일반적인 워크플로에서는 `prompt` 소켓을 연결하지 않으면 기존과 동일하게
동작합니다.

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

