---
name: comfyui-image-gen
description: "Tạo ảnh AI thực tế, ghép nhiều ảnh, chỉnh sửa ảnh theo câu lệnh và mở rộng khung hình qua ComfyUI Local API (127.0.0.1:8188) với Qwen-Image 2.1 GGUF trên RTX 3060 6GB VRAM. Kích hoạt khi cần sinh ảnh minh họa B-roll, ghép nhân vật/sản phẩm vào bối cảnh mới, sửa chi tiết ảnh có sẵn, xóa vật thể/outpaint, hoặc khi Hyperframes và yt-dlp không đáp ứng được tư liệu hình ảnh."
---

# Tạo, Ghép & Chỉnh Sửa Ảnh AI Qua ComfyUI (Qwen-Image 2.1)

Skill này kết nối trực tiếp tới hệ thống **ComfyUI** cục bộ (`E:\EDIT\Photoshop\ComfyUI_Qwen`) qua HTTP REST API (`http://127.0.0.1:8188`) để tạo ảnh mới, ghép nhiều ảnh tham chiếu, chỉnh sửa ảnh theo câu lệnh và mở rộng khung hình phục vụ biên tập video trên Concat MCP.

---

## 1. Quy Tắc Cô Lập File & Thư Mục Lưu Trữ (Bắt Buộc)

* **Thư mục dự án Concat (`<PROJECT_DIR>`)**: Toàn bộ file cấu hình JSON (`comfy_jobs.json`, `graph.json`) và ảnh kết quả (`.png`) **bắt buộc** lưu tập trung tại:
  `<PROJECT_DIR>\temp_assets\comfyui\batch_XX\` (tự động tăng số thứ tự `batch_01`, `batch_02`... để tránh ghi đè asset cũ).
* **Tuyệt đối không ghi file vào thư mục cài đặt Skill** (`skills/main-ntt-edit/modules/comfyui-image-gen/`).
* **Dọn dẹp gọn gàng**: Nhờ gom chung toàn bộ vào `<PROJECT_DIR>\temp_assets\comfyui\`, khi hoàn tất dự án hoặc không còn cần tư liệu AI, chỉ cần xóa duy nhất thư mục `<PROJECT_DIR>\temp_assets\comfyui\` là sạch toàn bộ file tạm lẫn ảnh đã sinh.

---

## 2. Cấu Hình Hệ Thống & File Khởi Chạy Chuẩn

* **Script khởi chạy backend (Ưu tiên 1):** `E:\EDIT\Photoshop\run_comfyui.bat`
* **Thư mục gốc ComfyUI:** `E:\EDIT\Photoshop\ComfyUI_Qwen`
* **Môi trường Conda chuyên biệt:** `comfyui` (`C:\Conda\envs\comfyui\python.exe`)
* **Thư mục cache HuggingFace:** `E:\EDIT\Photoshop\cache\huggingface`
* **Cổng API nội bộ:** `http://127.0.0.1:8188`
* **Cờ tối ưu phần cứng (RTX 3060 6GB VRAM / 32GB RAM):** `--lowvram --cuda-malloc --reserve-vram 0.5 --listen 127.0.0.1 --port 8188`
* **Danh mục Model & Custom Nodes thực tế trên máy:** Xem chi tiết tại `references/node-and-model.txt`.

> **Cơ chế tự động bật server:** Script điều khiển `scripts/comfyui_bridge.py` tự kiểm tra `http://127.0.0.1:8188`. Nếu server chưa chạy, script tự động kích hoạt `E:\EDIT\Photoshop\run_comfyui.bat` ở chế độ nền (xử lý luồng `< nul` để vượt qua lệnh `pause` ở cuối file `.bat` mà không bị treo).

---

## 3. Nguyên Tắc Sáng Tạo & Chọn Phương Án Thực Thi

`qwen-image-2.1-UC-Q4_K_M.gguf` kết hợp với bộ mã hóa đa phương thức `qwen3vl_8b_int8_convrot.safetensors` và `qwen_image_2.1_vae_bf16.safetensors` hỗ trợ mạnh cả sinh ảnh từ văn bản lẫn hiểu và biến đổi hình ảnh đầu vào. Chọn đúng chế độ theo bài toán dựng video:

