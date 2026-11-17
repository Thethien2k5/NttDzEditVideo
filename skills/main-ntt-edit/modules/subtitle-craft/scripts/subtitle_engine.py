import argparse
import json
import re
import sys
from pathlib import Path

MAX_FILE_BYTES = 10 * 1024 * 1024  # Giới hạn 10MB chống tràn bộ nhớ


# ==============================================================================
# CẤU HÌNH PRESET MÀU SẮC & HIỆU ỨNG (.ASS THEME ENGINE)
# ==============================================================================

STYLE_PRESETS = {
    "minimal-clean": {
        "description": "Tối giản, dễ đọc cho Vlog, giáo dục, phỏng vấn nhẹ nhàng",
        "font": "Arial",
        "size_16_9": 54,
        "size_9_16": 64,
        "bold": True,
        "spacing": 0.5,
        "primary_color": "#F8FAFC",
        "accent_color": "#FACC15",
        "outline_color": "#0F172A",
        "bg_color": "#000000",
        "bg_opacity": 0.45,
        "border_style": 1,
        "outline": 2.5,
        "shadow": 1.5,
        "default_effect": "fade",
        "speaker_palette": ["#F8FAFC", "#38BDF8", "#34D399", "#F472B6"],
    },
    "shorts-pop": {
        "description": "Năng động, chữ đậm nổi bật cho TikTok, Reels, YouTube Shorts",
        "font": "Arial",
        "size_16_9": 62,
        "size_9_16": 78,
        "bold": True,
        "spacing": 0.5,
        "primary_color": "#FFFFFF",
        "accent_color": "#FFE600",
        "outline_color": "#000000",
        "bg_color": "#000000",
        "bg_opacity": 0.65,
        "border_style": 1,
        "outline": 4.2,
        "shadow": 3.0,
        "default_effect": "pop",
        "speaker_palette": ["#FFFFFF", "#00F5D4", "#FF9E00", "#FF5D8F"],
    },
    "boxed-modern": {
        "description": "Nền hộp hiện đại cho Tin tức, Tài chính, Công nghệ, Explainer",
        "font": "Arial",
        "size_16_9": 50,
        "size_9_16": 60,
        "bold": True,
        "spacing": 0.5,
        "primary_color": "#FFFFFF",
        "accent_color": "#38BDF8",
        "outline_color": "#0B1120",
        "bg_color": "#0B1120",
        "bg_opacity": 0.78,
        "border_style": 3,
        "outline": 10.0,
        "shadow": 0.0,
        "default_effect": "fade",
        "speaker_palette": ["#FFFFFF", "#7DD3FC", "#FDE047", "#6EE7B7"],
    },
    "podcast-duo": {
        "description": "Phân màu rõ nét cho Podcast, Talkshow, hội thoại nhiều người",
        "font": "Arial",
        "size_16_9": 54,
        "size_9_16": 66,
        "bold": True,
        "spacing": 0.5,
        "primary_color": "#FFFFFF",
        "accent_color": "#F59E0B",
        "outline_color": "#111827",
        "bg_color": "#111827",
        "bg_opacity": 0.55,
        "border_style": 1,
        "outline": 3.0,
        "shadow": 2.0,
        "default_effect": "slide-up",
        "speaker_palette": ["#FFFFFF", "#FBBF24", "#34D399", "#FB7185"],
    },
    "cinematic": {
        "description": "Điện ảnh, tinh tế cho Storytelling, Du lịch, Phim tài liệu",
        "font": "Arial",
        "size_16_9": 48,
        "size_9_16": 58,
        "bold": False,
        "spacing": 1.5,
        "primary_color": "#F3F4F6",
        "accent_color": "#EAB308",
        "outline_color": "#090D16",
        "bg_color": "#000000",
        "bg_opacity": 0.60,
        "border_style": 1,
        "outline": 1.5,
        "shadow": 2.5,
        "default_effect": "blur-in",
        "speaker_palette": ["#F3F4F6", "#E5E7EB", "#FDE68A", "#BAE6FD"],
    },
    "gaming-neon": {
        "description": "Tương phản cao, viền rực cho Gaming, Livestream, Review Tech",
        "font": "Arial",
        "size_16_9": 58,
        "size_9_16": 72,
        "bold": True,
        "spacing": 0.5,
        "primary_color": "#FFFFFF",
        "accent_color": "#A3E635",
        "outline_color": "#4C1D95",
        "bg_color": "#1E1B4B",
        "bg_opacity": 0.65,
        "border_style": 1,
        "outline": 3.8,
        "shadow": 2.5,
        "default_effect": "pop",
        "speaker_palette": ["#FFFFFF", "#22D3EE", "#F43F5E", "#A3E635"],
    },
    "luxury-editorial": {
        "description": "Sang trọng, giãn chữ rộng cho Thời trang, Bất động sản, Thương hiệu",
        "font": "Arial",
        "size_16_9": 48,
        "size_9_16": 58,
        "bold": False,
        "spacing": 2.0,
        "primary_color": "#FAF8F5",
        "accent_color": "#D4AF37",
        "outline_color": "#141414",
        "bg_color": "#0A0A0A",
        "bg_opacity": 0.72,
        "border_style": 3,
        "outline": 9.0,
        "shadow": 0.0,
        "default_effect": "fade",
        "speaker_palette": ["#FAF8F5", "#E5C158", "#D1D5DB", "#F3E8FF"],
    },
    "karaoke-pulse": {
        "description": "Chạy chữ đổi màu & bật nhịp từng từ theo giọng đọc (Shorts/Reels)",
        "font": "Arial",
        "size_16_9": 60,
        "size_9_16": 76,
        "bold": True,
        "spacing": 0.5,
        "primary_color": "#E2E8F0",
        "accent_color": "#FFE600",
        "outline_color": "#000000",
        "bg_color": "#000000",
        "bg_opacity": 0.65,
        "border_style": 1,
        "outline": 4.0,
        "shadow": 2.5,
        "default_effect": "karaoke",
        "speaker_palette": ["#E2E8F0", "#7DD3FC", "#6EE7B7", "#FDBA74"],
    },
}

