import json
import os
import re
import uuid
import wave
from collections import deque
from datetime import datetime

import numpy as np

try:
    import av
except Exception:
    av = None

try:
    import torch
    import torchaudio
except Exception:
    torch = None
    torchaudio = None
from PIL import Image
from PIL.PngImagePlugin import PngInfo

import folder_paths

try:
    from comfy.cli_args import args as comfy_args
except Exception:
    comfy_args = None

try:
    from comfy_api.latest import Types as ComfyTypes
except Exception:
    ComfyTypes = None

from .eagle_client import add_item_from_path



SAMPLER_CLASS_NAMES = {
    "KSampler",
    "KSamplerAdvanced",
    "SamplerCustom",
    "SamplerCustomAdvanced",
}

FIXED_IMAGE_ANNOTATION_ORDER = (
    "positive_prompt,negative_prompt,model,size,seed,steps,cfg,sampler,scheduler"
)

FIXED_AUDIO_ANNOTATION_ORDER = (
    "audio_prompt,lyrics,model,duration,sample_rate,channels"
)

FIXED_VIDEO_ANNOTATION_ORDER = (
    "video_prompt,negative_prompt,model,size,duration,fps,seed,steps,cfg,sampler,scheduler"
)





def eagle_folder_id_input():
    return (
        "STRING",
        {
            "default": "",
            "multiline": False,
            "placeholder": "Example: MLZWD86F6YNH4",
            "tooltip": (
                "Paste the Eagle destination folder ID. "
                "Leave blank to save to the Eagle Library Root. "
                "To find folder IDs, open "
                "http://127.0.0.1:41595/api/folder/list in a browser while Eagle is running."
            ),
        },
    )


def normalize_eagle_folder_id(value):
    folder_id = str(value or "").strip()
    return folder_id or None

def ordered_unique(values: list[str]) -> list[str]:
    seen = set()
    result = []
    for value in values:
        text = str(value).strip()
        if not text:
            continue
        key = text.casefold()
        if key in seen:
            continue
        seen.add(key)
        result.append(text)
    return result


def sanitize_filename(name: str) -> str:
    name = (name or "").strip() or "file"
    name = re.sub(r'[<>:"/\\|?*\x00-\x1f]', "_", name)
    return name.rstrip(". ") or "file"


def render_template(template: str, index: int = 0) -> str:
    now = datetime.now()
    result = template or "%datetime%_%rand%"

    replacements = {
        "%date%": now.strftime("%Y%m%d"),
        "%time%": now.strftime("%H%M%S"),
        "%datetime%": now.strftime("%Y%m%d_%H%M%S"),
        "%index%": str(index),
        "%rand%": uuid.uuid4().hex[:8],
    }

    for key, value in replacements.items():
        result = result.replace(key, value)

    return sanitize_filename(result)


def first_model_name(metadata: dict | None, fallback: str = "UnknownModel") -> str:
    metadata = metadata or {}
    names = metadata.get("model_names") or []
    if names:
        return sanitize_filename(str(names[0]))
    return fallback


def render_subfolder_template(template: str, metadata: dict | None, fallback: str) -> str:
    now = datetime.now()
    raw = (template or fallback).strip().replace("\\", "/")
    if not raw:
        raw = fallback

    replacements = {
        "%date%": now.strftime("%Y-%m-%d"),
        "%time%": now.strftime("%H-%M-%S"),
        "%datetime%": now.strftime("%Y-%m-%d_%H-%M-%S"),
        "%model%": first_model_name(metadata),
    }

    parts = []
    for part in raw.strip("/").split("/"):
        piece = part
        for key, value in replacements.items():
            piece = piece.replace(key, value)
        piece = sanitize_filename(piece)
        if piece:
            parts.append(piece)

    if not parts:
        return fallback.strip("/")

    return "/".join(parts)


def safe_subfolder(base_dir: str, subfolder: str, fallback: str) -> tuple[str, str]:
    relative = (subfolder or fallback).strip().replace("\\", "/").strip("/")
    if not relative:
        relative = fallback

    candidate = os.path.abspath(os.path.join(base_dir, *relative.split("/")))
    base_abs = os.path.abspath(base_dir)

    if os.path.commonpath([candidate, base_abs]) != base_abs:
        raise RuntimeError("Subfolder must stay inside the ComfyUI output/temp directory.")

    os.makedirs(candidate, exist_ok=True)
    normalized = os.path.relpath(candidate, base_abs).replace("\\", "/")
    return candidate, normalized


def unique_path(directory: str, filename: str) -> str:
    os.makedirs(directory, exist_ok=True)

    stem, ext = os.path.splitext(filename)
    candidate = os.path.join(directory, filename)
    counter = 1

    while os.path.exists(candidate):
        candidate = os.path.join(directory, f"{stem}_{counter}{ext}")
        counter += 1

    return candidate


def tensor_to_pil(image_tensor) -> Image.Image:
    array = image_tensor.detach().cpu().numpy()
    array = np.clip(array * 255.0, 0, 255).astype(np.uint8)
    return Image.fromarray(array)


def metadata_enabled(embed_workflow: bool) -> bool:
    if not embed_workflow:
        return False
    if comfy_args is not None and getattr(comfy_args, "disable_metadata", False):
        return False
    return True


