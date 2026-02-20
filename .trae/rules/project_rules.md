1. langchain使用1.0以上版本，不要使用即将过时的0.1.0或者0.3.0；后端使用fastapi，python使用本地python3.13
2. 基于langchain的agent相关可以参考langchain官方教程
2. langchain官方教程1： https://docs.langchain.com/oss/python/langchain/knowledge-base 涉及 LangChain 的文档加载器、嵌入和向量存储抽象层，旨在支持从（向量）数据库和其他来源检索数据，以便与 LLM 工作流集成。对于那些需要获取数据以进行推理以用于模型推理的应用程序（例如检索增强生成，即 RAG）而言，这些抽象层至关重要。
3. langchain的官方教程2 RAG agent的实现方式: https://docs.langchain.com/oss/python/langchain/rag
4. langchain的技能实现方式：https://docs.langchain.com/oss/python/langchain/multi-agent/skills-sql-assistant
5. 所有与langchain相关的开发与设计需要参考langchain官方教程，不能自己凭空实现。
6. 项目开发框架：
    6.1. 发现需求：通过提问理解真实需求，挑战不合理假设，区分“必须有”和“以后加”
    6.2. 规划 明确v1版本要做什么，用通俗语言解释技能方案
    6.3. 构建 分阶段开发 边做边解释 测试后再推进 关键决策点同步，遇到问题给出选项绝非直接拍板
    6.4. 打磨：让产品看起来专业，优雅处理边界情况
    6.5. 交付：按需部署 提供清晰的使用指南，做好文档，给出v2版本的改进建议

7. 严格保留 ”->” 符号，不要替换为 ”-&gt”; 或其他字符
8. 严格保留 ”>” 符号，不要替换为 ”&gt”; 或其他字符
