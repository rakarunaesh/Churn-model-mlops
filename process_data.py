"""Clean the raw Telco Customer Churn dataset."""
import pandas as pd
from pathlib import Path
import logging

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger('data-processor')


def clean_data(df):
    """Clean the raw Telco Customer Churn dataset."""
    df_cleaned = df.copy()

    # customerID is an identifier, not a feature
    df_cleaned = df_cleaned.drop(columns=['customerID'], errors='ignore')

    # TotalCharges is stored as text and has 11 blank values, all belonging to
    # customers with tenure == 0 (brand new, not billed yet) - 0 is the
    # domain-correct fill here, not the column median.
    df_cleaned['TotalCharges'] = pd.to_numeric(df_cleaned['TotalCharges'], errors='coerce')
    missing_charges = df_cleaned['TotalCharges'].isnull().sum()
    if missing_charges > 0:
        logger.info(f"Filling {missing_charges} blank TotalCharges values with 0 (tenure=0 customers)")
        df_cleaned['TotalCharges'] = df_cleaned['TotalCharges'].fillna(0)

    # Target: Yes/No -> 1/0
    df_cleaned['Churn'] = df_cleaned['Churn'].map({'Yes': 1, 'No': 0})

    return df_cleaned


def process_data(input_file, output_file):
    """Full data processing pipeline."""
    output_path = Path(output_file).parent
    output_path.mkdir(parents=True, exist_ok=True)

    logger.info(f"Loading data from {input_file}")
    df = pd.read_csv(input_file)
    logger.info(f"Loaded data with shape: {df.shape}")

    df_cleaned = clean_data(df)

    df_cleaned.to_csv(output_file, index=False)
    logger.info(f"Saved processed data to {output_file}, shape: {df_cleaned.shape}")

    return df_cleaned


if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser(description="Data processing for Telco churn data.")
    parser.add_argument("--input", required=True, help="Path to raw CSV file")
    parser.add_argument("--output", required=True, help="Path for output cleaned CSV file")

    args = parser.parse_args()

    process_data(input_file=args.input, output_file=args.output)
