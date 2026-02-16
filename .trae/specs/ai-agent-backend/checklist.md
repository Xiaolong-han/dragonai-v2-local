# AI Agent 后端系统 - 验证清单

## 架构与设计
- [ ] 项目目录结构符合规范设计
- [ ] 使用FastAPI作为Web框架
- [ ] 使用LangChain 1.0+版本（不使用0.x版本）
- [ ] 架构清晰的分层设计（API、Service、Model）
- [ ] 预留技能扩展接口设计合理

## 数据库与缓存
- [ ] PostgreSQL数据库连接配置正确
- [ ] Redis连接配置正确
- [ ] Cache Aside缓存模式正确实现
- [ ] PostgresSaver配置正确用于Agent状态持久化
- [ ] ChromaDB向量存储配置正确
- [ ] 数据模型设计合理

## 用户认证与会话管理
- [ ] 用户名密码认证实现正确
- [ ] JWT认证实现正确
- [ ] 用户注册（用户名+密码）接口正常工作
- [ ] 用户登录（用户名+密码）接口正常工作
- [ ] 会话创建接口正常工作
- [ ] 会话删除接口正常工作
- [ ] 会话重命名接口正常工作
- [ ] 会话置顶接口正常工作
- [ ] 会话列表按正确顺序返回

## 通义千问模型集成
- [ ] qwen-flash模型可以正常调用
- [ ] qwen3-max模型可以正常调用
- [ ] qwen-vl-ocr模型可以正常调用
- [ ] qwen3-vl-plus模型可以正常调用
- [ ] z-image-turbo/qwen-image模型可以正常调用
- [ ] qwen3-coder-flash/qwen3-coder-plus模型可以正常调用
- [ ] qwen-mt-flash/qwen-mt-plus模型可以正常调用
- [ ] 专家模型深度思考功能正常工作

## RAG模块
- [ ] 文档加载器支持PDF格式
- [ ] 文档加载器支持WORD格式
- [ ] 文档加载器支持MARKDOWN格式
- [ ] 文档分割器工作正常
- [ ] 文档嵌入正常工作
- [ ] 向量存储到ChromaDB成功
- [ ] 检索器返回相关文档片段
- [ ] 知识库上传接口正常工作
- [ ] RAG工具可以被Agent调用

## 联网搜索（使用Tavily）
- [ ] TavilySearchResults集成正确
- [ ] Tavily搜索工具可以正常调用
- [ ] 搜索结果格式正确
- [ ] 搜索工具可以被Agent调用

## 技能系统（按LangChain官方方式）
- [ ] Skill TypedDict结构定义正确（name、description、content）
- [ ] load_skill工具实现正确，使用@tool装饰器
- [ ] load_skill工具可以正常加载技能完整内容
- [ ] SkillMiddleware实现正确
- [ ] SkillMiddleware正确向系统提示词注入技能描述
- [ ] SkillMiddleware正确注册load_skill工具
- [ ] 图像生成技能定义正确并正常工作
- [ ] 图像编辑技能定义正确并正常工作
- [ ] 编程技能定义正确并正常工作
- [ ] 翻译技能定义正确并正常工作
- [ ] Agent可以调用load_skill工具
- [ ] 技能可以按需加载（仅在需要时加载完整内容）

## 多模态处理
- [ ] 文件上传处理正常工作
- [ ] 文档理解（OCR）正常工作
- [ ] 图片理解正常工作
- [ ] 图片和文档存储到本地文件系统正常工作

## Agent系统（使用create_agent）
- [ ] 使用langchain.agents.create_agent创建Agent
- [ ] 系统提示词配置正确
- [ ] SkillMiddleware正确加载到Agent
- [ ] PostgresSaver正确配置为checkpointer
- [ ] Agent可以调用RAG工具
- [ ] Agent可以调用搜索工具
- [ ] Agent可以调用load_skill工具
- [ ] Agent状态可以正确持久化到PostgreSQL
- [ ] Agent状态可以正确从PostgreSQL恢复
- [ ] 完全遵循LangChain 1.0官方最佳实践

## 聊天API
- [ ] 聊天发送接口正常工作
- [ ] 消息历史查询接口正常工作
- [ ] 模型选择功能正常工作
- [ ] 多模态输入可以正确处理
- [ ] 流式响应（SSE）正常工作
- [ ] 缓存策略正确实现

## 测试覆盖
- [ ] 单元测试完整覆盖所有Service层
- [ ] 单元测试完整覆盖所有工具函数
- [ ] 单元测试完整覆盖所有Agent和技能
- [ ] 集成测试完整覆盖所有API接口
- [ ] 所有单元测试100%通过
- [ ] 所有集成测试100%通过
- [ ] 代码覆盖率>80%

## 部署与配置
- [ ] 部署文档清晰完整
- [ ] .env.example配置文件完整
- [ ] 数据库初始化脚本正常工作
- [ ] 启动脚本正常工作
- [ ] 系统可以在本地成功部署运行
