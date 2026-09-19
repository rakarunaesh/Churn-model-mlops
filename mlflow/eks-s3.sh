#!/bin/bash

set -euo pipefail

# Disable AWS CLI pager
export AWS_PAGER=""

# ==========================================
# Configuration
# ==========================================
ACTION="${1:-create}"

REGION="us-west-2"
CLUSTER_NAME="you-cluster-name"
BUCKET_NAME="your-bucket-name"

POLICY_NAME="mlflow-s3-policy"
ROLE_NAME="mlflow-pod-identity-role"

NAMESPACE="mlflow"
SERVICE_ACCOUNT="mlflow-mlflow"

ACCOUNT_ID=$(aws sts get-caller-identity --query Account --output text)

POLICY_ARN="arn:aws:iam::${ACCOUNT_ID}:policy/${POLICY_NAME}"
ROLE_ARN="arn:aws:iam::${ACCOUNT_ID}:role/${ROLE_NAME}"

echo "AWS Account ID: ${ACCOUNT_ID}"
echo "Action: ${ACTION}"

# ==========================================================
# Cleanup
# ==========================================================
if [[ "${ACTION}" == "cleanup" ]]; then

echo
echo "=========================================="
echo "Deleting Pod Identity Association"
echo "=========================================="

ASSOCIATION_ID=$(aws eks list-pod-identity-associations \
  --cluster-name "${CLUSTER_NAME}" \
  --namespace "${NAMESPACE}" \
  --region "${REGION}" \
  --query "associations[?serviceAccount=='${SERVICE_ACCOUNT}'].associationId" \
  --output text)

if [[ -n "${ASSOCIATION_ID}" && "${ASSOCIATION_ID}" != "None" ]]; then
    aws eks delete-pod-identity-association \
        --cluster-name "${CLUSTER_NAME}" \
        --association-id "${ASSOCIATION_ID}" \
        --region "${REGION}"

    echo "Deleted Pod Identity Association."
else
    echo "No Pod Identity Association found."
fi

echo
echo "=========================================="
echo "Detaching IAM Policy"
echo "=========================================="

aws iam detach-role-policy \
    --role-name "${ROLE_NAME}" \
    --policy-arn "${POLICY_ARN}" \
    || true

echo
echo "=========================================="
echo "Deleting IAM Role"
echo "=========================================="

aws iam delete-role \
    --role-name "${ROLE_NAME}" \
    || true

echo
echo "=========================================="
echo "Deleting IAM Policy"
echo "=========================================="

aws iam delete-policy \
    --policy-arn "${POLICY_ARN}" \
    || true

echo
echo "=========================================="
echo "Cleanup Complete"
echo "=========================================="
echo "Note: S3 bucket '${BUCKET_NAME}' was NOT deleted."

exit 0
fi

# ==========================================================
# Create
# ==========================================================

echo
echo "=========================================="
echo "Creating IAM Policy"
echo "=========================================="

POLICY_ARN=$(aws iam create-policy \
  --policy-name "${POLICY_NAME}" \
  --policy-document "{
    \"Version\": \"2012-10-17\",
    \"Statement\": [
      {
        \"Effect\": \"Allow\",
        \"Action\": [
          \"s3:GetObject\",
          \"s3:PutObject\",
          \"s3:DeleteObject\",
          \"s3:ListBucket\"
        ],
        \"Resource\": [
          \"arn:aws:s3:::${BUCKET_NAME}\",
          \"arn:aws:s3:::${BUCKET_NAME}/*\"
        ]
      }
    ]
  }" \
  --query 'Policy.Arn' \
  --output text)

echo "Created Policy:"
echo "${POLICY_ARN}"

echo
echo "=========================================="
echo "Creating IAM Role"
echo "=========================================="

aws iam create-role \
  --role-name "${ROLE_NAME}" \
  --assume-role-policy-document '{
    "Version": "2012-10-17",
    "Statement": [
      {
        "Effect": "Allow",
        "Principal": {
          "Service": "pods.eks.amazonaws.com"
        },
        "Action": [
          "sts:AssumeRole",
          "sts:TagSession"
        ]
      }
    ]
  }'

echo "Created Role:"
echo "${ROLE_ARN}"

echo
echo "=========================================="
echo "Attaching IAM Policy"
echo "=========================================="

aws iam attach-role-policy \
    --role-name "${ROLE_NAME}" \
    --policy-arn "${POLICY_ARN}"

echo "Policy attached."

echo
echo "=========================================="
echo "Creating Pod Identity Association"
echo "=========================================="

aws eks create-pod-identity-association \
    --cluster-name "${CLUSTER_NAME}" \
    --namespace "${NAMESPACE}" \
    --service-account "${SERVICE_ACCOUNT}" \
    --role-arn "${ROLE_ARN}" \
    --region "${REGION}"

echo
echo "=========================================="
echo "Verifying Association"
echo "=========================================="

aws eks list-pod-identity-associations \
    --cluster-name "${CLUSTER_NAME}" \
    --namespace "${NAMESPACE}" \
    --region "${REGION}"

echo
echo "=========================================="
echo "Setup Complete"
echo "=========================================="

echo "Bucket          : ${BUCKET_NAME}"
echo "Cluster         : ${CLUSTER_NAME}"
echo "Namespace       : ${NAMESPACE}"
echo "ServiceAccount  : ${SERVICE_ACCOUNT}"
echo "Policy ARN      : ${POLICY_ARN}"
echo "Role ARN        : ${ROLE_ARN}"