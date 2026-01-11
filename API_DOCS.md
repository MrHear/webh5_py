# OneSpace 博客系统接口文档 (API Documentation)

本文档定义了 OneSpace 博客系统前后端交互的标准 RESTful API 接口。

## 1. 基础说明

- **Base URL**: `/api/v1`
- **Content-Type**: `application/json`
- **时间格式**: ISO 8601 (YYYY-MM-DDTHH:mm:ss.sssZ)

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

### Comment (评论)

| 字段名 | 类型 | 说明 | 示例 |
| :--- | :--- | :--- | :--- |
| `id` | string | 评论唯一标识 (UUID) | `"c1"` |
| `postId` | string | 关联文章ID | `"p1"` |
| `content` | string | 评论内容 | `"写得很好！"` |
| `author` | string | 评论者昵称 | `"访客A"` |
| `isGuest` | boolean | 是否游客评论 | `true` |
| `likes` | number | 点赞数 | `5` |
| `isLiked` | boolean | 当前用户是否已点赞 | `false` |
| `createdAt` | string | 创建时间 | `"2026-01-11T12:30:00Z"` |
| `replyTo` | object | 被回复的评论信息 (可选) | `{ id, author, content }` |

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
    - `keyword`: string (搜索关键词，可选)

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
    "views": 1241
  }
}
```

---

### 3.3 创建新文章 (Auth)

发布一篇新的 Markdown 或富文本文章。

- **URL**: `/posts`
- **Method**: `POST`
- **Headers**: `Authorization: Bearer <token>`
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

### 3.4 更新文章 (Auth)

更新已有文章。

- **URL**: `/posts/{id}`
- **Method**: `PUT`
- **Headers**: `Authorization: Bearer <token>`
- **Request Body**: 同创建文章 (字段均为可选)

**响应示例 (200 OK):**

```json
{
  "code": 200,
  "message": "文章更新成功",
  "data": {
    "id": "1",
    "title": "更新后的标题",
    "summary": "...",
    "content": "...",
    "type": "markdown",
    "tags": ["技术"],
    "views": 100,
    "createdAt": "2026-01-10T12:00:00Z"
  }
}
```

---

### 3.5 删除文章 (Auth)

删除文章（软删除）。

- **URL**: `/posts/{id}`
- **Method**: `DELETE`
- **Headers**: `Authorization: Bearer <token>`

**响应示例 (200 OK):**

```json
{
  "code": 200,
  "message": "文章删除成功",
  "data": null
}
```

---

## 4. 评论 (Comments)

### 4.1 获取文章评论

获取指定文章的评论列表。

- **URL**: `/comments`
- **Method**: `GET`
- **Query Parameters**:
    - `postId`: string (文章ID，必填)
    - `sort`: string (排序方式: `time` | `likes`，默认 `time`)

**响应示例 (200 OK):**

```json
{
  "code": 200,
  "message": "success",
  "data": [
    {
      "id": "c1",
      "postId": "p1",
      "content": "评论内容",
      "author": "访客A",
      "createdAt": "2026-01-11T12:30:00Z",
      "isGuest": true,
      "likes": 5,
      "isLiked": false,
      "replyTo": {
        "id": "c0",
        "author": "访客B",
        "content": "原评论内容..."
      }
    }
  ]
}
```

---

### 4.2 发表评论

发表新评论或回复评论。

- **URL**: `/comments`
- **Method**: `POST`
- **Request Body**:

| 字段名 | 类型 | 必填 | 说明 |
| :--- | :--- | :--- | :--- |
| `postId` | string | 是 | 文章ID |
| `content` | string | 是 | 评论内容 (最多1000字) |
| `author` | string | 否 | 昵称 (默认"匿名访客") |
| `replyToId` | string | 否 | 被回复的评论ID |

**请求示例:**

```json
{
  "postId": "文章ID",
  "content": "评论内容",
  "author": "昵称",
  "replyToId": "被回复的评论ID"
}
```

**响应示例 (201 Created):**

```json
{
  "code": 201,
  "message": "评论发表成功",
  "data": {
    "id": "new_id",
    "postId": "p1",
    "content": "评论内容",
    "author": "昵称",
    "createdAt": "2026-01-11T12:30:00Z",
    "isGuest": true,
    "likes": 0,
    "isLiked": false,
    "replyTo": null
  }
}
```

---

### 4.3 点赞评论

点赞或取消点赞评论（基于IP判断）。

- **URL**: `/comments/{id}/like`
- **Method**: `POST`
- **Request Body**: `{}` (空)

**响应示例 (200 OK):**

```json
{
  "code": 200,
  "message": "操作成功",
  "data": {
    "isLiked": true,
    "likes": 6
  }
}
```

---

## 5. 系统 & 文件

### 5.1 登录

管理员登录获取Token。

- **URL**: `/auth/login`
- **Method**: `POST`
- **Request Body**:

```json
{
  "username": "admin",
  "password": "password"
}
```

**响应示例 (200 OK):**

```json
{
  "code": 200,
  "message": "登录成功",
  "data": {
    "access_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
    "token_type": "bearer",
    "expires_in": 86400
  }
}
```

---

### 5.2 文件上传 (Auth)

用于编辑器中上传图片。

- **URL**: `/upload`
- **Method**: `POST`
- **Headers**: `Authorization: Bearer <token>`
- **Content-Type**: `multipart/form-data`
- **Request Body**: `file` (Binary)

**响应示例 (200 OK):**

```json
{
  "code": 200,
  "message": "上传成功",
  "data": {
    "url": "https://api.onespace.com/uploads/image-123.jpg",
    "filename": "image.png"
  }
}
```
