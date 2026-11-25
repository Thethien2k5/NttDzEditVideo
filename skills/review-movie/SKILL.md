---
name: review-movie
description: "Skill độc lập điều phối quy trình làm video review / tóm tắt phim & video sang tiếng Việt trên Concat MCP: tải video (yt-dlp), tôn trọng bản cắt timeline của người dùng, tách âm thanh cảnh quan bằng Demucs, trích xuất kịch bản gốc bằng WhisperX và tự động biên soạn thêm kịch bản dẫn truyện ngôi thứ 3 (dừng báo cáo cả 2 file để kiểm duyệt), cắt gọn thông minh các đoạn tĩnh/ít thoại kết hợp biến đổi hình ảnh tránh bản quyền, chèn meme & sound-effects từ kho main-ntt-edit, xóa watermark/sub bằng VSR, lồng tiếng dẫn truyện VieNeu-TTS và dựng phụ đề chuẩn QC."
---

# Quy Trình Dựng Video Review & Tóm Tắt Ngôi Thứ 3 (`review-movie`)

Đây là **skill độc lập** (đặt tại `skills/review-movie/SKILL.md`), kế thừa kiến trúc vận hành từ `dub-video-vi-concat` và mở rộng chuyên sâu cho thể loại **Review / Tóm tắt phim & video** trên **Concat Video Editor MCP**, kết hợp kho tài nguyên và các module xử lý của **`main-ntt-edit`**.

---

## 1. Kiến Trúc Liên Kết & Quy Tắc An Toàn Tuyệt Đối

### 1.1. Đường dẫn công cụ, Sub-skill & Kho tài nguyên (`main-ntt-edit`)
Khi thực thi từng công đoạn, đọc và tuân thủ quy chuẩn kỹ thuật từ các module và thư mục tài nguyên của `main-ntt-edit`:
* **Nhạc trưởng Concat MCP**: `../main-ntt-edit/SKILL.md`
* **Tiền xử lý, tách tiếng & chép lời**: `../main-ntt-edit/modules/media-preprocess/SKILL.md`
* **Tổng hợp giọng nói tiếng Việt**: `../main-ntt-edit/modules/vieneu-tts-voiceover/SKILL.md`
* **Biên tập & kiểm chuẩn phụ đề (QC)**: `../main-ntt-edit/modules/subtitle-craft/SKILL.md` (script QC: `../main-ntt-edit/modules/subtitle-craft/scripts/subtitle_engine.py`)
* **Hiệu ứng & chuyển cảnh native Concat**: `../main-ntt-edit/modules/concat-native-fx/SKILL.md`
* **Hiệu ứng chuyển động & chống nhàm chán**: `../main-ntt-edit/modules/dynamic-visual-enhancer/SKILL.md` và `../main-ntt-edit/modules/hyperframes-motion/SKILL.md`
* **Kho Meme hình ảnh/video**: `../main-ntt-edit/meme` (tương đương `skills/main-ntt-edit/meme`)
* **Kho Hiệu ứng âm thanh (SFX)**: `../main-ntt-edit/sound-effects` (tương đương `skills/main-ntt-edit/sound-effects`)

