#!/usr/bin/env python3
"""
API文档的多CDN备选方案
如果当前CDN不可用，可以快速切换到其他镜像源
"""

# 国内可用的CDN镜像源配置
CDN_CONFIGS = {
    "bootcdn": {
        "name": "BootCDN (推荐)",
        "swagger_css": "https://cdn.bootcdn.net/ajax/libs/swagger-ui/5.17.14/swagger-ui.css",
        "swagger_js": "https://cdn.bootcdn.net/ajax/libs/swagger-ui/5.17.14/swagger-ui-bundle.js",
        "swagger_favicon": "https://cdn.bootcdn.net/ajax/libs/swagger-ui/5.17.14/favicon-32x32.png",
        "redoc_js": "https://cdn.bootcdn.net/ajax/libs/redoc/2.1.5/bundles/redoc.standalone.js"
    },
    
    "staticfile": {
        "name": "Staticfile CDN",
        "swagger_css": "https://cdn.staticfile.org/swagger-ui/5.17.14/swagger-ui.css",
        "swagger_js": "https://cdn.staticfile.org/swagger-ui/5.17.14/swagger-ui-bundle.js", 
        "swagger_favicon": "https://cdn.staticfile.org/swagger-ui/5.17.14/favicon-32x32.png",
        "redoc_js": "https://cdn.staticfile.org/redoc/2.1.5/bundles/redoc.standalone.js"
    },
    
    "unpkg_cn": {
        "name": "UNPKG 中国镜像",
        "swagger_css": "https://unpkg.com/swagger-ui-dist@5.17.14/swagger-ui.css",
        "swagger_js": "https://unpkg.com/swagger-ui-dist@5.17.14/swagger-ui-bundle.js",
        "swagger_favicon": "https://unpkg.com/swagger-ui-dist@5.17.14/favicon-32x32.png", 
        "redoc_js": "https://unpkg.com/redoc@2.1.5/bundles/redoc.standalone.js"
    },
    
    "local": {
        "name": "本地文件 (需要下载)",
        "swagger_css": "/static/swagger-ui.css",
        "swagger_js": "/static/swagger-ui-bundle.js",
        "swagger_favicon": "/static/favicon-32x32.png",
        "redoc_js": "/static/redoc.standalone.js"
    }
}

def get_docs_html(cdn_name="bootcdn"):
    """
    生成API文档HTML，使用指定的CDN源
    """
    config = CDN_CONFIGS.get(cdn_name, CDN_CONFIGS["bootcdn"])
    
    return f"""
    <!DOCTYPE html>
    <html>
    <head>
        <title>Mem0 API 文档</title>
        <link rel="stylesheet" type="text/css" href="{config['swagger_css']}" />
        <link rel="icon" type="image/png" href="{config['swagger_favicon']}" sizes="32x32" />
        <style>
            html {{
                box-sizing: border-box;
                overflow: -moz-scrollbars-vertical;
                overflow-y: scroll;
            }}
            *, *:before, *:after {{
                box-sizing: inherit;
            }}
            body {{
                margin:0;
                background: #fafafa;
            }}
            .cdn-info {{
                position: fixed;
                top: 10px;
                right: 10px;
                background: rgba(0,0,0,0.7);
                color: white;
                padding: 5px 10px;
                border-radius: 5px;
                font-size: 12px;
                z-index: 9999;
            }}
        </style>
    </head>
    <body>
        <div class="cdn-info">CDN: {config['name']}</div>
        <div id="swagger-ui"></div>
        <script src="{config['swagger_js']}"></script>
        <script>
            const ui = SwaggerUIBundle({{
                url: '/openapi.json',
                dom_id: '#swagger-ui',
                presets: [
                    SwaggerUIBundle.presets.apis,
                    SwaggerUIBundle.presets.standalone
                ],
                layout: "BaseLayout",
                deepLinking: true,
                showExtensions: true,
                showCommonExtensions: true
            }})
        </script>
    </body>
    </html>
    """

if __name__ == "__main__":
    # 测试各个CDN的可用性
    import requests
    import sys
    
    print("🔍 测试各CDN源的可用性...")
    
    for name, config in CDN_CONFIGS.items():
        if name == "local":
            continue
            
        print(f"\n📦 测试 {config['name']}:")
        
        try:
            # 测试CSS
            response = requests.head(config['swagger_css'], timeout=5)
            css_status = "✅" if response.status_code == 200 else f"❌ {response.status_code}"
            
            # 测试JS  
            response = requests.head(config['swagger_js'], timeout=5)
            js_status = "✅" if response.status_code == 200 else f"❌ {response.status_code}"
            
            print(f"  CSS: {css_status}")
            print(f"  JS:  {js_status}")
            
        except Exception as e:
            print(f"  ❌ 连接失败: {e}")
    
    print(f"\n💡 当前使用: {CDN_CONFIGS['bootcdn']['name']}")
    print("💡 如需切换CDN，请修改 simple-api.py 中的链接")