# K-Moda — Marketing Mix Modeling (MMM)

Econometric marketing-mix model that attributes a fashion retailer's weekly sales to
its media investment across 8 channels, models diminishing returns, and powers an
interactive budget-simulation dashboard. Academic project (B.Sc. in Mathematical
Engineering, UAX). **Synthetic data.**

## Objective
Estimate how much each advertising channel contributes to sales and explore better
budget allocations — turning media-spend decisions into data-driven ones.

## Data
- Synthetic dataset · weekly national granularity · 2020–2024.
- Training table: **261 weeks × 25 columns**, built from multiple sources (media
  investment, sales lines, orders, web/store traffic, city calendar, products) joined
  by week with LEFT JOINs.
- Target: weekly net sales (ex-VAT).
- 8 media channels: Paid Search, Social Paid, Video Online, Display, Email CRM,
  Exterior, Prensa, Radio Local (≈ €12M/year in media spend).
- Controls: temperature, rainfall, tourism and calendar/campaign flags.

## Methodology
- **Adstock** transformations to capture the carry-over effect of advertising.
- Model comparison (**Ridge, Elastic Net, SARIMAX, ARIMA**); **Ridge** chosen as the
  final MMM to estimate channel contributions under multicollinearity.
- **VIF** analysis for multicollinearity and **Hill saturation curves** for
  diminishing returns.
- Budget optimization with **SciPy** (SLSQP) under realistic constraints.
- Interactive **Streamlit** dashboard to simulate budget reallocations across channels.

## Limitations
National-level aggregation introduces structural multicollinearity between channels — a
known challenge in MMM — which makes individual channel coefficients sensitive and the
results indicative rather than definitive.

## Tech stack
Python · pandas · scikit-learn · statsmodels · SciPy · Streamlit · SQLite

## How to run
​```bash
pip install -r requirements.txt
streamlit run app.py
​```

---
*Academic project · Artificial Intelligence · Universidad Alfonso X el Sabio (UAX) · 2025–2026. Synthetic data.*

---
*Academic project · Artificial Intelligence · Universidad Alfonso X el Sabio (UAX) · 2025–2026. Synthetic data.*
