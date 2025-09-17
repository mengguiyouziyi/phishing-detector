#!/usr/bin/env python3
"""
钓鱼网站数据收集脚本
"""

import pandas as pd
import requests
import numpy as np
from urllib.parse import urlparse
import json
import time
import concurrent.futures
from typing import List, Dict, Any
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class PhishingDataCollector:
    """钓鱼网站数据收集器"""

    def __init__(self):
        self.datasets = {
            'uci_phishing': 'https://archive.ics.uci.edu/ml/machine-learning-databases/00379/PhishingData.arff',
            'phishtank': 'https://data.phishtank.com/data/online-valid.json',
            'urlnet': 'https://github.com/mjain0/URLNet/raw/master/URLNet/data/benign_list.txt',
            'kaggle_phishing': 'https://raw.githubusercontent.com/agarwalpooja/Phishing-Website-Detection/master/dataset.csv'
        }

    def download_uci_phishing_data(self) -> pd.DataFrame:
        """下载UCI钓鱼网站数据集"""
        try:
            url = 'https://archive.ics.uci.edu/ml/machine-learning-databases/00379/PhishingData.arff'
            response = requests.get(url)

            # 解析ARFF文件
            lines = response.text.split('\n')
            data_start = False
            data = []

            for line in lines:
                if line.strip().startswith('@data'):
                    data_start = True
                    continue
                if data_start and line.strip():
                    # 处理每一行数据
                    row = line.strip().split(',')
                    data.append(row)

            # 转换为DataFrame
            df = pd.DataFrame(data)
            logger.info(f"UCI数据集下载完成，共 {len(df)} 条记录")
            return df

        except Exception as e:
            logger.error(f"下载UCI数据集失败: {e}")
            return pd.DataFrame()

    def download_phishtank_data(self, limit: int = 1000) -> pd.DataFrame:
        """下载PhishTank钓鱼网站数据"""
        try:
            url = 'https://data.phishtank.com/data/online-valid.json'
            response = requests.get(url)
            data = response.json()

            # 提取URL和其他信息
            phishing_data = []
            for item in data[:limit]:
                phishing_data.append({
                    'url': item.get('url'),
                    'phish_id': item.get('phish_id'),
                    'target': item.get('target'),
                    'verified': item.get('verified'),
                    'verification_time': item.get('verification_time'),
                    'is_phishing': 1
                })

            df = pd.DataFrame(phishing_data)
            logger.info(f"PhishTank数据集下载完成，共 {len(df)} 条记录")
            return df

        except Exception as e:
            logger.error(f"下载PhishTank数据集失败: {e}")
            return pd.DataFrame()

    def download_legitimate_urls(self) -> pd.DataFrame:
        """下载正常网站URL"""
        try:
            # 从Tranco列表获取正常网站
            url = 'https://tranco-list.eu/download/ZQ100000/100000'
            response = requests.get(url)

            legitimate_urls = []
            for line in response.text.strip().split('\n')[:5000]:  # 限制5000个正常网站
                rank, domain = line.split(',')
                legitimate_urls.append({
                    'url': f'http://{domain}',
                    'domain': domain,
                    'rank': int(rank),
                    'is_phishing': 0
                })

            df = pd.DataFrame(legitimate_urls)
            logger.info(f"正常网站数据下载完成，共 {len(df)} 条记录")
            return df

        except Exception as e:
            logger.error(f"下载正常网站数据失败: {e}")
            return pd.DataFrame()

    def generate_synthetic_features(self, url: str) -> Dict[str, Any]:
        """生成URL特征"""
        try:
            parsed = urlparse(url)
            domain = parsed.netloc

            features = {
                'url_length': len(url),
                'domain_length': len(domain),
                'path_length': len(parsed.path),
                'query_length': len(parsed.query),
                'num_dots': url.count('.'),
                'num_hyphens': url.count('-'),
                'num_underscores': url.count('_'),
                'num_slashes': url.count('/'),
                'num_question_marks': url.count('?'),
                'num_equals': url.count('='),
                'num_at_symbols': url.count('@'),
                'num_ampersands': url.count('&'),
                'num_percent': url.count('%'),
                'has_ip_address': self._has_ip_address(domain),
                'has_https': url.startswith('https://'),
                'num_subdomains': len(domain.split('.')) - 1,
                'url_entropy': self._calculate_entropy(url),
                'domain_entropy': self._calculate_entropy(domain),
                'has_suspicious_words': self._has_suspicious_words(url),
                'num_digits': sum(c.isdigit() for c in url),
                'num_letters': sum(c.isalpha() for c in url),
                'digit_letter_ratio': sum(c.isdigit() for c in url) / max(1, sum(c.isalpha() for c in url)),
                'special_char_ratio': sum(not c.isalnum() for c in url) / len(url),
                'has_login_words': self._has_login_keywords(url),
                'has_bank_words': self._has_bank_keywords(url),
                'has_suspicious_tld': self._has_suspicious_tld(domain),
                'is_shortened_url': self._is_shortened_url(url)
            }

            return features

        except Exception as e:
            logger.error(f"生成URL特征失败: {e}")
            return {}

    def _has_ip_address(self, domain: str) -> bool:
        """检查是否包含IP地址"""
        import re
        ip_pattern = r'^\d{1,3}\.\d{1,3}\.\d{1,3}\.\d{1,3}$'
        return bool(re.match(ip_pattern, domain))

    def _calculate_entropy(self, text: str) -> float:
        """计算熵值"""
        if not text:
            return 0.0

        from collections import Counter
        import math

        counts = Counter(text)
        total = len(text)
        entropy = 0.0

        for count in counts.values():
            probability = count / total
            if probability > 0:
                entropy -= probability * math.log2(probability)

        return entropy

    def _has_suspicious_words(self, url: str) -> bool:
        """检查是否包含可疑词汇"""
        suspicious_words = [
            'login', 'signin', 'verify', 'secure', 'account', 'update',
            'confirm', 'banking', 'paypal', 'amazon', 'microsoft',
            'apple', 'google', 'facebook', 'twitter', 'instagram'
        ]

        return any(word.lower() in url.lower() for word in suspicious_words)

    def _has_login_keywords(self, url: str) -> bool:
        """检查是否包含登录相关关键词"""
        login_keywords = ['login', 'signin', 'auth', 'authentication', 'credential']
        return any(keyword in url.lower() for keyword in login_keywords)

    def _has_bank_keywords(self, url: str) -> bool:
        """检查是否包含银行相关关键词"""
        bank_keywords = ['bank', 'payment', 'credit', 'debit', 'transfer', 'wire']
        return any(keyword in url.lower() for keyword in bank_keywords)

    def _has_suspicious_tld(self, domain: str) -> bool:
        """检查是否包含可疑顶级域名"""
        suspicious_tlds = ['.tk', '.ml', '.ga', '.cf', '.xyz', '.top', '.click', '.download']
        return any(domain.endswith(tld) for tld in suspicious_tlds)

    def _is_shortened_url(self, url: str) -> bool:
        """检查是否为短链接"""
        shortened_domains = ['bit.ly', 'tinyurl.com', 'short.link', 'goo.gl', 't.co']
        return any(domain in url for domain in shortened_domains)

    def collect_and_process_data(self) -> pd.DataFrame:
        """收集并处理所有数据"""
        logger.info("开始收集钓鱼网站数据...")

        # 下载各数据集
        uci_data = self.download_uci_phishing_data()
        phishtank_data = self.download_phishtank_data(limit=2000)
        legitimate_data = self.download_legitimate_urls()

        # 合并数据
        all_data = []

        # 处理钓鱼网站数据
        if not phishtank_data.empty:
            for _, row in phishtank_data.iterrows():
                features = self.generate_synthetic_features(row['url'])
                features['is_phishing'] = 1
                features['source'] = 'phishtank'
                all_data.append(features)

        # 处理正常网站数据
        if not legitimate_data.empty:
            for _, row in legitimate_data.iterrows():
                features = self.generate_synthetic_features(row['url'])
                features['is_phishing'] = 0
                features['source'] = 'tranco'
                all_data.append(features)

        # 转换为DataFrame
        df = pd.DataFrame(all_data)

        # 数据清洗
        df = df.dropna()
        df = df[df['url_length'] > 0]

        # 保存数据
        df.to_csv('phishing_dataset.csv', index=False)
        df.to_json('phishing_dataset.json', orient='records', indent=2)

        logger.info(f"数据收集完成，共 {len(df)} 条记录")
        logger.info(f"钓鱼网站: {len(df[df['is_phishing'] == 1])}")
        logger.info(f"正常网站: {len(df[df['is_phishing'] == 0])}")

        return df

    def get_dataset_statistics(self, df: pd.DataFrame) -> Dict[str, Any]:
        """获取数据集统计信息"""
        stats = {
            'total_samples': len(df),
            'phishing_samples': len(df[df['is_phishing'] == 1]),
            'legitimate_samples': len(df[df['is_phishing'] == 0]),
            'phishing_ratio': len(df[df['is_phishing'] == 1]) / len(df),
            'feature_columns': [col for col in df.columns if col not in ['is_phishing', 'source']],
            'missing_values': df.isnull().sum().sum(),
            'data_sources': df['source'].value_counts().to_dict() if 'source' in df.columns else {}
        }

        return stats

if __name__ == "__main__":
    collector = PhishingDataCollector()
    dataset = collector.collect_and_process_data()

    if not dataset.empty:
        stats = collector.get_dataset_statistics(dataset)
        print("📊 数据集统计信息:")
        print(json.dumps(stats, indent=2, ensure_ascii=False))

        # 保存统计信息
        with open('dataset_statistics.json', 'w', encoding='utf-8') as f:
            json.dump(stats, f, indent=2, ensure_ascii=False)

        print("✅ 数据收集完成!")
        print("📁 数据文件: phishing_dataset.csv")
        print("📊 统计信息: dataset_statistics.json")
    else:
        print("❌ 数据收集失败!")