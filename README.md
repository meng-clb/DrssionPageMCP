# DrissionPage MCP Server -- 骚神出品

基于DrissionPage和FastMCP的浏览器自动化MCP服务器，提供丰富的浏览器操作API供AI调用。

## 项目简介
![logo](img/DrissionPageMCP-logo.png)

DrissionPage MCP  是一个基于 DrissionPage 和 FastMCP 的浏览器自动化MCP server服务器，它提供了一系列强大的浏览器操作 API，让您能够轻松通过AI实现网页自动化操作。

### 主要特性

- 支持浏览器的打开、关闭和连接管理
- 提供丰富的页面元素操作方法
- 支持 JavaScript 代码执行
- 支持 CDP 协议操作
- 提供便捷的文件下载功能
- 支持键盘按键模拟
- 支持页面截图功能
- 增加 网页后台监听数据包的功能
- 增加自动上传下载文件功能

#### Python要求
- Python >= 3.9
- pip（最新版本）
- uv （最新版本）


#### 浏览器要求
- Chrome 浏览器（推荐 90 及以上版本）


#### 必需的Python包
- drissionpage >= 4.1.0.18
- fastmcp >= 2.4.0
- uv

## 安装说明
把本仓库git clone到本地，核心文件是main.py。建议先使用 `python -m venv venv-DrissionPage-MCP` 创建并激活虚拟环境，然后运行 `pip install -r requirements.txt` 安装依赖。

### 安装到Cursor/VSCode编辑器

请将以下对应您操作系统的配置代码粘贴到编辑器的`mcpServers`设置中。

#### Windows 推荐配置 (更可靠)

这种方法通过指定虚拟环境中 `python.exe` 的绝对路径来启动服务器，可以避免很多在 Windows 上常见的环境和路径问题，是**推荐**的方式。

```json
{
  "mcpServers": {
    "DrssionPageMCP": {
      "type": "stdio",
      "command": "C:\\path\\to\\your\\project\\DrssionPageMCP\\venv-DrissionPage-MCP\\Scripts\\python.exe",
      "args": [
        "C:\\path\\to\\your\\project\\DrssionPageMCP\\main.py"
      ]
    }
  }
}
```
**注意:**
- **请务必将 `C:\\path\\to\\your\\project` 修改为您自己电脑上的实际绝对路径。**
- 在 JSON 文件中，Windows 路径的反斜杠 `\` 需要转义，即写成双反斜杠 `\\`。


#### macOS / Linux 推荐配置

在 macOS 和 Linux 上，如果 `uv` 已正确安装并位于 `PATH` 环境变量中，可以直接使用 `uv` 命令。

```json
{
  "mcpServers": {
    "DrssionPageMCP": {
      "type": "stdio",
      "command": "uv",
      "args": [
        "run",
        "/path/to/your/project/DrssionPageMCP/main.py"
      ]
    }
  }
}
```
**注意:**
- **请务必将 `/path/to/your/project` 修改为您自己电脑上的实际绝对路径。**


---
- [《MCP安装参考教程》](https://docs.trae.ai/ide/model-context-protocol)



## 调试命令

调试
```
npx -y @modelcontextprotocol/inspector uv run D:\\test10\\DrssionPageMCP\\main.py
```
或者
```
mcp dev  D:\\test10\\DrssionPageMCP\\main.py
```

## 更新日志
### v0.1.3
增加 自动上传下载文件功能
### v0.1.2
增加 网页后台监听数据包的功能

### v0.1.0

- 初始版本发布
- 实现基本的浏览器控制功能
- 提供元素操作 API
