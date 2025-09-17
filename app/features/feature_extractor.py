"""
特征提取器
从网站数据中提取机器学习特征
"""

import re
import json
import hashlib
import math
import logging
from typing import Dict, List, Any, Optional, Tuple
from urllib.parse import urlparse, parse_qs
from bs4 import BeautifulSoup
import numpy as np
from collections import Counter
from ..collectors.web_collector import WebsiteData
from ..database.models import WebsiteFeature

logger = logging.getLogger(__name__)

class FeatureExtractor:
    """特征提取器"""

    def __init__(self):
        self.suspicious_keywords = [
            'login', 'signin', 'password', 'credential', 'account', 'verify',
            'secure', 'bank', 'paypal', 'update', 'confirm', 'urgent',
            'suspended', 'limited', 'verify', 'authentication'
        ]

        self.suspicious_tlds = [
            '.tk', '.ml', '.ga', '.cf', '.gq', '.top', '.click', '.download',
            '.stream', '.science', '.work', '.party', '.trade', '.date'
        ]

        self.safe_domains = [
            'google.com', 'facebook.com', 'twitter.com', 'instagram.com',
            'linkedin.com', 'youtube.com', 'amazon.com', 'microsoft.com',
            'apple.com', 'github.com', 'stackoverflow.com', 'wikipedia.org'
        ]

    def extract_features(self, website_data: WebsiteData) -> Dict[str, Any]:
        """从网站数据中提取所有特征"""
        try:
            features = {}

            # URL特征
            url_features = self._extract_url_features(website_data.url)
            features.update(url_features)

            # HTTP特征
            http_features = self._extract_http_features(website_data)
            features.update(http_features)

            # HTML特征
            html_features = self._extract_html_features(website_data)
            features.update(html_features)

            # 内容特征
            content_features = self._extract_content_features(website_data)
            features.update(content_features)

            # JavaScript特征
            js_features = self._extract_javascript_features(website_data)
            features.update(js_features)

            # 安全特征
            security_features = self._extract_security_features(website_data)
            features.update(security_features)

            # SSL特征
            ssl_features = self._extract_ssl_features(website_data)
            features.update(ssl_features)

            logger.debug(f"特征提取完成: {len(features)} 个特征")
            return features

        except Exception as e:
            logger.error(f"特征提取失败: {e}")
            return {}

    def _extract_url_features(self, url: str) -> Dict[str, Any]:
        """提取URL特征"""
        features = {}

        try:
            parsed = urlparse(url)
            domain = parsed.netloc.lower()
            path = parsed.path
            query = parsed.query

            # 基础长度特征
            features['url_length'] = len(url)
            features['domain_length'] = len(domain)
            features['path_length'] = len(path)
            features['query_length'] = len(query)

            # URL熵（复杂性度量）
            features['url_entropy'] = self._calculate_entropy(url)

            # 域名特征
            features['has_ip_address'] = self._has_ip_address(domain)
            features['num_subdomains'] = self._count_subdomains(domain)
            features['domain_age_months'] = self._estimate_domain_age(domain)

            # 特殊字符
            features['has_at_symbol'] = '@' in url
            features['has_dash_symbol'] = '-' in domain
            features['num_dots'] = url.count('.')

            # 数字和字母特征
            features['num_digits'] = sum(c.isdigit() for c in url)
            features['num_letters'] = sum(c.isalpha() for c in url)
            features['num_special_chars'] = len(re.findall(r'[!@#$%^&*(),.?":{}|<>]', url))

            # URL结构特征
            features['has_port'] = parsed.port is not None
            features['has_fragment'] = bool(parsed.fragment)
            features['num_params'] = len(parse_qs(query))

            # 可疑域名检查
            features['has_suspicious_tld'] = any(domain.endswith(tld) for tld in self.suspicious_tlds)
            features['is_safe_domain'] = domain in self.safe_domains
            features['domain_similarity'] = self._calculate_domain_similarity(domain)

            # HTTPS特征
            features['is_https'] = url.startswith('https://')
            features['has_hsts'] = 'hsts' in domain.lower()

        except Exception as e:
            logger.warning(f"URL特征提取失败: {e}")
            # 设置默认值
            features.update({
                'url_length': 0, 'domain_length': 0, 'path_length': 0, 'query_length': 0,
                'url_entropy': 0.0, 'has_ip_address': False, 'num_subdomains': 0,
                'domain_age_months': 0, 'has_at_symbol': False, 'has_dash_symbol': False,
                'num_dots': 0, 'num_digits': 0, 'num_letters': 0, 'num_special_chars': 0,
                'has_port': False, 'has_fragment': False, 'num_params': 0,
                'has_suspicious_tld': False, 'is_safe_domain': False, 'domain_similarity': 0.0,
                'is_https': False, 'has_hsts': False
            })

        return features

    def _extract_http_features(self, website_data: WebsiteData) -> Dict[str, Any]:
        """提取HTTP响应头特征"""
        features = {}

        try:
            headers = website_data.headers

            # 状态码分类
            status_code = website_data.status_code
            features['status_code_category'] = status_code // 100  # 2xx, 3xx, 4xx, 5xx
            features['is_redirect'] = 300 <= status_code < 400
            features['is_error'] = status_code >= 400

            # 安全相关头
            features['has_content_security_policy'] = 'Content-Security-Policy' in headers
            features['has_x_frame_options'] = 'X-Frame-Options' in headers
            features['has_strict_transport_security'] = 'Strict-Transport-Security' in headers
            features['has_x_content_type_options'] = 'X-Content-Type-Options' in headers
            features['has_x_xss_protection'] = 'X-XSS-Protection' in headers

            # Cookie特征
            features['num_cookies'] = len(website_data.cookies)
            features['has_secure_cookie'] = any('secure' in cookie.lower() for cookie in website_data.cookies.values())
            features['has_http_only_cookie'] = any('httponly' in cookie.lower() for cookie in website_data.cookies.values())

            # 服务器信息
            server = headers.get('server', '').lower()
            features['has_known_server'] = any(srv in server for srv in ['apache', 'nginx', 'iis'])
            features['is_cloudflare'] = 'cloudflare' in server

            # 内容类型
            content_type = headers.get('content-type', '').lower()
            features['is_html_content'] = 'text/html' in content_type
            features['has_charset'] = 'charset=' in content_type

            # 缓存控制
            cache_control = headers.get('cache-control', '').lower()
            features['has_no_cache'] = 'no-cache' in cache_control
            features['has_no_store'] = 'no-store' in cache_control

            # 内容长度
            features['content_length_log'] = math.log1p(website_data.content_length)

            # 响应时间
            features['response_time_log'] = math.log1p(website_data.response_time)

        except Exception as e:
            logger.warning(f"HTTP特征提取失败: {e}")
            # 设置默认值
            features.update({
                'status_code_category': 0, 'is_redirect': False, 'is_error': False,
                'has_content_security_policy': False, 'has_x_frame_options': False,
                'has_strict_transport_security': False, 'has_x_content_type_options': False,
                'has_x_xss_protection': False, 'num_cookies': 0, 'has_secure_cookie': False,
                'has_http_only_cookie': False, 'has_known_server': False, 'is_cloudflare': False,
                'is_html_content': False, 'has_charset': False, 'has_no_cache': False,
                'has_no_store': False, 'content_length_log': 0.0, 'response_time_log': 0.0
            })

        return features

    def _extract_html_features(self, website_data: WebsiteData) -> Dict[str, Any]:
        """提取HTML结构特征"""
        features = {}

        try:
            soup = BeautifulSoup(website_data.html_content, 'lxml')

            # Meta标签
            meta_tags = soup.find_all('meta')
            features['num_meta_tags'] = len(meta_tags)
            features['has_description_meta'] = any(
                meta.get('name', '').lower() == 'description' for meta in meta_tags
            )
            features['has_keywords_meta'] = any(
                meta.get('name', '').lower() == 'keywords' for meta in meta_tags
            )

            # 外部资源
            features['num_external_scripts'] = len(website_data.external_scripts)
            features['num_external_stylesheets'] = len(website_data.external_stylesheets)

            # 表单特征
            features['num_forms'] = len(website_data.forms)
            features['has_password_form'] = any(form['has_password'] for form in website_data.forms)
            features['has_login_form'] = any(
                'login' in form['action'].lower() or 'signin' in form['action'].lower()
                for form in website_data.forms
            )

            # 链接特征
            all_links = website_data.links
            features['num_links'] = len(all_links)

            if all_links:
                domain = urlparse(website_data.url).netloc.lower()
                internal_links = [link for link in all_links if domain in link.lower()]
                features['num_internal_links'] = len(internal_links)
                features['num_external_links'] = len(all_links) - len(internal_links)
                features['internal_link_ratio'] = len(internal_links) / len(all_links)
            else:
                features['num_internal_links'] = 0
                features['num_external_links'] = 0
                features['internal_link_ratio'] = 0.0

            # 图片特征
            images = soup.find_all('img')
            features['num_images'] = len(images)
            features['has_external_images'] = any(
                not img.get('src', '').startswith('/') for img in images if img.get('src')
            )

            # Iframe特征
            iframes = soup.find_all('iframe')
            features['num_iframes'] = len(iframes)
            features['has_hidden_iframes'] = any(
                iframe.get('style', '').lower().find('display:none') != -1 or
                iframe.get('hidden') is not None
                for iframe in iframes
            )

            # 脚本特征
            scripts = soup.find_all('script')
            features['num_scripts'] = len(scripts)
            features['num_inline_scripts'] = len([s for s in scripts if not s.get('src')])

        except Exception as e:
            logger.warning(f"HTML特征提取失败: {e}")
            # 设置默认值
            features.update({
                'num_meta_tags': 0, 'has_description_meta': False, 'has_keywords_meta': False,
                'num_external_scripts': 0, 'num_external_stylesheets': 0, 'num_forms': 0,
                'has_password_form': False, 'has_login_form': False, 'num_links': 0,
                'num_internal_links': 0, 'num_external_links': 0, 'internal_link_ratio': 0.0,
                'num_images': 0, 'has_external_images': False, 'num_iframes': 0,
                'has_hidden_iframes': False, 'num_scripts': 0, 'num_inline_scripts': 0
            })

        return features

    def _extract_content_features(self, website_data: WebsiteData) -> Dict[str, Any]:
        """提取内容特征"""
        features = {}

        try:
            # 标题特征
            title = website_data.title
            features['title_length'] = len(title)
            features['has_title'] = bool(title.strip())

            # 内容长度
            content = website_data.html_content
            features['content_length'] = len(content)
            features['content_length_log'] = math.log1p(len(content))

            # 文本内容（去除HTML标签）
            text_content = self._extract_text(content)
            features['text_length'] = len(text_content)
            features['text_to_html_ratio'] = len(text_content) / max(len(content), 1)

            # 词频特征
            words = text_content.split()
            features['num_words'] = len(words)
            features['avg_word_length'] = np.mean([len(word) for word in words]) if words else 0

            # 可疑关键词
            text_lower = text_content.lower()
            features['has_suspicious_keywords'] = any(keyword in text_lower for keyword in self.suspicious_keywords)
            features['suspicious_keyword_count'] = sum(text_lower.count(keyword) for keyword in self.suspicious_keywords)

            # 表情符号和特殊字符
            features['has_emoji'] = len(re.findall(r'[\U0001F600-\U0001F64F]', text_content)) > 0
            features['exclamation_count'] = text_content.count('!')
            features['question_count'] = text_content.count('?')

            # 大写字母比例
            if text_content:
                uppercase_count = sum(1 for c in text_content if c.isupper())
                features['uppercase_ratio'] = uppercase_count / len(text_content)
            else:
                features['uppercase_ratio'] = 0.0

        except Exception as e:
            logger.warning(f"内容特征提取失败: {e}")
            # 设置默认值
            features.update({
                'title_length': 0, 'has_title': False, 'content_length': 0, 'content_length_log': 0.0,
                'text_length': 0, 'text_to_html_ratio': 0.0, 'num_words': 0, 'avg_word_length': 0.0,
                'has_suspicious_keywords': False, 'suspicious_keyword_count': 0, 'has_emoji': False,
                'exclamation_count': 0, 'question_count': 0, 'uppercase_ratio': 0.0
            })

        return features

    def _extract_javascript_features(self, website_data: WebsiteData) -> Dict[str, Any]:
        """提取JavaScript特征"""
        features = {}

        try:
            soup = BeautifulSoup(website_data.html_content, 'lxml')

            # 获取所有脚本内容
            scripts = []
            for script in soup.find_all('script'):
                if script.string:
                    scripts.append(script.string)

            js_content = ' '.join(scripts).lower()

            # 混淆检测
            features['has_obfuscated_js'] = self._detect_obfuscation(js_content)
            features['has_eval_function'] = 'eval(' in js_content
            features['has_document_write'] = 'document.write' in js_content
            features['has_inner_html'] = 'innerhtml' in js_content

            # 可疑函数
            features['has_escape_function'] = 'escape(' in js_content
            features['has_unescape_function'] = 'unescape(' in js_content
            features['has_fromcharcode'] = 'fromcharcode' in js_content

            # 重定向特征
            features['has_location_replace'] = 'location.replace' in js_content
            features['has_window_location'] = 'window.location' in js_content

            # 表单操作
            features['has_form_submission'] = 'submit(' in js_content or '.submit' in js_content

            # 加密相关
            features['has_crypto_terms'] = any(term in js_content for term in ['md5', 'sha1', 'sha256', 'encrypt', 'decrypt'])

            # 事件监听器
            features['has_event_listeners'] = 'addeventlistener' in js_content or 'attachEvent' in js_content

            # 长度特征
            features['js_content_length'] = len(js_content)
            features['js_content_length_log'] = math.log1p(len(js_content))

        except Exception as e:
            logger.warning(f"JavaScript特征提取失败: {e}")
            # 设置默认值
            features.update({
                'has_obfuscated_js': False, 'has_eval_function': False, 'has_document_write': False,
                'has_inner_html': False, 'has_escape_function': False, 'has_unescape_function': False,
                'has_fromcharcode': False, 'has_location_replace': False, 'has_window_location': False,
                'has_form_submission': False, 'has_crypto_terms': False, 'has_event_listeners': False,
                'js_content_length': 0, 'js_content_length_log': 0.0
            })

        return features

    def _extract_security_features(self, website_data: WebsiteData) -> Dict[str, Any]:
        """提取安全特征"""
        features = {}

        try:
            # Meta标签中的安全信息
            meta_tags = website_data.meta_tags
            features['has_no_index'] = meta_tags.get('robots', '').lower() == 'noindex'
            features['has_no_follow'] = meta_tags.get('robots', '').lower() == 'nofollow'

            # 隐藏元素检测
            soup = BeautifulSoup(website_data.html_content, 'lxml')
            hidden_elements = soup.find_all(style=re.compile(r'display\s*:\s*none|visibility\s*:\s*hidden'))
            features['has_hidden_elements'] = len(hidden_elements) > 0

            # 弹窗检测
            features['has_popup_code'] = 'window.open' in website_data.html_content.lower()
            features['has_alert_code'] = 'alert(' in website_data.html_content.lower()

            # 重定向检测
            features['has_meta_refresh'] = any(
                tag.get('http-equiv', '').lower() == 'refresh' for tag in soup.find_all('meta')
            )

            # 框架检测
            features['has_frameset'] = bool(soup.find('frameset'))

            # Base href检测
            base_tag = soup.find('base')
            features['has_base_href'] = base_tag is not None and base_tag.get('href')
            if features['has_base_href']:
                base_href = base_tag.get('href')
                domain = urlparse(website_data.url).netloc
                features['base_href_external'] = domain not in base_href
            else:
                features['base_href_external'] = False

        except Exception as e:
            logger.warning(f"安全特征提取失败: {e}")
            # 设置默认值
            features.update({
                'has_no_index': False, 'has_no_follow': False, 'has_hidden_elements': False,
                'has_popup_code': False, 'has_alert_code': False, 'has_meta_refresh': False,
                'has_frameset': False, 'has_base_href': False, 'base_href_external': False
            })

        return features

    def _extract_ssl_features(self, website_data: WebsiteData) -> Dict[str, Any]:
        """提取SSL特征"""
        features = {}

        try:
            ssl_info = website_data.ssl_info
            if ssl_info:
                features['has_ssl'] = True
                features['ssl_valid_days'] = ssl_info.get('valid_days', 0)
                features['ssl_is_valid'] = ssl_info.get('is_valid', True)
                features['ssl_expires_soon'] = ssl_info.get('valid_days', 365) < 30

                # 证书颁发者
                issuer = ssl_info.get('issuer', {})
                features['ssl_issuer_known'] = any(
                    ca in issuer.values() for ca in [
                        'Let\'s Encrypt', 'DigiCert', 'Comodo', 'Symantec',
                        'GoDaddy', 'GlobalSign', 'RapidSSL'
                    ]
                )

                # 证书主题
                subject = ssl_info.get('subject', {})
                features['ssl_subject_matches_domain'] = any(
                    domain_part in str(subject.values()).lower()
                    for domain_part in urlparse(website_data.url).netloc.split('.')
                )
            else:
                features.update({
                    'has_ssl': False, 'ssl_valid_days': 0, 'ssl_is_valid': False,
                    'ssl_expires_soon': True, 'ssl_issuer_known': False,
                    'ssl_subject_matches_domain': False
                })

        except Exception as e:
            logger.warning(f"SSL特征提取失败: {e}")
            # 设置默认值
            features.update({
                'has_ssl': False, 'ssl_valid_days': 0, 'ssl_is_valid': False,
                'ssl_expires_soon': True, 'ssl_issuer_known': False,
                'ssl_subject_matches_domain': False
            })

        return features

    def _calculate_entropy(self, text: str) -> float:
        """计算文本熵"""
        if not text:
            return 0.0

        # 计算字符频率
        char_counts = Counter(text)
        total_chars = len(text)

        # 计算熵
        entropy = 0.0
        for count in char_counts.values():
            probability = count / total_chars
            entropy -= probability * math.log2(probability)

        return entropy

    def _has_ip_address(self, domain: str) -> bool:
        """检查是否为IP地址"""
        ip_pattern = r'^\d{1,3}\.\d{1,3}\.\d{1,3}\.\d{1,3}$'
        return bool(re.match(ip_pattern, domain))

    def _count_subdomains(self, domain: str) -> int:
        """计算子域名数量"""
        parts = domain.split('.')
        return len(parts) - 2 if len(parts) > 2 else 0

    def _estimate_domain_age(self, domain: str) -> int:
        """估算域名年龄（月）"""
        # 这里是一个简化的估算，实际应该查询WHOIS数据库
        try:
            # 简单启发式：较长的域名通常是新的
            domain_length = len(domain)
            if domain_length > 20:
                return 3  # 3个月
            elif domain_length > 15:
                return 6  # 6个月
            else:
                return 12  # 12个月
        except:
            return 6  # 默认6个月

    def _calculate_domain_similarity(self, domain: str) -> float:
        """计算与知名域名的相似度"""
        max_similarity = 0.0
        for safe_domain in self.safe_domains:
            similarity = self._string_similarity(domain, safe_domain)
            max_similarity = max(max_similarity, similarity)
        return max_similarity

    def _string_similarity(self, s1: str, s2: str) -> float:
        """计算字符串相似度（编辑距离）"""
        from difflib import SequenceMatcher
        return SequenceMatcher(None, s1, s2).ratio()

    def _detect_obfuscation(self, js_content: str) -> bool:
        """检测JavaScript混淆"""
        if not js_content:
            return False

        # 检测混淆的常见特征
        obfuscation_patterns = [
            r'\\x[0-9a-fA-F]{2}',  # 十六进制转义
            r'\\u[0-9a-fA-F]{4}',  # Unicode转义
            r'[a-zA-Z_$][a-zA-Z0-9_$]*\s*=\s*function',  # 匿名函数
            r'eval\s*\(',  # eval函数
            r'document\.write\s*\(',  # document.write
            r'fromCharCode\s*\(',  # fromCharCode
        ]

        return any(re.search(pattern, js_content) for pattern in obfuscation_patterns)

    def _extract_text(self, html_content: str) -> str:
        """从HTML中提取纯文本"""
        try:
            soup = BeautifulSoup(html_content, 'lxml')
            # 移除script和style标签
            for script in soup(["script", "style"]):
                script.decompose()
            return soup.get_text(separator=' ', strip=True)
        except:
            return ""

    def create_feature_vector(self, features: Dict[str, Any]) -> np.ndarray:
        """将特征字典转换为numpy数组"""
        # 定义特征顺序
        feature_order = [
            # URL特征
            'url_length', 'domain_length', 'url_entropy', 'has_ip_address',
            'num_subdomains', 'domain_age_months', 'has_at_symbol', 'has_dash_symbol',
            'num_dots', 'num_digits', 'num_letters', 'num_special_chars',
            'has_port', 'has_fragment', 'num_params', 'has_suspicious_tld',
            'is_safe_domain', 'domain_similarity', 'is_https', 'has_hsts',

            # HTTP特征
            'status_code_category', 'is_redirect', 'is_error',
            'has_content_security_policy', 'has_x_frame_options',
            'has_strict_transport_security', 'has_x_content_type_options',
            'has_x_xss_protection', 'num_cookies', 'has_secure_cookie',
            'has_http_only_cookie', 'has_known_server', 'is_cloudflare',
            'is_html_content', 'has_charset', 'has_no_cache', 'has_no_store',
            'content_length_log', 'response_time_log',

            # HTML特征
            'num_meta_tags', 'has_description_meta', 'has_keywords_meta',
            'num_external_scripts', 'num_external_stylesheets', 'num_forms',
            'has_password_form', 'has_login_form', 'num_links',
            'num_internal_links', 'num_external_links', 'internal_link_ratio',
            'num_images', 'has_external_images', 'num_iframes',
            'has_hidden_iframes', 'num_scripts', 'num_inline_scripts',

            # 内容特征
            'title_length', 'has_title', 'content_length', 'content_length_log',
            'text_length', 'text_to_html_ratio', 'num_words', 'avg_word_length',
            'has_suspicious_keywords', 'suspicious_keyword_count', 'has_emoji',
            'exclamation_count', 'question_count', 'uppercase_ratio',

            # JavaScript特征
            'has_obfuscated_js', 'has_eval_function', 'has_document_write',
            'has_inner_html', 'has_escape_function', 'has_unescape_function',
            'has_fromcharcode', 'has_location_replace', 'has_window_location',
            'has_form_submission', 'has_crypto_terms', 'has_event_listeners',
            'js_content_length', 'js_content_length_log',

            # 安全特征
            'has_no_index', 'has_no_follow', 'has_hidden_elements',
            'has_popup_code', 'has_alert_code', 'has_meta_refresh',
            'has_frameset', 'has_base_href', 'base_href_external',

            # SSL特征
            'has_ssl', 'ssl_valid_days', 'ssl_is_valid', 'ssl_expires_soon',
            'ssl_issuer_known', 'ssl_subject_matches_domain'
        ]

        # 创建特征向量
        feature_vector = []
        for feature_name in feature_order:
            value = features.get(feature_name, 0)
            feature_vector.append(value)

        return np.array(feature_vector)

    def get_feature_names(self) -> List[str]:
        """获取特征名称列表"""
        return [
            # URL特征
            'url_length', 'domain_length', 'url_entropy', 'has_ip_address',
            'num_subdomains', 'domain_age_months', 'has_at_symbol', 'has_dash_symbol',
            'num_dots', 'num_digits', 'num_letters', 'num_special_chars',
            'has_port', 'has_fragment', 'num_params', 'has_suspicious_tld',
            'is_safe_domain', 'domain_similarity', 'is_https', 'has_hsts',

            # HTTP特征
            'status_code_category', 'is_redirect', 'is_error',
            'has_content_security_policy', 'has_x_frame_options',
            'has_strict_transport_security', 'has_x_content_type_options',
            'has_x_xss_protection', 'num_cookies', 'has_secure_cookie',
            'has_http_only_cookie', 'has_known_server', 'is_cloudflare',
            'is_html_content', 'has_charset', 'has_no_cache', 'has_no_store',
            'content_length_log', 'response_time_log',

            # HTML特征
            'num_meta_tags', 'has_description_meta', 'has_keywords_meta',
            'num_external_scripts', 'num_external_stylesheets', 'num_forms',
            'has_password_form', 'has_login_form', 'num_links',
            'num_internal_links', 'num_external_links', 'internal_link_ratio',
            'num_images', 'has_external_images', 'num_iframes',
            'has_hidden_iframes', 'num_scripts', 'num_inline_scripts',

            # 内容特征
            'title_length', 'has_title', 'content_length', 'content_length_log',
            'text_length', 'text_to_html_ratio', 'num_words', 'avg_word_length',
            'has_suspicious_keywords', 'suspicious_keyword_count', 'has_emoji',
            'exclamation_count', 'question_count', 'uppercase_ratio',

            # JavaScript特征
            'has_obfuscated_js', 'has_eval_function', 'has_document_write',
            'has_inner_html', 'has_escape_function', 'has_unescape_function',
            'has_fromcharcode', 'has_location_replace', 'has_window_location',
            'has_form_submission', 'has_crypto_terms', 'has_event_listeners',
            'js_content_length', 'js_content_length_log',

            # 安全特征
            'has_no_index', 'has_no_follow', 'has_hidden_elements',
            'has_popup_code', 'has_alert_code', 'has_meta_refresh',
            'has_frameset', 'has_base_href', 'base_href_external',

            # SSL特征
            'has_ssl', 'ssl_valid_days', 'ssl_is_valid', 'ssl_expires_soon',
            'ssl_issuer_known', 'ssl_subject_matches_domain'
        ]