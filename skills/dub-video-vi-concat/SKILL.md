---
name: dub-video-vi-concat
description: "Skill độc lập điều phối quy trình lồng tiếng (dubbing) và tái dựng video sang tiếng Việt trên Concat MCP: tải video (yt-dlp), tôn trọng bản cắt trên timeline của người dùng, tách riêng lời thoại gốc và âm thanh cảnh quan bằng Demucs, trích xuất kịch bản chuẩn mốc thời gian bằng WhisperX, hỗ trợ chỉnh sửa kịch bản đa nhân vật/đa sắc thái, xóa watermark & phụ đề cứng bằng VSR, lồng tiếng VieNeu-TTS, tạo phụ đề chuẩn QC (subtitle-craft) và tinh chỉnh hiệu ứng hình ảnh chống nhàm chán (dynamic-visual-enhancer)."
---

# Quy Trình Lồng Tiếng & Tái Dựng Video Tiếng Việt (`dub-video-vi-concat`)

Đây là **skill độc lập** (đặt tại `skills/dub-video-vi-concat/SKILL.md`), đóng vai trò quy trình đầu-cuối (end-to-end) để chuyển ngữ và lồng tiếng một video bất kỳ sang tiếng Việt trên **Concat Video Editor MCP**, đồng thời tái sử dụng các công cụ CLI và sub-skill chuyên biệt từ hệ sinh thái **`main-ntt-edit`**.

---

## 1. Kiến Trúc Liên Kết & Quy Tắc An Toàn Tuyệt Đối

### 1.1. Đường dẫn công cụ & Sub-skill liên kết (`main-ntt-edit`)
Khi thực thi từng công đoạn, đọc và tuân thủ quy chuẩn kỹ thuật từ các module tương ứng của `main-ntt-edit`:
* **Nhạc trưởng Concat MCP**: `../main-ntt-edit/SKILL.md`
* **Tiền xử lý, tách tiếng & chép lời**: `../main-ntt-edit/modules/media-preprocess/SKILL.md`
* **Tổng hợp giọng nói tiếng Việt**: `../main-ntt-edit/modules/vieneu-tts-voiceover/SKILL.md`
* **Biên tập & kiểm chuẩn phụ đề (QC)**: `../main-ntt-edit/modules/subtitle-craft/SKILL.md` (script QC: `../main-ntt-edit/modules/subtitle-craft/scripts/subtitle_engine.py`)
* **Hiệu ứng & chuyển cảnh native Concat**: `../main-ntt-edit/modules/concat-native-fx/SKILL.md`
* **Hiệu ứng chuyển động & chống nhàm chán**: `../main-ntt-edit/modules/dynamic-visual-enhancer/SKILL.md` và `../main-ntt-edit/modules/hyperframes-motion/SKILL.md`

**Đường dẫn CLI thực thi trực tiếp (môi trường `NttDzEditVideo` — Python 3.10 + CUDA 12.4):**
* `yt-dlp`: `F:\A_Tool\Tools\yt-dlp\yt-dlp.bat`
* `auto-editor`: `F:\A_Tool\Tools\auto-editor\auto-editor.bat`
* `VSR` (xóa sub/watermark): `F:\A_Tool\Tools\video-subtitle-remover\vsr.bat`
* `Demucs` (tách giọng & âm thanh cảnh quan): `F:\A_Tool\Tools\demucs\demucs.bat`
* `WhisperX` (chép lời & khóa mốc thời gian): `F:\A_Tool\Tools\whisperx\whisperx.bat`
* `VieNeu-TTS` (lồng tiếng): `F:\A_Tool\Tools\VieNeu-TTS\vieneu.bat`
* `Python` / `FFmpeg` / `FFprobe` (gọi trực tiếp `.exe` để tránh lỗi encoding `charmap` của `conda run`):
  * `C:\Conda\envs\NttDzEditVideo\python.exe`
  * `C:\Conda\envs\NttDzEditVideo\Scripts\ffmpeg.exe`
  * `C:\Conda\envs\NttDzEditVideo\Scripts\ffprobe.exe`

