---
name: hyperframes-motion
description: "Tạo đồ họa chuyển động (Intro, Outro, Lower-third, chữ động kinetic, hiệu ứng logo) bằng Hyperframes (HTML/CSS/GSAP): tự động tính thời lượng, xuất .mp4 cho phân đoạn độc lập hoặc .webm nền trong suốt (Alpha) cho lớp phủ (Overlay), đồng bộ track và lưu gọn trong thư mục dự án Concat."
---

# Đồ Họa Chuyển Động (Hyperframes Motion Graphics)

Sử dụng công cụ CLI bọc sẵn môi trường `NttDzEditVideo`:
- **Đường dẫn thực thi**: `F:\A_Tool\Tools\hyperframes\hyperframes.bat`

---

## 1. Xác Định Không Gian Dự Án & Thông Số Khung Hình

Trước khi khởi tạo Hyperframes, bắt buộc đọc trạng thái dự án đang mở qua `project_list` và `timeline_read` (hoặc `ffprobe` trên video gốc) để trích xuất 4 thông số động:

1. **Thư mục dự án Concat (`<PROJECT_DIR>`)**: Toàn bộ mã nguồn và file render tạm **bắt buộc** lưu tại `<PROJECT_DIR>\temp_assets\motion\clip_XX\` (tự động tăng số thứ tự `clip_01`, `clip_02`... để tránh ghi đè asset cũ). Tuyệt đối không ghi file vào thư mục cài đặt Skill.
2. **Chiều rộng (`<WIDTH>`) & Chiều cao (`<HEIGHT>`)**: Khớp 100% với timeline (ví dụ: `1920x1080` cho 16:9, `1080x1920` cho 9:16, hoặc kích thước tùy chỉnh).
3. **Tốc độ khung hình (`<FPS>`)**: Khớp tuyệt đối với timeline (ví dụ: `24`, `30`, `60`) để tránh giật hình hoặc lệch nhịp âm thanh khi ghép.
4. **Thời lượng chuẩn hóa (`<DURATION>`)**:
   - Nếu người dùng hoặc kịch bản chưa chỉ định giây cụ thể, tự động tính theo số từ hiển thị để đảm bảo đủ thời gian đọc:
     $$\text{DURATION} = \max\left(2.5,\; \text{số từ} \times 0.35 + 0.9\right)$$
   - Làm tròn đến 1 chữ số thập phân (ví dụ: `3.5`).

---

## 2. Phân Loại Chế Độ Render & Quy Tắc Đồng Bộ Track

Xác định mục đích phân đoạn trước khi viết CSS, chọn định dạng xuất và lên phương án chèn timeline:

### Trường hợp A — Phân đoạn độc lập (`[intro]`, `[outro]` toàn màn hình, nền kín)
- **CSS**: Thiết kế nền kín hoàn chỉnh (`background` có màu sắc, gradient hoặc họa tiết).
- **Định dạng xuất**: **`.mp4`** (`--format mp4`) — render nhanh, tối ưu dung lượng.
- **Vị trí & Đồng bộ Timeline**:
  - **Với `[outro]`**: Nối tiếp ngay sau điểm kết thúc của clip cuối cùng trên Track Video chính.
  - **Với `[intro]` (tại `0.0s`)**: Kiểm tra xem công cụ chỉnh sửa timeline của Concat có hỗ trợ **Ripple Insert** (tự động đẩy toàn bộ clip phía sau trên mọi track) hay không. Nếu không hỗ trợ Ripple Insert, **bắt buộc dịch chuyển (shift) toàn bộ các clip hiện có trên Track Video chính, Track Audio và Track Overlay sang phải một khoảng đúng bằng `<DURATION>`** trước khi chèn `[intro]` vào `0.0s` để chống lệch tiếng toàn cục.

### Trường hợp B — Lớp phủ đè lên video (Lower-third, chữ bay kinetic, chuyển cảnh, overlay)
- **CSS**: Bắt buộc đặt `html, body { background: transparent !important; }`.
- **Định dạng xuất**: **`.webm`** (`--format webm`) để giữ nguyên kênh trong suốt Alpha (`yuva420p`).
- **Vị trí Timeline**: Chèn vào **Track Video nằm trên cùng** (phía trên track chứa video nền) tại đúng mốc thời gian cần hiển thị, không làm dịch chuyển các track bên dưới.

---

## 3. Quy Trình Thực Thi Từng Bước

### Bước 1: Khởi tạo workspace cô lập & kiểm tra thư viện cục bộ
1. Kiểm tra thư mục `<PROJECT_DIR>\temp_assets\motion\` để lấy số thứ tự tiếp theo (`clip_01`, `clip_02`...).
2. Khởi tạo workspace:
   ```powershell
   & "F:\A_Tool\Tools\hyperframes\hyperframes.bat" init "<PROJECT_DIR>\temp_assets\motion\clip_01"
   ```
3. Kiểm tra danh sách file trong `<PROJECT_DIR>\temp_assets\motion\clip_01` để xác nhận đường dẫn file thư viện GSAP cục bộ (ví dụ: `gsap.min.js`). Nếu template chưa có sẵn file GSAP cục bộ, tìm và copy trực tiếp từ thư mục cài đặt `F:\A_Tool\Tools\hyperframes\` vào thư mục `clip_01`.

### Bước 2: Viết mã HTML/CSS/GSAP chuẩn hóa (Offline-First)
Chỉnh sửa mã nguồn trong `<PROJECT_DIR>\temp_assets\motion\clip_01\` và tuân thủ 4 quy tắc bắt buộc:

1. **Khóa khung hình & Vùng an toàn**:
   - Đặt `width: <WIDTH>px; height: <HEIGHT>px; margin: 0; overflow: hidden;` đúng tỷ lệ timeline.
   - Với video dọc `9:16`, giữ toàn bộ nội dung chữ trong vùng an toàn (cách viền tối thiểu `8%` chiều rộng và `12%` chiều cao trên/dưới) để tránh bị UI mạng xã hội che khuất.
2. **Tuyệt đối Offline (Chống lỗi font tiếng Việt & timeout)**:
   - Cấm tuyệt đối mọi URL internet (`https://`, `fonts.googleapis.com`, `cdnjs`, v.v.).
   - Nhúng GSAP qua đường dẫn tương đối cục bộ (`./gsap.min.js`).
   - Ưu tiên font hệ thống hỗ trợ đầy đủ dấu tiếng Việt: `'Segoe UI', 'Arial', 'Tahoma', sans-serif`.
