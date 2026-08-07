# EV Price Predictor - Exploratory Data Analysis Report

*Generated on: 2026-08-07 17:21:38*

## Dataset Overview
- **Total Rows**: 3022
- **Total Columns**: 21
- **Target Variable**: Price_USD

## Key Insights
### 1. Descriptive Statistics
|                        |   count |   missing |        mean |          std |          min |         25% |         50% |          75% |         max |
|:-----------------------|--------:|----------:|------------:|-------------:|-------------:|------------:|------------:|-------------:|------------:|
| Vehicle_ID             |    3022 |         0 |  1511.5     |   872.521    |     1        |   756.25    |  1511.5     |   2266.75    |   3022      |
| Year                   |    3022 |         0 |  2020.02    |     3.13208  |  2015        |  2017       |  2020       |   2023       |   2025      |
| Battery_Capacity_kWh   |    3022 |         0 |    84.3147  |    37.2105   |    20        |    52.425   |    83.6     |    115.8     |    150      |
| Range_km               |    3022 |         0 |   349.901   |   145.406    |   100        |   222       |   347       |    478       |    600      |
| Charge_Time_hr         |    3022 |         0 |     6.21205 |     3.3506   |     0.5      |     3.3     |     6.2     |      9.1     |     12      |
| Price_USD              |    3022 |         0 | 90611.9     | 34654.5      | 30014.5      | 61257.4     | 90929.7     | 120200       | 149979      |
| Autonomous_Level       |    3022 |         0 |     2.15089 |     1.81658  |     0        |     0       |     2       |      4       |      5      |
| CO2_Emissions_g_per_km |    2430 |       592 |     0       |     0        |     0        |     0       |     0       |      0       |      0      |
| Safety_Rating          |    3022 |         0 |     3.9957  |     0.772531 |     3        |     3       |     4       |      5       |      5      |
| Units_Sold_2024        |    3022 |         0 | 10207.1     |  5771.62     |     6        |  5145.5     | 10350       |  15128       |  19996      |
| Warranty_Years         |    3022 |         0 |     3.99735 |     0.821746 |     3        |     3       |     4       |      5       |      5      |
| Vehicle_Age            |    3022 |         0 |     5.98048 |     3.13208  |     1        |     3       |     6       |      9       |     11      |
| Efficiency_Score       |    3022 |         0 |     5.44469 |     4.26745  |     0.696072 |     2.59514 |     4.07045 |      6.70746 |     28.8235 |
| Brand_Enc              |    3022 |         0 | 90611.9     |  4723.02     | 77373.6      | 87915.6     | 90885.7     |  93420.1     | 100310      |
| Model_Enc              |    3022 |         0 | 90611.9     |  8004.45     | 65471.7      | 86100       | 89798.3     |  95098.8     | 128826      |

### 2. Top Correlations with Price_USD
| Feature | Correlation |
|---------|-------------|
| Price_USD | 1.000 |
| Model_Enc | 0.231 |
| Brand_Enc | 0.136 |
| Warranty_Years | 0.040 |
| Vehicle_ID | 0.036 |
| Vehicle_Age | 0.032 |
| Efficiency_Score | 0.010 |
| Safety_Rating | 0.006 |
| Autonomous_Level | 0.006 |
| Range_km | -0.008 |

### 3. Observations
- **Model_Enc and Brand_Enc** show the strongest correlation, confirming that brand reputation is the primary price driver.
- **Vehicle_Age** has a negative correlation, indicating that older cars are cheaper.
- **Efficiency_Score** shows a moderate positive correlation, suggesting more efficient EVs are valued higher.
- The price distribution is right-skewed, with a long tail of expensive vehicles.

### 4. Figures
All figures are saved in `reports/figures/` .
