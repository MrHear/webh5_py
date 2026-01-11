"""
初始化测试数据脚本
用于开发和测试环境
"""
import asyncio
import uuid
from datetime import datetime, timedelta
import random

# 添加父目录到路径
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent))

from app.database import get_db_context
from app.models import Post


# 示例文章数据
SAMPLE_POSTS = [
    {
        "title": "探索赛博朋克2077的神经接口技术",
        "summary": "深入分析游戏中呈现的脑机接口技术及其现实科学基础...",
        "content": """# 神经接口技术深度解析

赛博朋克的世界里，**脑机接口**不再是科幻，而是日常。

## 技术原理

神经元与硅基芯片的桥梁是通过纳米级电极阵列实现的。这些电极能够：

1. 读取神经信号
2. 写入感官数据
3. 增强认知能力

```python
class NeuralInterface:
    def __init__(self, user_id):
        self.user_id = user_id
        self.bandwidth = "100Gbps"
    
    def connect(self):
        print("神经链接已建立...")
```

> "技术的边界，就是人类的边界。" —— 某赛博朋克哲学家

## 未来展望

随着技术发展，我们或许真的能看到类似的接口问世。
""",
        "type": "markdown",
        "tags": ["技术", "赛博朋克", "科幻"]
    },
    {
        "title": "Vue3 组合式API完全指南",
        "summary": "从零开始学习Vue3 Composition API，掌握现代前端开发技能...",
        "content": """# Vue3 组合式API完全指南

Vue3 的 Composition API 是前端开发的一大革新。

## 为什么使用 Composition API？

- 更好的代码组织
- 更容易复用逻辑
- 更好的 TypeScript 支持

## 基本用法

```javascript
import { ref, computed, onMounted } from 'vue'

export default {
  setup() {
    const count = ref(0)
    const double = computed(() => count.value * 2)
    
    onMounted(() => {
      console.log('组件已挂载')
    })
    
    return { count, double }
  }
}
```

## 总结

Composition API 让 Vue 开发更加灵活和强大。
""",
        "type": "markdown",
        "tags": ["前端", "Vue", "JavaScript"]
    },
    {
        "title": "我的2077年度总结",
        "summary": "回顾这一年的成长与收获，展望未来的无限可能...",
        "content": "<h1>2077年度总结</h1><p>这一年过得很快，学到了很多东西。</p><h2>技术成长</h2><ul><li>掌握了神经编程</li><li>完成了3个重要项目</li><li>开始写技术博客</li></ul><p><strong>感谢所有支持我的人！</strong></p>",
        "type": "richtext",
        "tags": ["随笔", "年度总结"]
    }
]


async def init_test_data():
    """初始化测试数据"""
    async with get_db_context() as db:
        for i, post_data in enumerate(SAMPLE_POSTS):
            post = Post(
                id=str(uuid.uuid4()),
                title=post_data["title"],
                summary=post_data["summary"],
                content=post_data["content"],
                type=post_data["type"],
                tags=post_data["tags"],
                views=random.randint(100, 2000),
                created_at=datetime.now() - timedelta(days=i * 7)
            )
            db.add(post)
        
        await db.commit()
        print(f"✓ 成功创建 {len(SAMPLE_POSTS)} 篇测试文章")


if __name__ == "__main__":
    print("初始化测试数据...")
    asyncio.run(init_test_data())
    print("完成!")
