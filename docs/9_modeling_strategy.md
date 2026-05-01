# XGBoost Modeling Strategy

## Overview

This document outlines the modeling strategy across the product/item classifications (Continuous, Intermittent, Lumpy) and active outlet segments (Power Outlets, High-Value Active, Low-Value Sporadic). As per the defined scope, **Churned outlets are excluded** from this demand forecasting strategy. 

The strategy utilizes **XGBoost models** across the board. For the highly sporadic demand of **Lumpy** items within the mainstream outlet clusters (Cluster 0 and 1), a two-stage approach incorporating a classification model is used.

---

## 3x3 Modeling Grid

| Outlet Classification \ Product Classification | Continuous | Intermittent | Lumpy |
| :--- | :--- | :--- | :--- |
| **Power Outlets**<br>*(Top ~4.5K mega-accounts)* | **XGBoost Regressor** | **XGBoost Regressor** | **XGBoost Regressor** |
| **Cluster 0: High-Value Active**<br>*(Frequent, high-spend)* | **XGBoost Regressor** | **XGBoost Regressor** | **XGBoost Classifier + Regressor** |
| **Cluster 1: Low-Value Sporadic**<br>*(Infrequent, small-basket)* | **XGBoost Regressor** | **XGBoost Regressor** | **XGBoost Classifier + Regressor** |

---

## Technical Approach by Outlet Segment

### 1. Power Outlets
For these high-frequency mega-accounts, standard regression is sufficient to predict demand volume across all product classes:
- **Model**: XGBoost Regressor.
- **Granularity**: Modeled specifically to maximize accuracy for the segment driving ~72% of revenue.
- **Target**: Demand quantity/sales (log-transformed where skewness is high).

### 2. Mainstream Clusters (Cluster 0 & 1)
For the mainstream active segments (Cluster 0 and Cluster 1), the modeling approach depends on the product class:
- **Continuous & Intermittent Items**: Modeled using an **XGBoost Regressor**. 
- **Lumpy Items**: To handle the extreme zero-inflated and erratic nature of lumpy demand within these clusters, a two-stage modeling approach is applied:
  - **Stage 1 (Classification)**: An **XGBoost Classifier** predicts the probability of a non-zero demand event (i.e., *Will this segment buy this Lumpy SKU in the next period?*).
  - **Stage 2 (Regression)**: If the classifier predicts a purchase event, an **XGBoost Regressor** is conditionalized to predict the actual volume/spend (i.e., *How much will they buy?*).
  - **Benefit**: Explicitly separating the inter-arrival probability from the demand size resolves the zero-inflation bias that typically breaks regressors on lumpy distributions.

## Integration with Product Classes
While the primary model architectures (Regressor vs Classifier+Regressor) are defined by the **Outlet rows**, the **Product columns** (Continuous, Intermittent, Lumpy) govern the feature engineering and temporal treatment within the XGBoost estimators:
- **Continuous**: Heavy reliance on seasonal lag features and STL indices.
- **Intermittent/Lumpy**: Reliance on rolling aggregate features and larger time-windows to capture sparse demand signals smoothly, mimicking traditional methods like Croston and ADIDA.
