---
name: media-preprocess
description: "Tiền xử lý, trích xuất kịch bản và thu thập tài nguyên media trước khi dựng phim: cắt bỏ khoảng lặng/nói vấp bằng auto-editor, tẩy xóa phụ đề cứng hoặc logo/watermark bằng VSR AI, tách giọng khỏi nhạc nền bằng Demucs và trích xuất kịch bản/phụ đề đa ngôn ngữ theo mốc thời gian bằng WhisperX, tải video/B-roll/meme/nhạc nền & SFX không bản quyền chuẩn định dạng bằng yt-dlp, tách phông xanh sang .webm Alpha và chuẩn hóa âm lượng LUFS vào thư mục dự án Concat."
---

# Tiền Xử Lý, Trích Xuất Kịch Bản & Thu Thập Tư Liệu Media (`media-preprocess`)

Tất cả công cụ đều chạy qua file `.bat` kích hoạt sẵn đường dẫn thư viện của môi trường `NttDzEditVideo` (Python 3.10 + PyTorch CUDA 12.4) trên PowerShell:
- **`auto-editor`**: `F:\A_Tool\Tools\auto-editor\auto-editor.bat`
- **`VSR`**: `F:\A_Tool\Tools\video-subtitle-remover\vsr.bat`
- **`yt-dlp`**: `F:\A_Tool\Tools\yt-dlp\yt-dlp.bat`
- **`WhisperX`**: `F:\A_Tool\Tools\whisperx\whisperx.bat`
- **`Demucs`**: `F:\A_Tool\Tools\demucs\demucs.bat`
- **`ffmpeg` / `ffprobe`**: Gọi qua `conda run -n NttDzEditVideo ffmpeg` (hoặc `ffprobe`).

---

## 1. Quy Tắc Bắt Buộc Về Lưu Trữ, Tên File & Phần Cứng

