# backend/app/database.py
# 数据库连接和会话管理模块

from config import settings

from sqlalchemy import create_engine
from sqlalchemy.orm import declarative_base, sessionmaker

# 1. 创建数据库引擎 (核心接口)
# echo=True 表示在控制台输出所有执行的SQL，调试时非常有用，生产环境请设为False
engine = create_engine(
    settings.DATABASE_URL,
    echo=True,  # 开发阶段建议开启，方便排查问题
    # 如果使用SQLite，需要以下参数来支持多线程
    connect_args={"check_same_thread": False} if "sqlite" in settings.DATABASE_URL else {}
)

# 2. 创建本地会话工厂
# SessionLocal是生成数据库会话的“工厂”，每个请求会使用独立的会话
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

# 3. 创建声明性基类
# 所有数据模型（如Stock, News）都将继承这个Base类
Base = declarative_base()

# 依赖项函数：用于在FastAPI的路径操作中获取数据库会话
def get_db():
    """
    提供数据库会话的依赖项。
    使用方式：在FastAPI路径操作函数参数中声明 `db: Session = Depends(get_db)`
    确保会话在使用后正确关闭。
    """
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
        
# 外部调用函数，用于测试数据库连接
def test_db_connection():
    """测试数据库连接是否成功"""
    try:
        with engine.connect() as connection:
            print("Database connection successful!")
            return True
    except Exception as e:
        print("Database connection failed:", e)
        return False
        
# 如果直接运行此文件，可以测试数据库连接是否成功
if __name__ == "__main__":
    try:
        # 尝试连接数据库
        with engine.connect() as connection:
            print("Database connection successful!")
    except Exception as e:
        print("Database connection failed:", e)