3. **Đồng bộ thời lượng GSAP (`<DURATION>`)**:
   - Khai báo hằng số `TOTAL_DURATION = <DURATION>` ngay đầu script để tự động tính nhịp *Giữ đọc* (`holdDuration`), đảm bảo hiệu ứng kết thúc khớp tuyệt đối với tổng thời lượng render:
     ```javascript
     const TOTAL_DURATION = 3.5; // Thay bằng giá trị <DURATION> thực tế
     const IN_DUR = 0.4;
     const OUT_DUR = 0.35;
     const HOLD_DUR = Math.max(0.5, TOTAL_DURATION - IN_DUR - OUT_DUR);

     const tl = gsap.timeline();
     tl.from(".box", { y: 30, opacity: 0, duration: IN_DUR, ease: "power3.out" })
       .to(".box", { duration: HOLD_DUR }) // Nhịp giữ đọc tự động co giãn
       .to(".box", { y: -20, opacity: 0, duration: OUT_DUR, ease: "power2.in" });
     ```
4. **Kiểm soát kênh Alpha (Cho Trường hợp B)**:
   - Đảm bảo không thẻ cha nào (`html`, `body`, `#app`, `.container`) có màu nền đặc.
   - Tránh dùng `filter: drop-shadow(...)` hoặc `box-shadow` mờ lớn trên nền trong suốt vì dễ sinh viền xám răng cưa khi mã hóa VP9 (`yuva420p`); ưu tiên dùng nền khối sắc nét hoặc viền stroke mảnh.

### Bước 3: Render đầu ra & Bắt lỗi thực thi CLI
Chạy lệnh render truyền đầy đủ thông số động (`<WIDTH>`, `<HEIGHT>`, `<FPS>`, `<DURATION>`) và lưu log thực thi:

- **Xuất `.mp4` (Trường hợp A — Độc lập):**
  ```powershell
  & "F:\A_Tool\Tools\hyperframes\hyperframes.bat" render "<PROJECT_DIR>\temp_assets\motion\clip_01" --width <WIDTH> --height <HEIGHT> --fps <FPS> --duration <DURATION> --format mp4 --output "<PROJECT_DIR>\temp_assets\motion\clip_01\output.mp4"
  ```

- **Xuất `.webm` Alpha (Trường hợp B — Lớp phủ):**
  ```powershell
  & "F:\A_Tool\Tools\hyperframes\hyperframes.bat" render "<PROJECT_DIR>\temp_assets\motion\clip_01" --width <WIDTH> --height <HEIGHT> --fps <FPS> --duration <DURATION> --format webm --output "<PROJECT_DIR>\temp_assets\motion\clip_01\output.webm"
  ```

- **Kiểm tra trạng thái lệnh**: Nếu `$LASTEXITCODE -ne 0` hoặc file đầu ra không được tạo, **đọc ngay thông báo lỗi từ `stderr`/console** (lỗi cú pháp JS, sai đường dẫn GSAP hoặc sai selector) để sửa trực tiếp mã nguồn trước khi render lại.

### Bước 4: Hậu kiểm kỹ thuật (`ffprobe`) trước khi ghép
Trước khi gọi tool chèn vào timeline Concat, bắt buộc chạy `ffprobe` kiểm tra file đầu ra:
```powershell
ffprobe -v error -select_streams v:0 -show_entries stream=width,height,r_frame_rate,pix_fmt,duration -of default=noprint_wrappers=1 "<OUTPUT_FILE>"
```
- **Điều kiện đạt**:
  1. File tồn tại và có dung lượng `> 0 bytes`.
  2. Khớp chính xác `<WIDTH>x<HEIGHT>`, `<FPS>` và thời lượng xấp xỉ `<DURATION>` (sai số `< 0.1s`).
  3. Riêng file lớp phủ `.webm` bắt buộc có `pix_fmt=yuva420p`.
- **Xử lý lỗi**: Nếu thiếu kênh Alpha (`yuv420p` thay vì `yuva420p`) hoặc sai thông số khung hình, kiểm tra lại thuộc tính `background: transparent !important` trong CSS và tham số CLI, render lại tối đa 1 lần trước khi báo lỗi.

### Bước 5: Chèn vào Timeline Concat & Xác nhận đồng bộ
1. Gọi công cụ chỉnh sửa timeline của Concat để đưa `<OUTPUT_FILE>` vào đúng vị trí đã xác định ở Mục 2 (đảm bảo đã dịch chuyển các track liên quan nếu chèn `[intro]` ở `0.0s`).
2. Gọi lại `timeline_read` để xác nhận clip mới đã nằm đúng track, đúng mốc thời gian và không gây chồng lấn hoặc lệch pha âm thanh.