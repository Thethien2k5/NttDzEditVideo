---
name: media-preprocess
description: "Tiền xử lý và thu thập tài nguyên media trước khi dựng phim: cắt bỏ khoảng lặng/nói vấp bằng auto-editor, tẩy xóa phụ đề cứng hoặc logo/watermark bằng VSR AI, và tải video/nhạc nền chuẩn định dạng bằng yt-dlp vào thư mục dự án Concat."
---

# Tiền Xử Lý & Thu Thập Tư Liệu Media (`media-preprocess`)

Tất cả công cụ đều chạy qua file `.bat` kích hoạt sẵn môi trường `NttDzEditVideo` (Python 3.10 + PyTorch CUDA 12.4) trên PowerShell:
- **`auto-editor`**: `F:\A_Tool\Tools\auto-editor\auto-editor.bat`
- **`VSR`**: `F:\A_Tool\Tools\video-subtitle-remover\vsr.bat`
- **`yt-dlp`**: `F:\A_Tool\Tools\yt-dlp\yt-dlp.bat`

---

## 1. Quy Tắc Bắt Buộc Về Lưu Trữ, Tên File & Phần Cứng

1. **Khởi tạo thư mục đích trong dự án Concat (`<PROJECT_DIR>`)**:
   - Trước khi chạy bất kỳ lệnh nào, lấy đường dẫn dự án đang mở qua `project_list` hoặc `timeline_read`.
   - Luôn tạo sẵn thư mục lưu trữ tạm trước khi xuất file:
     ```powershell
     New-Item -ItemType Directory -Force -Path "<PROJECT_DIR>\temp_assets\preprocess" | Out-Null
     ```
   - Toàn bộ file tải về và file sau xử lý **bắt buộc** lưu tại `<PROJECT_DIR>\temp_assets\preprocess\`. Tuyệt đối không ghi đè file gốc và không lưu rác vào thư mục cài đặt Skill.

2. **Chuẩn hóa tên file đầu ra (Chống lỗi chuỗi lệnh)**:
   - Không đặt tên file chứa dấu ngoặc kép, ký tự đặc biệt hoặc emoji. Khi tải từ internet, luôn dùng cờ `--restrict-filenames` để tránh lỗi không đọc được đường dẫn ở các bước xử lý tiếp theo.

3. **Bảo vệ VRAM GPU RTX 3060 (Chạy tuần tự)**:
   - `VSR` sử dụng GPU RTX 3060 (CUDA 12.4) tiêu tốn nhiều VRAM. Chỉ xử lý **từng video một**.
   - **Cấm** chạy đồng thời nhiều tiến trình `vsr.bat`, hoặc chạy `vsr.bat` song song với `vieneu.bat` (TTS) hay tiến trình render của Concat.

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

## 4. Tải Video & Nhạc Nền Chuẩn Dựng Phim (`yt-dlp`)

Luôn ép container về **MP4 (codec hình H.264 `avc1` + codec tiếng AAC `mp4a`)** hoặc **MP3/WAV** cho âm thanh. Tuyệt đối tránh tải mặc định định dạng `.webm` (VP9/AV1) vì dễ gây giật lag hoặc lỗi giải mã khi đưa vào timeline Concat.

### Tải video chất lượng cao chuẩn H.264/MP4 (Đơn lẻ, chống tải nhầm cả playlist):
```powershell
& "F:\A_Tool\Tools\yt-dlp\yt-dlp.bat" --no-playlist --restrict-filenames -f "bv*[vcodec^=avc1]+ba[acodec^=mp4a]/b[ext=mp4]" --merge-output-format mp4 -o "<PROJECT_DIR>\temp_assets\preprocess\%(title)s.%(ext)s" "<URL>"
```

### Tải nhạc nền / hiệu ứng âm thanh (MP3 chất lượng cao nhất):
```powershell
& "F:\A_Tool\Tools\yt-dlp\yt-dlp.bat" --no-playlist --restrict-filenames -x --audio-format mp3 --audio-quality 0 -o "<PROJECT_DIR>\temp_assets\preprocess\%(title)s.%(ext)s" "<URL>"
```

### Tải âm thanh gốc không nén (WAV 48kHz — dùng khi cần xử lý giọng đọc/lọc tạp âm sâu):
```powershell
& "F:\A_Tool\Tools\yt-dlp\yt-dlp.bat" --no-playlist --restrict-filenames -x --audio-format wav --postprocessor-args "ffmpeg:-ar 48000" -o "<PROJECT_DIR>\temp_assets\preprocess\%(title)s.%(ext)s" "<URL>"
```

---

## 5. Quy Trình Kết Hợp (Pipeline Chuẩn) & Kiểm Tra Đầu Ra

Khi người dùng yêu cầu xử lý liên hoàn nhiều bước trên cùng một tư liệu, thực hiện đúng thứ tự tối ưu sau để tiết kiệm thời gian và tài nguyên GPU:

1. **Bước 1 — Thu thập (`yt-dlp`)**: Tải video nguồn chuẩn H.264/MP4 vào `<PROJECT_DIR>\temp_assets\preprocess\source.mp4`.
2. **Bước 2 — Cắt khoảng lặng (`auto-editor`)**: Lọc bỏ đoạn thừa trước (`source_clean.mp4`) để giảm thời lượng video, giúp bước AI phía sau chạy nhanh hơn và ít tốn VRAM hơn.
3. **Bước 3 — Xóa phụ đề/logo (`VSR`)**: Chạy VSR trên file đã cắt gọn (`source_clean.mp4` $\rightarrow$ `source_ready.mp4`).
4. **Bước 4 — Nghiệm thu trước khi bàn giao**:
   Kiểm tra file kết quả tồn tại và dung lượng lớn hơn `0 KB` trước khi báo hoàn thành hoặc chèn vào Concat:
   ```powershell
   Get-Item "<PROJECT_DIR>\temp_assets\preprocess\source_ready.mp4" | Select-Object Name, Length
   ```