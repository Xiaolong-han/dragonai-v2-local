"""RAG工具 - 知识库检索"""

from langchain_core.tools import tool
from app.services.knowledge_service import KnowledgeService


@tool
async def search_knowledge_base(query: str, k: int = 4) -> str:
    """
    从本地知识库中搜索相关文档。

    当用户询问项目文档、技术规范、API文档、内部资料等相关问题时使用此工具。

    Args:
        query: 搜索查询语句
        k: 返回文档数量，默认4条

    Returns:
        相关文档的格式化内容
    """
    service = KnowledgeService()
    documents = await service.search(query, k=k)

    if not documents:
        return "未找到相关文档。"

    formatted = []
    for i, doc in enumerate(documents, 1):
        source = doc.metadata.get("source", "未知")
        formatted.append(f"[文档 {i}] 来源: {source}\n{doc.page_content}\n")

    return "\n".join(formatted)
