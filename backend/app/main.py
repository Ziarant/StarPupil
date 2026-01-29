from fastapi import FastAPI
from database import engine, Base
from models import Stock, News, Signal  # 导入所有模型以确保表被创建

# 创建所有表
Base.metadata.create_all(bind=engine)

app = FastAPI()


# stocks.py测试
from routers import stocks
import uvicorn
# uvicorn是一个用于运行FastAPI应用的ASGI服务器
# 可以通过命令行运行，也可以在代码中调用uvicorn.run()来启动应用
app.include_router(stocks.router)

if __name__ == "__main__":
    # 测试应用是否启动成功
    # 127.0.0.1为本地回环地址，8082为自定义端口，用于测试
    # host:port为后端服务地址
    host = "127.0.0.1"
    port = 8082
    uvicorn.run(app, host=host, port=port)
    # 测试结果：
    # INFO:     Started server process [26516]
    # INFO:     Waiting for application startup.
    # INFO:     Application startup complete.
    # INFO:     Uvicorn running on http://127.0.0.1:8082 (Press CTRL+C to quit)
    # 结果表明FastAPI应用已成功启动并监听指定端口。  
    
    
