import io
import numpy as np
import pandas as pd
import plotly.graph_objects as go
from scipy.stats import norm
import streamlit as st

# ---------------------------------------------------------
# 1. PAGE CONFIGURATION & CUSTOM STYLING
# ---------------------------------------------------------
st.set_page_config(
    page_title="Institutional Option Greeks Engine",
    layout="wide",
    initial_sidebar_state="expanded",
)

# Custom CSS for UI Polish
st.markdown(
    """
    <style>
    /* Metric Card Styling */
    div[data-testid="stMetric"] {
        background-color: rgba(255, 255, 255, 0.03);
        border: 1px solid rgba(255, 255, 255, 0.1);
        padding: 12px 16px;
        border-radius: 8px;
        box-shadow: 0 2px 4px rgba(0,0,0,0.1);
    }

    /* Clean Sidebar Button Spacing */
    div[data-testid="stSidebar"] div.stButton > button {
        width: 100%;
        border-radius: 6px;
    }

    /* Subtle Header Lines */
    .sub-header {
        font-size: 1.1rem;
        font-weight: 600;
        margin-top: 1rem;
        margin-bottom: 0.5rem;
    }
    </style>
    """,
    unsafe_allow_html=True,
)


# ---------------------------------------------------------
# 2. CACHED GREEK & MATRIX CALCULATION ENGINE
# ---------------------------------------------------------
def black_scholes_greeks(S, K, T, r, sigma, option_type):
    """Calculate Black-Scholes 1st, 2nd, and 3rd Order Option Greeks."""
    T = np.maximum(T, 1e-5)
    sigma = np.maximum(sigma, 1e-5)

    d1 = (np.log(S / K) + (r + 0.5 * sigma ** 2) * T) / (sigma * np.sqrt(T))
    d2 = d1 - sigma * np.sqrt(T)

    pdf_d1 = norm.pdf(d1)
    cdf_d1 = norm.cdf(d1)
    cdf_d2 = norm.cdf(d2)

    # 1st Order
    if option_type == "call":
        delta = cdf_d1
        theta = -(S * pdf_d1 * sigma) / (
                2 * np.sqrt(T)
        ) - r * K * np.exp(-r * T) * cdf_d2
        rho = K * T * np.exp(-r * T) * cdf_d2
    else:
        delta = cdf_d1 - 1
        theta = -(S * pdf_d1 * sigma) / (
                2 * np.sqrt(T)
        ) + r * K * np.exp(-r * T) * norm.cdf(-d2)
        rho = -K * T * np.exp(-r * T) * norm.cdf(-d2)

    gamma = pdf_d1 / (S * sigma * np.sqrt(T))
    vega = S * pdf_d1 * np.sqrt(T)

    # 2nd Order
    vanna = -pdf_d1 * (d2 / sigma)
    vomma = vega * (d1 * d2 / sigma)

    # 3rd Order
    charm = -pdf_d1 * (
            2 * r * T - d2 * sigma * np.sqrt(T)
    ) / (2 * T * sigma * np.sqrt(T))
    speed = -gamma * (d1 / (sigma * np.sqrt(T)) + 1) / S
    zomma = gamma * (d1 * d2 - 1) / sigma

    return {
        "Delta": delta,
        "Gamma": gamma,
        "Theta (annual)": theta,
        "Theta (daily)": theta / 365,
        "Vega (per 1%)": vega / 100,
        "Rho (per 1%)": rho / 100,
        "Vanna (per 1%)": vanna / 100,
        "Vomma (per 1%)": vomma / 100,
        "Charm (daily)": charm / 365,
        "Speed": speed,
        "Zomma (per 1%)": zomma / 100,
    }


@st.cache_data(show_spinner=False)
def calculate_greeks_grid(S_range, Y_range, K, r, static_val, y_axis_var, option_type):
    """Calculates full 2D meshgrid matrix operations with Streamlit caching."""
    if y_axis_var == "Time to Expiry (Years)":
        S_grid, Y_grid = np.meshgrid(S_range, Y_range)
        return black_scholes_greeks(S_grid, K, Y_grid, r, static_val, option_type)
    else:
        S_grid, Y_grid = np.meshgrid(S_range, Y_range)
        return black_scholes_greeks(S_grid, K, static_val, r, Y_grid, option_type)