**Đường dẫn CLI thực thi trực tiếp (môi trường `NttDzEditVideo` — Python 3.10 + CUDA 12.4):**
* `yt-dlp`: `F:\A_Tool\Tools\yt-dlp\yt-dlp.bat`
* `auto-editor`: `F:\A_Tool\Tools\auto-editor\auto-editor.bat`
* `VSR` (xóa sub/watermark): `F:\A_Tool\Tools\video-subtitle-remover\vsr.bat`
* `Demucs` (tách giọng & âm thanh cảnh quan): `F:\A_Tool\Tools\demucs\demucs.bat`
* `WhisperX` (chép lời & khóa mốc thời gian): `F:\A_Tool\Tools\whisperx\whisperx.bat`
* `VieNeu-TTS` (lồng tiếng dẫn truyện): `F:\A_Tool\Tools\VieNeu-TTS\vieneu.bat`
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
$dirs = @("preprocess", "voiceover", "subtitles", "meme_sfx", "preview", "scripts")
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
      working_source.mp4                  # Video chuẩn hóa đầu vào (ưu tiên từ timeline)
      raw_audio.wav                       # Âm thanh gốc tách từ working_source.mp4 (48kHz stereo)
      demucs_out\htdemucs\raw_audio\
        vocals.wav                        # Track lời thoại gốc (chỉ dùng để chạy WhisperX)
        no_vocals.wav                     # Track âm thanh cảnh quan/SFX/nhạc nền gốc
      ambient_ready.wav                   # Âm thanh cảnh quan chuẩn hóa (-24 LUFS)
      vocals.json                         # Dữ liệu JSON gốc từ WhisperX
      script_original.txt                 # [FILE 1] Kịch bản nguyên văn trích xuất theo mốc thời gian
      script_review_3rd.txt               # [FILE 2] Kịch bản review dẫn truyện ngôi thứ 3
      cut_segments.json                   # Bản đồ các đoạn hình ảnh giữ lại & quy đổi mốc thời gian
      video_trimmed.mp4                   # Video đã cắt gọn đoạn tĩnh & biến đổi chống bản quyền
      ambient_trimmed.wav                 # Âm thanh cảnh quan đã cắt khớp đồng bộ với video_trimmed.mp4
      video_clean.mp4                     # Video sạch đã xóa watermark/logo & phụ đề cứng
      video_clean_mute.mp4                # Bản video review sạch đã tắt tiếng gốc (-an) đặt lên T1
    voiceover\
      raw_tts_001.wav                     # File xuất thô từ VieNeu-TTS
      voice_001.wav                       # File dẫn truyện đã xử lý hậu kỳ (48kHz mono, -14 LUFS)
      voice_manifest.json                 # Danh sách câu dẫn, sắc thái, thời lượng đo bằng soundfile
      voice_schedule.json                 # Mốc đặt thực tế (place) chống chồng lấn trên timeline
    meme_sfx\
      media_index.json                    # Chỉ mục toàn bộ file trong main-ntt-edit/meme & sound-effects
      meme_sfx_schedule.json              # Lịch chèn meme & sound-effects đã đồng bộ mốc thời gian mới
      sfx_001_ready.wav                   # Hiệu ứng âm thanh đã chuẩn hóa mức âm lượng (-16 LUFS)
      meme_001_ready.mp4                  # Clip meme đã chuẩn hóa kích thước/tỷ lệ khung hình
    subtitles\
      vi_subtitles.srt                    # File phụ đề chuẩn đã qua vòng kiểm tra QC
    preview\
      check_*.png                         # Frame xuất bằng ffmpeg.exe để kiểm chứng bằng OpenCV
    scripts\
      smart_trim_anticopyright.py         # Script phân tích chuyển động, cắt gọn & chống bản quyền
      parse_and_tts.ps1                   # Script đọc script_review_3rd.txt và sinh giọng dẫn truyện
      match_meme_sfx.py                   # Script ánh xạ meme & sound-effects từ main-ntt-edit
      schedule_and_mix.py                 # Script xếp lịch chống đè & kiểm tra peak mix
      verify_visual.py                    # Script kiểm tra số liệu xóa sub/watermark bằng cv2
