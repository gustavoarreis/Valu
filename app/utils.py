from typing import Any
import streamlit as st
import pandas as pd
import numpy as np
from yahooquery import Ticker
from logger import logger
from functools import wraps
import time

def timer_decorator(func):
    def wrapper(*args, **kwargs):
        start_time = time.time()
        result = func(*args, **kwargs)
        end_time = time.time()
        execution_time = end_time - start_time
        logger.info(f"Function '{func.__name__}' execution time: {execution_time} seconds")
        return result
    return wrapper

@timer_decorator
def create_input_group(group_name, value: float = 1.0, step: float = 1.0):
    st.sidebar.subheader(group_name)
    pessimist = st.sidebar.number_input("Pessimista (%)", value=value, step=step, min_value = -100.0, max_value = 100.0, key = f"pessimist_{group_name}",  format="%.1f")
    base = st.sidebar.number_input("Moderado (%)", value=value + step, step = step, min_value = -100.0, max_value = 100.0, key = f"base_{group_name}",  format="%.1f")
    optimist = st.sidebar.number_input("Otimista (%)", value=value + step*2, step= step,  min_value = -100.0, max_value = 100.0,key = f"optimist_{group_name}",  format="%.1f")
    return pessimist, base, optimist

@timer_decorator
def make_dictionary(return_as_df: bool = False, **kwargs):
    d = {}
    for key, value in kwargs.items():
        d[key] = value
    if return_as_df:
        return pd.DataFrame.from_dict(d, orient='index', columns=[''])
    else:
        return d