AVAILABLE_EFFECTS = [
    "none",
    "fade",
    "pop",
    "slide-up",
    "blur-in",
    "karaoke",
    "typewriter",
]


def parse_timestamp(ts: str) -> float:
    ts = ts.strip().replace(",", ".")
    parts = ts.split(":")
    if len(parts) == 3:
        return int(parts[0]) * 3600 + int(parts[1]) * 60 + float(parts[2])
    if len(parts) == 2:
        return int(parts[0]) * 60 + float(parts[1])
    if len(parts) == 1:
        return float(parts[0])
    raise ValueError(f"Định dạng timestamp không hợp lệ: {ts}")


def format_srt_timestamp(seconds: float) -> str:
    total_ms = max(0, round(seconds * 1000))
    hrs, rem = divmod(total_ms, 3_600_000)
    mins, rem = divmod(rem, 60_000)
    secs, ms = divmod(rem, 1000)
    return f"{hrs:02d}:{mins:02d}:{secs:02d},{ms:03d}"


def format_ass_timestamp(seconds: float) -> str:
    total_cs = max(0, round(seconds * 100))
    hrs, rem = divmod(total_cs, 360_000)
    mins, rem = divmod(rem, 6_000)
    secs, cs = divmod(rem, 100)
    return f"{hrs:d}:{mins:02d}:{secs:02d}.{cs:02d}"


def clean_text(raw: str) -> str:
    no_tags = re.sub(r"<[^>]+>|\{[^}]*\}|\*\*|==", "", raw)
    no_tags = re.sub(r"\[#[0-9A-Fa-f]{6,8}:([^\]]+)\]", r"\1", no_tags)
    return re.sub(r"\s+", " ", no_tags).strip()


def detect_ext(content: str) -> str:
    stripped = content.lstrip()
    if stripped.startswith("WEBVTT"):
        return ".vtt"
    if "Dialogue:" in content or "[Script Info]" in content:
        return ".ass"
    return ".srt"


def parse_ass_or_ssa(content: str):
    cues = []
    header_lines = []
    in_events = False

    for raw_line in content.splitlines():
        line = raw_line.strip()
        if line.startswith("[Events]"):
            in_events = True
            header_lines.append(raw_line)
            continue

        if not line.startswith("Dialogue:"):
            if not in_events or line.startswith("Format:"):
                header_lines.append(raw_line)
            continue

        payload = line[len("Dialogue:"):].strip()
        parts = payload.split(",", 9)
        if len(parts) < 10:
            continue

        start = parse_timestamp(parts[1])
        end = parse_timestamp(parts[2])
        raw_text = parts[9]
        text_lines = [
            clean_text(seg)
            for seg in re.split(r"\\[Nn]", raw_text)
            if clean_text(seg)
        ]
        cues.append({
            "id": str(len(cues) + 1),
            "start": start,
            "end": end,
            "lines": text_lines,
            "raw_lines": [seg for seg in re.split(r"\\[Nn]", raw_text) if seg.strip()],
            "ass_meta": parts[:9],
        })
    return cues, header_lines


def parse_subtitles(content: str, ext: str):
    if ext in {".ass", ".ssa"}:
        return parse_ass_or_ssa(content)

    content = re.sub(r"^WEBVTT[^\n]*\n+", "", content.strip())
    blocks = re.split(r"\n\s*\n", content.strip())
    cues = []

    for block in blocks:
        lines = [line.strip() for line in block.splitlines() if line.strip()]
        if len(lines) < 2:
            continue
        if lines[0].startswith(("NOTE", "STYLE", "REGION")):
            continue

        time_line_idx = 1 if "-->" in lines[1] else (0 if "-->" in lines[0] else -1)
        if time_line_idx == -1:
            continue

        cue_id = lines[0] if time_line_idx == 1 else str(len(cues) + 1)
        start_str, end_str = lines[time_line_idx].split("-->", 1)
        end_str = end_str.strip().split(" ")[0]
        start = parse_timestamp(start_str)
        end = parse_timestamp(end_str)

        raw_lines = lines[time_line_idx + 1:]
        text_lines = [clean_text(line) for line in raw_lines if clean_text(line)]
        cues.append({
            "id": cue_id,
            "start": start,
            "end": end,
            "lines": text_lines,
            "raw_lines": raw_lines,
            "ass_meta": None,
        })
    return cues, []


def read_safe_content(file_arg: str):
    if file_arg == "-":
        raw = sys.stdin.buffer.read(MAX_FILE_BYTES + 1)
        if len(raw) > MAX_FILE_BYTES:
            raise ValueError("Dữ liệu stdin vượt quá giới hạn 10MB.")
        content = raw.decode("utf-8-sig")
        return content, detect_ext(content)

    path = Path(file_arg)
    if not path.is_file():
        raise FileNotFoundError(f"Không tìm thấy file: {path}")
    if path.stat().st_size > MAX_FILE_BYTES:
        raise ValueError(f"File {path} vượt quá giới hạn 10MB.")
    content = path.read_text(encoding="utf-8-sig")
    return content, path.suffix.lower()


