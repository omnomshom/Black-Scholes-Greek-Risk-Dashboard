# Imports
import numpy as np
import pandas as pd
import plotly.graph_objects as go
from scipy.stats import norm
import streamlit as st

# Styling
st.set_page_config(
    page_title="Option Greeks Dashboard",
    layout="wide",
)

# CSS injection for styling clickable elements
# noinspection SpellCheckingInspection
st.markdown(
    """
    <style>
    /* Force 0px border-radius globally on all elements */
    *, *::before, *::after {
        border-radius: 0px !important;
    }

    /* Target input fields, dropdown menus, and number adjusters */
    div[data-baseweb="select"] > div,
    div[data-baseweb="base-input"],
    div[data-baseweb="input"] > div,
    .stNumberInput div,
    .stSelectbox div {
        border-radius: 0px !important;
    }

    /* Override previous metric card border-radius */
    div[data-testid="stMetric"] {
        background-color: rgba(255, 255, 255, 0.03);
        border: 1px solid rgba(255, 255, 255, 0.1);
        padding: 12px 16px;
        border-radius: 0px !important;
        box-shadow: 0 2px 4px rgba(0,0,0,0.1);
    }

    /* General Streamlit widget and container overrides */
    .stApp,
    .stButton > button,
    .stDownloadButton > button,
    .stForm,
    .stExpander,
    [data-testid="stNotification"],
    [data-testid="stDataFrame"],
    [data-testid="stImage"] img,
    [data-testid="stMainBlockContainer"],
    [data-testid="stVerticalBlock"] > div,
    .stAlert {
        border-radius: 0px !important;
    }
    </style>
    """,
    unsafe_allow_html=True,
)


# Calculation engine
def calculate_greeks(spot_price, strike_price, days_to_expiry, risk_free_rate, dividend_yield, sigma, option_type):
    """Calculate 1st, 2nd, and 3rd Order Option Greeks (with continuous dividend yield) using days to expiry."""
    # Standardised variables
    time_to_expiry_years = np.maximum(days_to_expiry / 365.0, 1e-5 / 365.0)
    sigma = np.maximum(sigma, 1e-5)

    d1 = (
        np.log(spot_price / strike_price)
        + (risk_free_rate - dividend_yield + 0.5 * sigma ** 2) * time_to_expiry_years
    ) / (sigma * np.sqrt(time_to_expiry_years))
    d2 = d1 - sigma * np.sqrt(time_to_expiry_years)

    pdf_d1 = norm.pdf(d1)
    cdf_d1 = norm.cdf(d1)
    cdf_d2 = norm.cdf(d2)
    disc_q = np.exp(-dividend_yield * time_to_expiry_years)
    disc_r = np.exp(-risk_free_rate * time_to_expiry_years)

    # 1st Order
    if option_type == "call":
        delta = disc_q * cdf_d1
        theta = (
            -(spot_price * disc_q * pdf_d1 * sigma) / (2 * np.sqrt(time_to_expiry_years))
            - risk_free_rate * strike_price * disc_r * cdf_d2
            + dividend_yield * spot_price * disc_q * cdf_d1
        )
        rho = strike_price * time_to_expiry_years * disc_r * cdf_d2
    else:
        delta = disc_q * (cdf_d1 - 1)
        theta = (
            -(spot_price * disc_q * pdf_d1 * sigma) / (2 * np.sqrt(time_to_expiry_years))
            + risk_free_rate * strike_price * disc_r * norm.cdf(-d2)
            - dividend_yield * spot_price * disc_q * norm.cdf(-d1)
        )
        rho = -strike_price * time_to_expiry_years * disc_r * norm.cdf(-d2)

    gamma = disc_q * pdf_d1 / (spot_price * sigma * np.sqrt(time_to_expiry_years))
    vega = spot_price * disc_q * pdf_d1 * np.sqrt(time_to_expiry_years)

    # 2nd Order
    vanna = -disc_q * pdf_d1 * (d2 / sigma)
    vomma = vega * (d1 * d2 / sigma)

    # 3rd Order
    charm_common = disc_q * pdf_d1 * (
        2 * (risk_free_rate - dividend_yield) * time_to_expiry_years - d2 * sigma * np.sqrt(time_to_expiry_years)
    ) / (2 * time_to_expiry_years * sigma * np.sqrt(time_to_expiry_years))
    if option_type == "call":
        charm = dividend_yield * disc_q * cdf_d1 - charm_common
    else:
        charm = -dividend_yield * disc_q * norm.cdf(-d1) - charm_common
    speed = -gamma * (d1 / (sigma * np.sqrt(time_to_expiry_years)) + 1) / spot_price
    zomma = gamma * (d1 * d2 - 1) / sigma

    return {
        "Delta": delta,
        "Gamma": gamma,
        "Theta (Annual)": theta,
        "Theta (Daily)": theta / 365,
        "Vega (per 1%)": vega / 100,
        "Rho (per 1%)": rho / 100,
        "Vanna (per 1%)": vanna / 100,
        "Vomma (per 1%)": vomma / 100,
        "Charm (Daily)": charm / 365,
        "Speed": speed,
        "Zomma (per 1%)": zomma / 100,
    }


