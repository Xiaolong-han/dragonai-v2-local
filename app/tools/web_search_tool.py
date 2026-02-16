
from langchain_community.tools.tavily_search import TavilySearchResults
from langchain.tools import tool
from typing import List, Dict, Any
from app.config import settings


def get_tavily_search_tool():
    """获取Tavily搜索工具实例"""
    return TavilySearchResults(
        api_key=settings.tavily_api_key,
        max_results=5,
        search_depth="advanced"
    )


@tool
def web_search(query: str):
    """
    使用Tavily进行联网搜索，获取最新信息
    
    Args:
        query: 搜索查询字符串
        
    Returns:
        搜索结果列表，每个结果包含title、url、content等字段
    """
    search_tool = get_tavily_search_tool()
    results = search_tool.invoke({"query": query})
    return results

