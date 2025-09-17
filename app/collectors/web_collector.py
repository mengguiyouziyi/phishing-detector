"""
网站数据收集器
负责收集网站的基本属性、HTTP响应头、内容特征等数据
"""

import asyncio
import aiohttp
import json
import time
import logging
from typing import Dict, List, Optional, Any
from urllib.parse import urlparse, urljoin
from bs4 import BeautifulSoup
import hashlib
import re
from dataclasses import dataclass
from datetime import datetime
import ssl

@dataclass
class WebsiteData:
    """网站数据结构"""
    url: str
    title: str
    headers: Dict[str, str]
    status_code: int
    content_type: str
    content_length: int
    cookies: Dict[str, str]
    html_content: str
    meta_tags: Dict[str, str]
    external_scripts: List[str]
    external_stylesheets: List[str]
    fingerprint: str
    collection_time: datetime
    response_time: float
    ssl_info: Optional[Dict[str, Any]] = None
    redirects: List[str] = None
    forms: List[Dict[str, Any]] = None
    links: List[str] = None

    def __post_init__(self):
        if self.redirects is None:
            self.redirects = []
        if self.forms is None:
            self.forms = []
        if self.links is None:
            self.links = []

class WebDataCollector:
    """网站数据收集器"""

    def __init__(self, config: Dict[str, Any]):
        self.config = config
        self.session = None
        self.logger = logging.getLogger(__name__)

        # 设置User-Agent和请求头
        self.headers = {
            'User-Agent': config.get('user_agent', 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'),
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8',
            'Accept-Language': 'en-US,en;q=0.5',
            'Accept-Encoding': 'gzip, deflate',
            'Connection': 'keep-alive',
        }

    async def __aenter__(self):
        """异步上下文管理器入口"""
        timeout = aiohttp.ClientTimeout(total=self.config.get('request_timeout', 30))
        connector = aiohttp.TCPConnector(
            limit=100,
            limit_per_host=10,
            ttl_dns_cache=300,
            use_dns_cache=True,
            ssl=False if not self.config.get('verify_ssl', True) else None
        )

        self.session = aiohttp.ClientSession(
            timeout=timeout,
            connector=connector,
            headers=self.headers
        )
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        """异步上下文管理器出口"""
        if self.session:
            await self.session.close()

    async def collect_website_data(self, url: str) -> Optional[WebsiteData]:
        """收集网站数据"""
        try:
            start_time = time.time()

            # 发送HTTP请求
            async with self.session.get(url, allow_redirects=self.config.get('follow_redirects', True)) as response:
                response_time = time.time() - start_time

                # 获取响应头
                headers = dict(response.headers)

                # 获取Cookie
                cookies = {}
                for cookie in response.cookies:
                    cookies[cookie.key] = cookie.value

                # 获取内容类型和长度
                content_type = headers.get('Content-Type', '').split(';')[0]
                content_length = int(headers.get('Content-Length', 0))

                # 读取HTML内容
                html_content = await response.text()

                # 如果是重定向，记录重定向链
                redirects = []
                if response.history:
                    redirects = [str(resp.url) for resp in response.history]

                # 解析HTML内容
                soup = BeautifulSoup(html_content, 'lxml')

                # 提取各种特征
                title = self._extract_title(soup)
                meta_tags = self._extract_meta_tags(soup)
                external_scripts = self._extract_external_scripts(soup, url)
                external_stylesheets = self._extract_external_stylesheets(soup, url)
                forms = self._extract_forms(soup)
                links = self._extract_links(soup, url)

                # 生成指纹
                fingerprint = self._generate_fingerprint(url, headers, html_content)

                # 获取SSL信息
                ssl_info = None
                if url.startswith('https://'):
                    ssl_info = await self._get_ssl_info(url)

                website_data = WebsiteData(
                    url=url,
                    title=title,
                    headers=headers,
                    status_code=response.status,
                    content_type=content_type,
                    content_length=content_length,
                    cookies=cookies,
                    html_content=html_content,
                    meta_tags=meta_tags,
                    external_scripts=external_scripts,
                    external_stylesheets=external_stylesheets,
                    fingerprint=fingerprint,
                    collection_time=datetime.now(),
                    response_time=response_time,
                    ssl_info=ssl_info,
                    redirects=redirects,
                    forms=forms,
                    links=links
                )

                self.logger.info(f"成功收集网站数据: {url}")
                return website_data

        except Exception as e:
            self.logger.error(f"收集网站数据失败 {url}: {e}")
            return None

    def _extract_title(self, soup: BeautifulSoup) -> str:
        """提取网页标题"""
        title_tag = soup.find('title')
        return title_tag.get_text().strip() if title_tag else ""

    def _extract_meta_tags(self, soup: BeautifulSoup) -> Dict[str, str]:
        """提取Meta标签"""
        meta_tags = {}

        for meta in soup.find_all('meta'):
            name = meta.get('name') or meta.get('property') or meta.get('http-equiv')
            content = meta.get('content', '')

            if name and content:
                meta_tags[name.lower()] = content

        return meta_tags

    def _extract_external_scripts(self, soup: BeautifulSoup, base_url: str) -> List[str]:
        """提取外部JavaScript链接"""
        scripts = []

        for script in soup.find_all('script', src=True):
            src = script.get('src')
            if src:
                # 转换为绝对URL
                absolute_url = urljoin(base_url, src)
                scripts.append(absolute_url)

        return scripts

    def _extract_external_stylesheets(self, soup: BeautifulSoup, base_url: str) -> List[str]:
        """提取外部CSS链接"""
        stylesheets = []

        for link in soup.find_all('link', rel='stylesheet'):
            href = link.get('href')
            if href:
                # 转换为绝对URL
                absolute_url = urljoin(base_url, href)
                stylesheets.append(absolute_url)

        return stylesheets

    def _extract_forms(self, soup: BeautifulSoup) -> List[Dict[str, Any]]:
        """提取表单信息"""
        forms = []

        for form in soup.find_all('form'):
            form_data = {
                'action': form.get('action', ''),
                'method': form.get('method', 'get').lower(),
                'fields': [],
                'has_password': False
            }

            # 提取表单字段
            for input_field in form.find_all(['input', 'textarea', 'select']):
                field_type = input_field.get('type', 'text')
                field_name = input_field.get('name', '')

                if field_name:
                    form_data['fields'].append({
                        'name': field_name,
                        'type': field_type
                    })

                    if field_type == 'password':
                        form_data['has_password'] = True

            forms.append(form_data)

        return forms

    def _extract_links(self, soup: BeautifulSoup, base_url: str) -> List[str]:
        """提取页面链接"""
        links = []

        for link in soup.find_all('a', href=True):
            href = link.get('href')
            if href and href.startswith(('http://', 'https://')):
                links.append(href)

        return links[:50]  # 限制链接数量

    def _generate_fingerprint(self, url: str, headers: Dict[str, str], html_content: str) -> str:
        """生成网站指纹"""
        # 组合多个特征生成唯一指纹
        fingerprint_data = f"{url}|{headers.get('server', '')}|{headers.get('x-powered-by', '')}|{len(html_content)}"

        # 使用SHA256生成指纹
        return hashlib.sha256(fingerprint_data.encode('utf-8')).hexdigest()

    async def _get_ssl_info(self, url: str) -> Optional[Dict[str, Any]]:
        """获取SSL证书信息"""
        try:
            parsed_url = urlparse(url)
            hostname = parsed_url.hostname

            if not hostname:
                return None

            # 创建SSL上下文
            context = ssl.create_default_context()
            context.check_hostname = False
            context.verify_mode = ssl.CERT_NONE

            # 获取SSL证书信息
            with context.wrap_socket(ssl.socket(), server_hostname=hostname) as s:
                s.connect((hostname, 443))
                cert = s.getpeercert()

                if cert:
                    return {
                        'issuer': dict(x[0] for x in cert.get('issuer', [])),
                        'subject': dict(x[0] for x in cert.get('subject', [])),
                        'version': cert.get('version'),
                        'serial_number': cert.get('serialNumber'),
                        'not_before': cert.get('notBefore'),
                        'not_after': cert.get('notAfter'),
                        'valid_days': self._calculate_ssl_validity(cert)
                    }

        except Exception as e:
            self.logger.warning(f"获取SSL信息失败 {url}: {e}")

        return None

    def _calculate_ssl_validity(self, cert: Dict[str, Any]) -> int:
        """计算SSL证书有效天数"""
        try:
            from datetime import datetime
            not_after = cert.get('notAfter', '')
            if not_after:
                # 解析日期格式，例如: 'Dec 31 23:59:59 2024 GMT'
                expiry_date = datetime.strptime(not_after, '%b %d %H:%M:%S %Y %Z')
                days_left = (expiry_date - datetime.now()).days
                return max(0, days_left)
        except:
            pass
        return 0

class BatchDataCollector:
    """批量数据收集器"""

    def __init__(self, config: Dict[str, Any]):
        self.config = config
        self.logger = logging.getLogger(__name__)
        self.collector = WebDataCollector(config)

    async def collect_batch(self, urls: List[str], max_concurrent: int = 10) -> List[WebsiteData]:
        """批量收集网站数据"""
        self.logger.info(f"开始批量收集 {len(urls)} 个网站")

        # 创建信号量控制并发
        semaphore = asyncio.Semaphore(max_concurrent)

        async def collect_with_semaphore(url: str) -> Optional[WebsiteData]:
            async with semaphore:
                return await self.collector.collect_website_data(url)

        # 创建任务列表
        tasks = [collect_with_semaphore(url) for url in urls]

        # 执行所有任务
        results = await asyncio.gather(*tasks, return_exceptions=True)

        # 过滤结果
        website_data_list = []
        for i, result in enumerate(results):
            if isinstance(result, WebsiteData):
                website_data_list.append(result)
            elif isinstance(result, Exception):
                self.logger.error(f"收集 {urls[i]} 失败: {result}")

        self.logger.info(f"批量收集完成，成功收集 {len(website_data_list)} 个网站")
        return website_data_list

    async def collect_from_file(self, file_path: str) -> List[WebsiteData]:
        """从文件中读取URL列表并收集数据"""
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                urls = [line.strip() for line in f if line.strip() and not line.startswith('#')]

            return await self.collect_batch(urls)

        except Exception as e:
            self.logger.error(f"从文件读取URL失败: {e}")
            return []

    async def collect_from_database(self, db_connector) -> List[WebsiteData]:
        """从数据库中读取URL列表并收集数据"""
        try:
            # 这里可以从数据库获取URL列表
            urls = await db_connector.get_pending_urls(limit=1000)
            return await self.collect_batch(urls)

        except Exception as e:
            self.logger.error(f"从数据库读取URL失败: {e}")
            return []