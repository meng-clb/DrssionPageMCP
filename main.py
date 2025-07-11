#!/usr/bin/env python3
# -*- coding: utf-8 -*-

from typing import Any, Literal
import re
from pathlib import Path
from DrissionPage import Chromium, ChromiumOptions
from mcp.server.fastmcp import FastMCP, Image, Context

from DrissionPage.items import SessionElement, ChromiumElement, ShadowRoot, NoneElement, ChromiumTab, MixTab, ChromiumFrame
from DrissionPage.common import Keys

提示 = '''
DrissionPage MCP  是一个基于 DrissionPage 和 FastMCP 的浏览器自动化MCP server服务器，它提供了一系列强大的浏览器操作 API，让您能够轻松通过AI实现网页自动化操作。
点击元素前，需要先获取页面所有可点击元素的信息，使用get_all_clickable_elements()方法。
输入元素前，需要先获取页面所有可输入元素的信息，使用get_all_input_elements()方法。
'''

# region DrissionPageMCP
class DrissionPageMCP():
    def __init__(self):
        self.browser: Chromium | None = None
        self.session = None
        self.current_tab: ChromiumTab | None = None
        self.current_frame = None
        self.current_shadow_root = None
        self.cdp_event_data = []
        self.response_listener_data = []

    def get_version(self) -> str:
        """ 获取版本号"""
        return "2.0.0" # Merged version

    async def connect_or_open_browser(self, config: dict = {'debug_port': 9222}) -> dict:
        """
        用DrissionPage 打开或接管已打开的浏览器，参数通过字典传递。
        必要参数:
            config (dict): 可选键包括 'debug_port'、'browser_path'、'headless'
        返回:
            dict: 浏览器信息
        """
        co = ChromiumOptions()
        if config.get("debug_port"):
            co.set_local_port(config["debug_port"])
        if config.get("browser_path"):
            co.set_browser_path(config["browser_path"])
        if config.get("headless", False):
            co.headless(True)

        self.browser = Chromium(co)
        self.current_tab = self.browser.latest_tab

        return {
            "browser_address": self.browser._chromium_options.address,
            "latest_tab_title": self.current_tab.title,
            "latest_tab_id": self.current_tab.tab_id,
        }

    async def new_tab(self, url: str) -> dict:
        """用DrissionPage 控制的浏览器,打开新标签页并 打开一个网址"""
        if not self.browser:
            await self.connect_or_open_browser()
        tab = self.browser.new_tab(url)
        self.current_tab = tab
        return {"title": tab.title, "tab_id": tab.tab_id, "url": tab.url, "dom": self.getSimplifiedDomTree()}

    def wait(self, a: int) -> str:
        """等待a秒"""
        if not self.current_tab: return "没有活动的标签页。"
        self.current_tab.wait(a)
        return f"等待{a}秒成功"

    async def get(self, url: str) -> dict:
        """在当前标签页打开一个网址"""
        if not self.browser:
            await self.connect_or_open_browser()
        self.current_tab.get(url)
        return {"title": self.current_tab.title, "tab_id": self.current_tab.tab_id, "url": self.current_tab.url, "dom": self.getSimplifiedDomTree()}

    # region 上传和下载
    def download_file(self, url: str, path: str, rename: str) -> str:
        """控制浏览器下载文件到指定路径"""
        if not self.current_tab: return "没有活动的标签页。"
        result = self.current_tab.download(file_url=url, save_path=path, rename=rename)
        return str(result)

    def upload_file(self, file_path: str) -> str:
        """点击网页上的 <input type="file"> 元素触发上传文件的操作，上传file_path文件到当前网页"""
        if not self.current_tab: return "没有活动的标签页。"
        x = "//input[@type='file']"
        if e := self.current_tab(f"xpath:{x}"):
            self.current_tab.set.upload_files(file_path)
            e.click(by_js=True)
            self.current_tab.wait.upload_paths_inputted()
            return f"{file_path} 上传成功 {e}"
        else:
            return f"元素{x}不存在，无法触发上传文件"

    @property
    def latest_tab(self) -> ChromiumTab | None:
        """获取最新标签页"""
        if self.browser:
            self.current_tab = self.browser.latest_tab
            return self.current_tab
        return None

    def get_tab_list(self) -> list:
        """获取当前浏览器的所有标签页的信息,包括url, title, id"""
        if not self.browser: return []
        tabs = self.browser.tabs
        tab_list = []
        for tab in tabs:
            info = {
                "url": tab.url,
                "title": tab.title,
                "id": tab.id,
            }
            tab_list.append(info)
        return tab_list

    # region 元素操作
    def is_element_exist(self, xpath: str = "", keyword: str = "") -> bool:
        """通过xpath或者文本节点是否包含关键词判断标签页中某个元素是否存在"""
        if not self.current_tab: return False
        if xpath and self.current_tab.ele(f"xpath:{xpath}", timeout=2):
            return True
        if keyword and self.current_tab.ele(f"text:{keyword}", timeout=2):
            return True
        return False

    def get_elements_by_tagname(self, tagname: str) -> list:
        """获取当前标签页中所有指定tagname的元素信息,返回元素outerHTML列表"""
        if not self.current_tab: return []
        elements = self.current_tab.eles(f'tag:{tagname}')
        return [e.html for e in elements]

    def get_elements_by_keyword(self, keyword: str) -> list:
        """根据关键词获取当前标签页中包含该关键词的文本节点的所有元素列表, 返回元素outerHTML列表"""
        if not self.current_tab: return []
        elements = self.current_tab.eles(f'text:{keyword}')
        return [e.html for e in elements]

    def getInputElementsInfo(self) -> list:
        """获取当前标签页的所有可进行输入操作的元素，对元素进行输入操作前优先使用这个方法"""
        if not self.current_tab: return []
        js_code = '''
        const inputElements = Array.from(document.querySelectorAll('input, select, textarea, button'));
        return inputElements.filter(el => !el.disabled).map(el => el.outerHTML);
        '''
        elements = self.current_tab.run_js(js_code)
        return elements

    def click_by_xpath(self, xpath: str) -> dict:
        """通过xpath点击当前标签页中某个元素"""
        if not self.current_tab: return {"error": "没有活动的标签页。"}
        locator = f"xpath:{xpath}"
        element = self.current_tab.ele(locator, timeout=3)
        if not element: return {"error": f"未找到XPath为 '{xpath}' 的元素。"}
        result = {"locator": locator, "element": str(element), "click_result": element.click()}
        return result

    def click_by_containing_text(self, content: str, index: int = 0) -> str:
        """根据包含指定文本的方式点击网页元素。"""
        if not self.current_tab: return "没有活动的标签页。"
        elements = self.current_tab.eles(f'text:{content}', timeout=3)
        if not elements:
            return f"元素 '{content}' 不存在"
        if len(elements) <= index:
            return f"找到 {len(elements)} 个 '{content}' 元素, 但索引 {index} 超出范围。"
        
        elements[index].click()
        return f"点击第 {index+1} 个 '{content}' 元素成功"

    def input_by_xpath(self, xpath: str, input_value: str, clear_first: bool = True) -> dict:
        """通过xpath给当前标签页中某个元素输入内容"""
        if not self.current_tab: return {"error": "没有活动的标签页。"}
        locator = f"xpath:{xpath}"
        if e := self.current_tab.ele(locator, timeout=4):
            result = {"locator": locator, "result": e.input(input_value, clear=clear_first)}
            return result
        else:
            return {"error": f"未找到XPath为 '{xpath}' 的元素。"}

    def get_current_tab_element_html(self, xpath: str) -> str:
        """获取当前标签页的某个元素的html"""
        if not self.current_tab: return "没有活动的标签页。"
        elem = self.current_tab.ele(f"xpath:{xpath}")
        return elem.html if elem else "未找到元素"

    # endregion

    # region 页面信息与JS
    def get_body_text(self) -> str:
        """获取当前标签页的body的文本内容"""
        if not self.current_tab: return "没有活动的标签页。"
        return self.current_tab('t:body').text

    def get_dom_tree(self, depth: int = -1) -> dict:
        """获取当前标签页的DOM树结构信息"""
        if not self.current_tab: return {"error": "没有活动的标签页。"}
        self.current_tab.run_cdp("DOM.enable")
        return self.current_tab.run_cdp("DOM.getDocument", depth=depth, pierce=True)

    def getSimplifiedDomTree(self) -> dict:
        """获取当前标签页的简化版DOM树"""
        if not self.current_tab: return {"error": "没有活动的标签页。"}
        from CodeBox import domTreeToJson
        return self.current_tab.run_js(domTreeToJson)

    def run_js(self, js_code: str) -> Any:
        """在当前标签页中运行JavaScript代码并返回执行结果"""
        if not self.current_tab: return "没有活动的标签页。"
        return self.current_tab.run_js(js_code)
    # endregion

    # region 按键与滚动
    def send_key(self, key: Literal["Enter", "Backspace", "HOME", "END", "PAGE_UP", "PAGE_DOWN", "DOWN", "UP", "LEFT", "RIGHT", "ESC", "Ctrl+C", "Ctrl+V", "Ctrl+A", "Delete"]) -> str:
        """向当前标签页发送特殊按键"""
        if not self.current_tab: return "没有活动的标签页。"
        key_map = {
            "Enter": Keys.ENTER, "Backspace": Keys.BACKSPACE, "HOME": Keys.HOME, "END": Keys.END,
            "PAGE_UP": Keys.PAGE_UP, "PAGE_DOWN": Keys.PAGE_DOWN, "DOWN": Keys.DOWN, "UP": Keys.UP,
            "LEFT": Keys.LEFT, "RIGHT": Keys.RIGHT, "ESC": Keys.ESCAPE, "Ctrl+C": Keys.CTRL_C,
            "Ctrl+V": Keys.CTRL_V, "Ctrl+A": Keys.CTRL_A, "Delete": Keys.DELETE,
        }
        try:
            self.current_tab.actions.type(key_map.get(key))
            return f"{self.current_tab.title} 网页发送 {key} 键成功"
        except Exception as e:
            return f"{self.current_tab.title} 网页发送 {key} 键失败: {e}"

    def page_down(self) -> str:
        """向当前标签页发送按键 page_down"""
        return self.send_key("PAGE_DOWN")

    def page_up(self) -> str:
        """向当前标签页发送按键 page_up"""
        return self.send_key("PAGE_UP")

    def arrow_down(self) -> str:
        """向当前标签页发送按键 arrow_down"""
        return self.send_key("DOWN")

    def arrow_up(self) -> str:
        """向当前标签页发送按键 arrow_up"""
        return self.send_key("UP")
    # endregion

    # region CDP与监听
    def run_cdp(self, cmd, **cmd_args) -> Any:
        """在当前标签页中运行谷歌CDP协议代码并获取结果"""
        if not self.current_tab: return "没有活动的标签页。"
        return self.current_tab.run_cdp(cmd, **cmd_args)

    def listen_cdp_event(self, event_name: str) -> str:
        """设置监听CDP事件"""
        if not self.current_tab: return "没有活动的标签页。"
        def r(**event):
            self.cdp_event_data.append({"event_name": event_name, "event_data": event})
        try:
            self.current_tab.driver.set_callback(event_name, r)
            return f"CDP 事件 '{event_name}' 的回调设置成功。"
        except Exception as e:
            return str(e)

    def get_cdp_event_data(self) -> list:
        """获取CDP事件回调函数收集到的数据"""
        return self.cdp_event_data

    def response_listener(self, mimeType: str, url_include: str = ".") -> str:
        """开启监听网页接收的数据包"""
        if not self.current_tab: return "没有活动的标签页。"
        self.current_tab.run_cdp("Network.enable")
        def r(**event):
            _url = event.get("response", {}).get("url", "")
            _mimeType = event.get("response", {}).get("mimeType", "")
            if mimeType in _mimeType and url_include in _url:
                self.response_listener_data.append({"event_name": "Network.responseReceived", "event_data": event})
        self.current_tab.driver.set_callback("Network.responseReceived", r)
        return f"开启监听网页接收的数据包, url包含关键字：{url_include}，mimeType：{mimeType}"

    def response_listener_stop(self, clear_data: bool = False) -> str:
        """关闭监听网页发送的数据包"""
        if not self.current_tab: return "没有活动的标签页。"
        self.current_tab.run_cdp("Network.disable")
        if clear_data:
            self.response_listener_data = []
        return f"监听网页发送的数据包关闭成功 ,是否清空数据: {clear_data}"

    def get_response_listener_data(self) -> list:
        """获取监听到的数据,返回数据列表"""
        return self.response_listener_data
    # endregion

    # region 截图与信息
    def get_current_tab_screenshot(self) -> Image:
        """获取当前标签页的网页截图"""
        if not self.current_tab: return Image(data=b"", format="jpeg")
        screenshot_bytes = self.current_tab.get_screenshot(as_bytes='jpeg')
        return Image(data=screenshot_bytes, format="jpeg")

    def get_current_tab_screenshot_as_file(self, path: str = ".", name: str = "screenshot.png") -> str:
        """获取当前标签页的屏幕截图并保存为文件"""
        if not self.current_tab: return "没有活动的标签页。"
        return self.current_tab.get_screenshot(path=path, name=name)

    def get_current_tab_info(self) -> dict:
        """获取当前标签页的信息,包括url, title, id"""
        if not self.current_tab: return {"error": "没有活动的标签页。"}
        return {"url": self.current_tab.url, "title": self.current_tab.title, "id": self.current_tab.tab_id}
    # endregion

    # region 拖动
    def move_to(self, xpath: str) -> dict:
        """鼠标移动悬停到指定xpath的元素上"""
        if not self.current_tab: return {"error": "没有活动的标签页。"}
        locator = f"xpath:{xpath}"
        element = self.current_tab.ele(locator, timeout=3)
        if element:
            element.hover()
            return {"locator": locator, "element": str(element)}
        else:
            return {"error": f"未找到XPath为 '{xpath}' 的元素。"}

    def drag(self, xpath: str, offset_x: int, offset_y: int) -> dict:
        """将元素拖动到指定偏移位置"""
        if not self.current_tab: return {"error": "没有活动的标签页。"}
        if e := self.current_tab.ele(f'xpath:{xpath}', timeout=3):
            e.drag(offset_x, offset_y)
            return {"offset_x": offset_x, "offset_y": offset_y}
        else:
            return {"error": f"未找到XPath为 '{xpath}' 的元素。"}
    # endregion

