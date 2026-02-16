
from app.llm.qwen_models import QwenCoderModel


class CodingSkill:
    """编程技能"""

    @staticmethod
    def code(
        prompt: str,
        model: str = "qwen3-coder-flash",
        temperature: float = 0.7,
        max_tokens: int = None
    ) -> dict:
        """
        生成代码

        Args:
            prompt: 编程需求描述
            model: 模型名称，可选 "qwen3-coder-flash" 或 "qwen3-coder-plus"
            temperature: 温度参数
            max_tokens: 最大token数

        Returns:
            包含代码生成结果的字典
        """
        if model == "qwen3-coder-plus":
            coder_model = QwenCoderModel.qwen3_coder_plus(
                temperature=temperature,
                max_tokens=max_tokens
            )
        else:
            coder_model = QwenCoderModel.qwen3_coder_flash(
                temperature=temperature,
                max_tokens=max_tokens
            )

        messages = [{"role": "user", "content": prompt}]
        return coder_model.invoke(messages)

    @staticmethod
    async def acode(
        prompt: str,
        model: str = "qwen3-coder-flash",
        temperature: float = 0.7,
        max_tokens: int = None
    ) -> dict:
        """
        异步生成代码

        Args:
            prompt: 编程需求描述
            model: 模型名称，可选 "qwen3-coder-flash" 或 "qwen3-coder-plus"
            temperature: 温度参数
            max_tokens: 最大token数

        Returns:
            包含代码生成结果的字典
        """
        if model == "qwen3-coder-plus":
            coder_model = QwenCoderModel.qwen3_coder_plus(
                temperature=temperature,
                max_tokens=max_tokens
            )
        else:
            coder_model = QwenCoderModel.qwen3_coder_flash(
                temperature=temperature,
                max_tokens=max_tokens
            )

        messages = [{"role": "user", "content": prompt}]
        return await coder_model.ainvoke(messages)

