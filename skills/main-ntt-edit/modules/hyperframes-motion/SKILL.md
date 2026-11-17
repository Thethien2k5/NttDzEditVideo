---
name: hyperframes-motion
description: "Tạo đồ họa chuyển động đa engine (Intro, Outro, Lower-third, chữ động kinetic, biểu đồ/số đếm, hiệu ứng hạt không khí, vật lý va chạm 2D, sân khấu 3D và sóng âm thanh) bằng Hyperframes (HTML/CSS/GSAP + Three.js, tsParticles, Matter.js, p5.js): tự động chọn engine, khóa nhịp khung hình xác định (Deterministic Frame Stepping), xuất .mp4 cho phân đoạn độc lập hoặc .webm nền trong suốt (Alpha) cho lớp phủ (Overlay), trả về mốc kích hoạt SFX để đồng bộ âm thanh và lưu gọn trong thư mục dự án Concat."
---

# Đồ Họa Chuyển Động Đa Engine (Hyperframes Motion Graphics)

Sử dụng công cụ CLI bọc sẵn môi trường `NttDzEditVideo`:
- **Đường dẫn thực thi**: `F:\A_Tool\Tools\hyperframes\hyperframes.bat`
- **Kho thư viện cục bộ (Offline Vendor)**: `F:\A_Tool\Tools\hyperframes\vendor\`

---

## 1. Xác Định Không Gian Dự Án & Thông Số Khung Hình

Trước khi khởi tạo Hyperframes, bắt buộc đọc trạng thái dự án đang mở qua `project_list` và `timeline_read` (hoặc `ffprobe` trên video gốc) để trích xuất 4 thông số động:

1. **Thư mục dự án Concat (`<PROJECT_DIR>`)**: Toàn bộ mã nguồn và file render tạm **bắt buộc** lưu tại `<PROJECT_DIR>\temp_assets\motion\clip_XX\` (tự động tăng số thứ tự `clip_01`, `clip_02`... để tránh ghi đè asset cũ). Tuyệt đối không ghi file vào thư mục cài đặt Skill.
2. **Chiều rộng (`<WIDTH>`) & Chiều cao (`<HEIGHT>`)**: Khớp 100% với timeline (ví dụ: `1920x1080` cho 16:9, `1080x1920` cho 9:16, hoặc kích thước tùy chỉnh).
3. **Tốc độ khung hình (`<FPS>`)**: Khớp tuyệt đối với timeline (ví dụ: `24`, `30`, `60`) để tránh giật hình hoặc lệch nhịp âm thanh khi ghép.
4. **Thời lượng chuẩn hóa (`<DURATION>`)**:
   - Nếu người dùng hoặc kịch bản chưa chỉ định giây cụ thể, tự động tính theo loại đồ họa và số từ hiển thị:
     - **Nhóm 1 — Câu đầy đủ / Thẻ thông tin (`[intro]`, `[outro]`, Lower-third, Quote Card)**:
       $$\text{DURATION} = \max\left(2.5,\; \text{số từ} \times 0.35 + 0.9\right)$$
     - **Nhóm 2 — Nhãn từ khóa nhanh / Micro-Overlay / Meme Tag (`1–3 từ`)**:
       $$\text{DURATION} = \max\left(1.4,\; \text{số từ} \times 0.30 + 0.8\right)$$
   - Làm tròn đến 1 chữ số thập phân (ví dụ: `3.5` hoặc `1.8`).

---

## 2. Phân Loại Chế Độ Render & Quy Tắc Đồng Bộ Track

Xác định mục đích phân đoạn trước khi viết CSS, chọn định dạng xuất và lên phương án chèn timeline:

### Trường hợp A — Phân đoạn độc lập (`[intro]`, `[outro]` toàn màn hình, nền kín)
- **CSS**: Thiết kế nền kín hoàn chỉnh (`background` có màu sắc, gradient, shader hoặc sân khấu 3D).
- **Định dạng xuất**: **`.mp4`** (`--format mp4`) — render nhanh, tối ưu dung lượng.
- **Vị trí & Đồng bộ Timeline**:
  - **Với `[outro]`**: Nối tiếp ngay sau điểm kết thúc của clip cuối cùng trên Track Video chính.
  - **Với `[intro]` (tại `0.0s`)**: Kiểm tra xem công cụ chỉnh sửa timeline của Concat có hỗ trợ **Ripple Insert** (tự động đẩy toàn bộ clip phía sau trên mọi track) hay không. Nếu không hỗ trợ Ripple Insert, **bắt buộc dịch chuyển (shift) toàn bộ các clip hiện có trên Track Video chính, Track Audio và Track Overlay sang phải một khoảng đúng bằng `<DURATION>`** trước khi chèn `[intro]` vào `0.0s` để chống lệch tiếng toàn cục.

### Trường hợp B — Lớp phủ đè lên video (Lower-third, chữ bay kinetic, biểu đồ, hạt không khí, vật lý rơi, sóng âm)
- **CSS / Canvas**: Bắt buộc đặt `html, body { background: transparent !important; }` và bật `alpha: true` trên WebGL/Canvas renderer.
- **Định dạng xuất**: **`.webm`** (`--format webm`) để giữ nguyên kênh trong suốt Alpha (`yuva420p`).
- **Vị trí Timeline**: Chèn vào **Track Video nằm trên cùng** (phía trên track chứa video nền) tại đúng mốc thời gian cần hiển thị, không làm dịch chuyển các track bên dưới.

---

## 3. Ma Trận Chọn Engine & Thư Viện Mẫu Hoạt Ảnh

### 3.1. Bảng điều phối Engine cục bộ (`vendor/`)
Luôn dùng **GSAP (`gsap.min.js`)** làm nhạc trưởng điều khiển timeline tổng (`TOTAL_DURATION`), và chỉ nạp thêm tối đa **1 engine phụ trợ** khi cảnh quay thực sự cần:

| Engine (`vendor/*.min.js`) | Khi nào sử dụng | Loại đầu ra điển hình |
| :--- | :--- | :--- |
| **`gsap.min.js`** *(Mặc định)* | Chữ động kinetic, thẻ từ khóa, số đếm tăng dần, thanh tiến trình, lower-third, khung meme. | `.mp4` / `.webm` |
| **`tsparticles.bundle.min.js`** | Lớp phủ không khí: tia lửa (`fire_sparks`), bụi điện ảnh (`floating_dust`), tuyết, pháo giấy (`confetti`), mạng lưới công nghệ (`tech_network`). | `.webm` (Alpha) |
| **`three.min.js`** | Intro/Outro 3D, mockup điện thoại/thẻ 3D xoay, khối hình học không gian chiều sâu, biểu đồ cột 3D. | `.mp4` / `.webm` |
| **`matter.min.js`** | Hiệu ứng vật lý 2D: các thẻ từ khóa, icon hoặc khối chữ rơi từ trên xuống, va chạm và nảy tự nhiên. | `.webm` (Alpha) |
| **`p5.min.js`** | Sóng âm thanh (Audio Visualizer) chạy theo nhịp thoại `.wav` từ `vieneu-tts-voiceover` hoặc nền hình học biến thiên (generative art). | `.mp4` / `.webm` |

> **Tham khảo mẫu code đầy đủ cho từng Engine:** Đọc file `references/engine_templates.md` trong thư mục skill này trước khi viết mã cho `tsParticles`, `Three.js`, `Matter.js` hoặc `p5.js`.

### 3.2. Các Archetype Thiết Kế Sẵn Dùng (Tối ưu giữ chân người xem)
1. **Hook Kinetic Title (`GSAP`)**: Tiêu đề mở đầu tách dòng, từ khóa chính tô màu tương phản mạnh (`#FFE600` hoặc `#38BDF8`), bật nảy `back.out(1.7)` kèm vạch sáng quét ngang.
2. **Keyword Callout Pill (`GSAP`)**: Thẻ từ khóa bo góc sắc nét kèm icon vector SVG nội tuyến đặt ở 1/3 trên hoặc lệch góc.
3. **Animated Counter / Metric Bar (`GSAP`)**: Số liệu hoặc phần trăm chạy tăng dần bằng `gsap.to({ val: 0 }, { val: TARGET, onUpdate: ... })` kết hợp thanh tiến trình.
4. **Lower-Third Danh Tính / Nguồn Trích Dẫn (`GSAP`)**: Thanh tiêu đề phụ đặt gọn gàng phía trên vùng phụ đề chính (`MarginV`).
5. **Atmospheric Particle Overlay (`tsParticles`)**: Lớp hạt bụi/tia lửa/pháo giấy chuyển động mượt trên nền trong suốt để phủ lên ảnh tĩnh từ ComfyUI.
6. **3D Stage / Device Showcase (`Three.js`)**: Sân khấu 3D ánh sáng studio với camera quỹ đạo mượt mà bằng GSAP.
7. **Physics Tag Drop (`Matter.js`)**: Các nhãn chủ đề hoặc icon rơi xuống sàn vô hình và nảy xếp chồng sinh động.
8. **Voice-Reactive Waveform (`p5.js`)**: Dải sóng âm thanh đa cột phản hồi theo biên độ giọng đọc.

### 3.3. Quy Tắc Né Vùng Phụ Đề (Subtitle Safe-Zone)
- Khi video có chạy phụ đề (`subtitle-craft`) ở cạnh dưới, **cấm** đặt các lớp phủ `Keyword Callout`, `Counter` hay `Meme Tag` đè lên vùng `20%` dưới cùng (với `16:9`) hoặc `25%` dưới cùng (với `9:16`). Ưu tiên bố trí ở **1/3 trên khung hình** hoặc **vùng giữa lệch trái/phải**.

### 3.4. Bàn Giao Mốc Kích Hoạt Âm Thanh (Motion-SFX Hook)
Sau khi render xong `.webm`/`.mp4`, ghi rõ **bộ 3 mốc giây tương đối** (`in_offset`, `impact_offset`, `out_offset`) và gợi ý loại SFX để `dynamic-visual-enhancer` gọi `media-preprocess` ghép vào `Audio Track 2`:
- Trượt ngang / Quét vạch / Chuyển camera 3D (`slide` / `wipe` / `orbit`) $\rightarrow$ `sfx_whoosh` tại `0.0s` và `TOTAL_DURATION - OUT_DUR`.
- Bật nảy từ khóa / Thẻ thông báo (`pop` / `scale`) $\rightarrow$ `sfx_pop` tại `0.05s`.
- Chốt con số / Va chạm vật lý (`counter` / `physics_hit`) $\rightarrow$ `sfx_ding` hoặc `sfx_pop` tại `IN_DUR + 0.3s`.

---

## 4. Quy Trình Thực Thi Từng Bước

### Bước 1: Khởi tạo workspace cô lập & nạp đúng thư viện cục bộ
1. Kiểm tra thư mục `<PROJECT_DIR>\temp_assets\motion\` để lấy số thứ tự tiếp theo (`clip_01`, `clip_02`...).
2. Khởi tạo workspace:
   ```powershell
   & "F:\A_Tool\Tools\hyperframes\hyperframes.bat" init "<PROJECT_DIR>\temp_assets\motion\clip_01"
   ```
3. Nạp thư viện cục bộ từ `F:\A_Tool\Tools\hyperframes\vendor\` vào `<PROJECT_DIR>\temp_assets\motion\clip_01\`:
   - Luôn đảm bảo có `gsap.min.js`.
   - Nếu cảnh dùng thêm `Three.js`, `tsParticles`, `Matter.js` hoặc `p5.js`, copy đúng file `.min.js` tương ứng từ `F:\A_Tool\Tools\hyperframes\vendor\` vào thư mục `clip_01`.

### Bước 2: Viết mã HTML/CSS/JS chuẩn hóa (Offline-First & Frame-Locked)
Chỉnh sửa mã nguồn trong `<PROJECT_DIR>\temp_assets\motion\clip_01\` và tuân thủ 5 quy tắc bắt buộc:

1. **Khóa khung hình & Vùng an toàn**:
   - Đặt `width: <WIDTH>px; height: <HEIGHT>px; margin: 0; overflow: hidden;` đúng tỷ lệ timeline.
   - Với video dọc `9:16`, giữ toàn bộ nội dung chữ trong vùng an toàn (cách viền tối thiểu `8%` chiều rộng và `12%` chiều cao trên/dưới).
2. **Tuyệt đối Offline (Chống lỗi font tiếng Việt & timeout)**:
   - Cấm tuyệt đối mọi URL internet (`https://`, `fonts.googleapis.com`, `cdnjs`, v.v.).
   - Nhúng thư viện qua đường dẫn tương đối cục bộ (`./gsap.min.js`, `./three.min.js`...).
   - Ưu tiên font hệ thống hỗ trợ đầy đủ dấu tiếng Việt: `'Segoe UI', 'Arial', 'Tahoma', sans-serif`.
3. **Khóa bước khung hình xác định (`Deterministic Frame Stepping`)**:
   - **Cấm** để `Three.js`, `Matter.js`, `p5.js` hay `tsParticles` tự chạy theo `requestAnimationFrame` tự do vì sẽ gây rớt khung hình (drop frame) khi Chromium encode nặng.
   - Bắt buộc điều khiển mọi cập nhật thông qua callback `onUpdate` của `gsap.timeline()` với bước thời gian cố định `dt = 1 / FPS`:
     ```javascript
     const TOTAL_DURATION = 3.5; // Thay bằng giá trị <DURATION> thực tế
     const FPS = 30;             // Thay bằng giá trị <FPS> thực tế
     const DT = 1 / FPS;
     const IN_DUR = 0.4;
     const OUT_DUR = 0.35;
     const HOLD_DUR = Math.max(0.5, TOTAL_DURATION - IN_DUR - OUT_DUR);

     const tl = gsap.timeline({
       onUpdate: () => {
         if (typeof window.onFrameStep === "function") {
           window.onFrameStep(tl.time(), DT);
         }
       }
     });
     tl.from(".box", { y: 30, opacity: 0, duration: IN_DUR, ease: "power3.out" })
       .to(".box", { duration: HOLD_DUR })
       .to(".box", { y: -20, opacity: 0, duration: OUT_DUR, ease: "power2.in" });
     ```
4. **Kiểm soát kênh Alpha (Cho Trường hợp B)**:
   - Đảm bảo không thẻ cha nào (`html`, `body`, `#app`, `.container`) có màu nền đặc.
   - Với WebGL (`Three.js` / `p5.js`), khởi tạo renderer với `{ alpha: true, antialias: true }` và `renderer.setClearColor(0x000000, 0)`.
   - Tránh dùng `filter: drop-shadow(...)` hoặc `box-shadow` mờ lớn trên nền trong suốt vì dễ sinh viền xám răng cưa khi mã hóa VP9 (`yuva420p`).
5. **Giải phóng bộ nhớ WebGL**:
   - Khi kết thúc render, tiến trình Chromium tự thoát và giải phóng toàn bộ VRAM (~150–350MB), không ảnh hưởng tới `ComfyUI` hay `VSR` ở bước sau.

### Bước 3: Render đầu ra & Bắt lỗi thực thi CLI
Chạy lệnh render truyền đầy đủ thông số động (`<WIDTH>`, `<HEIGHT>`, `<FPS>`, `<DURATION>`):

- **Xuất `.mp4` (Trường hợp A — Độc lập):**
  ```powershell
  & "F:\A_Tool\Tools\hyperframes\hyperframes.bat" render "<PROJECT_DIR>\temp_assets\motion\clip_01" --width <WIDTH> --height <HEIGHT> --fps <FPS> --duration <DURATION> --format mp4 --output "<PROJECT_DIR>\temp_assets\motion\clip_01\output.mp4"
  ```

- **Xuất `.webm` Alpha (Trường hợp B — Lớp phủ):**
  ```powershell
  & "F:\A_Tool\Tools\hyperframes\hyperframes.bat" render "<PROJECT_DIR>\temp_assets\motion\clip_01" --width <WIDTH> --height <HEIGHT> --fps <FPS> --duration <DURATION> --format webm --output "<PROJECT_DIR>\temp_assets\motion\clip_01\output.webm"
  ```

- **Kiểm tra trạng thái lệnh**: Nếu `$LASTEXITCODE -ne 0` hoặc file đầu ra không được tạo, **đọc ngay thông báo lỗi từ `stderr`/console** để sửa trực tiếp mã nguồn trước khi render lại.

### Bước 4: Hậu kiểm kỹ thuật (`ffprobe`) trước khi ghép
Trước khi gọi tool chèn vào timeline Concat, bắt buộc chạy `ffprobe` kiểm tra file đầu ra:
```powershell
ffprobe -v error -select_streams v:0 -show_entries stream=width,height,r_frame_rate,pix_fmt,duration -of default=noprint_wrappers=1 "<OUTPUT_FILE>"
```
- **Điều kiện đạt**:
  1. File tồn tại và có dung lượng `> 0 bytes`.
  2. Khớp chính xác `<WIDTH>x<HEIGHT>`, `<FPS>` và thời lượng xấp xỉ `<DURATION>` (sai số `< 0.1s`).
  3. Riêng file lớp phủ `.webm` bắt buộc có `pix_fmt=yuva420p`.
- **Xử lý lỗi**: Nếu thiếu kênh Alpha (`yuv420p` thay vì `yuva420p`) hoặc sai thông số khung hình, kiểm tra lại thuộc tính `background: transparent !important` và tham số CLI, render lại tối đa 1 lần trước khi báo lỗi.

### Bước 5: Chèn vào Timeline Concat & Xác nhận đồng bộ
1. Gọi công cụ chỉnh sửa timeline của Concat để đưa `<OUTPUT_FILE>` vào đúng vị trí đã xác định ở Mục 2 (đảm bảo đã dịch chuyển các track liên quan nếu chèn `[intro]` ở `0.0s`).
2. Nếu có SFX đi kèm (`whoosh`, `pop`, `ding`), đặt file SFX tương ứng lên Track Audio SFX tại `timeline_in_sec + offset`.
3. Gọi lại `timeline_read` để xác nhận clip mới đã nằm đúng track, đúng mốc thời gian và không gây chồng lấn hoặc lệch pha âm thanh.