```

---

## 3. Luồng Công Việc 3 Giai Đoạn (Có Điểm Dừng Kiểm Duyệt)

Quy trình được chia làm **3 giai đoạn rõ ràng** với **2 điểm dừng bắt buộc (Human-in-the-Loop)** để người dùng kiểm duyệt trước khi sản xuất hàng loạt.

---

### GIAI ĐOẠN 1: Thu Thập Video & Chốt Nguồn Timeline `[DỪNG KIỂM TRA 1]`

#### Bước 1.1 — Kiểm tra dự án Concat & Tải video (nếu có link)
1. Gọi `concat_timeline_read(path="<PROJECT_DIR>")` để kiểm tra trạng thái timeline hiện tại.
2. Nếu người dùng cung cấp đường dẫn URL (YouTube, TikTok, Douyin, Bilibili...), tải video chuẩn MP4 (H.264 + AAC) bằng `yt-dlp`:
   ```powershell
   & "F:\A_Tool\Tools\yt-dlp\yt-dlp.bat" --no-playlist --restrict-filenames -f "bv*[vcodec^=avc1]+ba[acodec^=mp4a]/b[ext=mp4]" --merge-output-format mp4 -o "<PROJECT_DIR>\temp_assets\preprocess\raw_downloaded.mp4" "<URL>"
   ```
   *(Nếu timeline đang trống, import `raw_downloaded.mp4` qua `concat_media_import` và đặt lên track video chính tại `0.0s`, sau đó gọi `concat_project_save`).*

#### Bước 1.2 — Điểm dừng 1: Yêu cầu người dùng kiểm tra & cắt tỉa sơ bộ
* **Dừng thực thi** và thông báo cho người dùng:
  > *"Đã sẵn sàng video nguồn. Bạn hãy kiểm tra trực tiếp trên timeline của Concat và cắt bỏ phần intro/outro hoặc các trường đoạn không muốn đưa vào bài review. Khi hoàn tất, hãy nhắn tôi tiếp tục để trích xuất kịch bản gốc và soạn kịch bản dẫn truyện ngôi thứ 3."*

---

### GIAI ĐOẠN 2: Trích Xuất Kịch Bản Gốc & Tạo Kịch Bản Ngôi Thứ 3 `[DỪNG KIỂM TRA 2]`

Ngay khi người dùng xác nhận tiếp tục sau Giai đoạn 1:

#### Bước 2.1 — Áp dụng quy tắc ưu tiên video trên Timeline
1. Gọi lại `concat_timeline_read(path="<PROJECT_DIR>")` để đọc danh sách clip trên track video chính:
   * **Trường hợp A — Trên timeline CÓ video**: Lấy chính video/các đoạn cắt trên timeline làm nguồn duy nhất, dùng `ffmpeg.exe` cắt/nối đúng theo `in_sec`, `out_sec` trên timeline để xuất ra `<PROJECT_DIR>\temp_assets\preprocess\working_source.mp4`.
   * **Trường hợp B — Trên timeline KHÔNG có video**: Chép `raw_downloaded.mp4` thành `working_source.mp4` và nạp lên track video chính tại `0.0s`.
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
   * **`vocals.wav`**: Chỉ dùng cho Bước 2.3 để nhận diện chữ, **sẽ bị loại bỏ hoàn toàn** ở bản dựng cuối.
   * **`no_vocals.wav`**: Chuẩn hóa về `-24 LUFS` thành `<PROJECT_DIR>\temp_assets\preprocess\ambient_ready.wav` để giữ tiếng động nền tự nhiên cho bản review:
     ```powershell
     & "C:\Conda\envs\NttDzEditVideo\Scripts\ffmpeg.exe" -y -v error -i "<PROJECT_DIR>\temp_assets\preprocess\demucs_out\htdemucs\raw_audio\no_vocals.wav" -af "loudnorm=I=-24:TP=-2.0:LRA=11" -ar 48000 -ac 2 -c:a pcm_s16le "<PROJECT_DIR>\temp_assets\preprocess\ambient_ready.wav"
     ```

#### Bước 2.3 — Xuất File 1: Kịch bản nguyên văn (`script_original.txt`) bằng `WhisperX`
1. Chạy `WhisperX` trên file giọng sạch `vocals.wav`:
   ```powershell
   & "F:\A_Tool\Tools\whisperx\whisperx.bat" "<PROJECT_DIR>\temp_assets\preprocess\demucs_out\htdemucs\raw_audio\vocals.wav" --model large-v3-turbo --compute_type float16 --batch_size 8 --output_dir "<PROJECT_DIR>\temp_assets\preprocess" --output_format json
   ```
2. Xuất dữ liệu nguyên văn kèm mốc thời gian vào **`<PROJECT_DIR>\temp_assets\preprocess\script_original.txt`**:
   ```text
   # ==============================================================================
   # [FILE 1] KỊCH BẢN NGUYÊN VĂN TRÍCH XUẤT TỪ VIDEO GỐC (script_original.txt)
   # Mục đích: Đối chiếu nội dung gốc và mốc thời gian trước khi duyệt bản Review.
   # ==============================================================================
   [00:00:02 -> 00:00:05]: Nguyên văn lời thoại 1
   [00:00:07 -> 00:00:11]: Nguyên văn lời thoại 2
   ```

#### Bước 2.4 — Xuất File 2: Tự động chuyển thể sang Kịch Bản Ngôi Thứ 3 (`script_review_3rd.txt`)
Ngay sau khi xuất xong `script_original.txt`, tự động đọc toàn bộ nội dung `script_original.txt`, phân tích mạch diễn biến và biên soạn thành file mới **`<PROJECT_DIR>\temp_assets\preprocess\script_review_3rd.txt`** theo văn phong **Người kể chuyện / Dẫn truyện ngôi thứ 3**:
* **Quy tắc chuyển thể ngôi thứ 3**:
  * Chuyển toàn bộ xưng hô trực tiếp (*"tôi"*, *"tao"*, *"mày"*, *"anh/em"*) thành góc nhìn người kể chuyện khách quan, cuốn hút (*"anh chàng"*, *"cô gái"*, *"nam chính"*, *"nhân vật này"*, *"hóa ra"*, *"không ngờ rằng..."*).
  * Gộp các câu thoại vụn vặt trong cùng một cảnh thành lời dẫn tóm tắt mạch lạc, súc tích, giữ đúng trọng tâm diễn biến và neo vào mốc thời gian gốc `[HH:MM:SS -> HH:MM:SS]:` để hệ thống khóa vùng hình ảnh tương ứng.
  * Tự động gợi ý sẵn các thẻ cảm xúc dẫn truyện (`[hào hứng]`, `[kịch tính]`, `[châm biếm]`, `[trầm ổn]`) và thẻ chèn tài nguyên (`[meme: từ_khóa]`, `[sfx: từ_khóa]`) tại các điểm nhấn hài hước hoặc cao trào.
* **Cấu trúc file `<PROJECT_DIR>\temp_assets\preprocess\script_review_3rd.txt`**:
  ```text
  # ==============================================================================
  # [FILE 2] KỊCH BẢN REVIEW DẪN TRUYỆN NGÔI THỨ 3 (script_review_3rd.txt)
  # HƯỚNG DẪN CHỈNH SỬA:
  # 1. Giữ nguyên cụm [HH:MM:SS -> HH:MM:SS]: ở đầu dòng (mốc neo cảnh phim gốc).
  #    Các đoạn hình ảnh KHÔNG nằm trong mốc kịch bản này và ít chuyển động sẽ được
  #    tự động cắt gọn ở Giai đoạn 3 để video súc tích và tránh bản quyền.
  # 2. Chỉnh sửa lời dẫn truyện ngôi thứ 3 (người kể chuyện) theo ý muốn.
  # 3. Thẻ giọng dẫn truyện (tùy chọn): [nv: Tên_Giọng] (VD: [nv: Thiện Minh]).
  # 4. Thẻ sắc thái dẫn truyện: [hào hứng], [kịch tính], [châm biếm], [trầm ổn], [ngạc nhiên]...
  # 5. Thẻ chèn Meme / SFX từ kho main-ntt-edit: [meme: từ_khóa] và/hoặc [sfx: từ_khóa].
  # ==============================================================================
  [00:00:02 -> 00:00:06]: [hào hứng] Mở đầu câu chuyện, anh chàng bất ngờ phát hiện một bí mật động trời ngay trong căn phòng của mình. [sfx: boom]
  [00:00:12 -> 00:00:18]: [châm biếm] Tưởng rằng mọi chuyện sẽ êm đẹp, nhưng pha xử lý cồng kềnh này lại khiến cả nhóm rơi vào tình huống dở khóc dở cười. [meme: cuoi_ra_nuoc_mat] [sfx: laugh]
  ```

#### Bước 2.5 — Điểm dừng 2: Bắt buộc dừng lại & Báo cáo tên 2 file cho người dùng kiểm tra
* **Dừng thực thi** ngay sau khi tạo xong 2 file, hiển thị rõ đường dẫn và tên của **cả 2 file** để người dùng kiểm tra:
  > *"Đã xuất xong 2 file kịch bản để bạn kiểm tra và đối chiếu:*
  > *1. **Kịch bản gốc nguyên văn**: `<PROJECT_DIR>\temp_assets\preprocess\script_original.txt`*
  > *2. **Kịch bản review ngôi thứ 3 (người kể/dẫn truyện)**: `<PROJECT_DIR>\temp_assets\preprocess\script_review_3rd.txt`*
  >
  > *Bạn hãy kiểm tra lại cả 2 file, chỉnh sửa lời dẫn truyện hoặc bổ sung thẻ `[meme: ...]`, `[sfx: ...]` trong file `script_review_3rd.txt`. Khi hoàn tất, hãy nhắn tôi tiếp tục để tiến hành cắt gọn tránh bản quyền, chèn meme/SFX và dựng timeline."*

---

### GIAI ĐOẠN 3: Cắt Gọn Tránh Bản Quyền, Nạp Meme/SFX & Dựng Timeline

Khi người dùng xác nhận đã kiểm tra xong 2 file kịch bản và yêu cầu tiếp tục, thực hiện **tuần tự từng bước** (không chạy song song tác vụ GPU):

#### Bước 3.1 — Quy tắc phân tích cú pháp `script_review_3rd.txt`
Bộ parser Python tách rạch ròi 5 thành phần trên mỗi dòng hợp lệ (bỏ qua dòng trống hoặc dòng bắt đầu bằng `#`):

