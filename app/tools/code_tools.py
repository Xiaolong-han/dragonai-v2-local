"""编程工具 - 代码生成和协助"""

from langchain_core.tools import tool
from app.llm.model_factory import ModelFactory


@tool
async def code_assist(prompt: str, language: str = "python") -> str:
    """
    协助编程任务，包括代码生成、调试、解释和优化。

    重要：此工具生成的代码是用户的核心需求，必须完整展示给用户，不要总结或省略。
    
    当用户需要编写代码、解决编程问题、理解代码、调试错误或优化代码时使用此工具。
    支持多种编程语言，包括Python、JavaScript、Java、C++、Go等。

    Args:
        prompt: 编程需求描述，详细说明需要实现什么功能或解决什么问题
        language: 编程语言，如python、javascript、java、c++、go等，默认python

    Returns:
        代码及解释说明 - 必须完整输出给用户
    """
    model = ModelFactory.get_coder_model(is_plus=False)
    messages = [
        {"role": "system", "content": f"""你是一个专业的{language}编程助手。
请提供清晰、高效、有注释的代码，并解释关键逻辑。

重要：你的回复将直接展示给用户，请确保：
1. 代码完整、可运行
2. 包含必要的注释和说明
3. 格式清晰，使用 markdown 代码块"""},
        {"role": "user", "content": prompt}
    ]
    result = await model.ainvoke(messages)
    return result.content