### 1.2. Quy tắc bất khả xâm phạm
1. **Cấm tuyệt đối ghi dữ liệu lên ổ `C:`**: Mọi file tải về, file trung gian, script phụ trợ, ảnh preview kiểm chứng và file render tạm **bắt buộc** lưu trong `<PROJECT_DIR>\temp_assets\`. Tuyệt đối không ghi ra `C:\Users\...` hay `C:\Temp\`.
   * *Xử lý ngoại lệ đường dẫn ASCII cho VSR*: Nếu `<PROJECT_DIR>` chứa dấu tiếng Việt khiến FFmpeg nội bộ của VSR báo lỗi codec `cp1252`, chỉ được phép tạo thư mục tạm ASCII ngay trên ổ `F:` (ví dụ: `F:\A_Tool\Tools\video-subtitle-remover\_temp_ascii_work\`), chạy VSR xong phải chép kết quả về `<PROJECT_DIR>\temp_assets\preprocess\` và xóa ngay thư mục tạm đó.
2. **Bảo vệ 6GB VRAM (NVIDIA RTX 3060)**: Chạy **tuần tự từng tác vụ AI một** (`Demucs` $\rightarrow$ `WhisperX` $\rightarrow$ `VSR` $\rightarrow$ `VieNeu-TTS`). Cấm chạy song song hoặc chạy khi Concat đang render.
3. **Encoding chuẩn UTF-8**: Mọi file `.ps1` sinh tự động phải lưu **UTF-8 có BOM** và đặt `$env:PYTHONIOENCODING = "utf-8"` ở đầu phiên chạy.
4. **Lưu dự án & Cấm tự ý Export**: Luôn gọi `concat_project_save` sau khi hoàn thiện timeline để đồng bộ ra giao diện Concat, sau đó **dừng lại** chờ người dùng kiểm tra (không gọi `export_start` khi chưa có lệnh).

---

## 2. Cấu Trúc Thư Mục Làm Việc Trong Dự Án (`<PROJECT_DIR>`)

Khởi tạo ngay khi bắt đầu phiên làm việc:
```powershell
$dirs = @("preprocess", "voiceover", "subtitles", "preview", "scripts")
foreach ($d in $dirs) {
    New-Item -ItemType Directory -Force -Path "<PROJECT_DIR>\temp_assets\$d" | Out-Null
}
```

```text
<PROJECT_DIR>\
  concat.json                             # File dự án Concat MCP
  temp_assets\
    preprocess\
      raw_downloaded.mp4                  # Video tải từ yt-dlp (nếu có)
      working_source.mp4                  # Video chuẩn hóa dùng xuyên suốt (ưu tiên từ timeline)
      raw_audio.wav                       # Âm thanh gốc tách từ working_source.mp4 (48kHz stereo)
      demucs_out\htdemucs\raw_audio\
        vocals.wav                        # Track lời thoại gốc (chỉ dùng để chạy WhisperX)
        no_vocals.wav                     # Track âm thanh cảnh quan/SFX/nhạc nền gốc
      ambient_ready.wav                   # Âm thanh cảnh quan đã chuẩn hóa LUFS (giữ cho bản cuối)
      script.txt                          # Kịch bản mốc thời gian + thẻ nhân vật/cảm xúc
      transcript.json                     # Dữ liệu JSON gốc từ WhisperX
      video_no_watermark.mp4              # Video sau bước xóa watermark/logo
      video_clean.mp4                     # Video sạch hoàn chỉnh (đã xóa watermark + phụ đề cứng)
      video_clean_mute.mp4                # Bản video sạch đã tắt tiếng gốc (-an) để đặt lên T1
    voiceover\
      raw_tts_001.wav                     # File xuất thô từ VieNeu-TTS
      voice_001.wav                       # File thoại đã xử lý hậu kỳ (48kHz mono, -14 LUFS)
      voice_manifest.json                 # Danh sách câu thoại, nhân vật, thời lượng đo bằng soundfile
      voice_schedule.json                 # Mốc đặt thực tế (place) chống chồng lấn trên timeline
    subtitles\
      vi_subtitles.srt                    # File phụ đề chuẩn đã qua vòng kiểm tra QC
    preview\
      check_*.png                         # Frame xuất bằng ffmpeg.exe để kiểm chứng bằng OpenCV
    scripts\
      parse_and_tts.ps1                   # Script đọc script.txt và sinh giọng đọc
      schedule_and_mix.py                 # Script xếp lịch chống đè & kiểm tra peak mix
      verify_visual.py                    # Script kiểm tra số liệu xóa sub/watermark bằng cv2
