---
name: concat-native-fx
description: "Cẩm nang và bộ công cụ điều khiển hiệu ứng hình ảnh, chuyển cảnh, chỉnh màu điện ảnh, keyframe chuyển động và âm thanh gốc (Native GPU Shaders) tích hợp sẵn trong Concat Video Editor qua Concat MCP hoặc trực tiếp qua concat.json: 22 chuyển cảnh (Transitions), 28 hiệu ứng hình ảnh (Video Effects), 57 bộ lọc màu (Filters/LUTs), 25 bộ lọc âm thanh (Audio Filters), Keyframing camera ảo (Punch-in, Ramp Zoom, Shake) và công cụ AI (Voice Isolation, Stabilize, Cutout, Chroma Key)."
---

# Cẩm Nang Hiệu Ứng & Chuyển Cảnh Native Concat (`concat-native-fx`)

Skill này là tài liệu kỹ thuật và hướng dẫn tác vụ toàn diện để **áp dụng trực tiếp kho hiệu ứng, chuyển cảnh, chỉnh màu và âm thanh gốc có sẵn trong phần mềm Concat** thông qua Concat MCP (hoặc chỉnh sửa nhanh file dự án `concat.json`).

> **Tại sao nên ưu tiên Concat Native FX thay vì render FFmpeg bên ngoài?**
> - **Thời gian thực (Real-time):** Chạy trực tiếp bằng GPU Shaders trên viewport của Concat, không tốn thời gian render file tạm.
> - **Tiết kiệm tài nguyên:** Không chiếm dụng 6GB VRAM của card RTX 3060 (để dành VRAM cho AI VieNeu-TTS, WhisperX).
> - **Khả năng biên tập mở:** Người dùng có thể kéo giãn độ dài chuyển cảnh hoặc tinh chỉnh thông số hiệu ứng trực tiếp trên giao diện Concat sau khi AI hoàn tất tác vụ.

---

## 1. Phương Thức Điều Khiển (MCP vs File JSON)

Có 2 phương thức chính để áp dụng hiệu ứng và chuyển cảnh:

### Phương Thức A: Thông qua Concat MCP (Ưu tiên khi Concat GUI đang mở)
- **Tạo chuyển cảnh giữa 2 clip:**
  1. *Cách 1 (Gắn vào đầu clip nhận):* Dùng `clip_update(path, clipId, patch={"transitionIn": {"id": "concat.<tên_chuyen_canh>", "duration": 1.0}})`
  2. *Cách 2 (Đặt layer chuyển cảnh độc lập trên track):* Dùng `edit_apply` với lệnh `addTransitionClip`.
- **Thêm hiệu ứng / LUT màu lên toàn bộ video hoặc từng đoạn:**
  1. *Cho từng clip:* Dùng `clip_update(path, clipId, patch={"videoEffects": [{"id": "concat.<tên_effect>", "params": {...}}]})`
  2. *Cho một khoảng thời gian trên nhiều track (Adjustment Layer):* Dùng `effect_layer_add(path, start, duration, effectId="concat.<tên_effect>", name="...")`
- **Keyframing chuyển động máy quay ảo (Ken Burns, Zoom, Pan):**
  - Dùng `keyframe_set(path, clipId, property="scale"|"offsetX"|"offsetY"|"opacity", at=0.0..1.0, value=...)`

### Phương Thức B: Can thiệp trực tiếp file `concat.json` (Chỉnh sửa batch nhanh khi Concat đóng)
- Mở và đọc `<PROJECT_DIR>\concat.json`.
- Thêm đối tượng vào mảng `videoEffects`, `filters` hoặc `transitionIn` của từng clip trong danh sách `clips`.

---

## 2. Bảng Tra Cứu 22 Hiệu Ứng Chuyển Cảnh (Transitions)

Toàn bộ chuyển cảnh gốc của Concat (gọi bằng tiền tố `concat.<tên_chuyen_canh>`):

