---
name: vieneu-tts-voiceover
description: "Đạo diễn giọng đọc và tạo lồng tiếng AI 48kHz giàu cảm xúc bằng VieNeu-TTS v3 Turbo (vieneu.bat) theo cốt truyện, nhịp điệu trình bày và sắc thái nhân vật; lưu gọn vào thư mục dự án Concat, đo thời lượng thực tế và dựng nhịp thoại trên track Audio của Concat MCP."
---

# Đạo Diễn & Lồng Tiếng AI Cảm Xúc (VieNeu-TTS v3 Turbo)

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

## 2. Đạo Diễn Âm Giọng & Sáng Tạo Phong Cách Theo Cốt Truyện

Trước khi xuất âm thanh, AI **không được đọc nguyên văn bản thô một cách đều đều**, mà phải đóng vai **Đạo diễn âm thanh (Voice Director)**: phân tích cốt truyện, thiết kế đường dây cảm xúc (Emotional Arc) và biên tập lại văn bản đầu vào để mô hình TTS diễn đạt có hồn nhất.

### A. Định hình phong cách trình bày theo thể loại nội dung

| Thể loại / Cốt truyện | Mục tiêu cảm xúc | Kỹ thuật trình bày & xử lý lời thoại |
| :--- | :--- | :--- |
| **Kể chuyện / Tự sự / Tâm lý** | Sâu lắng, gợi hình, cuốn người nghe vào mạch truyện | Giữ câu có độ ngân ở cuối ý bằng dấu `...`; tách các vế cảm xúc bằng dấu phẩy `,` để giọng có độ lắng; dùng `[thở dài]` ở đầu các câu chiêm nghiệm hoặc tiếc nuối. |
| **Hành động / Anime / Dark Fantasy** | Kịch tính, áp lực, biến chuyển tâm lý mạnh | Chia nhỏ câu ngắn, dứt khoát ở pha cao trào. Nếu dùng nhân vật có biến thể (như `sukuna`), chuyển đổi mượt giữa sắc thái trầm ổn (`uy quyền`) lúc thăm dò sang sắc thái gằn giọng, nhếch mép (`ngạo mạn`) khi bùng nổ. |
| **Video ngắn / Hook – Twist – CTA** | Giữ chân 3s đầu, tạo bất ngờ ở điểm lật | **Hook (3–5s đầu):** Câu ngắn, trực diện, nhấn mạnh từ khóa mở đầu.<br>**Build-up:** Nhịp đều, mạch lạc.<br>**Twist:** Tạo khoảng lặng dài trên timeline ngay trước câu chốt sự thật. |
| **Review / Giải thích / Kể chuyện đời thường** | Tự nhiên như đang trò chuyện, gần gũi | Chuyển văn viết khô khan sang văn nói có nhịp điệu; chèn tiểu từ cảm thán tự nhiên (*"thật sự luôn"*, *"nghe thì vô lý nhưng..."*) và đặt `[cười]` / `[hắng giọng]` đúng điểm rơi (punchline). |

### B. Nghệ thuật "Biên Tập Văn Bản Cho AI Đọc" (TTS Text Engineering)
Văn bản để mắt đọc khác với văn bản để AI phát âm hay. Trước khi truyền vào `-t`, hãy tinh chỉnh lời thoại theo 4 nguyên tắc:

1. **Điều khiển nhịp thở & ngữ điệu bằng dấu câu**:
   - **Dấu phẩy `,`**: Tạo nhịp lấy hơi ngắn (`~0.2s`). Bắt buộc chèn vào các câu dài trên 15 chữ để tránh AI đọc một lèo bị hụt hơi hoặc nuốt âm.
   - **Dấu ba chấm `...`**: Kéo dài nhẹ âm tiết trước đó, tạo sự ngập ngừng, bí ẩn, hoặc dư âm cảm xúc.
   - **Dấu gạch ngang ` - `**: Ngắt nhịp dứt khoát để nhấn mạnh vế giải thích hoặc cú lật phía sau.
   - **Dấu chấm than `!` & dấu hỏi `?`**: Đẩy cao cao độ cuối câu. Chỉ dùng ở điểm nhấn thực sự; tránh lạm dụng `!` ở mọi câu khiến giọng bị gắt.
2. **Tách câu theo cụm cảm xúc**:
   - Mỗi file `.wav` chỉ nên chứa **1 đến 3 câu cùng một trạng thái cảm xúc**. Khi mạch truyện đổi tông (ví dụ: đang kể bình thản chuyển sang giận dữ hoặc tiết lộ bí mật), **bắt buộc tách thành file `.wav` riêng** để kiểm soát nhịp nghỉ và biểu cảm tốt nhất.
