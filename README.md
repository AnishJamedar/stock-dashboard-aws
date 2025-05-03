# 📊 AWS Stock Dashboard

A cloud-native stock market analytics dashboard built with **AWS Athena**, **S3**, **Lambda**, **Step Functions**, and **Streamlit**. This project allows users to visualize historical stock data, trigger custom one-time queries, and explore insights—all deployed and running in the AWS Cloud.

---

## 🌐 Live Demo
Accessible via URL (`stock-dashboard.anishjamedar.com`).

---

## 🛠️ Architecture Overview

- **EventBridge** triggers daily stock fetches.
- **Step Function 1** invokes a Lambda with a Map state to fetch data from Alpha Vantage for predefined stocks (`AAPL`, `TSLA`, `GOOGL`, `NVDA`).
- **Lambda Function 1** writes raw stock data into partitioned S3 folders (`raw/symbol=XYZ/date=.../`).
- **S3 Event Notification** triggers **Lambda 2** to clean and transform the data, storing output in `clean/` partitioned folders.
- **Step Function 2** runs `MSCK REPAIR TABLE` query in Athena daily at 8:30 AM.
- **Athena** queries cleaned data stored in S3 and stores results in `athena-results/`.
- **Streamlit App** on EC2 connects to Athena to render analytics.
- **Lifecycle Rules**: Raw data deleted after 30 days, Athena results deleted after 10 days.

---

## 🔧 Features

- 📈 Prebuilt dashboard for 4 stocks (AAPL, TSLA, GOOGL, NVDA)
- 🔍 Custom stock support via Lambda trigger
- 🧹 Data cleaning and partitioning via Lambda + Step Functions
- 🗓️ Daily market updates at 8 AM ET
- 📦 Clean and modular code structure

---

## 🧱 Tech Stack
ads
- **Frontend**: Streamlit (hosted on EC2)
- **Backend & Infra**:
  - AWS Lambda
  - AWS Step Functions
  - Amazon S3
  - AWS Athena
  - Amazon EventBridge
- **Data Source**: [Alpha Vantage API](https://www.alphavantage.co)
- **Language**: Python 3.10+

---

## 📁 Project Structure

```
├── main.py                  # Streamlit frontend
├── lambda/                # AWS Lambda source codes
│   └── lambda1.py     # Lambda 1 (Fetch from API)
│   └── lambda2.py      # Lambda 2 (Clean & store to clean/)
│   └── lambda3.py      # Lambda 3 (Fetch the custom stock data)
├── diagrams/              # Architecture visuals
├── requirements.txt       # Python dependencies
└── README.md              # This file
```

---

## ⚙️ Setup Instructions

### 1. Deploy AWS Resources
Use CloudFormation or manual setup to:
- Create two Step Functions
- Add Lambda functions
- Configure S3 notifications
- Create Athena table with partitions (symbol, date)
- Add lifecycle rules to `raw/` and `athena-results/`

### 2. Streamlit Setup
```bash
pip install -r requirements.txt
streamlit run main.py
```

### 3. Environment Variables
Ensure the following are configured:
- `ALPHA_VANTAGE_KEY`
- `S3_BUCKET_NAME`

---

## 📸 Screenshots
![image](https://github.com/user-attachments/assets/675a0059-3b72-4d90-b3af-40a47a8c923e)
![image](https://github.com/user-attachments/assets/ea0dc862-f23a-48f5-bd38-93ca2732f683)
![image](https://github.com/user-attachments/assets/56060f80-8446-4cff-a67e-66c293ed8140)
![image](https://github.com/user-attachments/assets/63ce6b3c-0319-4d80-942c-d3c9355417f4)



---

## 💡 Future Enhancements

- Enable Auto Scaling Groups (ASG) if continuing with EC2 to handle fluctuating traffic.
- Use Amazon SQS or SNS to decouple Lambda invocations for better reliability and fault tolerance.
- Introduce API Gateway + Lambda for secure and structured stock symbol submission.
- Leverage AWS Glue DataBrew or Glue Jobs for more complex data transformations on raw data.
- Store cleaned data in AWS Redshift or TimeStream for high-performance analytics.
- Add Cognito-based authentication for personalized user dashboards and access control.
- Integrate QuickSight for enhanced, shareable BI-style dashboards.
- Cost optimization via intelligent lifecycle policies, object compression, and request tracking with CloudWatch Metrics.



---

## 📜 License
MIT License.

---

## 🙌 Acknowledgments
- Alpha Vantage for API data
- AWS for generous free-tier services
- Streamlit community for rapid prototyping tools

---

## 📬 Connect
If you liked this project, feel free to [connect on LinkedIn](https://linkedin.com/in/anishjamedar/) or give it a ⭐️ on GitHub!
