import os
import weakref

import folder_paths

try:
    from comfy_api.latest import Types as ComfyTypes
except Exception:
    ComfyTypes = None


_PREVIEW_RESULTS = weakref.WeakKeyDictionary()


def _make_video_preview_ref(video):
    """Create (or reuse) a temporary MP4 preview for a native ComfyUI VIDEO."""
    try:
        cached = _PREVIEW_RESULTS.get(video)
    except TypeError:
        cached = None

    if cached is not None and os.path.isfile(cached[0]):
        return cached[1]

    if ComfyTypes is None:
        raise RuntimeError(
            "Video Preview requires a current ComfyUI build with the native VIDEO API."
        )

    full_output_folder, filename, counter, subfolder, _ = folder_paths.get_save_image_path(
        "EagleBridge_video_preview",
        folder_paths.get_temp_directory(),
        0,
        0,
    )

    preview_format = ComfyTypes.VideoContainer.MP4
    extension = ComfyTypes.VideoContainer.get_extension(preview_format)
    file = f"{filename}_{counter:05}_.{extension}"
    full_path = os.path.join(full_output_folder, file)

    video.save_to(
        full_path,
        format=preview_format,
        codec="auto",
        preset="ultrafast",
    )

    preview_ref = {
        "filename": file,
        "subfolder": subfolder,
        "type": "temp",
    }

    try:
        _PREVIEW_RESULTS[video] = (full_path, preview_ref)
    except TypeError:
        # Some third-party VIDEO implementations may not support weak references.
        pass

    return preview_ref


class EagleVideoPreview:
    @classmethod
    def INPUT_TYPES(cls):
        return {
            "required": {
                "video": ("VIDEO",),
            },
        }

    RETURN_TYPES = ("VIDEO",)
    RETURN_NAMES = ("video",)
    FUNCTION = "run"
    CATEGORY = "EagleBridge"
    OUTPUT_NODE = True

    def run(self, video):
        preview_ref = _make_video_preview_ref(video)
        return {
            "ui": {"video": [preview_ref]},
            "result": (video,),
        }


NODE_CLASS_MAPPINGS = {
    "EagleVideoPreview": EagleVideoPreview,
}

NODE_DISPLAY_NAME_MAPPINGS = {
    "EagleVideoPreview": "Video Preview",
}