| Loại cú pháp | Mẫu nhận diện (Regex / Token) | Cách xử lý của hệ thống |
| :--- | :--- | :--- |
| **1. Mốc cảnh neo gốc** | `^\[\s*(\d{1,2}:\d{2}(?::\d{2})?(?:\.\d+)?)\s*->\s*(\d{1,2}:\d{2}(?::\d{2})?(?:\.\d+)?)\s*\]\s*:?` | Khóa vùng hình ảnh tương ứng (`orig_start`, `orig_end`) để **bảo toàn nội dung chính** khi cắt gọn, sau đó quy đổi sang mốc timeline mới sau khi cắt. **Không đọc thành tiếng.** |
| **2. Thẻ giọng dẫn truyện** | `\[(?:nv|voice)\s*:\s*([^\]]+)\]` | Chọn mẫu giọng người kể chuyện trong `VieNeu-TTS` (mặc định dùng giọng review truyền cảm nếu không ghi). **Không đọc thành tiếng.** |
| **3. Thẻ sắc thái dẫn truyện** | `[hào hứng]`, `[kịch tính]`, `[châm biếm]`, `[giận dữ]`, `[lớn giọng]`, `[trầm ổn]`, `[ngạc nhiên]`, `[buồn bã]`... | Ánh xạ sang biến thể giọng/tốc độ & EQ tương ứng, sau đó **xóa khỏi chuỗi văn bản** trước khi đưa vào TTS và phụ đề. |
| **4. Thẻ biểu cảm nội bộ TTS** | `[cười]`, `[thở dài]`, `[hắng giọng]`... | **Giữ nguyên** trong chuỗi đưa vào `vieneu.bat` để AI phát âm tự nhiên, nhưng **xóa khỏi chuỗi** khi xuất file phụ đề `.srt`. |
| **5. Thẻ Meme & SFX** | `\[meme\s*:\s*([^\]]+)\]` và `\[sfx\s*:\s*([^\]]+)\]` | Trích xuất từ khóa để tìm file khớp trong `../main-ntt-edit/meme` và `../main-ntt-edit/sound-effects`, sau đó **xóa khỏi chuỗi văn bản** trước khi đọc và làm phụ đề. |