@st.cache_data(show_spinner=False)
def calculate_greeks_grid(s_range, y_range, strike_price, risk_free_rate, dividend_yield, static_val, y_axis_var, option_type):
    """Calculates full 2D meshgrid matrix operations with Streamlit caching."""
    if y_axis_var == "Time to Expiry (Days)":
        s_grid, y_grid = np.meshgrid(s_range, y_range)
        return calculate_greeks(s_grid, strike_price, y_grid, risk_free_rate, dividend_yield, static_val, option_type)
    else:
        s_grid, y_grid = np.meshgrid(s_range, y_range)
        return calculate_greeks(s_grid, strike_price, static_val, risk_free_rate, dividend_yield, y_grid, option_type)


# Risk alert
def render_risk_alerts(spot_price, strike_price, days_to_expiry, greeks_dict):
    """Analyze position parameters and issue automated risk warnings."""
    alerts = []
    monitored_spot_dist = abs(spot_price - strike_price) / strike_price

    if days_to_expiry <= 30 and monitored_spot_dist <= 0.03:
        alerts.append((
            "error",
            f"**HIGH GAMMA PIN RISK ALERT:** Option is {days_to_expiry:.1f} days from expiry "
            f"and within {monitored_spot_dist * 100:.1f}% of strike. Expect extreme Delta acceleration "
            f"and rapid hedging requirements.",
        ))

    if abs(greeks_dict["Charm (Daily)"]) >= 0.01:
        alerts.append((
            "warning",
            f"**HIGH CHARM DRIFT:** Delta decays by **{greeks_dict['Charm (Daily)']:.4f} per day** "
            f"overnight without any underlying stock price movement.",
        ))

    vomma = greeks_dict["Vomma (per 1%)"]
    VOMMA_HIGH_THRESHOLD = 0.6

    if abs(vomma) >= VOMMA_HIGH_THRESHOLD:
        alerts.append((
            "info",
            f"**HIGH VOMMA VOLATILITY ACCELERATION:** Vega is highly sensitive to volatility "
            f"changes (Vomma = {vomma:.4f}), indicating that Vega will change significantly "
            f"as implied volatility moves. Implied volatility spikes will non-linearly affect "
            f"option value more than usual.",
        ))

    if not alerts:
        st.success(
            "**STABLE GREEK PROFILE:** No immediate Gamma Pin, Charm Drift, or Vomma risk warnings detected for current parameters."
        )
    else:
        for alert_type, msg in alerts:
            getattr(st, alert_type)(msg)