def qc_cues(
    cues,
    mode: str,
    fps: float,
    max_cpl_override=None,
    max_cps_override=None,
    min_dur_override=None,
    cuts=None,
):
    if fps <= 0:
        raise ValueError("FPS phải lớn hơn 0.")

    if mode == "9:16":
        max_cpl, max_cps, min_dur, max_dur = 20, 15.0, 0.6, 5.0
    else:
        max_cpl, max_cps, min_dur, max_dur = 42, 17.0, 1.0, 7.0

    if max_cpl_override is not None:
        max_cpl = max_cpl_override
    if max_cps_override is not None:
        max_cps = max_cps_override
    if min_dur_override is not None:
        min_dur = min_dur_override

    min_gap = 2.0 / fps
    cuts = sorted(cuts or [])
    errors = []

    for i, cue in enumerate(cues):
        cid = cue["id"]
        start = cue["start"]
        end = cue["end"]
        dur = end - start
        lines = cue["lines"]
        full_text = " ".join(lines)
        total_chars = len(full_text)

        if dur <= 0:
            errors.append(f"[Cue {cid}] Lỗi timecode: thời lượng <= 0s.")
            continue

        if len(lines) > 2:
            errors.append(f"[Cue {cid}] Vượt quá 2 dòng ({len(lines)} dòng).")

        for idx, line in enumerate(lines, 1):
            if len(line) > max_cpl:
                errors.append(
                    f"[Cue {cid} - Dòng {idx}] Vượt CPL: {len(line)}/{max_cpl} ký tự ('{line}')."
                )

        cps = total_chars / dur
        if cps > max_cps:
            errors.append(
                f"[Cue {cid}] Vượt tốc độ đọc CPS: {cps:.1f}/{max_cps} ký tự/giây."
            )

        if dur < min_dur:
            errors.append(
                f"[Cue {cid}] Thời lượng quá ngắn: {dur:.2f}s (tối thiểu {min_dur}s)."
            )
        elif dur > max_dur:
            errors.append(
                f"[Cue {cid}] Thời lượng quá dài: {dur:.2f}s (tối đa {max_dur}s)."
            )

        if total_chars < 8 or dur < min_dur:
            errors.append(
                f"[Cue {cid}] Cảnh báo từ mồ côi: {total_chars} ký tự, {dur:.2f}s "
                f"(ngưỡng tối thiểu 8 ký tự và {min_dur}s)."
            )

        if i > 0:
            prev_end = cues[i - 1]["end"]
            gap = start - prev_end
            if gap < -1e-4:
                errors.append(
                    f"[Cue {cid}] Lỗi chồng chéo (overlap) với Cue {cues[i - 1]['id']} ({gap:.2f}s)."
                )
            elif gap < min_gap - 1e-4:
                frames = gap * fps
                errors.append(
                    f"[Cue {cid}] Khoảng nghỉ quá ngắn: {frames:.1f} frame (tối thiểu 2 frame)."
                )

        for cut in cuts:
            if start + 1e-4 < cut < end - 1e-4:
                errors.append(
                    f"[Cue {cid}] Bắc cầu qua điểm cắt cảnh tại {cut:.3f}s."
                )
            elif 0 <= cut - end < min_gap - 1e-4:
                errors.append(
                    f"[Cue {cid}] Kết thúc quá sát điểm cắt cảnh {cut:.3f}s (cách < 2 frame)."
                )
            elif 0 <= start - cut < min_gap - 1e-4:
                errors.append(
                    f"[Cue {cid}] Bắt đầu quá sát điểm cắt cảnh {cut:.3f}s (cách < 2 frame)."
                )

    return errors


def serialize_cues(cues, out_format: str, ass_header=None) -> str:
    if out_format == "ass":
        header = ass_header if ass_header else [
            "[Script Info]",
            "ScriptType: v4.00+",
            "PlayResX: 1920",
            "PlayResY: 1080",
            "",
            "[V4+ Styles]",
            "Format: Name, Fontname, Fontsize, PrimaryColour, SecondaryColour, OutlineColour, BackColour, Bold, Italic, Underline, StrikeOut, ScaleX, ScaleY, Spacing, Angle, BorderStyle, Outline, Shadow, Alignment, MarginL, MarginR, MarginV, Encoding",
            "Style: Default,Arial,54,&H00FFFFFF,&H000000FF,&H00000000,&H64000000,-1,0,0,0,100,100,0,0,1,2,1,2,40,40,50,1",
            "",
            "[Events]",
            "Format: Layer, Start, End, Style, Name, MarginL, MarginR, MarginV, Effect, Text",
        ]
        body = []
        for cue in cues:
            start_str = format_ass_timestamp(cue["start"])
            end_str = format_ass_timestamp(cue["end"])
            text = r"\N".join(cue["raw_lines"])
            if cue.get("ass_meta") and len(cue["ass_meta"]) >= 9:
                meta = list(cue["ass_meta"])
                meta[1] = start_str
                meta[2] = end_str
                body.append(f"Dialogue: {','.join(meta)},{text}")
            else:
                body.append(f"Dialogue: 0,{start_str},{end_str},Default,,0,0,0,,{text}")
        return "\n".join(header + body) + "\n"

    blocks = []
    for idx, cue in enumerate(cues, 1):
        start_str = format_srt_timestamp(cue["start"])
        end_str = format_srt_timestamp(cue["end"])
        text = "\n".join(cue["raw_lines"])
        blocks.append(f"{idx}\n{start_str} --> {end_str}\n{text}")
    return "\n\n".join(blocks) + ("\n" if blocks else "")


# ==============================================================================
# HÀM XỬ LÝ MÀU SẮC, THẺ NGỮ NGHĨA & HIỆU ỨNG ĐỘNG (.ASS)
# ==============================================================================

def normalize_hex_color(hex_str: str) -> str:
    val = hex_str.strip().lstrip("#")
    if len(val) == 3:
        val = "".join(ch * 2 for ch in val)
    if len(val) not in (6, 8) or not re.fullmatch(r"[0-9A-Fa-f]{6,8}", val):
        raise ValueError(f"Mã màu hex không hợp lệ: '{hex_str}'. Yêu cầu dạng #RRGGBB hoặc #RRGGBBAA.")
    return val.upper()


def hex_to_ass_inline(hex_str: str) -> str:
    """Chuyển #RRGGBB sang &HBBGGRR& dùng trong thẻ override ASS."""
    h = normalize_hex_color(hex_str)
    rr, gg, bb = h[0:2], h[2:4], h[4:6]
    return f"&H{bb}{gg}{rr}&"