```

---

## 3. Luồng Công Việc 3 Giai Đoạn (Có Điểm Dừng Kiểm Duyệt)

Quy trình được chia làm **3 giai đoạn rõ ràng** với **2 điểm dừng bắt buộc (Human-in-the-Loop)** để người dùng kiểm tra và tinh chỉnh trước khi chạy sản xuất hàng loạt.

---

### GIAI ĐOẠN 1: Thu Thập Video & Chốt Nguồn Timeline `[DỪNG KIỂM TRA 1]`

#### Bước 1.1 — Kiểm tra dự án Concat & Tải video (nếu có link)
1. Gọi `concat_timeline_read(path="<PROJECT_DIR>")` để kiểm tra trạng thái timeline hiện tại.
2. Nếu người dùng cung cấp đường dẫn URL (YouTube, TikTok, Douyin, Bilibili...), tải video chuẩn MP4 (H.264 + AAC) bằng `yt-dlp`:
   ```powershell
   & "F:\A_Tool\Tools\yt-dlp\yt-dlp.bat" --no-playlist --restrict-filenames -f "bv*[vcodec^=avc1]+ba[acodec^=mp4a]/b[ext=mp4]" --merge-output-format mp4 -o "<PROJECT_DIR>\temp_assets\preprocess\raw_downloaded.mp4" "<URL>"
   ```
   *(Nếu timeline đang trống, import `raw_downloaded.mp4` qua `concat_media_import` và đặt lên track video chính tại `0.0s`, sau đó gọi `concat_project_save`).*

#### Bước 1.2 — Điểm dừng 1: Yêu cầu người dùng kiểm tra & cắt tỉa
* **Dừng thực thi** và thông báo cho người dùng:
  > *"Đã sẵn sàng video nguồn. Bạn hãy kiểm tra trực tiếp trên timeline của Concat và cắt bỏ những đoạn mở đầu, đoạn thừa hoặc khoảng chết không cần thiết. Khi hoàn tất, hãy nhắn tôi tiếp tục để trích xuất âm thanh và kịch bản."*

---

### GIAI ĐOẠN 2: Xác Định Video Chuẩn, Tách Âm Thanh & Trích Xuất Kịch Bản `[DỪNG KIỂM TRA 2]`

Ngay khi người dùng xác nhận tiếp tục sau Giai đoạn 1:

#### Bước 2.1 — Áp dụng quy tắc ưu tiên video trên Timeline
1. Gọi lại `concat_timeline_read(path="<PROJECT_DIR>")` để đọc danh sách clip trên track video chính:
   * **Trường hợp A — Trên timeline CÓ video (do người dùng đưa vào hoặc vừa cắt tỉa lại):**
     * **Bắt buộc** lấy chính video/các đoạn cắt trên timeline làm nguồn duy nhất cho toàn bộ các bước sau (để mốc thời gian kịch bản khớp tuyệt đối với timeline).
     * Nếu video trên timeline gồm nhiều đoạn cắt ghép hoặc bị trim điểm đầu/cuối, dùng `ffmpeg.exe` cắt/nối đúng theo thông số `in_sec`, `out_sec` trên timeline để xuất ra `<PROJECT_DIR>\temp_assets\preprocess\working_source.mp4` (hoặc export nhanh bản nháp không hiệu ứng vào `working_source.mp4`).
   * **Trường hợp B — Trên timeline KHÔNG có video:**
     * Chép `<PROJECT_DIR>\temp_assets\preprocess\raw_downloaded.mp4` thành `working_source.mp4` và nạp lên track video chính của timeline tại `0.0s`.
2. Đo thông số kỹ thuật (`width`, `height`, `fps`, `duration`) của `working_source.mp4` bằng `ffprobe.exe` và cập nhật cấu hình dự án Concat khớp tỷ lệ khung hình gốc.

#### Bước 2.2 — Tách âm thanh thành 2 phần: Lời thoại + Âm thanh cảnh quan (`Demucs`)
1. Trích xuất file âm thanh gốc chất lượng cao từ `working_source.mp4`:
   ```powershell
   & "C:\Conda\envs\NttDzEditVideo\Scripts\ffmpeg.exe" -y -v error -i "<PROJECT_DIR>\temp_assets\preprocess\working_source.mp4" -vn -ac 2 -ar 48000 -c:a pcm_s16le "<PROJECT_DIR>\temp_assets\preprocess\raw_audio.wav"
   ```
2. Chạy **`Demucs`** tách riêng 2 stem (`vocals.wav` và `no_vocals.wav`):
   ```powershell
   & "F:\A_Tool\Tools\demucs\demucs.bat" --two-stems=vocals -n htdemucs "<PROJECT_DIR>\temp_assets\preprocess\raw_audio.wav" -o "<PROJECT_DIR>\temp_assets\preprocess\demucs_out"
   ```
   * **`vocals.wav`** (lời thoại gốc): Chỉ dùng cho Bước 2.3 để nhận diện chữ, **sẽ bị loại bỏ hoàn toàn** ở bản dựng cuối.
   * **`no_vocals.wav`** (âm thanh cảnh quan, tiếng động môi trường, SFX, nhạc nền): Chuẩn hóa về `-22 LUFS` thành `<PROJECT_DIR>\temp_assets\preprocess\ambient_ready.wav` để **giữ nguyên cho sản phẩm cuối cùng**:
     ```powershell
     & "C:\Conda\envs\NttDzEditVideo\Scripts\ffmpeg.exe" -y -v error -i "<PROJECT_DIR>\temp_assets\preprocess\demucs_out\htdemucs\raw_audio\no_vocals.wav" -af "loudnorm=I=-22:TP=-2.0:LRA=11" -ar 48000 -ac 2 -c:a pcm_s16le "<PROJECT_DIR>\temp_assets\preprocess\ambient_ready.wav"
     ```

#### Bước 2.3 — Trích xuất kịch bản theo mốc thời gian Timeline (`WhisperX`)
1. Chạy `WhisperX` trên file giọng sạch `vocals.wav` (tự động nhận diện ngôn ngữ gốc hoặc truyền `--language` nếu đã biết):
   ```powershell
   & "F:\A_Tool\Tools\whisperx\whisperx.bat" "<PROJECT_DIR>\temp_assets\preprocess\demucs_out\htdemucs\raw_audio\vocals.wav" --model large-v3-turbo --compute_type float16 --batch_size 8 --output_dir "<PROJECT_DIR>\temp_assets\preprocess" --output_format json
   ```
2. Chuyển đổi `vocals.json` sang file kịch bản `<PROJECT_DIR>\temp_assets\preprocess\script.txt` kèm phần chú thích hướng dẫn sử dụng thẻ ở đầu file:
   ```text
   # ==============================================================================
   # KỊCH BẢN LỒNG TIẾNG (script.txt) - Mốc thời gian đồng bộ Timeline Concat
   # HƯỚNG DẪN CHỈNH SỬA:
   # 1. Giữ nguyên cụm [HH:MM:SS -> HH:MM:SS]: ở đầu dòng (mốc trên timeline).
   # 2. Thay lời thoại gốc bằng lời thoại tiếng Việt cần lồng tiếng.
   # 3. Thêm thẻ nhân vật (nếu nhiều giọng): [nv: Tên_Giọng] (VD: [nv: Trúc Ly], [nv: Thiện Minh]).
   # 4. Thêm thẻ sắc thái/cảm xúc trước lời thoại: [giận dữ], [lớn giọng], [trầm ổn], [chế giễu], [ngạc nhiên]...
   # 5. Thẻ tiếng động nội bộ VieNeu-TTS đặt trong câu: [cười], [thở dài]...
   # ==============================================================================
   [00:00:02 -> 00:00:05]: Nguyên văn lời thoại 1
   [00:00:07 -> 00:00:11]: Nguyên văn lời thoại 2
   ```

#### Bước 2.4 — Điểm dừng 2: Yêu cầu người dùng kiểm duyệt & gắn thẻ kịch bản
* **Dừng thực thi**, hiển thị đường dẫn file `<PROJECT_DIR>\temp_assets\preprocess\script.txt` và mời người dùng:
  1. Kiểm tra lại độ chính xác của mốc thời gian và nội dung trích xuất.
  2. Dịch/biên tập lại lời thoại tiếng Việt, bổ sung các câu còn thiếu.
  3. Chèn trực tiếp các thẻ nhân vật (`[nv: ...]`) và thẻ cảm xúc (`[giận dữ]`, `[lớn giọng]`, `[trầm ổn]`, `[cười]`...) vào file `script.txt`.
  4. Nhắn lệnh tiếp tục khi đã chỉnh sửa xong `script.txt`.

---

### GIAI ĐOẠN 3: Sản Xuất Tự Động Toàn Phần & Lưu Timeline

Khi người dùng xác nhận `script.txt` đã xong và yêu cầu tiếp tục, thực hiện **tuần tự từng bước** (không chạy song song tác vụ GPU):

#### Bước 3.1 — Quy tắc phân tích cú pháp `script.txt` (Chống nhầm lẫn thẻ)
Bộ parser Python phải phân tách rạch ròi 4 thành phần trên mỗi dòng hợp lệ (bỏ qua dòng trống hoặc dòng bắt đầu bằng `#`):