# region 初始化mcp
mcp = FastMCP("DrissionPageMCP", log_level="ERROR", instructions=提示)
b = DrissionPageMCP()

# Register all public methods of the class as tools
mcp.add_tool(b.get_version)
mcp.add_tool(b.connect_or_open_browser)
mcp.add_tool(b.new_tab)
mcp.add_tool(b.wait)
mcp.add_tool(b.get)
mcp.add_tool(b.download_file)
mcp.add_tool(b.upload_file)
mcp.add_tool(b.get_tab_list)
mcp.add_tool(b.is_element_exist)
mcp.add_tool(b.get_elements_by_tagname)
mcp.add_tool(b.get_elements_by_keyword)
mcp.add_tool(b.getInputElementsInfo)
mcp.add_tool(b.click_by_xpath)
mcp.add_tool(b.click_by_containing_text)
mcp.add_tool(b.input_by_xpath)
mcp.add_tool(b.get_current_tab_element_html)
mcp.add_tool(b.get_body_text)
mcp.add_tool(b.get_dom_tree)
mcp.add_tool(b.getSimplifiedDomTree)
mcp.add_tool(b.run_js)
mcp.add_tool(b.send_key)
mcp.add_tool(b.page_down)
mcp.add_tool(b.page_up)
mcp.add_tool(b.arrow_down)
mcp.add_tool(b.arrow_up)
mcp.add_tool(b.run_cdp)
mcp.add_tool(b.listen_cdp_event)
mcp.add_tool(b.get_cdp_event_data)
mcp.add_tool(b.response_listener)
mcp.add_tool(b.response_listener_stop)
mcp.add_tool(b.get_response_listener_data)
mcp.add_tool(b.get_current_tab_screenshot)
mcp.add_tool(b.get_current_tab_screenshot_as_file)
mcp.add_tool(b.get_current_tab_info)
mcp.add_tool(b.move_to)
mcp.add_tool(b.drag)

# region 保存数据到sqlite (Assuming ToolBox.py exists and is correct)
try:
    from ToolBox import save_dict_to_sqlite
    mcp.add_tool(save_dict_to_sqlite)
except ImportError:
    print("Warning: ToolBox.py or save_dict_to_sqlite not found. Skipping tool.")

def main():
    # 启动MCP服务器
    print("DrissionPage MCP server is running...")
    mcp.run(transport='stdio')

if __name__ == "__main__":
    main()
# endregion