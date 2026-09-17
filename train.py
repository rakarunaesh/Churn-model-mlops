"""Train churn prediction model"""
import os
import pandas as pd
import pickle
import mlflow
import mlflow.sklearn
from sklearn.model_selection import train_test_split
from sklearn.ensemble import RandomForestClassifier
from sklearn.metrics import accuracy_score, roc_auc_score

mlflow.set_tracking_uri(os.environ.get("MLFLOW_TRACKING_URI", "http://localhost:5000"))
mlflow.set_experiment("churn-model")

# Load feature-engineered data (produced by process_data.py + engineer.py -
# already one-hot encoded, so every non-target column is a feature)
df = pd.read_csv('data/featured_churn_data.csv')

X = df.drop(columns=['Churn'])
y = df['Churn']

# Split (stratify - Churn is imbalanced, ~27% positive)
X_train, X_test, y_train, y_test = train_test_split(
    X, y, test_size=0.2, random_state=42, stratify=y
)

n_estimators = 100
random_state = 42

with mlflow.start_run():
    mlflow.set_tag("git.sha", os.environ.get("GITHUB_SHA", "local"))
    mlflow.log_param("n_estimators", n_estimators)
    mlflow.log_param("random_state", random_state)

    # Train
    model = RandomForestClassifier(n_estimators=n_estimators, random_state=random_state)
    model.fit(X_train, y_train)

    # Evaluate
    y_pred = model.predict(X_test)
    y_proba = model.predict_proba(X_test)[:, 1]

    accuracy = accuracy_score(y_test, y_pred)
    auc = roc_auc_score(y_test, y_proba)

    print(f"Accuracy: {accuracy:.4f}")
    print(f"AUC-ROC: {auc:.4f}")

    mlflow.log_metric("accuracy", accuracy)
    mlflow.log_metric("auc_roc", auc)
    mlflow.sklearn.log_model(model, "model", registered_model_name="churn-predictor")

# Save locally too - this is what gets pushed to S3 for KServe to serve,
# and what the Dockerfile bakes in for standalone/local api.py testing.
with open('models/churn_model.pkl', 'wb') as f:
    pickle.dump(model, f)

print("Model saved to models/churn_model.pkl")