| Loại cú pháp | Mẫu nhận diện (Regex / Token) | Cách xử lý của hệ thống |
| :--- | :--- | :--- |
| **1. Mốc thời gian Timeline** | `^\[\s*(\d{1,2}:\d{2}(?::\d{2})?(?:\.\d+)?)\s*->\s*(\d{1,2}:\d{2}(?::\d{2})?(?:\.\d+)?)\s*\]\s*:?` | Quy đổi sang giây (`start_sec`, `end_sec`) làm vị trí neo mục tiêu trên timeline. **Không bao giờ đọc thành tiếng.** |
| **2. Thẻ nhân vật / Giọng đọc** | `\[(?:nv|voice)\s*:\s*([^\]]+)\]` | Chọn mẫu giọng trong `VieNeu-TTS` (VD: `Trúc Ly`, `Thiện Minh`, hoặc giọng clone). Nếu dòng không ghi thẻ này, dùng giọng mặc định của nhân vật chính. **Không đọc thành tiếng.** |
| **3. Thẻ chỉ đạo cảm xúc / Sắc thái** | `[giận dữ]`, `[lớn giọng]`, `[uy quyền]`, `[trầm ổn]`, `[chế giễu]`, `[ngạc nhiên]`, `[buồn bã]`, `[vui vẻ]`, `[thì thầm]`... | Ánh xạ sang biến thể giọng/tham số tốc độ & EQ tương ứng (xem Bảng ánh xạ bên dưới), sau đó **xóa khỏi chuỗi văn bản** trước khi đưa vào TTS và phụ đề. |
| **4. Thẻ biểu cảm âm thanh nội bộ TTS** | `[cười]`, `[thở dài]`, `[hắng giọng]`... | **Giữ nguyên** trong chuỗi đưa vào `vieneu.bat` để AI phát ra tiếng cười/thở dài tự nhiên, nhưng **xóa khỏi chuỗi** khi xuất file phụ đề `.srt`. |

