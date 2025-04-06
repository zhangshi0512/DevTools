#!/usr/bin/env python
# -*- coding: utf-8 -*-

import tkinter as tk
from tkinter import scrolledtext, ttk, messagebox, filedialog
import requests
import json
import time
import os
import threading
import queue
import concurrent.futures
import logging
from datetime import datetime
from functools import partial
from bs4 import BeautifulSoup
from langchain.llms.base import LLM
from langchain.prompts import PromptTemplate
from langchain.chains import LLMChain
from pydantic import Field
import configparser
import sqlite3

# 配置日志系统
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler("deepsearch.log"),
        logging.StreamHandler()
    ]
)

logger = logging.getLogger("DeepSearch")

# -----------------------------
# 配置管理类
# -----------------------------


class Config:
    def __init__(self, config_file="deepsearch_config.ini"):
        self.config_file = config_file
        self.config = configparser.ConfigParser()

        # 默认配置
        self.default_config = {
            'Search': {
                'engine': 'bing',
                'num_results': '5',
                'timeout': '10',
                'user_agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/114.0.0.0 Safari/537.36'
            },
            'LLM': {
                'model': 'qwen2.5:7b',
                'api_url': 'http://localhost:11434/api/generate',
                'temperature': '0.7',
                'max_tokens': '2048'
            },
            'UI': {
                'theme': 'default',
                'font': 'Arial 10',
                'history_size': '100'
            }
        }

        self.load_config()

    def load_config(self):
        # 加载配置文件，如果不存在则创建默认配置
        if os.path.exists(self.config_file):
            self.config.read(self.config_file)
            logger.info(f"配置已从 {self.config_file} 加载")
        else:
            for section, options in self.default_config.items():
                if not self.config.has_section(section):
                    self.config.add_section(section)
                for option, value in options.items():
                    self.config.set(section, option, value)
            self.save_config()
            logger.info(f"已创建默认配置文件 {self.config_file}")

    def save_config(self):
        with open(self.config_file, 'w') as f:
            self.config.write(f)
        logger.info(f"配置已保存到 {self.config_file}")

    def get(self, section, option, fallback=None):
        return self.config.get(section, option, fallback=fallback)

    def set(self, section, option, value):
        if not self.config.has_section(section):
            self.config.add_section(section)
        self.config.set(section, option, value)

    def get_int(self, section, option, fallback=None):
        return self.config.getint(section, option, fallback=fallback)

    def get_float(self, section, option, fallback=None):
        return self.config.getfloat(section, option, fallback=fallback)

    def get_boolean(self, section, option, fallback=None):
        return self.config.getboolean(section, option, fallback=fallback)

# -----------------------------
# 搜索引擎接口类
# -----------------------------


