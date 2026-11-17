---
name: subtitle-craft
description: Tạo, chỉnh sửa, ghép nối (concat) và kiểm định chất lượng phụ đề chuyên nghiệp (SRT/VTT/ASS) bám sát hình ảnh và giọng đọc, tối giản số chữ trên mỗi khung hình. Kích hoạt khi tạo phụ đề từ video/audio, ghép phụ đề cho pipeline nối nhiều clip (FFmpeg concat/chunked audio), chuyển transcript thô thành phụ đề hiển thị, biên tập phụ đề video ngang (16:9) hoặc dọc ngắn (9:16), hoặc kiểm tra lỗi CPL/CPS/tràn cảnh. Không kích hoạt khi người dùng chỉ yêu cầu xuất transcript văn bản thuần túy.
license: Internal use
---

# Subtitle Craft — Tạo, Ghép Nối & Kiểm Định Phụ Đề Chuẩn Agent

## Nguyên tắc cốt lõi & Ràng buộc vận hành

- **Phụ đề là lớp thông tin phụ trợ, không phải bản transcript nguyên văn.** Giữ số chữ tối thiểu trên mỗi khung hình để người xem không bị ngộp chữ và không che khuất hình ảnh.
- **Không ảo giác timecode:** Nếu đầu vào chỉ có văn bản thô (không có audio/video hoặc word-level timestamp), tuyệt đối không tự bịa timecode thực tế; chỉ chia cue theo chuẩn CPL và ước lượng thời lượng tối thiểu dựa trên CPS.
- **Chuẩn hóa mốc thời gian khi `concat`:** Trong pipeline ghép nhiều clip, luôn lấy **thời lượng stream thực tế từ `ffprobe`** làm mốc cộng dồn (offset), tuyệt đối không dùng mốc kết thúc của cue cuối clip trước để tránh lệch nhịp tích lũy (cumulative drift).

---

## Rẽ nhánh quy trình theo đầu vào

### Nhánh 1 — Video/Audio đơn lẻ (Single Media)
1. **Phân tích nhịp & hình ảnh:** Xác định nhịp đọc, cảm xúc, các **điểm cắt cảnh (shot cut)** và vùng hình ảnh nhạy cảm (mặt nhân vật, lower-third, chữ on-screen).
2. **Word-level alignment:** Trích xuất timestamp ở mức từ (Whisper, Soniox hoặc công cụ chuyên dụng). Sửa lỗi chính tả, tên riêng, số liệu trước khi chia cue.
3. **Segmentation (Chia cue):** Áp dụng quy tắc ngắt cụm ý nghĩa và thông số kỹ thuật vàng.
4. **Spotting (Canh nhịp):** Khớp word onset, cộng đuôi +0,2s (nếu không chạm cut), giữ khoảng nghỉ 2–4 frame.
5. **QC tự động:** Chạy `scripts/subtitle_engine.py qc` trước khi xuất bản.

### Nhánh 2 — Pipeline ghép nhiều clip / `concat` (FFmpeg Multi-Clip hoặc Chunked Audio)
1. **Xử lý độc lập từng mảnh:** Tạo và chia cue riêng cho từng clip/chunk theo Bước 1–4 của Nhánh 1. Nếu ghép transcript từ các chunk audio có vùng chồng lấn (overlap), khử trùng lặp từ ở điểm nối trước khi chia cue.
2. **Kẹp trần ranh giới clip (Boundary Clamping):** Với cue cuối cùng của mỗi clip, **cấm cộng đuôi +0,2s** nếu làm vượt quá thời lượng clip. Cue cuối bắt buộc kết thúc chậm nhất tại `clip_duration - 2_frames` để chữ không dính đè sang cảnh của clip tiếp theo.
3. **Ghép nối & Dịch chuyển offset:** Chạy `scripts/subtitle_engine.py concat` với thời lượng thực tế từng clip (từ `ffprobe`) để tự động kẹp trần ranh giới, cộng dồn offset, gộp header `.ass` (nếu có) và đánh lại số thứ tự cue `1, 2, 3...`.
4. **QC toàn cục:** Chạy `scripts/subtitle_engine.py qc` trên file sau khi ghép để kiểm tra các điểm tiếp giáp.