class Company:

    @timer_decorator
    def __init__(self, ticker: str, benchmark: str = '^BVSP', date: str = None):
        self.ticker = ticker
        self.company = Ticker(self.ticker)
        self.benchmark = benchmark
        self.date = date

    def __reduce__(self):
        return (self.__class__, (self.ticker, self.benchmark, self.date))


    @timer_decorator
    @st.cache_data
    def get_data(self, columns: list = None, frequency: str = 'a'):
        if columns == None:
            columns = [
                'TotalDebt', 'TotalRevenue', 'CostOfRevenue', 
                'GrossProfit', 'SellingGeneralAndAdministration','EBITDA', 
                'DepreciationAndAmortization', 'EBIT',
                'TaxProvision', 'FreeCashFlow', 'CashAndCashEquivalents',
                'WorkingCapital', 'CapitalExpenditure'
            ]
        df = self.company.get_financial_data(columns, frequency = frequency)
        assert df['currencyCode'].unique() == 'BRL', f"Dados em {df['currencyCode'].unique()[0]} e não BRL"
        return df

    @timer_decorator
    @st.cache_data
    def get_current_market_price(self):
        return self.company.history(period = '1d').iloc[0]['close']
    
    @timer_decorator
    @st.cache_data
    def set_date(self, df: pd.DataFrame):
        if self.date == None:
            n = 0
            while '12M' not in df[df.asOfDate == df.asOfDate.sort_values(ascending=False)[n]]['periodType'].values:
                n += 1
            return df.asOfDate.sort_values(ascending=False)[n]
        else:
            return self.date
        
    @timer_decorator
    @st.cache_data
    def set_financials(self, df: pd.DataFrame, date: str):
        df = df[df.asOfDate == date].reset_index(drop = True)
        financials = {}
        for item in [col for col in df.columns if col not in ['periodType', 'currencyCode']]:
            if np.isnan(df[df.periodType == 'TTM'][item].values[0]):
                financials[item] = df[df.periodType == '12M'][item].values[0]
            else:
                financials[item] = df[df.periodType == 'TTM'][item].values[0]
        df = self.company.valuation_measures
        financials['MarketCap'] = df[df.asOfDate == date]['MarketCap'].values[0]
        # financials['TotalShares'] = self.company.key_stats[self.ticker]['sharesOutstanding']
        # Mudar
        financials['PERatio'] = df[df.asOfDate == date]['PeRatio'].values[0]
        financials['PbRatio'] = df[df.asOfDate == date]['PbRatio'].values[0]
        financials['PsRatio'] = df[df.asOfDate == date]['PsRatio'].values[0]
        financials['ForwardPeRatio'] = df[df.asOfDate == date]['ForwardPeRatio'].values[0]
        financials['EnterprisesValueEBITDARatio'] =  df[df.asOfDate == date]['EnterprisesValueEBITDARatio'].values[0]
        financials['EnterprisesValueRevenueRatio'] = df[df.asOfDate == date]['EnterprisesValueRevenueRatio'].values[0]
        financials['TotalShares'] = 100000000
        return financials
    
    @timer_decorator
    @st.cache_data
    def calculate_target_de_ratio(self, debt: float, market_cap: float):
        return debt/market_cap
        
    @timer_decorator
    @st.cache_data
    def calculate_beta(self, start_date, end_date):
        stock_history = self.company.history(start=start_date, end=end_date)
        benchmark = Ticker(self.benchmark)
        benchmark_history = benchmark.history(start=start_date, end=end_date)
        stock_returns = stock_history['close'].pct_change()
        benchmark_returns = benchmark_history['close'].pct_change()
        returns_data = pd.DataFrame(zip(stock_returns, benchmark_returns), columns = ['stock_returns', 'benchmark_returns'])
        returns_data = returns_data.dropna()
        cov = returns_data['stock_returns'].cov(returns_data['benchmark_returns'])
        var = returns_data['benchmark_returns'].var()
        beta = cov / var
        return beta
    
    @timer_decorator
    @st.cache_data
    def calculate_tax_rate(self):
        return 0.34
    
    @timer_decorator
    @st.cache_data
    def calculate_relevered_beta(self, beta: float, tax_rate: float, target_de_ratio: float):
        return beta*(1+(1-tax_rate)*target_de_ratio)

    @timer_decorator
    @st.cache_data
    def calculate_market_risk_premium(self, market_cap: float):
        if market_cap < 2000000000:
            return 0.125
        elif market_cap > 10000000000:
            return 0.075
        else:
            return 0.1

    @timer_decorator
    @st.cache_data
    def calculate_risk_free_rate(self):
        #Mudar
        return 0.073

    @timer_decorator
    @st.cache_data
    def calculate_small_firm_premium(self):
        #Mudar
        return 0.0

    @timer_decorator
    @st.cache_data
    def calculate_cost_of_equity(self, relevered_beta: float, market_risk_premium: float, risk_free_rate: float, small_firm_premium: float):
        return relevered_beta*market_risk_premium + risk_free_rate + small_firm_premium

    @timer_decorator
    @st.cache_data
    def calculate_credit_spread_debt(self):
        #Mudar
        return 0.04

    @timer_decorator
    @st.cache_data
    def calculate_cost_of_debt(self, credit_spread_debt: float, risk_free_rate: float):
        return credit_spread_debt + risk_free_rate

    @timer_decorator
    @st.cache_data
    def calculate_e_de_ratio(self, target_de_ratio: float):
        return 1/(1+target_de_ratio)
    
    @timer_decorator
    @st.cache_data
    def calculate_wacc(self, cost_of_debt: float, tax_rate: float, e_de_ratio: float, cost_of_equity: float):
        return cost_of_debt*(1-tax_rate)*(1-e_de_ratio)+e_de_ratio*cost_of_equity
    
    @timer_decorator
    @st.cache_data
    def calculate_operating_taxes(self, ebit: float, tax_rate: float):
        return ebit*tax_rate
    
    @timer_decorator
    @st.cache_data
    def calculate_nopat(self, ebit: float, operating_taxes: float):
        return ebit - operating_taxes

    @timer_decorator
    @st.cache_data 
    def calculate_operating_capital(self, working_capital: float, capital_expenditure: float):
        return working_capital - capital_expenditure

    @timer_decorator
    @st.cache_data
    def calculate_rocb(self, nopat: float, operating_capital: float):
        return nopat/operating_capital
    
    @timer_decorator
    @st.cache_data
    def calculate_eva(self, operating_capital: float, rocb: float, wacc: float):
        return operating_capital*(rocb-wacc)
    
    @timer_decorator
    @st.cache_data
    def calculate_fcf_margin(self,  date: str, frequency: str = 'a'):
        df = self.company.get_financial_data(['FreeCashFlow', 'TotalRevenue'], frequency = frequency)
        assert df['currencyCode'].unique() == 'BRL', f"Dados em {df['currencyCode'].unique()[0]} e não BRL"
        df = df[df.asOfDate < date]
        df['Ratio'] = df['FreeCashFlow']/df['TotalRevenue']
        return df['Ratio'].mean()
    
    @timer_decorator
    @st.cache_data
    def calculate_discount_rate(self):
        return 1
    
    @timer_decorator
    @st.cache_data
    def calculate_pv_fcf(self, free_cash_flow: float, discount_rate: float):
        return free_cash_flow * discount_rate
    
    @timer_decorator
    @st.cache_data
    def generate_cash_flow(
            self, 
            d: dict, 
            long_term_growth: float, 
            long_term_rocb: float, 
            tax_rate: float, 
            fcf_margin: float,
            wacc: float, 
            fwd: int = 5, 
            return_as_df: bool = True):
        for n in range(1, fwd+1):
            d[n] = {}
            d[n]['Date'] = d[n-1]['Date'] + 1
            d[n]['TotalRevenue'] = d[n-1]['TotalRevenue'] * (1 + long_term_growth)
            d[n]['EBIT'] = d[n-1]['EBIT'] * (1 + long_term_growth)
            d[n]['TaxProvision'] = d[n]['EBIT'] * tax_rate
            d[n]['NOPAT'] = d[n-1]['NOPAT'] * (1 + long_term_growth)
            d[n]['FreeCashFlow'] = d[n]['TotalRevenue'] * fcf_margin
            d[n]['DiscountRate'] = d[n-1]['DiscountRate'] / (1 + wacc)
            d[n]['PV_FCF'] = d[n]['FreeCashFlow'] * d[n]['DiscountRate']
        d[n+1] = {}
        d[n+1]['Date'] = 'TV'
        d[n+1]['TotalRevenue'] = ""
        d[n+1]['EBIT'] = ""
        d[n+1]['TaxProvision'] = ""
        d[n+1]['NOPAT'] = d[n]['NOPAT'] * (1 + long_term_growth)
        d[n+1]['FreeCashFlow'] = d[n+1]['NOPAT'] * (1 - long_term_growth / long_term_rocb) / (wacc - long_term_growth)
        d[n+1]['DiscountRate'] = d[n]['DiscountRate']
        d[n+1]['PV_FCF'] = d[n+1]['FreeCashFlow'] * d[n+1]['DiscountRate']
        if return_as_df:
            df = pd.DataFrame(d)
            df.set_axis(df.iloc[0], axis=1, inplace=True)
            df = df[1:]
            df.columns = [str(int(col)) if col != 'TV' else col for col in df.columns]
            return df
        else:
            return d

    @timer_decorator
    @st.cache_data
    def calculate_enterprise_value(self, df: pd.DataFrame):
        return df.loc['PV_FCF'].sum()

    @timer_decorator
    @st.cache_data
    def calculate_equity(self, enterprise_value: float, cash: float, debt: float):
        return enterprise_value + cash - debt

    @timer_decorator
    @st.cache_data
    def calculate_fair_price(self, equity: float, total_shares: float):
        return equity/total_shares