3. **Chuẩn hóa ký tự chống đọc vấp (Text Normalization)**:
   - Chuyển toàn bộ số liệu, đơn vị, ký hiệu sang dạng chữ tiếng Việt tự nhiên trước khi đưa vào `-t`:
     - `100%` $\rightarrow$ `một trăm phần trăm`
     - `2026` $\rightarrow$ `hai nghìn không trăm hai mươi sáu` (hoặc `hai không hai sáu` với nội dung trẻ trung)
     - `50km/h`, `$100` $\rightarrow$ `năm mươi ki-lô-mét trên giờ`, `một trăm đô-la`
4. **Quy tắc đặt thẻ cảm xúc nội tại (`[cười]`, `[thở dài]`, `[hắng giọng]`)**:
   - **Mở đầu sắc thái:** `"[thở dài] Giá như lúc đó tôi nhận ra sớm hơn..."`
   - **Chuyển ngoặt giữa câu:** `"Tôi cứ ngỡ mọi chuyện đã an bài... [cười] nhưng hóa ra trò chơi mới chỉ bắt đầu."`
   - **Mật độ vàng:** Tối đa **1 thẻ cho mỗi 2–3 câu thoại**. Chèn quá dày sẽ làm giọng đọc thiếu tự nhiên.

---

## 3. Quy Tắc Bất Biến Về Phạm Vi Giọng Đọc (Voice Scope Policy)

1. **Tính nhất quán toàn kịch bản**:
   - Khi người dùng hoặc kịch bản đã chỉ định một giọng chủ đạo (ví dụ: `"nữ chính"`, `"Trúc Ly"`, `"Thiện Minh"`...), **BẮT BUỘC dùng duy nhất giọng đó cho 100% các phân đoạn**. Tuyệt đối không tự ý đổi sang giọng khác giữa chừng trừ khi kịch bản ghi rõ phân vai đổi người nói.

2. **Phân biệt rạch ròi 2 loại thẻ trong kịch bản**:
   - **Thẻ hiệu ứng cảm xúc nội tại (`[cười]`, `[thở dài]`, `[hắng giọng]`)**: Nằm *bên trong câu nói* để chính giọng đang chọn tự phát ra tiếng cười/thở dài. **CẤM TUYỆT ĐỐI** việc thấy thẻ `[cười]` mà tự động đổi sang giọng nhân vật khác (như Sukuna).
   - **Thẻ nhân vật & thần thái (`[sukuna: ngạo nghễ]`, `[sukuna: uy quyền]`, `[nữ chính]`)**: Dùng để ánh xạ sang tham số `-v`.

---

## 4. Bảng Ánh Xạ Phân Vai, Biến Thể & Nhân Bản Giọng

| Giọng / Nhân vật chỉ định | Thần thái / Chế độ | Tham số truyền vào CLI | Quy tắc xử lý |
| :--- | :--- | :--- | :--- |
| **`"nữ chính"`** | Mọi sắc thái (vui, cười, buồn, kể chuyện...) | `-v "nữ chính"` *(xuyên suốt)* | Giữ nguyên thẻ `[cười]`, `[thở dài]` trong chuỗi `-t` để mô hình nữ chính tự diễn cảm. |
| **Giọng mẫu tích hợp khác** (`"Trúc Ly"`, `"Thiện Minh"`...) | Mọi sắc thái | `-v "<tên_giọng>"` *(xuyên suốt)* | Nếu chưa chắc tên giọng có sẵn, chạy `vieneu.bat --list-voices` để kiểm tra trước. |
| **`"sukuna"`** (hoặc phân vai Sukuna) | Mặc định / Chung chung | `-v "sukuna"` | Bản chuẩn đa dụng. |
| | `[uy quyền]`, `[trầm ổn]`, `[ra lệnh]`, `[triết lý]` | `-v "sukuna (uy quyền)"` | Biến thể trầm đục, uy nghiêm, độc thoại đĩnh đạc. |
| | `[ngạo nghễ]`, `[khiêu khích]`, `[chiến đấu]`, `[cười cợt]` | `-v "sukuna (ngạo mạn)"` | Biến thể gằn khàn, ma mị, khiêu khích, cười nhếch mép. |
| **Nhân bản từ file âm thanh mẫu** | Người dùng cung cấp file `.wav` mẫu | `-r "<duong_dan\ref_voice.wav>"` | Thay tham số `-v` bằng `-r` để clone giọng trực tiếp từ file mẫu (nên dùng file mẫu sạch tạp âm, dài 5–15 giây). |

