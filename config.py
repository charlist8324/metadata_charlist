import os
from typing import Dict, Any


class Config:
    """
    应用程序配置类
    """
    # 从环境变量获取配置，如果没有则使用默认值
    SECRET_KEY = os.environ.get('SECRET_KEY') or 'dev-secret-key-for-metadata-manager'
    DATABASE_URL = os.environ.get('DATABASE_URL') or 'mysql+pymysql://root:Admin%40900@10.178.80.101:3306/meta_db?charset=utf8mb4'
    DEBUG = os.environ.get('DEBUG', 'False').lower() == 'true'
    
    # 数据库连接池配置
    DB_POOL_SIZE = int(os.environ.get('DB_POOL_SIZE', '10'))
    DB_POOL_MAX_OVERFLOW = int(os.environ.get('DB_POOL_MAX_OVERFLOW', '20'))
    DB_POOL_RECYCLE = int(os.environ.get('DB_POOL_RECYCLE', '3600'))  # 1小时
    DB_ECHO = os.environ.get('DB_ECHO', 'False').lower() == 'true'
    
    # API配置
    API_VERSION = 'v1'
    MAX_CONTENT_LENGTH = 16 * 1024 * 1024  # 16MB
    
    # 支持的数据库类型配置
    SUPPORTED_DATABASES = {
        'mysql': {
            'driver': 'pymysql',
            'port': 3306,
            'dialect': 'mysql',
            'test_query': 'SELECT 1'
        },
        'postgresql': {
            'driver': 'psycopg2',
            'port': 5432,
            'dialect': 'postgresql',
            'test_query': 'SELECT 1'
        },
        'sqlserver': {
            'driver': 'pyodbc',
            'port': 1433,
            'dialect': 'mssql',
            'test_query': 'SELECT 1'
        },
        'oracle': {
            'driver': 'cx_oracle',
            'port': 1521,
            'dialect': 'oracle',
            'test_query': 'SELECT 1 FROM DUAL'
        }
    }
    
    # 连接超时配置（秒）
    CONNECTION_TIMEOUT = int(os.environ.get('CONNECTION_TIMEOUT', '30'))
    QUERY_TIMEOUT = int(os.environ.get('QUERY_TIMEOUT', '60'))
    
    # 元数据抽取配置
    EXTRACTION_BATCH_SIZE = int(os.environ.get('EXTRACTION_BATCH_SIZE', '100'))  # 批量处理表的数量
    EXTRACTION_TIMEOUT = int(os.environ.get('EXTRACTION_TIMEOUT', '3600'))  # 抽取超时时间（秒）
    
    # 日志配置
    LOG_LEVEL = os.environ.get('LOG_LEVEL', 'INFO')
    LOG_FILE = os.environ.get('LOG_FILE', 'metadata_manager.log')


class DevelopmentConfig(Config):
    """
    开发环境配置
    """
    DEBUG = True
    DATABASE_URL = os.environ.get('DEV_DATABASE_URL') or 'mysql+pymysql://root:Admin%40900@10.178.80.101:3306/meta_db?charset=utf8mb4'


class ProductionConfig(Config):
    """
    生产环境配置
    """
    DEBUG = False
    DATABASE_URL = os.environ.get('PROD_DATABASE_URL') or 'mysql+pymysql://root:Admin%40900@10.178.80.101:3306/meta_db?charset=utf8mb4'
    
    # 生产环境安全配置
    SECRET_KEY = os.environ.get('SECRET_KEY') or \
        'you-must-set-a-secret-key-in-production'
    
    # 生产环境数据库配置
    DB_POOL_SIZE = int(os.environ.get('DB_POOL_SIZE', '20'))
    DB_POOL_MAX_OVERFLOW = int(os.environ.get('DB_POOL_MAX_OVERFLOW', '40'))


class TestingConfig(Config):
    """
    测试环境配置
    """
    TESTING = True
    DEBUG = True
    DATABASE_URL = 'sqlite:///:memory:'  # 使用内存数据库进行测试


# 配置字典
config: Dict[str, Any] = {
    'development': DevelopmentConfig,
    'production': ProductionConfig,
    'testing': TestingConfig,
    'default': DevelopmentConfig
}