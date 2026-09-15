import os
import unicodedata
from typing import Any

import requests

from .config import (
    EAGLE_ADD_TIMEOUT,
    EAGLE_HOST,
    EAGLE_LIST_TIMEOUT,
    EAGLE_OFFLINE_OPTION,
    EAGLE_PORT,
    LIBRARY_ROOT_OPTION,
)


def make_base_url(host: str = EAGLE_HOST, port: int = EAGLE_PORT) -> str:
    return f"http://{host}:{int(port)}/api"


def _normalize_text(value: Any) -> str:
    text = "" if value is None else str(value)
    text = unicodedata.normalize("NFC", text).strip()
    text = text.replace("\\", "/")
    while "//" in text:
        text = text.replace("//", "/")
    return text.strip("/")


def _extract_error(data: Any, fallback: str) -> str:
    if isinstance(data, dict):
        for key in ("message", "error", "msg"):
            value = data.get(key)
            if value:
                return str(value)
    return fallback


def _request_json(method: str, url: str, *, timeout: int, **kwargs) -> dict:
    try:
        response = requests.request(method, url, timeout=timeout, **kwargs)
        response.raise_for_status()
    except requests.RequestException as exc:
        raise RuntimeError(
            f"Could not connect to Eagle API at {make_base_url()}. "
            f"Make sure Eagle is running and a library is open. ({exc})"
        ) from exc

    try:
        data = response.json()
    except ValueError as exc:
        raise RuntimeError(
            f"Eagle API returned a non-JSON response: HTTP {response.status_code}"
        ) from exc

    if not isinstance(data, dict):
        raise RuntimeError("Eagle API returned an unexpected response.")

    if data.get("status") != "success":
        raise RuntimeError(_extract_error(data, "Eagle API request failed."))

    return data


def get_folder_list(
    host: str = EAGLE_HOST,
    port: int = EAGLE_PORT,
    timeout: int = EAGLE_LIST_TIMEOUT,
) -> list[dict]:
    url = f"{make_base_url(host, port)}/folder/list"
    data = _request_json("GET", url, timeout=timeout)
    folders = data.get("data") or []
    if not isinstance(folders, list):
        raise RuntimeError("Eagle folder/list returned an invalid folder list.")
    return folders


def flatten_folders(folders: list[dict], parent_path: str = "") -> list[dict]:
    result: list[dict] = []

    for folder in folders:
        if not isinstance(folder, dict):
            continue

        name = _normalize_text(folder.get("name", ""))
        folder_id = str(folder.get("id", "") or "").strip()

        if not name or not folder_id:
            continue

        current_path = f"{parent_path}/{name}" if parent_path else name

        result.append({
            "id": folder_id,
            "name": name,
            "path": current_path,
        })

        children = folder.get("children") or []
        if isinstance(children, list) and children:
            result.extend(flatten_folders(children, current_path))

    return result


def get_folder_options() -> list[str]:
    folders = flatten_folders(get_folder_list())
    return [LIBRARY_ROOT_OPTION] + [folder["path"] for folder in folders]


def resolve_folder_id(folder_value: str) -> str | None:
    value = _normalize_text(folder_value)

    if not value or value == _normalize_text(LIBRARY_ROOT_OPTION):
        return None

    if value == _normalize_text(EAGLE_OFFLINE_OPTION):
        raise RuntimeError(
            "Eagle is not connected. Start Eagle, open a library, "
            "then refresh the Eagle folder list."
        )

    folders = flatten_folders(get_folder_list())

    # Exact folder ID.
    for folder in folders:
        if value == folder["id"]:
            return folder["id"]

    wanted = value.casefold()

    # Exact full path.
    path_matches = [
        folder for folder in folders
        if _normalize_text(folder["path"]).casefold() == wanted
    ]
    if len(path_matches) == 1:
        return path_matches[0]["id"]

    # Exact unique name, for compatibility with older workflows.
    name_matches = [
        folder for folder in folders
        if _normalize_text(folder["name"]).casefold() == wanted
    ]
    if len(name_matches) == 1:
        return name_matches[0]["id"]

    if len(name_matches) > 1:
        candidates = ", ".join(folder["path"] for folder in name_matches[:10])
        raise RuntimeError(
            f"Eagle folder name is ambiguous: '{folder_value}'. "
            f"Choose the full path. Candidates: {candidates}"
        )

    raise RuntimeError(
        f"Eagle folder not found: '{folder_value}'. "
        "Refresh the Eagle folder list and select it again."
    )


def add_item_from_path(
    file_path: str,
    *,
    name: str | None = None,
    tags: list[str] | None = None,
    annotation: str = "",
    folder_id: str | None = None,
    website: str = "",
    host: str = EAGLE_HOST,
    port: int = EAGLE_PORT,
    timeout: int = EAGLE_ADD_TIMEOUT,
) -> dict:
    abs_path = os.path.abspath(file_path)

    if not os.path.isfile(abs_path):
        raise FileNotFoundError(abs_path)

    item_name = (name or os.path.splitext(os.path.basename(abs_path))[0]).strip()
    if not item_name:
        item_name = os.path.basename(abs_path)

    payload: dict[str, Any] = {
        "path": abs_path,
        "name": item_name,
    }

    if tags:
        payload["tags"] = tags
    if annotation:
        payload["annotation"] = annotation
    if folder_id:
        payload["folderId"] = folder_id
    if website:
        payload["website"] = website

    url = f"{make_base_url(host, port)}/item/addFromPath"
    data = _request_json("POST", url, timeout=timeout, json=payload)
    return data.get("data") or {}
