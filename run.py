"""启动脚本 - 设置 Windows 兼容的事件循环"""

import asyncio
import os
import sys

# Windows 上使用 SelectorEventLoop 以兼容 psycopg
# 必须在任何其他导入之前设置
if os.name == 'nt':
    asyncio.set_event_loop_policy(asyncio.WindowsSelectorEventLoopPolicy())

import uvicorn

if __name__ == "__main__":
    uvicorn.run(
        "app.main:create_app",
        host="0.0.0.0",
        port=8000,
        loop="asyncio",
        reload=True, 
        factory= True
        # workers=1
    )