# class Company:

#     def __init__(
#             self, 
#             ticker: str, 
#             tax_rate: float = 0.34, 
#             market_risk_premium: float = 0.02,
#             risk_free_rate: float = 0.073,
#             small_firm_premium: float = 0.0,
#             credit_spread_debt: float = 0.04,
#             frequency: str = 'a',
#             date: str = None):
#         self.ticker = ticker
#         self.company = Ticker(self.ticker)
#         self.tax_rate = tax_rate
#         self.unlevered_beta = self.company.summary_detail[self.ticker]['beta']
#         self.market_risk_premium = market_risk_premium
#         self.risk_free_rate = risk_free_rate
#         self.small_firm_premium = small_firm_premium
#         self.credit_spread_debt = credit_spread_debt
#         self.frequency = frequency
#         self.date = date

#     def __reduce__(self):
#         return (self.__class__, (self.ticker, self.tax_rate, self.market_risk_premium, self.risk_free_rate, self.small_firm_premium, self.credit_spread_debt, self.frequency, self.date))


#     @cache_hit_log
#     @st.cache
#     def get_target_de_ratio(self):
#         df = self.company.get_financial_data('TotalDebt', frequency = self.frequency)
#         assert df['currencyCode'].unique() == 'BRL', f"Dados em {df['currencyCode'].unique()[0]} e não BRL"
#         date = df.asOfDate.max() if self.date == None else self.date
#         debt = df[df.asOfDate == date]['TotalDebt'].values[0]
#         df = self.company.valuation_measures
#         market_cap = df[df.asOfDate == date]['MarketCap'].values[0]
#         self.target_de_ratio = debt/market_cap

