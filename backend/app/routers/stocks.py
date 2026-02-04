# stock数据相关路由
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from fastapi.background import BackgroundTasks
from typing import List

from database import get_db
from schemas import StockCreate, StockInDB, StockSimple, OperationResult
from services.data_fetcher import DataFetcher
import models

router = APIRouter()

@router.post("/stocks/update", response_model=OperationResult)
def update_all_stocks_data(background_tasks: BackgroundTasks, db: Session = Depends(get_db)):
    """更新所有stock的数据"""
    fetcher = DataFetcher()
    background_tasks.add_task(fetcher.update_stock_list, db)
    return {"success": True, "message": "已添加到后台任务"}

@router.post("/stocks/", response_model=StockInDB)
def create_stock(stock: StockCreate, db: Session = Depends(get_db)):
    """创建新stock"""
    # Pydantic 已验证 stock 数据格式正确
    db_stock = models.Stock(**stock.dict())
    db.add(db_stock)
    db.commit()
    db.refresh(db_stock)
    return db_stock  # 自动按 StockInDB 格式序列化

@router.get("/stocks/", response_model=List[StockSimple])
def list_stocks(skip: int = 0, limit: int = 100, db: Session = Depends(get_db)):
    """获取stock列表（精简信息）"""
    stocks = db.query(models.Stock).offset(skip).limit(limit).all()
    return stocks  # 自动过滤为 StockSimple 字段

@router.get("/stocks/{stock_id}", response_model=StockInDB)
def get_stock(stock_id: int, db: Session = Depends(get_db)):
    """获取stock详情"""
    stock = db.query(models.Stock).filter(models.Stock.id == stock_id).first()
    if not stock:
        raise HTTPException(status_code=404, detail="stock不存在")
    return stock

@router.post("/stocks/{symbol}/fetch-data", response_model=OperationResult)
async def fetch_stock_data(
    symbol: str,
    days: int = 30,
    background_tasks: BackgroundTasks = None,
    db: Session = Depends(get_db)
):
    """
    手动获取并更新某只stock的数据
    
    - **symbol**: stock代码
    - **days**: 获取最近多少天的历史数据
    - **background**: 是否后台执行（默认立即执行）
    """
    fetcher = DataFetcher()
    
    # 检查stock是否存在
    stock = db.query(models.Stock).filter(models.Stock.symbol == symbol).first()
    if not stock:
        # 如果不存在，尝试创建
        result = fetcher.fetch_and_save_stock_with_prices(db, symbol, days)
    else:
        # 如果存在，只更新价格数据
        result = fetcher.fetch_and_save_stock_with_prices(db, symbol, days)
    if result.get("error"):
        raise HTTPException(status_code=500, detail=result["error"])
    
    return {
        "success": True,
        "message": f"成功更新 {symbol} 的数据",
        "data": result
    }
    
@router.post("/stocks/{symbol}/fetch_stock_daily", response_model=OperationResult)
async def fetch_stock_daily(
    db: Session = Depends(get_db),
    symbol : str = "603707",
    start_date : str = None,
    end_date : str = None,
    adjust : str = "qfq",
    background_tasks: BackgroundTasks = None,
):
    fetcher = DataFetcher()
    print(symbol, start_date, end_date)
    background_tasks.add_task(fetcher.fetch_stock_daily, db, symbol, start_date, end_date, adjust)
    return {"success": True, "message": "已添加到后台任务"}
    
@router.post("/stocks/{symbol}/fetch-analysis-indicator", response_model=OperationResult)
async def fetch_analysis_indicator(
    db: Session = Depends(get_db),
    symbol : str = "603707",
    year : str = "2025",
    background_tasks: BackgroundTasks = None,
):
    fetcher = DataFetcher()
    print(symbol, year)
    background_tasks.add_task(fetcher.stock_analysis_indicator, db, symbol, year)
    
    return {"success": True, "message": "已添加到后台任务"}