"""
数据库连接和会话管理
"""

import logging
from sqlalchemy import create_engine, MetaData
from sqlalchemy.orm import sessionmaker, scoped_session
from sqlalchemy.pool import QueuePool
from contextlib import contextmanager
import yaml
import os
from typing import Generator
from .models import Base, create_indexes

logger = logging.getLogger(__name__)

class DatabaseManager:
    """数据库管理器"""

    def __init__(self, config_path: str = "config/settings.yaml"):
        self.config = self._load_config(config_path)
        self.engine = None
        self.SessionLocal = None
        self.session_factory = None

    def _load_config(self, config_path: str) -> dict:
        """加载配置文件"""
        try:
            with open(config_path, 'r', encoding='utf-8') as f:
                config = yaml.safe_load(f)
            return config.get('database', {})
        except FileNotFoundError:
            logger.error(f"配置文件 {config_path} 不存在")
            return {}

    def get_connection_string(self) -> str:
        """获取数据库连接字符串"""
        db_config = self.config

        # 支持环境变量覆盖
        host = os.getenv('DB_HOST', db_config.get('host', 'localhost'))
        port = os.getenv('DB_PORT', db_config.get('port', 3306))
        database = os.getenv('DB_NAME', db_config.get('name', 'phishing_detector'))
        username = os.getenv('DB_USER', db_config.get('user', 'root'))
        password = os.getenv('DB_PASSWORD', db_config.get('password', ''))

        connection_string = f"mysql+pymysql://{username}:{password}@{host}:{port}/{database}?charset=utf8mb4"

        logger.info(f"数据库连接: {host}:{port}/{database}")
        return connection_string

    def initialize(self):
        """初始化数据库连接"""
        try:
            connection_string = self.get_connection_string()

            # 创建引擎
            self.engine = create_engine(
                connection_string,
                poolclass=QueuePool,
                pool_size=self.config.get('pool_size', 20),
                max_overflow=self.config.get('max_overflow', 30),
                pool_pre_ping=True,
                pool_recycle=3600,
                echo=False  # 设置为True可以看到SQL语句
            )

            # 创建会话工厂
            self.session_factory = sessionmaker(bind=self.engine)
            self.SessionLocal = scoped_session(self.session_factory)

            # 创建所有表
            Base.metadata.create_all(bind=self.engine)

            # 创建额外索引
            create_indexes(self.engine)

            logger.info("数据库初始化完成")

        except Exception as e:
            logger.error(f"数据库初始化失败: {e}")
            raise

    @contextmanager
    def get_session(self) -> Generator:
        """获取数据库会话上下文管理器"""
        if not self.SessionLocal:
            self.initialize()

        session = self.SessionLocal()
        try:
            yield session
            session.commit()
        except Exception as e:
            session.rollback()
            logger.error(f"数据库操作失败: {e}")
            raise
        finally:
            session.close()

    def get_session_factory(self):
        """获取会话工厂"""
        if not self.SessionLocal:
            self.initialize()
        return self.SessionLocal

    def close(self):
        """关闭数据库连接"""
        if self.SessionLocal:
            self.SessionLocal.remove()
        if self.engine:
            self.engine.dispose()
        logger.info("数据库连接已关闭")

    def execute_raw_sql(self, sql: str, params: dict = None):
        """执行原始SQL"""
        with self.get_session() as session:
            result = session.execute(sql, params or {})
            return result.fetchall()

    def backup_database(self, backup_path: str):
        """备份数据库"""
        try:
            import subprocess
            import datetime

            db_config = self.config
            timestamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
            backup_file = f"{backup_path}/phishing_detector_{timestamp}.sql"

            command = [
                "mysqldump",
                f"-h{db_config.get('host')}",
                f"-P{db_config.get('port')}",
                f"-u{db_config.get('user')}",
                f"-p{db_config.get('password')}",
                db_config.get('name'),
                f"--result-file={backup_file}",
                "--single-transaction",
                "--routines",
                "--triggers"
            ]

            subprocess.run(command, check=True)
            logger.info(f"数据库备份完成: {backup_file}")
            return backup_file

        except Exception as e:
            logger.error(f"数据库备份失败: {e}")
            raise

    def restore_database(self, backup_file: str):
        """恢复数据库"""
        try:
            import subprocess

            db_config = self.config
            command = [
                "mysql",
                f"-h{db_config.get('host')}",
                f"-P{db_config.get('port')}",
                f"-u{db_config.get('user')}",
                f"-p{db_config.get('password')}",
                db_config.get('name')
            ]

            with open(backup_file, 'r') as f:
                subprocess.run(command, stdin=f, check=True)

            logger.info(f"数据库恢复完成: {backup_file}")

        except Exception as e:
            logger.error(f"数据库恢复失败: {e}")
            raise

    def get_table_stats(self):
        """获取数据库表统计信息"""
        stats = {}
        with self.get_session() as session:
            # 获取所有表名
            result = session.execute("""
                SELECT table_name, table_rows
                FROM information_schema.tables
                WHERE table_schema = DATABASE()
                ORDER BY table_name
            """)
            table_stats = result.fetchall()

            for table_name, row_count in table_stats:
                stats[table_name] = {
                    'row_count': row_count or 0,
                    'size_mb': self._get_table_size(session, table_name)
                }

        return stats

    def _get_table_size(self, session, table_name: str) -> float:
        """获取表大小（MB）"""
        result = session.execute("""
            SELECT ROUND(data_length / 1024 / 1024, 2) as size_mb
            FROM information_schema.tables
            WHERE table_schema = DATABASE() AND table_name = :table_name
        """, {'table_name': table_name})
        size = result.fetchone()
        return size[0] if size else 0.0

    def cleanup_old_data(self, days: int = 30):
        """清理旧数据"""
        try:
            from datetime import datetime, timedelta

            cutoff_date = datetime.utcnow() - timedelta(days=days)

            with self.get_session() as session:
                # 清理旧的预测记录
                deleted_predictions = session.execute("""
                    DELETE FROM predictions
                    WHERE prediction_time < :cutoff_date
                """, {'cutoff_date': cutoff_date}).rowcount

                # 清理旧的收集日志
                deleted_logs = session.execute("""
                    DELETE FROM collection_logs
                    WHERE log_time < :cutoff_date
                """, {'cutoff_date': cutoff_date}).rowcount

                # 清理旧的系统指标
                deleted_metrics = session.execute("""
                    DELETE FROM system_metrics
                    WHERE timestamp < :cutoff_date
                """, {'cutoff_date': cutoff_date}).rowcount

                logger.info(f"清理旧数据完成: predictions({deleted_predictions}), logs({deleted_logs}), metrics({deleted_metrics})")

        except Exception as e:
            logger.error(f"清理旧数据失败: {e}")
            raise

# 全局数据库管理器实例
db_manager = DatabaseManager()

def get_db():
    """获取数据库会话 - 用于FastAPI等框架"""
    return db_manager.SessionLocal()

def close_db():
    """关闭数据库连接"""
    db_manager.close()

# 便捷函数
@contextmanager
def db_session():
    """数据库会话上下文管理器"""
    with db_manager.get_session() as session:
        yield session

def execute_sql(sql: str, params: dict = None):
    """执行SQL查询"""
    return db_manager.execute_raw_sql(sql, params)

if __name__ == "__main__":
    # 测试数据库连接
    try:
        db_manager.initialize()
        print("✅ 数据库连接成功")

        # 获取表统计
        stats = db_manager.get_table_stats()
        print("\n📊 数据库表统计:")
        for table, info in stats.items():
            print(f"   {table}: {info['row_count']} 行, {info['size_mb']} MB")

        db_manager.close()
        print("✅ 数据库连接已关闭")

    except Exception as e:
        print(f"❌ 数据库连接失败: {e}")