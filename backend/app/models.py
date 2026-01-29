# backend/app/models.py
from sqlalchemy import Column, Integer, String, Float, DateTime, Text, Boolean, ForeignKey, Enum, JSON, Index
from sqlalchemy.orm import relationship
from datetime import datetime
import enum
from database import Base

# 时区设置（根据需要调整）
from pytz import timezone
TZ = timezone("Asia/Shanghai")


# ============ 枚举定义（提高数据规范性）============
class SignalType(str, enum.Enum):
    """信号类型枚举"""
    BUY = "buy"
    SELL = "sell"
    NEUTRAL = "neutral"
    STRONG_BUY = "strong_buy"
    STRONG_SELL = "strong_sell"

class NewsSentiment(str, enum.Enum):
    """新闻情感枚举"""
    POSITIVE = "positive"
    NEGATIVE = "negative"
    NEUTRAL = "neutral"
    MIXED = "mixed"

class MarketType(str, enum.Enum):
    """市场类型枚举"""
    SH = "SH"      # 上海证券交易所
    SZ = "SZ"      # 深圳证券交易所
    BJ = "BJ"      # 北京证券交易所
    HK = "HK"      # 香港交易所
    US = "US"      # 美国交易所

# ============ Stock 模型（股票表）============
class Stock(Base):
    """
    股票基本信息表
    存储股票代码、名称等核心信息
    """
    __tablename__ = "stocks"  # 数据库表名
    
    # 主键和唯一标识
    id = Column(Integer, primary_key=True, index=True)
    symbol = Column(String(20), unique=True, index=True, nullable=False, comment="股票代码，如 '000001.SZ'")
    name = Column(String(100), nullable=False, comment="股票名称")
    
    # 市场信息
    market = Column(Enum(MarketType), default=MarketType.SZ, comment="所属市场")
    industry = Column(String(50), comment="所属行业")
    listing_date = Column(DateTime, comment="上市日期")
    
    # 基础财务数据（可定期更新）
    current_price = Column(Float, comment="当前价格")
    market_cap = Column(Float, comment="市值（亿元）")
    pe_ratio = Column(Float, comment="市盈率")
    pb_ratio = Column(Float, comment="市净率")
    
    # 状态标志
    is_active = Column(Boolean, default=True, comment="是否活跃（退市股票设为False）")
    is_tracked = Column(Boolean, default=True, comment="是否被系统跟踪")
    
    # 关系定义：一个股票可以有多条新闻和多个信号
    news_items = relationship("News", back_populates="stock", cascade="all, delete-orphan")
    signals = relationship("Signal", back_populates="stock", cascade="all, delete-orphan")
    
    # 时间戳
    created_at = Column(DateTime, default=datetime.now(TZ), index=True)
    updated_at = Column(DateTime, default=datetime.now(TZ), onupdate=datetime.now(TZ), index=True)
    
    def __repr__(self):
        return f"<Stock(id={self.id}, symbol='{self.symbol}', name='{self.name}')>"

# ============ News 模型（新闻表）============
class News(Base):
    """
    股票新闻与舆情表
    存储新闻内容和AI分析结果
    """
    __tablename__ = "news"
    
    # 主键
    id = Column(Integer, primary_key=True, index=True)
    
    # 外键关联：这条新闻属于哪只股票
    stock_id = Column(Integer, ForeignKey("stocks.id", ondelete="CASCADE"), nullable=False, index=True)
    
    # 新闻内容
    title = Column(String(500), nullable=False, comment="新闻标题")
    summary = Column(Text, comment="新闻摘要")
    content = Column(Text, comment="新闻全文")
    source = Column(String(100), comment="新闻来源，如 '新浪财经'")
    url = Column(String(500), unique=True, comment="原文链接")
    publish_time = Column(DateTime, nullable=False, index=True, comment="新闻发布时间")
    
    # AI分析字段（由ai_service.py填充）
    sentiment = Column(Enum(NewsSentiment), comment="情感分析结果")
    sentiment_score = Column(Float, comment="情感分数，-1.0(极度负面)到1.0(极度正面)")
    
    # 关键词和分类
    keywords = Column(JSON, comment="新闻关键词列表，JSON格式")
    categories = Column(JSON, comment="新闻分类，如['公司公告', '财报季']")
    
    # 影响力评估
    impact_score = Column(Float, default=0.0, comment="影响力评分，0-1")
    is_important = Column(Boolean, default=False, comment="是否重要新闻")
    
    # 关系定义：新闻属于一只股票
    stock = relationship("Stock", back_populates="news_items")
    
    # 时间戳
    created_at = Column(DateTime, default=datetime.now(TZ), index=True)
    processed_at = Column(DateTime, comment="AI处理时间")
    
    def __repr__(self):
        return f"<News(id={self.id}, title='{self.title[:50]}...', sentiment={self.sentiment})>"

