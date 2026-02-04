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

# ============ Stock 模型（stock表）============
class Stock(Base):
    """
    stock基本信息表
    存储stock代码、名称等核心信息
    """
    __tablename__ = "stocks"  # 数据库表名
    
    # 主键和唯一标识
    id = Column(Integer, primary_key=True, index=True)
    symbol = Column(String(20), unique=True, index=True, nullable=False, comment="stock代码，如 '000001.SZ'")
    name = Column(String(100), nullable=False, comment="stock名称")
    
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
    is_active = Column(Boolean, default=True, comment="是否活跃（退市stock设为False）")
    is_tracked = Column(Boolean, default=True, comment="是否被系统跟踪")
    
    # 关系定义：一个stock可以有多条新闻和多个信号
    news_items = relationship("News", back_populates="stock", cascade="all, delete-orphan")
    signals = relationship("Signal", back_populates="stock", cascade="all, delete-orphan")
    
    # 时间戳
    created_at = Column(DateTime, default=datetime.now(TZ), index=True)
    updated_at = Column(DateTime, default=datetime.now(TZ), onupdate=datetime.now(TZ), index=True)
    
    def __repr__(self):
        return f"<Stock(id={self.id}, symbol='{self.symbol}', name='{self.name}')>"
    
# ============ StockFinancialIndicator 模型（stock财务指标表）============
class StockFinancialIndicator(Base):
    """
    stock财务指标表
    存储stock的各类财务分析指标
    """
    __tablename__ = "stock_financial_indicators"
    
    # 主键
    id = Column(Integer, primary_key=True, index=True)
    
    # 外键关联：这条指标数据属于哪只stock
    stock_id = Column(String, ForeignKey("stocks.symbol", ondelete="CASCADE"), nullable=False, index=True, comment="代码")
    
    # 财务指标字段:
    #    ['日期', '摊薄每股收益(元)', '加权每股收益(元)', '每股收益_调整后(元)', '扣除非经常性损益后的每股收益(元)',
    #    '每股净资产_调整前(元)', '每股净资产_调整后(元)', '每股经营性现金流(元)', '每股资本公积金(元)',
    #    '每股未分配利润(元)', '调整后的每股净资产(元)', '总资产利润率(%)', '主营业务利润率(%)', '总资产净利润率(%)',
    #    '成本费用利润率(%)', '营业利润率(%)', '主营业务成本率(%)', '销售净利率(%)', '股本报酬率(%)',
    #    '净资产报酬率(%)', '资产报酬率(%)', '销售毛利率(%)', '三项费用比重', '非主营比重', '主营利润比重',
    #    '股息发放率(%)', '投资收益率(%)', '主营业务利润(元)', '净资产收益率(%)', '加权净资产收益率(%)',
    #    '扣除非经常性损益后的净利润(元)', '主营业务收入增长率(%)', '净利润增长率(%)', '净资产增长率(%)',
    #    '总资产增长率(%)', '应收账款周转率(次)', '应收账款周转天数(天)', '存货周转天数(天)', '存货周转率(次)',
    #    '固定资产周转率(次)', '总资产周转率(次)', '总资产周转天数(天)', '流动资产周转率(次)', '流动资产周转天数(天)',
    #    '股东权益周转率(次)', '流动比率', '速动比率', '现金比率(%)', '利息支付倍数', '长期债务与营运资金比率(%)',
    #    '股东权益比率(%)', '长期负债比率(%)', '股东权益与固定资产比率(%)', '负债与所有者权益比率(%)',
    #    '长期资产与长期资金比率(%)', '资本化比率(%)', '固定资产净值率(%)', '资本固定化比率(%)', '产权比率(%)',
    #    '清算价值比率(%)', '固定资产比重(%)', '资产负债率(%)', '总资产(元)', '经营现金净流量对销售收入比率(%)',
    #    '资产的经营现金流量回报率(%)', '经营现金净流量与净利润的比率(%)', '经营现金净流量对负债比率(%)', '现金流量比率(%)',
    #    '短期股票投资(元)', '短期债券投资(元)', '短期其它经营性投资(元)', '长期股票投资(元)', '长期债券投资(元)',
    #    '长期其它经营性投资(元)', '1年以内应收帐款(元)', '1-2年以内应收帐款(元)', '2-3年以内应收帐款(元)',
    #    '3年以内应收帐款(元)', '1年以内预付货款(元)', '1-2年以内预付货款(元)', '2-3年以内预付货款(元)',
    #    '3年以内预付货款(元)', '1年以内其它应收款(元)', '1-2年以内其它应收款(元)', '2-3年以内其它应收款(元)',
    #    '3年以内其它应收款(元)'],
    report_date = Column(String, nullable=False, index=True, comment="日期")
    diluted_eps = Column(Float, comment="摊薄每股收益(元)")
    weighted_eps = Column(Float, comment="加权每股收益(元)")
    adjusted_eps = Column(Float, comment="每股收益_调整后(元)")
    non_recurring_eps = Column(Float, comment="扣除非经常性损益后的每股收益(元)")
    adjusted_net_assets_pre_share = Column(Float, comment="每股净资产_调整前(元)")
    adjusted_net_assets_post_share = Column(Float, comment="每股净资产_调整后(元)")
    operating_cash_flow_per_share = Column(Float, comment="每股经营性现金流(元)")
    capital_reserve_per_share= Column(Float, comment="每股资本公积金(元)")
    undistributed_profit_per_share= Column(Float, comment="每股未分配利润(元)")
    adjusted_net_assets_per_share= Column(Float, comment="调整后的每股净资产(元)")
    total_asset_return_rate= Column(Float, comment="总资产利润率(%)")
    main_business_profit_margin= Column(Float, comment="主营业务利润率(%)")
    total_asset_net_profit_rate= Column(Float, comment="总资产净利润率(%)")
    cost_expense_profit_margin= Column(Float, comment="成本费用利润率(%)")
    operating_profit_margin= Column(Float, comment="营业利润率(%)")
    main_business_cost_rate= Column(Float, comment="主营业务成本率(%)")
    sales_net_profit_margin= Column(Float, comment="销售净利率(%)")
    shareholder_return_rate= Column(Float, comment="股本报酬率(%)")
    net_asset_return_rate= Column(Float, comment="净资产报酬率(%)")
    asset_return_rate= Column(Float, comment="资产报酬率(%)")
    sales_gross_profit_margin= Column(Float, comment="销售毛利率(%)")
    three_expenses_ratio= Column(Float, comment="三项费用比重")
    non_main_business_ratio= Column(Float, comment="非主营比重")
    main_business_profit_ratio= Column(Float, comment="主营利润比重")
    dividend_payout_ratio= Column(Float, comment="股息发放率(%)")
    investment_return_rate= Column(Float, comment="投资收益率(%)")
    main_business_profit= Column(Float, comment="主营业务利润(元)")
    return_on_equity= Column(Float, comment="净资产收益率(%)")
    weighted_return_on_equity= Column(Float, comment="加权净资产收益率(%)")
    net_profit_excluding_non_recurring_items= Column(Float, comment="扣除非经常性损益后的净利润(元)")
    main_business_income_growth_rate= Column(Float, comment="主营业务收入增长率(%)")
    net_profit_growth_rate= Column(Float, comment="净利润增长率(%)")
    net_asset_growth_rate= Column(Float, comment="净资产增长率(%)")
    total_asset_growth_rate= Column(Float, comment="总资产增长率(%)")
    accounts_receivable_turnover= Column(Float, comment="应收账款周转率(次)")
    accounts_receivable_turnover_days= Column(Float, comment="应收账款周转天数(天)")
    inventory_turnover_days= Column(Float, comment="存货周转天数(天)")
    inventory_turnover= Column(Float, comment="存货周转率(次)")
    fixed_assets_turnover= Column(Float, comment="固定资产周转率(次)")
    total_assets_turnover= Column(Float, comment="总资产周转率(次)")
    total_assets_turnover_days= Column(Float, comment="总资产周转天数(天)")
    current_assets_turnover= Column(Float, comment="流动资产周转率(次)")
    current_assets_turnover_days= Column(Float, comment="流动资产周转天数(天)")
    shareholder_equity_turnover= Column(Float, comment="股东权益周转率(次)")
    current_ratio= Column(Float, comment="流动比率")
    quick_ratio= Column(Float, comment="速动比率")
    cash_ratio= Column(Float, comment="现金比率(%)")
    interest_coverage_ratio= Column(Float, comment="利息支付倍数")
    long_debt_to_working_capital_ratio= Column(Float, comment="长期债务与营运资金比率(%)")
    equity_ratio= Column(Float, comment="股东权益比率(%)")
    long_debt_to_asset_ratio= Column(Float, comment="长期负债比率(%)")
    equity_to_fixed_assets_ratio= Column(Float, comment="股东权益与固定资产比率(%)")
    liability_to_equity_ratio= Column(Float, comment="负债与所有者权益比率(%)")
    long_asset_to_long_fund_ratio= Column(Float, comment="长期资产与长期资金比率(%)")
    capitalized_ratio= Column(Float, comment="资本化比率(%)")
    fixed_assets_net_value_ratio= Column(Float, comment="固定资产净值率(%)")
    capital_fixed_ratio= Column(Float, comment="资本固定化比率(%)")
    equity_ratio2= Column(Float, comment="产权比率(%)")
    liquidation_value_ratio= Column(Float, comment="清算价值比率(%)")
    fixed_assets_ratio= Column(Float, comment="固定资产比重(%)")
    debt_to_asset_ratio= Column(Float, comment="资产负债率(%)")
    total_assets= Column(Float, comment="总资产(元)")
    operating_cash_flow_to_sales_ratio= Column(Float, comment="经营现金净流量对销售收入比率(%)")
    asset_operating_cash_flow_return_rate= Column(Float, comment="资产的经营现金流量回报率(%)")
    operating_cash_flow_to_net_profit_ratio= Column(Float, comment="经营现金净流量与净利润的比率(%)")
    operating_cash_flow_to_liability_ratio= Column(Float, comment="经营现金净流量对负债比率(%)")
    cash_flow_ratio= Column(Float, comment="现金流量比率(%)")
    short_term_stock_investment= Column(Float, comment="短期股票投资(元)")
    short_term_bond_investment= Column(Float, comment="短期债券投资(元)")
    short_term_other_operating_investments= Column(Float, comment="短期其它经营性投资(元)")
    long_term_stock_investment= Column(Float, comment="长期股票投资(元)")
    long_term_bond_investment= Column(Float, comment="长期债券投资(元)")
    long_term_other_operating_investments= Column(Float, comment="长期其它经营性投资(元)")
    accounts_receivable_within_1y= Column(Float, comment="1年以内应收帐款(元)")
    accounts_receivable_1_2y= Column(Float, comment="1-2年以内应收帐款(元)")
    accounts_receivable_2_3y= Column(Float, comment="2-3年以内应收帐款(元)")
    accounts_receivable_above_3y= Column(Float, comment="3年以内应收帐款(元)")
    prepayments_within_1y= Column(Float, comment="1年以内预付货款(元)")
    prepayments_1_2y= Column(Float, comment="1-2年以内预付货款(元)")
    prepayments_2_3y= Column(Float, comment="2-3年以内预付货款(元)")
    prepayments_above_3y= Column(Float, comment="3年以内预付货款(元)")
    other_receivables_within_1y= Column(Float, comment="1年以内其它应收款(元)")
    other_receivables_1_2y= Column(Float, comment="1-2年以内其它应收款(元)")
    other_receivables_2_3y= Column(Float, comment="2-3年以内其它应收款(元)")
    other_receivables_above_3y= Column(Float, comment="3年以内其它应收款(元)")

    # 关系定义：指标属于一只stock
    stock = relationship("Stock")
    
    # 复合唯一约束：同一stock同一报告日期只能有一条记录
    __table_args__ = (
        Index('idx_stock_report_date', 'stock_id', 'report_date', unique=True),
    )
    
    def __repr__(self):
        return f"<StockFinancialIndicator(stock_id={self.stock_id}, report_date={self.report_date})>"

