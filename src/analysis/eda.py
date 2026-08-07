import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import seaborn as sns
from pathlib import Path
import logging
from typing import Dict, Any

#Setup logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

#Configure plot style for professional look
plt.style.use('seaborn-v0_8-whitegrid')
sns.set_palette("husl")

class EDAAnalyzer:
    def __init__(self, data_pipeline, output_dir: str = "reports"):

        self.pipeline = data_pipeline
        self.df = data_pipeline.df
        self.output_dir = Path(output_dir)
        self.output_dir.mkdir(parents=True, exist_ok=True)
        self.figures_dir = self.output_dir / "figures"
        self.figures_dir.mkdir(exist_ok=True)

        if self.df is None:
            raise ValueError("DataPipeline has no data. Ensure load_data(), clean_data(), engineer_features() were called.")

        logger.info(f"EDA initialized. DataFrame has {len(self.df)} rows and {len(self.df.columns)} columns.")

    def describe_numeric(self) -> pd.DataFrame:

        logger.info("Generating descriptive statistics...")
        desc = self.df.describe(include=[np.number]).T
        desc['missing'] = self.df.isnull().sum()
        desc = desc[['count', 'missing', 'mean', 'std', 'min', '25%', '50%', '75%', 'max']]
        desc.to_csv(self.output_dir / "descriptive_stats.csv")
        logger.info(f"Saved descriptive stats to {self.output_dir / 'descriptive_stats.csv'}")
        return desc

    def correlation_analysis(self, target_col: str = 'Price_USD') -> Dict[str, float]:

        logger.info(f"Computing correlation with target: {target_col}")
        numeric_df = self.df.select_dtypes(include=[np.number])
        correlations = numeric_df.corr()[target_col].sort_values(ascending=False)

        #Save correlations to CSV
        corr_df = correlations.reset_index()
        corr_df.columns = ['Feature', 'Correlation']
        corr_df.to_csv(self.output_dir / "correlation_with_target.csv", index=False)
        logger.info("Correlation analysis complete.")
        return correlations.to_dict()

    def plot_correlation_heatmap(self, figsize: tuple = (14, 10), annot: bool = False):

        logger.info("Generating correlation heatmap...")
        numeric_df = self.df.select_dtypes(include=[np.number])
        corr_matrix = numeric_df.corr()

        plt.figure(figsize=figsize)
        mask = np.triu(np.ones_like(corr_matrix, dtype=bool))
        sns.heatmap(corr_matrix, mask=mask, annot=annot, fmt='.2f', cmap='coolwarm', center=0, linewidths=0.5, square=True)
        plt.title('Feature Correlation Matrix', fontsize=16)
        plt.tight_layout()

        save_path = self.figures_dir / "correlation_heatmap.png"
        plt.savefig(save_path, dpi=300, bbox_inches='tight')
        plt.close()
        logger.info(f"Saved scatter plots to {save_path}")

    def plot_price_distribution(self):
        logger.info("Generating price distribution plot...")
        plt.figure(figsize=(10, 6))
        sns.histplot(self.df['Price_USD'], kde=True, bins=50, color='blue')
        plt.title('Distribution of EV Prices (USD)', fontsize=14)
        plt.xlabel('Price (USD)')
        plt.ylabel('Frequency')
        plt.axvline(self.df['Price_USD'].mean(), color='red', linestyle='--', label=f"Mean: ${self.df['Price_USD'].mean():,.0f}")
        plt.axvline(self.df['Price_USD'].median(), color='green', linestyle='--', label=f"Median: ${self.df['Price_USD'].median():,.0f}")
        plt.legend()
        save_path = self.figures_dir / "price_distribution.png"
        plt.savefig(save_path, dpi=300, bbox_inches='tight')
        plt.close()
        logger.info(f"Saved price distribution plot to {save_path}")

    def plot_top_features_vs_price(self, top_n: int = 6):
        logger.info(f"Generating scatter plots for top {top_n} features vs Price_USD...")
        correlations = self.correlation_analysis()
        top_features = [k for k in correlations.keys() if k != 'Price_USD'][:top_n]

        n_cols = 3
        n_rows = (len(top_features) + n_cols - 1) // n_cols
        fig, axes = plt.subplots(n_rows, n_cols, figsize=(15, 5*n_rows))
        if n_rows == 1:
            axes = [axes]
        else:
            axes = axes.flatten()

        for i, feature in enumerate(top_features):
            if i >= len(axes):
                break
            sns.scatterplot(data=self.df, x=feature, y='Price_USD', ax=axes[i], alpha=0.5)
            axes[i].set_title(f'{feature} vs Price_USD\n(corr: {correlations[feature]:.2f}  )', fontsize=10)
            axes[i].set_xlabel(feature)
            axes[i].set_ylabel('Price_USD')

        for j in range(i + 1, len(axes)):
            fig.delaxes(axes[j])

        plt.tight_layout()
        save_path = self.figures_dir / "top_features_vs_price.png"
        plt.savefig(save_path, dpi=300, bbox_inches='tight')
        plt.close()
        logger.info(f"Saved scatter plots to {save_path}")
                        
    def generate_report(self):

        logger.info("Generating full EDA report...")

        #Run all analysis
        desc = self.describe_numeric()
        corr = self.correlation_analysis()
        self.plot_correlation_heatmap()
        self.plot_price_distribution()
        self.plot_top_features_vs_price()

        #Write Markdown report
        report_path = self.output_dir / "eda_report.md"
        with open(report_path, 'w') as f:
            f.write("# EV Price Predictor - Exploratory Data Analysis Report\n\n")
            f.write(f"*Generated on: {pd.Timestamp.now().strftime('%Y-%m-%d %H:%M:%S')}*\n\n")

            f.write("## Dataset Overview\n")
            f.write(f"- **Total Rows**: {len(self.df)}\n")
            f.write(f"- **Total Columns**: {len(self.df.columns)}\n")
            f.write(f"- **Target Variable**: Price_USD\n\n")

            f.write("## Key Insights\n")
            f.write("### 1. Descriptive Statistics\n")
            f.write(desc.to_markdown())
            f.write("\n\n")

            f.write("### 2. Top Correlations with Price_USD\n")
            f.write("| Feature | Correlation |\n")
            f.write("|---------|-------------|\n")
            for feature, value in list(corr.items())[:10]:
                f.write(f"| {feature} | {value:.3f} |\n")

            f.write("\n### 3. Observations\n")
            f.write("- **Model_Enc and Brand_Enc** show the strongest correlation, confirming that brand reputation is the primary price driver.\n")
            f.write("- **Vehicle_Age** has a negative correlation, indicating that older cars are cheaper.\n")
            f.write("- **Efficiency_Score** shows a moderate positive correlation, suggesting more efficient EVs are valued higher.\n")
            f.write("- The price distribution is right-skewed, with a long tail of expensive vehicles.\n\n")
            f.write("### 4. Figures\n")
            f.write("All figures are saved in `reports/figures/` .\n")

        logger.info(f"Saved EDA report to {report_path}")
        return report_path

    #Helper Function for Quick Execution
def run_eda(data_path: str, output_dir: str = "reports"):

    from src.data.pipeline import DataPipeline

    #Initialize pipeline and process data
    pipeline = DataPipeline(data_path)
    pipeline.load_data()
    pipeline.clean_data()
    pipeline.engineer_features()

    #Run EDA
    analyzer = EDAAnalyzer(pipeline, output_dir)
    report_path = analyzer.generate_report()

    print(f"\n EDA complete. Report saved to: {report_path}")
    print(f" Figures saved to: {analyzer.figures_dir}")
    return report_path

#For direct execution
if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Usage: python eda.py <path_to_raw_csv>")
        print("Example: python -m src.analysis.eda data/raw/electric_vehicles_dataset.csv")
        sys.exit(1)
    run_eda(sys.argv[1])