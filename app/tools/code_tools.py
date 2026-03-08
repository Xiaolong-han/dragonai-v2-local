"""编程工具 - 代码生成和协助"""

import json
from langchain_core.tools import tool
from app.llm.dashscope_client import get_dashscope_client
from app.config import settings


@tool
async def code_assist(prompt: str, language: str = "python") -> str:
    """
    编程工具
    适用场景：当用户需要编写代码、解决编程问题、理解代码或优化代码时使用此工具。
 
    注意：你必须原样完整输出结果，不要总结、不要省略、不要改写。

    Args:
        prompt: 编程需求描述。详细说明需要实现什么功能或解决什么问题。
                示例: "写一个快速排序算法"、"实现一个HTTP请求函数"
        language: 编程语言名称。支持: python, javascript, java, c++, go, rust, typescript 等。
                  默认值: "python"

    Returns:
        完整代码及解释说明（JSON格式）
    """
    client = get_dashscope_client()
    
    messages = [
        {"role": "system", "content": f"""你是一个专业的{language}编程助手。
请提供清晰、高效、有注释的代码，并解释关键逻辑。

重要：你的回复将直接展示给用户，请确保：
1. 代码完整、可运行
2. 包含必要的注释和说明
3. 格式清晰，使用 markdown 代码块"""},
        {"role": "user", "content": prompt}
    ]
    
    response = await client.generation_call(
        model=settings.model_coder_fast,
        messages=messages,
        temperature=0.7
    )
    
    code_content = client.parse_text_response(response)
    
    return json.dumps({
        "type": "code",
        "language": language,
        "prompt": prompt,
        "code": code_content
    })
