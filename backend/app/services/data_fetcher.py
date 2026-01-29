# 数据获取
import akshare as ak
import pandas as pd
from datetime import datetime, timedelta
from typing import List, Dict, Optional
import time
from sqlalchemy.orm import Session
from sqlalchemy.exc import IntegrityError
import logging

# attempted relative import with no known parent package问题解决：
# 在Python中，相对导入（如 from ..models import Stock）要求当前模块是作为包的一部分被导入的。
# 但在脚本直接运行时（如通过 python data_fetcher.py），它被视为主程序而非包的一部分，导致相对导入失败。
from models import Stock, StockPrice, MarketType
from database import SessionLocal

# 配置日志
logger = logging.getLogger(__name__)

class DataFetcher:
    """
    数据获取服务类
    提供从第三方数据源获取股票数据的功能
    使用场景为：
    - 启动初始化：
    - 定时任务：每日收盘后获取最新数据
    - 按需请求：用户请求时获取最新数据
    主要方法包括：
    - fetch_stock_list: 获取股票列表
    - fetch_stock_daily: 获取股票日线数据
    - fetch_stock_realtime: 获取股票实时数据
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
        
    def fetch_stock_list(self, market: MarketType = "SH") -> pd.DataFrame:
        """
        获取股票列表
        Args:
            market: 市场类型
        Returns:
            股票列表DataFrame
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
            symbol: str, 
            start_date: str = "20200101",
            end_date: Optional[str] = None,
            adjust: str = "qfq"
        ) -> pd.DataFrame:
            """
            获取股票日线数据
            
            Args:
                symbol: 股票代码，如 "000001"
                start_date: 开始日期，格式 "YYYYMMDD"
                end_date: 结束日期，默认今天
                adjust: 复权类型，"qfq"(前复权), "hfq"(后复权), ""(不复权)
                
            Returns:
                DataFrame 包含日期、开盘、收盘、最高、最低、成交量等
            """
            if end_date is None:
                end_date = datetime.now().strftime("%Y%m%d")
            
            for attempt in range(self.max_retries):
                try:
                    # 根据股票代码判断市场
                    if symbol.startswith(("0", "3")):
                        market = "SZ"
                    elif symbol.startswith("6"):
                        market = "SH"
                    elif symbol.startswith("8"):
                        market = "BJ"
                    else:
                        market = "SZ"  # 默认
                    
                    # 获取日线数据
                    stock_code = f"{symbol}.{market}"
                    df = ak.stock_zh_a_hist(
                        symbol=symbol,
                        period="daily",
                        start_date=start_date,
                        end_date=end_date,
                        adjust=adjust
                    )
                    
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
                    
                    logger.info(f"成功获取 {symbol} 从 {start_date} 到 {end_date} 的 {len(df)} 条日线数据")
                    return df
                    
                except Exception as e:
                    logger.error(f"第 {attempt+1} 次获取 {symbol} 日线数据失败: {e}")
                    if attempt < self.max_retries - 1:
                        time.sleep(self.retry_delay)
                    else:
                        return pd.DataFrame()
    
    def fetch_stock_realtime(self, symbols: List[str]) -> pd.DataFrame:
        """
        获取股票实时数据
        
        Args:
            symbols: 股票代码列表
            
        Returns:
            DataFrame 包含实时行情数据
        """
        try:
            # 获取实时行情数据
            df = ak.stock_zh_a_spot_em()
            
            # 过滤出需要的股票
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
            获取并保存股票信息及价格数据（完整流程）
            
            Args:
                db: 数据库会话
                symbol: 股票代码
                days: 获取最近多少天的数据
                
            Returns:
                包含操作结果的字典
            """
            result = {
                "symbol": symbol,
                "stock_saved": False,
                "prices_saved": 0,
                "error": None
            }
            
            try:
                # 1. 获取股票实时信息（如果可能）
                realtime_data = self.fetch_stock_realtime([symbol])
                
                if not realtime_data.empty:
                    stock_info = {
                        "symbol": symbol,
                        "name": realtime_data.iloc[0].get("name", f"股票{symbol}"),
                        "current_price": realtime_data.iloc[0].get("current_price"),
                        "market": "SZ" if str(symbol).startswith(("0", "3")) else "SH"
                    }
                else:
                    # 如果无法获取实时数据，创建基础信息
                    stock_info = {
                        "symbol": symbol,
                        "name": f"股票{symbol}",
                        "market": "SZ" if str(symbol).startswith(("0", "3")) else "SH"
                    }
                
                # 2. 保存股票信息到数据库
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
                    result["error"] = "保存股票信息失败"
                
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
        保存股票信息到数据库
        
        Args:
            db: 数据库会话
            stock_info: 股票信息字典
            
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
            logger.error(f"保存股票 {stock_info['symbol']} 失败，可能已存在: {e}")
            db.rollback()
            return None
        except Exception as e:
            logger.error(f"保存股票 {stock_info['symbol']} 失败: {e}")
            db.rollback()
            return None