def build_pnginfo(prompt, extra_pnginfo, embed_workflow: bool):
    if not metadata_enabled(embed_workflow):
        return None

    pnginfo = PngInfo()

    if prompt is not None:
        pnginfo.add_text("prompt", json.dumps(prompt))

    if extra_pnginfo is not None:
        for key, value in extra_pnginfo.items():
            pnginfo.add_text(str(key), json.dumps(value))

    return pnginfo


def build_comfy_webp_exif(image: Image.Image, prompt, extra_pnginfo, embed_workflow: bool):
    exif = image.getexif()

    if not metadata_enabled(embed_workflow):
        return exif

    if prompt is not None:
        exif[0x0110] = "prompt:{}".format(json.dumps(prompt))

    if extra_pnginfo is not None:
        tag = 0x010F
        for key, value in extra_pnginfo.items():
            exif[tag] = "{}:{}".format(key, json.dumps(value))
            tag -= 1
            if tag <= 0:
                break

    return exif


def save_pil_image(
    image: Image.Image,
    path: str,
    fmt: str,
    quality: int,
    *,
    prompt=None,
    extra_pnginfo=None,
    embed_workflow: bool = True,
    lossless_webp: bool = False,
):
    fmt = fmt.lower()

    if fmt == "png":
        kwargs = {"compress_level": 4}
        pnginfo = build_pnginfo(prompt, extra_pnginfo, embed_workflow)
        if pnginfo is not None:
            kwargs["pnginfo"] = pnginfo
        image.save(path, format="PNG", **kwargs)
        return

    if image.mode not in ("RGB", "L"):
        image = image.convert("RGB")

    if fmt == "webp":
        exif = build_comfy_webp_exif(image, prompt, extra_pnginfo, embed_workflow)
        kwargs = {"format": "WEBP", "method": 6, "exif": exif}
        if lossless_webp:
            kwargs["lossless"] = True
        else:
            kwargs["quality"] = int(quality)
        image.save(path, **kwargs)
        return

    image.save(
        path,
        format="JPEG",
        quality=int(quality),
        optimize=True,
    )



def normalize_prompt(prompt):
    return prompt if isinstance(prompt, dict) else {}


def get_prompt_node(prompt, node_id):
    if prompt is None or node_id is None:
        return None
    return prompt.get(str(node_id))


def get_linked_node_id(value):
    if isinstance(value, (list, tuple)) and value:
        return str(value[0])
    return None


def traverse_upstream(prompt, start_node_id, max_nodes=200):
    visited = set()
    order = []
    stack = [str(start_node_id)] if start_node_id is not None else []

    while stack and len(visited) < max_nodes:
        node_id = stack.pop()
        if node_id in visited:
            continue
        visited.add(node_id)

        node = get_prompt_node(prompt, node_id)
        if not isinstance(node, dict):
            continue

        order.append(node_id)
        inputs = node.get("inputs", {})
        if not isinstance(inputs, dict):
            continue

        for value in inputs.values():
            linked = get_linked_node_id(value)
            if linked and linked not in visited:
                stack.append(linked)

    return order


def find_first_node_by_class(prompt, start_node_id, class_names):
    for node_id in traverse_upstream(prompt, start_node_id):
        node = get_prompt_node(prompt, node_id)
        if node and node.get("class_type") in class_names:
            return node_id, node
    return None, None


def find_sampler_node(prompt, start_node_id):
    return find_first_node_by_class(prompt, start_node_id, SAMPLER_CLASS_NAMES)


def get_node_inputs(node):
    inputs = node.get("inputs", {}) if isinstance(node, dict) else {}
    return inputs if isinstance(inputs, dict) else {}


def linked_node(prompt, node, input_name):
    inputs = get_node_inputs(node)
    linked = get_linked_node_id(inputs.get(input_name))
    if linked:
        return linked, get_prompt_node(prompt, linked)
    return None, None


def extract_text_from_node(prompt, node_id, visited=None):
    """
    Conservative text extraction for one conditioning branch.
    """
    if visited is None:
        visited = set()

    stack = [str(node_id)] if node_id is not None else []

    while stack:
        current_id = stack.pop()
        if current_id in visited:
            continue
        visited.add(current_id)

        node = get_prompt_node(prompt, current_id)
        if not isinstance(node, dict):
            continue

        inputs = get_node_inputs(node)
        class_type = node.get("class_type", "")

        if class_type == "CLIPTextEncode":
            text = inputs.get("text")
            if isinstance(text, str) and text.strip():
                return text.strip()

        text_value = inputs.get("text")
        if isinstance(text_value, str) and text_value.strip():
            return text_value.strip()

        next_ids = []
        for key in ("conditioning", "cond", "base_cond", "added_cond", "clip", "text"):
            linked = get_linked_node_id(inputs.get(key))
            if linked:
                next_ids.append(linked)

        if not next_ids:
            for value in inputs.values():
                linked = get_linked_node_id(value)
                if linked:
                    next_ids.append(linked)

        stack.extend(reversed(next_ids))

    return ""


def clean_model_name(value):
    if not value:
        return ""
    name = str(value).replace("\\", "/").split("/")[-1]
    base, _ext = os.path.splitext(name)
    return base or name


def extract_model_names(prompt, start_node_id):
    names = []
    keys = ("ckpt_name", "unet_name", "model_name", "lora_name", "clip_name", "vae_name")

    for node_id in traverse_upstream(prompt, start_node_id):
        node = get_prompt_node(prompt, node_id)
        inputs = get_node_inputs(node)
        for key in keys:
            value = inputs.get(key)
            if isinstance(value, str) and value.strip():
                names.append(clean_model_name(value))

    return ordered_unique(names)


