---
name: dynamic-visual-enhancer
description: "Tăng cường thị giác, âm thanh và nhịp điệu chống nhàm chán cho video dựa trên giọng đọc và hình ảnh: điều phối liên hoàn media-preprocess (nhạc nền không bản quyền, SFX, meme phông xanh, B-roll), hyperframes-motion (đồ họa động .webm đa engine) và chuyển cảnh shader nghệ thuật (PixiJS + GL Transitions), tự động phát hiện khoảng tĩnh > 4s hoặc điểm nhấn lời thoại để tạo chuyển động máy quay ảo (Punch-in Zoom, Ramp Zoom, Impact Shake, Ken Burns) và dàn đa tầng lên Concat MCP."
---

# Tăng Cường Thị Giác, Âm Thanh & Nhịp Điệu (`dynamic-visual-enhancer`)

Skill này đóng vai trò **Đạo Diễn Nhịp Điệu Trung Tâm**, biến các đoạn video đứng yên, cảnh nói chuyện kéo dài (talking-head) hoặc ảnh tĩnh trở nên lôi cuốn bằng cách đồng bộ **chuyển động hình ảnh + chuyển cảnh GLSL + đồ họa động + meme + nhạc nền & SFX** theo từng nhịp lời thoại.

- **Môi trường thực thi**: Mọi lệnh CLI (`ffmpeg`, `ffprobe`, script Python phân tích âm thanh/hình ảnh) **bắt buộc** chạy qua `conda run -n NttDzEditVideo` trên PowerShell.
- **Hệ sinh thái phối hợp**:
  1. Gọi **`media-preprocess`** để tải & chuẩn hóa âm lượng (`LUFS`) nhạc nền không bản quyền (`bgm_*`), hiệu ứng âm thanh (`sfx_*`), B-roll minh họa (`broll_*`) và tách nền meme phông xanh (`meme_*_alpha.webm`).
  2. Gọi **`hyperframes-motion`** để render đồ họa vector/chữ động/hạt không khí/vật lý/3D/sóng âm trong suốt (`.webm` Alpha).
  3. Dùng **`PixiJS + GL Transitions`** (qua `hyperframes.bat` và kho cục bộ `F:\A_Tool\Tools\hyperframes\vendor\`) khi cần chuyển cảnh shader nghệ thuật giữa 2 ảnh AI từ ComfyUI hoặc tạo hiệu ứng parallax 2.5D / glitch nhấn nhịp.
  4. Thao tác trực tiếp trên **`Concat MCP`** để dàn đa tầng hình ảnh và âm thanh.

---

## 1. Quy Tắc Không Gian Lưu Trữ, Định Dạng & Nhịp Thị Giác (Bắt Buộc)

1. **Khởi tạo thư mục lưu trữ tạm trong dự án Concat (`<PROJECT_DIR>`)**:
   - Lấy đường dẫn dự án đang mở qua `project_list` / `timeline_read` và tạo thư mục đích trước khi xuất file:
     ```powershell
     New-Item -ItemType Directory -Force -Path "<PROJECT_DIR>\temp_assets\visual_fx" | Out-Null
     ```
   - Toàn bộ video đã xử lý chuyển động, chuyển cảnh GLSL và overlay `.webm` **bắt buộc** lưu tại `<PROJECT_DIR>\temp_assets\visual_fx\` theo quy tắc `fx_<stt>_<giay>s.<ext>`. Tuyệt đối không ghi đè file gốc.

2. **Quy tắc nhịp thị giác 3–5 giây (Visual Pacing Rule)**:
   - Không để một khung hình tĩnh hoặc một góc máy talking-head giữ nguyên quá **4–5 giây** mà không có sự biến đổi thị giác (zoom nhẹ, đổi góc crop, chuyển cảnh shader, hiện từ khóa minh họa, chèn meme hoặc B-roll).

3. **Chuẩn kênh Alpha (Nền trong suốt) cho lớp đè (Overlay)**:
   - Mọi hoạt ảnh hoặc meme chèn đè lên track video phía trên trong Concat **bắt buộc** xuất định dạng `.webm` hỗ trợ nền trong suốt (`yuva420p` / `libvpx-vp9` với `-auto-alt-ref 0`) để không che mất hình ảnh lớp dưới.

4. **Bảo vệ GPU RTX 3060**:
   - Chạy tuần tự từng tác vụ render; ưu tiên encoder phần cứng `-c:v h264_nvenc` cho các clip `.mp4` biến đổi góc máy.

---

## 2. Phân Tích Điểm Nhấn & Lập Bảng Nhịp Audio-Visual (Trigger Detection)

Trước khi gọi bất kỳ lệnh render nào, đọc dữ liệu timeline (`timeline_read`) và lời thoại/phụ đề để lập một **Kế hoạch Nhịp Điệu (Beat Sheet)** đối chiếu 4 nguồn tín hiệu sau:

| Nguồn tín hiệu | Dấu hiệu nhận biết | Hành động Thị Giác & Âm Thanh tương ứng |
| :--- | :--- | :--- |
| **Giọng đọc / Từ khóa đắt giá** | Khái niệm chính, con số thống kê, câu hỏi mở đầu (Hook), liệt kê bước 1-2-3 | Gọi **`hyperframes-motion`** tạo **Keyword Callout / Counter / Physics Tag Overlay** (`.webm`) + ghép **`sfx_pop` / `sfx_ding`** từ `media-preprocess`. |
| **Tình huống hài hước / Bất ngờ / Twist** | Câu nói châm biếm, phản ứng bất ngờ, ví von đời thường | Gọi **`media-preprocess`** tải **Meme phông xanh (`.webm` Alpha)** hoặc **Cutaway Meme (`1.5–2.5s`)** + **`sfx_boom` / `Impact Shake` / `Glitch Shader`** + tạm ngắt nhạc nền BGM để tạo điểm rơi hài hước. |
| **Âm thanh (`ffprobe` / `ffmpeg`)** | Đỉnh âm lượng nhấn giọng hoặc khoảng nghỉ chuyển ý (> `0.8s`) | Cắt chuyển góc **Punch-in / Punch-out** tại điểm chuyển ý + ghép **`sfx_whoosh`** mượt mà. |
| **Hình ảnh / Video nền** | Cảnh quay đứng yên > `4.5s`, chuỗi ảnh minh họa từ `comfyui-image-gen`, hoặc B-roll nối tiếp | Áp dụng **Ken Burns** / **PixiJS 2.5D Parallax** cho ảnh tĩnh, hoặc dùng **GL Transitions** nối mượt 2 ảnh/clip B-roll (`0.6s – 1.0s`). |

---

## 3. Bộ Kỹ Thuật Biến Đổi Thị Giác & Hiệu Ứng

### Kỹ thuật A: Chuyển động máy quay ảo tốc độ cao (`FFmpeg` NVENC)

1. **Punch-in Zoom (Phóng cận 112% dứt khoát tại câu nhấn mạnh):**
   ```powershell
   conda run -n NttDzEditVideo ffmpeg -y -i "<duong_dan\clip_goc.mp4>" -vf "scale=iw*1.12:ih*1.12,crop=iw/1.12:ih/1.12:(iw-ow)/2:(ih-oh)/2" -c:v h264_nvenc -cq 20 -c:a copy "<PROJECT_DIR>\temp_assets\visual_fx\fx_01_punchin.mp4"
   ```

2. **Smooth Ramp Zoom (Zoom đẩy mượt từ 100% $\rightarrow$ 112% trong 3 giây):**
   ```powershell
   conda run -n NttDzEditVideo ffmpeg -y -i "<duong_dan\clip_goc.mp4>" -vf "scale=w='<W>*(1+0.12*min(t/3.0,1))':h='<H>*(1+0.12*min(t/3.0,1))':eval=frame,crop=<W>:<H>:(in_w-<W>)/2:(in_h-<H>)/2" -c:v h264_nvenc -cq 20 -c:a copy "<PROJECT_DIR>\temp_assets\visual_fx\fx_02_rampzoom.mp4"
   ```

3. **Impact Camera Shake (Rung chấn nhẹ 0.25s khi gặp cú twist / meme):**
   ```powershell
   conda run -n NttDzEditVideo ffmpeg -y -i "<duong_dan\clip_goc.mp4>" -vf "scale='trunc(<W>*1.06/2)*2':'trunc(<H>*1.06/2)*2',crop=<W>:<H>:'(in_w-<W>)/2 + if(lt(t,0.25), sin(t*90)*18*(1-t/0.25), 0)':'(in_h-<H>)/2 + if(lt(t,0.25), cos(t*75)*12*(1-t/0.25), 0)'" -c:v h264_nvenc -cq 20 -c:a copy "<PROJECT_DIR>\temp_assets\visual_fx\fx_03_shake.mp4"
   ```

4. **Ken Burns Effect (Chuyển động Pan & Zoom mượt cho ảnh tĩnh):**
   ```powershell
   conda run -n NttDzEditVideo ffmpeg -y -loop 1 -i "<duong_dan\anh_tinh.png>" -vf "scale=8000:-1,zoompan=z='min(zoom+0.0012,1.15)':d=150:x='iw/2-(iw/zoom/2)':y='ih/2-(ih/zoom/2)':s=<W>x<H>:fps=30" -t 5 -c:v h264_nvenc -pix_fmt yuv420p "<PROJECT_DIR>\temp_assets\visual_fx\fx_04_kenburns.mp4"
   ```

### Kỹ thuật B: Đồ họa động đè lớp qua `hyperframes-motion` (Overlay `.webm`)
Điều phối sang **`hyperframes-motion`** để sinh clip overlay nền trong suốt (`<PROJECT_DIR>\temp_assets\motion\clip_XX\output.webm`):
- **Hook Title / Keyword Pop-up (`GSAP`)**: Nhãn từ khóa bật nảy ở 1/3 trên hoặc góc khung hình trong `1.4s – 2.5s`.
- **Animated Counter / Metric Bar (`GSAP`)**: Con số/tỷ lệ phần trăm chạy tăng dần khớp với lời đọc số liệu.
- **Atmospheric Particles (`tsParticles`)**: Lớp phủ bụi ánh sáng, tia lửa hoặc pháo giấy trong suốt giúp ảnh minh họa AI có chiều sâu điện ảnh.
- **Physics Tag Drop (`Matter.js`)**: Thẻ từ khóa rơi tự do và nảy xếp chồng sinh động.
- **Voice Waveform (`p5.js`)**: Sóng âm thanh đồng bộ nhịp thoại.

### Kỹ thuật C: Chèn B-Roll Minh Họa & Meme Đa Tầng qua `media-preprocess`
1. **Cutaway B-Roll (`2.5s – 3.5s`)**: Gọi `media-preprocess` tải đoạn minh họa Creative Commons chuẩn H.264/MP4, đặt lên `Video Track 2`.
2. **Meme Phông Xanh / Meme Phản Ứng**:
   - Với meme đã tách nền xanh (`meme_*_alpha.webm`): đặt trực tiếp lên `Video Track 3` (Overlay Alpha).
   - Với meme khung chữ nhật (PiP góc phải trên):
     ```powershell
     conda run -n NttDzEditVideo ffmpeg -y -f lavfi -i "color=c=black@0.0:s=<W>x<H>:r=<FPS>:d=<DUR>,format=yuva420p" -i "<PROJECT_DIR>\temp_assets\preprocess\meme_clip.mp4" -filter_complex "[1:v]scale=w='trunc(<W>*0.36/2)*2':h=-2[pip];[0:v][pip]overlay=x='<W>-w-40':y=80:shortest=1,format=yuva420p" -c:v libvpx-vp9 -b:v 2M -auto-alt-ref 0 -c:a libopus "<PROJECT_DIR>\temp_assets\visual_fx\fx_05_pip_meme.webm"
     ```

### Kỹ thuật D: Chuyển cảnh Shader GLSL & Hiệu ứng WebGL (`PixiJS + GL Transitions`)
Sử dụng khi cần **nối mượt 2 ảnh minh họa AI từ ComfyUI** hoặc tạo hiệu ứng chuyển cảnh cao cấp (`CrossZoom`, `DirectionalWarp`, `GlitchMemories`, `LuminanceMelt`) mà `FFmpeg xfade` thông thường không đạt độ mượt nghệ thuật:

1. **Chuẩn bị workspace chuyển cảnh**:
   - Tạo thư mục `<PROJECT_DIR>\temp_assets\visual_fx\gl_trans_XX\`, copy `gsap.min.js`, `pixi.min.js`, `gl-transitions.min.js` từ `F:\A_Tool\Tools\hyperframes\vendor\` và 2 ảnh nguồn (`img_a.png`, `img_b.png`) vào cùng thư mục (đảm bảo chạy offline 100%, không lỗi CORS).
2. **Khóa tiến trình chuyển cảnh theo `gsap.timeline()`**:
   - Biến `progress` (`0.0 -> 1.0`) được điều khiển bởi `gsap.to(state, { progress: 1, duration: TRANS_DUR, ease: "power2.inOut", onUpdate: renderShader })` để đảm bảo mỗi frame xuất ra khớp tuyệt đối `<FPS>`.
3. **Render & Chèn Timeline**:
   - Render bằng `hyperframes.bat render` ra file `.mp4` (`TRANS_DUR = 0.7s – 1.0s`), đặt lên `Video Track 2` phủ lên điểm giao nhau giữa 2 clip ảnh trên `Video Track 1`, kèm hiệu ứng tiếng **`sfx_whoosh`** trên `Audio Track 2`.

---

## 4. Thiết Kế Âm Thanh Đa Lớp (BGM Không Bản Quyền & SFX Đồng Bộ)

1. **Lớp Nhạc Nền Không Bản Quyền (`BGM` — `Audio Track 3`)**:
   - Tải qua `media-preprocess` (`bgm_ready.mp3` đã chuẩn hóa `-24 LUFS`), cắt đúng tổng thời lượng video kèm fade-in `1.0s` và fade-out `2.0s`:
     ```powershell
     conda run -n NttDzEditVideo ffmpeg -y -stream_loop -1 -i "<PROJECT_DIR>\temp_assets\preprocess\bgm_ready.mp3" -t <TONG_THOI_LUONG_VIDEO> -af "afade=t=in:st=0:d=1.0,afade=t=out:st=<TONG_THOI_LUONG_VIDEO_TRU_2>:d=2.0" -c:a libmp3lame -b:a 192k "<PROJECT_DIR>\temp_assets\visual_fx\bgm_timeline_full.mp3"
     ```
   - **Mẹo tạo điểm nhấn hài hước / cao trào**: Ngắt đoạn clip BGM tại khoảng `1.5s` quanh nhịp meme để giọng thoại/meme bật nổi rồi mới cho nhạc chạy tiếp.

2. **Lớp Hiệu Ứng Âm Thanh (`SFX` — `Audio Track 2`)**:
   - Cắt chuyển góc `Punch-in` / `Impact Shake` / `GL Transition` $\rightarrow$ đặt `sfx_whoosh` tại `timeline_in_sec - 0.1s`.
   - Đồ họa `hyperframes-motion` bật lên $\rightarrow$ đặt `sfx_pop` / `sfx_ding` khớp mốc `in_offset` / `impact_offset`.

---

## 5. Quy Trình Nghiệm Thu & Dàn Đa Tầng Lên Timeline Concat MCP

1. **Kiểm tra thông số dự án**: Gọi `timeline_read` để xác nhận độ phân giải (`width`, `height`), `fps`, danh sách track video/audio (`lane_id`) và vị trí các clip thoại hiện có.
2. **Xác minh tài nguyên đầu ra**: Trước khi đưa vào Concat, kiểm tra mọi file trong `<PROJECT_DIR>\temp_assets\visual_fx\` (và các file liên quan từ `preprocess\`, `motion\`) tồn tại, dung lượng `> 0 KB` và đo chính xác `duration`:
   ```powershell
   conda run -n NttDzEditVideo ffprobe -v error -show_entries format=duration -of default=noprint_wrappers=1:nokey=1 "<PROJECT_DIR>\temp_assets\visual_fx\fx_01_punchin.mp4"
   ```
3. **Nạp & Sắp xếp theo Sơ Đồ Tầng Chuẩn trên Concat MCP**:
   - Gọi `media_import` để đưa toàn bộ clip biến đổi, chuyển cảnh GLSL, đồ họa `.webm`, meme, B-roll, SFX và BGM vào kho dự án.
   - **Track Video 1 (Base)**: Dùng `clips_split` tại điểm nhấn trên track chính và thay thế đoạn tĩnh bằng clip `Punch-in` / `Ramp Zoom` / `Impact Shake` / `Ken Burns`.
   - **Track Video 2 (B-Roll & GL Transitions)**: Dùng `clip_add` đặt B-roll minh họa (`2.5–3.5s`) hoặc clip chuyển cảnh shader GLSL tại điểm nối giữa 2 cảnh.
   - **Track Video 3 (Overlay Alpha trên cùng)**: Dùng `clip_add` đặt đồ họa `.webm` (`hyperframes-motion`) và meme tách nền/PiP `.webm` tại đúng `timeline_in_sec`.
   - **Track Audio 2 (SFX & Meme Audio)**: Dùng `clip_add` đặt các file `sfx_*.mp3` khớp từng frame với chuyển động hình ảnh.
   - **Track Audio 3 (BGM)**: Dùng `clip_add` đặt `bgm_timeline_full.mp3` từ `0.0s` (cắt khoảng trống tại các nhịp meme nếu cần).
4. **Lưu đồng bộ**: Gọi `project_save` để cập nhật lên giao diện Concat (tuyệt đối không tự gọi `export_start`).