#### Bước 3.2 — Cắt Gọn Thông Minh & Biến Đổi Hình Ảnh Tránh Bản Quyền (`Smart Trim & Anti-Copyright`)
Chạy script Python `<PROJECT_DIR>\temp_assets\scripts\smart_trim_anticopyright.py` (kết hợp `auto-editor`, `OpenCV` và `FFmpeg`) trên `working_source.mp4` theo 4 quy tắc cốt lõi sau:

1. **Quy tắc 1 — Khóa bảo vệ mạch nội dung chính (Narrative Anchor Lock)**:
   * Tất cả các khoảng thời gian `[orig_start - 0.4s, orig_end + 0.4s]` có mặt trong `script_review_3rd.txt` được đánh dấu là **vùng nội dung cốt lõi (Protected Core)** $\rightarrow$ **Cấm cắt bỏ**, đảm bảo câu chuyện review liền mạch và đầy đủ diễn biến.
   * Đồng thời kiểm tra thời lượng dự kiến của câu dẫn tiếng Việt: nếu câu dẫn dài hơn cảnh gốc tương ứng, tự động giữ thêm phần hình ảnh chuyển động liền kề (hoặc giãn nhẹ nhịp cắt) để hình không bị hụt trước khi dứt lời dẫn.
2. **Quy tắc 2 — Tự động cắt bỏ đoạn tĩnh, ít hoạt ảnh hoặc ít lời thoại**:
   * Trên các khoảng nằm **ngoài** vùng bảo vệ cốt lõi:
     * Phân tích năng lượng âm thanh (qua `auto-editor` / `soundfile`) và chỉ số chuyển động điểm ảnh liên khung hình (`cv2.absdiff` optical motion score).
     * Loại bỏ các đoạn khung hình tĩnh (motion score thấp), khoảng lặng kéo dài, cảnh chuyển tiếp rề rà không có thoại hoặc không phục vụ nội dung review.
     * Chỉ giữ lại tối đa `0.8s–1.5s` các cảnh hành động/biểu cảm đắt giá (motion score cao) làm nhịp thở thị giác giữa các đoạn dẫn truyện.