| Transition ID | Tên hiển thị | Tham số tùy chỉnh (`params`) & Mặc định | Tình huống sử dụng phù hợp |
| :--- | :--- | :--- | :--- |
| `concat.dissolve` | Dissolve | *Không tham số* | Chuyển cảnh mượt mà tiêu chuẩn, phù hợp mọi thể loại. |
| `concat.blur-dissolve` | Blur Dissolve | `strength: 60.0` (Độ mờ xoá nhòe) | Chuyển cảnh nhớ lại quá khứ, đổi bối cảnh không gian. |
| `concat.fade-black` | Fade to Black | *Không tham số* | Kết thúc phân đoạn, lắng đọng cảm xúc, kết video. |
| `concat.fade-white` | Fade to White | *Không tham số* | Cú sốc, bừng sáng, thức giấc, hồi tưởng chớp nhoáng. |
| `concat.whip-pan` | Whip Pan | `speed: 80.0` (Tốc độ quét nhanh) | Chuyển cảnh hành động nhanh, chuyển camera sang vị trí mới. |
| `concat.zoom-transition`| Zoom | `direction: 0.0` (0: Zoom In đẩy tới, 1: Zoom Out kéo lùi) | Nhấn mạnh chi tiết, chuyển sang phối cảnh mới. |
| `concat.zoom-blur-transition`| Zoom Blur | `strength: 70.0` (Cường độ vệt mờ hướng tâm) | Chuyển cảnh cao trào, giật mình hoặc chuyển cảnh cực nhanh. |
| `concat.glitch-transition` | Glitch | `amount: 70.0` (Mức độ nhiễu điện tử) | Kịch bản công nghệ, phim kinh dị, khoa học viễn tưởng, game. |
| `concat.glitch-warp` | Glitch Warp | `amount: 75.0` (Mức biến dạng sóng tín hiệu) | Chuyển cảnh gián đoạn tín hiệu, phân đoạn bí ẩn. |
| `concat.rgb-split-wipe` | RGB Split | `spread: 60.0` (Độ phân tách 3 kênh màu đỏ-xanh) | Video âm nhạc, hiện đại, phong cách cyberpunk. |
| `concat.film-burn` | Film Burn | `heat: 70.0` (Độ lóa nhiệt của vệt cháy phim) | Video hoài niệm, phóng sự tài liệu, phim nhựa điện ảnh. |
| `concat.light-leak-transition` | Light Leak | `warmth: 70.0` (Độ ấm của vệt rò rỉ ánh sáng) | Video vlog cảm xúc, ngoài trời, đám cưới, nắng chiều. |
| `concat.light-leak-flash` | Light Leak Flash | `strength: 80.0` (Cường độ chớp sáng) | Điểm rơi cao trào của nhịp nhạc hoặc bắt đầu phần intro. |
| `concat.slide` | Slide | `direction: 0.0` (Hướng trượt góc 0..360) | Video dạng trình chiếu, review sản phẩm, bảng tin. |
| `concat.push` | Push | `direction: 0.0` (Hướng đẩy khung hình) | Đẩy khung hình cũ sang bên nhường chỗ cho khung hình mới. |
| `concat.cube` | Cube | *Không tham số* | Chuyển cảnh 3D hộp xoay cổ điển sinh động. |
| `concat.spin` | Spin | `turns: 1.0` (Số vòng xoay) | Tạo cảm giác choáng ngợp, xoay chuyển tình thế nhanh. |
| `concat.swirl` | Swirl | `twist: 70.0` (Độ xoáy lốc xoáy) | Biến ảo, ma thuật, chuyển đổi sang giấc mơ. |
| `concat.linear-wipe` | Linear Wipe | `direction: 0.0`, `softness: 20.0` (Độ mềm viền) | Quét ngang/dọc hiện đại phong cách truyền hình. |
| `concat.shape-wipe` | Shape Wipe | `shape: 0.0`, `softness: 15.0` | Quét theo hình khối mỹ thuật. |
| `concat.clock-wipe` | Clock Wipe | *Không tham số* | Thể hiện thời gian trôi qua, kim đồng hồ quét 360 độ. |
| `concat.iris` | Iris | `softness: 15.0` (Độ nhòe mép vòng tròn) | Vòng tròn khép lại phong cách phim hoạt hình cổ điển. |

---

## 3. Bảng Tra Cứu 28 Hiệu Ứng Hình Ảnh (Video Effects)

Các hiệu ứng thị giác tác động lên điểm ảnh (gọi bằng `concat.<tên_effect>`):

