---
name: vieneu-tts-voiceover
description: "Tạo giọng đọc lồng tiếng AI 48kHz có cảm xúc bằng VieNeu-TTS v3 Turbo (vieneu.bat) từ câu thoại, file kịch bản hoặc giọng mẫu nhân bản; lưu gọn vào thư mục dự án Concat, đo thời lượng thực tế và chèn vào track Audio của Concat MCP."
---

# Lồng Tiếng AI Cảm Xúc (VieNeu-TTS v3 Turbo)

Sử dụng công cụ CLI bọc sẵn môi trường `NttDzEditVideo` (Python 3.10 + PyTorch CUDA 12.4 + eSpeak-NG) trên PowerShell:
- **Đường dẫn thực thi**: `F:\A_Tool\Tools\VieNeu-TTS\vieneu.bat`

---

## 1. Quy Tắc Không Gian Lưu Trữ, Encoding & Hiệu Năng (Bắt Buộc)

1. **Khởi tạo thư mục đích trong dự án Concat (`<PROJECT_DIR>`)**:
   - Trước khi chạy lệnh, lấy đường dẫn thư mục dự án đang mở qua `project_list` hoặc `timeline_read`.
   - Luôn tạo sẵn thư mục lưu trữ tạm trước khi xuất file:
     ```powershell
     New-Item -ItemType Directory -Force -Path "<PROJECT_DIR>\temp_assets\voiceover" | Out-Null
     ```
   - Mọi file `.wav` xuất ra và file kịch bản tạm `.txt` **bắt buộc** lưu tại `<PROJECT_DIR>\temp_assets\voiceover\`. Tuyệt đối không lưu vào thư mục cài đặt Skill.

2. **Chạy tuần tự bảo vệ VRAM (RTX 3060)**:
   - Chỉ chạy **từng lệnh `vieneu.bat` một** (không chạy song song nhiều tiến trình TTS cùng lúc hoặc chạy chung với `vsr.bat` / Concat render) để tránh tràn VRAM.

3. **Chuẩn hóa UTF-8 & dấu ngoặc trong PowerShell (Chống lỗi tiếng Việt)**:
   - Trước khi gọi CLI có tham số tiếng Việt có dấu (`-t`, `-v`), ép console PowerShell dùng chuẩn UTF-8 để không bị lỗi font hoặc sai tên giọng:
     ```powershell
     [Console]::InputEncoding = [Console]::OutputEncoding = [System.Text.Encoding]::UTF8
     ```
   - Tránh đặt dấu ngoặc kép `"` bên trong nội dung chuỗi `-t "..."` (nếu cần trích dẫn trong lời thoại, dùng dấu nháy đơn `'` hoặc thoát ký tự đúng chuẩn PowerShell).

---

## 2. Quy Tắc Bất Biến Về Phạm Vi Giọng Đọc (Voice Scope Policy)

1. **Tính nhất quán toàn kịch bản**:
   - Khi người dùng hoặc kịch bản đã chỉ định một giọng chủ đạo (ví dụ: `"nữ chính"`, `"Trúc Ly"`, `"Thiện Minh"`...), **BẮT BUỘC dùng duy nhất giọng đó cho 100% các phân đoạn**. Tuyệt đối không tự ý đổi sang giọng khác giữa chừng trừ khi kịch bản ghi rõ phân vai đổi người nói.

2. **Phân biệt rạch ròi 2 loại thẻ trong kịch bản**:
   - **Thẻ hiệu ứng cảm xúc nội tại (`[cười]`, `[thở dài]`, `[hắng giọng]`)**: Nằm *bên trong câu nói* để chính giọng đang chọn tự phát ra tiếng cười/thở dài. **CẤM TUYỆT ĐỐI** việc thấy thẻ `[cười]` mà tự động đổi sang giọng nhân vật khác (như Sukuna).
   - **Thẻ nhân vật & thần thái (`[sukuna: ngạo nghễ]`, `[sukuna: uy quyền]`, `[nữ chính]`)**: Dùng để ánh xạ sang tham số `-v`.

---

## 3. Bảng Ánh Xạ Phân Vai, Biến Thể & Nhân Bản Giọng