**Bảng ánh xạ thẻ sắc thái cảm xúc sang thông số giọng & hậu kỳ:**
* `[giận dữ]`, `[lớn giọng]`, `[uy quyền]`: Chọn biến thể giọng đanh thép (nếu có), tăng nhẹ tốc độ đọc (`+5%`), tăng EQ dải trung-cao (`+2dB @ 3kHz`) và nén động lực chắc tiếng.
* `[chế giễu]`, `[ngạo mạn]`: Chọn biến thể giọng ngạo mạn/nhấn nhá, giữ tốc độ tự nhiên.
* `[trầm ổn]`, `[nghiêm túc]`: Giảm nhẹ tốc độ (`-5%`), tăng ấm dải trầm (`lowshelf +3.5dB @ 170Hz`).
* `[vui vẻ]`, `[hào hứng]`: Tăng nhẹ tốc độ (`+5%`), giữ âm sắc sáng.
* *(Mọi thẻ `[...]` nằm ngoài danh sách thẻ nội bộ của VieNeu-TTS đều phải được lọc bỏ khỏi text trước khi đọc để tránh AI đọc nhầm tên thẻ).*

#### Bước 3.2 — Xóa Watermark / Logo & Che/Xóa Phụ Đề Cứng (`VSR AI`)
1. **Xác định tọa độ vùng cần xóa (`YMIN YMAX XMIN XMAX`)**:
   * Dùng script OpenCV (`C:\Conda\envs\NttDzEditVideo\python.exe`) quét mẫu frame trong `working_source.mp4` để tìm tọa độ hộp bao (`bbox`) của **watermark/logo** (thường ở 4 góc màn hình) và **dải phụ đề cứng** (thường ở dải dưới `y: 75%–98%` khung hình).