# ============ Signal 模型（信号表）============
class Signal(Base):
    """
    投资信号表
    由strategy_engine.py生成
    """
    __tablename__ = "signals"
    
    # 主键
    id = Column(Integer, primary_key=True, index=True)
    
    # 外键关联：这个信号属于哪只股票
    stock_id = Column(Integer, ForeignKey("stocks.id", ondelete="CASCADE"), nullable=False, index=True)
    
    # 信号基本信息
    signal_type = Column(Enum(SignalType), nullable=False, index=True, comment="信号类型")
    strength = Column(Float, default=1.0, comment="信号强度，0.0到1.0")
    confidence = Column(Float, default=0.8, comment="置信度，0.0到1.0")
    
    # 信号详情
    reason = Column(Text, nullable=False, comment="信号生成原因，如 'RSI超卖 + 负面新闻消化完毕'")
    strategy_name = Column(String(50), nullable=False, comment="生成信号的策略名称，如 'RSI_Strategy'")
    
    # 技术指标快照（信号触发时的值）
    trigger_price = Column(Float, nullable=False, comment="触发价格")
    trigger_rsi = Column(Float, comment="触发时RSI值")
    trigger_macd = Column(Float, comment="触发时MACD值")
    trigger_ma20 = Column(Float, comment="触发时20日均线")
    
    # 额外数据（JSON格式，便于扩展）
    signal_metadata = Column(JSON, comment="额外元数据，如 {'volume_ratio': 1.5, 'breakout': True}")
    
    # 状态管理
    is_active = Column(Boolean, default=True, comment="信号是否仍有效")
    is_notified = Column(Boolean, default=False, comment="是否已发送通知")
    is_processed = Column(Boolean, default=False, comment="用户是否已处理")
    expiration_time = Column(DateTime, comment="信号过期时间")
    
    # 关系定义：信号属于一只股票
    stock = relationship("Stock", back_populates="signals")
    
    # 时间戳
    generated_at = Column(DateTime, default=datetime.now(TZ), nullable=False, index=True)
    
    def __repr__(self):
        return f"<Signal(id={self.id}, stock_id={self.stock_id}, type={self.signal_type}, strength={self.strength})>"

# ============ 可选：股票历史价格表 ============
class StockPrice(Base):
    """
    股票历史价格表（可选，根据需求添加）
    用于存储每日价格数据，支持技术分析
    """
    __tablename__ = "stock_prices"
    
    id = Column(Integer, primary_key=True, index=True)
    stock_id = Column(Integer, ForeignKey("stocks.id", ondelete="CASCADE"), nullable=False, index=True)
    
    # 价格数据
    date = Column(DateTime, nullable=False, index=True, comment="交易日")
    open_price = Column(Float, comment="开盘价")
    close_price = Column(Float, comment="收盘价")
    high_price = Column(Float, comment="最高价")
    low_price = Column(Float, comment="最低价")
    volume = Column(Float, comment="成交量")
    turnover = Column(Float, comment="成交额")
    
    # 复权因子
    adj_factor = Column(Float, default=1.0, comment="复权因子")
    
    # 关系
    stock = relationship("Stock")
    
    # 复合唯一约束：同一股票同一日期只能有一条记录
    __table_args__ = (
        # 这里使用Index创建复合索引和唯一约束
        Index('idx_stock_date', 'stock_id', 'date', unique=True),
    )
    
    def __repr__(self):
        return f"<StockPrice(stock_id={self.stock_id}, date={self.date}, close={self.close_price})>"