def extract_model_candidates(prompt, start_node_id):
    """
    Return upstream model-like filenames together with the input key/class that
    exposed them. Video selection can then prefer the actual diffusion model
    over VAE/text-encoder/support models.
    """
    candidates = []
    keys = (
        "ckpt_name",
        "unet_name",
        "model_name",
        "diffusion_model",
        "lora_name",
        "clip_name",
        "vae_name",
    )

    seen = set()

    for node_id in traverse_upstream(prompt, start_node_id):
        node = get_prompt_node(prompt, node_id)
        if not isinstance(node, dict):
            continue

        inputs = get_node_inputs(node)
        class_type = str(node.get("class_type") or "")

        for key in keys:
            value = inputs.get(key)
            if not isinstance(value, str) or not value.strip():
                continue

            name = clean_model_name(value)
            if not name:
                continue

            identity = (name, key, class_type)
            if identity in seen:
                continue
            seen.add(identity)

            candidates.append(
                {
                    "name": name,
                    "key": key,
                    "class_type": class_type,
                }
            )

    return candidates


def score_video_model_candidate(candidate):
    """
    Favor main video diffusion/checkpoint models and strongly demote VAE,
    text encoders, LoRAs and other support components.
    """
    name = str(candidate.get("name") or "")
    key = str(candidate.get("key") or "").lower()
    class_type = str(candidate.get("class_type") or "").lower()
    lower = name.lower()

    score = 0

    # Input-key signal.
    if key in ("unet_name", "diffusion_model"):
        score += 35
    elif key == "ckpt_name":
        score += 30
    elif key == "model_name":
        score += 12
    elif key == "lora_name":
        score -= 55
    elif key in ("clip_name", "vae_name"):
        score -= 120

    # Strong video-model naming signals.
    if re.search(r"(^|[_\-.])(t2v|i2v|v2v|fl2v)([_\-.]|$)", lower):
        score += 120

    if "video" in lower:
        score += 45

    # Useful tie-breakers for practical video checkpoints.
    if "turbo" in lower:
        score += 18
    if re.search(r"(^|[_\-.])\d+step(s)?([_\-.]|$)", lower):
        score += 10
    if "minimax" in lower or "wan" in lower or "ltx" in lower:
        score += 12

    # Support-model penalties.
    support_terms = (
        "vae",
        "text_encoder",
        "textencoder",
        "clip",
        "tokenizer",
        "qwen",
        "t5",
        "llama",
        "bert",
        "vit",
    )
    if any(term in lower for term in support_terms):
        score -= 140

    support_class_terms = (
        "vae",
        "clip",
        "textencoder",
        "text_encoder",
        "llm",
        "vision",
    )
    if any(term in class_type for term in support_class_terms):
        score -= 80

    return score


def select_primary_video_model(prompt, start_node_id):
    candidates = extract_model_candidates(prompt, start_node_id)
    if not candidates:
        return ""

    # Stable max(): equal scores preserve upstream traversal order.
    best = max(candidates, key=score_video_model_candidate)
    return best.get("name") or ""


def extract_sampler_metadata(prompt, start_node_id):
    node_id, node = find_sampler_node(prompt, start_node_id)
    if node is None:
        return {}

    inputs = get_node_inputs(node)
    data = {
        "sampler_class": node.get("class_type") or "",
        "seed": inputs.get("seed"),
        "steps": inputs.get("steps"),
        "cfg": inputs.get("cfg"),
        "sampler_name": inputs.get("sampler_name") or "",
        "scheduler": inputs.get("scheduler") or "",
        "denoise": inputs.get("denoise"),
    }

    pos_id, _ = linked_node(prompt, node, "positive")
    neg_id, _ = linked_node(prompt, node, "negative")

    positive = ""
    negative = ""

    if pos_id:
        positive = extract_text_from_node(prompt, pos_id)
        if positive:
            data["positive_prompt"] = positive

    if neg_id:
        negative = extract_text_from_node(prompt, neg_id)
        if negative and negative.strip() != positive.strip():
            data["negative_prompt"] = negative

    model_names = []
    model_id, _ = linked_node(prompt, node, "model")
    if model_id:
        model_names.extend(extract_model_names(prompt, model_id))

    if not model_names:
        model_names.extend(extract_model_names(prompt, node_id))

    if model_names:
        data["model_names"] = model_names

    return data



def find_upstream_string_input(prompt, start_node_id, candidate_keys):
    """
    Breadth-first search for the nearest non-empty string input.
    Key matching is case-insensitive and candidate_keys order defines priority.
    """
    if not isinstance(prompt, dict) or start_node_id is None:
        return ""

    priority = [str(key).casefold() for key in candidate_keys]
    queue = deque([str(start_node_id)])
    visited = set()

    while queue:
        node_id = queue.popleft()
        if node_id in visited:
            continue
        visited.add(node_id)

        node = get_prompt_node(prompt, node_id)
        if not isinstance(node, dict):
            continue

        inputs = get_node_inputs(node)
        folded = {str(key).casefold(): value for key, value in inputs.items()}

        for wanted in priority:
            value = folded.get(wanted)
            if isinstance(value, str) and value.strip():
                return value.strip()

        for value in inputs.values():
            linked = get_linked_node_id(value)
            if linked and linked not in visited:
                queue.append(linked)

    return ""