def hex_to_ass_style(hex_str: str, opacity: float = 1.0) -> str:
    """Chuyển #RRGGBB (hoặc #RRGGBBAA) sang &HAABBGGRR dùng trong [V4+ Styles]."""
    h = normalize_hex_color(hex_str)
    rr, gg, bb = h[0:2], h[2:4], h[4:6]
    if len(h) == 8:
        css_opacity = int(h[6:8], 16) / 255.0
    else:
        css_opacity = max(0.0, min(1.0, opacity))
    # Trong ASS: 00 = đục hoàn toàn, FF = trong suốt hoàn toàn
    ass_alpha = round((1.0 - css_opacity) * 255)
    return f"&H{ass_alpha:02X}{bb}{gg}{rr}"


def parse_time_windows(raw_windows: str):
    windows = []
    if not raw_windows:
        return windows
    for item in raw_windows.split(","):
        item = item.strip()
        if not item:
            continue
        if "-" not in item:
            raise ValueError(f"Sai cú pháp khoảng thời gian '{item}'. Yêu cầu dạng start-end (VD: 5.0-9.5).")
        s_str, e_str = item.split("-", 1)
        windows.append((parse_timestamp(s_str), parse_timestamp(e_str)))
    return windows


def resolve_preset_config(preset_name: str, mode: str, overrides: dict) -> dict:
    if preset_name not in STYLE_PRESETS:
        raise ValueError(
            f"Preset '{preset_name}' không tồn tại. Các preset hợp lệ: {', '.join(STYLE_PRESETS.keys())}"
        )
    cfg = dict(STYLE_PRESETS[preset_name])
    cfg["speaker_palette"] = list(cfg["speaker_palette"])

    if mode == "9:16":
        cfg["play_res_x"] = 1080
        cfg["play_res_y"] = 1920
        cfg["font_size"] = overrides.get("font_size") or cfg["size_9_16"]
        cfg["margin_l"] = 60
        cfg["margin_r"] = 60
        cfg["margin_v_bottom"] = 360  # Vùng an toàn dưới của video dọc (tránh UI TikTok/Reels)
        cfg["margin_v_top"] = 220
    else:
        cfg["play_res_x"] = 1920
        cfg["play_res_y"] = 1080
        cfg["font_size"] = overrides.get("font_size") or cfg["size_16_9"]
        cfg["margin_l"] = 90
        cfg["margin_r"] = 90
        cfg["margin_v_bottom"] = 85
        cfg["margin_v_top"] = 70

    if overrides.get("font"):
        cfg["font"] = overrides["font"]
    if overrides.get("primary_color"):
        normalize_hex_color(overrides["primary_color"])
        cfg["primary_color"] = overrides["primary_color"]
        cfg["speaker_palette"][0] = overrides["primary_color"]
    if overrides.get("accent_color"):
        normalize_hex_color(overrides["accent_color"])
        cfg["accent_color"] = overrides["accent_color"]
    if overrides.get("outline_color"):
        normalize_hex_color(overrides["outline_color"])
        cfg["outline_color"] = overrides["outline_color"]
    if overrides.get("bg_color"):
        normalize_hex_color(overrides["bg_color"])
        cfg["bg_color"] = overrides["bg_color"]
    if overrides.get("border_style") is not None:
        cfg["border_style"] = overrides["border_style"]

    return cfg


def build_ass_header(cfg: dict, default_alignment: int = 2) -> list:
    bold_flag = -1 if cfg["bold"] else 0
    margin_v = cfg["margin_v_top"] if default_alignment == 8 else cfg["margin_v_bottom"]
    if default_alignment == 5:
        margin_v = 0

    sec_col = hex_to_ass_style(cfg["accent_color"], 1.0)
    out_col = hex_to_ass_style(cfg["outline_color"], 1.0)
    back_col = (
        hex_to_ass_style(cfg["bg_color"], cfg["bg_opacity"])
        if cfg["border_style"] == 3
        else hex_to_ass_style(cfg["bg_color"], cfg["bg_opacity"])
    )

    def make_style_line(name: str, primary_hex: str, align: int, m_v: int) -> str:
        prim_col = hex_to_ass_style(primary_hex, 1.0)
        return (
            f"Style: {name},{cfg['font']},{cfg['font_size']},"
            f"{prim_col},{sec_col},{out_col},{back_col},"
            f"{bold_flag},0,0,0,100,100,{cfg['spacing']},0,"
            f"{cfg['border_style']},{cfg['outline']},{cfg['shadow']},"
            f"{align},{cfg['margin_l']},{cfg['margin_r']},{m_v},1"
        )

    styles = [
        make_style_line("Default", cfg["primary_color"], default_alignment, margin_v),
    ]
    for idx, sp_hex in enumerate(cfg["speaker_palette"], 1):
        styles.append(make_style_line(f"S{idx}", sp_hex, default_alignment, margin_v))

    return [
        "[Script Info]",
        "ScriptType: v4.00+",
        f"PlayResX: {cfg['play_res_x']}",
        f"PlayResY: {cfg['play_res_y']}",
        "WrapStyle: 2",
        "ScaledBorderAndShadow: yes",
        "",
        "[V4+ Styles]",
        "Format: Name, Fontname, Fontsize, PrimaryColour, SecondaryColour, OutlineColour, BackColour, Bold, Italic, Underline, StrikeOut, ScaleX, ScaleY, Spacing, Angle, BorderStyle, Outline, Shadow, Alignment, MarginL, MarginR, MarginV, Encoding",
        *styles,
        "",
        "[Events]",
        "Format: Layer, Start, End, Style, Name, MarginL, MarginR, MarginV, Effect, Text",
    ]


