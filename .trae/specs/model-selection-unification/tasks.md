# 模型选择统一化 - The Implementation Plan (Decomposed and Prioritized Task List)

## [ ] Task 0: 添加通用聊天模型列表 API
- **Priority**: P0
- **Depends On**: None
- **Description**: 
  - 创建新的 API 端点 `/api/v1/models/chat`
  - 创建相应的响应 Schema
  - 返回通用聊天模型列表（包括快速和专家模型）
- **Acceptance Criteria Addressed**: [AC-6]
- **Test Requirements**:
  - `programmatic` TR-0.1: GET /api/v1/models/chat 端点正常响应
  - `programmatic` TR-0.2: 响应包含通用聊天模型，标注快速/专家

## [ ] Task 0a: 添加专项技能模型列表 API
- **Priority**: P0
- **Depends On**: None
- **Description**: 
  - 创建新的 API 端点 `/api/v1/models/skills`
  - 创建相应的响应 Schema
  - 返回各专项技能的模型列表，每个技能单独列出自己的快速和专家模型
- **Acceptance Criteria Addressed**: [AC-7]
- **Test Requirements**:
  - `programmatic` TR-0a.1: GET /api/v1/models/skills 端点正常响应
  - `programmatic` TR-0a.2: 响应每个技能单独列出自己的快速和专家模型

## [ ] Task 1: 更新技能 Schema 添加 is_expert 参数
- **Priority**: P0
- **Depends On**: None
- **Description**: 
  - 更新 `app/schemas/skills.py` 中的所有技能请求类
  - 添加 `is_expert` 可选字段
  - 保持 `model` 字段的向后兼容性
  - 更新文档说明新参数的使用方式
- **Acceptance Criteria Addressed**: [AC-1, AC-2, AC-5]
- **Test Requirements**:
  - `programmatic` TR-1.1: 所有技能请求类都有 `is_expert` 字段
  - `programmatic` TR-1.2: `model` 字段仍然存在且为可选
  - `human-judgement` TR-1.3: 字段文档清晰说明使用方式
- **Notes**: 默认值应该为 `False`，表示使用快速模型

## [ ] Task 2: 更新技能实现以支持 is_expert
- **Priority**: P0
- **Depends On**: Task 1
- **Description**: 
  - 更新 `app/skills/` 下的所有技能实现
  - 添加 `is_expert` 参数支持
  - 实现模型选择逻辑：如果提供了 `model` 则使用该模型，否则根据 `is_expert` 选择
  - 确保每个技能都使用自己的快速/专家模型对
- **Acceptance Criteria Addressed**: [AC-1, AC-2, AC-3, AC-4]
- **Test Requirements**:
  - `programmatic` TR-2.1: 当提供 `is_expert=True` 时使用该技能的专家模型
  - `programmatic` TR-2.2: 当提供 `is_expert=False` 或未提供时使用该技能的快速模型
  - `programmatic` TR-2.3: 当同时提供 `model` 和 `is_expert` 时，优先使用 `model`
  - `programmatic` TR-2.4: 未提供任何参数时使用该技能的默认快速模型

## [ ] Task 3: 更新技能 API 路由层
- **Priority**: P0
- **Depends On**: Task 2
- **Description**: 
  - 更新 `app/api/v1/skills.py` 中的所有端点
  - 传递新的 `is_expert` 参数给技能实现
  - 保持向后兼容的参数处理
- **Acceptance Criteria Addressed**: [AC-1, AC-2, AC-5]
- **Test Requirements**:
  - `programmatic` TR-3.1: 所有技能端点能正确处理 `is_expert` 参数
  - `programmatic` TR-3.2: 使用 `model` 参数的旧代码仍能正常工作

## [ ] Task 4: 运行并更新测试
- **Priority**: P1
- **Depends On**: Task 3
- **Description**: 
  - 更新 `tests/unit/test_skills.py` 以测试新的参数
  - 运行现有测试确保没有破坏现有功能
  - 添加新的测试用例验证 `is_expert` 参数功能
- **Acceptance Criteria Addressed**: [AC-1, AC-2, AC-3, AC-4]
- **Test Requirements**:
  - `programmatic` TR-4.1: 所有现有测试通过
  - `programmatic` TR-4.2: 新添加的测试覆盖 `is_expert` 参数的所有场景

## [ ] Task 5: 验证集成测试
- **Priority**: P1
- **Depends On**: Task 4
- **Description**: 
  - 运行集成测试确保 API 端点功能正常
  - 验证聊天 API 和技能 API 的风格一致性
- **Acceptance Criteria Addressed**: [AC-1, AC-2, AC-5]
- **Test Requirements**:
  - `programmatic` TR-5.1: 集成测试全部通过
  - `human-judgement` TR-5.2: API 风格统一，用户体验一致
