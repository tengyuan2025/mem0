#!/bin/bash
# Swagger UI 本地资源管理脚本

STATIC_DIR="static"
SWAGGER_VERSION="5.17.14"

echo "🛠️  Swagger UI 本地资源管理工具"
echo "=================================="

show_help() {
    echo "用法: $0 [选项]"
    echo ""
    echo "选项:"
    echo "  download    下载最新的Swagger UI资源"
    echo "  update      更新现有资源到最新版本"
    echo "  status      查看当前资源状态"
    echo "  clean       清理本地资源"
    echo "  size        显示资源文件大小"
    echo "  help        显示此帮助信息"
}

download_resources() {
    echo "📥 下载Swagger UI资源..."
    
    # 创建静态目录
    mkdir -p "$STATIC_DIR"
    
    # 取消代理设置，避免影响下载
    unset http_proxy https_proxy
    
    # 下载资源文件
    echo "  下载 CSS..."
    curl -L -o "$STATIC_DIR/swagger-ui.css" \
        "https://cdn.bootcdn.net/ajax/libs/swagger-ui/$SWAGGER_VERSION/swagger-ui.css"
    
    echo "  下载 JavaScript..."
    curl -L -o "$STATIC_DIR/swagger-ui-bundle.js" \
        "https://cdn.bootcdn.net/ajax/libs/swagger-ui/$SWAGGER_VERSION/swagger-ui-bundle.js"
    
    echo "  下载 图标..."
    curl -L -o "$STATIC_DIR/favicon-32x32.png" \
        "https://cdn.bootcdn.net/ajax/libs/swagger-ui/$SWAGGER_VERSION/favicon-32x32.png"
    
    echo "✅ 下载完成！"
}

show_status() {
    echo "📊 当前资源状态:"
    echo "----------------"
    
    if [ -d "$STATIC_DIR" ]; then
        echo "📁 静态目录: $STATIC_DIR"
        echo "📦 Swagger版本: $SWAGGER_VERSION"
        echo ""
        echo "文件列表:"
        
        for file in swagger-ui.css swagger-ui-bundle.js favicon-32x32.png; do
            if [ -f "$STATIC_DIR/$file" ]; then
                size=$(ls -lh "$STATIC_DIR/$file" | awk '{print $5}')
                echo "  ✅ $file ($size)"
            else
                echo "  ❌ $file (缺失)"
            fi
        done
        
        echo ""
        echo "🌐 访问地址:"
        echo "  • API文档: http://localhost:8000/docs"
        echo "  • CSS: http://localhost:8000/static/swagger-ui.css"
        echo "  • JS: http://localhost:8000/static/swagger-ui-bundle.js"
    else
        echo "❌ 静态目录不存在"
        echo "💡 运行 '$0 download' 下载资源"
    fi
}

show_size() {
    echo "📏 资源文件大小:"
    echo "----------------"
    
    if [ -d "$STATIC_DIR" ]; then
        total_size=$(du -sh "$STATIC_DIR" | cut -f1)
        echo "总大小: $total_size"
        echo ""
        echo "详细信息:"
        ls -lh "$STATIC_DIR/" | grep -v "^d" | awk '{print "  " $9 ": " $5}'
    else
        echo "❌ 静态目录不存在"
    fi
}

clean_resources() {
    echo "🗑️  清理本地资源..."
    
    if [ -d "$STATIC_DIR" ]; then
        read -p "确定要删除所有本地资源吗？[y/N] " -n 1 -r
        echo
        if [[ $REPLY =~ ^[Yy]$ ]]; then
            rm -rf "$STATIC_DIR"
            echo "✅ 清理完成"
        else
            echo "❌ 取消清理"
        fi
    else
        echo "❌ 静态目录不存在，无需清理"
    fi
}

update_resources() {
    echo "🔄 更新Swagger UI资源..."
    
    # 备份现有资源
    if [ -d "$STATIC_DIR" ]; then
        backup_dir="${STATIC_DIR}_backup_$(date +%Y%m%d_%H%M%S)"
        cp -r "$STATIC_DIR" "$backup_dir"
        echo "📂 已备份到: $backup_dir"
    fi
    
    # 下载新资源
    download_resources
    
    echo "✅ 更新完成"
}

# 主逻辑
case "${1:-help}" in
    "download")
        download_resources
        ;;
    "update")
        update_resources
        ;;
    "status")
        show_status
        ;;
    "clean")
        clean_resources
        ;;
    "size")
        show_size
        ;;
    "help"|*)
        show_help
        ;;
esac