### Nhánh 3 — Chỉ có file phụ đề có sẵn (`.srt`, `.vtt`, `.ass`, `.ssa`) hoặc văn bản thô
- Bỏ qua bước trích xuất audio -> đi thẳng vào **Segmentation** -> **Spotting** (nếu đã có timecode) -> **QC tự động**.

---

## Thông số kỹ thuật "vàng"

| Thông số | Video ngang (16:9) | Video dọc (9:16) | Ghi chú |
| :--- | :---: | :---: | :--- |
| Ký tự tối đa/dòng (CPL) | **42** | **20** | Tính cả dấu cách |
| Số dòng tối đa/cue | **2** | **2** | Ưu tiên **1 dòng** nếu vừa CPL |
| Tốc độ đọc (CPS) | **15–17** ký tự/giây | **13–15** ký tự/giây | Nội dung trẻ em: giảm thêm ~2 CPS |
| Thời lượng tối thiểu/cue | **1,0 giây** | **0,6 giây** | Shorts giật nhịp nhanh có thể hạ còn 0,4s |
| Thời lượng tối đa/cue | **5–7 giây** | **5 giây** | Tránh chữ đeo bám hình ảnh |
| Ngưỡng từ mồ côi | **< 8 ký tự hoặc < 1,0s** | **< 8 ký tự hoặc < 0,6s** | Gộp vào cue liền kề nếu ngắn hơn |
| Khoảng trống giữa các cue | **2–4 frame** | **2–4 frame** | Tạo nhịp nghỉ cho mắt |
| Vùng an toàn | 20% dưới cùng, căn giữa | 25% dưới cùng, căn giữa | Tránh che mặt và lower-third |

---

## Quy tắc Segmentation, Spotting & Đồng bộ hình ảnh

### Quy tắc ngắt dòng (One-line-first)
- **Ưu tiên 1 dòng/cue** nếu cụm ý nghĩa nằm gọn trong CPL; chỉ xuống 2 dòng khi bắt buộc.
- **Được phép ngắt tại:** Dấu câu (`.`, `,`, `?`, `!`, `;`, `:`, `...`), ranh giới mệnh đề (sau *và, nhưng, vì, nếu, khi, để...*), hoặc sau cụm danh từ hoàn chỉnh.
- **Cấm ngắt giữa:** Mạo từ + danh từ (*"cái / hợp đồng"*), tính từ + danh từ (*"quan trọng / nhất"*), động từ + bổ ngữ ngắn (*"đi / về"*), tên riêng, con số và thuật ngữ ghép.
- **Tối giản khi vượt CPS:** Lược bỏ từ đệm/từ lặp vô nghĩa (*"thì, là, mà, ừm, kiểu như"*), **không paraphrase** làm sai lệch giọng văn gốc.

### Quy tắc canh nhịp & Tránh cắt cảnh
- **Bắt đầu cue:** Đúng thời điểm phát âm từ đầu tiên (word onset).
- **Kết thúc cue:** Muộn hơn từ cuối ~0,2s để mắt kịp chốt, **ngoại trừ** khi gặp điểm cắt cảnh hoặc hết clip.
- **Điểm cắt cảnh (Shot cut) & Ranh giới `concat`:** Một cue chỉ thuộc về một cảnh. Phải kết thúc trước cut ít nhất **2 frame** và bắt đầu sau cut ít nhất **2 frame**.

### Xử lý chống che khuất theo định dạng
- **`.srt` / `.vtt`:** Khi xuất hiện lower-third hoặc đồ họa ở cạnh dưới, rút gọn phụ đề xuống tối đa **1 dòng ngắn** (<= 35 ký tự với 16:9) hoặc ngắt kết thúc trước khi đồ họa xuất hiện.
- **`.ass` / `.ssa`:** Dùng thẻ `{\an8}` hoặc tăng `MarginV` để đẩy phụ đề lên vùng an toàn phía trên khi phần dưới bị chiếm dụng.