# App layout
def main():
    st.title("Option Greeks Platform")

    if "S" not in st.session_state:
        st.session_state.S = 100.0
    if "K" not in st.session_state:
        st.session_state.K = 105.0
    if "days" not in st.session_state:
        st.session_state.days = 30.0
    if "r_pct" not in st.session_state:
        st.session_state.r_pct = 4.5
    if "q_pct" not in st.session_state:
        st.session_state.q_pct = 1.5
    if "sigma_pct" not in st.session_state:
        st.session_state.sigma_pct = 20.0

    # Main Page Input Controls
    with st.expander("Parameters & Visualization Settings", expanded=True):
        col1, col2, col3 = st.columns(3)

        with col1:
            option_type = st.selectbox("Option Type", ["call", "put"])
            spot_price = st.number_input("Underlying Stock Price ($)", min_value=0.01, value=st.session_state.S, step=1.0)
            strike_price = st.number_input("Strike Price ($)", min_value=0.01, value=st.session_state.K, step=1.0)
            sigma_pct = st.number_input("Volatility (%)", min_value=0.01, value=st.session_state.sigma_pct, step=1.0)

        with col2:
            days_to_expiry = st.number_input(
                "Time to Expiry (Days)", min_value=0.1, value=st.session_state.days, step=1.0
            )
            r_pct = st.number_input(
                "Risk-free Interest Rate (%)", min_value=0.0, value=st.session_state.r_pct, step=0.1
            )
            q_pct = st.number_input(
                "Dividend Yield (%)", min_value=0.0, value=st.session_state.q_pct, step=0.1
            )

        with col3:
            y_axis_var = st.radio("Y-Axis Variable", ["Time to Expiry (Days)", "Volatility (%)"])
            color_themes = {
                "Purple & Yellow": "Viridis",
                "Red & Green": "RdYlGn",
                "Phoenix": "Plasma",
                "Navy & Yellow": "Cividis",
                "White & Blue": "Blues",
                "Thermal": "Hot",
                "Red & Blue": "RdBu",
            }
            selected_theme_label = st.selectbox("Chart Color Theme", options=list(color_themes.keys()))
            color_choice = color_themes[selected_theme_label]

    risk_free_rate = r_pct / 100.0
    dividend_yield = q_pct / 100.0
    sigma = sigma_pct / 100.0

    # Point Estimate Greeks
    greeks_data = calculate_greeks(spot_price, strike_price, days_to_expiry, risk_free_rate, dividend_yield, sigma, option_type)

    # Risk Alerts
    st.markdown("### Risk & Pin-Risk Diagnostics")
    render_risk_alerts(spot_price, strike_price, days_to_expiry, greeks_data)

    st.divider()

    # Metrics Dashboard
    st.markdown("### Primary Greeks")
    c1 = st.columns(4)
    c1[0].metric("Delta", f"{greeks_data['Delta']:.4f}")
    c1[1].metric("Theta (Daily)", f"{greeks_data['Theta (Daily)']:.4f}")
    c1[2].metric("Vega (per 1%)", f"{greeks_data['Vega (per 1%)']:.4f}")
    c1[3].metric("Rho (per 1%)", f"{greeks_data['Rho (per 1%)']:.4f}")

    st.markdown("### Second-Order Greeks")
    c2 = st.columns(3)
    c2[0].metric("Gamma (dDelta/dSpot)", f"{greeks_data['Gamma']:.4f}", help="Delta sensitivity to spot price move")
    c2[1].metric(
        "Vanna (dDelta/dVol)", f"{greeks_data['Vanna (per 1%)']:.4f}", help="Delta sensitivity per 1% change in Volatility"
    )
    c2[2].metric(
        "Vomma (dVega/dVol)", f"{greeks_data['Vomma (per 1%)']:.4f}", help="Vega sensitivity per 1% change in Volatility"
    )

    st.markdown("### Third-Order Greeks")
    c3 = st.columns(3)
    c3[0].metric("Charm (Daily Delta Decay)", f"{greeks_data['Charm (Daily)']:.4f}", help="Delta decay per calendar day")
    c3[1].metric("Speed (dGamma/dSpot)", f"{greeks_data['Speed']:.6f}", help="Gamma sensitivity to spot price move")
    c3[2].metric("Zomma (dGamma/dVol)", f"{greeks_data['Zomma (per 1%)']:.4f}", help="Gamma sensitivity to volatility move")

    st.divider()

    # Meshgrid Calculation
    s_range = np.linspace(max(0.01, spot_price * 0.5), spot_price * 1.5, 60)

    if y_axis_var == "Time to Expiry (Days)":
        y_range = np.linspace(1, max(days_to_expiry * 1.5, 365), 60)
        surfaces = calculate_greeks_grid(
            s_range, y_range, strike_price, risk_free_rate, dividend_yield, sigma, y_axis_var, option_type
        )
        y_label = "Time to Expiry (Days)"
        y_plot_vals = y_range
        current_y_val = days_to_expiry
    else:
        y_range = np.linspace(0.05, max(sigma * 2.0, 1.0), 60)
        surfaces = calculate_greeks_grid(
            s_range, y_range, strike_price, risk_free_rate, dividend_yield, days_to_expiry, y_axis_var, option_type
        )
        y_label = "Volatility (%)"
        y_plot_vals = y_range * 100
        current_y_val = sigma_pct

    greeks_to_plot = {
        "Delta": surfaces["Delta"],
        "Theta (Daily)": surfaces["Theta (Daily)"],
        "Vega (per 1%)": surfaces["Vega (per 1%)"],
        "Rho (per 1%)": surfaces["Rho (per 1%)"],
        "Gamma": surfaces["Gamma"],
        "Vanna (per 1%)": surfaces["Vanna (per 1%)"],
        "Vomma (per 1%)": surfaces["Vomma (per 1%)"],
        "Charm (Daily)": surfaces["Charm (Daily)"],
        "Speed": surfaces["Speed"],
        "Zomma (per 1%)": surfaces["Zomma (per 1%)"],
    }

    # Tabs
    tab1, tab2, tab3, tab4 = st.tabs([
        "Heatmaps",
        "3D Surfaces",
        "Cross-Sectional Profile Slices",
        "Raw Data Export"
    ])

    with tab1:
        st.markdown(f"### 2D Heatmaps (Stock Price vs {y_label})")
        grid_cols_2d = st.columns(2)
        for i, (g_name, z_val) in enumerate(greeks_to_plot.items()):
            fig_2d = go.Figure(
                data=go.Heatmap(
                    x=s_range,
                    y=y_plot_vals,
                    z=z_val,
                    colorscale=color_choice,
                    colorbar=dict(title=g_name),
                    hovertemplate="Stock: %{x:$.2f}<br>" + f"{y_label}: %{{y:.1f}}<br>{g_name}: %{{z:.4f}}<extra></extra>",
                )
            )
            fig_2d.add_vline(x=spot_price, line_dash="dash", line_color="red", opacity=0.7, annotation_text=f"S=${spot_price:.2f}")
            fig_2d.add_hline(
                y=current_y_val, line_dash="dash", line_color="white", opacity=0.7, annotation_text=f"Current={current_y_val:.1f}"
            )
            fig_2d.update_layout(
                title=f"{g_name} Heatmap",
                xaxis_title="Stock Price ($)",
                yaxis_title=y_label,
                height=380,
                margin=dict(l=40, r=40, b=40, t=50),
            )
            with grid_cols_2d[i % 2]:
                st.plotly_chart(fig_2d, use_container_width=True)

    with tab2:
        st.markdown(f"### 3D Surfaces (Stock Price vs {y_label})")
        grid_cols_3d = st.columns(2)
        for i, (g_name, z_val) in enumerate(greeks_to_plot.items()):
            fig_3d = go.Figure(data=[go.Surface(x=s_range, y=y_plot_vals, z=z_val, colorscale=color_choice)])
            fig_3d.update_layout(
                title=f"{g_name} Surface",
                height=450,
                margin=dict(l=20, r=20, b=20, t=40),
                scene=dict(xaxis_title="Stock Price ($)", yaxis_title=y_label, zaxis_title=g_name),
            )
            with grid_cols_3d[i % 2]:
                st.plotly_chart(fig_3d, use_container_width=True)

    with tab3:
        st.markdown("### 1D Cross-Sectional Sensitivity Slices")
        slice_col1, slice_col2 = st.columns(2)
        with slice_col1:
            target_greek = st.selectbox(
                "Select Target Greek to Analyze",
                list(greeks_to_plot.keys()),
            )
        with slice_col2:
            slice_variable = st.radio(
                "Overlay Comparison Across:", ["Time to Expiry (Days)", "Volatility (σ)"], horizontal=True
            )

        fig_1d = go.Figure()
        if slice_variable == "Time to Expiry (Days)":
            day_frames = [7, 30, 90, 180, 365]
            for day_val in day_frames:
                g_slice = calculate_greeks(s_range, strike_price, day_val, risk_free_rate, dividend_yield, sigma, option_type)
                fig_1d.add_trace(
                    go.Scatter(
                        x=s_range,
                        y=g_slice[target_greek],
                        mode="lines",
                        name=f"DTE = {day_val} Days",
                    )
                )
        else:
            vol_levels = [0.10, 0.20, 0.35, 0.50, 0.80]
            for v_val in vol_levels:
                g_slice = calculate_greeks(
                    s_range, strike_price, days_to_expiry, risk_free_rate, dividend_yield, v_val, option_type
                )
                fig_1d.add_trace(
                    go.Scatter(x=s_range, y=g_slice[target_greek], mode="lines", name=f"Vol = {int(v_val * 100)}%")
                )

        fig_1d.add_vline(x=spot_price, line_dash="dash", line_color="red", annotation_text=f"Current S = ${spot_price:.2f}")
        fig_1d.update_layout(
            title=f"{target_greek} Profile across {slice_variable}",
            xaxis_title="Stock Price ($)",
            yaxis_title=target_greek,
            height=500,
            margin=dict(l=30, r=30, b=30, t=50),
        )
        st.plotly_chart(fig_1d, use_container_width=True)

    # Data Export Tab
    with tab4:
        st.markdown("### Raw Surface Grid Export")
        export_greek = st.selectbox("Select Greek Grid to Download", list(greeks_to_plot.keys()))

        df_export = pd.DataFrame(
            greeks_to_plot[export_greek],
            index=np.round(y_plot_vals, 2),
            columns=np.round(s_range, 2)
        )
        df_export.index.name = y_label

        # Streamlit dataframe
        st.dataframe(
            df_export.style.format("{:.4f}"),
            use_container_width=True,
            height=400
        )

        csv_data = df_export.to_csv()

        st.download_button(
            label=f"Download {export_greek} Matrix CSV",
            data=csv_data,
            file_name=f"{export_greek.lower().replace(' ', '_').replace('(', '').replace(')', '').replace('%', 'pct')}_grid.csv",
            mime="text/csv",
            use_container_width=True,
        )


if __name__ == "__main__":
    main()