class SearchEngine:
    def __init__(self, config):
        self.config = config
        self.headers = {
            "User-Agent": config.get('Search', 'user_agent')
        }
        self.timeout = config.get_int('Search', 'timeout', fallback=10)

    def search(self, query, num_results=5):
        """根据配置选择搜索引擎执行搜索"""
        engine = self.config.get('Search', 'engine', fallback='bing').lower()

        if engine == 'bing':
            return self.search_bing(query, num_results)
        elif engine == 'google':
            return self.search_google(query, num_results)
        elif engine == 'duckduckgo':
            return self.search_duckduckgo(query, num_results)
        else:
            logger.warning(f"未知搜索引擎: {engine}，默认使用 Bing")
            return self.search_bing(query, num_results)

    def search_bing(self, query, num_results=5):
        """
        使用 Bing 搜索引擎获取搜索结果
        """
        base_url = "https://www.bing.com/search"
        params = {"q": query, "count": num_results}
        try:
            response = requests.get(
                base_url,
                headers=self.headers,
                params=params,
                timeout=self.timeout
            )
            response.raise_for_status()

            soup = BeautifulSoup(response.text, "html.parser")
            possible_selectors = [".b_algo", ".b_ans", ".b_ad"]
            items = []

            for selector in possible_selectors:
                items.extend(soup.select(selector))

            # 移除重复项目并只取前 num_results 项
            items = list(dict.fromkeys(items))[:num_results]
            results = []

            for item in items:
                # 提取标题
                title_element = item.select_one("h2 a") or item.select_one(
                    "h2") or item.select_one("a")
                title = title_element.get_text(strip=True) if title_element and title_element.get_text(
                    strip=True) else item.get_text(strip=True)[:80]

                # 提取链接
                if title_element and title_element.name == "a" and title_element.has_attr("href"):
                    link = title_element["href"]
                else:
                    a_fallback = item.select_one("a[href]")
                    link = a_fallback["href"] if a_fallback else "No link"

                # 移除脚本和样式元素
                for tag in item(["script", "style"]):
                    tag.extract()

                snippet_element = item.select_one(".b_caption p")
                snippet = snippet_element.get_text(" ", strip=True) if snippet_element and snippet_element.get_text(
                    strip=True) else item.get_text(" ", strip=True)

                results.append({
                    "title": title,
                    "url": link,
                    "snippet": snippet
                })

            return results

        except requests.exceptions.RequestException as e:
            logger.error(f"Bing 搜索请求失败: {e}")
            return {"error": f"搜索请求失败: {e}"}
        except Exception as e:
            logger.error(f"Bing 搜索结果解析失败: {e}")
            return {"error": f"搜索结果解析失败: {e}"}

    def search_google(self, query, num_results=5):
        """
        使用 Google 搜索引擎获取搜索结果
        注意：Google 可能会阻止自动化请求，这里仅作为示例
        """
        logger.info("Google 搜索暂未实现，使用 Bing 替代")
        return self.search_bing(query, num_results)

    def search_duckduckgo(self, query, num_results=5):
        """
        使用 DuckDuckGo 搜索引擎获取搜索结果
        注意：这是简化实现，可能需要更多适配
        """
        logger.info("DuckDuckGo 搜索暂未实现，使用 Bing 替代")
        return self.search_bing(query, num_results)

    def fetch_page_content(self, url):
        """获取网页完整内容"""
        if not url.startswith("http"):
            return "无效或缺失 URL"

        try:
            response = requests.get(
                url, headers=self.headers, timeout=self.timeout)
            response.raise_for_status()
            response.encoding = response.apparent_encoding

            soup = BeautifulSoup(response.text, "html.parser")

            # 移除脚本和样式标签
            for script_or_style in soup(["script", "style"]):
                script_or_style.extract()

            # 识别常见内容标签
            common_tags = ["p", "div", "section", "article", "span",
                           "li", "blockquote", "h1", "h2", "h3", "h4", "h5", "h6"]
            content_elements = soup.find_all(common_tags)
            text_list = [elem.get_text(
                strip=True) for elem in content_elements if elem.get_text(strip=True)]

            return "\n".join(text_list) if text_list else "未在多个标签中找到文本内容。"

        except requests.exceptions.RequestException as e:
            logger.error(f"获取页面内容失败 ({url}): {e}")
            return f"网络错误: {e}"
        except Exception as e:
            logger.error(f"解析页面内容失败 ({url}): {e}")
            return f"解析错误: {e}"

# -----------------------------
# 搜索结果处理类
# -----------------------------


