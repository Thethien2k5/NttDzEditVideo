---
name: main-ntt-edit
description: "Skill điều phối trung tâm để biên tập video chuyên nghiệp qua Concat Video Editor MCP (127.0.0.1:7420): phân tích kịch bản theo mốc thời gian, cắt ghép timeline, chèn phụ đề/tiêu đề, xuất bản video và điều hướng sang các sub-skill lồng tiếng (VieNeu-TTS), đồ họa động (Hyperframes), hoặc tiền xử lý media (auto-editor, VSR, yt-dlp)."
---

# Điều Phối Biên Tập Video (Concat MCP Orchestrator)

Skill này đóng vai trò nhạc trưởng: nhận diện ý định người dùng, phân rã kịch bản, điều khiển trực tiếp **Concat Video Editor** qua MCP và gọi các sub-skill chuyên biệt khi cần tạo tài nguyên hoặc làm sạch tư liệu.

---

## 1. Quy Tắc An Toàn & Vòng Đời Kết Nối (Bắt Buộc)

1. **Quản lý kết nối MCP**: Chỉ kết nối tới Concat MCP khi bắt đầu phiên chỉnh sửa video. Khi chưa có yêu cầu hoặc đã hoàn thành tác vụ, ngắt/không duy trì kết nối thừa.
2. **Cấm tự ý xuất video (`export_start`)**: Tuyệt đối không tự render video thành phẩm khi người dùng chưa yêu cầu. Luôn dừng lại sau khi lưu timeline để người dùng kiểm tra trực tiếp trên giao diện Concat.
3. **Luôn lưu dự án (`project_save`)**: Sau bất kỳ thao tác thay đổi nào trên timeline (thêm, cắt, dịch chuyển, xóa clip, thêm chữ), bắt buộc gọi `project_save` để đồng bộ lên cửa sổ Concat.
4. **Bảo toàn file gốc & cô lập file tạm**: Không ghi đè file tư liệu gốc. Mọi file tạm (âm thanh TTS, video cắt lọc, overlay) phải lưu vào thư mục tạm riêng của dự án với tên gắn mốc thời gian/số thứ tự để tránh ghi đè lẫn nhau.
5. **Giao tiếp tiếng Việt**: Xác minh file tồn tại trên ổ đĩa trước khi thao tác và báo cáo tiến độ ngắn gọn bằng tiếng Việt.
6. **Quy chuẩn môi trường thực thi (`NttDzEditVideo`)**:
   - Mọi tác vụ CLI (`vieneu`, `hyperframes`, `vsr`, `auto-editor`, `yt-dlp`, `ffmpeg`, `ffprobe`) **bắt buộc** phải chạy trong phạm vi môi trường Conda `NttDzEditVideo` (Python 3.10 + CUDA 12.4).
   - **Ưu tiên 1:** Gọi trực tiếp các file `.bat` wrapper đã cấu hình sẵn tại `F:\A_Tool\Tools\<tên_tool>\*.bat`.
   - **Ưu tiên 2:** Nếu gọi lệnh trực tiếp (đặc biệt là `ffmpeg` / `ffprobe` hoặc script Python phụ trợ), bắt buộc dùng cú pháp `conda run -n NttDzEditVideo <lệnh>` — tuyệt đối không chạy bằng Python mặc định của hệ thống (base/system) để tránh lỗi thiếu thư viện hoặc mất hỗ trợ GPU.

---

## 2. Bản Đồ Điều Hướng Ý Định (Intent Routing)

> **Quy tắc nạp sub-skill:** Toàn bộ sub-skill nằm tại `skills/main-ntt-edit/modules/<tên-sub-skill>/SKILL.md`. Khi cần dùng sub-skill nào trong bảng dưới, bắt buộc đọc file `SKILL.md` tương ứng trước khi thực thi.

| Yêu cầu của người dùng | Hành động / Công cụ thực thi |
| :--- | :--- |
| **Cắt ghép, chia đoạn, chèn clip/nhạc** | Thực thi trực tiếp bằng **Concat MCP** (Mục 4.1). |
| **Tạo phụ đề, chữ chạy, tiêu đề chính** | Thực thi trực tiếp bằng **Concat MCP** (`captions_add`, `title_add` - Mục 4.2). và gọi sub-skill **`subtitle-craft`**|
| **Lồng tiếng, thuyết minh, đọc kịch bản** | Gọi sub-skill **`vieneu-tts-voiceover`** tạo file `.wav` -> nạp vào Concat MCP. |
| **Tạo Intro, Outro, Lower-third, chữ bay** | Gọi sub-skill **`hyperframes-motion`** tạo `.webm`, `.mp4` tùy trường hợp -> chèn trên cùng timeline của Concat. |
| **Cắt khoảng lặng, xóa logo/sub, tải tư liệu** | Gọi sub-skill **`media-preprocess`** (`auto-editor`, `VSR`, `yt-dlp`) -> nạp file sạch vào Concat. |
| **Render / Xuất video thành phẩm** | Chỉ chạy khi người dùng yêu cầu rõ: `project_save` -> `export_start` -> `export_wait`. |
| **Tăng sinh động, chống nhàm chán (zoom theo nhịp thoại, overlay từ khóa, ken burns)** | Gọi sub-skill **`dynamic-visual-enhancer`** phân tích giọng đọc/hình ảnh -> tạo chuyển động/overlay `.webm` nạp vào Concat MCP. |

> **Lưu ý hiệu năng & Đồng bộ:** Chạy tuần tự các tác vụ nặng GPU (`vsr`, `vieneu-tts`) để tránh tràn VRAM (RTX 3060). Luôn kiểm tra thời lượng thực tế (`duration`) của file `.wav`/`.webm` vừa tạo trước khi tính mốc `timeline_in_sec` cho đoạn kế tiếp.

