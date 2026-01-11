# OneSpace 博客系统接口文档 (API Documentation)

本文档定义了 OneSpace 博客系统前后端交互的标准 RESTful API 接口。

## 1. 基础说明

- **Base URL**: `/api/v1` (建议)
- **Content-Type**: `application/json`
- **时间格式**: ISO 8601 (YYYY-MM-DD 或 YYYY-MM-DDTHH:mm:ss.sssZ)

---

## 2. 数据模型 (Models)

### Post (文章)

| 字段名 | 类型 | 说明 | 示例 |
| :--- | :--- | :--- | :--- |
| `id` | string | 文章唯一标识 (UUID) | `"550e8400-e29b-41d4-a716-446655440000"` |
| `title` | string | 文章标题 | `"Vue3 深度解析"` |
| `summary` | string | 文章摘要 (用于列表展示) | `"本文深入探讨 Vue3 的响应式原理..."` |
| `content` | string | 文章正文 (Markdown 或 HTML) | `"# 标题\n内容..."` |
| `type` | string | 文章类型 | `"markdown"` 或 `"richtext"` |
| `tags` | string[] | 标签列表 | `["技术", "前端"]` |
| `views` | number | 阅读量 | `1024` |
| `createdAt` | string | 创建时间 | `"2026-01-10"` |

---

## 3. 接口定义 (Endpoints)

### 3.1 获取文章列表

获取博客首页的时间轴文章列表。

- **URL**: `/posts`
- **Method**: `GET`
- **Query Parameters (可选)**:
    - `page`: number (页码，默认 1)
    - `limit`: number (每页数量，默认 10)
    - `type`: string (筛选类型: 'markdown' | 'richtext')

**响应示例 (200 OK):**

```json
{
  "code": 200,
  "message": "success",
  "data": {
    "total": 100,
    "page": 1,
    "list": [
      {
        "id": "1",
        "title": "神经网络与赛博植入体技术解析",
        "summary": "探索2077年生物神经元与硅基芯片之间的接口技术发展...",
        "type": "markdown",
        "tags": ["技术", "赛博义体"],
        "createdAt": "2077-09-12",
        "views": 1240
      }
      // ... 注意：列表中通常不返回 content 以减少流量
    ]
  }
}
```

---

### 3.2 获取文章详情

根据 ID 获取单篇文章的完整内容。

- **URL**: `/posts/{id}`
- **Method**: `GET`
- **Path Parameters**:
    - `id`: string (文章 ID)

**响应示例 (200 OK):**

```json
{
  "code": 200,
  "message": "success",
  "data": {
    "id": "1",
    "title": "神经网络与赛博植入体技术解析",
    "summary": "探索2077年生物神经元与硅基芯片之间的接口技术发展...",
    "content": "# 神经网络与赛博植入体技术解析\n\n**人类**与**机器**的界限日益模糊...",
    "type": "markdown",
    "tags": ["技术", "赛博义体"],
    "createdAt": "2077-09-12",
    "views": 1241 // 后端可在获取详情时自动增加阅读量
  }
}
```

---

### 3.3 创建新文章

发布一篇新的 Markdown 或富文本文章。

- **URL**: `/posts`
- **Method**: `POST`
- **Request Body**:

| 字段名 | 类型 | 必填 | 说明 |
| :--- | :--- | :--- | :--- |
| `title` | string | 是 | 标题 |
| `content` | string | 是 | 正文内容 |
| `summary` | string | 是 | 自动截取的摘要 |
| `type` | string | 是 | `'markdown'` 或 `'richtext'` |
| `tags` | string[] | 否 | 标签列表 |

**请求示例:**

```json
{
  "title": "新的灵感",
  "content": "<p>今天天气不错...</p>",
  "summary": "今天天气不错...",
  "type": "richtext",
  "tags": ["随笔"]
}
```

**响应示例 (201 Created):**

```json
{
  "code": 201,
  "message": "文章发布成功",
  "data": {
    "id": "new-uuid-1234",
    "createdAt": "2026-01-10"
  }
}
```

---

### 3.4 (预留) 图片上传

用于编辑器中上传图片。

- **URL**: `/upload`
- **Method**: `POST`
- **Request Body**: `FormData` (file)

**响应示例:**

```json
{
  "code": 200,
  "data": {
    "url": "https://api.onespace.com/uploads/image-123.jpg"
  }
}
```