| Giọng / Nhân vật chỉ định | Thần thái / Chế độ | Tham số truyền vào CLI | Quy tắc xử lý |
| :--- | :--- | :--- | :--- |
| **`"nữ chính"`** | Mọi sắc thái (vui, cười, buồn, kể chuyện...) | `-v "nữ chính"` *(xuyên suốt)* | Giữ nguyên thẻ `[cười]`, `[thở dài]` trong chuỗi `-t` để mô hình nữ chính tự diễn cảm. |
| **Giọng mẫu tích hợp khác** (`"Trúc Ly"`, `"Thiện Minh"`...) | Mọi sắc thái | `-v "<tên_giọng>"` *(xuyên suốt)* | Nếu chưa chắc tên giọng có sẵn, chạy `vieneu.bat --list-voices` để kiểm tra trước. |
| **`"sukuna"`** (hoặc phân vai Sukuna) | Mặc định / Chung chung | `-v "sukuna"` | Bản chuẩn đa dụng. |
| | `[uy quyền]`, `[trầm ổn]`, `[ra lệnh]`, `[triết lý]` | `-v "sukuna (uy quyền)"` | Biến thể trầm đục, uy nghiêm, độc thoại đĩnh đạc. |
| | `[ngạo nghễ]`, `[khiêu khích]`, `[chiến đấu]`, `[cười cợt]` | `-v "sukuna (ngạo mạn)"` | Biến thể gằn khàn, ma mị, khiêu khích, cười nhếch mép. |
| **Nhân bản từ file âm thanh mẫu** | Người dùng cung cấp file `.wav` mẫu | `-r "<duong_dan\ref_voice.wav>"` | Thay tham số `-v` bằng `-r` để clone giọng trực tiếp từ file mẫu (nên dùng file mẫu sạch tạp âm, dài 5–15 giây). |

---

## 4. Quy Trình Thực Thi: Sinh Audio $\rightarrow$ Đo Thời Lượng $\rightarrow$ Chèn Concat MCP

### Bước 1: Chốt giọng chủ đạo & quy tắc đặt tên file
- Xác định cố định tham số `-v` (hoặc `-r`) trước khi chạy lệnh đầu tiên.
- Đặt tên file theo quy tắc `voice_<stt>_<moc_giay>s.wav` (ví dụ `voice_01_0000s.wav`, `voice_02_0014s.wav` tương ứng mốc giây dự kiến trên timeline) trong `<PROJECT_DIR>\temp_assets\voiceover\` để không bao giờ ghi đè file trước đó.

### Bước 2: Chạy lệnh sinh audio (Tuần tự từng câu/đoạn)
- **Cách 1 — Đọc từng câu thoại (Khuyên dùng, giữ nguyên thẻ biểu cảm trong văn bản):**
  ```powershell
  & "F:\A_Tool\Tools\VieNeu-TTS\vieneu.bat" -t "Ôi chuyện này buồn cười thật đấy! [cười] Bạn có tin được không?" -v "nữ chính" -o "<PROJECT_DIR>\temp_assets\voiceover\voice_01_0014s.wav"
  ```
- **Cách 2 — Nhân bản giọng từ file `.wav` mẫu:**
  ```powershell
  & "F:\A_Tool\Tools\VieNeu-TTS\vieneu.bat" -t "Chào mừng các bạn đã quay trở lại với kênh của mình." -r "<duong_dan\ref_voice.wav>" -o "<PROJECT_DIR>\temp_assets\voiceover\voice_01_0000s.wav"
  ```
- *(Lưu ý chia câu: Nếu đoạn văn quá dài trên 3–4 câu, hãy tách nhỏ theo dấu chấm `.` / `?` / `!` thành nhiều file `voice_01`, `voice_02`... để giọng đọc giữ nhịp tự nhiên, không bị hụt hơi hoặc nuốt chữ.)*

### Bước 3: Kiểm tra file & đo thời lượng thực tế
Trước khi chèn vào timeline, kiểm tra file `.wav` tồn tại (`Length > 0`) và đo chính xác độ dài thực tế (tính bằng giây) bằng `ffprobe` (hoặc Python):
```powershell
$wavPath = "<PROJECT_DIR>\temp_assets\voiceover\voice_01_0014s.wav"
if ((Test-Path $wavPath) -and ((Get-Item $wavPath).Length -gt 0)) {
    $duration = & ffprobe -v error -show_entries format=duration -of default=noprint_wrappers=1:nokey=1 "$wavPath"
    Write-Output "File OK | Duration: $([math]::Round([double]$duration, 3))s"
} else {
    Write-Error "Lỗi: File audio không tồn tại hoặc rỗng!"
}
```

### Bước 4: Chèn vào Track Audio của Concat MCP & Chống đè thoại
1. Đọc trạng thái timeline hiện tại qua `timeline_read` để xác định track Audio dành cho lồng tiếng (Voiceover) và vị trí kết thúc của clip thoại liền trước (`prev_end_time`).
2. Tính mốc đặt clip mới:
   - Nếu không có mốc thời gian cứng từ kịch bản, đặt `start_time = prev_end_time + 0.3s` (tạo khoảng nghỉ lấy hơi tự nhiên từ `0.2s` đến `0.5s`).
   - Nếu có mốc thời gian cứng, đối chiếu `start_time + duration` với clip kế tiếp để đảm bảo **không bị đè âm thanh** (nếu bị lẹm sang câu sau, báo lại hoặc điều chỉnh giãn cảnh hình ảnh tương ứng).
3. Gọi công cụ chèn media của Concat MCP để đưa file `.wav` từ `<PROJECT_DIR>\temp_assets\voiceover\` vào đúng track Audio.