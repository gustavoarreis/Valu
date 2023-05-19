import streamlit as st
import pandas as pd
from yahooquery import Ticker

def create_input_group(group_name):
    st.sidebar.subheader(group_name)
    pessimist = st.sidebar.number_input("Pessimista (%)", value=0.0, step=1.0, min_value = -100.0, max_value = 100.0, key = f"pessimist_{group_name}",  format="%.1f")
    base = st.sidebar.number_input("Moderado (%)", value=0.0, step = 1.0, min_value = -100.0, max_value = 100.0, key = f"base_{group_name}",  format="%.1f")
    optimist = st.sidebar.number_input("Otimista (%)", value=0.0, step= 1.0,  min_value = -100.0, max_value = 100.0,key = f"optimist_{group_name}",  format="%.1f")
    return pessimist, base, optimist



class Company:

    def __init__(
            self, 
            ticker: str, 
            tax_rate: float = 0.34, 
            unlevered_beta: float = 0.72,
            target_de_ratio: float = 0.3,
            market_risk_premium: float = 0.02,
            risk_free_rate: float = 0.073,
            small_firm_premium: float = 0.0,
            credit_spread_debt: float = 0.04):
        self.company = Ticker(ticker)
        self.tax_rate = tax_rate
        self.unlevered_beta = unlevered_beta
        self.market_risk_premium = market_risk_premium
        self.risk_free_rate = risk_free_rate
        self.small_firm_premium = small_firm_premium
        self.credit_spread_debt = credit_spread_debt
        self.target_de_ratio = target_de_ratio


    def pnl_account(self, pnl_account: list, freq: str = 'a', date: str = None):
        df = self.company.get_financial_data(pnl_account, frequency = freq)
        assert df['currencyCode'].unique() == 'BRL', f"Dados em {df['currencyCode'].unique()[0]} e não BRL"
        if date == None:
            date = df.asOfDate.max()
        df = df[(df.asOfDate == date) & (df.periodType == 'TTM')].pivot_table(
            columns = 'asOfDate', values = pnl_account
        ).reindex(pnl_account)
        return df
    
    def get_wacc(self, return_as_df: bool = True):
        self.relevered_beta = self.unlevered_beta*(1+(1-self.tax_rate)*self.target_de_ratio)
        self.cost_of_equity = self.relevered_beta*self.market_risk_premium + self.risk_free_rate + self.small_firm_premium
        self.cost_of_debt = self.credit_spread_debt + self.risk_free_rate
        self.e_de_ratio = 1/(1+self.target_de_ratio)
        self.wacc = self.cost_of_debt*(1-self.tax_rate)*(1-self.e_de_ratio)+self.e_de_ratio*self.cost_of_equity
        if return_as_df:
            df =  pd.DataFrame([self.unlevered_beta, self.relevered_beta, self.cost_of_equity, self.cost_of_debt, self.e_de_ratio, self.wacc],
                               index = ['Unlevered Beta', 'Relevered Beta', 'Cost Of Equity', 'Cost Of Debt', 'E/D+E Ratio', 'WACC'])
            return df