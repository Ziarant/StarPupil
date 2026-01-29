# 应用默认行为和逻辑配置
from pydantic_settings import BaseSettings
from pydantic import ConfigDict
from typing import Optional

class Settings(BaseSettings):
    """项目核心配置类，自动从环境变量或 .env 文件加载"""
    
    # 1. 数据库配置
    # 默认SQLite，生产环境需替换
    # 协议 "sqlite:///"，它告诉SQLAlchemy使用SQLite数据库驱动;
    # 然后是路径 "./starpupil.db"，这里的 "./" 表示当前工作目录，通常是项目根目录或者backend目录，具体取决于程序启动位置。(首次运行自动创建)
    DATABASE_URL: str = "sqlite:///./starpupil.db"
    
    # 2. AI/金融数据服务配置 (根据你最终选用的服务填写)
    # 以DeepSeek Chat API为例（注意：通用模型对金融分析效果有限，建议用专用金融MCP）
    AI_API_KEY: Optional[str] = "sk-f47f3a78f7b74203bdfc669965194ac3"
    AI_API_BASE: str = "https://api.deepseek.com"
    
    # 如果选用金融MCP服务（推荐）
    FINANCE_MCP_API_KEY: Optional[str] = None
    FINANCE_MCP_BASE_URL: str = "https://api.finance-mcp.example.com"  # 示例地址
    
    # 3. 数据源配置
    AKSHARE_TIMEOUT: int = 30  # akshare请求超时时间（秒）
    
    # 4. 应用与安全配置
    APP_ENV: str = "development"  # development, testing, production
    SECRET_KEY: str = "your-secret-key-change-in-production"  # 用于JWT等
    BACKEND_CORS_ORIGINS: list = ["http://localhost:5173"]  # Vue前端默认地址
    
    # 5. 任务调度配置
    SCHEDULER_TIMEZONE: str = "Asia/Shanghai"
    ENABLE_SCHEDULED_TASKS: bool = True
    
    # 6. 通知配置
    SMTP_SERVER: Optional[str] = "smtp.qq.com"
    SMTP_PORT: Optional[int] = "465"
    SMTP_USERNAME: Optional[str] = "pca2358797100@foxmail.com"
    SMTP_PASSWORD: Optional[str] = "gtwkplcrpxrmebhh"
    NOTIFICATION_EMAIL: Optional[str] = "2358797100@qq.com"

     # Pydantic V2 的正确配置方式
    model_config = ConfigDict(
        env_file=".env",  # 指定从项目根目录的 .env 文件加载
        env_file_encoding="utf-8",  # 明确指定编码
        case_sensitive=False,  # 环境变量不区分大小写
        # 如果你需要支持嵌套列表（如BACKEND_CORS_ORIGINS），可能需要额外处理
        # 或者将BACKEND_CORS_ORIGINS定义为逗号分隔的字符串，然后在代码中解析
    )

# 辅助函数：根据环境获取数据库配置（示例）
def get_database_config():
    """根据环境返回数据库配置"""
    if settings.APP_ENV == "testing":
        return {"sqlalchemy.url": "sqlite:///./test.db"}
    return {"sqlalchemy.url": settings.DATABASE_URL}

# 创建全局配置实例
settings = Settings()

if __name__ == "__main__":
    # 测试配置加载
    print("Database URL:", settings.DATABASE_URL)
    print("AI API Key:", settings.AI_API_KEY)
    print("SMTP Server:", settings.SMTP_SERVER)