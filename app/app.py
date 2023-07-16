import streamlit as st
import pandas as pd
import numpy as np
import logging
import time
from logger import logger
from utils import create_input_group, make_dictionary, Company

logger.setLevel(logging.INFO)

def app():

    start = time.time()

    st.set_page_config(layout= "wide", page_icon = 'assets/logo.png')

    pd.set_option('display.float_format', '{:.4f}'.format)

    # Sidebar
    lt_growth = create_input_group("Crescimento de longo prazo")
    roic = create_input_group("ROIC", step = 5.0, value = 5.0)
    fcf_margin = create_input_group("Margem FCF", step = 5.0, value = 5.0)

    c1, c2 = st.columns((1, 1))

    with c1:
        st.image('assets/logo.png', use_column_width=False, width=300)

    # ACHAR LISTA DE TODAS AS AÇÕES
    with c2:
        stock_list = ['B3SA3.SA', 'PETR4.SA', 'ITUB3.SA', 'ITUB4.SA', 'ELET3.SA', 'ARZZ3.SA']
        st.write('')
        st.write('')
        stock = st.selectbox('Selecione a ação', options = stock_list)
    
    # MELHOR JEITO DE CHUMBAR ISSO

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
    tax_rate = comp.calculate_tax_rate()
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
    operating_taxes = comp.calculate_operating_taxes(ebit = financials['EBIT'], tax_rate = tax_rate)
    nopat = comp.calculate_nopat(ebit = financials['EBIT'], operating_taxes=operating_taxes)
    operating_capital = comp.calculate_operating_capital(working_capital = financials['WorkingCapital'], capital_expenditure=financials['CapitalExpenditure'])
    rocb = comp.calculate_rocb(nopat = nopat, operating_capital=operating_capital)
    eva = comp.calculate_eva(operating_capital=operating_capital, rocb = rocb, wacc = wacc)
    fcf_margin_historical = comp.calculate_fcf_margin(date = date)
    metricas_df = make_dictionary(
        WACC = wacc,
        ROIC = rocb,
        FCFMargin = fcf_margin_historical,
        return_as_df=True
    )

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

    # Pessimista
    free_cash_flow_pessimista = comp.generate_cash_flow(
        d = free_cash_flow, 
        long_term_growth=lt_growth[0]/100, 
        long_term_rocb=roic[0]/100,
        fcf_margin=fcf_margin[0]/100, 
        tax_rate = tax_rate, 
        wacc = wacc)
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

    #Moderado
    free_cash_flow_moderado = comp.generate_cash_flow(
        d = free_cash_flow, 
        long_term_growth=lt_growth[1]/100, 
        long_term_rocb=roic[1]/100,
        fcf_margin=fcf_margin[1]/100, 
        tax_rate = tax_rate,
        wacc = wacc)
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

    # Otimista
    free_cash_flow_otimista = comp.generate_cash_flow(
        d = free_cash_flow, 
        long_term_growth=lt_growth[2]/100, 
        long_term_rocb=roic[2]/100,
        fcf_margin=fcf_margin[2]/100, 
        tax_rate = tax_rate,
        wacc = wacc)
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
    st.write(f'Data-base:{date}')
    
    c1, c2, c3 = st.columns([1, 1, 2])

    valuation_price = '${:.2f}'.format(np.mean([fair_price_pessimista, fair_price_moderado, fair_price_moderado]))
    current_price = '${:.2f}'.format(comp.get_current_market_price())
    
    with c1:
        st.write("# Resultado 12M")
        st.dataframe(pnl_account)

    with c2:
        st.write("# Métricas")
        st.dataframe(metricas_df)

    with c3:
        # st.write(f"#    {stock}")
        # st.write(f'<div style="text-align: center; font-size: 24px; font-weight: bold;">{stock}</div>', unsafe_allow_html=True)
        st.markdown(f"<h1 style='text-align: center;'>{stock}</h1>", unsafe_allow_html=True)
        # st.title(stock)
        c4, c5 = st.columns((1, 1))
        with c4:
            # st.write("## Preço Atual")
            # st.subheader('Preço Atual')
            # st.write(f"### {current_price}")
            st.markdown("<h2 style='text-align: center;'>Preço Atual</h2>", unsafe_allow_html=True)
            st.write("---")  # Adds a horizontal line for separation
            st.markdown(f"<h3 style='text-align: center;'>{current_price}</h3>", unsafe_allow_html=True)
        with c5:
            # st.write("## Meu Valuation")
            # st.subheader('Meu Valuation')
            # st.write(f"### {valuation_price}")
            st.markdown("<h2 style='text-align: center;'>Meu Valuation</h2>", unsafe_allow_html=True)
            st.write("---")  # Adds a horizontal line for separation
            st.markdown(f"<h3 style='text-align: center;'>{valuation_price}</h3>", unsafe_allow_html=True)

    st.write('# Cenário Pessimista')

    c4, c5 = st.columns([3, 1])

    with c4:
        st.dataframe(free_cash_flow_pessimista, use_container_width = True)
    with c5:
        st.dataframe(enterprise_df_pessimista)

    st.write('# Cenário Moderado')

    c4, c5 = st.columns([3, 1])

    with c4:
        st.dataframe(free_cash_flow_moderado, use_container_width = True)
    with c5:
        st.dataframe(enterprise_df_moderado)

    st.write('# Cenário Otimista')

    c4, c5 = st.columns([3, 1])

    with c4:
        st.dataframe(free_cash_flow_otimista, use_container_width = True)
    with c5:
        st.dataframe(enterprise_df_otimista)

    execution_time = time.time() - start
    logger.info(f"Page executed in {execution_time} seconds.\n")

