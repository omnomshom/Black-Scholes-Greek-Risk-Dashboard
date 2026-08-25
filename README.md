# Black Scholes Greek Risk Dashboard
A Black-Scholes option Greeks and dashboard suite built with Python and Streamlit. Features real-time parameter sliders, 2D heatmaps, 3D interactive surfaces, cross-sectional sensitivity slices, and automated pin-risk diagnostics.

# Features 
Advanced Greek Calculations - Computes full 1st-order (Delta, Gamma, Theta, Vega, Rho), 2nd-order (Vanna, Vomma), and 3rd-order (Charm, Speed, Zomma) Greeks.
Pin-Risk & Stress-Test Diagnostics - Automated alert engine that flags critical gamma pin risks, charm drift, and volatility acceleration thresholds.
Interactive Visualizations - Dynamic 2D heatmaps and 3D interactive surfaces rendered via Plotly.
Cross-Sectional Slices - sensitivity curves across varying timeframes and volatility levels.
Data Export - Instant matrix grid calculations and CSV export capabilities.

Main Language - Python
Web Framework - Streamlit
Numerical Computing - NumPy, SciPy 
Data Manipulation - Pandas
Visualization - Plotly

# Installation and Setup 
1. Clone the repository:
   ```bash
   git clone https://github.com/omnomshom/Black-Scholes-Greek-Risk-Dashboard.git
   cd Black-Scholes-Greek-Risk-Dashboard
   ```

2. **Install the required dependencies:**
   ```bash
   pip install streamlit numpy pandas plotly scipy
   ```

3. **Run the Streamlit application:**
   ```bash
   streamlit run Main.py

# Usage Guide 

1. Sidebar Parameters - Configure your option specifications including option Type (Call/Put), underlying Stock Price, strike price, time to expiry, risk-free rate, and volatility.
2. Diagnostics Banner - Review automated safety warnings regarding gamma pinning or charm decay.
3. Dashboards & Tabs
   - Heatmaps / 3D Surfaces - explore visual exposure profiles across parameter space.
   - Cross-Sectional Slices - analyse localized sensitivity gradients.
   - Raw Data Export - download complete computed matrix grids as CSV files.
