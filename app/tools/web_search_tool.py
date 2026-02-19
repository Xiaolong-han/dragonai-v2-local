"""联网搜索工具"""

from langchain_core.tools import tool
from langchain_community.tools.tavily_search import TavilySearchResults
from app.config import settings


@tool
async def web_search(query: str) -> str:
    """
    使用联网搜索获取最新信息。

    当用户询问实时信息、新闻、当前事件、天气、股价或知识库中未包含的内容时使用此工具。

    Args:
        query: 搜索查询语句

    Returns:
        搜索结果的格式化摘要
    """
    if not settings.tavily_api_key:
        return "错误：未配置Tavily API密钥，无法执行联网搜索。"

    search_tool = TavilySearchResults(
        api_key=settings.tavily_api_key,
        max_results=5,
        search_depth="advanced"
    )
    results = await search_tool.ainvoke({"query": query})
    return str(results)