def app2():

    start = time.time()

    st.set_page_config(layout= "wide", page_icon = 'assets/logo.png')

    pd.set_option('display.float_format', '{:.4f}'.format)

    # Sidebar
    lt_growth = create_input_group("Crescimento de longo prazo")
    roic = create_input_group("ROIC", step = 5.0, value = 5.0)
    fcf_margin = create_input_group("Margem FCF", step = 5.0, value = 5.0)

    c1, c2 = st.columns((1, 1))

    with c1:
        st.image('assets/logo.png', use_column_width=False, width=300)

    # ACHAR LISTA DE TODAS AS AÇÕES
    with c2:
        stock_list = ['B3SA3.SA', 'PETR4.SA', 'ITUB3.SA', 'ITUB4.SA', 'ELET3.SA', 'ARZZ3.SA']
        st.write('')
        st.write('')
        stock = st.selectbox('Selecione a ação', options = stock_list)
    
    # MELHOR JEITO DE CHUMBAR ISSO

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
    tax_rate = comp.calculate_tax_rate()
    relevered_beta = comp.calculate_relevered_beta(beta = beta, tax_rate = tax_rate, target_de_ratio=target_de_ratio)
    market_risk_premium = comp.calculate_market_risk_premium(financials['MarketCap'])
    risk_free_rate = comp.calculate_risk_free_rate()
    small_firm_premium = comp.calculate_small_firm_premium()
    cost_of_equity = comp.calculate_cost_of_equity(
        relevered_beta=relevered_beta, market_risk_premium=market_risk_premium, risk_free_rate=risk_free_rate, small_firm_premium=small_firm_premium
    )
    credit_spread_debt = comp.calculate_credit_spread_debt()
    cost_of_debt = comp.calculate_cost_of_debt(credit_spread_debt=credit_spread_debt, risk_free_rate=risk_free_rate)
    e_de_ratio = comp.calculate_e_de_ratio(target_de_ratio=target_de_ratio)
    wacc = comp.calculate_wacc(cost_of_debt=cost_of_debt, tax_rate=tax_rate, e_de_ratio=e_de_ratio, cost_of_equity=cost_of_equity)
    operating_taxes = comp.calculate_operating_taxes(ebit = financials['EBIT'], tax_rate = tax_rate)
    nopat = comp.calculate_nopat(ebit = financials['EBIT'], operating_taxes=operating_taxes)
    operating_capital = comp.calculate_operating_capital(working_capital = financials['WorkingCapital'], capital_expenditure=financials['CapitalExpenditure'])
    rocb = comp.calculate_rocb(nopat = nopat, operating_capital=operating_capital)
    eva = comp.calculate_eva(operating_capital=operating_capital, rocb = rocb, wacc = wacc)
    fcf_margin_historical = comp.calculate_fcf_margin(date = date)
    metricas_df = make_dictionary(
        WACC = wacc,
        ROIC = rocb,
        FCFMargin = fcf_margin_historical,
        return_as_df=True
    )

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

    # Pessimista
    free_cash_flow_pessimista = comp.generate_cash_flow(
        d = free_cash_flow, 
        long_term_growth=lt_growth[0]/100, 
        long_term_rocb=roic[0]/100,
        fcf_margin=fcf_margin[0]/100, 
        tax_rate = tax_rate, 
        wacc = wacc)
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

    #Moderado
    free_cash_flow_moderado = comp.generate_cash_flow(
        d = free_cash_flow, 
        long_term_growth=lt_growth[1]/100, 
        long_term_rocb=roic[1]/100,
        fcf_margin=fcf_margin[1]/100, 
        tax_rate = tax_rate,
        wacc = wacc)
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

    # Otimista
    free_cash_flow_otimista = comp.generate_cash_flow(
        d = free_cash_flow, 
        long_term_growth=lt_growth[2]/100, 
        long_term_rocb=roic[2]/100,
        fcf_margin=fcf_margin[2]/100, 
        tax_rate = tax_rate,
        wacc = wacc)
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
    st.write(f'Data-base:{date}')
    

    valuation_price = '${:.2f}'.format(np.mean([fair_price_pessimista, fair_price_moderado, fair_price_moderado]))
    current_price = '${:.2f}'.format(comp.get_current_market_price())
    
    st.markdown(f"<h1 style='text-align: center;'>Indicadores</h1>", unsafe_allow_html=True)

    c4, c5, c6, c7, c8 = st.columns(5)

    style = """
    <style>
    .blue-text {
        color: blue;
        text-align: center;
        font-size: 24px; /* Use the same font size as the h1 header for P/L */
    }
    </style>
    """
    st.markdown(style, unsafe_allow_html=True)

    with c4:
        st.markdown(f"<h1 style='text-align: center;'>P/L</h1>", unsafe_allow_html=True)
        st.markdown(f"<p class='blue-text'>{'{:.0f}'.format(financials['PERatio'])}</p>", unsafe_allow_html=True)  # Adds a horizontal line for separation
        st.markdown(f"<h1 style='text-align: center;'>P/VP</h1>", unsafe_allow_html=True)
        st.markdown(f"<p class='blue-text'>{'{:.0f}'.format(financials['PbRatio'])}</p>", unsafe_allow_html=True) 

    with c5:
        st.markdown(f"<h1 style='text-align: center;'>P/L Projetado</h1>", unsafe_allow_html=True)
        st.markdown(f"<p class='blue-text'>{'{:.0f}'.format(financials['ForwardPeRatio'])}</p>", unsafe_allow_html=True)
        st.markdown(f"<h1 style='text-align: center;'>P/Vendas</h1>", unsafe_allow_html=True)
        st.markdown(f"<p class='blue-text'>{'{:.0f}'.format(financials['PsRatio'])}</p>", unsafe_allow_html=True)

    with c6:
        st.markdown(f"<h1 style='text-align: center;'>E/V Ebitda</h1>", unsafe_allow_html=True)
        st.markdown(f"<p class='blue-text'>{'{:.0f}'.format(financials['EnterprisesValueEBITDARatio'])}</p>", unsafe_allow_html=True)
        st.markdown(f"<h1 style='text-align: center;'>ROIC</h1>", unsafe_allow_html=True)
        st.markdown(f"<p class='blue-text'>{'{:.0f}'.format(rocb)}</p>", unsafe_allow_html=True)

    with c7:
        st.markdown(f"<h1 style='text-align: center;'>E/V Receita</h1>", unsafe_allow_html=True)
        st.markdown(f"<p class='blue-text'>{'{:.0f}'.format(financials['EnterprisesValueRevenueRatio'])}</p>", unsafe_allow_html=True)
        st.markdown(f"<h1 style='text-align: center;'>Margem FCF</h1>", unsafe_allow_html=True)
        st.markdown(f"<p class='blue-text'>{'{:.0%}'.format(fcf_margin_historical)}</p>", unsafe_allow_html=True)

    with c8:
        st.markdown(f"<h1 style='text-align: center;'>Capitalização</h1>", unsafe_allow_html=True)
        st.markdown(f"<p class='blue-text'>{'{:.0f}'.format(financials['MarketCap']/1000000000) + str(' bi')}</p>", unsafe_allow_html=True)
        st.markdown(f"<h1 style='text-align: center;'>Dívida P/L</h1>", unsafe_allow_html=True)
        st.markdown(f"<p class='blue-text'>{'{:.2%}'.format(target_de_ratio)}</p>", unsafe_allow_html=True)  

    c9, c10, c11, c12 = st.columns(4)

    with c9:
        st.write('---')
        st.markdown(f"<h1 style='text-align: left;'>Crescimento</h1>", unsafe_allow_html=True)
        st.markdown(f"<h1 style='text-align: left;'>ROIC</h1>", unsafe_allow_html=True)
        st.markdown(f"<h1 style='text-align: left;'>Margem FCF</h1>", unsafe_allow_html=True)
        st.markdown(f"<h1 style='text-align: left;'>Preço Alvo</h1>", unsafe_allow_html=True)
        st.markdown(f"<h1 style='text-align: left;'>Preço Atual</h1>", unsafe_allow_html=True)
        st.markdown(f"<h1 style='text-align: left;'>Potencial</h1>", unsafe_allow_html=True)
        # c13, c14 = st.columns(2)
        # with c13:
        #     st.write('Preço Atual')
        # with c14:
        #     st.write(current_price)
        # c15, c16 = st.columns(2)
        # with c15:
        #     st.write('Alvo Médio')
        # with c16:
        #     st.write('X')

    style = """
    <style>
    .green-text {
        color: green;
        text-align: center;
        font-size: 24px; /* Use the same font size as the h1 header for P/L */
    }
    </style>
    """
    st.markdown(style, unsafe_allow_html=True)

    with c10:
        st.markdown(f"<h1 style='text-align: center;'>Pessimista</h1>", unsafe_allow_html=True)
        st.markdown(f"<p class='blue-text'>{'{:.0%}'.format(lt_growth[0]/100)}</p>", unsafe_allow_html=True)
        st.markdown(f"<p class='blue-text'>{'{:.0%}'.format(roic[0]/100)}</p>", unsafe_allow_html=True)
        st.markdown(f"<p class='blue-text'>{'{:.0%}'.format(fcf_margin[0]/100)}</p>", unsafe_allow_html=True)
        st.markdown(f"<p class='green-text'>{'${:.2f}'.format(fair_price_pessimista)}</p>", unsafe_allow_html=True)
        st.markdown(f"<p class='green-text'>{current_price}</p>", unsafe_allow_html=True)
        st.markdown(f"<p class='green-text'>{'{:.0%}'.format(fair_price_pessimista/comp.get_current_market_price() - 1)}</p>", unsafe_allow_html=True)
        st.write("---")

    with c11:
        st.markdown(f"<h1 style='text-align: center;'>Moderado</h1>", unsafe_allow_html=True)
        st.markdown(f"<p class='blue-text'>{'{:.0%}'.format(lt_growth[1]/100)}</p>", unsafe_allow_html=True)
        st.markdown(f"<p class='blue-text'>{'{:.0%}'.format(roic[1]/100)}</p>", unsafe_allow_html=True)
        st.markdown(f"<p class='blue-text'>{'{:.0%}'.format(fcf_margin[1]/100)}</p>", unsafe_allow_html=True)
        st.markdown(f"<p class='green-text'>{'${:.2f}'.format(fair_price_moderado)}</p>", unsafe_allow_html=True)
        st.markdown(f"<p class='green-text'>{current_price}</p>", unsafe_allow_html=True)
        st.markdown(f"<p class='green-text'>{'{:.0%}'.format(fair_price_moderado/comp.get_current_market_price() - 1)}</p>", unsafe_allow_html=True)
        st.write("---")

    with c12:
        st.markdown(f"<h1 style='text-align: center;'>Otimista</h1>", unsafe_allow_html=True)
        st.markdown(f"<p class='blue-text'>{'{:.0%}'.format(lt_growth[2]/100)}</p>", unsafe_allow_html=True)
        st.markdown(f"<p class='blue-text'>{'{:.0%}'.format(roic[2]/100)}</p>", unsafe_allow_html=True)
        st.markdown(f"<p class='blue-text'>{'{:.0%}'.format(fcf_margin[2]/100)}</p>", unsafe_allow_html=True)
        st.markdown(f"<p class='green-text'>{'${:.2f}'.format(fair_price_otimista)}</p>", unsafe_allow_html=True)
        st.markdown(f"<p class='green-text'>{current_price}</p>", unsafe_allow_html=True)
        st.markdown(f"<p class='green-text'>{'{:.0%}'.format(fair_price_otimista/comp.get_current_market_price() - 1)}</p>", unsafe_allow_html=True)
        st.write("---")

    execution_time = time.time() - start
    logger.info(f"Page executed in {execution_time} seconds.\n")

if __name__ == '__main__':
    app2()