import os
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import QueuePool
from contextlib import contextmanager
from urllib.parse import quote_plus
from exceptions import DatabaseConnectionException
import logging



class DatabaseConfig:
    """
    数据库配置类
    """
    def __init__(self):
        # 获取环境变量或使用默认值
        # 默认使用MySQL作为元数据存储库
        default_url = 'mysql+pymysql://root:Admin%40900@10.178.80.101:3306/meta_db?charset=utf8mb4'
        self.database_url = os.getenv('DATABASE_URL', default_url)
        self.engine = None
        self.SessionLocal = None
        
    def init_db(self):
        """初始化数据库引擎"""
        try:
            self.engine = create_engine(
                self.database_url,
                poolclass=QueuePool,
                pool_size=10,
                max_overflow=20,
                pool_pre_ping=True,
                echo=False,  # 设为True可查看SQL语句
                connect_args={
                    'connect_timeout': 30,
                    'charset': 'utf8mb4'
                }
            )
            
            # 创建会话工厂
            self.SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=self.engine)
            
            return self.engine
        except Exception as e:
            logging.error(f"数据库引擎初始化失败: {str(e)}")
            raise DatabaseConnectionException(f"数据库引擎初始化失败: {str(e)}")
    
    @contextmanager
    def get_session(self):
        """获取数据库会话的上下文管理器"""
        session = self.SessionLocal()
        try:
            yield session
            session.commit()
        except Exception as e:
            session.rollback()
            logging.error(f"数据库会话错误: {str(e)}")
            raise DatabaseConnectionException(f"数据库操作失败: {str(e)}")
        finally:
            session.close()


# 支持的数据库类型映射
SUPPORTED_DATABASES = {
    'mysql': {
        'driver': 'pymysql',
        'port': 3306,
        'dialect': 'mysql'
    },
    'postgresql': {
        'driver': 'psycopg2',
        'port': 5432,
        'dialect': 'postgresql'
    },
    'sqlserver': {
        'driver': 'pyodbc',
        'port': 1433,
        'dialect': 'mssql'
    },
    'oracle': {
        'driver': 'cx_oracle',
        'port': 1521,
        'dialect': 'oracle'
    }
}


def get_connection_string(db_type, host, port, username, password, database):
    """
    根据数据库类型生成连接字符串
    """
    if db_type not in SUPPORTED_DATABASES:
        raise ValueError(f"不支持的数据库类型: {db_type}")
    
    config = SUPPORTED_DATABASES[db_type]
    
    # URL编码用户名和密码，防止特殊字符造成问题
    encoded_username = quote_plus(str(username))
    encoded_password = quote_plus(str(password))
    encoded_database = quote_plus(str(database))
    
    if db_type == 'mysql':
        return f"mysql+pymysql://{encoded_username}:{encoded_password}@{host}:{port}/{encoded_database}"
    elif db_type == 'postgresql':
        return f"postgresql+psycopg2://{encoded_username}:{encoded_password}@{host}:{port}/{encoded_database}"
    elif db_type == 'sqlserver':
        # SQL Server需要额外的参数
        return f"mssql+pyodbc://{encoded_username}:{encoded_password}@{host}:{port}/{encoded_database}?driver=ODBC+Driver+17+for+SQL+Server"
    elif db_type == 'oracle':
        return f"oracle+cx_oracle://{encoded_username}:{encoded_password}@{host}:{port}/{encoded_database}"
    else:
        raise ValueError(f"未知的数据库类型: {db_type}")