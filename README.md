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
- ✅ Quick Evaluate: Đánh giá nhanh CV mà không cần JD
- ✅ Hỗ trợ nhiều AI Provider: HuggingFace, Gemini, ChatGPT, DeepSeek
- ✅ Thêm tiêu chí đánh giá tùy chỉnh cho từng JD
- ✅ Xem lịch sử đánh giá
- ✅ Xuất báo cáo chi tiết

## Cài đặt

### Yêu cầu

- [Docker](https://docs.docker.com/get-docker/)
  - **macOS / Windows**: Cài đặt **Docker Desktop** (Đã bao gồm Docker Engine & Compose)
  - **Linux**: Cài đặt **Docker Engine** + **Docker Compose Plugin**



### 🍎 Chạy nhanh (macOS)

Bạn có thể khởi động ứng dụng dễ dàng bằng cách double-click vào **`matcher/Matcher.app`**.
*(Lần đầu chạy có thể cần cấp quyền hoặc chuột phải chọn Open)*

### Chạy bằng Terminal

```bash
docker-compose up -d --build
```

Lệnh này sẽ khởi động 4 container:
- `matcher-web`: Web server (FastAPI)
- `matcher-worker`: Worker xử lý AI background
- `matcher-redis`: Redis queue
- `matcher-postgres`: Database

#### Bước 3: Truy cập ứng dụng

Mở trình duyệt và truy cập: `http://localhost:8000`

#### Các lệnh hữu ích khác

- Xem log (để debug):
  ```bash
  docker-compose logs -f
  ```
- Dừng ứng dụng:
  ```bash
  docker-compose down
  ```
- Restart ứng dụng (khi code thay đổi):
  ```bash
  docker-compose restart
  ```

---

## 🔑 Hướng dẫn lấy API Key HuggingFace (Miễn phí)

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
4. Chọn Model: `deepseek-ai/DeepSeek-V3.2-Exp:novita` (khuyến nghị vì thông minh và miễn phí)
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
- ✅ Quick Evaluate: Instantly evaluate CV without a JD
- ✅ Multiple AI Provider support: HuggingFace, Gemini, ChatGPT, DeepSeek
- ✅ Add custom evaluation criteria for each JD
- ✅ View evaluation history
- ✅ Export detailed reports

## Installation

### Requirements

- [Docker](https://docs.docker.com/get-docker/)
  - **macOS / Windows**: Install **Docker Desktop** (Includes Docker Engine & Compose)
  - **Linux**: Install **Docker Engine** + **Docker Compose Plugin**



### 🍎 One-click Run (macOS)

You can easily start the application by double-clicking on **`matcher/Matcher.app`**.
*(On first run, you might need to right-click and select Open to grant permission)*

### Quick Start Guide 🚀

We recommend using Docker to run the application for maximum stability across all platforms (macOS, Linux, Windows w/ WSL2).

#### Step 1: Clone the project

```bash
git clone <repository-url>
cd ListCV/matcher
```

#### Step 2: Run with Docker Compose

Simply run the following command. It will automatically install dependencies, setup the database, and start the app:

```bash
docker-compose up -d --build
```

This starts 4 containers:
- `matcher-web`: Web server (FastAPI)
- `matcher-worker`: Background AI worker
- `matcher-redis`: Redis queue
- `matcher-postgres`: Database

#### Step 3: Access the application

Open your browser and navigate to: `http://localhost:8000`

#### Useful Commands

- View logs (for debugging):
  ```bash
  docker-compose logs -f
  ```
- Stop application:
  ```bash
  docker-compose down
  ```
- Restart application (after code changes):
  ```bash
  docker-compose restart
  ```

---

## 🔑 How to Get HuggingFace API Key (Free)

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
4. Select Model: `deepseek-ai/DeepSeek-V3.2-Exp:novita` (recommended for best free performance)
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
│   │   ├── history.html
│   ├── jd/                   # JD files storage
│   ├── cv/                   # CV files storage
│   └── reports/              # Generated reports
└── README.md
```

## 📄 License

MIT License

---

Made with ❤️ by DA Tools