class SearchProcessor:
    def __init__(self, search_engine, config):
        self.search_engine = search_engine
        self.config = config
        self.result_cache = {}  # 简单的缓存机制

    def search_fulltext(self, query, num_results=None):
        """
        执行搜索并获取完整页面内容
        """
        if num_results is None:
            num_results = self.config.get_int(
                'Search', 'num_results', fallback=5)

        # 检查缓存
        cache_key = f"{query}_{num_results}"
        if cache_key in self.result_cache:
            logger.info(f"从缓存获取搜索结果: {query}")
            return self.result_cache[cache_key]

        results = self.search_engine.search(query, num_results)

        if isinstance(results, dict) and "error" in results:
            return results

        # 使用线程池并行获取页面内容
        with concurrent.futures.ThreadPoolExecutor(max_workers=5) as executor:
            # 提交所有任务
            future_to_result = {
                executor.submit(self.search_engine.fetch_page_content, r["url"]): r
                for r in results
            }

            # 处理完成的任务
            for future in concurrent.futures.as_completed(future_to_result):
                result = future_to_result[future]
                try:
                    full_text = future.result()
                    result["full_text"] = full_text
                except Exception as e:
                    logger.error(f"获取完整文本失败: {e}")
                    result["full_text"] = f"获取内容失败: {e}"

        # 缓存结果
        self.result_cache[cache_key] = results
        return results

    def format_results(self, results, max_full_text_length=300):
        """
        将搜索结果格式化为便于阅读的文本
        """
        if isinstance(results, dict) and "error" in results:
            return results["error"]

        if not isinstance(results, list):
            return str(results)

        out_lines = []
        for i, r in enumerate(results, start=1):
            full_text = r.get("full_text", "")
            if len(full_text) > max_full_text_length:
                full_text = full_text[:max_full_text_length] + "..."

            out_lines.append(
                f"结果 {i}:\n"
                f"  - 标题: {r.get('title', 'N/A')}\n"
                f"  - URL: {r.get('url', 'N/A')}\n"
                f"  - 摘要: {r.get('snippet', 'N/A')}\n"
                f"  - 全文 (截断): {full_text}\n"
            )

        return "\n".join(out_lines)

    def export_results(self, results, export_format="txt"):
        """
        导出搜索结果为不同格式
        """
        if export_format == "txt":
            return self.format_results(results)
        elif export_format == "json":
            return json.dumps(results, ensure_ascii=False, indent=2)
        elif export_format == "markdown":
            md_lines = ["# 搜索结果\n"]

            for i, r in enumerate(results, start=1):
                md_lines.append(f"## 结果 {i}: {r.get('title', 'N/A')}")
                md_lines.append(
                    f"[{r.get('url', 'N/A')}]({r.get('url', 'N/A')})")
                md_lines.append(f"\n### 摘要\n{r.get('snippet', 'N/A')}")
                md_lines.append(
                    f"\n### 页面内容\n{r.get('full_text', 'N/A')[:500]}...\n")

            return "\n".join(md_lines)
        else:
            return f"不支持的导出格式: {export_format}"

# -----------------------------
# 本地 LLM 接口类
# -----------------------------


class OllamaLLM(LLM):
    model: str = Field(default="qwen2.5:7b", description="Ollama 模型名称")
    api_url: str = Field(
        default="http://localhost:11434/api/generate", description="Ollama API 端点")
    temperature: float = Field(default=0.7, description="生成温度")
    max_tokens: int = Field(default=2048, description="最大生成 token 数")

    @property
    def _llm_type(self) -> str:
        return "ollama"

    def _call(self, prompt: str, stop=None) -> str:
        payload = {
            "model": self.model,
            "prompt": prompt,
            "stop": stop,
            "temperature": self.temperature,
            "max_tokens": self.max_tokens
        }

        try:
            response = requests.post(self.api_url, json=payload, stream=True)
            response.raise_for_status()

            complete_text = ""
            for line in response.iter_lines():
                if line:
                    try:
                        obj = json.loads(line.decode("utf-8")
                                         if isinstance(line, bytes) else line)
                    except json.JSONDecodeError:
                        continue

                    complete_text += obj.get("response", "")

                    if obj.get("done", False):
                        break

            return complete_text

        except requests.exceptions.RequestException as e:
            logger.error(f"LLM API 调用失败: {e}")
            return f"LLM API 调用错误: {e}"
        except Exception as e:
            logger.error(f"LLM 处理失败: {e}")
            return f"LLM 处理错误: {e}"

# -----------------------------
# 查询历史数据库管理类
# -----------------------------


