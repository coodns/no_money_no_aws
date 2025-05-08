# 🚨 AWS Free Tier Alert and Budget Management System

<div align="center">
  <img src="https://img.shields.io/badge/AWS_CDK-v2-orange" alt="AWS CDK v2"/>
  <img src="https://img.shields.io/badge/Python-3.9+-blue" alt="Python 3.9+"/>
  <img src="https://img.shields.io/badge/License-MIT-green" alt="MIT License"/>
</div>

<br>

> **필독** </br>
> if you dont have a permission to create aws budget and etc then you can't use this project as well, and it is not verified that working well, because i dont need to use a freetier :)

<br>

**An infrastructure automation solution that helps you effectively manage your AWS Free Tier period and prevent budget overruns**

## 🌟 Introduction

AWS Free Tier offers various AWS services free of charge within limited usage for 12 months. However, unexpected costs may occur when the Free Tier period ends or when usage exceeds the free limits.

This project uses AWS CDK to solve the following problems:

- Unexpected costs due to missing the Free Tier expiration date
- Costs incurred by creating resources that exceed Free Tier limits
- Difficulty in controlling costs due to lack of budget alerts

<br>

## 🔍 Key Features

### 1️⃣ Free Tier Expiration Alert System
- ⏰ Email notifications 30 days, 7 days, and 1 day before Free Tier expiration
- 📅 Automatic calculation based on account creation date
- 🔄 Daily automatic check (CloudWatch Events + Lambda)

### 2️⃣ Budget Alert Configuration
- 💰 Overall account budget alerts (monthly $10 USD)
- 🧩 Service-specific budget alerts (EC2, S3, RDS)
- 📊 Email notifications when reaching 80% and 100% of budget

### 3️⃣ Free Tier Resource Restriction IAM Policy
- 🛡️ Admin permissions by default, but limited to creating only Free Tier resources
- 🚫 Automatic blocking when attempting to create resources exceeding Free Tier
- 🔗 Policy attachment to existing IAM users

<br>

## 🚀 Installation and Deployment

### Prerequisites
- AWS CLI installed and configured
- Python 3.9 or higher
- AWS CDK installed
- Poetry (optional)

### Installation Steps

#### Method 1: Using Poetry

1. **Clone the repository**
   ```bash
   git clone <repository-url>
   ```

2. **Install dependencies with Poetry**
   ```bash
   poetry install
   ```

3. **Bootstrap CDK with Poetry (first time only)**
   ```bash
   poetry run cdk bootstrap
   ```

4. **Deploy with Poetry**
   ```bash
   poetry run cdk deploy \
     --parameters AccountCreationDate=YYYY-MM-DD \
     --parameters EmailAddress=your-email@example.com \
     --parameters ExistingUserName=username # arn 이 아닌 iam 이름만 꼭 적을것
   ```

#### Method 2: Using Virtual Environment

1. **Clone the repository**
   ```bash
   git clone <repository-url>
   cd no_money_no_gwangju
   ```

2. **Set up virtual environment**
   ```bash
   python -m venv .venv
   source .venv/bin/activate  # Windows: .venv\Scripts\activate
   ```

3. **Install dependencies**
   ```bash
   pip install -r requirements.txt
   ```

4. **Bootstrap CDK (first time only)**
   ```bash
   cdk bootstrap
   ```

5. **Deploy**
   ```bash
   cdk deploy \
     --parameters AccountCreationDate=YYYY-MM-DD \
     --parameters EmailAddress=your-email@example.com \
     --parameters ExistingUserArn=arn:aws:iam::123456789012:user/username
   ```

6. **Destroy (if it need)**
   ```bash
   cdk destroy FreeTierAlertsStack
   ```
<br>

#### How to check my account Creation date ❓

**메일을 찾든지 aws support 문의 하던지 알아서 ㄱㄱ 그것까진 난 모름**


## 📝 Usage

### Post-Deployment Verification

1. **Email Subscription Confirmation**
   - You will receive an SNS topic subscription confirmation email.
   - Click the confirmation link in the email to activate alert notifications.

2. **IAM Policy Verification**
   - Check "FreeTierAdminPolicy" in AWS Console under IAM > Policies
   - Verify that the policy is correctly attached to the specified user

3. **Budget Alert Verification**
   - Check the created budgets in AWS Console under Billing > Budgets

<br>

## ⚙️ Customization

### Adjusting Budget Limits
Modify the following values in the `app.py` file:
```python
# Change overall budget limit
budget_limit=budgets.CfnBudget.SpendProperty(
    amount=10,  # Change to desired amount
    unit="USD"
)

# Change service-specific budget limit
budget_limit=budgets.CfnBudget.SpendProperty(
    amount=1,  # Change to desired amount
    unit="USD"
)
```

### Adjusting Alert Thresholds
```python
notification=budgets.CfnBudget.NotificationProperty(
    comparison_operator="GREATER_THAN",
    notification_type="ACTUAL",
    threshold=80,  # Change to desired threshold (e.g., 50, 75, 90)
    threshold_type="PERCENTAGE"
)
```

### Modifying Free Tier Restriction Policy
Add or modify service and resource restrictions in the IAM policy statements as needed.

<br>

## ⚠️ Important Notes

- **Email Subscription Confirmation**: You must confirm the SNS topic subscription email after deployment for alerts to work.
- **Budget Alert Delay**: AWS budget alerts may be delayed by up to several hours after actual costs are incurred.
- **Account Creation Date Accuracy**: For Free Tier expiration alerts to work correctly, you must enter the exact account creation date.
- **IAM Permissions**: Appropriate permissions are required for the user to whom the policy will be attached.
- **If your free tier approvements are ends, please delete this cloudformation stack and delete all the related resources**
<br>

---

<div align="center">
  <p>Made ⭐ with for coodns</p>
  <p>© 2024 coodns</p>
</div>
