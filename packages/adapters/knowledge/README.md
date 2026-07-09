# RAG 知识库适配器 (content-factory-knowledge)

通过 HTTP 客户端调用 `workspace/knowledge/knowledge-base` 的 RAG API，对内部知识库进行语义检索。

## 前置依赖

启动知识库 API：

```bash
cd /Users/chenlei/workspace/knowledge/knowledge-base
source .venv/bin/activate
uvicorn api:app --host 127.0.0.1 --port 8002
```

## 环境变量

| 变量名 | 必需 | 说明 |
|---|---|---|
| `CF_KNOWLEDGE_URL` | 否 | 知识库 API 地址，默认 `http://127.0.0.1:8002` |

## 用法

```python
from content_factory_knowledge import KnowledgeSearchProvider

kb = KnowledgeSearchProvider()

# 语义检索（hybrid / mmr / vector / bm25）
result = await kb.search("什么是 Alpha 因子", domain="hybrid", limit=10)
for doc in result["results"]:
    print(doc["title"], doc["score"])

# RAG 检索 + LLM 回答
answer = await kb.query_with_answer("什么是 Alpha 因子")
print(answer["answer"])

# 服务健康
await kb.health()
```