class HistoryDB:
    def __init__(self, db_file="deepsearch_history.db"):
        self.db_file = db_file
        self.init_db()

    def init_db(self):
        """初始化数据库表结构"""
        try:
            conn = sqlite3.connect(self.db_file)
            cursor = conn.cursor()

            # 创建历史记录表
            cursor.execute('''
            CREATE TABLE IF NOT EXISTS search_history (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                query TEXT NOT NULL,
                timestamp TEXT NOT NULL,
                engine TEXT,
                results TEXT,
                analysis TEXT
            )
            ''')

            conn.commit()
            conn.close()
            logger.info("历史数据库初始化成功")
        except Exception as e:
            logger.error(f"历史数据库初始化失败: {e}")

    def add_history(self, query, results=None, analysis=None, engine="bing"):
        """添加新的搜索历史记录"""
        try:
            timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            results_json = json.dumps(results) if results else None

            conn = sqlite3.connect(self.db_file)
            cursor = conn.cursor()

            cursor.execute(
                "INSERT INTO search_history (query, timestamp, engine, results, analysis) VALUES (?, ?, ?, ?, ?)",
                (query, timestamp, engine, results_json, analysis)
            )

            conn.commit()
            conn.close()
            logger.info(f"已添加历史记录: {query}")
            return True
        except Exception as e:
            logger.error(f"添加历史记录失败: {e}")
            return False

    def get_history(self, limit=100):
        """获取最近的搜索历史记录"""
        try:
            conn = sqlite3.connect(self.db_file)
            cursor = conn.cursor()

            cursor.execute(
                "SELECT id, query, timestamp FROM search_history ORDER BY timestamp DESC LIMIT ?",
                (limit,)
            )

            records = cursor.fetchall()
            conn.close()

            return [{"id": r[0], "query": r[1], "timestamp": r[2]} for r in records]
        except Exception as e:
            logger.error(f"获取历史记录失败: {e}")
            return []

    def get_history_detail(self, history_id):
        """获取指定历史记录的详细信息"""
        try:
            conn = sqlite3.connect(self.db_file)
            cursor = conn.cursor()

            cursor.execute(
                "SELECT query, timestamp, engine, results, analysis FROM search_history WHERE id = ?",
                (history_id,)
            )

            record = cursor.fetchone()
            conn.close()

            if record:
                results = json.loads(record[3]) if record[3] else None
                return {
                    "query": record[0],
                    "timestamp": record[1],
                    "engine": record[2],
                    "results": results,
                    "analysis": record[4]
                }
            else:
                return None
        except Exception as e:
            logger.error(f"获取历史记录详情失败: {e}")
            return None

    def delete_history(self, history_id):
        """删除指定的历史记录"""
        try:
            conn = sqlite3.connect(self.db_file)
            cursor = conn.cursor()

            cursor.execute(
                "DELETE FROM search_history WHERE id = ?", (history_id,))

            conn.commit()
            conn.close()
            logger.info(f"已删除历史记录 ID: {history_id}")
            return True
        except Exception as e:
            logger.error(f"删除历史记录失败: {e}")
            return False

    def clear_history(self):
        """清空所有历史记录"""
        try:
            conn = sqlite3.connect(self.db_file)
            cursor = conn.cursor()

            cursor.execute("DELETE FROM search_history")

            conn.commit()
            conn.close()
            logger.info("已清空所有历史记录")
            return True
        except Exception as e:
            logger.error(f"清空历史记录失败: {e}")
            return False

# -----------------------------
# 深度搜索分析类
# -----------------------------


