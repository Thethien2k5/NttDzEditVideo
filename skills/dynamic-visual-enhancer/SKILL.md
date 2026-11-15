---
name: dynamic-visual-enhancer
description: "Tăng cường thị giác chống nhàm chán cho video dựa trên giọng đọc và hình ảnh: tự động phát hiện khoảng tĩnh > 4s hoặc điểm nhấn lời thoại để tạo chuyển động máy quay ảo (Punch-in Zoom, Ken Burns), sinh đồ họa động trong suốt (.webm) qua hyperframes-motion và dàn lên Concat MCP."
---

# Tăng Cường Thị Giác & Nhịp Điệu Hình Ảnh (`dynamic-visual-enhancer`)

Skill này biến các đoạn video đứng yên, cảnh nói chuyện kéo dài (talking-head) hoặc ảnh tĩnh trở nên sinh động bằng cách đồng bộ hiệu ứng hình ảnh với nhịp điệu giọng đọc và nội dung kịch bản.

- **Môi trường thực thi**: Mọi lệnh CLI (`ffmpeg`, `ffprobe`, script Python phân tích âm thanh/hình ảnh) **bắt buộc** chạy qua `conda run -n NttDzEditVideo` trên PowerShell.
- **Công cụ phối hợp**: Gọi **`hyperframes-motion`** khi cần render đồ họa vector/chữ động trong suốt (`.webm`) và thao tác trên **`Concat MCP`** để dàn lên track video lớp trên.

---

## 1. Quy Tắc Không Gian Lưu Trữ, Định Dạng & Nhịp Thị Giác (Bắt Buộc)

