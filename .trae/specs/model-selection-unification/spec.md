# 模型选择统一化 - Product Requirement Document

## Overview
- **Summary**: 统一所有 API 接口的模型选择方式，使聊天 API 和技能 API 保持一致的用户体验，使用简单的 `is_expert` 布尔值替代需要记忆的完整模型名称。
- **Purpose**: 解决当前聊天 API 和技能 API 模型选择方式不一致的问题，简化用户操作，提供统一、友好的用户体验。
- **Target Users**: 使用 DragonAI 后端 API 的开发者和最终用户

## Goals
- 统一聊天 API 和技能 API 的模型选择接口风格
- 每个技能都有自己的快速和专家两个模型选项
- 使用 `is_expert` 布尔值选择快速或专家模型
- 保持向后兼容性（继续支持直接指定模型名称）
- 添加 API 端点列出通用聊天模型和各专项技能模型
- 简化用户操作，降低使用门槛

## Non-Goals (Out of Scope)
- 不改变当前已有的模型列表和配置
- 不添加新的模型功能或模型类型
- 不重构底层模型工厂的核心逻辑

## Background & Context
- 当前聊天 API (`/api/v1/chat/send`) 使用 `is_expert` 布尔值来选择快速或专家模型
- 技能 API (`/api/v1/skills/*`) 使用完整的模型名称（如 "qwen3-coder-flash"、"qwen-mt-plus" 等）
- 这种不一致性增加了用户的学习成本和使用难度
- 项目已有完善的 `ModelFactory` 类，包含所有模型的快速/专家区分逻辑

## Functional Requirements
- **FR-1**: 每个技能都有自己的快速和专家两个模型选项
- **FR-2**: 所有技能 API 支持 `is_expert` 参数来选择该技能的快速或专家模型
- **FR-3**: 保持向后兼容性，继续支持直接指定 `model` 名称
- **FR-4**: 为每个技能类型定义默认的快速/专家模型映射
- **FR-5**: 更新所有技能 API 的请求/响应 Schema
- **FR-6**: 添加 API 端点列出通用聊天模型列表（用于主聊天界面）
- **FR-7**: 添加 API 端点列出各专项技能的模型列表（每个技能单独列出自己的快速和专家模型）

## Non-Functional Requirements
- **NFR-1**: 所有 API 变更保持现有功能的正确性
- **NFR-2**: 代码变更符合项目现有的代码风格和架构
- **NFR-3**: 确保变更不会引入性能退化

## Constraints
- **Technical**: 使用 Python 3.13、FastAPI、Pydantic、现有 ModelFactory
- **Business**: 保持向后兼容性，不破坏现有用户的代码
- **Dependencies**: 依赖现有的 ModelFactory 和技能实现

## Assumptions
- 用户更倾向于使用简单的 `is_expert` 而不是记忆复杂的模型名称
- 现有技能的快速/专家模型对是固定且明确的
- 向后兼容性对现有用户是重要的

## Acceptance Criteria

### AC-1: 每个技能都有自己的快速和专家模型
- **Given**: 所有专项技能（编程、翻译、图像生成、图像编辑等）
- **When**: 查看每个技能的可用模型
- **Then**: 每个技能都有自己对应的快速和专家两个模型选项
- **Verification**: `programmatic`

### AC-2: 技能 API 支持 is_expert 参数
- **Given**: 用户调用某技能 API 时
- **When**: 用户提供 `is_expert` 参数（true/false）
- **Then**: API 自动选择该技能对应的快速/专家模型，无需用户指定完整模型名称
- **Verification**: `programmatic`

### AC-3: 保持向后兼容性
- **Given**: 用户调用技能 API 时
- **When**: 用户直接提供 `model` 参数（完整模型名称）
- **Then**: API 继续使用用户指定的模型，功能正常
- **Verification**: `programmatic`

### AC-4: 默认值合理
- **Given**: 用户调用技能 API 时
- **When**: 用户未提供 `is_expert` 或 `model` 参数
- **Then**: API 使用该技能的默认快速模型
- **Verification**: `programmatic`

### AC-5: 接口风格统一
- **Given**: 所有 API 接口
- **When**: 查看 API 文档和使用方式
- **Then**: 聊天 API 和技能 API 的模型选择方式保持一致（都使用 is_expert）
- **Verification**: `human-judgment`

### AC-6: 通用聊天模型列表 API 可用
- **Given**: 用户访问通用聊天模型列表 API
- **When**: 调用 GET /api/v1/models/chat
- **Then**: 返回通用聊天模型列表（包括快速和专家模型）
- **Verification**: `programmatic`

### AC-7: 专项技能模型列表 API 可用
- **Given**: 用户访问专项技能模型列表 API
- **When**: 调用 GET /api/v1/models/skills
- **Then**: 返回各专项技能的模型列表，每个技能单独列出自己的快速和专家模型
- **Verification**: `programmatic`
