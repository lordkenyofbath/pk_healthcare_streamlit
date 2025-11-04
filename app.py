import streamlit as st
import numpy as np
import numpy_financial as npf
import pandas as pd

st.set_page_config(page_title="Pakistan Healthcare Feasibility (Pilot)", page_icon="🩺", layout="wide")

# ---------- Helpers
PKR = "PKR"

def pkr(x):
    try:
        return f"{PKR} {x:,.0f}"
    except Exception:
        return x

def simple_payback(capex, annual_fcfe):
    if annual_fcfe <= 0:
        return np.nan
    return capex / annual_fcfe

# ---------- Sidebar: Global assumptions
with st.sidebar:
    st.header("Global Assumptions")
    fx_depreciation = st.slider("PKR depreciation vs imports (annual)", 0.0, 0.30, 0.10, 0.01,
                                help="Proxy for cost inflation on imported equipment/consumables")
    discount_rate = st.slider("Discount rate (real)", 0.10, 0.30, 0.18, 0.01)
    years = st.slider("Projection horizon (years)", 3, 7, 5, 1)
    price_growth = st.slider("Price growth per year", 0.00, 0.20, 0.05, 0.01)
    st.caption("Tweak these to run quick scenario tests across all models.")

st.title("🩺 Pakistan Healthcare Feasibility – Pilot Dashboard")
st.markdown("**Deliver First : Develop Second** — three venture templates in the PKR 10–50M window. Adjust assumptions to see ROI, payback, NPV, IRR.")

tabs = st.tabs(["Diagnostics Micro-Clinic", "Tele-Wellness Platform", "Cosmetic / Laser Studio"])

# ---------- 1) Diagnostics
with tabs[0]:
    st.subheader("Diagnostics & Imaging Micro-Clinic")
    col1, col2, col3 = st.columns(3)
    with col1:
        capex = st.slider("CAPEX (PKR M)", 10.0, 60.0, 35.0, 1.0) * 1e6
        lease_ratio = st.slider("Lease share of equipment CAPEX", 0.0, 0.8, 0.5, 0.05)
        opex_ratio = st.slider("OPEX as % of revenue", 0.40, 0.80, 0.58, 0.01)
    with col2:
        avg_price = st.number_input("Avg revenue per test (PKR)", 1500.0, 15000.0, 4200.0, 100.0)
        tests_per_day = st.number_input("Tests per day (avg)", 30.0, 300.0, 120.0, 5.0)
        utilization = st.slider("Utilization (days/year)", 200, 340, 300, 5)
    with col3:
        staffing = st.number_input("Annual staffing cost (PKR M)", 5.0, 60.0, 18.0, 0.5) * 1e6
        other_fixed = st.number_input("Other fixed costs (PKR M)", 1.0, 20.0, 6.0, 0.5) * 1e6
        lease_cost = st.number_input("Annual lease (as % of leased CAPEX)", 0.0, 0.25, 0.12, 0.01)

    gross_rev = avg_price * tests_per_day * utilization
    variable_costs = opex_ratio * gross_rev * (1 + fx_depreciation)
    lease_payment = lease_cost * (capex * lease_ratio)
    ebitda = gross_rev - variable_costs - staffing - other_fixed - lease_payment
    tax_rate = 0.20
    tax = max(0.0, ebitda) * tax_rate
    fcfe = ebitda - tax

    flows = [-capex] + [fcfe * ((1 + price_growth) ** (t-1)) for t in range(1, years+1)]
    npv = npf.npv(discount_rate, flows)
    irr = npf.irr(flows)
    payback = simple_payback(capex, fcfe)

    st.markdown("### Results")
    m = pd.DataFrame({
        "Metric": ["Revenue (Year 1)", "EBITDA (Year 1)", "Tax (Year 1)", "FCFE (Year 1)", "Simple Payback (yrs)", "NPV", "IRR"],
        "Value": [pkr(gross_rev), pkr(ebitda), pkr(tax), pkr(fcfe),
                  f"{payback:,.1f}" if payback==payback else "n/a",
                  pkr(npv), f"{irr*100:.1f}%"]
    })
    st.dataframe(m, use_container_width=True)

