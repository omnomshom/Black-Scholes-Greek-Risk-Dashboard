# Option Greeks Dashboard
Option Greeks dashboard suite built with Python and Streamlit. Features variable parameters, 2D heatmaps, 3D interactive surfaces, cross-sectional sensitivity slices, and automated pin-risk diagnostics.


# Features 
Greek calculator and visualiser - computes and visualises 1st order (Delta, Gamma, Theta, Vega, Rho), 2nd order (Vanna, Vomma), and 3rd-order (Charm, Speed, Zomma) Greeks.
Pin-risk and stress test diagnostics - automated alert engine that flags critical gamma pin risks, charm drift, and volatility acceleration thresholds.
Interactive visualizations - dynamic heatmaps and interactive 3D surfaces rendered via Plotly.
Cross-sectional slices - sensitivity curves across varying timeframes and volatility levels.
Data export - instant matrix grid calculations and CSV export capabilities.

Main Language - Python
Web Framework - Streamlit
Numerical Computing - NumPy, SciPy 
Data Manipulation - Pandas
Visualization - Plotly


# Installation and Setup 
1. **Clone the repository:**
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

1. Sidebar Parameters - configure your option specifications including option Type (Call/Put), underlying Stock Price, strike price, time to expiry, risk-free rate, and volatility.
2. Diagnostics banner - review automated safety warnings regarding gamma pinning or charm decay.
3. Dashboards and tabs
   - Heatmaps / 3D Surfaces - explore visual exposure profiles across parameter space.
   - Cross-sectional slices - analyse localized sensitivity gradients.
   - Raw data export - download complete computed matrix grids as CSV files.


# Ouputs
<img width="1770" height="622" alt="image" src="https://github.com/user-attachments/assets/b81127d8-46aa-44f9-adb2-b8ee6e5d6add" />

<img width="1817" height="720" alt="image" src="https://github.com/user-attachments/assets/bc4f7252-650b-42e7-8894-d9e8e8fb9757" />

<img width="1367" height="587" alt="image" src="https://github.com/user-attachments/assets/3aeec915-a371-4ad7-bd8f-2934ee5adc1e" />

<img width="1371" height="658" alt="image" src="https://github.com/user-attachments/assets/672a9522-87ff-4233-8302-2f0e3a7d94ce" />

<img width="1346" height="801" alt="image" src="https://github.com/user-attachments/assets/6d6d3fe4-12ae-4247-95f4-aaa9a75f74d7" />

<img width="1380" height="787" alt="image" src="https://github.com/user-attachments/assets/a41e8268-fbdc-4dd3-9d56-e09a8c9977e5" />




