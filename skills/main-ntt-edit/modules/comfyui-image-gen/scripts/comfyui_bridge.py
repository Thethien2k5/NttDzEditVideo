#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
ComfyUI Local API Bridge for comfyui-image-gen.
- Auto-starts E:\EDIT\Photoshop\run_comfyui.bat in background if 127.0.0.1:8188 is down.
- Isolates all generated outputs & configs inside <PROJECT_DIR>\temp_assets\comfyui\batch_XX\
  (auto-incrementing batch_01, batch_02...) for easy cleanup and zero overwrites.
- Supports Text-to-Image (t2i), Multi-Image Editing/Compositing (edit),
  Custom Node Graphs (graph), Batch Execution, and Live Node Inspection.
- Designed for Qwen-Image 2.1 GGUF + Qwen3-VL 8B on RTX 3060 6GB VRAM.
- Zero third-party dependencies (Python standard library only).
"""

import argparse
import copy
import json
import mimetypes
import os
import random
import re
import subprocess
import sys
import time
import urllib.error
import urllib.parse
import urllib.request
import uuid
from pathlib import Path

DEFAULT_BAT_PATH = r"E:\EDIT\Photoshop\run_comfyui.bat"
DEFAULT_HOST = "127.0.0.1"
DEFAULT_PORT = 8188

DEFAULT_UNET = "qwen-image-2.1-UC-Q4_K_M.gguf"
DEFAULT_CLIP = "qwen3vl_8b_int8_convrot.safetensors"
DEFAULT_VAE = "qwen_image_2.1_vae_bf16.safetensors"

ASPECT_PRESETS = {
    "16:9": (1280, 720),
    "9:16": (720, 1280),
    "1:1": (1024, 1024),
    "4:3": (1152, 864),
    "3:4": (864, 1152),
}


def allocate_batch_dir(project_dir: str) -> str:
    """
    Creates and returns <PROJECT_DIR>\temp_assets\comfyui\batch_XX
    with auto-incrementing XX (batch_01, batch_02...) so assets never collide
    and the whole folder can be deleted cleanly when no longer needed.
    """
    base_comfy_dir = os.path.join(os.path.abspath(project_dir), "temp_assets", "comfyui")
    os.makedirs(base_comfy_dir, exist_ok=True)

    max_idx = 0
    for entry in os.listdir(base_comfy_dir):
        m = re.fullmatch(r"batch_(\d+)", entry)
        if m:
            max_idx = max(max_idx, int(m.group(1)))

    next_dir = os.path.join(base_comfy_dir, f"batch_{max_idx + 1:02d}")
    os.makedirs(next_dir, exist_ok=True)
    return next_dir


def resolve_path_in_batch(raw_path: str, batch_dir: str | None) -> str:
    """If raw_path is relative and batch_dir is set, resolves it inside batch_dir."""
    if os.path.isabs(raw_path) or not batch_dir:
        return os.path.abspath(raw_path)
    return os.path.join(batch_dir, raw_path)


def http_json(url: str, payload: dict | None = None, timeout: float = 20.0) -> dict:
    data = None
    headers = {}
    if payload is not None:
        data = json.dumps(payload).encode("utf-8")
        headers["Content-Type"] = "application/json"
    req = urllib.request.Request(url, data=data, headers=headers)
    with urllib.request.urlopen(req, timeout=timeout) as resp:
        raw = resp.read().decode("utf-8")
        return json.loads(raw) if raw.strip() else {}


def is_server_alive(base_url: str) -> bool:
    try:
        http_json(f"{base_url}/system_stats", timeout=3.0)
        return True
    except Exception:
        return False


def ensure_comfyui_running(
    base_url: str,
    bat_path: str,
    auto_start: bool,
    startup_timeout: int = 120,
) -> bool:
    """Checks ComfyUI API; starts E:\\EDIT\\Photoshop\\run_comfyui.bat in background if needed."""
    if is_server_alive(base_url):
        print(f"[ComfyUI] Backend da san sang tai {base_url}")
        return False

    if not auto_start:
        raise RuntimeError(
            f"ComfyUI chua chay tai {base_url} va --no-auto-start dang duoc bat."
        )

    if not os.path.isfile(bat_path):
        raise FileNotFoundError(f"Khong tim thay file khoi chay: {bat_path}")

    print(f"[ComfyUI] Dang khoi dong ngam qua {bat_path} ...")
    bat_dir = os.path.dirname(os.path.abspath(bat_path))
    log_path = os.path.join(bat_dir, "comfyui_api_background.log")

    # Redirect '< nul' so 'pause' at the end of run_comfyui.bat never hangs
    cmd_str = f'"{bat_path}" < nul > "{log_path}" 2>&1'
    creationflags = 0
    if os.name == "nt":
        creationflags = subprocess.CREATE_NEW_PROCESS_GROUP | subprocess.DETACHED_PROCESS

    subprocess.Popen(
        ["cmd.exe", "/c", cmd_str],
        cwd=bat_dir,
        creationflags=creationflags,
    )

    deadline = time.time() + startup_timeout
    while time.time() < deadline:
        if is_server_alive(base_url):
            elapsed = int(startup_timeout - (deadline - time.time()))
            print(f"[ComfyUI] Khoi dong thanh cong sau {elapsed}s!")
            return True
        time.sleep(2.0)

    raise TimeoutError(
        f"ComfyUI khong phan hoi sau {startup_timeout}s. Kiem tra log tai: {log_path}"
    )


def free_vram(base_url: str) -> None:
    """Unloads models from 6GB VRAM so VSR/VieNeu-TTS/Concat can run safely."""
    try:
        http_json(
            f"{base_url}/free",
            payload={"unload_models": True, "free_memory": True},
            timeout=15.0,
        )
        print("[ComfyUI] Da giai phong VRAM GPU (unload_models + free_memory).")
    except Exception as exc:
        print(f"[ComfyUI] Canh bao: Khong the goi /free ({exc}).")


def upload_image_to_comfy(base_url: str, local_path: str, overwrite: bool = True) -> str:
    """Uploads a local image file to ComfyUI /upload/image using pure stdlib multipart/form-data."""
    abs_path = os.path.abspath(local_path)
    if not os.path.isfile(abs_path):
        raise FileNotFoundError(f"Khong tim thay anh dau vao: {abs_path}")

    filename = os.path.basename(abs_path)
    mime_type = mimetypes.guess_type(abs_path)[0] or "image/png"
    boundary = f"----NttComfyBoundary{uuid.uuid4().hex}"

    with open(abs_path, "rb") as f:
        file_bytes = f.read()

    parts = [
        f"--{boundary}\r\n".encode("utf-8"),
        f'Content-Disposition: form-data; name="image"; filename="{filename}"\r\n'.encode("utf-8"),
        f"Content-Type: {mime_type}\r\n\r\n".encode("utf-8"),
        file_bytes,
        b"\r\n",
        f"--{boundary}\r\n".encode("utf-8"),
        b'Content-Disposition: form-data; name="overwrite"\r\n\r\n',
        b"true\r\n" if overwrite else b"false\r\n",
        f"--{boundary}--\r\n".encode("utf-8"),
    ]
    body = b"".join(parts)

    req = urllib.request.Request(
        f"{base_url}/upload/image",
        data=body,
        headers={"Content-Type": f"multipart/form-data; boundary={boundary}"},
        method="POST",
    )
    with urllib.request.urlopen(req, timeout=30.0) as resp:
        res = json.loads(resp.read().decode("utf-8"))

    uploaded_name = res.get("name", filename)
    subfolder = res.get("subfolder", "")
    return f"{subfolder}/{uploaded_name}" if subfolder else uploaded_name


def get_node_info(base_url: str, node_class: str) -> dict | None:
    try:
        data = http_json(f"{base_url}/object_info/{urllib.parse.quote(node_class)}", timeout=10.0)
        return data.get(node_class)
    except Exception:
        return None


def inspect_nodes(base_url: str, keyword: str) -> None:
    all_info = http_json(f"{base_url}/object_info", timeout=20.0)
    kw = keyword.lower()
    matches = [k for k in sorted(all_info.keys()) if kw in k.lower()]
    if not matches:
        print(f"Khong tim thay node nao khop voi '{keyword}'.")
        return

    for name in matches[:25]:
        info = all_info[name]
        req_inputs = info.get("input", {}).get("required", {})
        opt_inputs = info.get("input", {}).get("optional", {})
        outputs = info.get("output", [])
        print(f"=== {name} (display: {info.get('display_name', name)}) ===")
        print(f"  Required inputs: {list(req_inputs.keys())}")
        if opt_inputs:
            print(f"  Optional inputs: {list(opt_inputs.keys())}")
        print(f"  Outputs: {outputs}")


def build_base_loaders(
    base_url: str,
    unet_name: str,
    clip_name: str,
    vae_name: str,
    shift: float,
) -> tuple[dict, list]:
    """Creates model, CLIP, VAE and optional ModelSamplingAuraFlow nodes."""
    wf = {
        "1": {
            "class_type": "UnetLoaderGGUF",
            "inputs": {"unet_name": unet_name},
            "_meta": {"title": "Load Qwen-Image 2.1 GGUF"},
        },
        "2": {
            "class_type": "CLIPLoader",
            "inputs": {
                "clip_name": clip_name,
                "type": "qwen_image",
                "device": "default",
            },
            "_meta": {"title": "Load Qwen3-VL 8B Text Encoder"},
        },
        "3": {
            "class_type": "VAELoader",
            "inputs": {"vae_name": vae_name},
            "_meta": {"title": "Load Qwen-Image 2.1 VAE"},
        },
    }

    if get_node_info(base_url, "ModelSamplingAuraFlow") is not None:
        wf["4"] = {
            "class_type": "ModelSamplingAuraFlow",
            "inputs": {"model": ["1", 0], "shift": shift},
            "_meta": {"title": "ModelSamplingAuraFlow"},
        }
        model_ref = ["4", 0]
    else:
        model_ref = ["1", 0]

    return wf, model_ref


def build_t2i_workflow(
    base_url: str,
    prompt: str,
    negative: str,
    width: int,
    height: int,
    seed: int,
    steps: int,
    cfg: float,
    sampler: str,
    scheduler: str,
    shift: float,
    filename_prefix: str,
) -> dict:
    wf, model_ref = build_base_loaders(
        base_url, DEFAULT_UNET, DEFAULT_CLIP, DEFAULT_VAE, shift
    )

    latent_cls = (
        "EmptySD3LatentImage"
        if get_node_info(base_url, "EmptySD3LatentImage") is not None
        else "EmptyLatentImage"
    )

    wf["5"] = {
        "class_type": "CLIPTextEncode",
        "inputs": {"text": prompt, "clip": ["2", 0]},
        "_meta": {"title": "Positive Prompt"},
    }
    wf["6"] = {
        "class_type": "CLIPTextEncode",
        "inputs": {"text": negative, "clip": ["2", 0]},
        "_meta": {"title": "Negative Prompt"},
    }
    wf["7"] = {
        "class_type": latent_cls,
        "inputs": {"width": width, "height": height, "batch_size": 1},
        "_meta": {"title": "Empty Latent"},
    }
    wf["8"] = {
        "class_type": "KSampler",
        "inputs": {
            "model": model_ref,
            "positive": ["5", 0],
            "negative": ["6", 0],
            "latent_image": ["7", 0],
            "seed": seed,
            "steps": steps,
            "cfg": cfg,
            "sampler_name": sampler,
            "scheduler": scheduler,
            "denoise": 1.0,
        },
        "_meta": {"title": "KSampler"},
    }
    wf["9"] = {
        "class_type": "VAEDecode",
        "inputs": {"samples": ["8", 0], "vae": ["3", 0]},
        "_meta": {"title": "VAE Decode"},
    }
    wf["10"] = {
        "class_type": "SaveImage",
        "inputs": {"filename_prefix": filename_prefix, "images": ["9", 0]},
        "_meta": {"title": "Save Image"},
    }
    return wf


def build_edit_workflow(
    base_url: str,
    uploaded_images: list[str],
    prompt: str,
    negative: str,
    width: int | None,
    height: int | None,
    seed: int,
    steps: int,
    cfg: float,
    sampler: str,
    scheduler: str,
    denoise: float,
    shift: float,
    filename_prefix: str,
) -> dict:
    """
    Dynamically constructs a Qwen-Image 2.1 multi-image editing / compositing graph
    based on live ComfyUI node capabilities.
    """
    wf, model_ref = build_base_loaders(
        base_url, DEFAULT_UNET, DEFAULT_CLIP, DEFAULT_VAE, shift
    )

    has_scale_node = get_node_info(base_url, "ImageScaleToTotalPixels") is not None
    scaled_refs = []
    next_id = 10

    for idx, img_name in enumerate(uploaded_images[:3], start=1):
        load_id = str(next_id)
        next_id += 1
        wf[load_id] = {
            "class_type": "LoadImage",
            "inputs": {"image": img_name},
            "_meta": {"title": f"Load Input Image {idx}"},
        }
        if has_scale_node:
            scale_id = str(next_id)
            next_id += 1
            wf[scale_id] = {
                "class_type": "ImageScaleToTotalPixels",
                "inputs": {
                    "image": [load_id, 0],
                    "upscale_method": "lanczos",
                    "megapixels": 1.0,
                },
                "_meta": {"title": f"Scale Image {idx} (6GB Safe)"},
            }
            scaled_refs.append([scale_id, 0])
        else:
            scaled_refs.append([load_id, 0])

    if width is not None and height is not None:
        latent_id = str(next_id)
        next_id += 1
        latent_cls = (
            "EmptySD3LatentImage"
            if get_node_info(base_url, "EmptySD3LatentImage") is not None
            else "EmptyLatentImage"
        )
        wf[latent_id] = {
            "class_type": latent_cls,
            "inputs": {"width": width, "height": height, "batch_size": 1},
            "_meta": {"title": "Target Aspect Latent"},
        }
        latent_ref = [latent_id, 0]
        effective_denoise = 1.0
    else:
        vae_enc_id = str(next_id)
        next_id += 1
        wf[vae_enc_id] = {
            "class_type": "VAEEncode",
            "inputs": {"pixels": scaled_refs[0], "vae": ["3", 0]},
            "_meta": {"title": "VAE Encode Base Image"},
        }
        latent_ref = [vae_enc_id, 0]
        effective_denoise = denoise

    edit_plus_info = get_node_info(base_url, "TextEncodeQwenImageEditPlus")
    edit_single_info = get_node_info(base_url, "TextEncodeQwenImageEdit")
    has_ref_latent = get_node_info(base_url, "ReferenceLatent") is not None

    if edit_plus_info is not None:
        pos_id = str(next_id)
        neg_id = str(next_id + 1)
        next_id += 2

        pos_inputs = {"clip": ["2", 0], "prompt": prompt, "vae": ["3", 0]}
        neg_inputs = {"clip": ["2", 0], "prompt": negative, "vae": ["3", 0]}
        for idx, ref in enumerate(scaled_refs, start=1):
            pos_inputs[f"image{idx}"] = ref
            neg_inputs[f"image{idx}"] = ref

        wf[pos_id] = {
            "class_type": "TextEncodeQwenImageEditPlus",
            "inputs": pos_inputs,
            "_meta": {"title": "Qwen Edit Plus Positive"},
        }
        wf[neg_id] = {
            "class_type": "TextEncodeQwenImageEditPlus",
            "inputs": neg_inputs,
            "_meta": {"title": "Qwen Edit Plus Negative"},
        }
        pos_ref = [pos_id, 0]
        neg_ref = [neg_id, 0]

    elif edit_single_info is not None:
        pos_id = str(next_id)
        neg_id = str(next_id + 1)
        next_id += 2

        wf[pos_id] = {
            "class_type": "TextEncodeQwenImageEdit",
            "inputs": {
                "clip": ["2", 0],
                "prompt": prompt,
                "vae": ["3", 0],
                "image": scaled_refs[0],
            },
            "_meta": {"title": "Qwen Edit Positive"},
        }
        wf[neg_id] = {
            "class_type": "TextEncodeQwenImageEdit",
            "inputs": {
                "clip": ["2", 0],
                "prompt": negative,
                "vae": ["3", 0],
                "image": scaled_refs[0],
            },
            "_meta": {"title": "Qwen Edit Negative"},
        }
        pos_ref = [pos_id, 0]
        neg_ref = [neg_id, 0]

        if has_ref_latent and len(scaled_refs) > 1:
            for extra_idx, extra_img in enumerate(scaled_refs[1:], start=2):
                enc_id = str(next_id)
                ref_pos_id = str(next_id + 1)
                ref_neg_id = str(next_id + 2)
                next_id += 3
                wf[enc_id] = {
                    "class_type": "VAEEncode",
                    "inputs": {"pixels": extra_img, "vae": ["3", 0]},
                    "_meta": {"title": f"VAE Encode Ref {extra_idx}"},
                }
                wf[ref_pos_id] = {
                    "class_type": "ReferenceLatent",
                    "inputs": {"conditioning": pos_ref, "latent": [enc_id, 0]},
                    "_meta": {"title": f"ReferenceLatent Pos {extra_idx}"},
                }
                wf[ref_neg_id] = {
                    "class_type": "ReferenceLatent",
                    "inputs": {"conditioning": neg_ref, "latent": [enc_id, 0]},
                    "_meta": {"title": f"ReferenceLatent Neg {extra_idx}"},
                }
                pos_ref = [ref_pos_id, 0]
                neg_ref = [ref_neg_id, 0]
    else:
        pos_id = str(next_id)
        neg_id = str(next_id + 1)
        next_id += 2
        wf[pos_id] = {
            "class_type": "CLIPTextEncode",
            "inputs": {"text": prompt, "clip": ["2", 0]},
            "_meta": {"title": "Positive Prompt"},
        }
        wf[neg_id] = {
            "class_type": "CLIPTextEncode",
            "inputs": {"text": negative, "clip": ["2", 0]},
            "_meta": {"title": "Negative Prompt"},
        }
        pos_ref = [pos_id, 0]
        neg_ref = [neg_id, 0]
        if has_ref_latent:
            for idx, img_ref in enumerate(scaled_refs, start=1):
                enc_id = str(next_id)
                ref_pos_id = str(next_id + 1)
                next_id += 2
                wf[enc_id] = {
                    "class_type": "VAEEncode",
                    "inputs": {"pixels": img_ref, "vae": ["3", 0]},
                    "_meta": {"title": f"VAE Encode Ref {idx}"},
                }
                wf[ref_pos_id] = {
                    "class_type": "ReferenceLatent",
                    "inputs": {"conditioning": pos_ref, "latent": [enc_id, 0]},
                    "_meta": {"title": f"ReferenceLatent {idx}"},
                }
                pos_ref = [ref_pos_id, 0]

    ksampler_id = str(next_id)
    decode_id = str(next_id + 1)
    save_id = str(next_id + 2)

    wf[ksampler_id] = {
        "class_type": "KSampler",
        "inputs": {
            "model": model_ref,
            "positive": pos_ref,
            "negative": neg_ref,
            "latent_image": latent_ref,
            "seed": seed,
            "steps": steps,
            "cfg": cfg,
            "sampler_name": sampler,
            "scheduler": scheduler,
            "denoise": effective_denoise,
        },
        "_meta": {"title": "KSampler"},
    }
    wf[decode_id] = {
        "class_type": "VAEDecode",
        "inputs": {"samples": [ksampler_id, 0], "vae": ["3", 0]},
        "_meta": {"title": "VAE Decode"},
    }
    wf[save_id] = {
        "class_type": "SaveImage",
        "inputs": {"filename_prefix": filename_prefix, "images": [decode_id, 0]},
        "_meta": {"title": "Save Image"},
    }
    return wf


def patch_custom_graph(
    graph: dict,
    uploaded_names: list[str],
    prompt: str | None,
    negative: str | None,
    seed: int,
    filename_prefix: str,
) -> dict:
    """Patches uploaded image names, optional prompts, seed and output prefix in a custom graph."""
    wf = copy.deepcopy(graph)

    if uploaded_names:
        load_nodes = [
            nid for nid, n in sorted(wf.items(), key=lambda x: str(x[0]))
            if n.get("class_type") == "LoadImage"
        ]
        for nid, up_name in zip(load_nodes, uploaded_names):
            wf[nid].setdefault("inputs", {})["image"] = up_name

    for nid, node in wf.items():
        ctype = node.get("class_type", "")
        inputs = node.setdefault("inputs", {})
        if ctype in ("KSampler", "KSamplerAdvanced") and "seed" in inputs:
            inputs["seed"] = seed
        elif ctype == "SaveImage":
            inputs["filename_prefix"] = filename_prefix

    if prompt is not None:
        for nid, node in wf.items():
            ctype = node.get("class_type", "")
            title = node.get("_meta", {}).get("title", "").lower()
            if ctype in ("CLIPTextEncode", "TextEncodeQwenImageEdit", "TextEncodeQwenImageEditPlus"):
                if "negative" not in title:
                    key = "prompt" if "prompt" in node.get("inputs", {}) else "text"
                    node["inputs"][key] = prompt
                    break

    if negative is not None:
        for nid, node in wf.items():
            ctype = node.get("class_type", "")
            title = node.get("_meta", {}).get("title", "").lower()
            if ctype in ("CLIPTextEncode", "TextEncodeQwenImageEdit", "TextEncodeQwenImageEditPlus"):
                if "negative" in title:
                    key = "prompt" if "prompt" in node.get("inputs", {}) else "text"
                    node["inputs"][key] = negative
                    break

    return wf


def execute_workflow(base_url: str, wf: dict, output_path: str, timeout: int) -> str:
    client_id = str(uuid.uuid4())
    res = http_json(
        f"{base_url}/prompt",
        payload={"prompt": wf, "client_id": client_id},
        timeout=30.0,
    )
    prompt_id = res.get("prompt_id")
    if not prompt_id:
        raise RuntimeError(f"ComfyUI khong tra ve prompt_id: {res}")

    deadline = time.time() + timeout
    history_item = None
    while time.time() < deadline:
        hist = http_json(f"{base_url}/history/{prompt_id}", timeout=15.0)
        if prompt_id in hist:
            history_item = hist[prompt_id]
            status_str = history_item.get("status", {}).get("status_str", "")
            if status_str == "error":
                raise RuntimeError(f"ComfyUI bao loi thuc thi: {history_item.get('status')}")
            if history_item.get("outputs"):
                break
        time.sleep(1.5)

    if not history_item or not history_item.get("outputs"):
        raise TimeoutError(f"Qua thoi gian cho ({timeout}s) cho prompt_id={prompt_id}")

    saved_img = None
    for node_out in history_item["outputs"].values():
        images = node_out.get("images", [])
        if images:
            saved_img = images[0]
            break

    if not saved_img:
        raise RuntimeError(f"Khong tim thay anh dau ra trong history: {history_item}")

    query = urllib.parse.urlencode(
        {
            "filename": saved_img["filename"],
            "subfolder": saved_img.get("subfolder", ""),
            "type": saved_img.get("type", "output"),
        }
    )
    img_url = f"{base_url}/view?{query}"

    abs_out = os.path.abspath(output_path)
    os.makedirs(os.path.dirname(abs_out), exist_ok=True)
    with urllib.request.urlopen(img_url, timeout=30.0) as resp:
        with open(abs_out, "wb") as f:
            f.write(resp.read())

    print(f"[ComfyUI] Hoan tat: {abs_out}")
    return abs_out


def run_job(
    base_url: str,
    job: dict,
    defaults: argparse.Namespace,
    batch_dir: str | None,
    job_index: int,
) -> str:
    raw_input_images = job.get("input_images") or defaults.input_images or []
    input_images = [resolve_path_in_batch(p, batch_dir) for p in raw_input_images]

    raw_graph_path = job.get("graph_json") or defaults.graph_json
    graph_json_path = resolve_path_in_batch(raw_graph_path, batch_dir) if raw_graph_path else None

    raw_upload_images = job.get("upload_images") or defaults.upload_images or []
    upload_images = [resolve_path_in_batch(p, batch_dir) for p in raw_upload_images]

    mode = job.get("mode") or defaults.mode
    if not mode:
        if graph_json_path:
            mode = "graph"
        elif input_images:
            mode = "edit"
        else:
            mode = "t2i"

    raw_out = job.get("output") or defaults.output or defaults.filename
    if not raw_out:
        if batch_dir:
            raw_out = f"img_{job_index:02d}.png"
        else:
            raise ValueError("Can cung cap --output hoac --project-dir.")

    output_path = resolve_path_in_batch(raw_out, batch_dir)

    prompt = job.get("prompt", defaults.prompt)
    negative = job.get("negative", defaults.negative)

    raw_seed = int(job.get("seed", defaults.seed))
    seed = random.randint(1, 2**31 - 1) if raw_seed < 0 else raw_seed

    steps = int(job.get("steps", defaults.steps))
    cfg = float(job.get("cfg", defaults.cfg))
    sampler = job.get("sampler", defaults.sampler)
    scheduler = job.get("scheduler", defaults.scheduler)
    denoise = float(job.get("denoise", defaults.denoise))
    shift = float(job.get("shift", defaults.shift))
    prefix = f"ntt_comfy_temp/gen_{uuid.uuid4().hex[:8]}"

    aspect = job.get("aspect", defaults.aspect)
    width = job.get("width") or defaults.width
    height = job.get("height") or defaults.height
    if (width is None or height is None) and aspect:
        preset_w, preset_h = ASPECT_PRESETS.get(aspect, (1280, 720))
        width = width or preset_w
        height = height or preset_h

    if mode == "graph":
        if not graph_json_path or not os.path.isfile(graph_json_path):
            raise FileNotFoundError(f"Khong tim thay file graph JSON: {graph_json_path}")
        with open(graph_json_path, "r", encoding="utf-8") as f:
            raw_graph = json.load(f)
        uploaded_names = [upload_image_to_comfy(base_url, p) for p in upload_images]
        wf = patch_custom_graph(raw_graph, uploaded_names, prompt, negative, seed, prefix)
        print(f"[ComfyUI] Chay Custom Graph ({graph_json_path}, seed={seed}) -> {output_path}")

    elif mode == "edit":
        if not input_images:
            raise ValueError("Che do 'edit' can it nhat 1 anh trong --input-images.")
        if not prompt:
            raise ValueError("Che do 'edit' can --prompt mo ta yeu cau chinh sua/ghep anh.")
        uploaded_names = [upload_image_to_comfy(base_url, p) for p in input_images]
        explicit_w = job.get("width") or defaults.width or (ASPECT_PRESETS[job["aspect"]][0] if "aspect" in job else (ASPECT_PRESETS[defaults.aspect][0] if defaults.aspect else None))
        explicit_h = job.get("height") or defaults.height or (ASPECT_PRESETS[job["aspect"]][1] if "aspect" in job else (ASPECT_PRESETS[defaults.aspect][1] if defaults.aspect else None))
        wf = build_edit_workflow(
            base_url=base_url,
            uploaded_images=uploaded_names,
            prompt=prompt,
            negative=negative,
            width=explicit_w,
            height=explicit_h,
            seed=seed,
            steps=steps,
            cfg=cfg,
            sampler=sampler,
            scheduler=scheduler,
            denoise=denoise,
            shift=shift,
            filename_prefix=prefix,
        )
        print(f"[ComfyUI] Chay Edit/Composite ({len(uploaded_names)} anh, seed={seed}) -> {output_path}")

    else:
        if not prompt:
            raise ValueError("Che do 't2i' can --prompt.")
        w = int(width or 1280)
        h = int(height or 720)
        wf = build_t2i_workflow(
            base_url=base_url,
            prompt=prompt,
            negative=negative,
            width=w,
            height=h,
            seed=seed,
            steps=steps,
            cfg=cfg,
            sampler=sampler,
            scheduler=scheduler,
            shift=shift,
            filename_prefix=prefix,
        )
        print(f"[ComfyUI] Chay Text-to-Image ({w}x{h}, seed={seed}) -> {output_path}")

    return execute_workflow(base_url, wf, output_path, defaults.timeout)


def main() -> int:
    parser = argparse.ArgumentParser(
        description="ComfyUI API Bridge cho comfyui-image-gen (Qwen-Image 2.1)"
    )
    parser.add_argument(
        "--mode",
        type=str,
        choices=["t2i", "edit", "graph"],
        default=None,
        help="Che do: t2i (tao anh moi), edit (ghep/sua anh), graph (do thi JSON tuy chinh)",
    )
    parser.add_argument(
        "--project-dir",
        type=str,
        default=None,
        help="Thu muc goc du an Concat (<PROJECT_DIR>). Tu dong tao <PROJECT_DIR>\\temp_assets\\comfyui\\batch_XX\\",
    )
    parser.add_argument(
        "--filename",
        type=str,
        default=None,
        help="Ten file dau ra khi dung --project-dir (vi du: scene_01.png)",
    )
    parser.add_argument("--prompt", type=str, default=None, help="Cau lenh mo ta / yeu cau chinh sua")
    parser.add_argument("--negative", type=str, default="", help="Negative prompt")
    parser.add_argument("--output", type=str, default=None, help="Duong dan file .png dau ra (tuy chon neu da co --project-dir)")
    parser.add_argument("--input-images", nargs="+", default=None, help="Danh sach anh dau vao cho che do edit")
    parser.add_argument("--graph-json", type=str, default=None, help="Duong dan file JSON do thi node tuy chinh")
    parser.add_argument("--upload-images", nargs="+", default=None, help="Anh local can upload khi chay --graph-json")
    parser.add_argument("--batch-json", type=str, default=None, help="File JSON danh sach nhieu tac vu")
    parser.add_argument(
        "--aspect",
        type=str,
        default=None,
        choices=list(ASPECT_PRESETS.keys()),
        help="Ty le khung hinh (16:9, 9:16, 1:1, 4:3, 3:4)",
    )
    parser.add_argument("--width", type=int, default=None, help="Chieu rong (px)")
    parser.add_argument("--height", type=int, default=None, help="Chieu cao (px)")
    parser.add_argument("--seed", type=int, default=-1, help="Seed (-1 = ngau nhien)")
    parser.add_argument("--steps", type=int, default=20, help="So buoc lay mau (mac dinh: 20)")
    parser.add_argument("--cfg", type=float, default=3.0, help="CFG scale (mac dinh: 3.0)")
    parser.add_argument("--sampler", type=str, default="euler", help="Sampler (mac dinh: euler)")
    parser.add_argument("--scheduler", type=str, default="simple", help="Scheduler (mac dinh: simple)")
    parser.add_argument("--denoise", type=float, default=0.85, help="Denoise cho edit fallback (mac dinh: 0.85)")
    parser.add_argument("--shift", type=float, default=3.1, help="ModelSamplingAuraFlow shift (mac dinh: 3.1)")
    parser.add_argument("--bat-path", type=str, default=DEFAULT_BAT_PATH, help="Duong dan run_comfyui.bat")
    parser.add_argument("--host", type=str, default=DEFAULT_HOST)
    parser.add_argument("--port", type=int, default=DEFAULT_PORT)
    parser.add_argument(
        "--auto-start",
        action=argparse.BooleanOptionalAction,
        default=True,
        help="Tu dong bat run_comfyui.bat neu server chua chay",
    )
    parser.add_argument(
        "--free-vram",
        action=argparse.BooleanOptionalAction,
        default=True,
        help="Giai phong VRAM sau khi hoan thanh",
    )
    parser.add_argument("--timeout", type=int, default=300, help="Timeout moi tac vu (giay)")
    parser.add_argument("--inspect-nodes", type=str, default=None, help="Tra cuu input/output cua node tren server")

    args = parser.parse_args()
    base_url = f"http://{args.host}:{args.port}"

    ensure_comfyui_running(
        base_url=base_url,
        bat_path=args.bat_path,
        auto_start=args.auto_start,
    )

    if args.inspect_nodes is not None:
        inspect_nodes(base_url, args.inspect_nodes)
        return 0

    batch_dir = None
    if args.project_dir:
        batch_dir = allocate_batch_dir(args.project_dir)
        print(f"[ComfyUI] Thu muc luu tap trung cua lo nay: {batch_dir}")

    jobs = []
    if args.batch_json:
        with open(args.batch_json, "r", encoding="utf-8") as f:
            jobs = json.load(f)
        if not isinstance(jobs, list) or not jobs:
            raise ValueError("--batch-json phai la mang JSON chua it nhat 1 tac vu.")
    else:
        if not args.output and not batch_dir:
            parser.error("Can cung cap --project-dir hoac --output (hoac --batch-json / --inspect-nodes).")
        jobs = [{}]

    generated_files = []
    try:
        for idx, job in enumerate(jobs, start=1):
            print(f"--- Tac vu {idx}/{len(jobs)} ---")
            out_file = run_job(base_url, job, args, batch_dir, idx)
            generated_files.append(out_file)
    finally:
        if args.free_vram:
            free_vram(base_url)

    print(
        json.dumps(
            {
                "status": "success",
                "batch_dir": batch_dir,
                "files": generated_files,
            },
            ensure_ascii=False,
        )
    )
    return 0


if __name__ == "__main__":
    try:
        sys.exit(main())
    except Exception as e:
        print(f"[ComfyUI ERROR] {e}", file=sys.stderr)
        sys.exit(1)
