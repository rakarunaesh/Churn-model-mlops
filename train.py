"""Train churn prediction model"""
import os
import pandas as pd
import pickle
import mlflow
import mlflow.xgboost
from sklearn.model_selection import train_test_split, RandomizedSearchCV
from xgboost import XGBClassifier
from sklearn.metrics import accuracy_score, roc_auc_score

mlflow.set_tracking_uri(os.environ.get("MLFLOW_TRACKING_URI", "http://localhost:5000"))
mlflow.set_experiment("churn-model")

# Load feature-engineered data (produced by process_data.py + engineer.py -
# already one-hot encoded, so every non-target column is a feature)
df = pd.read_csv('data/processed/featured_churn_data.csv')

X = df.drop(columns=['Churn'])
y = df['Churn']

# Split (stratify - Churn is imbalanced, ~27% positive)
X_train, X_test, y_train, y_test = train_test_split(
    X, y, test_size=0.2, random_state=42, stratify=y
)

random_state = 42

# Churn is ~27% positive - tell XGBoost to weight the minority class instead
# of optimizing for raw accuracy, which a naive model can game by always
# predicting "no churn".
scale_pos_weight = (y_train == 0).sum() / (y_train == 1).sum()

param_distributions = {
    "n_estimators": [100, 200, 300, 400],
    "max_depth": [3, 4, 5, 6, 7],
    "learning_rate": [0.01, 0.05, 0.1, 0.2],
    "subsample": [0.7, 0.8, 0.9, 1.0],
    "colsample_bytree": [0.7, 0.8, 0.9, 1.0],
    "min_child_weight": [1, 3, 5],
}

with mlflow.start_run():
    mlflow.set_tag("git.sha", os.environ.get("GITHUB_SHA", "local"))
    mlflow.log_param("scale_pos_weight", scale_pos_weight)

    search = RandomizedSearchCV(
        XGBClassifier(
            random_state=random_state,
            scale_pos_weight=scale_pos_weight,
            eval_metric="logloss",
        ),
        param_distributions=param_distributions,
        n_iter=20,
        scoring="roc_auc",
        cv=5,
        random_state=random_state,
        n_jobs=-1,
    )
    search.fit(X_train, y_train)
    model = search.best_estimator_

    mlflow.log_params(search.best_params_)
    mlflow.log_metric("cv_best_auc_roc", search.best_score_)

    # Evaluate
    y_pred = model.predict(X_test)
    y_proba = model.predict_proba(X_test)[:, 1]

    accuracy = accuracy_score(y_test, y_pred)
    auc = roc_auc_score(y_test, y_proba)

    print(f"Best params: {search.best_params_}")
    print(f"CV best AUC-ROC: {search.best_score_:.4f}")
    print(f"Accuracy: {accuracy:.4f}")
    print(f"AUC-ROC: {auc:.4f}")

    mlflow.log_metric("accuracy", accuracy)
    mlflow.log_metric("auc_roc", auc)
    mlflow.xgboost.log_model(model, "model", registered_model_name="churn-predictor")

# Save locally too - this is what gets pushed to S3 for KServe to serve,
# and what the Dockerfile bakes in for standalone/local api.py testing.
os.makedirs('models/trained', exist_ok=True)
with open('models/trained/churn_model.pkl', 'wb') as f:
    pickle.dump(model, f)

print("Model saved to models/trained/churn_model.pkl")
