# 在 FastAPI 项目中用于定义 API 的“数据契约”（schemas.py）
# 定义API 输入输出格式的 Pydantic 模型
from pydantic import BaseModel, Field
from typing import List, Optional
from datetime import datetime
from enum import Enum
from pytz import timezone
TZ = timezone("Asia/Shanghai")

# 枚举定义（与 models.py 保持一致）
class SignalType(str, Enum):
    # 信号类型枚举
    BUY = "buy"
    SELL = "sell"
    NEUTRAL = "neutral"
    STRONG_BUY = "strong_buy"
    STRONG_SELL = "strong_sell"
    
class MarketType(str, Enum):
    # 市场类型枚举
    SH = "SH"  # 上海证券交易所
    SZ = "SZ"  # 深圳证券交易所
    HK = "HK"  # 港股
    US = "US"  # 美股
    
class NewsSentiment(str, Enum):
    # 新闻情感枚举
    POSITIVE = "positive"   # 积极
    NEGATIVE = "negative"   # 消极
    NEUTRAL = "neutral"     # 中性
    MIXED = "mixed"         # 混合
    
# News Pydantic 模型
class NewsBase(BaseModel):
    '''
    新闻基本信息模型
    用于创建和更新新闻信息
    '''
    title: str = Field(..., max_length=500)
    source: Optional[str] = Field(None, max_length=100)
    url: Optional[str] = Field(None, max_length=500)
    publish_time: datetime
    
class NewsCreate(NewsBase):
    '''
    创建新闻模型
    '''
    stock_id: int
    
class NewsInDB(NewsBase):
    '''
    数据库中的新闻模型
    包含ID和创建时间
    '''
    id: int
    stock_id: int
    sentiment: Optional[NewsSentiment]
    sentiment_score: Optional[float] = Field(None, ge=-1.0, le=1.0)  # -1到1
    created_at: datetime
    
    class Config:
        from_attributes = True
        
# Signal 模型
class SignalBase(BaseModel):
    '''
    信号基本信息模型
    用于创建和更新信号信息
    '''
    signal_type: SignalType
    strength: float = Field(1.0, ge=0.0, le=1.0)  # 范围验证
    reason: str
    trigger_price: float = Field(..., gt=0)

class SignalCreate(SignalBase):
    '''
    创建信号模型
    '''
    stock_id: int
    strategy_name: str = "RSI_Strategy"

class SignalInDB(SignalBase):
    '''
    数据库中的信号模型
    包含ID和生成时间
    '''
    id: int
    stock_id: int
    confidence: float = Field(0.8, ge=0.0, le=1.0)
    generated_at: datetime
    is_active: bool = True
    
    class Config:
        from_attributes = True

# Stock Pydantic 模型
class StockBase(BaseModel):
    '''
    stock基本信息模型
    用于创建和更新stock信息
    '''
    symbol: str = Field(..., example="000001.SZ", description="stock代码")
    name: str = Field(..., example="平安银行", description="stock名称")
    market: MarketType = Field(..., description="所属市场")
    industry: Optional[str] = Field(None, example="银行", description="所属行业")
    listing_date: Optional[datetime] = Field(None, description="上市日期")
    current_price: Optional[float] = Field(None, example=15.23, description="当前价格")
    market_cap: Optional[float] = Field(None, example=500.0, description="市值（亿元）")
    pe_ratio: Optional[float] = Field(None, example=12.5, description="市盈率")
    pb_ratio: Optional[float] = Field(None, example=1.2, description="市净率")
    is_active: bool = Field(True, description="是否活跃（退市stock设为False）")
    is_tracked: bool = Field(True, description="是否被系统跟踪")

    class Config:
        orm_mode = True
        use_enum_values = True
        json_encoders = {
            datetime: lambda v: v.strftime("%Y-%m-%d %H:%M:%S") if v else None
        }
        
class StockCreate(StockBase):
    '''
    创建stock模型
    '''
    # 只需要基础字段，不需要id、created_at等
    pass


class StockInDB(StockBase):
    # 响应模型，输出到前端
    '''
    数据库中的stock模型
    包含ID和时间戳
    '''
    id: int
    current_price: Optional[float]      # 当前价格
    market_cap: Optional[float]         # 市值（亿元）
    created_at: datetime                # 创建时间
    updated_at: datetime                # 更新时间
    
    class Config:
        from_attributes = True
    
    # 响应示例：
    # example = {
    #     "id": 1,
    #     "symbol": "000001.SZ",
    #     "name": "平安银行",
    #     "market": "SZ",
    #     "industry": "银行",
    #     "listing_date": "1991-04-03 00:00:00",
    #     "current_price": 15.23,
    #     "market_cap": 500.0,
    #     "pe_ratio": 12.5,
    #     "pb_ratio": 1.2,
    #     "is_active": True,
    #     "is_tracked": True,
    #     "created_at": "2024-01-01 12:00:00",
    #     "updated_at": "2024-06-01 12:00:00"
    # }
    
# 精简版 Stock 列表响应模型
class StockSimple(StockBase):
    """
        列表页，只返回最基本信息：
    """
    id: int
    current_price: Optional[float]
    
    class Config:
        from_attributes = True
    