# ---------- 2) Tele-Wellness
with tabs[1]:
    st.subheader("Tele-Wellness Platform")
    col1, col2, col3 = st.columns(3)
    with col1:
        capex = st.slider("Initial build & setup (PKR M)", 5.0, 35.0, 18.0, 0.5) * 1e6
        users = st.number_input("Users (Year 1)", 1000, 200000, 25000, 1000)
        arpu = st.number_input("Avg monthly ARPU (PKR)", 200.0, 2000.0, 550.0, 50.0)
    with col2:
        cogs_ratio = st.slider("Direct service cost (% revenue)", 0.05, 0.40, 0.15, 0.01)
        sga_ratio = st.slider("Sales & marketing (% revenue)", 0.10, 0.60, 0.25, 0.01)
        churn = st.slider("Monthly churn", 0.00, 0.15, 0.05, 0.01)
    with col3:
        growth_users = st.slider("User growth per year", 0.05, 1.00, 0.35, 0.05)
        arpu_growth = st.slider("ARPU growth per year", 0.00, 0.25, 0.08, 0.01)
        fixed_costs = st.number_input("Fixed platform costs (PKR M)", 5.0, 50.0, 12.0, 0.5) * 1e6

    rev_y1 = users * arpu * 12
    y = users
    flows = [-capex]
    for t in range(1, years+1):
        if t > 1:
            y = y * (1 + growth_users) * (1 - churn*12*0.4)
        arpu_t = arpu * ((1 + arpu_growth) ** (t-1))
        rev_t = y * arpu_t * 12
        cogs = cogs_ratio * rev_t * (1 + fx_depreciation*0.3)
        sga = sga_ratio * rev_t
        ebitda = rev_t - cogs - sga - fixed_costs
        tax = max(0.0, ebitda) * 0.20
        fcfe = ebitda - tax
        flows.append(fcfe)

    npv = npf.npv(discount_rate, flows)
    irr = npf.irr(flows)
    payback = np.nan
    if flows[1] > 0:
        payback = simple_payback(-flows[0], flows[1])

    st.markdown("### Results")
    m = pd.DataFrame({
        "Metric": ["Revenue (Year 1)", "EBITDA (Year 1 est.)", "Simple Payback (approx.)", "NPV", "IRR"],
        "Value": [pkr(rev_y1), pkr(flows[1]+0), f"{payback:,.1f}" if payback==payback else "n/a", pkr(npv), f"{irr*100:.1f}%"]
    })
    st.dataframe(m, use_container_width=True)

# ---------- 3) Cosmetic / Laser Studio
with tabs[2]:
    st.subheader("Cosmetic / Laser Therapy Studio")
    col1, col2, col3 = st.columns(3)
    with col1:
        capex = st.slider("Fit-out & devices (PKR M)", 8.0, 40.0, 22.0, 0.5) * 1e6
        sessions_per_day = st.number_input("Sessions per day", 10.0, 120.0, 45.0, 1.0)
        avg_price = st.number_input("Avg revenue per session (PKR)", 3000.0, 30000.0, 9000.0, 250.0)
    with col2:
        days = st.slider("Operating days / year", 220, 340, 300, 5)
        consumables_ratio = st.slider("Consumables (% revenue)", 0.05, 0.35, 0.15, 0.01)
        marketing_ratio = st.slider("Marketing (% revenue)", 0.05, 0.30, 0.12, 0.01)
    with col3:
        staffing = st.number_input("Annual staffing cost (PKR M)", 4.0, 40.0, 14.0, 0.5) * 1e6
        rent = st.number_input("Rent & utilities (PKR M)", 2.0, 25.0, 9.0, 0.5) * 1e6
        price_growth_local = st.slider("Price growth per year (studio)", 0.00, 0.25, 0.07, 0.01)

    rev = sessions_per_day * avg_price * days
    consumables = consumables_ratio * rev * (1 + fx_depreciation*0.5)
    marketing = marketing_ratio * rev
    ebitda = rev - consumables - marketing - staffing - rent
    tax = max(0.0, ebitda) * 0.20
    fcfe = ebitda - tax

    flows = [-capex]
    for t in range(1, years+1):
        rev_t = rev * ((1 + price_growth_local) ** (t-1))
        cons_t = consumables_ratio * rev_t * (1 + fx_depreciation*0.5)
        mkt_t = marketing_ratio * rev_t
        ebitda_t = rev_t - cons_t - mkt_t - staffing - rent
        tax_t = max(0.0, ebitda_t) * 0.20
        fcfe_t = ebitda_t - tax_t
        flows.append(fcfe_t)

    npv = npf.npv(discount_rate, flows)
    irr = npf.irr(flows)
    payback = simple_payback(capex, fcfe)

    st.markdown("### Results")
    m = pd.DataFrame({
        "Metric": ["Revenue (Year 1)", "EBITDA (Year 1)", "Tax (Year 1)", "FCFE (Year 1)", "Simple Payback (yrs)", "NPV", "IRR"],
        "Value": [pkr(rev), pkr(ebitda), pkr(tax), pkr(fcfe),
                  f"{payback:,.1f}" if payback==payback else "n/a",
                  pkr(npv), f"{irr*100:.1f}%"]
    })
    st.dataframe(m, use_container_width=True)

st.caption("© MBBB Consulting | Ken Holden — Deliver First : Develop Second — Pilot feasibility tool")

  
