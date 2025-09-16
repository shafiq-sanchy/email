import streamlit as st
import smtplib, ssl, json, time, os
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from itertools import cycle
import pandas as pd

# ==========================
# Load SMTP Accounts
# ==========================
def load_smtp_accounts():
    if os.path.exists("smtp_accounts.json"):
        with open("smtp_accounts.json", "r") as f:
            return json.load(f)
    return []

smtp_accounts = load_smtp_accounts()
smtp_cycle = cycle(smtp_accounts) if smtp_accounts else None

# ==========================
# Streamlit UI
# ==========================
st.set_page_config(page_title="Bulk Email Sender", layout="centered")
st.title("Sender (Mailjet + Brevo)")

# Upload or paste recipients
option = st.radio("📋 Add Recipients", ["Paste Emails", "Upload CSV/Excel"])
recipients = []

if option == "Paste Emails":
    emails_text = st.text_area("Paste emails (one per line)", height=150)
    recipients = [e.strip() for e in emails_text.splitlines() if e.strip()]
else:
    file = st.file_uploader("Upload CSV/Excel with 'email' column", type=["csv", "xlsx"])
    if file:
        if file.name.endswith(".csv"):
            df = pd.read_csv(file)
        else:
            df = pd.read_excel(file)
        if "email" in df.columns:
            recipients = df["email"].dropna().tolist()
        else:
            st.error("CSV/Excel must have an 'email' column.")

# Email details
sender_name = st.text_input("👤 Sender Name", value="Your Name")
subject = st.text_input("✉️ Email Subject")
body = st.text_area("📝 Email Body (HTML allowed)", height=200)

# Send emails
if st.button("🚀 Send Emails"):
    if not smtp_accounts:
        st.error("⚠️ No SMTP accounts configured! Add them in smtp_accounts.json.")
    elif not recipients:
        st.error("⚠️ No recipients found.")
    elif not subject or not body:
        st.error("⚠️ Subject and body required.")
    else:
        st.info(f"Starting to send {len(recipients)} emails...")
        progress = st.progress(0)
        sent_count = 0

        for i, recipient in enumerate(recipients):
            smtp = next(smtp_cycle)  # rotate accounts
            try:
                msg = MIMEMultipart()
                msg["From"] = f"{sender_name} <{smtp['email']}>"
                msg["To"] = recipient
                msg["Subject"] = subject
                msg.attach(MIMEText(body, "html"))

                context = ssl.create_default_context()
                with smtplib.SMTP(smtp["server"], smtp["port"]) as server:
                    server.starttls(context=context)
                    server.login(smtp["email"], smtp["password"])
                    server.sendmail(smtp["email"], recipient, msg.as_string())

                sent_count += 1
            except Exception as e:
                st.error(f"❌ Failed to send to {recipient} via {smtp['email']} : {e}")

            progress.progress((i + 1) / len(recipients))
            time.sleep(0.5)  # throttle a bit

        st.success(f"✅ Sent {sent_count}/{len(recipients)} emails successfully!")
