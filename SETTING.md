# Hướng Dẫn Cài Đặt và Thiết Lập Môi Trường Conda Cho Bộ Công Cụ Video (NttDzEditVideo)

Tài liệu này ghi lại toàn bộ quy trình thiết lập môi trường Conda, cài đặt các thư viện AI và liên kết các công cụ CLI phục vụ cho việc chỉnh sửa và biên tập video tự động.

---

## 1. Yêu Cầu Hệ Thống & Lưu Ý Tiên Quyết

- **Hệ điều hành**: Windows 10 / Windows 11 (64-bit).
- **Phần cứng**: Khuyến nghị GPU NVIDIA (đã kiểm thử và tối ưu trên RTX 3060 Laptop GPU với CUDA 12.4).
- **Conda**: Miniconda hoặc Anaconda đã được cài đặt và thêm vào PATH.
- **Node.js & npm**: Phiên bản LTS (dùng cho Hyperframes).
- **eSpeak-NG**: Đã cài đặt vào hệ thống tại `C:\Program Files\eSpeak NG` (bắt buộc cho VieNeu-TTS để chuyển đổi văn bản sang âm vị chuẩn).
- **Python**: **Bắt buộc dùng Python 3.10** (để tương thích chuẩn giữa PyTorch CUDA, PaddleOCR, OnnxRuntime và VieNeu-TTS).

---

## 2. Tạo và Khởi Tạo Môi Trường Conda

Mở Terminal (PowerShell hoặc CMD) và thực hiện tuần tự:

```powershell
# 1. Tạo môi trường ảo với Python 3.10
conda create -n NttDzEditVideo python=3.10 -y

# 2. Kích hoạt môi trường
conda activate NttDzEditVideo
```

---

## 3. Cài Đặt PyTorch Hỗ Trợ CUDA 12.4

Để tận dụng tối đa GPU cho các tác vụ AI (khử watermark LaMa/STTN, tổng hợp giọng nói VieNeu-TTS):

```powershell
# Cài đặt PyTorch, Torchvision, Torchaudio phiên bản CUDA 12.4
pip install torch torchvision torchaudio --index-url https://download.pytorch.org/whl/cu124
```

Kiểm tra kích hoạt GPU:
```powershell
python -c "import torch; print('CUDA Available:', torch.cuda.is_available()); print('Device Name:', torch.cuda.get_device_name(0) if torch.cuda.is_available() else 'CPU')"
```

---

## 4. Tích Hợp FFmpeg & FFprobe Vào Môi Trường

Để mọi công cụ CLI nhận diện FFmpeg trực tiếp mà không phụ thuộc vào PATH toàn cục của Windows:

1. Tải bản build tĩnh FFmpeg (gồm `ffmpeg.exe` và `ffprobe.exe`).
2. Đặt cả hai file trực tiếp vào thư mục Scripts của môi trường Conda:
   ```text
   C:\Conda\envs\NttDzEditVideo\Scripts\ffmpeg.exe
   C:\Conda\envs\NttDzEditVideo\Scripts\ffprobe.exe
   ```
3. Sau khi kích hoạt môi trường (`conda activate NttDzEditVideo`), lệnh `ffmpeg` và `ffprobe` sẽ tự động sẵn sàng.

---

## 5. Cài Đặt Chi Tiết Từng Công Cụ

### 5.1. yt-dlp (Tải Video & Audio Đa Nền Tảng)
Cài đặt trực tiếp qua pip trong Conda:
```powershell
pip install yt-dlp
```
Tệp wrapper `F:\A_Tool\Tools\yt-dlp\yt-dlp.bat`:
```bat
@echo off
rem Wrapper goi yt-dlp trong moi truong conda NttDzEditVideo
"C:\Conda\envs\NttDzEditVideo\Scripts\yt-dlp.exe" %*
```

---

### 5.2. auto-editor (Tự Động Cắt Ghép & Lọc Khoảng Lặng)
Cài đặt qua pip:
```powershell
pip install auto-editor
```
Tệp wrapper `F:\A_Tool\Tools\auto-editor\auto-editor.bat`:
```bat
@echo off
rem Wrapper goi auto-editor trong moi truong conda NttDzEditVideo
"C:\Conda\envs\NttDzEditVideo\Scripts\auto-editor.exe" %*
```

---

### 5.3. video-subtitle-remover (Xóa Phụ Đề & Watermark Bằng AI)
1. Thư mục mã nguồn: `F:\A_Tool\Tools\video-subtitle-remover`
2. Cài đặt các thư viện phụ thuộc:
   ```powershell
   pip install opencv-python onnxruntime-gpu paddlepaddle-gpu paddleocr tqdm
   ```