# ---------------------------------------------------------
# 3. STRESS-TEST & RISK ALERT ENGINE
# ---------------------------------------------------------
def render_risk_alerts(S, K, T, greeks):
    """Analyze position parameters and issue automated risk warnings."""
    alerts = []
    monitored_spot_dist = abs(S - K) / K

    if T <= (30 / 365) and monitored_spot_dist <= 0.03:
        alerts.append((
            "error",
            f"**HIGH GAMMA PIN RISK ALERT:** Option is {T * 365:.1f} days from expiry and within {monitored_spot_dist * 100:.1f}% of strike. Expect extreme Delta acceleration and rapid hedging requirements.",
        ))

    if abs(greeks["Charm (daily)"]) >= 0.01:
        alerts.append((
            "warning",
            f"**HIGH CHARM DRIFT:** Delta decays by **{greeks['Charm (daily)']:.4f} per day** overnight without any underlying stock price movement.",
        ))

    if abs(greeks["Vomma (per 1%)"]) >= 0.02:
        alerts.append((
            "info",
            f"**HIGH VOMMA VOLATILITY ACCELERATION:** Vega is highly sensitive to volatility changes (Vomma = {greeks['Vomma (per 1%)']:.4f}). Implied Volatility spikes will non-linearly expand option value.",
        ))

    if not alerts:
        st.success(
            "**STABLE GREEK PROFILE:** No immediate Gamma Pin, Charm Drift, or Vomma risk warnings detected for current parameters."
        )
    else:
        for alert_type, msg in alerts:
            getattr(st, alert_type)(msg)