def extract_audio_text_metadata(prompt, start_node_id):
    """
    Extract music prompt/caption and lyrics from common ACE-Step style workflows.
    """
    data = {}

    audio_prompt = find_upstream_string_input(
        prompt,
        start_node_id,
        ("caption", "prompt", "tags", "sample_query", "description"),
    )
    lyrics = find_upstream_string_input(
        prompt,
        start_node_id,
        ("lyrics", "lyric"),
    )

    if audio_prompt:
        data["audio_prompt"] = audio_prompt
    if lyrics:
        data["lyrics"] = lyrics

    return data


def extract_video_text_metadata(prompt, start_node_id):
    """
    Extract prompt text from custom video workflows that do not use a normal
    KSampler/CLIPTextEncode positive-conditioning branch.

    The aliases cover common MiniMax/Wan/LTX/custom-node naming without relying
    on one specific node class.
    """
    data = {}

    video_prompt = find_upstream_string_input(
        prompt,
        start_node_id,
        (
            "prompt",
            "positive_prompt",
            "positive_text",
            "prompt_text",
            "text_prompt",
            "caption",
            "description",
            "text",
        ),
    )

    negative_prompt = find_upstream_string_input(
        prompt,
        start_node_id,
        (
            "negative_prompt",
            "negative_text",
            "negative",
        ),
    )

    if video_prompt:
        data["video_prompt"] = video_prompt

    if negative_prompt and negative_prompt.strip() != video_prompt.strip():
        data["negative_prompt"] = negative_prompt

    return data


def build_audio_metadata(prompt_graph, unique_id):
    metadata = extract_sampler_metadata(prompt_graph, unique_id)
    metadata.update(extract_audio_text_metadata(prompt_graph, unique_id))

    if not metadata.get("model_names"):
        model_names = extract_model_names(prompt_graph, unique_id)
        if model_names:
            metadata["model_names"] = model_names

    return metadata


def build_video_metadata(prompt_graph, unique_id):
    metadata = extract_sampler_metadata(prompt_graph, unique_id)
    video_text = extract_video_text_metadata(prompt_graph, unique_id)

    if not video_text.get("video_prompt") and metadata.get("positive_prompt"):
        video_text["video_prompt"] = metadata.get("positive_prompt")

    if not video_text.get("negative_prompt") and metadata.get("negative_prompt"):
        video_text["negative_prompt"] = metadata.get("negative_prompt")

    metadata.update(video_text)

    primary_video_model = select_primary_video_model(prompt_graph, unique_id)
    if primary_video_model:
        metadata["model_names"] = [primary_video_model]
    elif metadata.get("model_names"):
        metadata["model_names"] = (metadata.get("model_names") or [])[:1]

    return metadata



def format_value(value):
    if value is None or value == "":
        return None
    return str(value)


def format_trimmed_number(value, digits: int = 2):
    if value is None:
        return None

    try:
        numeric = float(value)
    except Exception:
        return None

    if abs(numeric - round(numeric)) < 1e-9:
        return str(int(round(numeric)))

    return f"{numeric:.{digits}f}".rstrip("0").rstrip(".")


def format_duration_value(duration_seconds: float | None):
    value = format_trimmed_number(duration_seconds, 2)
    return f"{value} sec" if value is not None else None


def format_fps_value(fps: float | None):
    return format_trimmed_number(fps, 2)


def parse_annotation_order(order_text: str) -> list[str]:
    aliases = {
        "prompt": "positive_prompt",
        "positive": "positive_prompt",
        "negative": "negative_prompt",
        "model_name": "model",
        "filename": "file",
        "resolution": "size",
    }

    fields = []
    for raw in re.split(r"[,|\n]+", order_text):
        key = raw.strip().lower()
        if not key:
            continue
        key = aliases.get(key, key)
        if key not in fields:
            fields.append(key)
    return fields


def build_annotation(
    media_type: str,
    *,
    file_format: str = "",
    filename: str = "",
    width: int | None = None,
    height: int | None = None,
    sample_rate: int | None = None,
    channels: int | None = None,
    duration_seconds: float | None = None,
    fps: float | None = None,
    metadata: dict | None = None,
    annotation_order: str = "",
):
    metadata = metadata or {}
    fields = parse_annotation_order(annotation_order)

    if not fields:
        return ""

    model_names = metadata.get("model_names", [])

    values = {
        "type": ("Type", media_type if media_type else None),
        "file": ("File", filename if filename else None),
        "format": ("Format", file_format.lower() if file_format else None),
        "size": ("Size", f"{width}x{height}" if width and height else None),
        "model": ("Model", ", ".join(model_names) if model_names else None),
        "seed": ("Seed", format_value(metadata.get("seed"))),
        "steps": ("Steps", format_value(metadata.get("steps"))),
        "cfg": ("CFG", format_value(metadata.get("cfg"))),
        "sampler": ("Sampler", format_value(metadata.get("sampler_name"))),
        "scheduler": ("Scheduler", format_value(metadata.get("scheduler"))),
        "denoise": ("Denoise", format_value(metadata.get("denoise"))),
        "duration": ("Duration", format_duration_value(duration_seconds)),
        "fps": ("FPS", format_fps_value(fps)),
        "sample_rate": ("Sample Rate", f"{sample_rate} Hz" if sample_rate else None),
        "channels": ("Channels", str(channels) if channels else None),
        "positive_prompt": ("Positive Prompt", metadata.get("positive_prompt") or None),
        "negative_prompt": ("Negative Prompt", metadata.get("negative_prompt") or None),
        "video_prompt": ("Prompt", metadata.get("video_prompt") or None),
        "audio_prompt": ("Prompt", metadata.get("audio_prompt") or None),
        "lyrics": ("Lyrics", metadata.get("lyrics") or None),
    }

    lines = []
    previous_kind = None  # "prompt" or "meta"

    for field in fields:
        item = values.get(field)
        if not item:
            continue

        label, value = item
        if value is None or value == "":
            continue

        current_kind = "prompt" if field in ("positive_prompt", "negative_prompt", "video_prompt", "audio_prompt", "lyrics") else "meta"

        # Insert a blank line when switching between prompt blocks and metadata blocks,
        # which makes long prompts much easier to scan in Eagle.
        if lines and previous_kind is not None and current_kind != previous_kind:
            lines.append("")

        if current_kind == "prompt":
            if lines and previous_kind == "prompt":
                lines.append("")
            lines.append(f"{label}:")
            lines.append(str(value).strip())
        else:
            lines.append(f"{label}: {value}")

        previous_kind = current_kind

    return "\n".join(lines).strip()

