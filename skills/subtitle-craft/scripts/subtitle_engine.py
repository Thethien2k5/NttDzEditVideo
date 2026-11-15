import argparse
import json
import re
import sys
from pathlib import Path

MAX_FILE_BYTES = 10 * 1024 * 1024  # Giới hạn 10MB chống tràn bộ nhớ


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
    no_tags = re.sub(r"<[^>]+>|\{[^}]*\}", "", raw)
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


def main():
    parser = argparse.ArgumentParser(description="Engine QC & Concat phụ đề cho Subtitle Craft")
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
    p_cat.add_argument("--out", type=str, default="-", help="File đầu ra (mặc định '-' xuất ra stdout)")
    p_cat.add_argument("--run-qc", action="store_true", help="Tự động chạy QC toàn cục sau khi ghép")
    p_cat.set_defaults(func=cmd_concat)

    args = parser.parse_args()
    try:
        sys.exit(args.func(args))
    except Exception as exc:
        print(f"LỖI: {exc}", file=sys.stderr)
        sys.exit(1)


if __name__ == "__main__":
    main()