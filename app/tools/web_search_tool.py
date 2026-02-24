"""联网搜索工具"""

from langchain_core.tools import tool
from tavily import TavilyClient
from app.config import settings

tavily_client = TavilyClient(api_key=settings.tavily_api_key)


@tool
async def web_search(query: str, max_results: int = 5) -> str:
    """
    使用联网搜索获取最新信息。

    当用户询问实时信息、新闻、当前事件、天气、股价或知识库中未包含的内容时使用此工具。

    Args:
        query: 搜索查询语句
        max_results: 返回结果数量，默认5条

    Returns:
        搜索结果
    """
    results = tavily_client.search(query, search_depth="advanced",
                                   include_raw_content=False, 
                                   max_results=max_results, topic="general")
    return results