def merge_annotation(memo_text, generated_annotation):
    memo = (memo_text or "").strip()
    auto_text = (generated_annotation or "").strip()

    parts = []
    if auto_text:
        parts.append(auto_text)

    if memo:
        if parts:
            parts.append("")
        parts.append("Memo:")
        parts.append(memo)

    return "\n".join(parts).strip()

def model_name_tags(metadata: dict | None) -> list[str]:
    metadata = metadata or {}
    return ordered_unique((metadata.get("model_names") or [])[:1])



def audio_batch_to_float32(waveform):
    if hasattr(waveform, "detach"):
        array = waveform.detach().cpu().float().numpy()
    else:
        array = np.asarray(waveform, dtype=np.float32)

    if array.ndim == 1:
        array = array[None, None, :]
    elif array.ndim == 2:
        array = array[None, :, :]
    elif array.ndim != 3:
        raise RuntimeError(f"Unsupported AUDIO waveform shape: {array.shape}")

    array = np.nan_to_num(array, nan=0.0, posinf=1.0, neginf=-1.0)
    array = np.clip(array, -1.0, 1.0).astype(np.float32, copy=False)
    return [batch for batch in array]


def write_wav_float(path: str, waveform_cs: np.ndarray, sample_rate: int):
    pcm = (waveform_cs.T * 32767.0).round().astype(np.int16)
    channels = 1 if pcm.ndim == 1 else pcm.shape[1]

    with wave.open(path, "wb") as wav:
        wav.setnchannels(int(channels))
        wav.setsampwidth(2)
        wav.setframerate(int(sample_rate))
        wav.writeframes(pcm.astype("<i2", copy=False).tobytes())


def parse_bitrate(bitrate: str) -> int:
    text = str(bitrate or "192k").strip().lower()
    if text.endswith("k"):
        return int(float(text[:-1]) * 1000)
    return int(text)


def opus_sample_rate(source_rate: int) -> int:
    supported = [8000, 12000, 16000, 24000, 48000]

    if source_rate in supported:
        return source_rate

    if source_rate > 48000:
        return 48000

    for rate in supported:
        if rate > source_rate:
            return rate

    return 48000


def resample_audio_if_needed(
    waveform_cs: np.ndarray,
    source_rate: int,
    target_rate: int,
) -> np.ndarray:
    if source_rate == target_rate:
        return waveform_cs

    if torch is None or torchaudio is None:
        raise RuntimeError(
            "Opus requires a supported sample rate and torchaudio is unavailable "
            f"for resampling ({source_rate} Hz -> {target_rate} Hz)."
        )

    tensor = torch.from_numpy(waveform_cs)
    resampled = torchaudio.functional.resample(
        tensor,
        int(source_rate),
        int(target_rate),
    )
    return resampled.cpu().numpy().astype(np.float32, copy=False)


def write_compressed_audio(
    path: str,
    waveform_cs: np.ndarray,
    sample_rate: int,
    fmt: str,
    bitrate: str,
):
    if av is None:
        raise RuntimeError(
            f"PyAV is required to save {fmt.upper()} audio, but it could not be imported."
        )

    fmt = fmt.lower()
    target_rate = int(sample_rate)
    working = waveform_cs

    if fmt == "opus":
        target_rate = opus_sample_rate(target_rate)
        working = resample_audio_if_needed(
            working,
            int(sample_rate),
            target_rate,
        )

    channels = int(working.shape[0])
    if channels not in (1, 2):
        raise RuntimeError(
            f"{fmt.upper()} export currently supports mono or stereo audio; "
            f"received {channels} channels."
        )

    layout = "mono" if channels == 1 else "stereo"

    if fmt == "mp3":
        codec = "libmp3lame"
    elif fmt == "opus":
        codec = "libopus"
    elif fmt == "flac":
        codec = "flac"
    else:
        raise RuntimeError(f"Unsupported compressed audio format: {fmt}")

    container = av.open(path, mode="w", format=fmt)

    try:
        stream = container.add_stream(
            codec,
            rate=target_rate,
            layout=layout,
        )

        if fmt in ("mp3", "opus"):
            stream.bit_rate = parse_bitrate(bitrate)

        # Match ComfyUI's own AudioSaveHelper packing approach:
        # channels x samples -> packed interleaved float samples.
        packed = (
            np.ascontiguousarray(working.T)
            .reshape(1, -1)
            .astype(np.float32, copy=False)
        )

        frame = av.AudioFrame.from_ndarray(
            packed,
            format="flt",
            layout=layout,
        )
        frame.sample_rate = target_rate
        frame.pts = 0

        packets = stream.encode(frame)
        if packets:
            container.mux(packets)

        packets = stream.encode(None)
        if packets:
            container.mux(packets)
    finally:
        container.close()