3. **Quy tắc 3 — Phá chuỗi nhận diện bản quyền hình ảnh (Anti-Content-ID Visual Rules)**:
   * **Ngắt nhịp cảnh dài (Jump-cut / Micro-trim)**: Không để bất kỳ cảnh liên tục nào kéo dài quá `4.0s–5.0s` mà không có biến đổi; tự động chèn vết cắt vi mô (`0.15s–0.25s`) hoặc đổi góc zoom (`1.03x` $\leftrightarrow$ `1.07x`) giữa các nhịp câu dẫn.
   * **Biến đổi khung hình & màu sắc tiết chế**: Áp dụng tinh chỉnh nhẹ tỷ lệ phóng đại/crop (`scale=iw*1.04:ih*1.04,crop=iw/1.04:ih/1.04`), vi chỉnh màu sắc/tương phản (`eq=contrast=1.03:saturation=1.05:brightness=0.01`) và tốc độ nhẹ (`1.02x` nếu cần rút gọn nhịp).
   * **Lật ngang có chọn lọc (`hflip`)**: Chỉ áp dụng lật ngang cho các phân đoạn đã được kiểm tra bằng OpenCV/OCR là **không chứa chữ viết, biển hiệu hay phụ đề cứng** để tránh làm ngược chữ.
4. **Quy tắc 4 — Xuất video/âm thanh đồng bộ & Quy đổi mốc thời gian**:
   * Cắt và nối chính xác các đoạn được giữ lại thành `video_trimmed.mp4` và `ambient_trimmed.wav` (cùng một danh sách đoạn cắt để hình và tiếng khớp tuyệt đối).
   * Lưu bảng ánh xạ thời gian cũ $\rightarrow$ mới vào `<PROJECT_DIR>\temp_assets\preprocess\cut_segments.json` và cập nhật lại toàn bộ `[mapped_start, mapped_end]` cho từng dòng kịch bản trong `script_review_3rd.txt`.

