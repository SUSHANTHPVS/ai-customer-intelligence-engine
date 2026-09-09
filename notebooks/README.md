# Notebooks

Jupyter notebooks for exploratory data analysis and model development.

## Notebook Index

### 01_EDA.ipynb
**Exploratory Data Analysis**
- Data loading and overview
- Missing values analysis
- Distribution analysis
- Correlation analysis
- Basic customer segmentation insights

### 02_Cohort_Analysis.ipynb
**Cohort & Retention Analysis**
- Cohort analysis by signup month
- Retention curves
- Month-over-month retention rates
- Identify patterns in customer retention

### 03_Segmentation.ipynb
**Customer Segmentation**
- RFM (Recency, Frequency, Monetary) analysis
- K-Means clustering
- Behavioral segmentation
- Segment profiling and characterization

### 04_Churn_Model.ipynb
**Churn Prediction Modeling**
- Feature engineering for churn prediction
- Model training (Logistic Regression, Random Forest, XGBoost, LightGBM)
- Model evaluation and comparison
- Hyperparameter tuning
- Cross-validation

### 05_SHAP_Analysis.ipynb
**Model Explainability**
- SHAP values computation
- Feature importance analysis
- Local explanations (why did model predict churn for customer X?)
- Global explainability
- SHAP plots and visualizations

### 06_Revenue_Risk.ipynb
**Revenue-at-Risk Engine**
- Customer Lifetime Value (LTV) calculation
- Churn probability × LTV = Revenue at Risk
- Customer risk ranking
- Portfolio risk assessment
- Intervention ROI estimation

## Running Notebooks

```bash
# Activate virtual environment
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Start Jupyter Lab
jupyter lab

# Or use VSCode's Jupyter extension
# Open .ipynb file and run cells
```

## Best Practices

1. **Cell Organization**: Group related cells with markdown headers
2. **Documentation**: Use markdown cells to explain code and findings
3. **Reproducibility**: Always include data loading and seed setting
4. **Visualization**: Include plots for all key findings
5. **Version Control**: Commit notebooks with executed cells
6. **Performance**: Use smaller datasets for iteration, full dataset for final runs

## From Notebook to Production

Insights from notebooks should be:
1. Documented in `docs/` as markdown
2. Implemented in `src/` as reusable Python modules
3. Packaged in `api/` for FastAPI endpoints
4. Visualized in `dashboard/` for BI tools
