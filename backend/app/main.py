import time, os
from contextlib import asynccontextmanager

# 第三方库
from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from fastapi.exceptions import RequestValidationError
from starlette.exceptions import HTTPException as StarletteHTTPException
import uvicorn

# 本地应用导入
from database import engine, Base
from models import Stock, News, Signal  # 导入所有模型以确保表被创建
from config import settings
from routers import stocks

# 生命周期管理：在应用启动时创建所有表
@asynccontextmanager
async def lifespan(app: FastAPI):
    # 应用启动时创建所有表
    print("🚀 StarPupil 后端服务启动中...")
    # 确保日志目录存在
    os.makedirs("logs", exist_ok=True)
    print(f"📁 日志目录: {os.path.abspath('logs')}")
    
    Base.metadata.create_all(bind=engine)
    print("🗄️  数据库表已创建/验证")
    
    yield
    # 应用关闭时可以执行清理操作（如果需要）
    pass
    print("Application shutdown complete.")

# 创建 FastAPI 应用实例
app = FastAPI(
    title="StarPupil Backend Service",                                          # 应用标题
    description="Backend service for StarPupil stock analysis platform.",       # 应用描述
    version="1.0.0",                                                            # 应用版本
    lifespan=lifespan,                                                         # 生命周期管理
)

# ============ 中间件配置 =============
# 1.跨域资源共享 (CORS) 中间件配置
app.add_middleware(
    CORSMiddleware,
    allow_origins = settings.BACKEND_CORS_ORIGINS,  # 从配置读取:允许的前端地址列表
    allow_credentials = True,                       # 允许携带凭证（如Cookies）
    allow_methods = ["GET", "POST", "PUT", "DELETE", "PATCH", "OPTIONS"],
    allow_headers = ["*"],
)

# 2. 请求日志中间件
# 每次有HTTP请求到达服务器时，都会先经过这个中间件，然后再传递给路由处理函数，最后返回响应时再经过这个中间件
@app.middleware("http")
async def add_process_time_header(request: Request, call_next):
    start_time = time.time()
    response = await call_next(request)
    process_time = time.time() - start_time
    
    # 开发环境输出详细日志
    # 构建日志消息
    if settings.APP_ENV == "development":
        log_message = (
            f"[{time.strftime('%Y-%m-%d %H:%M:%S')}] "
            f"{request.method} {request.url.path} - "
            f"Status: {response.status_code} - "
            f"Time: {process_time:.3f}s"
        )
        print(log_message)
    
    # 写入日志文件（带错误处理）
    try:
        # 确保目录存在
        os.makedirs("logs", exist_ok=True)
        
        log_file_path = os.path.join("logs", "server.log")
        # 以追加模式写入日志文件
        with open(log_file_path, "a", encoding="utf-8") as log_file:
            log_file.write(log_message + "\n")
            
    except Exception as e:
        # 如果写入失败，只输出到控制台，不中断请求
        print(f"⚠️ 日志写入失败（不影响请求）: {e}")
    
    # 添加处理时间到响应头
    response.headers["X-Process-Time"] = f"{process_time:.3f}"
    
    return response

# ============ 异常处理 ============
@app.exception_handler(StarletteHTTPException)
async def http_exception_handler(request, exc):
    return JSONResponse(
        status_code=exc.status_code,
        content={"error": exc.detail}
    )

@app.exception_handler(RequestValidationError)
async def validation_exception_handler(request, exc):
    return JSONResponse(
        status_code=422,
        content={"error": "请求参数验证失败", "details": exc.errors()}
    )

# ============= 路由配置 ==============
# stocks, news, signals等路由

@app.get("/health")
async def health_check():
    """健康检查"""
    return {
        "status": "healthy",
        "timestamp": time.time(),
        "environment": settings.APP_ENV
    }

# uvicorn是一个用于运行FastAPI应用的ASGI服务器
# 可以通过命令行运行，也可以在代码中调用uvicorn.run()来启动应用
# api/v1 版本前缀
app.include_router(stocks.router, prefix="/api/v1", tags=["stocks"])

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
    
    
# 当前进度：
# 运行main.py
# cmd测试：
# 更新信息      curl -X POST "http://127.0.0.1:8082/api/v1/stocks/update"
# 获取信息      curl -X POST "http://127.0.0.1:8082/api/v1/stocks/603707/fetch-data?days=2"
# 获取财务指标  curl -X POST "http://127.0.0.1:8082/api/v1/stocks/000001/fetch-analysis-indicator?year=2020"
# 获取日线数据  curl -X POST "http://127.0.0.1:8082/api/v1/stocks/000004/fetch_stock_daily?start_date=20250101&end_date=20260203"
    
    