1. **Khởi tạo thư mục đích trong dự án Concat (`<PROJECT_DIR>`)**:
   - Trước khi chạy bất kỳ lệnh nào, lấy đường dẫn dự án đang mở qua `project_list` hoặc `timeline_read`.
   - Luôn tạo sẵn thư mục lưu trữ tạm trước khi xuất file:
     ```powershell
     New-Item -ItemType Directory -Force -Path "<PROJECT_DIR>\temp_assets\preprocess" | Out-Null
     ```
   - Toàn bộ file tải về và file sau xử lý **bắt buộc** lưu tại `<PROJECT_DIR>\temp_assets\preprocess\` với tiền tố phân loại rõ ràng để các skill khác (`hyperframes-motion`, `dynamic-visual-enhancer`, `subtitle-craft`) nhận diện ngay:
     - `raw_*` / `source_*`: Video thoại/tư liệu chính.
     - `bgm_*`: Nhạc nền không bản quyền.
     - `sfx_*`: Hiệu ứng âm thanh ngắn (`whoosh`, `pop`, `ding`, `boom`...).
     - `meme_*`: Video/âm thanh meme hoặc meme phông xanh đã tách nền (`meme_*_alpha.webm`).
     - `broll_*`: Cảnh quay minh họa phụ trợ.
     - `transcript_*` / `vocals_*`: File kịch bản văn bản (`.txt`), phụ đề (`.srt`), dữ liệu JSON (`.json`) và track giọng tách riêng (`.wav`).
   - Tuyệt đối không ghi đè file gốc và không lưu rác vào thư mục cài đặt Skill.

2. **Chuẩn hóa tên file đầu ra (Chống lỗi chuỗi lệnh)**:
   - Không đặt tên file chứa dấu ngoặc kép, ký tự đặc biệt hoặc emoji. Khi tải từ internet, luôn dùng cờ `--restrict-filenames` để tránh lỗi không đọc được đường dẫn ở các bước xử lý tiếp theo.

3. **Bảo vệ VRAM GPU RTX 3060 6GB (Chạy tuần tự)**:
   - Các công cụ AI (`vsr.bat`, `whisperx.bat`, `demucs.bat`, `vieneu.bat`) sử dụng GPU RTX 3060 (CUDA 12.4) tiêu tốn nhiều VRAM. Chỉ xử lý **từng tác vụ và từng file một**.
   - **Cấm** chạy đồng thời nhiều tiến trình nặng GPU hoặc chạy song song với tiến trình render của Concat để tránh tràn 6GB VRAM (`CUDA out of memory`).

4. **Chạy hoàn toàn qua CLI (Non-interactive)**:
   - Không kích hoạt giao diện đồ họa (GUI) gây treo terminal của Agent.

---

## 2. Cắt Khoảng Lặng & Lọc Thô (`auto-editor`)

Dùng khi video quay thô (talking-head, tutorial, voiceover) có nhiều đoạn ngập ngừng, lấy hơi dài hoặc khoảng chết âm thanh.

### Lệnh chuẩn (Tăng tốc phần cứng GPU RTX 3060 qua `h264_nvenc`):
```powershell
& "F:\A_Tool\Tools\auto-editor\auto-editor.bat" "<duong_dan\raw_video.mp4>" --edit audio:threshold=4% --margin 0.2s --video-codec h264_nvenc -o "<PROJECT_DIR>\temp_assets\preprocess\raw_video_clean.mp4"
```

### Tinh chỉnh ngưỡng âm thanh (`threshold`) theo thực tế:
- **Giọng thu âm chuẩn, mic gần**: `--edit audio:threshold=4%` (Mặc định khuyên dùng).
- **Giọng đọc nhỏ, thu xa mic** (tránh cắt lẹm chữ cuối câu): hạ xuống `--edit audio:threshold=2%` và tăng `--margin 0.25s`.
- **Môi trường có tiếng quạt/ồn nền nhẹ**: nâng lên `--edit audio:threshold=6%`.
- **Dự phòng nếu lỗi NVENC**: đổi `--video-codec h264_nvenc` thành `--video-codec libx264`.

---

## 3. Tẩy Xóa Phụ Đề Cứng / Watermark (`VSR AI`)

Dùng để làm sạch phụ đề dính cứng (hardsub) hoặc logo góc màn hình trên video nguồn trước khi đưa vào dựng.

### Lệnh chuẩn:
```powershell
& "F:\A_Tool\Tools\video-subtitle-remover\vsr.bat" -i "<duong_dan\input_video.mp4>" -o "<PROJECT_DIR>\temp_assets\preprocess\input_video_nosub.mp4"
```

### Lưu ý vận hành an toàn cho VSR:
- Nếu chưa rõ các cờ tùy chọn vùng chọn (ROI/tọa độ) của bản `vsr.bat` hiện tại, chạy `& "F:\A_Tool\Tools\video-subtitle-remover\vsr.bat" --help` trước khi thực thi.
- Với video độ phân giải cao (2K/4K) hoặc thời lượng dài (> 5 phút), nên cắt đoạn cần dùng trước rồi mới đưa qua VSR để tránh tràn VRAM RTX 3060.

---

## 4. Tải Video, B-Roll, Meme & Âm Thanh Không Bản Quyền (`yt-dlp`)

Luôn ép container về **MP4 (codec hình H.264 `avc1` + codec tiếng AAC `mp4a`)** hoặc **MP3/WAV** cho âm thanh. Tuyệt đối tránh tải mặc định định dạng `.webm` (VP9/AV1) vì dễ gây giật lag hoặc lỗi giải mã khi đưa vào timeline Concat.

### 4.1. Tải video chất lượng cao chuẩn H.264/MP4 (Đơn lẻ, chống tải nhầm cả playlist):
```powershell
& "F:\A_Tool\Tools\yt-dlp\yt-dlp.bat" --no-playlist --restrict-filenames -f "bv*[vcodec^=avc1]+ba[acodec^=mp4a]/b[ext=mp4]" --merge-output-format mp4 -o "<PROJECT_DIR>\temp_assets\preprocess\%(title)s.%(ext)s" "<URL>"
```

### 4.2. Chỉ tải đúng trích đoạn ngắn từ video dài (Tiết kiệm 95% thời gian & dung lượng):
Dùng khi cần trích `3–7 giây` B-roll hoặc meme từ một video dài:
```powershell
& "F:\A_Tool\Tools\yt-dlp\yt-dlp.bat" --no-playlist --restrict-filenames --download-sections "*00:01:15-00:01:22" --force-keyframes-at-cuts -f "bv*[vcodec^=avc1]+ba[acodec^=mp4a]/b[ext=mp4]" --merge-output-format mp4 -o "<PROJECT_DIR>\temp_assets\preprocess\broll_%(id)s.%(ext)s" "<URL>"
```

### 4.3. Tìm & Tải Nhạc Nền Không Bản Quyền (BGM — Lọc tự động video < 5 phút):
Luôn đính kèm từ khóa an toàn bản quyền (`no copyright`, `royalty free`, `NCS`, `Kevin MacLeod`) và bộ lọc `--match-filter "duration < 300"` để tránh tải nhầm livestream/mix dài hàng giờ:
```powershell
& "F:\A_Tool\Tools\yt-dlp\yt-dlp.bat" --no-playlist --restrict-filenames --match-filter "duration < 300" -x --audio-format mp3 --audio-quality 0 -o "<PROJECT_DIR>\temp_assets\preprocess\bgm_raw_%(id)s.%(ext)s" "ytsearch1:<tu_khoa_nhac> no copyright background music"
```

### 4.4. Tìm & Tải Hiệu Ứng Âm Thanh (SFX — Lọc tự động < 15 giây):
Dùng cho các tiếng động chuyển cảnh (`whoosh`, `pop`, `ding`, `glitch`, `vine boom`, `cash register`):
```powershell
& "F:\A_Tool\Tools\yt-dlp\yt-dlp.bat" --no-playlist --restrict-filenames --match-filter "duration < 15" -x --audio-format mp3 --audio-quality 0 -o "<PROJECT_DIR>\temp_assets\preprocess\sfx_raw_%(id)s.%(ext)s" "ytsearch1:<ten_sfx> sound effect no copyright"
```

### 4.5. Tìm & Tải Meme Video / Green-Screen Meme (< 20 giây):
```powershell
& "F:\A_Tool\Tools\yt-dlp\yt-dlp.bat" --no-playlist --restrict-filenames --match-filter "duration < 20" -f "bv*[vcodec^=avc1]+ba[acodec^=mp4a]/b[ext=mp4]" --merge-output-format mp4 -o "<PROJECT_DIR>\temp_assets\preprocess\meme_raw_%(id)s.%(ext)s" "ytsearch1:<ten_meme> green screen meme"
```

### 4.6. Tải âm thanh gốc không nén (WAV 48kHz — dùng khi cần xử lý giọng đọc/lọc tạp âm sâu):
```powershell
& "F:\A_Tool\Tools\yt-dlp\yt-dlp.bat" --no-playlist --restrict-filenames -x --audio-format wav --postprocessor-args "ffmpeg:-ar 48000" -o "<PROJECT_DIR>\temp_assets\preprocess\%(title)s.%(ext)s" "<URL>"
```

---

## 5. Chuẩn Hóa Âm Lượng (LUFS) & Tách Phông Xanh Meme (`FFmpeg`)

Mọi tài nguyên tải từ internet **bắt buộc** qua bước hậu xử lý nhanh bằng `FFmpeg` trước khi bàn giao cho `dynamic-visual-enhancer` hoặc nạp vào Concat MCP để tránh lệch âm lượng hoặc còn nền xanh:

1. **Chuẩn hóa Nhạc Nền (BGM $\rightarrow$ `-24 LUFS` êm dịu, không đè giọng đọc):**
   ```powershell
   conda run -n NttDzEditVideo ffmpeg -y -i "<PROJECT_DIR>\temp_assets\preprocess\bgm_raw.mp3" -af "loudnorm=I=-24:TP=-2.0:LRA=11" -c:a libmp3lame -b:a 192k "<PROJECT_DIR>\temp_assets\preprocess\bgm_ready.mp3"
   ```

2. **Cắt khoảng lặng đầu + Chuẩn hóa SFX (`-14 LUFS` sắc nét, đánh khớp từng frame):**
   ```powershell
   conda run -n NttDzEditVideo ffmpeg -y -i "<PROJECT_DIR>\temp_assets\preprocess\sfx_raw.mp3" -af "silenceremove=start_periods=1:start_duration=0:start_threshold=-45dB,loudnorm=I=-14:TP=-1.5:LRA=7" -c:a libmp3lame -b:a 192k "<PROJECT_DIR>\temp_assets\preprocess\sfx_ready.mp3"
   ```

3. **Tách nền phông xanh Meme $\rightarrow$ `.webm` trong suốt (`yuva420p`) + Chuẩn hóa tiếng (`-16 LUFS`):**
   *(Dùng `-auto-alt-ref 0` để đảm bảo kênh Alpha VP9 hiển thị trong suốt hoàn hảo trên Concat)*
   ```powershell
   conda run -n NttDzEditVideo ffmpeg -y -i "<PROJECT_DIR>\temp_assets\preprocess\meme_raw.mp4" -vf "colorkey=0x00FF00:0.28:0.12,despill=green,format=yuva420p" -af "loudnorm=I=-16:TP=-1.5:LRA=9" -c:v libvpx-vp9 -b:v 2M -auto-alt-ref 0 -c:a libopus "<PROJECT_DIR>\temp_assets\preprocess\meme_01_alpha.webm"
   ```

---

## 6. Trích Xuất Kịch Bản & Căn Mốc Thời Gian Đa Ngôn Ngữ (`WhisperX` + `Demucs`)

Dùng để nghe và chép lời tự động từ video hoặc file âm thanh (hỗ trợ đa ngôn ngữ: tiếng Việt, Anh, Nhật, Hàn, Trung...), khóa chuẩn mốc thời gian từng câu/từ bằng `wav2vec2` và xuất ra kịch bản dạng `[HH:MM:SS -> HH:MM:SS]: Nội dung`.

### 6.1. Trường hợp A — Giọng nói rõ, không lẫn nhạc nền lớn (Chạy thẳng `WhisperX`):
- Chỉ định rõ ngôn ngữ (`--language vi`, `en`, `ja`...) nếu đã biết để tăng tốc độ và độ chính xác; bỏ cờ `--language` nếu cần tự nhận diện đa ngôn ngữ.
```powershell
& "F:\A_Tool\Tools\whisperx\whisperx.bat" "<duong_dan\source_video.mp4>" --model large-v3-turbo --compute_type float16 --batch_size 8 --language vi --output_dir "<PROJECT_DIR>\temp_assets\preprocess" --output_format all
```

### 6.2. Trường hợp B — Video/Audio có lẫn nhạc nền (BGM) hoặc tiếng ồn mạnh (Tách giọng trước):
Chạy **tuần tự** 2 bước để chống ảo giác sinh chữ sai ở đoạn nhạc dạo và không vượt ngưỡng 6GB VRAM:

1. **Bước 1 — Tách riêng track giọng nói (`vocals.wav`) bằng `Demucs`:**
   ```powershell
   & "F:\A_Tool\Tools\demucs\demucs.bat" --two-stems=vocals -n htdemucs "<duong_dan\source_video.mp4>" -o "<PROJECT_DIR>\temp_assets\preprocess\demucs_out"
   ```
   *(File giọng sạch sẽ nằm tại `<PROJECT_DIR>\temp_assets\preprocess\demucs_out\htdemucs\<ten_file_khong_duoi>\vocals.wav`).*

2. **Bước 2 — Chép lời & căn mốc thời gian trên file `vocals.wav` bằng `WhisperX`:**
   ```powershell
   & "F:\A_Tool\Tools\whisperx\whisperx.bat" "<PROJECT_DIR>\temp_assets\preprocess\demucs_out\htdemucs\<ten_file>\vocals.wav" --model large-v3-turbo --compute_type float16 --batch_size 8 --language vi --output_dir "<PROJECT_DIR>\temp_assets\preprocess" --output_format all
   ```

### 6.3. Xuất kịch bản chuẩn `[HH:MM:SS -> HH:MM:SS]: Nội dung` từ file `.json`:
Sau khi `WhisperX` sinh ra file `<ten_file>.json` và `<ten_file>.srt`, chạy lệnh sau để xuất file kịch bản `.txt` đúng chuẩn đọc/dựng:
```powershell
conda run -n NttDzEditVideo python -c "import json, datetime; fmt=lambda s: str(datetime.timedelta(seconds=int(s))).zfill(8); data=json.load(open(r'<PROJECT_DIR>\temp_assets\preprocess\<ten_file>.json', encoding='utf-8')); lines=[f'[{fmt(seg["start"])} -> {fmt(seg["end"])}]: {seg["text"].strip()}' for seg in data['segments']]; open(r'<PROJECT_DIR>\temp_assets\preprocess\transcript_script.txt', 'w', encoding='utf-8').write('
'.join(lines)); print('
'.join(lines))"
```

### Lưu ý hiệu năng & xử lý sự cố VRAM (RTX 3060 6GB):
- Nếu gặp lỗi tràn bộ nhớ GPU (`CUDA out of memory`), giảm `--batch_size 8` xuống `--batch_size 4` (hoặc `--compute_type int8_float16`).
- Với video/audio dài trên **90 phút**, dùng `ffmpeg` cắt nhỏ thành từng đoạn 15–20 phút trước khi chạy `WhisperX` để bộ căn chỉnh `wav2vec2` không chiếm dụng quá nhiều RAM/VRAM.

---

## 7. Quy Trình Kết Hợp (Pipeline Chuẩn) & Kiểm Tra Đầu Ra

Khi người dùng yêu cầu xử lý liên hoàn nhiều bước trên cùng một tư liệu, thực hiện đúng thứ tự tối ưu sau để tiết kiệm thời gian và tài nguyên GPU:

1. **Bước 1 — Thu thập (`yt-dlp`)**: Tải video nguồn chuẩn H.264/MP4 vào `<PROJECT_DIR>\temp_assets\preprocess\source.mp4`.
2. **Bước 2 — Cắt khoảng lặng (`auto-editor`)**: Lọc bỏ đoạn thừa trước (`source_clean.mp4`) để giảm thời lượng video, giúp các bước AI phía sau chạy nhanh hơn và ít tốn VRAM hơn.
3. **Bước 3 — Xóa phụ đề/logo (`VSR`)**: Chạy VSR trên file đã cắt gọn (`source_clean.mp4` $\rightarrow$ `source_ready.mp4`).
4. **Bước 4 — Trích xuất kịch bản (`Demucs` $\rightarrow$ `WhisperX`)**: Tách giọng (nếu có nhạc nền) và xuất `transcript_script.txt` + `.srt` từ `source_ready.mp4`.
5. **Bước 5 — Nghiệm thu & Bàn giao thông số cho Skill kế tiếp**:
   Kiểm tra file kết quả tồn tại, dung lượng `> 0 KB` và đo chính xác `duration` trước khi báo hoàn thành hoặc chuyển sang `subtitle-craft` / `dynamic-visual-enhancer` / `Concat MCP`:
   ```powershell
   Get-Item "<PROJECT_DIR>\temp_assets\preprocess\source_ready.mp4" | Select-Object Name, Length
   conda run -n NttDzEditVideo ffprobe -v error -show_entries format=duration -of default=noprint_wrappers=1:nokey=1 "<PROJECT_DIR>\temp_assets\preprocess\source_ready.mp4"
   ```