---

## 5. Quy Trình Thực Thi: Biên Tập $\rightarrow$ Sinh Audio $\rightarrow$ Đo Thời Lượng $\rightarrow$ Dựng Nhịp Concat MCP

### Bước 1: Phân tích kịch bản, chốt giọng & quy tắc đặt tên file
- Đọc toàn bộ kịch bản, xác định thể loại nội dung và biên tập lại lời thoại theo **Mục 2** (chèn dấu ngắt nghỉ, chuẩn hóa số/ký hiệu, đặt thẻ cảm xúc đúng điểm rơi).
- Xác định cố định tham số `-v` (hoặc `-r`) trước khi chạy lệnh đầu tiên.
- Đặt tên file theo quy tắc `voice_<stt>_<moc_giay>s.wav` (ví dụ `voice_01_0000s.wav`, `voice_02_0014s.wav` tương ứng mốc giây dự kiến trên timeline) trong `<PROJECT_DIR>\temp_assets\voiceover\` để không bao giờ ghi đè file trước đó.

### Bước 2: Chạy lệnh sinh audio (Tuần tự từng câu/đoạn)
- **Cách 1 — Đọc từng cụm câu thoại đã biên tập ngữ điệu:**
  ```powershell
  & "F:\A_Tool\Tools\VieNeu-TTS\vieneu.bat" -t "Tôi cứ ngỡ mọi chuyện đã kết thúc ở đó... [cười] nhưng hóa ra, màn kịch mới chỉ vừa bắt đầu!" -v "nữ chính" -o "<PROJECT_DIR>\temp_assets\voiceover\voice_01_0014s.wav"
  ```
- **Cách 2 — Nhân bản giọng từ file `.wav` mẫu:**
  ```powershell
  & "F:\A_Tool\Tools\VieNeu-TTS\vieneu.bat" -t "Chào mừng các bạn đã quay trở lại với kênh của mình." -r "<duong_dan\ref_voice.wav>" -o "<PROJECT_DIR>\temp_assets\voiceover\voice_01_0000s.wav"
  ```

### Bước 3: Kiểm tra file & đo thời lượng thực tế
Trước khi chèn vào timeline, kiểm tra file `.wav` tồn tại (`Length > 0`) và đo chính xác độ dài thực tế (tính bằng giây) bằng `ffprobe`:
```powershell
$wavPath = "<PROJECT_DIR>\temp_assets\voiceover\voice_01_0014s.wav"
if ((Test-Path $wavPath) -and ((Get-Item $wavPath).Length -gt 0)) {
    $duration = & ffprobe -v error -show_entries format=duration -of default=noprint_wrappers=1:nokey=1 "$wavPath"
    Write-Output "File OK | Duration: $([math]::Round([double]$duration, 3))s"
} else {
    Write-Error "Lỗi: File audio không tồn tại hoặc rỗng!"
}
```

### Bước 4: Dựng nhịp (Dynamic Pacing) & Chèn vào Track Audio của Concat MCP
1. Đọc trạng thái timeline hiện tại qua `timeline_read` để xác định track Audio dành cho lồng tiếng (Voiceover) và vị trí kết thúc của clip thoại liền trước (`prev_end_time`).
2. Tính mốc đặt clip mới (`start_time = prev_end_time + gap`) dựa theo **nhịp điệu cốt truyện** (nếu kịch bản không ép mốc thời gian cứng):
   - **Đối thoại dồn dập / Hành động / Tranh luận:** `gap = 0.05s – 0.15s` (nối sát, tạo cảm giác gấp gáp).
   - **Thuyết minh / Kể chuyện mạch lạc chuẩn:** `gap = 0.25s – 0.40s` (khoảng lấy hơi tự nhiên).
   - **Chuyển cảnh / Chuyển ý lớn:** `gap = 0.50s – 0.80s` (cho người xem thời gian ngấm hình ảnh).
   - **Khoảng lặng đắt giá (trước Plot Twist hoặc sau câu thoại cao trào):** `gap = 0.80s – 1.20s` (tạo sức nặng cảm xúc).
3. Nếu có mốc thời gian cứng từ kịch bản, đối chiếu `start_time + duration` với clip kế tiếp để đảm bảo **không bị đè âm thanh** (nếu bị lẹm sang câu sau, báo lại hoặc điều chỉnh giãn cảnh hình ảnh tương ứng).
4. Gọi công cụ chèn media của Concat MCP để đưa file `.wav` từ `<PROJECT_DIR>\temp_assets\voiceover\` vào đúng track Audio.