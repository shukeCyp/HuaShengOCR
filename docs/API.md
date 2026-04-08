# API 文档

项目地址：`apps/paddleocr-webapp`

## 在线 Swagger 文档

启动服务后可访问：

- `/docs` Swagger UI
- `/redoc` ReDoc
- `/openapi.json` OpenAPI JSON

如果你当前通过 Cloudflare Tunnel 暴露，则可直接访问：

- `https://linking-income-explain-precisely.trycloudflare.com/docs`

---

## 1. 健康检查

### `GET /health`

返回示例：

```json
{
  "ok": true,
  "engine": "OnnxOCR"
}
```

---

## 2. 单图 OCR

### `POST /api/ocr`

上传一张图片，返回 OCR 文本与明细。

### 请求

- Content-Type: `multipart/form-data`
- 字段：`file`

### 返回示例

```json
{
  "success": true,
  "engine": "OnnxOCR",
  "filename": "demo.jpg",
  "saved_path": "xxx.jpg",
  "count": 2,
  "full_text": "第一行\n第二行",
  "items": [
    {
      "text": "第一行",
      "score": 0.9988,
      "box": [[0,0],[100,0],[100,20],[0,20]]
    }
  ]
}
```

---

## 3. 视频单帧检查（推荐给前端抽帧模式）

### `POST /api/video-review/frame-check`

适用于：
- 浏览器本地每秒抽一帧
- 每次把当前帧发给后端
- 后端 OCR + 检测是否包含链接

### 请求

- Content-Type: `multipart/form-data`
- 字段：
  - `file`: 当前帧图片
  - `second`: 当前帧对应的视频秒数

### 返回示例

```json
{
  "success": true,
  "passed": false,
  "second": 12,
  "text": "访问 www.example.com",
  "links": ["www.example.com"],
  "matched": true,
  "count": 1,
  "items": [
    {
      "text": "访问 www.example.com",
      "score": 0.9961,
      "box": [[0,0],[100,0],[100,20],[0,20]]
    }
  ]
}
```

### 判定规则

只要识别文本中包含任意链接，就返回：
- `matched: true`
- `passed: false`

当前匹配范围包括：
- `http://...`
- `https://...`
- `www....`
- 常见域名后缀，如 `.com .cn .net .org .io ...`

---

## 4. 后端整段视频审核任务（保留接口）

### `POST /api/video-review/tasks`

上传整段视频到后端，后端每秒抽帧并处理。

### 返回示例

```json
{
  "success": true,
  "task_id": "abc123",
  "stream_url": "/api/video-review/stream/abc123"
}
```

---

## 5. 查询后端视频审核任务结果

### `GET /api/video-review/result/{task_id}`

返回示例：

```json
{
  "success": true,
  "status": "passed",
  "done": true,
  "result": {
    "success": true,
    "passed": true,
    "reason": "未检测到链接",
    "filename": "demo.mp4",
    "frames_scanned": 24,
    "first_hit_second": null,
    "hit_frames": []
  }
}
```