# ---------------------------------------------------------
# 4. MAIN APP LAYOUT
# ---------------------------------------------------------
def main():
    st.title("Black-Scholes Greek & Risk Suite")

    # Session State Initialization for Scenario Presets
    if "S" not in st.session_state: st.session_state.S = 100.0
    if "K" not in st.session_state: st.session_state.K = 100.0
    if "T" not in st.session_state: st.session_state.T = 0.1
    if "r_pct" not in st.session_state: st.session_state.r_pct = 5.0
    if "sigma_pct" not in st.session_state: st.session_state.sigma_pct = 20.0
    
    st.sidebar.header("Option Parameters")
    option_type = st.sidebar.selectbox("Option Type", ["call", "put"])
    S = st.sidebar.number_input("Underlying Stock Price ($)", min_value=0.01, value=st.session_state.S, step=1.0)
    K = st.sidebar.number_input("Strike Price ($)", min_value=0.01, value=st.session_state.K, step=1.0)
    T = st.sidebar.number_input("Time to Expiry (years)", min_value=0.001, value=st.session_state.T, step=0.05)
    r_pct = st.sidebar.number_input("Risk-free Interest Rate (%)", min_value=0.0, value=st.session_state.r_pct,
                                    step=0.1)
    sigma_pct = st.sidebar.number_input("Volatility (%)", min_value=0.01, value=st.session_state.sigma_pct, step=1.0)

    r = r_pct / 110.0
    sigma = sigma_pct / 100.0

    st.sidebar.divider()
    st.sidebar.header("Visualization Settings")
    y_axis_var = st.sidebar.radio("Y-Axis Variable", ["Time to Expiry (Years)", "Volatility (%)"])

    COLOR_THEMES = {
        "Purple & Yellow": "Viridis",
        "Red & Green": "RdYlGn",
        "Phoenix": "Plasma",
        "Navy & Yellow": "Cividis",
        "White & Blue": "Blues",
        "Thermal": "Hot",
        "Red & Blue": "RdBu",
    }


    selected_theme_label = st.sidebar.selectbox("Chart Color Theme", options=list(COLOR_THEMES.keys()))
    color_choice = COLOR_THEMES[selected_theme_label]

    # Calculate Point Estimate Greeks
    greeks = black_scholes_greeks(S, K, T, r, sigma, option_type)

    # Risk Alerts Banner
    st.markdown("### Risk & Pin-Risk Diagnostics")
    render_risk_alerts(S, K, T, greeks)

    st.divider()

    # Metrics Dashboard
    st.markdown("### 1st Order Greeks")
    c1 = st.columns(5)
    c1[0].metric("Delta", f"{greeks['Delta']:.4f}")
    c1[1].metric("Gamma", f"{greeks['Gamma']:.4f}")
    c1[2].metric("Theta (Daily)", f"{greeks['Theta (daily)']:.4f}")
    c1[3].metric("Vega (per 1%)", f"{greeks['Vega (per 1%)']:.4f}")
    c1[4].metric("Rho (per 1%)", f"{greeks['Rho (per 1%)']:.4f}")

    st.markdown("<div class='sub-header'>2nd & 3rd Order Higher Greeks</div>", unsafe_allow_html=True)
    c2 = st.columns(5)
    c2[0].metric("Vanna (dDelta/dVol)", f"{greeks['Vanna (per 1%)']:.4f}",
                 help="Delta sensitivity per 1% change in Volatility")
    c2[1].metric("Vomma (dVega/dVol)", f"{greeks['Vomma (per 1%)']:.4f}",
                 help="Vega sensitivity per 1% change in Volatility")
    c2[2].metric("Charm (Daily Delta Decay)", f"{greeks['Charm (daily)']:.4f}", help="Delta decay per calendar day")
    c2[3].metric("Speed (dGamma/dSpot)", f"{greeks['Speed']:.6f}", help="Gamma sensitivity to spot price move")
    c2[4].metric("Zomma (dGamma/dVol)", f"{greeks['Zomma (per 1%)']:.4f}", help="Gamma sensitivity to volatility move")

    st.divider()

    # Dynamic Meshgrid Calculation
    S_range = np.linspace(max(0.01, S * 0.5), S * 1.5, 60)

    if y_axis_var == "Time to Expiry (Years)":
        Y_range = np.linspace(0.005, max(T * 1.5, 1.0), 60)
        surfaces = calculate_greeks_grid(S_range, Y_range, K, r, sigma, y_axis_var, option_type)
        y_label = "Time to Expiry (Years)"
        Y_plot_vals = Y_range
        current_y_val = T
    else:
        Y_range = np.linspace(0.05, max(sigma * 2.0, 1.0), 60)
        surfaces = calculate_greeks_grid(S_range, Y_range, K, r, T, y_axis_var, option_type)
        y_label = "Volatility (%)"
        Y_plot_vals = Y_range * 100
        current_y_val = sigma_pct

    greeks_to_plot = {
        "Delta": surfaces["Delta"],
        "Gamma": surfaces["Gamma"],
        "Theta (Daily)": surfaces["Theta (daily)"],
        "Vega (per 1%)": surfaces["Vega (per 1%)"],
        "Vanna (per 1%)": surfaces["Vanna (per 1%)"],
        "Vomma (per 1%)": surfaces["Vomma (per 1%)"],
        "Charm (Daily)": surfaces["Charm (daily)"],
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
        for i, (g_name, Z) in enumerate(greeks_to_plot.items()):
            fig_2d = go.Figure(
                data=go.Heatmap(
                    x=S_range,
                    y=Y_plot_vals,
                    z=Z,
                    colorscale=color_choice,
                    colorbar=dict(title=g_name),
                    hovertemplate="Stock: %{x:$.2f}<br>" + f"{y_label}: %{{y:.2f}}<br>{g_name}: %{{z:.4f}}<extra></extra>",
                )
            )
            fig_2d.add_vline(x=S, line_dash="dash", line_color="red", opacity=0.7, annotation_text=f"S=${S:.2f}")
            fig_2d.add_hline(y=current_y_val, line_dash="dash", line_color="white", opacity=0.7,
                             annotation_text=f"Current={current_y_val:.2f}")
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
        for i, (g_name, Z) in enumerate(greeks_to_plot.items()):
            fig_3d = go.Figure(data=[go.Surface(x=S_range, y=Y_plot_vals, z=Z, colorscale=color_choice)])
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
            slice_variable = st.radio("Overlay Comparison Across:", ["Time to Expiry (T)", "Volatility (σ)"],
                                      horizontal=True)

        fig_1d = go.Figure()
        if slice_variable == "Time to Expiry (T)":
            timeframes = [0.02, 0.08, 0.25, 0.5, 1.0]
            for t_val in timeframes:
                g_slice = black_scholes_greeks(S_range, K, t_val, r, sigma, option_type)
                fig_1d.add_trace(go.Scatter(x=S_range, y=g_slice[target_greek], mode="lines",
                                            name=f"T = {t_val:.2f} Yrs ({int(t_val * 365)}d)"))
        else:
            vol_levels = [0.10, 0.20, 0.35, 0.50, 0.80]
            for v_val in vol_levels:
                g_slice = black_scholes_greeks(S_range, K, T, r, v_val, option_type)
                fig_1d.add_trace(
                    go.Scatter(x=S_range, y=g_slice[target_greek], mode="lines", name=f"Vol = {int(v_val * 100)}%"))

        fig_1d.add_vline(x=S, line_dash="dash", line_color="red", annotation_text=f"Current S = ${S:.2f}")
        fig_1d.update_layout(
            title=f"{target_greek} Profile across {slice_variable}",
            xaxis_title="Stock Price ($)",
            yaxis_title=target_greek,
            height=500,
            margin=dict(l=30, r=30, b=30, t=50),
        )
        st.plotly_chart(fig_1d, use_container_width=True)

    # Raw Data Export Tab
    with tab4:
        st.markdown("### Raw Surface Grid Export")
        export_greek = st.selectbox("Select Greek Grid to Download", list(greeks_to_plot.keys()))

        df_export = pd.DataFrame(
            greeks_to_plot[export_greek],
            index=np.round(Y_plot_vals, 3),
            columns=np.round(S_range, 2)
        )
        df_export.index.name = y_label

        st.dataframe(df_export.style.format("{:.4f}"), use_container_width=True)

        csv_buffer = io.BytesIO()
        df_export.to_csv(csv_buffer)

        st.download_button(
            label=f"Download {export_greek} Matrix CSV",
            data=csv_buffer.getvalue(),
            file_name=f"{export_greek.lower().replace(' ', '_')}_grid.csv",
            mime="text/csv",
            use_container_width=True,
        )

    st.divider()
    with st.expander("Greek Formulas Reference"):
        st.markdown(
            r"""
            **Base Equations:**  
            $d_1 = \frac{\ln(S/K) + (r + \frac{1}{2}\sigma^2)T}{\sigma\sqrt{T}}, \quad d_2 = d_1 - \sigma\sqrt{T}$

            ---

            **1st Order Greeks:**
            * $\Delta_{Call} = N(d_1), \quad \Delta_{Put} = N(d_1) - 1$
            * $\Gamma = \frac{N'(d_1)}{S \sigma \sqrt{T}}$
            * $\Theta_{Call} = -\frac{S N'(d_1) \sigma}{2\sqrt{T}} - r K e^{-rT} N(d_2)$
            * $\text{Vega} = S N'(d_1) \sqrt{T}$

            ---

            **2nd Order Greeks:**
            * $\text{Vanna} = \frac{\partial \Delta}{\partial \sigma} = -N'(d_1) \frac{d_2}{\sigma}$
            * $\text{Vomma} = \frac{\partial \text{Vega}}{\partial \sigma} = \text{Vega} \times \frac{d_1 d_2}{\sigma}$

            ---

            **3rd Order Greeks:**
            * $\text{Charm} = \frac{\partial \Delta}{\partial T} = -N'(d_1) \left[ \frac{2rT - d_2 \sigma \sqrt{T}}{2 T \sigma \sqrt{T}} \right]$
            * $\text{Speed} = \frac{\partial \Gamma}{\partial S} = -\frac{\Gamma}{S} \left[ \frac{d_1}{\sigma \sqrt{T}} + 1 \right]$
            * $\text{Zomma} = \frac{\partial \Gamma}{\partial \sigma} = \Gamma \left[ \frac{d_1 d_2 - 1}{\sigma} \right]$
            """
        )

if __name__ == "__main__":
    main()