3. **Lưu ý sửa lỗi tương thích Python 3.10**:
   - Trong file `backend/inpaint/sttn_auto_inpaint.py` dòng 245, thay thế cú pháp f-string lồng nháy đơn thành nháy kép để tránh lỗi cú pháp (`SyntaxError`).
4. Tệp wrapper `F:\A_Tool\Tools\video-subtitle-remover\vsr.bat`:
   ```bat
   @echo off
   rem Wrapper chay video-subtitle-remover CLI bang moi truong conda NttDzEditVideo
   "C:\Conda\envs\NttDzEditVideo\python.exe" "F:\A_Tool\Tools\video-subtitle-remover\backend\main.py" %*
   ```

---

### 5.4. VieNeu-TTS v3 Turbo 48kHz (Tổng Hợp Giọng Nói Tiếng Việt & Nhân Bản Giọng)
1. Thư mục mã nguồn: `F:\A_Tool\Tools\VieNeu-TTS`
2. Yêu cầu phụ thuộc hệ thống:
   - Cài đặt phần mềm eSpeak-NG vào `C:\Program Files\eSpeak NG`.
3. Cài đặt các thư viện Python:
   ```powershell
   pip install phonemizer soundfile torchaudio gradio pyyaml
   # Cài đặt gói vieneu nội bộ trong thư mục VieNeu-TTS
   pip install -e F:\A_Tool\Tools\VieNeu-TTS
   ```
4. Tệp wrapper CLI `F:\A_Tool\Tools\VieNeu-TTS\vieneu.bat`:
   ```bat
   @echo off
   setlocal
   rem Wrapper chay VieNeu-TTS CLI bang moi truong Conda NttDzEditVideo
   set "PATH=C:\Program Files\eSpeak NG;C:\Conda\envs\NttDzEditVideo\Scripts;%PATH%"
   "C:\Conda\envs\NttDzEditVideo\python.exe" "F:\A_Tool\Tools\VieNeu-TTS\cli.py" %*
   endlocal
   ```
5. Tệp khởi chạy WebUI `F:\A_Tool\Tools\VieNeu-TTS\run_webui.bat`:
   ```bat
   @echo off
   call "F:\A_Tool\Tools\VieNeu-TTS\vieneu.bat" --web
   ```

---

### 5.5. Hyperframes (Video Đồ Họa Chuyển Động Bằng Web Code)
1. Cài đặt CLI Hyperframes toàn cục bằng npm:
   ```powershell
   npm install -g hyperframes
   ```
2. Khởi tạo cấu hình và cài đặt Chrome Headless Shell:
   ```powershell
   hyperframes doctor
   ```
3. Tệp wrapper `F:\A_Tool\Tools\hyperframes\hyperframes.bat` (kết nối trực tiếp với FFmpeg của Conda):
   ```bat
   @echo off
   setlocal
   rem Wrapper chay Hyperframes CLI kem theo FFmpeg tu Conda NttDzEditVideo
   set "PATH=C:\Conda\envs\NttDzEditVideo\Scripts;%PATH%"
   call "C:\Users\ASUS\AppData\Roaming\npm\hyperframes.cmd" %*
   endlocal
   ```

---

## 6. Cấu Hình Kết Nối Concat Video Editor MCP

Concat Editor cung cấp MCP Server dạng Stdio để AI điều khiển trực tiếp timeline, cắt ghép, thêm text, hiệu ứng và xuất video.

File cấu hình MCP của Antigravity nằm tại:
`C:\Users\ASUS\.gemini\config\mcp_config.json`

Cập nhật nội dung cấu hình chính xác:
```json
{
  "mcpServers": {
    "concat": {
      "command": "E:\\EDIT\\Concat\\concat.exe",
      "args": ["--mcp", "window"],
      "env": {
        "CONCAT_API_ADDRESS": "127.0.0.1:7420",
        "CONCAT_API_TOKEN": "46f4ba0ee750efe37982c617fe759614",
        "CONCAT_MCP_ROOTS": "F:\\;D:\\;C:\\;E:\\"
      }
    }
  }
}
```

> **Giải thích cơ chế**:
> - `concat.exe --mcp window`: Khởi chạy cầu nối MCP Stdio ở chế độ `window`, tự động bắt sóng cửa sổ Concat Editor đang mở.
> - `CONCAT_API_ADDRESS`: `127.0.0.1:7420` là cổng IPC nội bộ của Concat Automation.
> - `CONCAT_API_TOKEN`: Mã token xác thực phiên làm việc.
> - `CONCAT_MCP_ROOTS`: Danh sách các ổ đĩa cho phép agent đọc ghi tư liệu video.
