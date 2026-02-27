#!/bin/bash
set -e

echo "========================================"
echo "  DragonAI 部署脚本"
echo "========================================"

RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m'

log_info() {
    echo -e "${GREEN}[INFO]${NC} $1"
}

log_warn() {
    echo -e "${YELLOW}[WARN]${NC} $1"
}

log_error() {
    echo -e "${RED}[ERROR]${NC} $1"
}

check_command() {
    if ! command -v $1 &> /dev/null; then
        log_error "$1 未安装，请先安装 $1"
        exit 1
    fi
}

check_commands() {
    log_info "检查依赖..."
    check_command docker
    check_command docker-compose
    log_info "依赖检查通过"
}

check_env_file() {
    if [ ! -f .env.production ]; then
        log_error ".env.production 文件不存在"
        log_info "请复制 .env.production.example 并配置环境变量"
        exit 1
    fi
    
    if grep -q "your-very-secure-secret-key" .env.production; then
        log_warn "请修改 .env.production 中的 SECRET_KEY"
    fi
    
    if grep -q "your-qwen-api-key" .env.production; then
        log_warn "请配置 .env.production 中的 QWEN_API_KEY"
    fi
}

build_frontend() {
    log_info "构建前端..."
    
    if [ ! -d "frontend/node_modules" ]; then
        log_info "安装前端依赖..."
        cd frontend
        npm install
        cd ..
    fi
    
    cd frontend
    npm run build
    cd ..
    
    if [ ! -d "frontend/dist" ]; then
        log_error "前端构建失败"
        exit 1
    fi
    
    log_info "前端构建完成"
}

deploy() {
    log_info "启动部署..."
    
    cp .env.production .env
    
    docker-compose down
    
    docker-compose build --no-cache
    
    docker-compose up -d
    
    log_info "等待服务启动..."
    sleep 10
    
    log_info "检查服务状态..."
    docker-compose ps
    
    log_info "部署完成!"
    log_info "访问地址: http://localhost"
    log_info "API 文档: http://localhost/docs"
}

show_logs() {
    log_info "显示日志 (Ctrl+C 退出)..."
    docker-compose logs -f
}

case "${1:-deploy}" in
    deploy)
        check_commands
        check_env_file
        build_frontend
        deploy
        ;;
    logs)
        show_logs
        ;;
    stop)
        log_info "停止服务..."
        docker-compose down
        log_info "服务已停止"
        ;;
    restart)
        log_info "重启服务..."
        docker-compose restart
        log_info "服务已重启"
        ;;
    status)
        docker-compose ps
        ;;
    build)
        build_frontend
        docker-compose build --no-cache
        ;;
    *)
        echo "用法: $0 {deploy|logs|stop|restart|status|build}"
        exit 1
        ;;
esac