#### Bước 3.3 — Xóa Watermark / Logo & Phụ Đề Cứng (`VSR AI`)
1. Quét mẫu frame trên `video_trimmed.mp4` bằng OpenCV (`cv2`) để xác định tọa độ hộp bao (`YMIN YMAX XMIN XMAX`) của watermark/logo và dải phụ đề cứng gốc (nếu video quá dài hãy chia ra từng đoạn ngắn khoản 3-4 phút để giảm gánh nặng cho thiết bị).
2. Chạy `vsr.bat` (sử dụng thư mục tạm ASCII trên ổ `F:` nếu `<PROJECT_DIR>` có dấu tiếng Việt, sau đó chép về `<PROJECT_DIR>\temp_assets\preprocess\video_clean.mp4` và dọn sạch thư mục tạm):
   ```powershell
   & "F:\A_Tool\Tools\video-subtitle-remover\vsr.bat" `
     -i "<ascii_path\trimmed.mp4>" `
     -o "<ascii_path\clean.mp4>" `
     -c <YMIN_LOGO> <YMAX_LOGO> <XMIN_LOGO> <XMAX_LOGO> `
     -c <YMIN_SUB> <YMAX_SUB> <XMIN_SUB> <XMAX_SUB> `
     --inpaint-mode sttn-auto
   ```
3. Xuất 2–3 frame đối chiếu vào `<PROJECT_DIR>\temp_assets\preview\` để kiểm chứng bằng `cv2`, sau đó tắt hoàn toàn track âm thanh gốc:
   ```powershell
   & "C:\Conda\envs\NttDzEditVideo\Scripts\ffmpeg.exe" -y -v error -i "<PROJECT_DIR>\temp_assets\preprocess\video_clean.mp4" -an -c:v libx264 -crf 18 -preset medium "<PROJECT_DIR>\temp_assets\preprocess\video_clean_mute.mp4"
   ```

#### Bước 3.4 — Sinh giọng dẫn truyện ngôi thứ 3 (`VieNeu-TTS`) & Xếp lịch chống đè
1. Đọc danh sách giọng đọc khả dụng (`& "F:\A_Tool\Tools\VieNeu-TTS\vieneu.bat" --list-voices`) và ưu tiên chọn giọng dẫn chuyện rõ ràng, truyền cảm, có nhịp điệu kể chuyện cuốn hút (hoặc đúng giọng `[nv: ...]` người dùng chỉ định).
2. Chạy tuần tự từng câu dẫn qua `vieneu.bat` (UTF-8 BOM `.ps1`), chuẩn hóa hậu kỳ về **48kHz Mono, `-14 LUFS`, chống vỡ tiếng (`alimiter`)**:
   ```powershell
   & "C:\Conda\envs\NttDzEditVideo\Scripts\ffmpeg.exe" -y -v error -i "<raw_tts.wav>" -af "highpass=f=70,lowshelf=g=3.0:f=170,acompressor=threshold=-20dB:ratio=3:attack=6:release=180,loudnorm=I=-14:TP=-1.5:LRA=9,alimiter=limit=0.95" -ar 48000 -ac 1 "<voice_out.wav>"
   ```
3. Đo `duration` thực tế bằng `soundfile` và tính vị trí đặt chống chồng lấn trên timeline đã cắt gọn:
   $$\text{place}_i = \max(\text{mapped\_start}_i,\; \text{place}_{i-1} + \text{duration}_{i-1} + 0.10)$$
   *(Nếu tổng thời lượng lời dẫn vượt quá độ dài `video_trimmed.mp4` ở cuối video, tự động điều chỉnh nhịp nghỉ hoặc kéo nhẹ thời lượng cảnh cuối để lời dẫn không bị cắt cụt).*

#### Bước 3.5 — Quét & Nạp Meme / Sound-Effects từ Kho `main-ntt-edit`
Chạy script Python `<PROJECT_DIR>\temp_assets\scripts\match_meme_sfx.py` để tích hợp tài nguyên tạo tính giải trí và giữ chân người xem:
1. **Lập chỉ mục kho tài nguyên**:
   * Quét toàn bộ file trong `../main-ntt-edit/sound-effects` (`.wav`, `.mp3`, `.ogg`, `.m4a`) và `../main-ntt-edit/meme` (`.mp4`, `.webm`, `.mov`, `.gif`, `.png`, `.jpg`), chuẩn hóa tên file (bỏ dấu tiếng Việt, tách từ khóa) lưu vào `meme_sfx\media_index.json`.
2. **Quy tắc khớp & tự động đề xuất Meme / SFX**:
   * **Ưu tiên 1 (Thẻ chỉ định trong kịch bản)**: Tìm chính xác file khớp từ khóa trong thẻ `[meme: ...]` và `[sfx: ...]` của `script_review_3rd.txt`.
   * **Ưu tiên 2 (Tự động bổ sung theo sắc thái câu dẫn)**: Nếu người dùng không gắn thẻ thủ công ở các câu mang sắc thái mạnh (`[châm biếm]`, `[ngạc nhiên]`, `[hào hứng]`, `[kịch tính]`), tự động chọn 1 SFX phù hợp (ví dụ: tiếng *whoosh*, *boom*, *vine boom*, *cười*, *ting*) và chèn thêm `2–4` Meme hình ảnh/video ngắn (`1.2s–2.2s`) xuyên suốt video với giãn cách tối thiểu `8s–12s` giữa 2 meme để không gây rối mắt.
3. **Chuẩn hóa định dạng trước khi đưa lên Timeline**:
   * **SFX (`sfx_XXX_ready.wav`)**: Chuyển về `48kHz stereo`, chuẩn hóa mức âm lượng `-16 LUFS` (đủ nổi bật nhưng không lấn át giọng dẫn truyện `-14 LUFS`).
   * **Meme hình ảnh/video (`meme_XXX_ready.mp4`)**: Chuẩn hóa cùng `fps` với dự án, hiển thị dạng **PiP góc màn hình** (kích thước ~`30%–35%` khung hình kèm viền nổi bật) hoặc **Cutaway toàn màn hình ngắn** (`1.0s–1.8s`), đồng thời tắt âm thanh gốc của meme nếu trùng thời điểm đang có giọng dẫn truyện.

#### Bước 3.6 — Dựng Timeline Đa Track trên Concat MCP & Phụ Đề QC
1. Làm sạch timeline và import toàn bộ tài nguyên qua `concat_media_import`:
   * **Track T1 (Video chính)**: `video_clean_mute.mp4` đặt tại `0.0s`.
   * **Track T2 (Lớp Meme & Hiệu ứng thị giác)**: Các clip `meme_XXX_ready.mp4` và overlay chữ/nhãn từ khóa (`hyperframes-motion` / `dynamic-visual-enhancer`).
   * **Track T3 (Âm thanh cảnh quan gốc)**: `ambient_trimmed.wav` đặt tại `0.0s` (volume `0.75`–`0.85`, tự động ducking mượt xuống `0.35` trong các khoảng có giọng dẫn truyện).
   * **Track T4 (Giọng dẫn truyện ngôi thứ 3)**: Các clip `voice_XXX.wav` đặt chính xác tại `place_i` (volume `1.0`).
   * **Track T5 (Hiệu ứng âm thanh SFX)**: Các clip `sfx_XXX_ready.wav` từ `main-ntt-edit/sound-effects` đặt đúng điểm nhấn câu dẫn (volume `0.85`–`0.95`).
2. **Kiểm tra Peak Mix Audio**: Chạy `schedule_and_mix.py` xác nhận tổng biên độ đỉnh của `T3 + T4 + T5` luôn **$< -0.5\text{ dBFS}$** (không clipping).
3. **Tạo & Kiểm chuẩn Phụ Đề (`subtitle-craft`)**:
   * Tạo `<PROJECT_DIR>\temp_assets\subtitles\vi_subtitles.srt` bám sát mốc `place_i` và `duration_i` của giọng dẫn truyện (đã lọc sạch mọi thẻ `[...]`).
   * Chia cue ngắn gọn ($\text{CPL} \le 42\text{ ký tự/dòng}$, $\text{CPS} \le 17\text{ ký tự/giây}$, thời lượng tối thiểu `1.0s`).
   * Chạy vòng lặp QC bằng `subtitle_engine.py` đến khi đạt `0 lỗi`:
     ```powershell
     $env:PYTHONIOENCODING = "utf-8"
     & "C:\Conda\envs\NttDzEditVideo\python.exe" "..\main-ntt-edit\modules\subtitle-craft\scripts\subtitle_engine.py" qc "<PROJECT_DIR>\temp_assets\subtitles\vi_subtitles.srt" --mode 16:9 --fps <FPS_DU_AN>
     ```
   * Nạp phụ đề đạt chuẩn lên **Track T6 (trên cùng)** bằng `concat_captions_add`.

#### Bước 3.7 — Nghiệm thu & Lưu dự án (`concat_project_save`)
1. Rà soát toàn bộ 6 track trên timeline qua `concat_timeline_read`: đảm bảo không có clip chồng lấn trên cùng track, phụ đề nằm trên lớp video và meme, không có file tạm nào nằm ngoài `<PROJECT_DIR>\temp_assets\`.
2. Gọi **`concat_project_save(path="<PROJECT_DIR>")`**.
3. Báo cáo tóm tắt kết quả cho người dùng (thời lượng trước và sau khi cắt gọn tránh bản quyền, số câu dẫn truyện ngôi thứ 3, danh sách Meme & SFX đã nạp từ `main-ntt-edit`, trạng thái xóa watermark/sub và kết quả QC phụ đề) và **mời người dùng kiểm tra trực tiếp trên cửa sổ Concat** trước khi xuất bản.

---

## 4. Checklist Xác Nhận Trước Khi Hoàn Tất

- [ ] **Không có bất kỳ file nào được ghi lên ổ `C:`** (toàn bộ nằm trong `<PROJECT_DIR>\temp_assets\`).
- [ ] Giai đoạn 2 đã xuất đầy đủ cả 2 file (`script_original.txt` và `script_review_3rd.txt` ngôi thứ 3) và **đã dừng lại báo cáo tên cả 2 file** cho người dùng kiểm tra trước khi dựng.
- [ ] Video đã được cắt gọn các đoạn tĩnh/ít thoại trong khi vẫn bảo toàn 100% các mốc cảnh có lời dẫn truyện chính, kèm biến đổi hình ảnh chống bản quyền.
- [ ] Đã nạp và chuẩn hóa đúng các tài nguyên từ `skills/main-ntt-edit/meme` và `skills/main-ntt-edit/sound-effects`.
- [ ] Âm thanh gốc đã tách bằng `Demucs`: lời thoại cũ bị loại bỏ 100%, âm thanh cảnh quan (`no_vocals`) được cắt khớp đồng bộ với video và không clipping khi mix cùng giọng dẫn + SFX.
- [ ] Watermark/logo và phụ đề cứng đã được xóa sạch bằng VSR và kiểm chứng bằng OpenCV.
- [ ] Phụ đề tiếng Việt đạt chuẩn `subtitle-craft` QC (`0 lỗi`) trên track cao nhất và đã gọi `concat_project_save` (chưa tự ý export).

--- 

## 5. Cuối cùng
- Đề xuất tên và mô tả hèm hashtag nên đặt khi đăng video đó lên các mạng xã hội (YouTube, TikTok, Facebook, Instagram...) để tối ưu SEO và tăng lượt tiếp cận.