# ============ News 模型（新闻表）============
class News(Base):
    """
    stock新闻与舆情表
    存储新闻内容和AI分析结果
    """
    __tablename__ = "news"
    
    # 主键
    id = Column(Integer, primary_key=True, index=True)
    
    # 外键关联：这条新闻属于哪只stock
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
    
    # 关系定义：新闻属于一只stock
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
    
    # 外键关联：这个信号属于哪只stock
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
    
    # 关系定义：信号属于一只stock
    stock = relationship("Stock", back_populates="signals")
    
    # 时间戳
    generated_at = Column(DateTime, default=datetime.now(TZ), nullable=False, index=True)
    
    def __repr__(self):
        return f"<Signal(id={self.id}, stock_id={self.stock_id}, type={self.signal_type}, strength={self.strength})>"

# ============ stock历史价格表 ============
class StockPrice(Base):
    """
    stock历史价格表（可选，根据需求添加）
    用于存储每日价格数据，支持技术分析,参数包括：
    id - 主键
    stock_id - 外键，关联Stock表的symbol字段
    date - 日期
    open_price - 开盘价
    close_price - 收盘价
    high_price - 最高价
    low_price - 最低价
    volume - 成交量
    amount - 成交额
    outstanding_share - 流通股本
    change_percent - 涨跌幅%
    change_amount - 涨跌额
    turnover - 换手率%
    """
    __tablename__ = "stock_prices"
    
    id = Column(Integer, primary_key=True, index=True)
    stock_id = Column(String, ForeignKey("stocks.symbol", ondelete="CASCADE"), nullable=False, index=True)
    
    # 价格数据
    date = Column(String, nullable=False, index=True, comment="交易日")
    open_price = Column(Float, comment="开盘价")
    close_price = Column(Float, comment="收盘价")
    high_price = Column(Float, comment="最高价")
    low_price = Column(Float, comment="最低价")
    volume = Column(Float, comment="成交量")
    amount = Column(Float, comment="成交额")
    outstanding_share = Column(Float, comment="流通股本")
    change_percent = Column(Float, comment="涨跌幅%")
    change_amount = Column(Float, comment="涨跌额")
    turnover = Column(Float, comment="换手率%")
    
    # 复权因子
    adj_factor = Column(Float, default=1.0, comment="复权因子")
    
    # 关系
    stock = relationship("Stock")
    
    # 复合唯一约束：同一stock同一日期只能有一条记录
    __table_args__ = (
        # 这里使用Index创建复合索引和唯一约束
        Index('idx_stock_date', 'stock_id', 'date', unique=True),
    )
    
    def __repr__(self):
        return f"<StockPrice(stock_id={self.stock_id}, date={self.date}, close={self.close_price})>"