class DeepSearchAnalyzer:
    def __init__(self, config, search_processor, history_db=None):
        self.config = config
        self.search_processor = search_processor
        self.history_db = history_db

        # 初始化 LLM
        self.llm = OllamaLLM(
            model=config.get('LLM', 'model', fallback='qwen2.5:7b'),
            api_url=config.get(
                'LLM', 'api_url', fallback='http://localhost:11434/api/generate'),
            temperature=config.get_float('LLM', 'temperature', fallback=0.7),
            max_tokens=config.get_int('LLM', 'max_tokens', fallback=2048)
        )

        # 初始化提示模板
        self.init_prompt_templates()

    def init_prompt_templates(self):
        """初始化不同类型的提示模板"""
        # 默认分析模板
        self.default_prompt = PromptTemplate(
            template=(
                "根据以下实时搜索结果：\n\n{search_results}\n\n"
                "以及用户查询：{query}\n\n"
                "请进行深度搜索分析并生成详细的纯文本报告。"
                "报告必须格式化为带有清晰标题和要点的正常文档。"
                "报告应包含三个部分：\n"
                "1. 查询\n"
                "2. 实时搜索结果（列出每个结果的标题、URL 和摘要）\n"
                "3. 深度搜索分析（详细总结）\n\n"
                "请确保分析准确、全面且无偏见。提供具体事实和来源，而非一般性陈述。"
                "不要包含任何 JSON 格式、字典键、大括号、引号或转义字符。"
                "仅输出看起来像典型报告的纯文本。"
            ),
            input_variables=["search_results", "query"]
        )

        # 学术研究模板
        self.academic_prompt = PromptTemplate(
            template=(
                "根据以下实时学术搜索结果：\n\n{search_results}\n\n"
                "以及研究查询：{query}\n\n"
                "请提供深度学术分析，专注于研究方法、关键发现和学术共识。"
                "请生成一份结构化学术报告，包含：\n"
                "1. 研究问题概述\n"
                "2. 方法学分析\n"
                "3. 关键发现与趋势\n"
                "4. 研究差距和未来方向\n"
                "5. 结论\n\n"
                "请使用学术风格，注重精确引用关键论点的来源。"
                "输出应为纯文本格式，适合学术评论。"
            ),
            input_variables=["search_results", "query"]
        )

        # 技术分析模板
        self.tech_prompt = PromptTemplate(
            template=(
                "根据以下关于技术主题的搜索结果：\n\n{search_results}\n\n"
                "以及技术查询：{query}\n\n"
                "请提供深入的技术分析报告，包含：\n"
                "1. 技术概述和背景\n"
                "2. 核心技术原理分析\n"
                "3. 应用场景和实施细节\n"
                "4. 优势、局限性和替代方案\n"
                "5. 未来发展趋势\n\n"
                "请确保分析是技术准确的，提供具体的代码示例或架构细节（如适用）。"
                "输出应为结构化的纯文本技术报告。"
            ),
            input_variables=["search_results", "query"]
        )

        # 新闻分析模板
        self.news_prompt = PromptTemplate(
            template=(
                "根据以下新闻搜索结果：\n\n{search_results}\n\n"
                "以及新闻查询：{query}\n\n"
                "请提供全面的新闻分析报告，包含：\n"
                "1. 事件摘要\n"
                "2. 关键事实和时间线\n"
                "3. 不同信息来源的观点比较\n"
                "4. 背景和上下文\n"
                "5. 可能的影响和后续发展\n\n"
                "请确保分析平衡客观，区分事实和观点，并标明不同来源的信息。"
                "输出应为纯文本格式，像一篇专业的新闻分析文章。"
            ),
            input_variables=["search_results", "query"]
        )

    def analyze(self, query, query_type="default"):
        """执行深度搜索并生成分析报告"""
        # 1. 执行搜索
        search_results = self.search_processor.search_fulltext(query)

        if isinstance(search_results, dict) and "error" in search_results:
            return {"error": search_results["error"]}

        # 2. 格式化搜索结果
        formatted_results = self.search_processor.format_results(
            search_results)

        # 3. 选择合适的提示模板
        if query_type == "academic":
            prompt_template = self.academic_prompt
        elif query_type == "tech":
            prompt_template = self.tech_prompt
        elif query_type == "news":
            prompt_template = self.news_prompt
        else:
            prompt_template = self.default_prompt

        # 4. 创建 LLM 链
        chain = LLMChain(llm=self.llm, prompt=prompt_template)

        # 5. 执行分析
        try:
            analysis_result = chain.invoke(
                {"search_results": formatted_results, "query": query})

            # 6. 保存到历史记录
            if self.history_db:
                self.history_db.add_history(
                    query=query,
                    results=search_results,
                    analysis=analysis_result,
                    engine=self.config.get('Search', 'engine', fallback='bing')
                )

            return {
                "query": query,
                "results": search_results,
                "analysis": analysis_result,
                "formatted_results": formatted_results
            }
        except Exception as e:
            logger.error(f"LLM 分析失败: {e}")
            return {"error": f"分析过程中出错: {e}"}

