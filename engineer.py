"""Feature engineering for the Telco Customer Churn dataset."""
import pandas as pd
import logging
from sklearn.compose import ColumnTransformer
from sklearn.preprocessing import OneHotEncoder
from sklearn.pipeline import Pipeline
from sklearn.impute import SimpleImputer
import joblib

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger('feature-engineering')

CATEGORICAL_FEATURES = [
    'gender', 'Partner', 'Dependents', 'PhoneService', 'MultipleLines',
    'InternetService', 'OnlineSecurity', 'OnlineBackup', 'DeviceProtection',
    'TechSupport', 'StreamingTV', 'StreamingMovies', 'Contract',
    'PaperlessBilling', 'PaymentMethod',
]
NUMERICAL_FEATURES = ['SeniorCitizen', 'tenure', 'MonthlyCharges', 'TotalCharges']


def create_preprocessor():
    """Create the preprocessing pipeline (impute + one-hot encode)."""
    numerical_transformer = Pipeline(steps=[
        ('imputer', SimpleImputer(strategy='median'))
    ])

    categorical_transformer = Pipeline(steps=[
        ('onehot', OneHotEncoder(handle_unknown='ignore', sparse_output=False))
    ])

    return ColumnTransformer(transformers=[
        ('num', numerical_transformer, NUMERICAL_FEATURES),
        ('cat', categorical_transformer, CATEGORICAL_FEATURES),
    ])


def run_feature_engineering(input_file, output_file, preprocessor_file):
    """Full feature engineering pipeline."""
    logger.info(f"Loading data from {input_file}")
    df = pd.read_csv(input_file)

    preprocessor = create_preprocessor()
    X = df[NUMERICAL_FEATURES + CATEGORICAL_FEATURES]
    y = df['Churn']

    X_transformed = preprocessor.fit_transform(X)
    logger.info(f"Fitted the preprocessor and transformed the features -> shape {X_transformed.shape}")

    joblib.dump(preprocessor, preprocessor_file)
    logger.info(f"Saved preprocessor to {preprocessor_file}")

    df_transformed = pd.DataFrame(X_transformed)
    df_transformed['Churn'] = y.values
    df_transformed.to_csv(output_file, index=False)
    logger.info(f"Saved fully preprocessed data to {output_file}, shape: {df_transformed.shape}")

    return df_transformed


if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser(description='Feature engineering for Telco churn data.')
    parser.add_argument('--input', required=True, help='Path to cleaned CSV file')
    parser.add_argument('--output', required=True, help='Path for output CSV file (engineered features)')
    parser.add_argument('--preprocessor', required=True, help='Path for saving the preprocessor')

    args = parser.parse_args()

    run_feature_engineering(args.input, args.output, args.preprocessor)
