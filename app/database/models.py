"""
数据库模型定义
用于存储网站特征数据和模型训练信息
"""

from sqlalchemy import Column, Integer, String, Text, Float, DateTime, Boolean, JSON, ForeignKey, Index
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import relationship
from datetime import datetime
import json

Base = declarative_base()

class Website(Base):
    """网站基本信息表"""
    __tablename__ = 'websites'

    id = Column(Integer, primary_key=True, autoincrement=True)
    url = Column(String(2048), unique=True, nullable=False, index=True)
    domain = Column(String(255), nullable=False, index=True)
    title = Column(String(500))
    status_code = Column(Integer)
    content_type = Column(String(100))
    content_length = Column(Integer)
    collection_time = Column(DateTime, default=datetime.utcnow, index=True)
    last_updated = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    is_phishing = Column(Boolean, nullable=True)  # 标签：是否为钓鱼网站
    confidence_score = Column(Float)  # 模型置信度分数
    fingerprint = Column(String(64), unique=True, index=True)
    is_active = Column(Boolean, default=True)

    # 关联关系
    http_headers = relationship("HTTPHeader", back_populates="website", cascade="all, delete-orphan")
    meta_tags = relationship("MetaTag", back_populates="website", cascade="all, delete-orphan")
    external_resources = relationship("ExternalResource", back_populates="website", cascade="all, delete-orphan")
    features = relationship("WebsiteFeature", back_populates="website", cascade="all, delete-orphan")
    ssl_info = relationship("SSLInfo", back_populates="website", uselist=False, cascade="all, delete-orphan")

class HTTPHeader(Base):
    """HTTP响应头表"""
    __tablename__ = 'http_headers'

    id = Column(Integer, primary_key=True, autoincrement=True)
    website_id = Column(Integer, ForeignKey('websites.id'), nullable=False)
    header_name = Column(String(100), nullable=False)
    header_value = Column(Text)
    created_at = Column(DateTime, default=datetime.utcnow)

    # 关联关系
    website = relationship("Website", back_populates="http_headers")

    # 索引
    __table_args__ = (
        Index('idx_website_header', 'website_id', 'header_name'),
    )

class MetaTag(Base):
    """Meta标签表"""
    __tablename__ = 'meta_tags'

    id = Column(Integer, primary_key=True, autoincrement=True)
    website_id = Column(Integer, ForeignKey('websites.id'), nullable=False)
    name = Column(String(100), nullable=False)
    content = Column(Text)
    created_at = Column(DateTime, default=datetime.utcnow)

    # 关联关系
    website = relationship("Website", back_populates="meta_tags")

    # 索引
    __table_args__ = (
        Index('idx_website_meta', 'website_id', 'name'),
    )

class ExternalResource(Base):
    """外部资源表（JavaScript、CSS等）"""
    __tablename__ = 'external_resources'

    id = Column(Integer, primary_key=True, autoincrement=True)
    website_id = Column(Integer, ForeignKey('websites.id'), nullable=False)
    resource_type = Column(String(20), nullable=False)  # 'script', 'stylesheet', 'image', etc.
    resource_url = Column(String(2048), nullable=False)
    domain = Column(String(255))
    is_external = Column(Boolean, default=True)
    content_length = Column(Integer)
    created_at = Column(DateTime, default=datetime.utcnow)

    # 关联关系
    website = relationship("Website", back_populates="external_resources")

    # 索引
    __table_args__ = (
        Index('idx_website_resource', 'website_id', 'resource_type'),
        Index('idx_resource_domain', 'domain'),
    )

class SSLInfo(Base):
    """SSL证书信息表"""
    __tablename__ = 'ssl_info'

    id = Column(Integer, primary_key=True, autoincrement=True)
    website_id = Column(Integer, ForeignKey('websites.id'), nullable=False, unique=True)
    issuer = Column(JSON)
    subject = Column(JSON)
    version = Column(String(10))
    serial_number = Column(String(128))
    not_before = Column(DateTime)
    not_after = Column(DateTime)
    valid_days = Column(Integer)
    is_valid = Column(Boolean, default=True)
    created_at = Column(DateTime, default=datetime.utcnow)

    # 关联关系
    website = relationship("Website", back_populates="ssl_info")

class WebsiteFeature(Base):
    """网站特征表 - 用于机器学习"""
    __tablename__ = 'website_features'

    id = Column(Integer, primary_key=True, autoincrement=True)
    website_id = Column(Integer, ForeignKey('websites.id'), nullable=False, unique=True)

    # 基础特征
    url_length = Column(Integer)
    domain_length = Column(Integer)
    url_entropy = Column(Float)
    has_ip_address = Column(Boolean)
    num_subdomains = Column(Integer)
    has_at_symbol = Column(Boolean)
    has_dash_symbol = Column(Boolean)

    # URL结构特征
    num_special_chars = Column(Integer)
    num_digits = Column(Integer)
    num_uppercase = Column(Integer)
    num_lowercase = Column(Integer)

    # HTTP特征
    status_code_category = Column(Integer)  # 2xx, 3xx, 4xx, 5xx
    has_content_security_policy = Column(Boolean)
    has_x_frame_options = Column(Boolean)
    has_strict_transport_security = Column(Boolean)
    has_x_content_type_options = Column(Boolean)
    num_cookies = Column(Integer)
    has_secure_cookie = Column(Boolean)
    has_http_only_cookie = Column(Boolean)

    # HTML特征
    num_meta_tags = Column(Integer)
    num_external_scripts = Column(Integer)
    num_external_stylesheets = Column(Integer)
    num_forms = Column(Integer)
    has_password_form = Column(Boolean)
    num_links = Column(Integer)
    num_internal_links = Column(Integer)
    num_external_links = Column(Integer)

    # 内容特征
    title_length = Column(Integer)
    content_length = Column(Integer)
    text_to_html_ratio = Column(Float)
    num_words = Column(Integer)
    avg_word_length = Column(Float)

    # JavaScript特征
    has_obfuscated_js = Column(Boolean)
    num_inline_scripts = Column(Integer)
    has_eval_function = Column(Boolean)
    has_document_write = Column(Boolean)

    # 安全特征
    has_suspicious_keywords = Column(Boolean)
    num_suspicious_iframes = Column(Integer)
    has_hidden_elements = Column(Boolean)

    # 创建和更新时间
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    # 关联关系
    website = relationship("Website", back_populates="features")