1. **Chế độ 1 - Sinh ảnh mới từ mô tả (`--mode t2i`):**
   * Dùng khi cần cảnh quay B-roll thực tế, bối cảnh điện ảnh, chân dung hoặc minh họa ý tưởng chưa có ảnh gốc.
   * Viết prompt tiếng Anh giàu chi tiết nhiếp ảnh: *Chủ thể + Hành động/Bố cục + Bối cảnh + Ánh sáng + Góc máy/Ống kính*.

2. **Chế độ 2 - Ghép ảnh & Chỉnh sửa theo câu lệnh (`--mode edit`):**
   * Dùng khi có sẵn 1 hoặc nhiều ảnh gốc (`--input-images img1.png img2.png ...`) và cần: ghép nhân vật/sản phẩm vào bối cảnh mới, giữ đồng nhất ngoại hình nhân vật qua nhiều phân cảnh, thay đổi trang phục, đổi ánh sáng ngày/đêm, hoặc biến đổi phong cách.
   * Script tự động upload các ảnh đầu vào lên ComfyUI, chuẩn hóa kích thước an toàn cho 6GB VRAM (`ImageScaleToTotalPixels` ~ 1.0 MP) và nối vào node điều kiện đa phương thức của Qwen-Image (`TextEncodeQwenImageEditPlus` / `TextEncodeQwenImageEdit` + `ReferenceLatent`).

3. **Chế độ 3 - Đồ thị Node tự do (`--graph-json`):**
   * Dùng khi cần kết hợp các custom nodes chuyên sâu có sẵn trên máy (xem `references/node-and-model.txt`):
     * Xóa vật thể / Inpaint / Outpaint mở rộng khung hình `9:16` sang `16:9` bằng `comfyui-inpaint-nodes` (`INPAINT_VAEEncodeInpaintConditioning`, `INPAINT_MaskedFill`, `INPAINT_ColorMatch`, `INPAINT_InpaintWithModel`).
     * Khóa dáng người hoặc bố cục bằng `comfyui_controlnet_aux` (`DWPreprocessor`, `DepthAnythingV2Preprocessor`, `CannyEdgePreprocessor`).
     * Giữ khuôn mặt hoặc truyền phong cách bằng `ComfyUI_IPAdapter_plus` (`IPAdapterFaceID`, `IPAdapterAdvanced`).
     * Tách nền / gán kênh Alpha bằng `ETN_ApplyMaskToImage`.
   * Trước khi dựng JSON tùy chỉnh, kiểm tra nhanh tên socket của node thực tế trên server bằng lệnh `--inspect-nodes <TenNode>`.

---

## 4. Hướng Dẫn Gọi Script `scripts/comfyui_bridge.py`

Mọi lệnh CLI gọi từ môi trường `NttDzEditVideo` (`conda run -n NttDzEditVideo python ...`). Khi truyền `--project-dir "<PROJECT_DIR>"`, script **tự động tạo thư mục `<PROJECT_DIR>\temp_assets\comfyui\batch_XX\`** và gom toàn bộ sản phẩm vào đó.

### 4.1. Sinh ảnh mới (Text-to-Image)

```cmd
conda run -n NttDzEditVideo python "skills/main-ntt-edit/modules/comfyui-image-gen/scripts/comfyui_bridge.py" ^
  --mode t2i ^
  --project-dir "<PROJECT_DIR>" ^
  --filename "scene_01_studio.png" ^
  --prompt "Cinematic medium shot of a Vietnamese filmmaker editing video in a dark modern studio, warm desk lamp and cool monitor glow, 35mm lens, shallow depth of field, photorealistic" ^
  --aspect 16:9
```
*(Kết quả tự động lưu tại `<PROJECT_DIR>\temp_assets\comfyui\batch_01\scene_01_studio.png`)*

### 4.2. Ghép nhiều ảnh hoặc sửa ảnh theo câu lệnh (Multi-Image Edit / Composite)

```cmd
conda run -n NttDzEditVideo python "skills/main-ntt-edit/modules/comfyui-image-gen/scripts/comfyui_bridge.py" ^
  --mode edit ^
  --project-dir "<PROJECT_DIR>" ^
  --filename "scene_02_composite.png" ^
  --input-images "<PROJECT_DIR>\assets\character.png" "<PROJECT_DIR>\assets\coffee_shop.png" ^
  --prompt "Place the person from image 1 sitting naturally at the wooden table inside the cozy coffee shop from image 2, warm morning sunlight through window, cinematic photography" ^
  --aspect 16:9