2. **Chạy VSR làm sạch tuần tự (hoặc truyền nhiều cờ `-c` trong 1 lần chạy)**:
   * Nếu `<PROJECT_DIR>` là đường dẫn ASCII thuần túy, chạy trực tiếp trong `<PROJECT_DIR>\temp_assets\preprocess\`.
   * Nếu `<PROJECT_DIR>` có dấu tiếng Việt, chép `working_source.mp4` sang `F:\A_Tool\Tools\video-subtitle-remover\_temp_ascii_work\src.mp4`, chạy VSR, rồi chép kết quả về `<PROJECT_DIR>\temp_assets\preprocess\video_clean.mp4` và xóa thư mục tạm trên `F:`:
     ```powershell
     & "F:\A_Tool\Tools\video-subtitle-remover\vsr.bat" `
       -i "<ascii_path\src.mp4>" `
       -o "<ascii_path\clean.mp4>" `
       -c <YMIN_LOGO> <YMAX_LOGO> <XMIN_LOGO> <XMAX_LOGO> `
       -c <YMIN_SUB> <YMAX_SUB> <XMIN_SUB> <XMAX_SUB> `
       --inpaint-mode sttn-auto
     ```
   * *(Trường hợp phụ đề cứng nằm trên nền đen cố định hoặc VSR để lại vệt mờ ở nền chữ: có thể kết hợp thêm lớp che nền đồng màu/blur mượt bằng `FFmpeg` hoặc overlay gọn từ `hyperframes-motion` nếu người dùng yêu cầu).*
