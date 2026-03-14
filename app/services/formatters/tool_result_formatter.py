"""工具结果格式化器"""

import json
import logging
from typing import Dict, Any, Optional

logger = logging.getLogger(__name__)


class ToolResultFormatter:
    """工具结果格式化器，统一处理工具返回结果的格式化"""
    
    @staticmethod
    def get_args_preview(args: dict, max_length: int = 50) -> str:
        """生成工具调用参数的预览文本
        
        Args:
            args: 工具调用参数字典
            max_length: 最大预览长度
            
        Returns:
            参数预览字符串
        """
        if not args:
            return ""
        
        preview_parts = []
        for key, value in args.items():
            if isinstance(value, str):
                value_preview = value[:max_length] + "..." if len(value) > max_length else value
            elif isinstance(value, (list, dict)):
                value_str = str(value)
                value_preview = value_str[:max_length] + "..." if len(value_str) > max_length else value_str
            else:
                value_preview = str(value)
            preview_parts.append(f"{key}={value_preview}")
        
        return ", ".join(preview_parts)
    
    @staticmethod
    def format_result(tool_name: str, content: Any) -> Dict[str, Any]:
        """格式化工具结果
        
        Args:
            tool_name: 工具名称
            content: 工具返回内容
            
        Returns:
            格式化后的结果，包含 summary, links, details
        """
        parsed = ToolResultFormatter._parse_content(content)
        
        formatters = {
            "web_search": ToolResultFormatter._format_web_search,
            "search_knowledge_base": ToolResultFormatter._format_knowledge,
            "read_file": ToolResultFormatter._format_file,
            "read_pdf": ToolResultFormatter._format_file,
            "read_word": ToolResultFormatter._format_file,
            "write_file": ToolResultFormatter._format_operation,
            "edit_file": ToolResultFormatter._format_operation,
            "ls": ToolResultFormatter._format_list,
            "glob": ToolResultFormatter._format_list,
            "grep": ToolResultFormatter._format_list,
            "code_assist": ToolResultFormatter._format_code,
            "generate_image": ToolResultFormatter._format_image_generated,
            "edit_image": ToolResultFormatter._format_image_edited,
            "translate_text": ToolResultFormatter._format_translation,
        }
        
        formatter = formatters.get(tool_name, ToolResultFormatter._format_default)
        return formatter(parsed)
    
    @staticmethod
    def _parse_content(content: Any) -> Any:
        """解析内容，尝试从 JSON 字符串解析"""
        if isinstance(content, str):
            try:
                return json.loads(content)
            except (json.JSONDecodeError, TypeError):
                return content
        return content
    
    @staticmethod
    def _format_web_search(content: Any) -> Dict[str, Any]:
        """网页搜索结果"""
        if isinstance(content, dict):
            count = content.get("count", 0)
            links = content.get("links", [])
            
            return {
                "summary": f"找到 {count} 条结果",
                "links": links,
                "details": ""
            }
        
        return {"summary": "搜索完成", "links": [], "details": ""}
    
    @staticmethod
    def _format_knowledge(content: Any) -> Dict[str, Any]:
        """知识库检索结果"""
        if isinstance(content, dict):
            count = content.get("count", 0)
            documents = content.get("documents", [])
            
            sources = []
            seen = set()
            for doc in documents:
                source = doc.get("source", "未知")
                if source not in seen:
                    seen.add(source)
                    sources.append({"title": source, "url": ""})
            
            return {
                "summary": f"找到 {count} 条相关文档" if count > 0 else "未找到相关文档",
                "links": sources,
                "details": ""
            }
        
        return {"summary": "知识库检索完成", "links": [], "details": ""}
    
    @staticmethod
    def _format_file(content: Any) -> Dict[str, Any]:
        """文件读取结果"""
        if isinstance(content, dict):
            return {
                "summary": "文件读取完成",
                "links": [],
                "details": content.get("content", str(content))[:1000]
            }
        
        text = str(content)
        lines = text.split("\n")
        summary = f"读取 {len(lines)} 行" if len(lines) > 1 else "文件读取完成"
        
        return {
            "summary": summary,
            "links": [],
            "details": text[:1000]
        }
    
    @staticmethod
    def _format_operation(content: Any) -> Dict[str, Any]:
        """文件操作结果"""
        return {
            "summary": "操作完成",
            "links": [],
            "details": str(content) if content else "成功"
        }
    
    @staticmethod
    def _format_list(content: Any) -> Dict[str, Any]:
        """列表结果"""
        if isinstance(content, list):
            return {
                "summary": f"找到 {len(content)} 项",
                "links": [],
                "details": "\n".join(str(item) for item in content[:20])
            }
        
        return {
            "summary": "查询完成",
            "links": [],
            "details": str(content)[:500]
        }
    
    @staticmethod
    def _format_code(content: Any) -> Dict[str, Any]:
        """代码生成结果"""
        if isinstance(content, dict):
            language = content.get("language", "code")
            code = content.get("code", "")
            return {
                "summary": f"{language} 代码生成完成",
                "links": [],
                "details": code
            }
        
        return {
            "summary": "代码生成完成",
            "links": [],
            "details": str(content)
        }
    
    @staticmethod
    def _format_image_generated(content: Any) -> Dict[str, Any]:
        """图片生成结果"""
        if isinstance(content, dict):
            urls = content.get("urls", [])
            count = content.get("count", len(urls))
            prompt = content.get("prompt", "")
            size = content.get("size", "")
            
            details_parts = []
            if prompt:
                details_parts.append(f"提示词: {prompt}")
            if size:
                details_parts.append(f"尺寸: {size}")
            
            return {
                "summary": f"已生成 {count} 张图片",
                "links": [{"title": f"图片 {i+1}", "url": url} for i, url in enumerate(urls)],
                "details": "\n".join(details_parts)
            }
        
        return {"summary": "图片生成完成", "links": [], "details": ""}
    
    @staticmethod
    def _format_image_edited(content: Any) -> Dict[str, Any]:
        """图片编辑结果"""
        if isinstance(content, dict):
            url = content.get("url", "")
            prompt = content.get("prompt", "")
            original = content.get("original_image", "")
            
            details_parts = []
            if prompt:
                details_parts.append(f"提示词: {prompt}")
            if original:
                details_parts.append(f"原图: {original}")
            
            return {
                "summary": "图片编辑完成",
                "links": [{"title": "编辑后的图片", "url": url}] if url else [],
                "details": "\n".join(details_parts)
            }
        
        return {"summary": "图片编辑完成", "links": [], "details": ""}
    
    @staticmethod
    def _format_translation(content: Any) -> Dict[str, Any]:
        """翻译结果"""
        if isinstance(content, dict):
            target_lang = content.get("target_lang", "")
            translated = content.get("translated_text", "")
            
            lang_map = {
                "zh": "中文", "en": "英语", "ja": "日语", 
                "ko": "韩语", "fr": "法语", "de": "德语", "es": "西班牙语"
            }
            lang_name = lang_map.get(target_lang, target_lang)
            
            return {
                "summary": f"已翻译为{lang_name}",
                "links": [],
                "details": translated
            }
        
        return {"summary": "翻译完成", "links": [], "details": str(content)}
    
    @staticmethod
    def _format_default(content: Any) -> Dict[str, Any]:
        """默认格式化"""
        if isinstance(content, dict):
            return {
                "summary": content.get("summary", "执行完成"),
                "links": content.get("links", []),
                "details": json.dumps(content, ensure_ascii=False)[:500]
            }
        
        return {
            "summary": "执行完成",
            "links": [],
            "details": str(content)[:500] if content else ""
        }
