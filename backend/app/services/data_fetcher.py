# 数据获取
import akshare as ak
import pandas as pd
from datetime import datetime, timedelta
from typing import List, Dict, Optional
import time
from sqlalchemy.orm import Session
from sqlalchemy.exc import IntegrityError
import logging
import requests

# attempted relative import with no known parent package问题解决：
# 在Python中，相对导入（如 from ..models import Stock）要求当前模块是作为包的一部分被导入的。
# 但在脚本直接运行时（如通过 python data_fetcher.py），它被视为主程序而非包的一部分，导致相对导入失败。
from models import Stock, StockPrice, MarketType, StockFinancialIndicator

# 配置日志
logger = logging.getLogger(__name__)

class DataFetcher:
    """
    数据获取服务类
    提供从第三方数据源获取stock数据的功能
    使用场景为：
    - 启动初始化：
    - 定时任务：每日收盘后获取最新数据
    - 按需请求：用户请求时获取最新数据
    主要方法包括：
    - fetch_stock_list: 获取stock列表
    - fetch_stock_daily: 获取stock日线数据
    - fetch_stock_realtime: 获取stock实时数据
    其他方法可根据需要添加
    """
    def __init__(self, max_retries: int = 3, retry_delay: int = 2):
        """
        初始化数据获取器
        
        Args:
            max_retries: 最大重试次数，默认3次
            retry_delay: 重试延迟（秒），默认2秒
        """
        self.max_retries = max_retries
        self.retry_delay = retry_delay
        
    def update_stock_list(self, db: Session):
        """
        更新stock列表到数据库
        Args:
            db: 数据库会话
        """
        # 市场信息
        # market = Column(Enum(MarketType), default=MarketType.SZ, comment="所属市场")
        # industry = Column(String(50), comment="所属行业")
        # listing_date = Column(DateTime, comment="上市日期")
        
        # # 基础财务数据（可定期更新）
        # current_price = Column(Float, comment="当前价格")
        # market_cap = Column(Float, comment="市值（亿元）")
        # pe_ratio = Column(Float, comment="市盈率")
        # pb_ratio = Column(Float, comment="市净率")
        
        # 查询是否存在stock表
        stockTable = db.query(Stock).first()
        if stockTable:
            print("Stock表已存在，跳过创建")
        else:
            df_base = ak.stock_info_a_code_name()
            for _, row in df_base.iterrows():
                # 检查是否已存在
                stock = db.query(Stock).filter(Stock.symbol == row['code']).first()
                symbol=row['code']
                if symbol.startswith(("0", "3")):
                    market = "SZ"
                elif symbol.startswith("6"):
                    market = "SH"
                elif symbol.startswith("8"):
                    market = "BJ"
                else:
                    market = "SZ"  # 默认
                if not stock:
                    stock = Stock(
                        symbol = symbol,
                        name=row['name'],
                        market = market
                    )
                    db.add(stock)

            # 查询行业、上市日期等信息
            # try:
            #     stock_info = ak.stock_individual_info_em(symbol=row['code'])
            #     # 更新日线数据
                
            #     if not stock_info.empty:
            #         stock.industry = stock_info.iloc[0].get("行业")
            #         listing_date_str = stock_info.iloc[0].get("上市时间")
            #         if listing_date_str:
            #             stock.listing_date = datetime.strptime(listing_date_str, "%Y-%m-%d")
            #     db.commit()
            # except Exception as e:
            #     logger.error(f"获取 {row['code']} 行业和上市日期失败: {e}")
        # 后台更新数据库
        symbols = db.query(Stock.symbol).all()
        for symbol in symbols:
            print("======={symbol}=======")
            # self.fetch_stock_daily(db, symbol[0])
            # cmd执行指令：curl -X POST "http://127.0.0.1:8082/api/v1/stocks/{symbol}/fetch_stock_daily"
            # 日期限定在30日内
            start_date = (datetime.now() - timedelta(days=30)).strftime("%Y%m%d")
            end_date = datetime.now().strftime("%Y%m%d")
            requests.post("http://127.0.0.1:8082/api/v1/stocks/" + symbol[0] + "/fetch_stock_daily?start_date=" + start_date + "&end_date=" + end_date)
        logger.info("Stock列表已更新到数据库")
        
    def fetch_stock_list(self, market: MarketType = "SH") -> pd.DataFrame:
        """
        获取stock列表
        Args:
            market: 市场类型
        Returns:
            stock列表DataFrame
        """
        for attempt in range(self.max_retries):
            try:
                if market == MarketType.SZ:
                    stock_df = ak.stock_info_sz_name_code()
                elif market == MarketType.SH:
                    stock_df = ak.stock_info_sh_name_code()
                else:
                    raise ValueError(f"Unsupported market type: {market}")
                return stock_df
            except Exception as e:
                logger.error(f"Error fetching stock list for {market}: {e}")
                if attempt < self.max_retries - 1:
                    time.sleep(self.retry_delay)
                else:
                    raise
                
    def fetch_stock_daily(
            self, 
            db : Session,
            symbol: str, 
            start_date: str = "20200101",
            end_date: Optional[str] = None,
            adjust: str = "qfq"
        ) -> pd.DataFrame:
            """
            获取stock日线数据
            
            Args:
                symbol: stock代码，如 "000001"
                start_date: 开始日期，格式 "YYYYMMDD"
                end_date: 结束日期，默认今天
                adjust: 复权类型，"qfq"(前复权), "hfq"(后复权), ""(不复权)
                
            Returns:
                DataFrame 包含日期、开盘、收盘、最高、最低、成交量等
            """
            if end_date is None:
                end_date = datetime.now().strftime("%Y%m%d")
            
            for attempt in range(self.max_retries):
                # 重试获取数据
                try:
                    # 根据stock代码判断市场
                    if symbol.startswith(("0", "3")):
                        market = "sz"
                    elif symbol.startswith("6"):
                        market = "sh"
                    elif symbol.startswith("8"):
                        market = "bj"
                    else:
                        market = "sz"  # 默认
                    
                    # 获取日线数据
                    # stock_code = f"{market}{symbol}"
                    # df = ak.stock_zh_a_hist(
                    #     symbol=symbol,
                    #     period="daily",
                    #     start_date=start_date,
                    #     end_date=end_date,
                    #     adjust=adjust
                    # )
                    print(f"start_date: {start_date}, end_date: {end_date}")
                    df = ak.stock_zh_a_daily(market + symbol, start_date, end_date)
                    
                    if df.empty:
                        logger.warning(f"未获取到 {symbol} 的历史数据")
                        return df
                    
                    # 重命名列以符合我们的数据库字段
                    column_mapping = {
                        "日期": "date",
                        "开盘": "open_price",
                        "收盘": "close_price",
                        "最高": "high_price",
                        "最低": "low_price",
                        "成交量": "volume",
                        "成交额": "turnover",
                        "振幅": "amplitude",
                        "涨跌幅": "change_percent",
                        "涨跌额": "change_amount",
                        "换手率": "turnover_rate"
                    }
                    
                    df = df.rename(columns=column_mapping)
                    df["symbol"] = symbol
                    df["market"] = market
                    
                    logger.info(f"成功获取 {market + symbol} 从 {start_date} 到 {end_date} 的 {len(df)} 条日线数据")
                    # 写入数据库
                    for _, row in df.iterrows():
                        price = StockPrice(
                            stock_id=symbol,
                            date=row["date"],
                            open_price=row["open"],
                            close_price=row["close"],
                            high_price=row["high"],
                            low_price=row["low"],
                            volume=row["volume"],
                            amount = row.get("amount"),
                            outstanding_share = row.get("outstanding_share"),
                            turnover=row.get("turnover")
                        )
                        db.merge(price)  # 使用merge避免重复插入
                        db.commit()
                    return df
                    
                except Exception as e:
                    logger.error(f"第 {attempt+1} 次获取 {market + symbol} 日线数据失败: {e}")
                    if attempt < self.max_retries - 1:
                        time.sleep(self.retry_delay)
                    else:
                        return pd.DataFrame()
    
    def fetch_stock_realtime(self, symbols: List[str]) -> pd.DataFrame:
        """
        获取stock实时数据
        
        Args:
            symbols: stock代码列表
            
        Returns:
            DataFrame 包含实时行情数据
        """
        # 使用stock_data_daily = ak.stock_zh_a_daily(symbol, start_date, end_date)
        # ak.stock_zh_a_spot_em() 返回所有沪深京A股的实时行情    
        # df = ak.stock_zh_a_spot_em()
        print(df.columns)
            
        try:
            # 获取实时行情数据
            
            
            # 过滤出需要的stock
            if symbols:
                df = df[df["代码"].isin(symbols)]
            
            # 重命名列
            column_mapping = {
                "代码": "symbol",
                "名称": "name",
                "最新价": "current_price",
                "涨跌幅": "change_percent",
                "涨跌额": "change_amount",
                "成交量": "volume",
                "成交额": "turnover",
                "振幅": "amplitude",
                "最高": "high_price",
                "最低": "low_price",
                "今开": "open_price",
                "昨收": "pre_close",
                "换手率": "turnover_rate",
                "市盈率-动态": "pe_ratio",
                "市净率": "pb_ratio",
                "总市值": "total_market_cap",
                "流通市值": "circulating_market_cap"
            }
            
            df = df.rename(columns=column_mapping)
            return df
            
        except Exception as e:
            logger.error(f"获取实时数据失败: {e}")
            return pd.DataFrame()
        
    def fetch_and_save_stock_with_prices(
            self, 
            db: Session, 
            symbol: str, 
            days: int = 30
        ) -> Dict:
            """
            获取并保存stock信息及价格数据（完整流程）
            
            Args:
                db: 数据库会话
                symbol: stock代码
                days: 获取最近多少天的数据
                
            Returns:
                包含操作结果的字典
            """
            # 初始化结果字典
            result = {
                "symbol": symbol,       # stock代码
                "stock_saved": False,   # stock信息是否保存成功
                "prices_saved": 0,      # 保存的价格数据条数
                "error": None           # 错误信息（如果有）
            }
            
            print("====result====\n",result)
            
            try:
                # 1. 获取stock实时信息（如果可能）
                realtime_data = self.fetch_stock_realtime([symbol])
                
                if not realtime_data.empty:
                    stock_info = {
                        "symbol": symbol,
                        "name": realtime_data.iloc[0].get("name", f"{symbol}"),
                        "current_price": realtime_data.iloc[0].get("current_price"),
                        "market": "SZ" if str(symbol).startswith(("0", "3")) else "SH"
                    }
                else:
                    # 如果无法获取实时数据，创建基础信息
                    stock_info = {
                        "symbol": symbol,
                        "name": f"{symbol}",
                        "market": "SZ" if str(symbol).startswith(("0", "3")) else "SH"
                    }
                
                print("=========stock_info=========")
                print(stock_info)
                
                # 2. 保存stock信息到数据库
                stock = self.save_stock_to_db(db, stock_info)
                if stock:
                    result["stock_saved"] = True
                    
                    # 3. 计算日期范围
                    from datetime import datetime, timedelta
                    end_date = datetime.now()
                    start_date = end_date - timedelta(days=days)
                    start_date_str = start_date.strftime("%Y%m%d")
                    end_date_str = end_date.strftime("%Y%m%d")
                    
                    # 4. 获取日线数据
                    price_df = self.fetch_stock_daily(
                        symbol=symbol,
                        start_date=start_date_str,
                        end_date=end_date_str
                    )
                    
                    if not price_df.empty:
                        # 5. 保存价格数据
                        saved_count = self.save_stock_prices_to_db(db, symbol, price_df)
                        result["prices_saved"] = saved_count
                    else:
                        result["error"] = "无法获取价格数据"
                        
                else:
                    result["error"] = "保存stock信息失败"
                
                return result
                
            except Exception as e:
                error_msg = f"获取并保存 {symbol} 数据失败: {str(e)}"
                import logging
                logger = logging.getLogger(__name__)
                logger.error(error_msg)
                result["error"] = error_msg
                return result
            
    def save_stock_to_db(self, db: Session, stock_info: Dict) -> Optional[Stock]:
        """
        保存stock信息到数据库
        
        Args:
            db: 数据库会话
            stock_info: stock信息字典
            
        Returns:
            保存的Stock对象或None
        """
        try:
            stock = db.query(Stock).filter(Stock.symbol == stock_info["symbol"]).first()
            if not stock:
                stock = Stock(**stock_info)
                db.add(stock)
                db.commit()
                db.refresh(stock)
            return stock
        except IntegrityError as e:
            logger.error(f"保存stock {stock_info['symbol']} 失败，可能已存在: {e}")
            db.rollback()
            return None
        except Exception as e:
            logger.error(f"保存stock {stock_info['symbol']} 失败: {e}")
            db.rollback()
            return None
        
    def save_stock_prices_to_db(self, db: Session, symbol: str, price_df: pd.DataFrame) -> int:
        """
        保存stock价格数据到数据库
        
        Args:
            db: 数据库会话
            symbol: stock代码
            price_df: 价格数据DataFrame
            
        Returns:
            保存的记录数
        """
        saved_count = 0
        for _, row in price_df.iterrows():
            try:
                # 检查是否已存在
                existing_price = db.query(StockPrice).filter(
                    StockPrice.symbol == symbol,
                    StockPrice.date == row["date"]
                ).first()
                
                if not existing_price:
                    stock_price = StockPrice(
                        symbol=symbol,
                        date=row["date"],
                        open_price=row["open_price"],
                        close_price=row["close_price"],
                        high_price=row["high_price"],
                        low_price=row["low_price"],
                        volume=row["volume"],
                        turnover=row.get("turnover"),
                        change_percent=row.get("change_percent"),
                        change_amount=row.get("change_amount"),
                        turnover_rate=row.get("turnover_rate")
                    )
                    db.add(stock_price)
                    saved_count += 1
            except Exception as e:
                logger.error(f"保存价格数据失败 for {symbol} on {row['date']}: {e}")
        
        try:
            db.commit()
        except Exception as e:
            logger.error(f"提交价格数据失败 for {symbol}: {e}")
            db.rollback()
        
        return saved_count
    
    def stock_analysis_indicator(self, db: Session, symbol : str = "600004", start_year : str = "2025"):
        '''
        获取财务指标,
        并保存到数据库中
        '''
        analysis = ak.stock_financial_analysis_indicator(symbol, start_year)
        # 更新到数据库：
        # 根据symbol和日期查找对应的StockFinancialIndicator记录，若不存在则创建新记录
        for _, row in analysis.iterrows():
            date_str = row['日期']
            indicator = db.query(StockFinancialIndicator).filter(
                StockFinancialIndicator.stock_id == symbol,
                StockFinancialIndicator.report_date == date_str
            ).first()
            if not indicator:
                indicator = StockFinancialIndicator(
                    stock_id=symbol,
                    report_date=date_str,
                    diluted_eps=row.get('摊薄每股收益(元)'),
                    weighted_eps=row.get('加权每股收益(元)'),
                    adjusted_eps=row.get('每股收益_调整后(元)'),
                    non_recurring_eps=row.get('扣除非经常性损益后的每股收益(元)'),
                    adjusted_net_assets_pre_share=row.get('每股净资产_调整前(元)'),
                    adjusted_net_assets_post_share=row.get('每股净资产_调整后(元)'),
                    operating_cash_flow_per_share=row.get('每股经营性现金流(元)'),
                    capital_reserve_per_share=row.get('每股资本公积金(元)'),
                    undistributed_profit_per_share=row.get('每股未分配利润(元)'),
                    adjusted_net_assets_per_share=row.get('调整后的每股净资产(元)'),
                    total_asset_return_rate=row.get('总资产利润率(%)'),
                    main_business_profit_margin=row.get('主营业务利润率(%)'),
                    total_asset_net_profit_rate=row.get('总资产净利润率(%)'),
                    cost_expense_profit_margin=row.get('成本费用利润率(%)'),
                    operating_profit_margin=row.get('营业利润率(%)'),
                    main_business_cost_rate=row.get('主营业务成本率(%)'),
                    sales_net_profit_margin=row.get('销售净利率(%)'),
                    shareholder_return_rate=row.get('股本报酬率(%)'),
                    net_asset_return_rate=row.get('净资产报酬率(%)'),
                    asset_return_rate=row.get('资产报酬率(%)'),
                    sales_gross_profit_margin=row.get('销售毛利率(%)'),
                    three_expenses_ratio=row.get('三项费用比重'),
                    non_main_business_ratio=row.get('非主营比重'),
                    main_business_profit_ratio=row.get('主营利润比重'),
                    dividend_payout_ratio=row.get('股息发放率(%)'),
                    investment_return_rate=row.get('投资收益率(%)'),
                    main_business_profit=row.get('主营业务利润(元)'),
                    return_on_equity=row.get('净资产收益率(%)'),
                    weighted_return_on_equity=row.get('加权净资产收益率(%)'),
                    net_profit_excluding_non_recurring_items=row.get('扣除非经常性损益后的净利润(元)'),
                    main_business_income_growth_rate=row.get('主营业务收入增长率(%)'),
                    net_profit_growth_rate=row.get('净利润增长率(%)'),
                    net_asset_growth_rate=row.get('净资产增长率(%)'),
                    total_asset_growth_rate=row.get('总资产增长率(%)'),
                    accounts_receivable_turnover=row.get('应收账款周转率(次)'),
                    accounts_receivable_turnover_days=row.get('应收账款周转天数(天)'),
                    inventory_turnover_days=row.get('存货周转天数(天)'),
                    inventory_turnover=row.get('存货周转率(次)'),
                    fixed_assets_turnover=row.get('固定资产周转率(次)'),
                    total_assets_turnover=row.get('总资产周转率(次)'),
                    total_assets_turnover_days=row.get('总资产周转天数(天)'),
                    current_assets_turnover=row.get('流动资产周转率(次)'),
                    current_assets_turnover_days=row.get('流动资产周转天数(天)'),
                    shareholder_equity_turnover=row.get('股东权益周转率(次)'),
                    current_ratio=row.get('流动比率'),
                    quick_ratio=row.get('速动比率'),
                    cash_ratio=row.get('现金比率(%)'),
                    interest_coverage_ratio=row.get('利息支付倍数'),
                    long_debt_to_working_capital_ratio=row.get('长期债务与营运资金比率(%)'),
                    equity_ratio=row.get('股东权益比率(%)'),
                    long_debt_to_asset_ratio=row.get('长期负债比率(%)'),
                    equity_to_fixed_assets_ratio=row.get('股东权益与固定资产比率(%)'),
                    liability_to_equity_ratio=row.get('负债与所有者权益比率(%)'),
                    long_asset_to_long_fund_ratio=row.get('长期资产与长期资金比率(%)'),
                    capitalized_ratio=row.get('资本化比率(%)'),
                    fixed_assets_net_value_ratio=row.get('固定资产净值率(%)'),
                    capital_fixed_ratio=row.get('资本固定化比率(%)'),
                    equity_ratio2=row.get('产权比率(%)'),
                    liquidation_value_ratio=row.get('清算价值比率(%)'),
                    fixed_assets_ratio=row.get('固定资产比重(%)'),
                    debt_to_asset_ratio=row.get('资产负债率(%)'),
                    total_assets=row.get('总资产(元)'),
                    operating_cash_flow_to_sales_ratio=row.get('经营现金净流量对销售收入比率(%)'),
                    asset_operating_cash_flow_return_rate=row.get('资产的经营现金流量回报率(%)'),
                    operating_cash_flow_to_net_profit_ratio=row.get('经营现金净流量与净利润的比率(%)'),
                    operating_cash_flow_to_liability_ratio=row.get('经营现金净流量对负债比率(%)'),
                    cash_flow_ratio=row.get('现金流量比率(%)'),
                    short_term_stock_investment=row.get('短期股票投资(元)'),
                    short_term_bond_investment=row.get('短期债券投资(元)'),
                    short_term_other_operating_investments=row.get('短期其它经营性投资(元)'),
                    long_term_stock_investment=row.get('长期股票投资(元)'),
                    long_term_bond_investment=row.get('长期债券投资(元)'),
                    long_term_other_operating_investments=row.get('长期其它经营性投资(元)'),
                    accounts_receivable_within_1y=row.get('1年以内应收帐款(元)'),
                    accounts_receivable_1_2y=row.get('1-2年以内应收帐款(元)'),
                    accounts_receivable_2_3y=row.get('2-3年以内应收帐款(元)'),
                    accounts_receivable_above_3y=row.get('3年以内应收帐款(元)'),
                    prepayments_within_1y=row.get('1年以内预付货款(元)'),
                    prepayments_1_2y=row.get('1-2年以内预付货款(元)'),
                    prepayments_2_3y=row.get('2-3年以内预付货款(元)'),
                    prepayments_above_3y=row.get('3年以内预付货款(元)'),
                    other_receivables_within_1y=row.get('1年以内其它应收款(元)'),
                    other_receivables_1_2y=row.get('1-2年以内其它应收款(元)'),
                    other_receivables_2_3y=row.get('2-3年以内其它应收款(元)'),
                    other_receivables_above_3y=row.get('3年以内其它应收款(元)')
                )
                db.add(indicator)
        db.commit()
        return analysis
        