3. **Kiểm chứng bằng số liệu & Tắt tiếng gốc**:
   * Xuất 2–3 frame đối chiếu vào `<PROJECT_DIR>\temp_assets\preview\` bằng `ffmpeg.exe` và dùng `cv2` xác nhận vùng logo/phụ đề đã được hòa trộn sạch với nền.
   * Tắt hoàn toàn track âm thanh gốc trên video hình để chuẩn bị đưa lên Track T1:
     ```powershell
     & "C:\Conda\envs\NttDzEditVideo\Scripts\ffmpeg.exe" -y -v error -i "<PROJECT_DIR>\temp_assets\preprocess\video_clean.mp4" -an -c:v libx264 -crf 18 -preset medium "<PROJECT_DIR>\temp_assets\preprocess\video_clean_mute.mp4"
     ```

#### Bước 3.3 — Sinh giọng lồng tiếng đa nhân vật (`VieNeu-TTS`) & Xếp lịch chống đè
1. Đọc danh sách giọng đọc khả dụng (`& "F:\A_Tool\Tools\VieNeu-TTS\vieneu.bat" --list-voices`) và ánh xạ đúng từng nhân vật (`[nv: ...]`) trong `script.txt`.
2. Chạy lần lượt từng câu thoại qua `vieneu.bat` (UTF-8 BOM `.ps1`), sau đó chuẩn hóa toàn bộ clip thoại về **48kHz Mono, `-14 LUFS`, chống vỡ tiếng (`alimiter`)**:
   ```powershell
   & "C:\Conda\envs\NttDzEditVideo\Scripts\ffmpeg.exe" -y -v error -i "<raw_tts.wav>" -af "highpass=f=70,lowshelf=g=3.0:f=170,acompressor=threshold=-20dB:ratio=3:attack=6:release=180,loudnorm=I=-14:TP=-1.5:LRA=9,alimiter=limit=0.95" -ar 48000 -ac 1 "<voice_out.wav>"
   ```
3. **Đo độ dài thực tế & Tính mốc đặt (`place`) chống chồng lấn**:
   * Dùng thư viện `soundfile` trong Python để đo `duration` chính xác từng file `voice_*.wav`.
   * Tính vị trí đặt thực tế trên timeline:
     $$\text{place}_i = \max(\text{script\_start}_i,\; \text{place}_{i-1} + \text{duration}_{i-1} + 0.08)$$
   * Lưu toàn bộ thông tin vào `<PROJECT_DIR>\temp_assets\voiceover\voice_schedule.json`.

#### Bước 3.4 — Tinh chỉnh âm thanh cảnh quan (`ambient_ready.wav`) & Kiểm tra Mix
* Thay vì xóa sạch âm thanh gốc, ta giữ nguyên `ambient_ready.wav` (đã tách bằng `Demucs` ở Giai đoạn 2) làm nền không gian tự nhiên cho video.
* Nếu âm thanh cảnh quan có đoạn nhạc/tiếng động lớn đè lên giọng lồng tiếng, áp dụng giảm âm lượng mượt (`ducking` êm từ `1.0` xuống `0.45`–`0.60` với thời gian chuyển `ramp = 0.15s`) đúng trong các khoảng `[place_i, place_i + duration_i]`, giữ nguyên `1.0` ở các đoạn không thoại.
* Kiểm tra bằng Python (`soundfile` + `numpy`) đảm bảo tổng biên độ đỉnh (peak mix) của `ambient` + `voiceover` luôn **$< -0.5\text{ dBFS}$** (không clipping).

#### Bước 3.5 — Dựng Timeline trên Concat MCP & Thêm Phụ Đề Chuẩn QC
1. Xóa các clip nháp cũ trên timeline (nếu có) và import toàn bộ tài nguyên sạch qua `concat_media_import`:
   * **Track T1 (Video chính)**: `video_clean_mute.mp4` đặt tại `0.0s`.
   * **Track T2 (Âm thanh cảnh quan)**: `ambient_ready.wav` đặt tại `0.0s` (volume `0.85`–`0.95`).
   * **Track T3 (Lời thoại lồng tiếng)**: Các clip `voice_XXX.wav` đặt chính xác tại `place_i` (volume `1.0`).
2. **Tạo & Kiểm chuẩn Phụ Đề (`subtitle-craft`)**:
   * Tạo file `<PROJECT_DIR>\temp_assets\subtitles\vi_subtitles.srt` bám sát mốc `place_i` và `duration_i` của giọng đọc tiếng Việt (đã lọc bỏ mọi thẻ `[...]` trong nội dung hiển thị).
   * Tách câu dài thành các cue ngắn gọn ($\text{CPL} \le 42\text{ ký tự/dòng}$, $\text{CPS} \le 17\text{ ký tự/giây}$, thời lượng tối thiểu `1.0s`, khoảng hở giữa 2 cue $\approx 0.06\text{s}$).
   * Chạy vòng lặp kiểm tra chất lượng bằng `subtitle_engine.py` đến khi đạt `0 lỗi`:
     ```powershell
     $env:PYTHONIOENCODING = "utf-8"
     & "C:\Conda\envs\NttDzEditVideo\python.exe" "..\main-ntt-edit\modules\subtitle-craft\scripts\subtitle_engine.py" qc "<PROJECT_DIR>\temp_assets\subtitles\vi_subtitles.srt" --mode 16:9 --fps <FPS_DU_AN>
     ```
   * Nạp phụ đề đạt chuẩn lên **Track T4 (trên cùng)** bằng `concat_captions_add`.

#### Bước 3.6 — Tinh chỉnh hiệu ứng hình ảnh chống nhàm chán (`dynamic-visual-enhancer`)
* Đọc sub-skill `../main-ntt-edit/modules/dynamic-visual-enhancer/SKILL.md` và áp dụng các điểm nhấn thị giác tiết chế để video lồng tiếng sinh động, giữ chân người xem mà không gây rối mắt:
  * **Nhấn nhịp thoại (Subtle Zoom / Punch-in)**: Tạo chuyển động zoom nhẹ (`1.0` $\rightarrow$ `1.05`–`1.08`) tại các câu thoại cao trào hoặc thẻ cảm xúc mạnh (`[giận dữ]`, `[lớn giọng]`, `[ngạc nhiên]`).
  * **Từ khóa / Callout đồ họa (nếu phù hợp nội dung)**: Chèn nhãn tên nhân vật (Lower-third) khi nhân vật mới xuất hiện lần đầu hoặc overlay từ khóa nổi bật (`.webm` nền trong suốt tạo bằng `hyperframes-motion`).
  * **Chuyển cảnh mượt**: Thêm crossfade ngắn (`0.15s`–`0.25s`) tại các điểm cắt nối.

#### Bước 3.7 — Nghiệm thu & Lưu dự án (`concat_project_save`)
1. Rà soát toàn bộ timeline qua `concat_timeline_read`: đảm bảo không có clip chồng lấn trên cùng track, phụ đề nằm trên lớp video, không có file tạm nào nằm ngoài `<PROJECT_DIR>\temp_assets\`.
2. Gọi **`concat_project_save(path="<PROJECT_DIR>")`**.
3. Báo cáo tóm tắt kết quả cho người dùng (số câu thoại đã lồng tiếng, danh sách nhân vật đã dùng, trạng thái xóa watermark/sub, QC phụ đề) và **mời người dùng kiểm tra trực tiếp trên cửa sổ Concat** trước khi xuất bản.

---

## 4. Checklist Xác Nhận Trước Khi Hoàn Tất

- [ ] **Không có bất kỳ file nào được ghi lên ổ `C:`** (toàn bộ nằm trong `<PROJECT_DIR>\temp_assets\`).
- [ ] Video nguồn tuân thủ đúng quy tắc ưu tiên (lấy bản đã cắt trên timeline của người dùng nếu có).
- [ ] Âm thanh gốc đã tách bằng `Demucs`: lời thoại cũ bị thay thế 100%, âm thanh cảnh quan (`no_vocals`) được giữ lại mượt mà.
- [ ] Kịch bản `script.txt` đã phân tách chuẩn xác `[mốc thời gian]`, `[nv: nhân vật]`, `[thẻ cảm xúc]` (không đọc nhầm thẻ thành tiếng).
- [ ] Watermark/logo và phụ đề cứng đã được xóa sạch và kiểm chứng bằng số liệu OpenCV.
- [ ] Phụ đề tiếng Việt đạt chuẩn `subtitle-craft` QC (CPL/CPS) và nằm trên track cao nhất.
- [ ] Đã bổ sung hiệu ứng thị giác chống nhàm chán hợp lý và gọi `concat_project_save` (chưa tự ý export).