---

## Công cụ CLI tự động (`scripts/subtitle_engine.py`)

Luôn chạy script kiểm định trước khi bàn giao kết quả cho người dùng hoặc chuyển sang bước render FFmpeg:

```bash
# 1. Kiểm tra chất lượng file phụ đề (hỗ trợ .srt, .vtt, .ass, .ssa hoặc '-' qua stdin)
python scripts/subtitle_engine.py duong_dan.srt --mode 16:9 --fps 30

# 2. Kiểm tra kèm danh sách mốc cắt cảnh (giây hoặc HH:MM:SS.mmm)
python scripts/subtitle_engine.py duong_dan.srt --mode 9:16 --fps 30 --cuts 4.20,11.85,00:00:19.500

# 3. Ghép nhiều file phụ đề theo thời lượng clip thực tế (từ ffprobe) + tự động kẹp trần + QC
python scripts/subtitle_engine.py concat clip1.srt:12.500 clip2.srt:8.240 --fps 30 --mode 16:9 --run-qc --out final.srt
```

---

## Checklist QC bắt buộc trước khi bàn giao

- [ ] Đã chạy `scripts/subtitle_engine.py qc` và đạt **0 lỗi** về CPL, CPS, thời lượng tối thiểu/tối đa, từ mồ côi, overlap và khoảng nghỉ >= 2 frame.
- [ ] Không có cue nào bắc cầu qua điểm cắt cảnh hoặc tràn đuôi sang clip kế tiếp khi `concat`.
- [ ] Phụ đề không che mặt nhân vật, lower-third hoặc chữ on-screen.
- [ ] Đã rà soát chính tả, tên riêng, đơn vị đo lường và con số.

---

## Hệ thống Màu Sắc, Preset & Hiệu Ứng Động (`.ass` Theme Engine)

Khi người dùng yêu cầu phụ đề sinh động, có màu nhấn, phân biệt người nói hoặc hiệu ứng chuyển động, **không tự viết tay mã màu ASS** (dễ sai hệ màu đảo ngược `&HBBGGRR&`). Thay vào đó, Agent gắn **thẻ ngữ nghĩa nhẹ** vào văn bản và gọi lệnh `scripts/subtitle_engine.py style` để biên dịch sang `.ass` chuẩn xác 100%.

### 1. Cú pháp thẻ ngữ nghĩa trong văn bản cue

- **Nhấn mạnh từ khóa (`**từ khóa**` hoặc `==từ khóa==`):** Tự động đổi sang màu nhấn (`accent_color`) của preset và in đậm. Chỉ nhấn **1–2 từ khóa đắt giá/cue** để giữ nhịp thị giác.
  - *Ví dụ:* `Bí quyết giúp bạn **tăng gấp đôi** hiệu suất.`
- **Màu chỉ định trực tiếp (`[#RRGGBB:cụm từ]`):** Tô màu riêng cho một cụm từ cụ thể theo mã hex chuẩn RGB.
  - *Ví dụ:* `Cảnh báo [#EF4444:rủi ro thanh khoản] tăng cao.`
- **Phân màu theo người nói (`{S1}`, `{S2}`, `{S3}`, `{S4}`):** Đặt ở đầu cue để gán bảng màu riêng cho từng nhân vật (hoặc giữ nguyên tiền tố `[Tên nhân vật]:` và bật cờ `--auto-speaker`).
  - *Ví dụ:* `{S1} Bạn nghĩ sao về kế hoạch này?` / `{S2} Tôi hoàn toàn **đồng ý**!`
- **Né vùng che khuất (`{top}`):** Đặt ở đầu cue để tự động đẩy phụ đề lên vùng an toàn phía trên (`\an8`) khi gặp lower-third hoặc đồ họa ở cạnh dưới.