#     @cache_hit_log
#     @st.cache
#     def get_pnl_account(self, financials: list):
#         df = self.company.get_financial_data(financials, frequency = self.frequency)
#         assert df['currencyCode'].unique() == 'BRL', f"Dados em {df['currencyCode'].unique()[0]} e não BRL"
#         date = df.asOfDate.max() if self.date == None else self.date
#         self.pnl_account = {}
#         for item in financials:
#             self.pnl_account[item] = df[(df.asOfDate == date) & (df.periodType == 'TTM')][item].values[0]

#     @cache_hit_log
#     @st.cache
#     def get_wacc(self, return_as_df: bool = True):
#         self.wacc = {}
#         self.wacc['ReleveredBeta'] = self.unlevered_beta*(1+(1-self.tax_rate)*self.target_de_ratio)
#         self.wacc['CostOfEquity'] = self.wacc['ReleveredBeta']*self.market_risk_premium + self.risk_free_rate + self.small_firm_premium
#         self.wacc['CostOfDebt'] = self.credit_spread_debt + self.risk_free_rate
#         self.wacc['EDERatio'] = 1/(1+self.target_de_ratio)
#         self.wacc['WACC'] = self.wacc['CostOfDebt']*(1-self.tax_rate)*(1-self.wacc['EDERatio'])+self.wacc['EDERatio']*self.wacc['CostOfEquity']

#     @cache_hit_log
#     @st.cache
#     def get_rocb(self):
#         self.rocb = {}
#         self.rocb['EBIT'] = self.pnl_account['EBIT']
#         self.rocb['OperatingTaxes'] = self.rocb['EBIT'] * self.tax_rate
#         self.rocb['NOPAT'] = self.rocb['EBIT'] - self.rocb['OperatingTaxes']
#         df = self.company.get_financial_data('WorkingCapital', frequency = self.frequency)
#         assert df['currencyCode'].unique() == 'BRL', f"Dados em {df['currencyCode'].unique()[0]} e não BRL"
#         date = df.asOfDate.max() if self.date == None else self.date
#         self.rocb['WorkingCapital'] = df[(df.asOfDate == date)]['WorkingCapital'].values[0]
#         self.rocb['ROCB'] = self.rocb['NOPAT']/self.rocb['WorkingCapital']
#         self.rocb['WACC'] = self.wacc['WACC']
#         self.rocb['EVA'] = self.rocb['WorkingCapital']*(self.rocb['ROCB'] - self.rocb['WACC'])
#         self.rocb['FCFMargin'] = self.get_fcf_margin()

#     @cache_hit_log
#     @st.cache
#     def get_fcf_margin(self):
#         df = self.company.get_financial_data(['FreeCashFlow', 'TotalRevenue'], frequency = self.frequency)
#         assert df['currencyCode'].unique() == 'BRL', f"Dados em {df['currencyCode'].unique()[0]} e não BRL"
#         date = df.asOfDate.max() if self.date == None else self.date
#         df = df[df.asOfDate < date]
#         df['Ratio'] = df['FreeCashFlow']/df['TotalRevenue']
#         return df['Ratio'].mean()

#     @cache_hit_log
#     @st.cache
#     def get_free_cash_flow(self, financials: list):
#         df = self.company.get_financial_data(financials, frequency = self.frequency)
#         assert df['currencyCode'].unique() == 'BRL', f"Dados em {df['currencyCode'].unique()[0]} e não BRL"
#         date = df.asOfDate.max() if self.date == None else self.date
#         df = df[(df.asOfDate == date) & (df.periodType == '12M')]
#         df['NOPAT'] = df['EBIT'] - df['TaxProvision']
#         df['DiscountRate'] = 1
#         df['PV_FCF'] = df['FreeCashFlow'] * df['DiscountRate']
#         df = df[['asOfDate', 'TotalRevenue', 'EBIT', 'TaxProvision', 'NOPAT', 'FreeCashFlow', 'DiscountRate', 'PV_FCF']].reset_index(drop = True)
#         df['asOfDate'] = df['asOfDate'].apply(lambda x: x.year)
#         self.free_cash_flow = df.to_dict(orient = 'index')