def render_inline_semantic_markup(line: str, base_hex: str, accent_hex: str, base_bold: bool) -> str:
    """Biên dịch **keyword**, ==keyword== và [#HEX:text] sang thẻ màu ASS chuẩn."""
    base_ass = hex_to_ass_inline(base_hex)
    accent_ass = hex_to_ass_inline(accent_hex)
    b_reset = r"\b1" if base_bold else r"\b0"

    # 1. Màu chỉ định trực tiếp: [#RRGGBB:cụm từ]
    def repl_custom_hex(match):
        custom_ass = hex_to_ass_inline(match.group(1))
        inner = match.group(2)
        return f"{{\\c{custom_ass}\\b1}}{inner}{{\\c{base_ass}{b_reset}}}"

    out = re.sub(r"\[(#[0-9A-Fa-f]{6,8}):([^\]]+)\]", repl_custom_hex, line)

    # 2. Nhấn mạnh từ khóa: **từ khóa** hoặc ==từ khóa==
    def repl_accent(match):
        inner = match.group(1)
        return f"{{\\c{accent_ass}\\b1}}{inner}{{\\c{base_ass}{b_reset}}}"

    out = re.sub(r"\*\*([^*]+)\*\*|==([^=]+)==", lambda m: repl_accent(m if m.group(1) is not None else type("M", (), {"group": lambda _, i: m.group(2)})()), out)
    return out


def build_word_animated_lines(
    raw_lines: list,
    cue_start: float,
    cue_end: float,
    base_hex: str,
    accent_hex: str,
    effect: str,
    word_timings: list = None,
) -> list:
    """Tạo hiệu ứng karaoke (đổi màu + bật nhịp từng từ) hoặc typewriter (hiện từng từ)."""
    dur_ms = max(100, round((cue_end - cue_start) * 1000))
    base_ass = hex_to_ass_inline(base_hex)
    accent_ass = hex_to_ass_inline(accent_hex)

    # Trích xuất danh sách từ theo từng dòng kèm cờ nhấn mạnh
    tokenized_lines = []
    flat_tokens = []
    for line in raw_lines:
        line_tokens = []
        # Tách các cụm **accent** trước để giữ trạng thái nhấn mạnh
        parts = re.split(r"(\*\*[^*]+\*\*|==[^=]+==)", line)
        for part in parts:
            if not part:
                continue
            is_accented = (part.startswith("**") and part.endswith("**")) or (part.startswith("==") and part.endswith("=="))
            clean_part = part[2:-2] if is_accented else part
            clean_part = re.sub(r"\[#[0-9A-Fa-f]{6,8}:([^\]]+)\]", r"\1", clean_part)
            for word in clean_part.split():
                tok = {"word": word, "accent": is_accented}
                line_tokens.append(tok)
                flat_tokens.append(tok)
        tokenized_lines.append(line_tokens)

    if not flat_tokens:
        return raw_lines

    # Tính mốc thời gian (ms tương đối từ đầu cue) cho từng từ
    matched_words = []
    if word_timings:
        matched_words = [
            w for w in word_timings
            if w["end"] >= cue_start - 0.05 and w["start"] <= cue_end + 0.05
        ]

    intervals_ms = []
    if len(matched_words) == len(flat_tokens):
        for w in matched_words:
            t1 = max(0, round((w["start"] - cue_start) * 1000))
            t2 = min(dur_ms, max(t1 + 40, round((w["end"] - cue_start) * 1000)))
            intervals_ms.append((t1, t2))
    else:
        # Ước lượng theo trọng số độ dài ký tự
        usable_ms = max(80, dur_ms - 60)
        weights = [max(2, len(t["word"])) for t in flat_tokens]
        total_w = sum(weights)
        cursor = 0.0
        for w_val in weights:
            step = (w_val / total_w) * usable_ms
            t1 = round(cursor)
            t2 = min(dur_ms, max(t1 + 40, round(cursor + step)))
            intervals_ms.append((t1, t2))
            cursor += step

    idx = 0
    rendered_lines = []
    for line_tokens in tokenized_lines:
        rendered_words = []
        for tok in line_tokens:
            t1, t2 = intervals_ms[idx]
            idx += 1
            word_txt = tok["word"]

            if effect == "typewriter":
                if t1 <= 15:
                    col_tag = f"\\c{accent_ass}" if tok["accent"] else ""
                    rendered_words.append(f"{{{col_tag}}}{word_txt}" if col_tag else word_txt)
                else:
                    col_tag = f"\\c{accent_ass}" if tok["accent"] else ""
                    rendered_words.append(
                        f"{{\\alpha&HFF&{col_tag}\\t({t1},{min(dur_ms, t1 + 25)},\\alpha&H00&)}}{word_txt}"
                    )
            else:  # karaoke
                in_end = min(dur_ms, t1 + 35)
                out_end = min(dur_ms, t2 + 45)
                rest_col = accent_ass if tok["accent"] else base_ass
                rendered_words.append(
                    f"{{\\t({t1},{in_end},\\c{accent_ass}\\fscx108\\fscy108)"
                    f"\\t({t2},{out_end},\\c{rest_col}\\fscx100\\fscy100)}}{word_txt}"
                )
        rendered_lines.append(" ".join(rendered_words))

    return rendered_lines