```

### 4.3. Chạy hàng loạt nhiều cảnh trong 1 phiên (`--batch-json`)

Lưu file JSON vào chính thư mục batch dự kiến (ví dụ `<PROJECT_DIR>\temp_assets\comfyui\batch_01\comfy_jobs.json`). Trong JSON chỉ cần ghi tên file ngắn ở trường `"output"`, khi chạy kèm `--project-dir "<PROJECT_DIR>"` toàn bộ ảnh sẽ tự gom chung vào 1 thư mục `batch_XX`:

```json
[
  {
    "mode": "t2i",
    "prompt": "Aerial wide shot of Saigon river at golden hour, dramatic clouds, photorealistic",
    "aspect": "16:9",
    "output": "broll_01.png"
  },
  {
    "mode": "edit",
    "input_images": ["broll_01.png"],
    "prompt": "Transform the scene into a vibrant cyberpunk night with neon reflections on the river water, keep the exact city skyline structure",
    "aspect": "16:9",
    "output": "broll_02_night.png"
  }
]
```

Chạy 1 lệnh duy nhất (nạp model 1 lần, sinh xong toàn bộ vào cùng 1 thư mục rồi tự động xả VRAM):

```cmd
conda run -n NttDzEditVideo python "skills/main-ntt-edit/modules/comfyui-image-gen/scripts/comfyui_bridge.py" ^
  --project-dir "<PROJECT_DIR>" ^
  --batch-json "<PROJECT_DIR>\temp_assets\comfyui\batch_01\comfy_jobs.json"
```

### 4.4. Chạy đồ thị Node tự thiết kế (`--graph-json`) & Tra cứu Node

* Tra cứu cấu trúc input/output thực tế của node trên ComfyUI:

```cmd
conda run -n NttDzEditVideo python "skills/main-ntt-edit/modules/comfyui-image-gen/scripts/comfyui_bridge.py" --inspect-nodes TextEncodeQwenImageEdit
```

* Thực thi đồ thị JSON tùy chỉnh:

```cmd
conda run -n NttDzEditVideo python "skills/main-ntt-edit/modules/comfyui-image-gen/scripts/comfyui_bridge.py" ^
  --project-dir "<PROJECT_DIR>" ^
  --graph-json "<PROJECT_DIR>\temp_assets\comfyui\batch_01\custom_inpaint_graph.json" ^
  --upload-images "<PROJECT_DIR>\temp_assets\raw_frame.png" ^
  --filename "clean_frame.png"
```

---

## 5. Đồng Bộ Timeline Concat MCP & An Toàn 6GB VRAM

1. **Khớp tỷ lệ khung hình dự án:** Đọc thông số dự án qua `timeline_read` trước khi sinh ảnh:
   * Dự án ngang `16:9` -> `--aspect 16:9` (`1280x720`).
   * Dự án dọc `9:16` -> `--aspect 9:16` (`720x1280`).
   * Dự án vuông `1:1` -> `--aspect 1:1` (`1024x1024`).
2. **Tạo chuyển động cho ảnh tĩnh:** Sau khi có file `.png` trong `<PROJECT_DIR>\temp_assets\comfyui\batch_XX\`, có thể chuyển qua sub-skill `dynamic-visual-enhancer` để thêm hiệu ứng Ken Burns (zoom/pan) khớp độ dài file thoại `.wav`, sau đó nạp vào Concat MCP (`media_import` -> `clip_add` -> `clip_trim` -> `project_save`).
3. **Kỷ luật VRAM (RTX 3060 6GB):**
   * Tuyệt đối không chạy ComfyUI song song với `vsr` hoặc `vieneu-tts-voiceover`.
   * Không đặt độ phân giải vượt quá ngưỡng ~1 Megapixel (`1280x720` / `1024x1024`).
   * Mặc định script luôn gọi `POST http://127.0.0.1:8188/free` (`{"unload_models": true, "free_memory": true}`) sau khi hoàn tất để trả lại toàn bộ VRAM cho các công cụ dựng phim tiếp theo.