def write_audio_file(
    path: str,
    waveform_cs: np.ndarray,
    sample_rate: int,
    fmt: str,
    bitrate: str,
):
    fmt = fmt.lower()

    if fmt == "wav":
        write_wav_float(path, waveform_cs, sample_rate)
        return

    if fmt in ("flac", "mp3", "opus"):
        write_compressed_audio(
            path,
            waveform_cs,
            sample_rate,
            fmt,
            bitrate,
        )
        return

    raise RuntimeError(f"Unsupported audio format: {fmt}")


class EagleSaveImage:
    @classmethod
    def INPUT_TYPES(cls):
        return {
            "required": {
                "image": ("IMAGE",),
                "eagle_folder_id": eagle_folder_id_input(),
                "file_name_template": (
                    "STRING",
                    {
                        "default": "%datetime%_%rand%",
                        "multiline": False,
                        "tooltip": "Supports %date%, %time%, %datetime%, %index%, %rand%.",
                    },
                ),
                "local_subfolder": (
                    "STRING",
                    {
                        "default": "EagleBridge/Image/%date%/",
                        "multiline": False,
                        "tooltip": "Supports %date%, %time%, %datetime%, %model%.",
                    },
                ),
                "format": (["webp", "png", "jpg"], {"default": "webp"}),
                "quality": ("INT", {"default": 95, "min": 1, "max": 100, "step": 1}),
                "lossless_webp": ("BOOLEAN", {"default": False}),
                "save_local_copy": ("BOOLEAN", {"default": True}),
                "preview": ("BOOLEAN", {"default": True}),
                "memo": ("STRING", {"default": "", "multiline": True}),
                "website": ("STRING", {"default": "", "multiline": False}),
            },
            "hidden": {
                "prompt": "PROMPT",
                "extra_pnginfo": "EXTRA_PNGINFO",
                "unique_id": "UNIQUE_ID",
            },
        }

    RETURN_TYPES = ()
    FUNCTION = "run"
    CATEGORY = "EagleBridge"
    OUTPUT_NODE = True

    def run(
        self,
        image,
        eagle_folder_id,
        file_name_template,
        local_subfolder,
        format,
        quality,
        lossless_webp,
        save_local_copy,
        preview,
        memo,
        website,
        prompt=None,
        extra_pnginfo=None,
        unique_id=None,
    ):
        folder_id = normalize_eagle_folder_id(eagle_folder_id)
        prompt_graph = normalize_prompt(prompt)
        metadata = extract_sampler_metadata(prompt_graph, unique_id)

        output_root = folder_paths.get_output_directory()
        temp_root = folder_paths.get_temp_directory()

        resolved_local_subfolder = render_subfolder_template(
            local_subfolder,
            metadata,
            "EagleBridge/Image/%date%/",
        )
        output_dir, output_subfolder = safe_subfolder(
            output_root, resolved_local_subfolder, "EagleBridge/Image"
        )
        temp_dir, temp_subfolder = safe_subfolder(
            temp_root, "EagleBridge", "EagleBridge"
        )

        previews: list[dict] = []
        batch_count = int(image.shape[0])
        height = int(image.shape[1]) if image.ndim >= 3 else None
        width = int(image.shape[2]) if image.ndim >= 3 else None

        for index in range(batch_count):
            pil_image = tensor_to_pil(image[index])
            base_name = render_template(file_name_template, index)
            ext = format.lower()

            filename = (
                f"{base_name}_{index:02d}.{ext}"
                if batch_count > 1
                else f"{base_name}.{ext}"
            )

            if save_local_copy:
                file_path = unique_path(output_dir, filename)
                preview_type = "output"
                preview_subfolder = output_subfolder
            else:
                file_path = unique_path(temp_dir, filename)
                preview_type = "temp"
                preview_subfolder = temp_subfolder

            save_pil_image(
                pil_image,
                file_path,
                ext,
                int(quality),
                prompt=prompt,
                extra_pnginfo=extra_pnginfo,
                embed_workflow=True,
                lossless_webp=bool(lossless_webp),
            )

            final_tags = model_name_tags(metadata)

            final_annotation = merge_annotation(
                memo,
                build_annotation(
                    media_type="Image",
                    file_format=ext,
                    filename=os.path.basename(file_path),
                    width=width,
                    height=height,
                    metadata=metadata,
                    annotation_order=FIXED_IMAGE_ANNOTATION_ORDER,
                ),
            )

            item_name = os.path.splitext(os.path.basename(file_path))[0]
            add_item_from_path(
                file_path,
                name=item_name,
                tags=final_tags,
                annotation=final_annotation,
                folder_id=folder_id,
                website=(website or "").strip(),
            )

            if preview:
                previews.append(
                    {
                        "filename": os.path.basename(file_path),
                        "subfolder": preview_subfolder,
                        "type": preview_type,
                    }
                )

        result = {"result": ()}
        if preview:
            result["ui"] = {"images": previews}
        return result