| Effect ID | Thể loại | Tham số chính (`params`) | Tác dụng & Ứng dụng |
| :--- | :--- | :--- | :--- |
| `concat.beat-shake` | Rung giật (Shake) | `bpm: 120.0, amount: 50.0, length: 60.0, punch: 30.0, blur: 50.0` | **Rung giật theo nhịp nhạc** tự động, tạo năng lượng cho video âm nhạc/gaming. |
| `concat.impact` | Rung va đập (Shake) | `amount: 60.0, length: 0.45, punch: 40.0, direction: 0.0, blur: 60.0` | **Rung chấn va chạm** dứt khoát khi có tiếng nổ, meme rơi, cú đấm, twist bất ngờ. |
| `concat.shake` | Rung tự do (Shake) | `style: 0.0, amount: 50.0, speed: 50.0, rotation: 40.0, blur: 40.0` | Tạo cảm giác máy quay cầm tay chân thật (Handheld Camera) cho ảnh tĩnh/cảnh đứng yên. |
| `concat.prism-shake`| Rung tán sắc | `amount: 50.0, speed: 50.0, split: 60.0` | Rung kèm tách màu lăng kính, dùng cho trạng thái căng thẳng/chóng mặt. |
| `concat.chromatic-aberration` | Quang sai | `shift: 4.0` | Viền lệch màu điện ảnh, phong cách Retro / Game / Sci-fi. |
| `concat.chroma-key` | Tách phông xanh | `color: 0.0, strength: 100.0, spill: 100.0, balance: 50.0, clip_black: 10.0, clip_white: 85.0` | **Tách phông xanh trực tiếp trên Concat** cho Meme, nhân vật, B-roll không cần render trước! |
| `concat.luma-key` | Tách phông sáng | `threshold: 10.0, softness: 10.0, invert: 0.0` | Tách nền sáng/trắng hoặc nền tối nhanh chóng. |
| `concat.remove-black` | Tách nền đen | `threshold: 4.0, strength: 100.0` | Chèn các hiệu ứng khói, lửa, tia lửa nền đen vào mà không cần kênh Alpha. |
| `concat.bloom-pulse`| Phát sáng đập | `amount: 50.0, speed: 2.0` | Phát sáng phập phồng ma mị cho phân đoạn kỳ ảo hoặc công nghệ cao. |
| `concat.glow` | Phát sáng viền | `amount: 45.0` | Tỏa sáng mềm mại xung quanh vật thể sáng. |
| `concat.halation` | Hào quang phim | `threshold: 55.0, radius: 22.0, amount: 45.0, tint: 0.0` | Giả lập ánh đỏ viền bóng đèn như cuộn phim nhựa Kodak Vision. |
| `concat.corona` | Quầng sáng | `threshold: 60.0, radius: 18.0, amount: 55.0, cool: 70.0` | Vầng hào quang lạnh xung quanh nguồn sáng mạnh. |
| `concat.film-grain` | Hạt phim | `amount: 12.0` | Thêm chất nhiễu hạt điện ảnh 35mm, triệt tiêu cảm giác thô cứng của đồ họa kỹ thuật số. |
| `concat.motion-blur`| Vệt mờ chuyển động | `length: 18.0, angle: 0.0` | Thêm vệt mờ theo góc hướng, tăng độ mượt khi vật thể di chuyển nhanh. |
| `concat.zoom-blur` | Mờ hướng tâm | `amount: 25.0, x: 50.0, y: 50.0` | Tập trung thị giác người xem vào tâm điểm giữa màn hình. |
| `concat.gaussian-blur`| Làm mờ đều | `radius: 10.0` | Làm mờ hậu cảnh khi cần nổi bật tiêu đề hoặc chữ chạy phía trên. |
| `concat.pixelate` | Điểm ảnh lớn | `size: 16.0` | Hiệu ứng game 8-bit, kiểm duyệt thông tin nhạy cảm. |
| `concat.posterize` | Giảm mảng màu | `levels: 4.0` | Phong cách Pop-art, tranh in truyện tranh. |
| `concat.halftone` | In báo cổ điển | `size: 6.0` | Hiệu ứng chấm mực in báo phong cách truyện tranh Spider-Verse. |
| `concat.fisheye` | Ống kính mắt cá | `strength: 50.0` | Bo cong góc rộng cực đại phong cách camera trượt ván hoặc góc nhìn thú cưng. |
| `concat.vignette` | Tối góc khung hình | `strength: 50.0` | Làm tối nhẹ 4 góc để hướng ánh nhìn người xem vào trung tâm. |
| `concat.white-balance` | Cân bằng trắng | `temperature: 6500.0, tint: 0.0` | Sửa ám vàng/ám xanh của video quay thực tế. |
| `concat.curves` | Đường cong màu | `luma: 0.0, red: 0.0, green: 0.0, blue: 0.0` | Chỉnh tương phản từng kênh màu nâng cao. |
| `concat.color-wheels` | Vòng xoay màu | `lift: 0.0, gamma: 0.0, gain: 0.0` | Chỉnh tông tối (Shadows), tông giữa (Midtones) và tông sáng (Highlights). |

