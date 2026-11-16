---
name: dynamic-visual-enhancer
description: "Tăng cường thị giác, âm thanh và nhịp điệu chống nhàm chán cho video dựa trên giọng đọc và hình ảnh: điều phối liên hoàn media-preprocess (nhạc nền không bản quyền, SFX, meme phông xanh, B-roll) và hyperframes-motion (đồ họa động .webm), tự động phát hiện khoảng tĩnh > 4s hoặc điểm nhấn lời thoại để tạo chuyển động máy quay ảo (Punch-in Zoom, Ramp Zoom, Impact Shake, Ken Burns) và dàn đa tầng lên Concat MCP."
---

# Tăng Cường Thị Giác, Âm Thanh & Nhịp Điệu (`dynamic-visual-enhancer`)

Skill này đóng vai trò **Đạo Diễn Nhịp Điệu Trung Tâm**, biến các đoạn video đứng yên, cảnh nói chuyện kéo dài (talking-head) hoặc ảnh tĩnh trở nên lôi cuốn bằng cách đồng bộ **chuyển động hình ảnh + đồ họa động + meme + nhạc nền & SFX** theo từng nhịp lời thoại.

- **Môi trường thực thi**: Mọi lệnh CLI (`ffmpeg`, `ffprobe`, script Python phân tích âm thanh/hình ảnh) **bắt buộc** chạy qua `conda run -n NttDzEditVideo` trên PowerShell.
- **Hệ sinh thái phối hợp**:
  1. Gọi **`media-preprocess`** để tải & chuẩn hóa âm lượng (`LUFS`) nhạc nền không bản quyền (`bgm_*`), hiệu ứng âm thanh (`sfx_*`), B-roll minh họa (`broll_*`) và tách nền meme phông xanh (`meme_*_alpha.webm`).
  2. Gọi **`hyperframes-motion`** để render đồ họa vector/chữ động/biểu đồ trong suốt (`.webm` Alpha).
  3. Thao tác trực tiếp trên **`Concat MCP`** để dàn đa tầng hình ảnh và âm thanh.

---

## 1. Quy Tắc Không Gian Lưu Trữ, Định Dạng & Nhịp Thị Giác (Bắt Buộc)