class EagleSaveAudio:
    @classmethod
    def INPUT_TYPES(cls):
        return {
            "required": {
                "audio": ("AUDIO",),
                "eagle_folder_id": eagle_folder_id_input(),
                "file_name_template": (
                    "STRING",
                    {
                        "default": "%datetime%_%rand%",
                        "multiline": False,
                        "tooltip": "Supports %date%, %time%, %datetime%, %index%, %rand%.",
                    },
                ),
                "local_subfolder": (
                    "STRING",
                    {
                        "default": "EagleBridge/Audio/%date%/",
                        "multiline": False,
                        "tooltip": "Supports %date%, %time%, %datetime%, %model%.",
                    },
                ),
                "format": (
                    ["wav", "flac", "mp3", "opus"],
                    {"default": "wav"},
                ),
                "bitrate": (
                    ["64k", "96k", "128k", "192k", "256k", "320k"],
                    {
                        "default": "192k",
                        "tooltip": "Used by MP3/Opus. WAV and FLAC are lossless and ignore this setting.",
                    },
                ),
                "save_local_copy": ("BOOLEAN", {"default": True}),
                "preview": (
                    "BOOLEAN",
                    {
                        "default": True,
                        "tooltip": "Show ComfyUI's audio player after saving.",
                    },
                ),
                "memo": ("STRING", {"default": "", "multiline": True}),
                "website": ("STRING", {"default": "", "multiline": False}),
            },
            "hidden": {
                "prompt": "PROMPT",
                "unique_id": "UNIQUE_ID",
            },
        }

    RETURN_TYPES = ("AUDIO",)
    RETURN_NAMES = ("audio",)
    FUNCTION = "run"
    CATEGORY = "EagleBridge"
    OUTPUT_NODE = True

    def run(
        self,
        audio,
        eagle_folder_id,
        file_name_template,
        local_subfolder,
        format,
        bitrate,
        save_local_copy,
        preview,
        memo,
        website,
        prompt=None,
        unique_id=None,
    ):
        if not isinstance(audio, dict) or "waveform" not in audio or "sample_rate" not in audio:
            raise RuntimeError(
                "Unsupported AUDIO object. Expected ComfyUI AUDIO with waveform and sample_rate."
            )

        source_sample_rate = int(audio["sample_rate"])
        batches = audio_batch_to_float32(audio["waveform"])
        channel_count = int(batches[0].shape[0]) if batches else 0

        folder_id = normalize_eagle_folder_id(eagle_folder_id)
        prompt_graph = normalize_prompt(prompt)
        metadata = build_audio_metadata(prompt_graph, unique_id)

        output_root = folder_paths.get_output_directory()
        temp_root = folder_paths.get_temp_directory()

        resolved_local_subfolder = render_subfolder_template(
            local_subfolder,
            metadata,
            "EagleBridge/Audio/%date%/",
        )
        output_dir, output_subfolder = safe_subfolder(
            output_root,
            resolved_local_subfolder,
            "EagleBridge/Audio",
        )
        temp_dir, temp_subfolder = safe_subfolder(
            temp_root,
            "EagleBridge/Audio",
            "EagleBridge/Audio",
        )

        audio_previews = []
        fmt = str(format).lower()

        for index, waveform_cs in enumerate(batches):
            base_name = render_template(file_name_template, index)
            filename = (
                f"{base_name}_{index:02d}.{fmt}"
                if len(batches) > 1
                else f"{base_name}.{fmt}"
            )

            if save_local_copy:
                target_dir = output_dir
                preview_type = "output"
                preview_subfolder = output_subfolder
            else:
                target_dir = temp_dir
                preview_type = "temp"
                preview_subfolder = temp_subfolder

            file_path = unique_path(target_dir, filename)

            write_audio_file(
                file_path,
                waveform_cs,
                source_sample_rate,
                fmt,
                bitrate,
            )

            duration = (
                float(waveform_cs.shape[1]) / float(source_sample_rate)
                if source_sample_rate > 0
                else None
            )

            final_tags = model_name_tags(metadata)

            final_annotation = merge_annotation(
                memo,
                build_annotation(
                    media_type="Audio",
                    file_format=fmt,
                    filename=os.path.basename(file_path),
                    sample_rate=source_sample_rate,
                    channels=channel_count,
                    duration_seconds=duration,
                    metadata=metadata,
                    annotation_order=FIXED_AUDIO_ANNOTATION_ORDER,
                ),
            )

            item_name = os.path.splitext(os.path.basename(file_path))[0]
            add_item_from_path(
                file_path,
                name=item_name,
                tags=final_tags,
                annotation=final_annotation,
                folder_id=folder_id,
                website=(website or "").strip(),
            )

            if preview:
                audio_previews.append(
                    {
                        "filename": os.path.basename(file_path),
                        "subfolder": preview_subfolder,
                        "type": preview_type,
                    }
                )

        result = {"result": (audio,)}
        if preview:
            result["ui"] = {"audio": audio_previews}
        return result


