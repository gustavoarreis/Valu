import streamlit as st
from utils import create_input_group, Company

def app():

    # Sidebar
    lt_growth = create_input_group("Crescimento de longo prazo")
    debt_percentage = create_input_group("Percentual de dívida")
    roic = create_input_group("ROIC")
    fcf_margin = create_input_group("Margem FCF")

    # ACHAR LISTA DE TODAS AS AÇÕES
    stock_list = ['B3SA3.SA', 'PETR4.SA', 'ITUB4.SA', 'ELET3.SA', 'ARZZ3.SA']
    stock = st.selectbox('Selecione a ação', options = stock_list)
    
    # MELHOR JEITO DE CHUMBAR ISSO
    pnl_account = ['TotalRevenue', 'CostOfRevenue', 'GrossProfit', 'SellingGeneralAndAdministration','EBITDA', 'DepreciationAndAmortization', 'EBIT']

    # Trazer informações
    comp = Company(stock)
    st.dataframe(comp.pnl_account(pnl_account = pnl_account, date = '2022-12-31'))
    st.dataframe(comp.get_wacc())

if __name__ == '__main__':
    app()