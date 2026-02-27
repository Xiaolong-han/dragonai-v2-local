@echo off
setlocal enabledelayedexpansion

echo ========================================
echo   DragonAI 部署脚本 (Windows)
echo ========================================

if "%1"=="" goto deploy
if "%1"=="deploy" goto deploy
if "%1"=="logs" goto logs
if "%1"=="stop" goto stop
if "%1"=="restart" goto restart
if "%1"=="status" goto status
if "%1"=="build" goto build
goto usage

:deploy
echo [INFO] 检查依赖...
where docker >nul 2>&1
if errorlevel 1 (
    echo [ERROR] Docker 未安装，请先安装 Docker Desktop
    exit /b 1
)

where docker-compose >nul 2>&1
if errorlevel 1 (
    echo [ERROR] docker-compose 未安装
    exit /b 1
)

echo [INFO] 依赖检查通过

if not exist .env.production (
    echo [ERROR] .env.production 文件不存在
    echo [INFO] 请复制 .env.production.example 并配置环境变量
    exit /b 1
)

echo [INFO] 构建前端...
cd frontend
if not exist node_modules (
    echo [INFO] 安装前端依赖...
    call npm install
)
call npm run build
cd ..

if not exist frontend\dist (
    echo [ERROR] 前端构建失败
    exit /b 1
)

echo [INFO] 启动部署...
copy /Y .env.production .env

docker-compose down
docker-compose build --no-cache
docker-compose up -d

echo [INFO] 等待服务启动...
timeout /t 10 /nobreak >nul

echo [INFO] 检查服务状态...
docker-compose ps

echo.
echo [INFO] 部署完成!
echo [INFO] 访问地址: http://localhost
echo [INFO] API 文档: http://localhost/docs
goto end

:logs
echo [INFO] 显示日志 (Ctrl+C 退出)...
docker-compose logs -f
goto end

:stop
echo [INFO] 停止服务...
docker-compose down
echo [INFO] 服务已停止
goto end

:restart
echo [INFO] 重启服务...
docker-compose restart
echo [INFO] 服务已重启
goto end

:status
docker-compose ps
goto end

:build
echo [INFO] 构建前端...
cd frontend
call npm run build
cd ..
echo [INFO] 构建 Docker 镜像...
docker-compose build --no-cache
goto end

:usage
echo 用法: %0 {deploy^|logs^|stop^|restart^|status^|build}
exit /b 1

:end
endlocal
