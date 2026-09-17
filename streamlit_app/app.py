import streamlit as st
import requests
import os
import socket

st.set_page_config(
    page_title="Customer Churn Predictor",
    layout="wide",
    initial_sidebar_state="collapsed"
)

st.title("Customer Churn Prediction")
st.markdown(
    """
    <p style="font-size: 18px; color: gray;">
        A simple MLOps demonstration project for real-time customer churn prediction
    </p>
    """,
    unsafe_allow_html=True,
)

col1, col2 = st.columns(2, gap="large")

with col1:
    st.subheader("Customer Details")

    gender = st.selectbox("Gender", options=["Female", "Male"])
    senior_citizen = st.selectbox("Senior Citizen", options=["No", "Yes"])
    partner = st.selectbox("Has a Partner", options=["No", "Yes"])
    dependents = st.selectbox("Has Dependents", options=["No", "Yes"])
    tenure = st.slider("Tenure (months)", 0, 72, 12)

    st.subheader("Services")

    phone_service = st.selectbox("Phone Service", options=["Yes", "No"])
    if phone_service == "No":
        multiple_lines = "No phone service"
        st.selectbox("Multiple Lines", options=["No phone service"], disabled=True)
    else:
        multiple_lines = st.selectbox("Multiple Lines", options=["No", "Yes"])

    internet_service = st.selectbox("Internet Service", options=["DSL", "Fiber optic", "No"])
    internet_dependent_options = ["No internet service"] if internet_service == "No" else ["No", "Yes"]

    if internet_service == "No":
        online_security = online_backup = device_protection = tech_support = "No internet service"
        streaming_tv = streaming_movies = "No internet service"
        st.caption("Streaming/security add-ons unavailable without internet service")
    else:
        online_security = st.selectbox("Online Security", options=internet_dependent_options)
        online_backup = st.selectbox("Online Backup", options=internet_dependent_options)
        device_protection = st.selectbox("Device Protection", options=internet_dependent_options)
        tech_support = st.selectbox("Tech Support", options=internet_dependent_options)
        streaming_tv = st.selectbox("Streaming TV", options=internet_dependent_options)
        streaming_movies = st.selectbox("Streaming Movies", options=internet_dependent_options)

    st.subheader("Billing")

    contract = st.selectbox("Contract", options=["Month-to-month", "One year", "Two year"])
    paperless_billing = st.selectbox("Paperless Billing", options=["Yes", "No"])
    payment_method = st.selectbox(
        "Payment Method",
        options=["Electronic check", "Mailed check", "Bank transfer (automatic)", "Credit card (automatic)"],
    )
    monthly_charges = st.number_input("Monthly Charges ($)", min_value=0.0, max_value=200.0, value=70.0, step=0.5)
    total_charges = st.number_input(
        "Total Charges ($)", min_value=0.0, max_value=10000.0, value=monthly_charges * tenure, step=1.0
    )

    predict_button = st.button("Predict Churn", use_container_width=True)

with col2:
    st.subheader("Prediction Result")

    if predict_button:
        api_data = {
            "gender": gender,
            "SeniorCitizen": 1 if senior_citizen == "Yes" else 0,
            "Partner": partner,
            "Dependents": dependents,
            "tenure": tenure,
            "PhoneService": phone_service,
            "MultipleLines": multiple_lines,
            "InternetService": internet_service,
            "OnlineSecurity": online_security,
            "OnlineBackup": online_backup,
            "DeviceProtection": device_protection,
            "TechSupport": tech_support,
            "StreamingTV": streaming_tv,
            "StreamingMovies": streaming_movies,
            "Contract": contract,
            "PaperlessBilling": paperless_billing,
            "PaymentMethod": payment_method,
            "MonthlyCharges": monthly_charges,
            "TotalCharges": total_charges,
        }

        with st.spinner("Calculating prediction..."):
            try:
                api_endpoint = os.getenv("API_URL", "http://churn-predictor:8000")
                predict_url = f"{api_endpoint.rstrip('/')}/predict"

                st.caption(f"Connecting to API at: {predict_url}")

                response = requests.post(predict_url, json=api_data, timeout=10)
                response.raise_for_status()
                prediction = response.json()

                st.session_state.prediction = prediction
            except requests.exceptions.RequestException as e:
                st.error(f"Error connecting to API: {e}")
                st.session_state.pop("prediction", None)

    if "prediction" in st.session_state:
        pred = st.session_state.prediction
        will_churn = pred["churn"] == 1
        probability = pred["churn_probability"]

        if will_churn:
            st.markdown(
                f'<div style="background:#fee2e2;padding:24px;border-radius:8px;text-align:center;">'
                f'<span style="font-size:32px;font-weight:700;color:#b91c1c;">Likely to Churn</span></div>',
                unsafe_allow_html=True,
            )
        else:
            st.markdown(
                f'<div style="background:#dcfce7;padding:24px;border-radius:8px;text-align:center;">'
                f'<span style="font-size:32px;font-weight:700;color:#15803d;">Likely to Stay</span></div>',
                unsafe_allow_html=True,
            )

        st.markdown("<br>", unsafe_allow_html=True)
        st.metric("Churn Probability", f"{probability:.1%}")
        st.progress(probability)

        if will_churn:
            st.warning("Consider proactive retention outreach: discount offer, personalized support, or a loyalty check-in.")
    else:
        st.markdown(
            """
            <div style="display: flex; height: 300px; align-items: center; justify-content: center; color: #6b7280; text-align: center;">
                Fill out the form and click "Predict Churn" to see the result.
            </div>
            """,
            unsafe_allow_html=True,
        )

version = os.getenv("APP_VERSION", "1.0.0")
hostname = socket.gethostname()

st.markdown("<hr>", unsafe_allow_html=True)
st.markdown(
    f"""
    <div style="text-align: center; color: gray; margin-top: 20px;">
        <p><strong>Version:</strong> {version} | <strong>Hostname:</strong> {hostname}</p>
    </div>
    """,
    unsafe_allow_html=True,
)