---

## 4. Bảng Tra Cứu Bộ Lọc Màu Điện Ảnh (57 Filters / LUTs)

Gắn nhanh qua `clip_update` hoặc `effect_layer_add` để đổi toàn bộ tông màu (mood) của cảnh:

| Thể loại | Filter ID tiêu biểu | Đặc điểm & Phong cách |
| :--- | :--- | :--- |
| **Cinematic (13)** | `concat.teal-orange`, `concat.cyberpunk`, `concat.noir`, `concat.night`, `concat.after-hours`, `concat.bleach-bypass`, `concat.cool-blue`, `concat.film`, `concat.indie`, `concat.moody`, `concat.sci-fi`, `concat.wet-street`, `concat.window-seat` | Phong cách phim chiếu rạp Hollywood: tương phản cao, tông xanh-cam kinh điển, tông phim đen trắng Noir huyền bí hoặc đêm neon cyberpunk. |
| **Film & Retro (10)** | `concat.vhs`, `concat.vintage`, `concat.super-8`, `concat.classic-chrome`, `concat.retro-70s`, `concat.instant-print`, `concat.bronze`, `concat.falling-dust`, `concat.mono`, `concat.point-and-shoot` | Giả lập băng từ VHS thập niên 80, phim nhựa Super 8mm, máy chụp lấy liền Polaroids. |
| **Everyday & Vlog (10)**| `concat.golden-hour`, `concat.fresh`, `concat.clean`, `concat.vivid`, `concat.soft-light`, `concat.cloudless-sky`, `concat.aquamarine`, `concat.linen`, `concat.walnut`, `concat.whitewash` | Tone màu trong trẻo, tự nhiên, rực rỡ, ánh nắng hoàng hôn ấm áp thích hợp cho vlog đời sống. |
| **Scenery & Mùa (4)** | `concat.autumn`, `concat.winter-cool`, `concat.tropical`, `concat.landscape-pop` | Tôn màu cây cối, lá vàng mùa thu, cái lạnh mùa đông hoặc màu xanh ngọc bãi biển. |
| **Portrait (Chân dung) (4)**| `concat.blush`, `concat.luminous`, `concat.natural`, `concat.rosy` | Làm mịn màng tông da người dẫn chuyện, tạo sắc hồng hào, tự nhiên. |
| **Stylised & Vibe (8)** | `concat.vaporwave`, `concat.city-lights`, `concat.mint-haze`, `concat.neon`, `concat.pink-fuzz`, `concat.retro-cartoon`, `concat.spooky`, `concat.dreamy` | Mơ màng, lãng đãng, bí hiểm hoặc siêu thực. |
| **Adjust Toàn Năng** | `concat.adjust` | Chỉnh tay tất cả thông số: `saturation`, `exposure`, `contrast`, `highlights`, `shadows`, `sharpen`, `vignette`, `fade`. |

---

## 5. Bảng Tra Cứu 25 Bộ Lọc Âm Thanh (Audio Filters)

Áp dụng cho track thoại hoặc track nhạc (`filters` trong `clip_update` hoặc `effect_layer_add` với `sound=True`):

| Thể loại | Filter ID | Tham số chính | Tác dụng |
| :--- | :--- | :--- | :--- |
| **Làm sạch (Clean)** | `concat.denoise` | `strength: 50.0` | Giảm tiếng ồn nền (quạt gió, tiếng rào rào). |
| | `concat.enhance-voice`| `amount: 60.0` | Tăng cường độ rõ ràng và dày dặn của giọng đọc. |
| | `concat.loudness` | `target: -23.0` | Chuẩn hóa âm lượng LUFS chống đoạn to đoạn nhỏ. |
| **Giọng nhân vật (Voice)**| `concat.telephone` | `drive: 3.0` | Giả lập giọng nói qua điện thoại. |
| | `concat.megaphone` | `drive: 5.0` | Giả lập giọng nói qua loa phóng thanh / loa cầm tay. |
| | `concat.radio` | `noise: 30.0` | Giọng nói đài phát thanh cổ điển hoặc bộ đàm quân đội. |
| | `concat.chipmunk` | `pitch: 7.0` | Nâng giọng cao như sóc chuột (hài hước / meme). |
| | `concat.deep` | `pitch: -3.0, body: 3.0` | Hạ trầm giọng nói tạo cảm giác nguy hiểm, thần bí. |
| | `concat.whisper` | `air: 5.0` | Giọng thì thầm đầy hơi thở. |
| | `concat.robot` | `depth: 5.0` | Giọng nói máy móc người máy AI. |
| **Không gian (Space)** | `concat.room`, `concat.hall`, `concat.cathedral`, `concat.stadium` | `size: 40.0..60.0` | Tạo độ vang dội theo kích thước căn phòng đến nhà thờ/sân vận động. |
| | `concat.echo` | `delay: 0.25, decay: 0.4` | Tiếng vọng lặp lại. |
| | `concat.underwater` | `depth: 5.0` | Âm thanh nghẹt như bị chìm dưới nước. |