1. **Khởi tạo thư mục lưu trữ tạm trong dự án Concat (`<PROJECT_DIR>`)**:
   - Lấy đường dẫn dự án đang mở qua `project_list` / `timeline_read` và tạo thư mục đích trước khi xuất file:
     ```powershell
     New-Item -ItemType Directory -Force -Path "<PROJECT_DIR>\temp_assets\visual_fx" | Out-Null
     ```
   - Toàn bộ video đã xử lý chuyển động và overlay `.webm` **bắt buộc** lưu tại `<PROJECT_DIR>\temp_assets\visual_fx\` theo quy tắc `fx_<stt>_<giay>s.<ext>`. Tuyệt đối không ghi đè file gốc.

2. **Quy tắc nhịp thị giác 3–5 giây (Visual Pacing Rule)**:
   - Không để một khung hình tĩnh hoặc một góc máy talking-head giữ nguyên quá **4–5 giây** mà không có sự biến đổi thị giác (zoom nhẹ, đổi góc crop, hiện từ khóa minh họa, chèn meme hoặc B-roll).

3. **Chuẩn kênh Alpha (Nền trong suốt) cho lớp đè (Overlay)**:
   - Mọi hoạt ảnh hoặc meme chèn đè lên track video phía trên trong Concat **bắt buộc** xuất định dạng `.webm` hỗ trợ nền trong suốt (`yuva420p` / `libvpx-vp9` với `-auto-alt-ref 0`) để không che mất hình ảnh lớp dưới.

4. **Bảo vệ GPU RTX 3060**:
   - Chạy tuần tự từng tác vụ render; ưu tiên encoder phần cứng `-c:v h264_nvenc` cho các clip `.mp4` biến đổi góc máy.

---

## 2. Phân Tích Điểm Nhấn & Lập Bảng Nhịp Audio-Visual (Trigger Detection)

Trước khi gọi bất kỳ lệnh render nào, đọc dữ liệu timeline (`timeline_read`) và lời thoại/phụ đề để lập một **Kế hoạch Nhịp Điệu (Beat Sheet)** đối chiếu 4 nguồn tín hiệu sau:

| Nguồn tín hiệu | Dấu hiệu nhận biết | Hành động Thị Giác & Âm Thanh tương ứng |
| :--- | :--- | :--- |
| **Giọng đọc / Từ khóa đắt giá** | Khái niệm chính, con số thống kê, câu hỏi mở đầu (Hook), liệt kê bước 1-2-3 | Gọi **`hyperframes-motion`** tạo **Keyword Callout / Counter Overlay** (`.webm`) + ghép **`sfx_pop` / `sfx_ding`** từ `media-preprocess`. |
| **Tình huống hài hước / Bất ngờ / Twist** | Câu nói châm biếm, phản ứng bất ngờ, ví von đời thường | Gọi **`media-preprocess`** tải **Meme phông xanh (`.webm` Alpha)** hoặc **Cutaway Meme (`1.5–2.5s`)** + **`sfx_boom` / `Impact Shake`** + tạm ngắt nhạc nền BGM để tạo điểm rơi hài hước. |
| **Âm thanh (`ffprobe` / `ffmpeg`)** | Đỉnh âm lượng nhấn giọng hoặc khoảng nghỉ chuyển ý (> `0.8s`) | Cắt chuyển góc **Punch-in / Punch-out** tại điểm chuyển ý + ghép **`sfx_whoosh`** mượt mà. |
| **Hình ảnh / Video nền** | Cảnh quay đứng yên > `4.5s`, đoạn mô tả sự vật bên ngoài, hoặc tư liệu là **ảnh tĩnh** | Áp dụng **Smooth Ramp Zoom** / **Ken Burns (Pan & Zoom)** cho ảnh tĩnh, hoặc gọi **`media-preprocess`** chèn **Cutaway B-Roll (`2.5–3.5s`)**. |

---

## 3. Bộ Kỹ Thuật Biến Đổi Thị Giác & Hiệu Ứng (`FFmpeg` NVENC)

### Kỹ thuật A: Chuyển động máy quay ảo (Tự thích ứng 16:9 và 9:16)

1. **Punch-in Zoom (Phóng cận 112% dứt khoát tại câu nhấn mạnh):**
   Tạo hiệu ứng nhảy góc máy (jump-zoom) cho video talking-head mà không làm méo tỷ lệ khung hình:
   ```powershell
   conda run -n NttDzEditVideo ffmpeg -y -i "<duong_dan\clip_goc.mp4>" -vf "scale=iw*1.12:ih*1.12,crop=iw/1.12:ih/1.12:(iw-ow)/2:(ih-oh)/2" -c:v h264_nvenc -cq 20 -c:a copy "<PROJECT_DIR>\temp_assets\visual_fx\fx_01_punchin.mp4"
   ```

2. **Smooth Ramp Zoom (Zoom đẩy mượt từ 100% $\rightarrow$ 112% trong 3 giây):**
   Dùng cho câu dẫn nhập hoặc đoạn kể chuyện cần kéo sự tập trung dần dần (thay `<W>` và `<H>` bằng kích thước dự án Concat như `1920` và `1080` hoặc `1080` và `1920`):
   ```powershell
   conda run -n NttDzEditVideo ffmpeg -y -i "<duong_dan\clip_goc.mp4>" -vf "scale=w='<W>*(1+0.12*min(t/3.0,1))':h='<H>*(1+0.12*min(t/3.0,1))':eval=frame,crop=<W>:<H>:(in_w-<W>)/2:(in_h-<H>)/2" -c:v h264_nvenc -cq 20 -c:a copy "<PROJECT_DIR>\temp_assets\visual_fx\fx_02_rampzoom.mp4"
   ```

3. **Impact Camera Shake (Rung chấn nhẹ 0.25s khi gặp cú twist / meme):**
   ```powershell
   conda run -n NttDzEditVideo ffmpeg -y -i "<duong_dan\clip_goc.mp4>" -vf "scale='trunc(<W>*1.06/2)*2':'trunc(<H>*1.06/2)*2',crop=<W>:<H>:'(in_w-<W>)/2 + if(lt(t,0.25), sin(t*90)*18*(1-t/0.25), 0)':'(in_h-<H>)/2 + if(lt(t,0.25), cos(t*75)*12*(1-t/0.25), 0)'" -c:v h264_nvenc -cq 20 -c:a copy "<PROJECT_DIR>\temp_assets\visual_fx\fx_03_shake.mp4"
   ```

4. **Ken Burns Effect (Chuyển động Pan & Zoom mượt cho ảnh tĩnh):**
   Biến ảnh tĩnh (`.jpg`, `.png`) thành video chuyển động mượt trong thời lượng `<SO_GIAY>` giây (ví dụ `5s` ở `30fps` $\rightarrow$ `d=150` frame; thay `<W>x<H>` bằng kích thước dự án Concat):
   ```powershell
   conda run -n NttDzEditVideo ffmpeg -y -loop 1 -i "<duong_dan\anh_tinh.png>" -vf "scale=8000:-1,zoompan=z='min(zoom+0.0012,1.15)':d=150:x='iw/2-(iw/zoom/2)':y='ih/2-(ih/zoom/2)':s=<W>x<H>:fps=30" -t 5 -c:v h264_nvenc -pix_fmt yuv420p "<PROJECT_DIR>\temp_assets\visual_fx\fx_04_kenburns.mp4"
   ```

### Kỹ thuật B: Đồ họa động đè lớp qua `hyperframes-motion` (Overlay `.webm`)
Điều phối sang **`hyperframes-motion`** để sinh clip overlay nền trong suốt (`<PROJECT_DIR>\temp_assets\motion\clip_XX\output.webm`):
- **Hook Title / Keyword Pop-up**: Nhãn từ khóa bật nảy ở 1/3 trên hoặc góc khung hình trong `1.4s – 2.5s`.
- **Animated Counter / Metric Card**: Con số/tỷ lệ phần trăm chạy tăng dần khớp với lời đọc số liệu.
- **Callout Arrow / Focus Frame**: Mũi tên chỉ điểm hoặc khung sáng khoanh vùng chi tiết khi làm video hướng dẫn/review.
- **Retention Progress Bar**: Thanh tiến trình chạy dọc mép màn hình giúp tăng tỷ lệ xem hết video.

### Kỹ thuật C: Chèn B-Roll Minh Họa & Meme Đa Tầng qua `media-preprocess`
1. **Cutaway B-Roll (`2.5s – 3.5s`)**: Gọi `media-preprocess` tải đoạn minh họa Creative Commons chuẩn H.264/MP4, đặt lên `Video Track 2` để che đi khoảng trống thị giác mà vẫn giữ nguyên giọng đọc bên dưới.
2. **Meme Phông Xanh / Meme Phản Ứng**:
   - Với meme đã tách nền xanh (`meme_*_alpha.webm` từ `media-preprocess`): đặt trực tiếp lên `Video Track 3` (Overlay Alpha) tại đúng câu nói hài hước.
   - Với meme khung chữ nhật (không có phông xanh) cần hiện góc màn hình kiểu Picture-in-Picture mà không che mặt nhân vật: đóng gói thành khung `.webm` trong suốt đặt sẵn ở góc phải trên (`x = <W> - ow - 40`, `y = 80`) để nạp thẳng vào Concat MCP:
     ```powershell
     conda run -n NttDzEditVideo ffmpeg -y -f lavfi -i "color=c=black@0.0:s=<W>x<H>:r=<FPS>:d=<DUR>,format=yuva420p" -i "<PROJECT_DIR>\temp_assets\preprocess\meme_clip.mp4" -filter_complex "[1:v]scale=w='trunc(<W>*0.36/2)*2':h=-2[pip];[0:v][pip]overlay=x='<W>-w-40':y=80:shortest=1,format=yuva420p" -c:v libvpx-vp9 -b:v 2M -auto-alt-ref 0 -c:a libopus "<PROJECT_DIR>\temp_assets\visual_fx\fx_05_pip_meme.webm"
     ```

---

## 4. Thiết Kế Âm Thanh Đa Lớp (BGM Không Bản Quyền & SFX Đồng Bộ)

Để video cuốn hút ở cả phần nghe lẫn phần nhìn, luôn triển khai đồng thời 2 lớp âm thanh phụ trợ thông qua `media-preprocess`:

1. **Lớp Nhạc Nền Không Bản Quyền (`BGM` — `Audio Track 3`)**:
   - Chọn thể loại nhạc khớp cảm xúc video (`upbeat tech`, `chill lofi`, `cinematic tension`, `acoustic vlog`) và tải qua `media-preprocess` (`bgm_ready.mp3` đã chuẩn hóa `-24 LUFS`).
   - Cắt vừa đúng tổng thời lượng video và thêm fade-in `1.0s` đầu video + fade-out `2.0s` cuối video để kết thúc êm ái:
     ```powershell
     conda run -n NttDzEditVideo ffmpeg -y -stream_loop -1 -i "<PROJECT_DIR>\temp_assets\preprocess\bgm_ready.mp3" -t <TONG_THOI_LUONG_VIDEO> -af "afade=t=in:st=0:d=1.0,afade=t=out:st=<TONG_THOI_LUONG_VIDEO_TRU_2>:d=2.0" -c:a libmp3lame -b:a 192k "<PROJECT_DIR>\temp_assets\visual_fx\bgm_timeline_full.mp3"
     ```
   - **Mẹo tạo điểm nhấn hài hước / cao trào**: Khi chèn meme hoặc câu chốt bất ngờ, ngắt đoạn clip BGM tại khoảng `1.5s` đó trên timeline Concat để giọng thoại hoặc tiếng meme vang lên nổi bật rồi mới cho nhạc chạy tiếp.

2. **Lớp Hiệu Ứng Âm Thanh (`SFX` — `Audio Track 2`)**:
   - Tải sẵn bộ `3–5` file `sfx_ready.mp3` ngắn gọn từ `media-preprocess` (`whoosh`, `pop`, `ding`, `boom`) và đặt chính xác tại các mốc chuyển động:
     - Cắt chuyển góc `Punch-in` / `Impact Shake` $\rightarrow$ đặt `sfx_whoosh` tại `timeline_in_sec - 0.1s`.
     - Đồ họa `hyperframes-motion` bật lên $\rightarrow$ đặt `sfx_pop` / `sfx_ding` khớp mốc `in_offset` / `impact_offset`.

---

## 5. Quy Trình Nghiệm Thu & Dàn Đa Tầng Lên Timeline Concat MCP

1. **Kiểm tra thông số dự án**: Gọi `timeline_read` để xác nhận độ phân giải (`width`, `height`), `fps`, danh sách track video/audio (`lane_id`) và vị trí các clip thoại hiện có.
2. **Xác minh tài nguyên đầu ra**: Trước khi đưa vào Concat, kiểm tra mọi file trong `<PROJECT_DIR>\temp_assets\visual_fx\` (và các file liên quan từ `preprocess\`, `motion\`) tồn tại, dung lượng `> 0 KB` và đo chính xác `duration`:
   ```powershell
   conda run -n NttDzEditVideo ffprobe -v error -show_entries format=duration -of default=noprint_wrappers=1:nokey=1 "<PROJECT_DIR>\temp_assets\visual_fx\fx_01_punchin.mp4"
   ```
3. **Nạp & Sắp xếp theo Sơ Đồ Tầng Chuẩn trên Concat MCP**:
   - Gọi `media_import` để đưa toàn bộ clip biến đổi, đồ họa `.webm`, meme, B-roll, SFX và BGM vào kho dự án.
   - **Track Video 1 (Base)**: Dùng `clips_split` tại điểm nhấn trên track chính và thay thế đoạn tĩnh bằng clip `Punch-in` / `Ramp Zoom` / `Impact Shake` / `Ken Burns`.
   - **Track Video 2 (B-Roll)**: Dùng `clip_add` đặt B-roll minh họa (`2.5–3.5s`) đè lên đoạn thoại mô tả bối cảnh.
   - **Track Video 3 (Overlay Alpha trên cùng)**: Dùng `clip_add` đặt đồ họa `.webm` (`hyperframes-motion`) và meme tách nền/PiP `.webm` tại đúng `timeline_in_sec`.
   - **Track Audio 2 (SFX & Meme Audio)**: Dùng `clip_add` đặt các file `sfx_*.mp3` khớp từng frame với chuyển động hình ảnh.
   - **Track Audio 3 (BGM)**: Dùng `clip_add` đặt `bgm_timeline_full.mp3` từ `0.0s` (cắt khoảng trống tại các nhịp meme nếu cần).
4. **Lưu đồng bộ**: Gọi `project_save` để cập nhật lên giao diện Concat (tuyệt đối không tự gọi `export_start`).