### 2. Bộ Preset phong cách dựng sẵn (`--preset`)

| Tên Preset | Thể loại video phù hợp | Đặc trưng thị giác | Hiệu ứng mặc định |
| :--- | :--- | :--- | :---: |
| `minimal-clean` | Vlog, Giáo dục, Phỏng vấn | Chữ trắng ngà thanh thoát, viền mảnh, nhấn vàng nắng | `fade` |
| `shorts-pop` | TikTok, Reels, YouTube Shorts | Chữ đậm lớn, viền đen dày, từ khóa vàng chanh nổi bật | `pop` |
| `boxed-modern` | Tin tức, Tài chính, Công nghệ | Nền hộp tối bán trong suốt (`BorderStyle=3`), nhấn xanh cyan | `fade` |
| `podcast-duo` | Podcast, Talkshow 2–4 người | Bảng màu phân tách rõ từng người nói (Trắng / Vàng / Ngọc / San hô) | `slide-up` |
| `cinematic` | Storytelling, Du lịch, Tài liệu | Giãn chữ rộng, bóng đổ mềm điện ảnh, nhấn vàng champagne | `blur-in` |
| `gaming-neon` | Gaming, Livestream, Review Tech | Viền tím điện tương phản cao, nhấn xanh neon | `pop` |
| `luxury-editorial` | Thời trang, Bất động sản, Brand | Nền hộp tối sang trọng, giãn chữ rộng, nhấn vàng kim | `fade` |
| `karaoke-pulse` | Shorts/Reels chạy chữ từng từ | Đổi màu và bật nhịp phóng nhẹ theo từng từ đang đọc | `karaoke` |

### 3. Danh sách hiệu ứng chuyển động (`--effect`)

- `none`: Hiển thị tĩnh (chỉ áp dụng màu sắc, font, viền/nền hộp và phân vai).
- `fade`: Mờ dần vào/ra mượt mà (`\fad`), tự động rút ngắn theo độ dài cue.
- `pop`: Bật nảy nhẹ (`86% -> 105% -> 100%`) tạo điểm nhấn nhịp nhanh cho video ngắn.
- `slide-up`: Trượt nhẹ từ dưới lên vị trí chuẩn kết hợp làm mờ.
- `blur-in`: Hiệu ứng lấy nét mềm mại kiểu điện ảnh.
- `karaoke`: Highlight đổi màu và bật nhịp lần lượt từng từ (hỗ trợ khớp chính xác word-level timestamps qua `--words-json` hoặc tự ước lượng theo độ dài từ).
- `typewriter`: Hiển thị lần lượt từng từ xuất hiện theo nhịp đọc.

### 4. Lệnh CLI tạo màu, hiệu ứng & ghép nối đồng bộ

```bash
# 1. Xem danh sách toàn bộ preset & hiệu ứng đang có
python scripts/subtitle_engine.py presets

# 2. Áp dụng preset cho video dọc 9:16 (Shorts/Reels) + kiểm tra QC tự động
python scripts/subtitle_engine.py style input.srt --preset shorts-pop --mode 9:16 --run-qc --out styled.ass

# 3. Tùy biến màu thương hiệu, font chữ, tự nhận diện người nói & né lower-third theo khung giờ
python scripts/subtitle_engine.py style podcast.srt --preset podcast-duo --effect slide-up \
  --primary-color "#FFFFFF" --accent-color "#00E5FF" --auto-speaker \
  --top-windows "5.0-11.5,42.0-48.0" --out podcast.ass

# 4. Ghép nối nhiều clip và xuất thẳng ra file .ass đã có màu & hiệu ứng
python scripts/subtitle_engine.py concat clip1.srt:12.500 clip2.srt:8.240 --fps 30 --mode 16:9 \
  --preset boxed-modern --run-qc --out final.ass

# 5. Burn-in phụ đề .ass vào video bằng FFmpeg
ffmpeg -i input.mp4 -vf "ass=final.ass" -c:a copy output.mp4
```