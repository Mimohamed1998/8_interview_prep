# Outlet Cluster Definitions

Based on the predefined outlet thresholds and the K-Means clustering results from the `product_classification.ipynb` pipeline, the outlet population has been segmented into **4 distinct clusters** (2 rule-based, 2 behavioral K-Means clusters).

## 1. Rule-Based Predefined Clusters

These clusters were separated *before* the K-Means algorithm to prevent distribution distortion by outliers and inactive accounts.

### 1.1 Churned Outlets
- **Definition**: Outlets with `active_months == 0` over the trailing 12-month window (`is_active == False`).
- **Population**: ~49,447 outlets.
- **Characteristics**: These outlets have completely stopped purchasing. They require a distinct reactivation scoring model rather than standard demand forecasting.

### 1.2 Power Outlets
- **Definition**: Active outlets whose `total_net_sales` exceeds the 3× IQR upper bound (Q3 + 3*IQR).
- **Population**: ~4,534 outlets.
- **Revenue Impact**: Account for ~72.22% of total gross sales.
- **Characteristics**: These are the mega-accounts. They represent the structural anchors of the business and warrant individualized account-level demand models rather than aggregate cluster models.

---

## 2. K-Means Behavioral Clusters (Mainstream Outlets)

The remaining ~62,202 active outlets were clustered using K-Means (`k=2`) on 7 log-transformed and scaled behavioral features.

### 2.1 Cluster 0: High-Value Active
- **Population Proportion**: Moderate
- **Key Characteristics**:
  - **High Frequency & Spend**: Frequent purchasers (~4.1 transactions per active month) with strong basket sizes averaging ~$5,053.
  - **Category Breadth**: Purchasing across roughly ~4 categories on average.
  - **Cash & Returns**: Moderately high cash usage (~42%) and higher return rates (~26%).
- **Business Implication**: This segment constitutes the core active base of mainstream outlets. They drive significant volume and buy across multiple categories, but they also have elevated return rates which must be managed. 

### 2.2 Cluster 1: Low-Value Sporadic
- **Population Proportion**: Largest
- **Key Characteristics**:
  - **Low Frequency & Spend**: Infrequent purchases (~1.8 transactions per active month) with small basket sizes averaging ~$1,264.
  - **Category Breadth**: Narrow product selection, purchasing from only ~1.9 categories.
  - **Low Returns**: Very clean purchasing behavior with low return rates (~5.5%).
- **Business Implication**: This is the long-tail convenience segment. They buy small amounts infrequently and stick to a narrow range of products, but their orders rarely result in returns. The strategy here should focus on cost-to-serve minimization and automated fulfillment.
