# Matcher

> 🇻🇳 [Tiếng Việt](#tiếng-việt) | 🇬🇧 [English](#english)

---

# Tiếng Việt

## Giới thiệu

**Matcher** là ứng dụng AI giúp đánh giá và so sánh CV ứng viên với mô tả công việc (Job Description). Ứng dụng sử dụng các mô hình AI tiên tiến để phân tích và cho điểm mức độ phù hợp.

## Tính năng

- ✅ Upload và quản lý CV (PDF, DOCX)
- ✅ Upload và quản lý JD (DOCX)
- ✅ Đánh giá tự động CV với JD bằng AI
- ✅ Hỗ trợ nhiều AI Provider: HuggingFace, Gemini, ChatGPT, DeepSeek
- ✅ Thêm tiêu chí đánh giá tùy chỉnh cho từng JD
- ✅ Xem lịch sử đánh giá
- ✅ Xuất báo cáo chi tiết

## Cài đặt

### Yêu cầu

- Python 3.9+
- Redis Server
- pip

### Cách 1: Chạy nhanh (Khuyến nghị) 🚀

#### macOS
1. Double-click vào **`Matcher.app`** trong thư mục `matcher/`
2. Ứng dụng sẽ tự động:
   - Khởi động Docker (nếu chưa chạy)
   - Khởi động Redis và các services
   - Mở trình duyệt tại `http://localhost:8000`

#### Windows
1. Double-click vào **`start-windows.bat`** trong thư mục `matcher/`
2. Ứng dụng sẽ tự động:
   - Cài đặt Docker (nếu chưa có)
   - Khởi động Docker và Redis
   - Mở trình duyệt tại `http://localhost:8000`

#### Dừng ứng dụng
- **macOS**: Đóng cửa sổ Terminal hoặc nhấn `Ctrl+C`
- **Windows**: Double-click vào `stop-windows.bat` hoặc đóng cửa sổ Command Prompt

---

### Cách 2: Chạy bằng CLI (Cho developer)

#### Bước 1: Clone dự án

```bash
git clone <repository-url>
cd ListCV
```

#### Bước 2: Cài đặt dependencies

```bash
cd matcher
pip install -r requirements.txt
```

#### Bước 3: Khởi động Redis

```bash
# macOS (với Homebrew)
brew services start redis

# Ubuntu/Debian
sudo systemctl start redis

# Windows (WSL)
sudo service redis-server start
```

#### Bước 4: Chạy ứng dụng

```bash
# Terminal 1: Chạy server
cd matcher
uvicorn app.main:app --reload --port 8000

# Terminal 2: Chạy worker xử lý queue
cd matcher
rq worker
```

#### Bước 5: Truy cập ứng dụng

Mở trình duyệt và truy cập: `http://localhost:8000`

---

## 🔑 Hướng dẫn lấy API Key HuggingFace

### Bước 1: Đăng ký tài khoản

1. Truy cập [https://huggingface.co/join](https://huggingface.co/join)
2. Điền thông tin và tạo tài khoản
3. Xác nhận email

### Bước 2: Tạo Access Token

1. Đăng nhập vào [https://huggingface.co](https://huggingface.co)
2. Click vào avatar góc phải → chọn **Settings**
3. Trong menu bên trái, chọn **Access Tokens**
4. Click nút **New token** (hoặc **Create new token**)
5. Đặt tên token (VD: `cv-matcher`)
6. Chọn Role: **Read** (đủ để sử dụng)
7. Click **Generate token**
8. **Sao chép token** (bắt đầu bằng `hf_...`) - Lưu ý: Token chỉ hiển thị 1 lần!

### Bước 3: Cấu hình trong ứng dụng

1. Mở ứng dụng tại `http://localhost:8000`
2. Click **AI Settings** ở sidebar
3. Chọn Provider: **HuggingFace**
4. Chọn Model: `deepseek-ai/DeepSeek-V3.2-Exp:novita` (khuyến nghị)
5. Dán API Key vào ô
6. Click **Test Connection** để kiểm tra
7. Click **Save** để lưu

---

# English

## Introduction

**Matcher** is an AI-powered application that evaluates and compares candidate CVs with Job Descriptions. The application uses advanced AI models to analyze and score the compatibility level.

## Features

- ✅ Upload and manage CVs (PDF, DOCX)
- ✅ Upload and manage JDs (DOCX)
- ✅ Automatic CV-JD evaluation using AI
- ✅ Multiple AI Provider support: HuggingFace, Gemini, ChatGPT, DeepSeek
- ✅ Add custom evaluation criteria for each JD
- ✅ View evaluation history
- ✅ Export detailed reports

## Installation

### Requirements

- Python 3.9+
- Redis Server
- pip

### Method 1: Quick Start (Recommended) 🚀

#### macOS
1. Double-click **`Matcher.app`** in the `matcher/` folder
2. The app will automatically:
   - Start Docker (if not running)
   - Start Redis and all services
   - Open your browser at `http://localhost:8000`

#### Windows
1. Double-click **`start-windows.bat`** in the `matcher/` folder
2. The app will automatically:
   - Install Docker (if not installed)
   - Start Docker and Redis
   - Open your browser at `http://localhost:8000`

#### Stop the application
- **macOS**: Close the Terminal window or press `Ctrl+C`
- **Windows**: Double-click `stop-windows.bat` or close the Command Prompt window

---

### Method 2: Run via CLI (For developers)

#### Step 1: Clone the project

```bash
git clone <repository-url>
cd ListCV
```

#### Step 2: Install dependencies

```bash
cd matcher
pip install -r requirements.txt
```

#### Step 3: Start Redis

```bash
# macOS (with Homebrew)
brew services start redis

# Ubuntu/Debian
sudo systemctl start redis

# Windows (WSL)
sudo service redis-server start
```

#### Step 4: Run the application

```bash
# Terminal 1: Run server
cd matcher
uvicorn app.main:app --reload --port 8000

# Terminal 2: Run queue worker
cd matcher
rq worker
```

#### Step 5: Access the application

Open your browser and navigate to: `http://localhost:8000`

---

## 🔑 How to Get HuggingFace API Key

### Step 1: Create an account

1. Go to [https://huggingface.co/join](https://huggingface.co/join)
2. Fill in your information and create an account
3. Verify your email

### Step 2: Create Access Token

1. Log in to [https://huggingface.co](https://huggingface.co)
2. Click on your avatar (top right) → select **Settings**
3. In the left menu, select **Access Tokens**
4. Click **New token** (or **Create new token**)
5. Name your token (e.g., `cv-matcher`)
6. Select Role: **Read** (sufficient for usage)
7. Click **Generate token**
8. **Copy the token** (starts with `hf_...`) - Note: Token is only shown once!

### Step 3: Configure in the application

1. Open the app at `http://localhost:8000`
2. Click **AI Settings** in the sidebar
3. Select Provider: **HuggingFace**
4. Select Model: `deepseek-ai/DeepSeek-V3.2-Exp:novita` (recommended)
5. Paste the API Key
6. Click **Test Connection** to verify
7. Click **Save** to save settings

---

## 📁 Project Structure

```
ListCV/
├── matcher/
│   ├── app/
│   │   ├── main.py           # FastAPI application
│   │   ├── worker.py         # Background job processor
│   │   ├── database.py       # Database models
│   │   └── ai_providers/     # AI provider implementations
│   ├── frontend/
│   │   ├── index.html        # Main comparison page
│   │   ├── jd-management.html
│   │   ├── cv-management.html
│   │   └── history.html
│   ├── jd/                   # JD files storage
│   ├── cv/                   # CV files storage
│   └── reports/              # Generated reports
└── README.md
```

## 📄 License

MIT License

---

Made with ❤️ by DA Tools