class TrainingDataset(Base):
    """训练数据集表"""
    __tablename__ = 'training_datasets'

    id = Column(Integer, primary_key=True, autoincrement=True)
    name = Column(String(100), nullable=False)
    description = Column(Text)
    version = Column(String(20), nullable=False)
    total_samples = Column(Integer)
    phishing_samples = Column(Integer)
    legitimate_samples = Column(Integer)
    features_used = Column(JSON)
    created_at = Column(DateTime, default=datetime.utcnow)
    is_active = Column(Boolean, default=True)

class Model(Base):
    """机器学习模型表"""
    __tablename__ = 'models'

    id = Column(Integer, primary_key=True, autoincrement=True)
    name = Column(String(100), nullable=False)
    version = Column(String(20), nullable=False)
    algorithm = Column(String(50), nullable=False)  # random_forest, xgboost, neural_network, etc.
    accuracy = Column(Float)
    precision = Column(Float)
    recall = Column(Float)
    f1_score = Column(Float)
    auc_score = Column(Float)
    feature_importance = Column(JSON)
    hyperparameters = Column(JSON)
    training_dataset_id = Column(Integer, ForeignKey('training_datasets.id'))
    model_path = Column(String(500))
    created_at = Column(DateTime, default=datetime.utcnow)
    is_active = Column(Boolean, default=True)
    deployment_status = Column(String(20), default='training')  # training, deployed, deprecated

    # 关联关系
    training_dataset = relationship("TrainingDataset")

class Prediction(Base):
    """预测记录表"""
    __tablename__ = 'predictions'

    id = Column(Integer, primary_key=True, autoincrement=True)
    website_id = Column(Integer, ForeignKey('websites.id'), nullable=False)
    model_id = Column(Integer, ForeignKey('models.id'), nullable=False)
    predicted_label = Column(Boolean, nullable=False)  # True: phishing, False: legitimate
    confidence_score = Column(Float, nullable=False)
    prediction_time = Column(DateTime, default=datetime.utcnow, index=True)
    features_used = Column(JSON)
    processing_time = Column(Float)  # 毫秒

    # 关联关系
    website = relationship("Website")
    model = relationship("Model")

class CollectionTask(Base):
    """数据收集任务表"""
    __tablename__ = 'collection_tasks'

    id = Column(Integer, primary_key=True, autoincrement=True)
    task_name = Column(String(100), nullable=False)
    description = Column(Text)
    status = Column(String(20), default='pending')  # pending, running, completed, failed
    total_urls = Column(Integer, default=0)
    processed_urls = Column(Integer, default=0)
    failed_urls = Column(Integer, default=0)
    start_time = Column(DateTime)
    end_time = Column(DateTime)
    created_by = Column(String(100))
    created_at = Column(DateTime, default=datetime.utcnow)
    config = Column(JSON)

class CollectionLog(Base):
    """数据收集日志表"""
    __tablename__ = 'collection_logs'

    id = Column(Integer, primary_key=True, autoincrement=True)
    task_id = Column(Integer, ForeignKey('collection_tasks.id'), nullable=True)
    url = Column(String(2048))
    status = Column(String(20))  # success, failed, timeout, redirect
    error_message = Column(Text)
    response_time = Column(Float)
    status_code = Column(Integer)
    log_time = Column(DateTime, default=datetime.utcnow, index=True)

    # 索引
    __table_args__ = (
        Index('idx_task_status', 'task_id', 'status'),
    )

class SystemMetrics(Base):
    """系统指标表"""
    __tablename__ = 'system_metrics'

    id = Column(Integer, primary_key=True, autoincrement=True)
    metric_name = Column(String(50), nullable=False)
    metric_value = Column(Float, nullable=False)
    timestamp = Column(DateTime, default=datetime.utcnow, index=True)
    metric_data = Column(JSON)

# 创建索引的辅助函数
def create_indexes(engine):
    """创建额外的索引"""
    indexes = [
        # 性能优化索引
        Index('idx_websites_domain_status', Website.domain, Website.is_phishing),
        Index('idx_websites_collection_time', Website.collection_time.desc()),
        Index('idx_features_url_entropy', WebsiteFeature.url_entropy),
        Index('idx_predictions_confidence', Prediction.confidence_score.desc()),
        Index('idx_system_metrics_time', SystemMetrics.timestamp.desc()),
    ]

    for index in indexes:
        try:
            index.create(engine)
        except Exception as e:
            print(f"创建索引失败: {e}")

# 数据库初始化SQL
INIT_SQL = """
-- 创建数据库（如果不存在）
CREATE DATABASE IF NOT EXISTS phishing_detector CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;

USE phishing_detector;

-- 创建用户和权限（如果需要）
-- CREATE USER IF NOT EXISTS 'phishing_user'@'%' IDENTIFIED BY 'your_password';
-- GRANT ALL PRIVILEGES ON phishing_detector.* TO 'phishing_user'@'%';
-- FLUSH PRIVILEGES;
"""