class EagleSaveVideo:
    @classmethod
    def INPUT_TYPES(cls):
        return {
            "required": {
                "video": ("VIDEO",),
                "eagle_folder_id": eagle_folder_id_input(),
                "file_name_template": (
                    "STRING",
                    {
                        "default": "%datetime%_%rand%",
                        "multiline": False,
                        "tooltip": "Supports %date%, %time%, %datetime%, %index%, %rand%.",
                    },
                ),
                "local_subfolder": (
                    "STRING",
                    {
                        "default": "EagleBridge/Video/%date%/",
                        "multiline": False,
                        "tooltip": "Supports %date%, %time%, %datetime%, %model%.",
                    },
                ),
                "format": (
                    ["mp4", "webm", "mkv"],
                    {"default": "mp4"},
                ),
                "codec": (
                    ["auto", "h264", "av1"],
                    {"default": "auto"},
                ),
                "save_local_copy": ("BOOLEAN", {"default": True}),
                "preview": (
                    "BOOLEAN",
                    {
                        "default": True,
                        "tooltip": "Show an in-node video player after saving.",
                    },
                ),
                "memo": ("STRING", {"default": "", "multiline": True}),
                "website": ("STRING", {"default": "", "multiline": False}),
            },
            "hidden": {
                "prompt": "PROMPT",
                "extra_pnginfo": "EXTRA_PNGINFO",
                "unique_id": "UNIQUE_ID",
            },
        }

    RETURN_TYPES = ("VIDEO",)
    RETURN_NAMES = ("video",)
    FUNCTION = "run"
    CATEGORY = "EagleBridge"
    OUTPUT_NODE = True

    def run(
        self,
        video,
        eagle_folder_id,
        file_name_template,
        local_subfolder,
        format,
        codec,
        save_local_copy,
        preview,
        memo,
        website,
        prompt=None,
        extra_pnginfo=None,
        unique_id=None,
    ):
        if ComfyTypes is None:
            raise RuntimeError(
                "ComfyUI VIDEO API could not be imported. "
                "This node requires a current ComfyUI build with native VIDEO support."
            )

        if not hasattr(video, "save_to"):
            raise RuntimeError(
                "The connected value is not a native ComfyUI VIDEO object "
                "(missing save_to())."
            )

        folder_id = normalize_eagle_folder_id(eagle_folder_id)
        prompt_graph = normalize_prompt(prompt)
        metadata = build_video_metadata(prompt_graph, unique_id)

        output_root = folder_paths.get_output_directory()
        temp_root = folder_paths.get_temp_directory()

        resolved_local_subfolder = render_subfolder_template(
            local_subfolder,
            metadata,
            "EagleBridge/Video/%date%/",
        )
        output_dir, output_subfolder = safe_subfolder(
            output_root,
            resolved_local_subfolder,
            "EagleBridge/Video",
        )
        temp_dir, temp_subfolder = safe_subfolder(
            temp_root,
            "EagleBridge/Video",
            "EagleBridge/Video",
        )

        fmt = str(format).lower()
        codec_name = str(codec).lower()

        if fmt == "webm" and codec_name == "h264":
            raise RuntimeError(
                "WebM does not support H.264 in this node. "
                "Choose codec 'auto' or 'av1'."
            )

        base_name = render_template(file_name_template, 0)
        filename = f"{base_name}.{fmt}"

        if save_local_copy:
            target_dir = output_dir
            preview_type = "output"
            preview_subfolder = output_subfolder
        else:
            target_dir = temp_dir
            preview_type = "temp"
            preview_subfolder = temp_subfolder

        file_path = unique_path(target_dir, filename)

        embedded_metadata = None
        metadata_disabled = bool(
            comfy_args is not None
            and getattr(comfy_args, "disable_metadata", False)
        )
        if not metadata_disabled:
            embedded_metadata = {}
            if isinstance(extra_pnginfo, dict):
                embedded_metadata.update(extra_pnginfo)
            if prompt is not None:
                embedded_metadata["prompt"] = prompt
            if not embedded_metadata:
                embedded_metadata = None

        video.save_to(
            file_path,
            format=ComfyTypes.VideoContainer(fmt),
            codec=ComfyTypes.VideoCodec(codec_name),
            metadata=embedded_metadata,
        )

        width = height = None
        duration = None
        fps = None

        try:
            width, height = video.get_dimensions()
        except Exception:
            pass

        try:
            duration = float(video.get_duration())
        except Exception:
            pass

        try:
            fps = float(video.get_frame_rate())
        except Exception:
            pass

        final_tags = model_name_tags(metadata)

        final_annotation = merge_annotation(
            memo,
            build_annotation(
                media_type="Video",
                file_format=fmt,
                filename=os.path.basename(file_path),
                width=width,
                height=height,
                duration_seconds=duration,
                fps=fps,
                metadata=metadata,
                annotation_order=FIXED_VIDEO_ANNOTATION_ORDER,
            ),
        )

        item_name = os.path.splitext(os.path.basename(file_path))[0]
        add_item_from_path(
            file_path,
            name=item_name,
            tags=final_tags,
            annotation=final_annotation,
            folder_id=folder_id,
            website=(website or "").strip(),
        )

        result = {"result": (video,)}
        if preview:
            result["ui"] = {
                "video": [
                    {
                        "filename": os.path.basename(file_path),
                        "subfolder": preview_subfolder,
                        "type": preview_type,
                    }
                ]
            }
        return result


NODE_CLASS_MAPPINGS = {
    "EagleSaveImage": EagleSaveImage,
    "EagleSaveAudio": EagleSaveAudio,
    "EagleSaveVideo": EagleSaveVideo,
}

NODE_DISPLAY_NAME_MAPPINGS = {
    "EagleSaveImage": "Eagle Save Image",
    "EagleSaveAudio": "Eagle Save Audio",
    "EagleSaveVideo": "Eagle Save Video",
}
