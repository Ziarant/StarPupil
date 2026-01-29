# stock数据相关路由
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from typing import List

from database import get_db
from schemas import StockCreate, StockInDB, StockSimple
import models

router = APIRouter()

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