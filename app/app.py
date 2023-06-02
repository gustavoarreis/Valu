import streamlit as st
import pandas as pd
import logging
import time
from logger import logger
from utils import create_input_group, make_dictionary, Company

logger.setLevel(logging.INFO)

def app():

    start = time.time()

    st.set_page_config(layout= "wide")

    pd.set_option('display.float_format', '{:.4f}'.format)

    # Sidebar
    lt_growth = create_input_group("Crescimento de longo prazo")
    debt_percentage = create_input_group("Percentual de dívida")
    roic = create_input_group("ROIC", step = 5.0, value = 5.0)
    fcf_margin2 = create_input_group("Margem FCF")

    # ACHAR LISTA DE TODAS AS AÇÕES
    stock_list = ['B3SA3.SA', 'PETR4.SA', 'ITUB3.SA', 'ITUB4.SA', 'ELET3.SA', 'ARZZ3.SA']
    stock = st.selectbox('Selecione a ação', options = stock_list)
    
    # MELHOR JEITO DE CHUMBAR ISSO

    c1, c2, c3 = st.columns((1, 1, 1))

    tax_rate = 0.34
    comp = Company(stock)
    data = comp.get_data()
    date = comp.set_date(data)
    financials = comp.set_financials(df = data, date = date)
    pnl_account = make_dictionary(
            TotalRevenue = financials['TotalRevenue'],
            CostOfRevenue = financials['CostOfRevenue'],
            GrossProfit = financials['GrossProfit'],
            SellingGeneralAndAdministration = financials['SellingGeneralAndAdministration'],
            EBITDA = financials['EBITDA'],
            DepreciationAndAmortization = financials['DepreciationAndAmortization'],
            EBIT = financials['EBIT'],
            return_as_df= True
    )
    beta = comp.calculate_beta(start_date = '2019-12-31', end_date = '2023-12-31')
    target_de_ratio = comp.calculate_target_de_ratio(debt = financials['TotalDebt'], market_cap = financials['MarketCap'])
    relevered_beta = comp.calculate_relevered_beta(beta = beta, tax_rate = tax_rate, target_de_ratio=target_de_ratio)
    market_risk_premium = comp.calculate_market_risk_premium()
    risk_free_rate = comp.calculate_risk_free_rate()
    small_firm_premium = comp.calculate_small_firm_premium()
    cost_of_equity = comp.calculate_cost_of_equity(
        relevered_beta=relevered_beta, market_risk_premium=market_risk_premium, risk_free_rate=risk_free_rate, small_firm_premium=small_firm_premium
    )
    credit_spread_debt = comp.calculate_credit_spread_debt()
    cost_of_debt = comp.calculate_cost_of_debt(credit_spread_debt=credit_spread_debt, risk_free_rate=risk_free_rate)
    e_de_ratio = comp.calculate_e_de_ratio(target_de_ratio=target_de_ratio)
    wacc = comp.calculate_wacc(cost_of_debt=cost_of_debt, tax_rate=tax_rate, e_de_ratio=e_de_ratio, cost_of_equity=cost_of_equity)
    wacc_df = make_dictionary(
        ReleveredBeta = relevered_beta,
        CostOfEquity = cost_of_equity,
        CostOfDebt = cost_of_debt,
        EDERatio = e_de_ratio,
        WACC = wacc,
        return_as_df=True
    )
    operating_taxes = comp.calculate_operating_taxes(ebit = financials['EBIT'], tax_rate = tax_rate)
    nopat = comp.calculate_nopat(ebit = financials['EBIT'], operating_taxes=operating_taxes)
    operating_capital = comp.calculate_operating_capital(working_capital = financials['WorkingCapital'], capital_expenditure=financials['CapitalExpenditure'])
    rocb = comp.calculate_rocb(nopat = nopat, operating_capital=operating_capital)
    eva = comp.calculate_eva(operating_capital=operating_capital, rocb = rocb, wacc = wacc)
    fcf_margin = comp.calculate_fcf_margin(date = date)
    rocb_df = make_dictionary(
        EBIT = financials['EBIT'],
        OperatingTaxes = operating_taxes, 
        NOPAT = nopat,
        OperatingCapital = operating_capital,
        ROCB = rocb,
        WACC = wacc, 
        EVA = eva,
        FCFMargin = fcf_margin,
        return_as_df = True
    )

    # Trazer informações
    with c1:
        st.write("## Profit and Loss Account")
        # for key, value in comp.pnl_account.items():
        #     st.write(f"{key}: {value}")
        # df = pd.DataFrame.from_dict(comp.pnl_account, orient='index', columns=[''])
        st.dataframe(pnl_account)
        # st.write(*comp.pnl_account.items())

    with c2:
        st.write("## WACC")
        # comp.get_wacc()
        # for key, value in comp.wacc.items():
        #     st.write(f"{key}: {value}")
        st.dataframe(wacc_df)
        # st.write(*comp.wacc.items())
    
    with c3:
        st.write("## ROCB")
        # comp.get_rocb()
        # for key, value in comp.wacc.items():
        #     st.write(f"{key}: {value}")
        # df = pd.DataFrame.from_dict(comp.rocb, orient='index', columns=[''])
        st.dataframe(rocb_df)
        # st.write(*comp.wacc.items())

    # Início do FCF

    discount_rate = comp.calculate_discount_rate()
    pv_fcf = comp.calculate_pv_fcf(free_cash_flow = financials['FreeCashFlow'], discount_rate=discount_rate)
    free_cash_flow = {}
    free_cash_flow[0] = make_dictionary(
        Date = date.year,
        TotalRevenue = financials['TotalRevenue'],
        EBIT = financials['EBIT'],
        TaxProvision = operating_taxes,
        NOPAT = nopat,
        FreeCashFlow = financials['FreeCashFlow'],
        DiscountRate = discount_rate,
        PV_FCF = pv_fcf
    )

    st.write('# Cenário Pessimista')

    c4, c5 = st.columns([3, 1])

    with c4:
        # df = comp.generate_cash_flow()
        free_cash_flow_pessimista = comp.generate_cash_flow(d = free_cash_flow, long_term_growth=lt_growth[0]/100, long_term_rocb=roic[0]/100,
            tax_rate = tax_rate, fcf_margin=fcf_margin2[0]/100, wacc = wacc)
        st.dataframe(free_cash_flow_pessimista, use_container_width = True)
    with c5:
        # comp.get_enterprise_value(financials = value)
        # df = pd.DataFrame.from_dict(comp.valuation, orient = 'index', columns = [''])
        enterprise_value_pessimista = comp.calculate_enterprise_value(free_cash_flow_pessimista)
        equity_pessimista = comp.calculate_equity(enterprise_value = enterprise_value_pessimista, cash = financials['CashAndCashEquivalents'], debt = financials['TotalDebt'])
        fair_price_pessimista = comp.calculate_fair_price(equity=equity_pessimista, total_shares = financials['TotalShares'])
        enterprise_df_pessimista = make_dictionary(
            EnterpriseValue = enterprise_value_pessimista,
            Cash = financials['CashAndCashEquivalents'],
            Debt = financials['TotalDebt'],
            Equity = equity_pessimista,
            TotalShares = financials['TotalShares'],
            FairPrice = fair_price_pessimista,
            return_as_df= True
        )
        st.dataframe(enterprise_df_pessimista)

    st.write('# Cenário Moderado')

    c4, c5 = st.columns([3, 1])

    with c4:
        # df = comp.generate_cash_flow()
        free_cash_flow_moderado = comp.generate_cash_flow(d = free_cash_flow, long_term_growth=lt_growth[1]/100, long_term_rocb=roic[1]/100,
            tax_rate = tax_rate, fcf_margin=fcf_margin2[1]/100, wacc = wacc)
        st.dataframe(free_cash_flow_moderado, use_container_width = True)
    with c5:
        # comp.get_enterprise_value(financials = value)
        # df = pd.DataFrame.from_dict(comp.valuation, orient = 'index', columns = [''])
        enterprise_value_moderado = comp.calculate_enterprise_value(free_cash_flow_moderado)
        equity_moderado = comp.calculate_equity(enterprise_value = enterprise_value_moderado, cash = financials['CashAndCashEquivalents'], debt = financials['TotalDebt'])
        fair_price_moderado = comp.calculate_fair_price(equity=equity_moderado, total_shares = financials['TotalShares'])
        enterprise_df_moderado = make_dictionary(
            EnterpriseValue = enterprise_value_moderado,
            Cash = financials['CashAndCashEquivalents'],
            Debt = financials['TotalDebt'],
            Equity = equity_moderado,
            TotalShares = financials['TotalShares'],
            FairPrice = fair_price_moderado,
            return_as_df= True
        )
        st.dataframe(enterprise_df_moderado)

    st.write('# Cenário Otimista')

    c4, c5 = st.columns([3, 1])

    with c4:
        # df = comp.generate_cash_flow()
        free_cash_flow_otimista = comp.generate_cash_flow(d = free_cash_flow, long_term_growth=lt_growth[2]/100, long_term_rocb=roic[2]/100,
            tax_rate = tax_rate, fcf_margin=fcf_margin2[2]/100, wacc = wacc)
        st.dataframe(free_cash_flow_otimista, use_container_width = True)
    with c5:
        # comp.get_enterprise_value(financials = value)
        # df = pd.DataFrame.from_dict(comp.valuation, orient = 'index', columns = [''])
        enterprise_value_otimista = comp.calculate_enterprise_value(free_cash_flow_otimista)
        equity_otimista = comp.calculate_equity(enterprise_value = enterprise_value_otimista, cash = financials['CashAndCashEquivalents'], debt = financials['TotalDebt'])
        fair_price_otimista = comp.calculate_fair_price(equity=equity_otimista, total_shares = financials['TotalShares'])
        enterprise_df_otimista = make_dictionary(
            EnterpriseValue = enterprise_value_otimista,
            Cash = financials['CashAndCashEquivalents'],
            Debt = financials['TotalDebt'],
            Equity = equity_otimista,
            TotalShares = financials['TotalShares'],
            FairPrice = fair_price_otimista,
            return_as_df= True
        )
        st.dataframe(enterprise_df_otimista)

    execution_time = time.time() - start
    logger.info(f"Page executed in {execution_time} seconds.\n")

if __name__ == '__main__':
    app()