# -----------------------------
# GUI 应用类
# -----------------------------


class DeepSearchApp(tk.Tk):
    def __init__(self):
        super().__init__()

        # 初始化配置
        self.config_manager = Config()

        # 设置窗口
        self.title("DeepSearch - 搜索增强分析工具")
        self.geometry("1000x800")

        # 初始化搜索组件
        self.search_engine = SearchEngine(self.config_manager)
        self.search_processor = SearchProcessor(
            self.search_engine, self.config_manager)
        self.history_db = HistoryDB()
        self.analyzer = DeepSearchAnalyzer(
            self.config_manager, self.search_processor, self.history_db)

        # 状态变量
        self.is_searching = False
        self.search_queue = queue.Queue()
        self.current_query = None
        self.current_results = None

        # 创建界面组件
        self.create_widgets()

        # 启动后台处理线程
        self.process_thread = threading.Thread(
            target=self.process_search_queue, daemon=True)
        self.process_thread.start()

        # 加载历史记录
        self.load_history()

    def create_widgets(self):
        # 创建菜单栏
        self.create_menu()

        # 顶部查询区域
        self.create_query_frame()

        # 中间分隔区域，包含历史记录和输出
        self.main_paned = ttk.PanedWindow(self, orient=tk.HORIZONTAL)
        self.main_paned.pack(fill=tk.BOTH, expand=True, padx=10, pady=5)

        # 左侧历史记录区域
        self.create_history_frame()

        # 右侧结果区域
        self.create_results_frame()

        # 底部状态栏
        self.create_status_bar()

    def create_menu(self):
        menubar = tk.Menu(self)

        # 文件菜单
        file_menu = tk.Menu(menubar, tearoff=0)
        file_menu.add_command(label="导出结果...", command=self.export_results)
        file_menu.add_command(label="设置...", command=self.show_settings)
        file_menu.add_separator()
        file_menu.add_command(label="退出", command=self.quit)
        menubar.add_cascade(label="文件", menu=file_menu)

        # 编辑菜单
        edit_menu = tk.Menu(menubar, tearoff=0)
        edit_menu.add_command(label="复制", command=self.copy_selected)
        edit_menu.add_command(label="清除历史", command=self.clear_history)
        menubar.add_cascade(label="编辑", menu=edit_menu)

        # 查询类型菜单
        query_menu = tk.Menu(menubar, tearoff=0)
        query_menu.add_command(
            label="普通查询", command=lambda: self.set_query_type("default"))
        query_menu.add_command(
            label="学术研究", command=lambda: self.set_query_type("academic"))
        query_menu.add_command(
            label="技术分析", command=lambda: self.set_query_type("tech"))
        query_menu.add_command(
            label="新闻分析", command=lambda: self.set_query_type("news"))
        menubar.add_cascade(label="查询类型", menu=query_menu)

        # 帮助菜单
        help_menu = tk.Menu(menubar, tearoff=0)
        help_menu.add_command(label="使用说明", command=self.show_help)
        help_menu.add_command(label="关于", command=self.show_about)
        menubar.add_cascade(label="帮助", menu=help_menu)

        self.config(menu=menubar)