def style_cues(
    cues: list,
    cfg: dict,
    effect: str,
    default_position: str = "bottom",
    top_windows: list = None,
    auto_speaker: bool = False,
    word_timings: list = None,
) -> list:
    pos_to_align = {"bottom": 2, "center": 5, "top": 8}
    base_align = pos_to_align.get(default_position, 2)
    top_windows = top_windows or []
    speaker_name_map = {}
    styled_cues = []

    for cue in cues:
        start = cue["start"]
        end = cue["end"]
        dur_ms = max(50, round((end - start) * 1000))
        raw_lines = list(cue["raw_lines"])
        if not raw_lines:
            continue

        # 1. Xác định vị trí (Alignment): thẻ {top} / {\an8} hoặc trùng khoảng lower-third
        cue_align = base_align
        first_line_clean = raw_lines[0].strip()

        if re.match(r"^(?:\{top\}|\{\\an8\})\s*", first_line_clean, flags=re.IGNORECASE):
            cue_align = 8
            raw_lines[0] = re.sub(r"^(?:\{top\}|\{\\an8\})\s*", "", first_line_clean, flags=re.IGNORECASE)
        elif re.match(r"^(?:\{center\}|\{\\an5\})\s*", first_line_clean, flags=re.IGNORECASE):
            cue_align = 5
            raw_lines[0] = re.sub(r"^(?:\{center\}|\{\\an5\})\s*", "", first_line_clean, flags=re.IGNORECASE)
        else:
            for w_start, w_end in top_windows:
                if start < w_end - 1e-3 and end > w_start + 1e-3:
                    cue_align = 8
                    break

        # 2. Xác định người nói ({S1}..{S4} hoặc [Tên]:)
        style_name = "Default"
        speaker_idx = 0

        sp_match = re.match(r"^\{S([1-4])\}\s*", raw_lines[0].strip(), flags=re.IGNORECASE)
        if sp_match:
            speaker_idx = int(sp_match.group(1))
            raw_lines[0] = re.sub(r"^\{S[1-4]\}\s*", "", raw_lines[0].strip(), flags=re.IGNORECASE)
        elif auto_speaker:
            name_match = re.match(r"^\[([^\]]{1,24})\]:\s*", raw_lines[0].strip())
            if name_match:
                sp_name = name_match.group(1).strip().lower()
                if sp_name not in speaker_name_map:
                    speaker_name_map[sp_name] = (len(speaker_name_map) % len(cfg["speaker_palette"])) + 1
                speaker_idx = speaker_name_map[sp_name]

        if 1 <= speaker_idx <= len(cfg["speaker_palette"]):
            style_name = f"S{speaker_idx}"
            speaker_hex = cfg["speaker_palette"][speaker_idx - 1]
        else:
            speaker_hex = cfg["primary_color"]

        # 3. Tạo hiệu ứng chuyển động & render văn bản
        motion_tags = []
        if cue_align != base_align:
            motion_tags.append(f"\\an{cue_align}")

        if effect in {"karaoke", "typewriter"}:
            if effect == "karaoke":
                fad_in = min(80, dur_ms // 4)
                fad_out = min(80, dur_ms // 4)
                motion_tags.append(f"\\fad({fad_in},{fad_out})")
            rendered_lines = build_word_animated_lines(
                raw_lines=raw_lines,
                cue_start=start,
                cue_end=end,
                base_hex=speaker_hex,
                accent_hex=cfg["accent_color"],
                effect=effect,
                word_timings=word_timings,
            )
        else:
            if effect == "fade":
                fad_in = min(130, dur_ms // 3)
                fad_out = min(110, dur_ms // 3)
                motion_tags.append(f"\\fad({fad_in},{fad_out})")
            elif effect == "pop":
                t_peak = min(85, max(30, dur_ms // 4))
                t_settle = min(155, max(t_peak + 30, dur_ms // 2))
                fad_out = min(80, dur_ms // 4)
                motion_tags.append(
                    f"\\fad(40,{fad_out})\\fscx86\\fscy86"
                    f"\\t(0,{t_peak},\\fscx105\\fscy105)"
                    f"\\t({t_peak},{t_settle},\\fscx100\\fscy100)"
                )
            elif effect == "slide-up":
                cx = cfg["play_res_x"] // 2
                if cue_align == 8:
                    cy = cfg["margin_v_top"]
                    y1 = max(10, cy - 26)
                elif cue_align == 5:
                    cy = cfg["play_res_y"] // 2
                    y1 = cy + 26
                else:
                    cy = cfg["play_res_y"] - cfg["margin_v_bottom"]
                    y1 = cy + 26
                t_move = min(130, max(50, dur_ms // 3))
                fad_in = min(100, dur_ms // 3)
                fad_out = min(90, dur_ms // 3)
                motion_tags.append(f"\\move({cx},{y1},{cx},{cy},0,{t_move})\\fad({fad_in},{fad_out})")
            elif effect == "blur-in":
                t_focus = min(160, max(60, dur_ms // 3))
                fad_in = min(140, dur_ms // 3)
                fad_out = min(120, dur_ms // 3)
                motion_tags.append(f"\\blur6\\fad({fad_in},{fad_out})\\t(0,{t_focus},\\blur0)")

            rendered_lines = [
                render_inline_semantic_markup(line, speaker_hex, cfg["accent_color"], cfg["bold"])
                for line in raw_lines
            ]

        if motion_tags:
            rendered_lines[0] = f"{{{''.join(motion_tags)}}}{rendered_lines[0]}"

        clean_lines = [clean_text(l) for l in raw_lines if clean_text(l)]
        styled_cues.append({
            "id": cue["id"],
            "start": start,
            "end": end,
            "lines": clean_lines,
            "raw_lines": rendered_lines,
            "ass_meta": ["0", format_ass_timestamp(start), format_ass_timestamp(end), style_name, "", "0", "0", "0", ""],
        })

    return styled_cues


# ==============================================================================
# CÁC LỆNH CLI (QC, CONCAT, STYLE, PRESETS)
# ==============================================================================

def cmd_qc(args):
    content, ext = read_safe_content(args.file)
    cues, _ = parse_subtitles(content, ext)
    cuts = [parse_timestamp(x) for x in args.cuts.split(",") if x.strip()] if args.cuts else []

    errors = qc_cues(
        cues,
        mode=args.mode,
        fps=args.fps,
        max_cpl_override=args.max_cpl,
        max_cps_override=args.max_cps,
        min_dur_override=args.min_dur,
        cuts=cuts,
    )

    print(f"=== KẾT QUẢ QC ({args.mode} @ {args.fps}fps) - Tổng số cue: {len(cues)} ===")
    if not errors:
        print("ĐẠT CHUẨN 100%! Không phát hiện lỗi nào.")
        return 0

    print(f"Phát hiện {len(errors)} cảnh báo/lỗi cần xử lý:\n")
    for err in errors:
        print(f" - {err}")
    return 1


def cmd_concat(args):
    if args.fps <= 0:
        raise ValueError("FPS phải lớn hơn 0.")

    items = []
    if args.manifest:
        manifest_path = Path(args.manifest)
        data = json.loads(manifest_path.read_text(encoding="utf-8-sig"))
        for entry in data:
            items.append((entry["sub"], float(entry["duration"])))
    else:
        for spec in args.clips:
            if ":" not in spec:
                raise ValueError(f"Sai cú pháp '{spec}'. Yêu cầu dạng: duong_dan_file:thoi_luong_giay")
            sub_path, dur_str = spec.rsplit(":", 1)
            items.append((sub_path, float(dur_str)))

    if not items:
        raise ValueError("Cần ít nhất 1 cặp file_sub:duration để ghép nối.")

    safe_margin = 2.0 / args.fps
    merged_cues = []
    first_ass_header = None
    first_ext = ".srt"
    offset = 0.0

    for idx, (sub_path, clip_dur) in enumerate(items):
        if clip_dur <= 0:
            raise ValueError(f"Thời lượng clip không hợp lệ ({clip_dur}s) cho {sub_path}")

        content, ext = read_safe_content(sub_path)
        if idx == 0:
            first_ext = ext
        cues, header = parse_subtitles(content, ext)
        if first_ass_header is None and header:
            first_ass_header = header

        max_allowed_end = max(0.0, clip_dur - safe_margin)

        for cue in cues:
            c_start = cue["start"]
            c_end = cue["end"]

            if c_start >= max_allowed_end:
                print(
                    f"[Cảnh báo concat] Bỏ qua cue '{' '.join(cue['lines'])}' ở {sub_path} "
                    f"do bắt đầu sau giới hạn clip ({c_start:.2f}s >= {max_allowed_end:.2f}s).",
                    file=sys.stderr,
                )
                continue

            if c_end > max_allowed_end:
                print(
                    f"[Kẹp trần concat] Cắt đuôi cue '{' '.join(cue['lines'])}' tại {sub_path}: "
                    f"{c_end:.3f}s -> {max_allowed_end:.3f}s (tránh tràn sang clip sau).",
                    file=sys.stderr,
                )
                c_end = max_allowed_end

            merged_cues.append({
                "id": str(len(merged_cues) + 1),
                "start": c_start + offset,
                "end": c_end + offset,
                "lines": cue["lines"],
                "raw_lines": cue["raw_lines"],
                "ass_meta": cue["ass_meta"],
            })

        offset += clip_dur

    if args.preset:
        cfg = resolve_preset_config(args.preset, args.mode, {})
        effect = args.effect or cfg["default_effect"]
        first_ass_header = build_ass_header(cfg, default_alignment=2)
        merged_cues = style_cues(merged_cues, cfg, effect=effect)
        out_fmt = "ass"
    else:
        out_fmt = args.format if args.format else ("ass" if first_ext in {".ass", ".ssa"} else "srt")

    output_text = serialize_cues(merged_cues, out_fmt, first_ass_header)

    if args.out == "-":
        sys.stdout.write(output_text)
    else:
        Path(args.out).write_text(output_text, encoding="utf-8")
        print(f"Đã xuất {len(merged_cues)} cue ra file: {args.out}", file=sys.stderr)

    if args.run_qc:
        errors = qc_cues(merged_cues, mode=args.mode, fps=args.fps)
        if errors:
            print(f"\n[QC sau concat] Phát hiện {len(errors)} cảnh báo/lỗi:", file=sys.stderr)
            for err in errors:
                print(f" - {err}", file=sys.stderr)
            return 1
        print("\n[QC sau concat] ĐẠT CHUẨN 100%!", file=sys.stderr)

    return 0


def cmd_style(args):
    content, ext = read_safe_content(args.file)
    cues, _ = parse_subtitles(content, ext)

    overrides = {
        "font": args.font,
        "font_size": args.font_size,
        "primary_color": args.primary_color,
        "accent_color": args.accent_color,
        "outline_color": args.outline_color,
        "bg_color": args.bg_color,
        "border_style": 3 if args.box else (1 if args.no_box else None),
    }
    cfg = resolve_preset_config(args.preset, args.mode, overrides)
    effect = args.effect or cfg["default_effect"]
    pos_to_align = {"bottom": 2, "center": 5, "top": 8}
    default_align = pos_to_align[args.position]

    top_windows = parse_time_windows(args.top_windows)
    word_timings = None
    if args.words_json:
        w_path = Path(args.words_json)
        if not w_path.is_file():
            raise FileNotFoundError(f"Không tìm thấy file word-level JSON: {w_path}")
        word_timings = json.loads(w_path.read_text(encoding="utf-8-sig"))

    header = build_ass_header(cfg, default_alignment=default_align)
    styled_cues = style_cues(
        cues=cues,
        cfg=cfg,
        effect=effect,
        default_position=args.position,
        top_windows=top_windows,
        auto_speaker=args.auto_speaker,
        word_timings=word_timings,
    )

    output_text = serialize_cues(styled_cues, "ass", header)

    if args.out == "-":
        sys.stdout.write(output_text)
    else:
        Path(args.out).write_text(output_text, encoding="utf-8")
        print(
            f"Đã áp dụng preset '{args.preset}' (effect: '{effect}') cho {len(styled_cues)} cue -> {args.out}",
            file=sys.stderr,
        )

    if args.run_qc:
        errors = qc_cues(styled_cues, mode=args.mode, fps=args.fps)
        if errors:
            print(f"\n[QC sau style] Phát hiện {len(errors)} cảnh báo/lỗi:", file=sys.stderr)
            for err in errors:
                print(f" - {err}", file=sys.stderr)
            return 1
        print("\n[QC sau style] ĐẠT CHUẨN 100%!", file=sys.stderr)

    return 0


def cmd_presets(args):
    if args.json:
        payload = {
            "presets": STYLE_PRESETS,
            "effects": AVAILABLE_EFFECTS,
        }
        print(json.dumps(payload, ensure_ascii=False, indent=2))
        return 0

    print("=== DANH SÁCH PRESET MÀU SẮC & PHONG CÁCH ===")
    for name, info in STYLE_PRESETS.items():
        print(
            f" - {name:<18} | Effect mặc định: {info['default_effect']:<10} | "
            f"Chữ: {info['primary_color']} | Nhấn: {info['accent_color']} -> {info['description']}"
        )
    print(f"\n=== CÁC HIỆU ỨNG CHUYỂN ĐỘNG (--effect) ===\n {', '.join(AVAILABLE_EFFECTS)}")
    return 0


def main():
    parser = argparse.ArgumentParser(description="Engine QC, Concat & Styling phụ đề cho Subtitle Craft")
    subparsers = parser.add_subparsers(dest="command", required=True)

    # Lệnh qc
    p_qc = subparsers.add_parser("qc", help="Kiểm tra chất lượng phụ đề")
    p_qc.add_argument("file", help="Đường dẫn file .srt/.vtt/.ass/.ssa hoặc '-' đọc từ stdin")
    p_qc.add_argument("--mode", choices=["16:9", "9:16"], default="16:9")
    p_qc.add_argument("--fps", type=float, default=30.0)
    p_qc.add_argument("--max-cpl", type=int, default=None)
    p_qc.add_argument("--max-cps", type=float, default=None)
    p_qc.add_argument("--min-dur", type=float, default=None)
    p_qc.add_argument("--cuts", type=str, default="", help="Các mốc cắt cảnh cách nhau dấu phẩy (VD: 8.15,15.40)")
    p_qc.set_defaults(func=cmd_qc)

    # Lệnh concat
    p_cat = subparsers.add_parser("concat", help="Ghép phụ đề từ nhiều clip theo thời lượng thực tế")
    p_cat.add_argument("clips", nargs="*", help="Danh sách cặp file_sub:duration_giay (VD: c1.srt:10.5 c2.srt:8.2)")
    p_cat.add_argument("--manifest", type=str, default=None, help="File JSON chứa mảng [{\"sub\": ..., \"duration\": ...}]")
    p_cat.add_argument("--fps", type=float, default=30.0)
    p_cat.add_argument("--mode", choices=["16:9", "9:16"], default="16:9")
    p_cat.add_argument("--format", choices=["srt", "ass"], default=None, help="Định dạng xuất (mặc định theo file đầu tiên)")
    p_cat.add_argument("--preset", choices=list(STYLE_PRESETS.keys()), default=None, help="Áp dụng preset màu/hiệu ứng ASS sau khi ghép")
    p_cat.add_argument("--effect", choices=AVAILABLE_EFFECTS, default=None, help="Ghi đè hiệu ứng chuyển động khi dùng --preset")
    p_cat.add_argument("--out", type=str, default="-", help="File đầu ra (mặc định '-' xuất ra stdout)")
    p_cat.add_argument("--run-qc", action="store_true", help="Tự động chạy QC toàn cục sau khi ghép")
    p_cat.set_defaults(func=cmd_concat)

    # Lệnh style
    p_style = subparsers.add_parser("style", help="Tạo phụ đề .ass có màu sắc, phân vai & hiệu ứng động")
    p_style.add_argument("file", help="Đường dẫn file .srt/.vtt/.ass/.ssa hoặc '-' đọc từ stdin")
    p_style.add_argument("--preset", choices=list(STYLE_PRESETS.keys()), default="minimal-clean", help="Bộ giao diện màu & font mẫu")
    p_style.add_argument("--effect", choices=AVAILABLE_EFFECTS, default=None, help="Hiệu ứng chuyển động (mặc định theo preset)")
    p_style.add_argument("--mode", choices=["16:9", "9:16"], default="16:9")
    p_style.add_argument("--fps", type=float, default=30.0)
    p_style.add_argument("--font", type=str, default=None, help="Tên font chữ (VD: Inter, Roboto, Arial, Montserrat)")
    p_style.add_argument("--font-size", type=int, default=None, help="Ghi đè cỡ chữ")
    p_style.add_argument("--primary-color", type=str, default=None, help="Màu chữ chính dạng hex (VD: #FFFFFF)")
    p_style.add_argument("--accent-color", type=str, default=None, help="Màu nhấn từ khóa dạng hex (VD: #FFE600)")
    p_style.add_argument("--outline-color", type=str, default=None, help="Màu viền chữ dạng hex (VD: #000000)")
    p_style.add_argument("--bg-color", type=str, default=None, help="Màu nền hộp/bóng dạng hex (VD: #0B1120)")
    p_style.add_argument("--box", action="store_true", help="Bật nền hộp bao quanh chữ (BorderStyle=3)")
    p_style.add_argument("--no-box", action="store_true", help="Tắt nền hộp, dùng viền + đổ bóng (BorderStyle=1)")
    p_style.add_argument("--position", choices=["bottom", "top", "center"], default="bottom", help="Vị trí hiển thị mặc định")
    p_style.add_argument("--top-windows", type=str, default="", help="Các khoảng thời gian đẩy phụ đề lên trên tránh lower-third (VD: 4.5-9.0,18.0-22.5)")
    p_style.add_argument("--auto-speaker", action="store_true", help="Tự động phân màu khi gặp tiền tố [Tên nhân vật]:")
    p_style.add_argument("--words-json", type=str, default=None, help="File JSON word-level timestamps cho hiệu ứng karaoke/typewriter chính xác từng từ")
    p_style.add_argument("--out", type=str, default="-", help="File .ass đầu ra (mặc định '-' xuất ra stdout)")
    p_style.add_argument("--run-qc", action="store_true", help="Tự động chạy QC sau khi tạo style")
    p_style.set_defaults(func=cmd_style)

    # Lệnh presets
    p_list = subparsers.add_parser("presets", help="Liệt kê danh sách preset màu sắc & hiệu ứng")
    p_list.add_argument("--json", action="store_true", help="Xuất danh sách dạng JSON")
    p_list.set_defaults(func=cmd_presets)

    args = parser.parse_args()
    try:
        sys.exit(args.func(args))
    except Exception as exc:
        print(f"LỖI: {exc}", file=sys.stderr)
        sys.exit(1)


if __name__ == "__main__":
    main()