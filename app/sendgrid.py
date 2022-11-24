from T1 import settings
import json
import requests


class SendGrid:
    def __init__(self) -> None:
        self.url = "https://api.sendgrid.com/v3/mail/send"
        self.headers = {
            "Content-Type": "application/json",
            "Authorization": f"Bearer {settings.SENDGRID_API_KEY}",
        }
        
    def send_sendgrid_mail(self, payload):
        r = requests.request(
            "POST", url=self.url, data=json.dumps(payload), headers=self.headers
        )
        if not r.status_code in [200,201,202]:
            raise Exception


    def send_email_to_forgot_password_link(self, email, username, forgot_password_link):
        payload = {
            "from": {"email": settings.FROM_EMAIL}, 
            "personalizations": [
                {
                    "to": [{"email": email}],
                    "dynamic_template_data": {
                        "username": username,
                        "forgot_password_link": forgot_password_link,
                    },
                },
            ],
            "template_id": settings.FORGOT_PASSWORD_TEMPLATE_ID, 
        }
        self.send_sendgrid_mail(payload=payload)

    def send_otp_to_email(self,email,otp):
        payload = {
            "from": {"email": settings.FROM_EMAIL}, 
            "personalizations": [
                {
                    "to": [{"email": email}],
                    "dynamic_template_data": {
                        "otp": otp,
                    },
                },
            ],
            "template_id": settings.OTP_TEMPLATE_ID, 
        }
        self.send_sendgrid_mail(payload=payload)