1. **Khởi tạo thư mục lưu trữ tạm trong dự án Concat (`<PROJECT_DIR>`)**:
   - Lấy đường dẫn dự án đang mở qua `project_list` / `timeline_read` và tạo thư mục đích trước khi xuất file:
     ```powershell
     New-Item -ItemType Directory -Force -Path "<PROJECT_DIR>\temp_assets\visual_fx" | Out-Null
     ```
   - Toàn bộ video đã xử lý chuyển động và overlay `.webm` **bắt buộc** lưu tại `<PROJECT_DIR>\temp_assets\visual_fx\` theo quy tắc `fx_<stt>_<giay>s.<ext>`. Tuyệt đối không ghi đè file gốc.

2. **Quy tắc nhịp thị giác 3–5 giây (Visual Pacing Rule)**:
   - Không để một khung hình tĩnh hoặc một góc máy talking-head giữ nguyên quá **4–5 giây** mà không có sự biến đổi thị giác (zoom nhẹ, đổi góc crop, hiện từ khóa minh họa hoặc chèn B-roll).

3. **Chuẩn kênh Alpha (Nền trong suốt) cho lớp đè (Overlay)**:
   - Mọi hoạt ảnh chèn đè lên track video phía trên trong Concat **bắt buộc** xuất định dạng `.webm` hỗ trợ nền trong suốt (`yuva420p` / `libvpx-vp9`) để không che mất hình ảnh lớp dưới.

4. **Bảo vệ GPU RTX 3060**:
   - Chạy tuần tự từng tác vụ render; ưu tiên encoder phần cứng `-c:v h264_nvenc` cho các clip `.mp4` biến đổi góc máy.

---

## 2. Phân Tích Điểm Nhấn Từ Giọng Đọc & Hình Ảnh (Trigger Detection)

Trước khi tạo hiệu ứng, đọc dữ liệu timeline (`timeline_read`) và đối chiếu 3 nguồn tín hiệu sau để xác định các mốc thời gian (`timeline_in_sec`) cần can thiệp:

| Nguồn tín hiệu | Dấu hiệu nhận biết | Hành động thị giác tương ứng |
| :--- | :--- | :--- |
| **Giọng đọc / Kịch bản** | Từ khóa đắt giá, con số thống kê, câu hỏi hoặc đoạn lên cao giọng | Tạo **Kinetic Keyword / Counter Overlay** (`.webm`) hoặc **Punch-in Zoom** đúng lúc từ khóa vang lên. |
| **Âm thanh (`ffprobe` / `ffmpeg`)** | Đỉnh âm lượng đột ngột (nhấn giọng) hoặc khoảng nghỉ chuyển ý (> `0.8s`) | Cắt chuyển góc **Punch-in / Punch-out** tại điểm chuyển ý để tạo nhịp cắt dứt khoát. |
| **Hình ảnh / Video nền** | Cảnh quay đứng yên > `4.5s`, đoạn chia sẻ màn hình khó nhìn, hoặc tư liệu là **ảnh tĩnh** | Áp dụng **Ken Burns (Pan & Zoom)** cho ảnh tĩnh, hoặc tạo **Callout / Khoanh vùng** làm rõ chi tiết. |

---

## 3. Bộ Kỹ Thuật Biến Đổi Thị Giác & Lệnh Thực Thi

### Kỹ thuật A: Chuyển động máy quay ảo (`FFmpeg` — Tự thích ứng 16:9 và 9:16)

1. **Punch-in Zoom (Phóng cận 112% tại câu nhấn mạnh — Giữ nguyên khung hình gốc):**
   Dùng để tạo hiệu ứng nhảy góc máy (jump-zoom) cho video talking-head mà không làm méo tỷ lệ khung hình (tự động nhận diện cả video ngang `1920x1080` lẫn video dọc `1080x1920`):
   ```powershell
   conda run -n NttDzEditVideo ffmpeg -y -i "<duong_dan\clip_goc.mp4>" -vf "scale=iw*1.12:ih*1.12,crop=iw/1.12:ih/1.12:(iw-ow)/2:(ih-oh)/2" -c:v h264_nvenc -cq 20 -c:a copy "<PROJECT_DIR>\temp_assets\visual_fx\fx_01_punchin.mp4"
   ```

2. **Ken Burns Effect (Chuyển động Pan & Zoom mượt cho ảnh tĩnh):**
   Biến ảnh tĩnh (`.jpg`, `.png`) thành video chuyển động mượt trong thời lượng `<SO_GIAY>` giây (ví dụ `5s` ở `30fps` $\rightarrow$ `d=150` frame; thay `<W>x<H>` bằng kích thước dự án Concat như `1920x1080` hoặc `1080x1920`):
   ```powershell
   conda run -n NttDzEditVideo ffmpeg -y -loop 1 -i "<duong_dan\anh_tinh.png>" -vf "scale=8000:-1,zoompan=z='min(zoom+0.0012,1.15)':d=150:x='iw/2-(iw/zoom/2)':y='ih/2-(ih/zoom/2)':s=<W>x<H>:fps=30" -t 5 -c:v h264_nvenc -pix_fmt yuv420p "<PROJECT_DIR>\temp_assets\visual_fx\fx_02_kenburns.mp4"
   ```

### Kỹ thuật B: Đồ họa động đè lớp qua `hyperframes-motion` (Overlay `.webm`)

Khi lời thoại nhắc đến khái niệm quan trọng, số liệu hoặc bước hướng dẫn, điều phối sang **`hyperframes-motion`** để sinh clip overlay nền trong suốt (`<PROJECT_DIR>\temp_assets\visual_fx\fx_<stt>_<giay>s.webm`) thuộc một trong các nhóm sau:
- **Keyword Pop-up / Highlight Badge**: Nhãn chữ từ khóa bật nảy ở 1/3 dưới hoặc góc khung hình trong `2.0s – 3.0s`.
- **Animated Counter / Metric Card**: Con số/tỷ lệ phần trăm chạy tăng dần khớp với lời đọc số liệu.
- **Callout Arrow / Focus Frame**: Mũi tên chỉ điểm hoặc khung sáng khoanh vùng chi tiết khi làm video hướng dẫn/review.
- **Retention Progress Bar**: Thanh tiến trình chạy dọc mép màn hình giúp tăng tỷ lệ xem hết video.

### Kỹ thuật C: Chèn cảnh minh họa nhanh (Cutaway B-Roll 2–3 giây)

Nếu giọng đọc mô tả một sự vật/bối cảnh mà video gốc không có hình ảnh minh họa:
- Lấy clip B-roll có sẵn trong dự án hoặc gọi **`media-preprocess`** (`yt-dlp` nguồn Creative Commons) tải đoạn minh họa ngắn, cắt gọn `2.5s – 3.5s` và đặt lên track video phía trên để che đi khoảng trống thị giác.

---

## 4. Quy Trình Nghiệm Thu & Dàn Lên Timeline Concat MCP

1. **Kiểm tra thông số dự án**: Gọi `timeline_read` để xác nhận độ phân giải (`width`, `height`), `fps`, danh sách track video (`lane_id`) và vị trí các clip thoại hiện có.
2. **Xác minh tài nguyên đầu ra**: Trước khi đưa vào Concat, kiểm tra mọi file trong `<PROJECT_DIR>\temp_assets\visual_fx\` tồn tại, dung lượng `> 0 KB` và đo chính xác `duration`:
   ```powershell
   conda run -n NttDzEditVideo ffprobe -v error -show_entries format=duration -of default=noprint_wrappers=1:nokey=1 "<PROJECT_DIR>\temp_assets\visual_fx\fx_01_punchin.mp4"
   ```
3. **Nạp & sắp xếp trên Concat MCP**:
   - Gọi `media_import` để đưa file vào kho dự án.
   - Với **Overlay `.webm` / B-Roll**: Dùng `clip_add` đặt lên **track video lớp trên (`overlay_lane_id`)** tại đúng mốc `timeline_in_sec` của từ khóa/nhịp thoại.
   - Với **Punch-in / Ken Burns `.mp4`**: Dùng `clips_split` tại điểm nhấn trên track chính và thay thế đoạn tĩnh bằng clip đã tạo chuyển động.
4. **Lưu đồng bộ**: Gọi `project_save` để cập nhật lên giao diện Concat (tuyệt đối không tự gọi `export_start`).