"""调试中间件 - 用于观察最终的 system prompt"""

import logging
from typing import Any, Awaitable, Callable

from langchain.agents.middleware.types import AgentMiddleware, ContextT, ModelRequest, ModelResponse, ResponseT, StateT_co

logger = logging.getLogger(__name__)


class DebugMiddleware(AgentMiddleware[StateT_co, ContextT, ResponseT]):
    """调试中间件 - 打印最终的 system prompt
    
    用于观察技能是否正确加载到系统提示中。
    
    使用方式：
    ```python
    middleware = [
        FilesystemMiddleware(backend=skills_backend),
        SkillsMiddleware(backend=skills_backend, sources=["/"]),
        DebugMiddleware(),  # 放在最后，可以看到最终结果
    ]
    ```
    """
    
    state_schema = dict
    
    def __init__(self, log_full_prompt: bool = False, max_length: int = 2000):
        """初始化调试中间件
        
        Args:
            log_full_prompt: 是否打印完整的 system prompt
            max_length: 打印的最大长度（字符数）
        """
        self.log_full_prompt = log_full_prompt
        self.max_length = max_length
    
    def wrap_model_call(
        self,
        request: ModelRequest[ContextT],
        handler: Callable[[ModelRequest[ContextT]], ModelResponse[ResponseT]],
    ) -> ModelResponse[ResponseT]:
        """在模型调用前打印 system prompt"""
        self._log_system_prompt(request)
        return handler(request)
    
    async def awrap_model_call(
        self,
        request: ModelRequest[ContextT],
        handler: Callable[[ModelRequest[ContextT]], Awaitable[ModelResponse[ResponseT]]],
    ) -> ModelResponse[ResponseT]:
        """在模型调用前打印 system prompt (异步版本)"""
        self._log_system_prompt(request)
        return await handler(request)
    
    def _log_system_prompt(self, request: ModelRequest[ContextT]) -> None:
        """打印 system prompt"""
        system_message = request.system_message
        
        if system_message is None:
            logger.info("[DEBUG-MIDDLEWARE] System prompt: (None)")
            return
        
        content = getattr(system_message, 'content', str(system_message))
        
        if isinstance(content, list):
            content = '\n'.join(
                item.get('text', str(item)) if isinstance(item, dict) else str(item)
                for item in content
            )
        
        if self.log_full_prompt:
            logger.info(f"[DEBUG-MIDDLEWARE] System prompt ({len(content)} chars):\n{content}")
        else:
            truncated = content[:self.max_length]
            if len(content) > self.max_length:
                truncated += f"\n... (truncated, total {len(content)} chars)"
            logger.info(f"[DEBUG-MIDDLEWARE] System prompt ({len(content)} chars):\n{truncated}")
        
        self._log_skills_info(content)
    
    def _log_skills_info(self, content: str) -> None:
        """分析并打印技能相关信息"""
        lines = content.split('\n')
        
        skills_section_found = False
        skills_found = []
        
        for i, line in enumerate(lines):
            if "## Skills System" in line or "**Available Skills:**" in line:
                skills_section_found = True
                logger.info(f"[DEBUG-MIDDLEWARE] Found Skills section at line {i}")
            
            if skills_section_found and line.startswith("- **"):
                skill_name = line.split("**")[1] if "**" in line else line
                skills_found.append(skill_name)
        
        if skills_found:
            logger.info(f"[DEBUG-MIDDLEWARE] Skills in prompt: {skills_found}")
        elif "Skills System" not in content:
            logger.warning("[DEBUG-MIDDLEWARE] No Skills section found in system prompt!")
