# Hướng Dẫn Cài Đặt & Kết Nối Concat Video Editor MCP

*(Tài liệu dành cho người dùng thiết lập môi trường ban đầu)*

## 1. Bật Automation Server trên Concat
1. Khởi chạy ứng dụng Concat (`E:\EDIT\Concat\concat.exe`).
2. Nhấn biểu tượng bánh răng **Cài đặt** -> chọn thẻ **Tự động hóa** (Automation).
3. Gạt công tắc **"Script và ứng dụng"** sang trạng thái **Bật**.
4. Xác nhận trạng thái hiển thị: `Đang lắng nghe tại 127.0.0.1:7420` và sao chép chuỗi **Token**.

## 2. Cấu Hình MCP Client

Thêm khối cấu hình sau vào tệp thiết lập MCP của AI Agent bạn đang dùng:

```json
{
  "mcpServers": {
    "concat": {
      "command": "E:\\EDIT\\Concat\\concat.exe",
      "args": ["--mcp", "window"],
      "env": {
        "CONCAT_API_ADDRESS": "127.0.0.1:7420",
        "CONCAT_API_TOKEN": "<TOKEN_HIEN_THI_TRONG_CAI_DAT_CONCAT>",
        "CONCAT_MCP_ROOTS": "C:\\;D:\\;E:\\;F:\\"
      }
    }
  }
}
```

**Vị trí file cấu hình theo từng Agent:**
* **Antigravity**: `~/.gemini/config/mcp_config.json`
* **Claude Desktop**: `%APPDATA%\Claude\claude_desktop_config.json`
* **Claude Code (CLI)**: Chạy lệnh `claude mcp add concat -- E:\EDIT\Concat\concat.exe --mcp window`
* **Cursor / Windsurf**: Mục *MCP Servers* trong Settings hoặc `.cursor/mcp.json`
* **VS Code (Cline / Roo Code)**: `cline_mcp_settings.json`

## 3. Xử Lý Sự Cố Thường Gặp
* **Connection Refused / Port Closed**: Kiểm tra tiến trình `concat.exe` đã mở chưa, công tắc *"Script và ứng dụng"* đã bật chưa, hoặc chạy PowerShell: `Test-NetConnection -ComputerName 127.0.0.1 -Port 7420`.
* **Unauthorized / Sai Token**: Cập nhật lại `CONCAT_API_TOKEN` trùng khớp 100% với mã mới nhất trong Cài đặt Concat.
* **Access Denied khi import/export**: Kiểm tra ổ đĩa chứa file đã nằm trong `CONCAT_MCP_ROOTS` chưa.