#     @cache_hit_log
#     @st.cache
#     def generate_cash_flow(self, long_term_growth: float, long_term_rocb: float, fwd: int = 5, return_as_df: bool = True):
#         for n in range(1, fwd+1):
#             self.free_cash_flow[n] = {}
#             self.free_cash_flow[n]['asOfDate'] = self.free_cash_flow[n-1]['asOfDate'] + 1
#             self.free_cash_flow[n]['TotalRevenue'] = self.free_cash_flow[n-1]['TotalRevenue']*(1+long_term_growth)
#             self.free_cash_flow[n]['EBIT'] = self.free_cash_flow[n-1]['EBIT']*(1+long_term_growth)
#             self.free_cash_flow[n]['TaxProvision'] = self.free_cash_flow[n]['EBIT'] * self.tax_rate
#             self.free_cash_flow[n]['NOPAT'] = self.free_cash_flow[n-1]['NOPAT']*(1+long_term_growth)
#             self.free_cash_flow[n]['FreeCashFlow'] = self.free_cash_flow[n]['TotalRevenue'] * self.rocb['FCFMargin']
#             self.free_cash_flow[n]['DiscountRate'] = self.free_cash_flow[n-1]['DiscountRate']/(1+self.wacc['WACC'])
#             self.free_cash_flow[n]['PV_FCF'] = self.free_cash_flow[n]['FreeCashFlow'] * self.free_cash_flow[n]['DiscountRate']
#         self.free_cash_flow[n+1] = {}
#         self.free_cash_flow[n+1]['asOfDate'] = 'TV'
#         self.free_cash_flow[n+1]['TotalRevenue'] = ""
#         self.free_cash_flow[n+1]['EBIT'] = ""
#         self.free_cash_flow[n+1]['TaxProvision'] = ""
#         self.free_cash_flow[n+1]['NOPAT'] = self.free_cash_flow[n]['NOPAT']*(1+long_term_growth)
#         self.free_cash_flow[n+1]['FreeCashFlow'] = self.free_cash_flow[n+1]['NOPAT']*(1-long_term_growth/long_term_rocb)/(self.wacc['WACC'] - long_term_growth)
#         self.free_cash_flow[n+1]['DiscountRate'] = self.free_cash_flow[n]['DiscountRate']
#         self.free_cash_flow[n+1]['PV_FCF'] = self.free_cash_flow[n+1]['FreeCashFlow'] * self.free_cash_flow[n+1]['DiscountRate']
#         if return_as_df:
#             df = pd.DataFrame(self.free_cash_flow)
#             df.set_axis(df.iloc[0], axis=1, inplace=True)
#             df = df[1:]
#             df.columns = [str(int(col)) if col != 'TV' else col for col in df.columns]
#             return df
            
#     @cache_hit_log
#     @st.cache
#     def get_enterprise_value(self, financials: list):
#         df = self.company.get_financial_data(financials, frequency = self.frequency)
#         assert df['currencyCode'].unique() == 'BRL', f"Dados em {df['currencyCode'].unique()[0]} e não BRL"
#         date = df.asOfDate.max() if self.date == None else self.date
#         df = df[df.asOfDate == date]
#         self.valuation = {}
#         self.valuation['EnterpriseValue'] = 0
#         for d in self.free_cash_flow:
#             self.valuation['EnterpriseValue'] += self.free_cash_flow[d]['PV_FCF']
#         self.valuation['Cash'] = df['CashAndCashEquivalents'].values[0]
#         self.valuation['Debt'] = df['TotalDebt'].values[0]
#         self.valuation['Equity'] = self.valuation['EnterpriseValue'] + self.valuation['Cash'] - self.valuation['Debt']
#         self.valuation['TotalShares'] = self.company.key_stats[self.ticker]['sharesOutstanding']
#         self.valuation['FairPrice'] = self.valuation['Equity']/self.valuation['TotalShares']