---

## 6. Hướng Dẫn Code Mẫu Áp Dụng Thực Chiến Qua Concat MCP

### Kịch bản 1: Thêm Chuyển Cảnh Whip Pan Giữa 2 Phân Đoạn
```python
# Gọi lệnh clip_update để gắn chuyển cảnh vào điểm đầu của clip thứ 2
client.call_tool("clip_update", {
    "path": project_path,
    "clipId": "c12", # ID của clip tiếp theo
    "patch": {
        "transitionIn": {
            "id": "concat.whip-pan",
            "duration": 0.8,
            "params": {"speed": 85.0}
        }
    }
})
```

### Kịch bản 2: Tách Phông Xanh Cho Meme Trực Tiếp Trên Timeline
Không cần dùng ffmpeg hay rembg tách nền trước, chỉ cần import video meme phông xanh vào track trên cùng và áp dụng Chroma Key:
```python
client.call_tool("clip_update", {
    "path": project_path,
    "clipId": "c15", # Clip meme phông xanh
    "patch": {
        "videoEffects": [
            {
                "id": "concat.chroma-key",
                "params": {
                    "color": 0.0,       # 0.0 là màu xanh lá (Green)
                    "strength": 100.0,
                    "spill": 100.0,     # Khử phản quang xanh trên mép
                    "balance": 50.0
                }
            }
        ]
    }
})
```

### Kịch bản 3: Ken Burns Cho Ảnh Tĩnh Bằng Keyframe Native (Không Cần FFmpeg!)
Tạo hiệu ứng đẩy máy từ tốn từ 100% lên 115% trong suốt chiều dài ảnh tĩnh:
```python
# Điểm bắt đầu (at=0.0): Phóng to chuẩn 1.0
client.call_tool("keyframe_set", {
    "path": project_path,
    "clipId": "c20",
    "property": "scale",
    "at": 0.0,
    "value": 1.0,
    "ease": [0.0, 0.0, 1.0, 1.0]
})

# Điểm kết thúc (at=1.0): Phóng to 1.15x
client.call_tool("keyframe_set", {
    "path": project_path,
    "clipId": "c20",
    "property": "scale",
    "at": 1.0,
    "value": 1.15,
    "ease": [0.0, 0.0, 1.0, 1.0]
})
```

### Kịch bản 4: Phủ Tông Màu Điện Ảnh Teal-Orange Cho Cả Dự Án
Thêm một lớp hiệu ứng (Adjustment Layer) phủ lên mọi track bên dưới từ giây thứ 0 đến giây 60:
```python
client.call_tool("effect_layer_add", {
    "path": project_path,
    "start": 0.0,
    "duration": 60.0,
    "effectId": "concat.teal-orange",
    "name": "Look Điện Ảnh Mỹ"
})
```

### Kịch bản 5: Chống Rung Cho Đoạn Phim Cầm Tay (`clip_stabilize`)
```python
client.call_tool("clip_stabilize", {
    "path": project_path,
    "clipId": "c5",
    "smoothness": 0.75 # Độ mượt chống rung từ 0.0 đến 1.0
})
```

---

## 7. Quy Tắc Phối Hợp & Kiểm Tra An Toàn

1. **Sau khi thực hiện mọi thao tác áp dụng hiệu ứng/chuyển cảnh**, bắt buộc gọi `project_save(path=...)` để lưu xuống file dự án `concat.json`.
2. **Không lạm dụng quá nhiều hiệu ứng cùng lúc:** Một clip chỉ nên kết hợp tối đa 1 bộ lọc màu (Filter/LUT) + 1 hiệu ứng chuyển động/quang sai (Shake/Film Grain) để giữ độ sắc nét và chuyên nghiệp cho video.
3. **Khi cần kiểm tra danh mục hiệu ứng thực tế trên máy người dùng:** Gọi công cụ `effects_list(path=...)` để lấy danh sách thời gian thực cùng giá trị min/max của từng thông số.