>**Thư mục dự án Concat (`<PROJECT_DIR>`)**: Toàn bộ mã nguồn và file render tạm **bắt buộc** lưu trong `<PROJECT_DIR>\temp_assets\`.

---

## 3. Quy Tắc Đọc Cú Pháp Kịch Bản

Khi người dùng đưa kịch bản có gắn thẻ định dạng, phân tách như sau:

* **Thẻ mốc thời gian + sắc thái**:
  ```text
  [00:14] [trầm ổn] Để tải về, hãy truy cập vào trang web abc.
  ```
  -> `00:14` là vị trí chèn trên timeline (`timeline_in_sec = 14.0`). Phần `[trầm ổn] Để tải về, hãy truy cập vào trang web abc.` chuyển sang sub-skill **`vieneu-tts-voiceover`** để sinh giọng đọc.

* **Thẻ phân đoạn đặc biệt (`[intro]`, `[outro]`)**:
  ```text
  [intro] [ngạo nghễ] Nếu các ngươi đang lo lắng về abc.
  ```
  -> Nếu không có video đi kèm, dùng nội dung câu thoại kết hợp sub-skill **`hyperframes-motion`** để dựng video đồ họa mở đầu, đồng thời gọi **`vieneu-tts-voiceover`** tạo giọng đọc khớp thời lượng.
  -> Mặc định `[intro]` đặt tại đầu timeline (`0.0s`) nếu không ghi mốc thời gian; `[outro]` đặt nối tiếp ở cuối timeline.

---

## 4. Quy Trình Thao Tác Trên Concat MCP

### 4.1. Khởi tạo phiên làm việc (Handshake)
1. Gọi `concat_version` để xác thực kết nối IPC (`mcp.mode` trả về `"window"` hoặc `"headless"`).
2. Gọi `project_list` và `timeline_read` để kiểm tra dự án đang mở, danh sách `lane_id` (track video, audio, phụ đề) và tổng thời lượng.
3. Nếu chưa có dự án mở: hỏi thư mục để gọi `project_open(path="...")` hoặc khởi tạo bằng `project_create(path="...", fps=..., width=..., height=...)`.

### 4.2. Biên tập Timeline, Phụ đề & Xuất bản
* **Nhập & đặt clip vào timeline**:
  1. `media_import(path="<duong_dan_project>", file="<duong_dan_media>")` -> lấy `media_id`.
  2. `clip_add(path="...", lane_id="<id_track>", media_id="<media_id>", timeline_in_sec=0.0)`
  3. Cắt/tách khi cần: `clip_trim(path="...", clip_id="...", in_sec=1.5, out_sec=10.0)`, `clips_split(path="...", clip_ids=["..."], split_sec=5.0)`, `clips_remove(path="...", clip_ids=["..."])`.
  4. `project_save(path="...")`.

* **Thêm phụ đề & tiêu đề**:
  * Phụ đề theo lời thoại:
```json
captions_add(
  path="<duong_dan_project>",
  lane_id="<track_phu_de>",
  captions=[
    {"start_sec": 0.5, "end_sec": 3.2, "text": "Nội dung câu 1"},
    {"start_sec": 3.5, "end_sec": 6.8, "text": "Nội dung câu 2"}
  ]
)
```
  * Tiêu đề nổi bật (Headline/CTA):
```json
title_add(
  path="<duong_dan_project>",
  lane_id="<track_video_tren_cung>",
  text="TIÊU ĐỀ CHÍNH",
  start_sec=0.0,
  duration_sec=4.0
)
```

* **Xuất bản (Chỉ khi được yêu cầu)**:
  `project_save(path="...")` -> `export_start(path="...", output="<file_xuat.mp4>")` -> theo dõi bằng `export_status` / `export_wait` và trả về đường dẫn file hoàn chỉnh.

---

## 5. Bảng Tham Chiếu Nhanh Công Cụ Concat MCP

| Tên Tool | Tham số chính | Chức năng |
| :--- | :--- | :--- |
| `concat_version` | `{}` | Kiểm tra trạng thái kết nối IPC với Concat GUI |
| `project_open` / `project_create` | `path`, (`fps`, `width`, `height`) | Mở dự án có sẵn hoặc tạo dự án mới |
| `project_save` | `path` | Lưu toàn bộ thay đổi timeline xuống đĩa |
| `timeline_read` | `path` | Đọc JSON cấu trúc các track (`lane_id`), clip và thời lượng |
| `media_import` | `path`, `file` | Nạp file video, ảnh, audio vào kho tài nguyên dự án |
| `clip_add` | `path`, `lane_id`, `media_id`, `timeline_in_sec` | Chèn clip vào track tại mốc giây chỉ định |
| `clip_trim` | `path`, `clip_id`, `in_sec`, `out_sec` | Cắt gọt điểm đầu và điểm cuối của clip |
| `clips_split` | `path`, `clip_ids`, `split_sec` | Cắt đôi clip tại mốc giây |
| `clips_move` | `path`, `clip_ids`, `delta_sec` | Dịch chuyển clip sang trái/phải theo số giây |
| `clips_remove` | `path`, `clip_ids` | Xóa clip khỏi timeline |
| `title_add` | `path`, `lane_id`, `text`, `start_sec`, `duration_sec` | Chèn lớp chữ tiêu đề tĩnh lên video |
| `captions_add` | `path`, `lane_id`, `captions` | Chèn hàng loạt phụ đề khớp mốc thời gian |
| `export_start` / `export_status` / `export_wait` | `path`, (`output`) | Khởi chạy, kiểm tra tiến độ và chờ render hoàn tất |


---