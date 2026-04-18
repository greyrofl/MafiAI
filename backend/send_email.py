import smtplib
import random
import string
from email.message import EmailMessage

SMTP_SERVER = "smtp.gmail.com"
SMTP_PORT = 587
SENDER_EMAIL = "arturgiliazov2012@gmail.com"
APP_PASSWORD = "qkhviefgnikmlwmc"


def generate_code(length=6):
    return ''.join(random.choices(string.digits, k=length))


def send_verification_code(recipient_email: str, code: str):
    subject = "Verification code MafiaChat"
    
    text_content = f"Your verification code: {code}"
    
    html_content = f"""<!DOCTYPE html>
<html>
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <style>
        @keyframes gradient {{
            0% {{ background-position: 0% 50%; }}
            50% {{ background-position: 100% 50%; }}
            100% {{ background-position: 0% 50%; }}
        }}
    </style>
</head>
<body style="margin: 0; padding: 0; background: linear-gradient(-45deg, #8b0000, #000000, #8b0000, #000000); background-size: 400% 400%; animation: gradient 3s ease infinite; font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;">
    <table role="presentation" width="100%" cellspacing="0" cellpadding="0" border="0">
        <tr>
            <td align="center" style="padding: 50px 20px;">
                <table role="presentation" width="100%" max-width="500" cellspacing="0" cellpadding="0" border="0" style="background: #ffffff; border-radius: 20px; box-shadow: 0 20px 60px rgba(0,0,0,0.3); overflow: hidden;">
                    <tr>
                        <td style="background: linear-gradient(135deg, #8b0000 0%, #000000 100%); padding: 40px 30px; text-align: center;">
                            <h1 style="margin: 0; color: #ffffff; font-size: 28px; font-weight: 700; text-shadow: 2px 2px 4px rgba(0,0,0,0.2);">MafiaChat</h1>
                            <p style="margin: 10px 0 0 0; color: rgba(255,255,255,0.9); font-size: 14px;">Online Mafia Game</p>
                        </td>
                    </tr>
                    <tr>
                        <td style="padding: 40px 30px; text-align: center;">
                            <h2 style="margin: 0 0 20px 0; color: #333333; font-size: 24px; font-weight: 600;">Email Verification</h2>
                            <p style="margin: 0 0 30px 0; color: #666666; font-size: 16px; line-height: 1.6;">Hello!<br>Enter this code to complete your registration:</p>
                            <div style="background: linear-gradient(135deg, #f5f7fa 0%, #e4e8ec 100%); border-radius: 15px; padding: 25px 40px; display: inline-block; margin: 20px 0; border: 2px solid #8b0000;">
                                <span style="font-family: 'Courier New', monospace; font-size: 36px; font-weight: 800; color: #8b0000; letter-spacing: 8px; text-shadow: 2px 2px 4px rgba(139,0,0,0.3);">{code}</span>
                            </div>
                            <p style="margin: 30px 0 0 0; color: #888888; font-size: 13px; line-height: 1.6;">
                                This code expires in <strong>10 minutes</strong>.<br>
                                If you didn't request this, please ignore this email.
                            </p>
                        </td>
                    </tr>
                    <tr>
                        <td style="background: #f8f9fa; padding: 25px 30px; text-align: center; border-top: 1px solid #eeeeee;">
                            <p style="margin: 0; color: #999999; font-size: 12px;">MafiaChat &copy; 2026. All rights reserved.</p>
                        </td>
                    </tr>
                </table>
            </td>
        </tr>
    </table>
</body>
</html>"""

    message = EmailMessage()
    message["From"] = SENDER_EMAIL
    message["To"] = recipient_email
    message["Subject"] = subject
    message.set_content(text_content, subtype="plain", charset="utf-8")
    message.add_alternative(html_content, subtype="html", charset="utf-8")
    
    try:
        server = smtplib.SMTP(SMTP_SERVER, SMTP_PORT)
        server.starttls()
        server.login(SENDER_EMAIL, APP_PASSWORD)
        server.send_message(message)
        server.quit()
        print(f"SUCCESS: Email sent to {recipient_email}")
        return True
    except Exception as e:
        print(f"EMAIL ERROR: {e}")
        return False


def send_welcome_email(recipient_email: str, username: str = ""):
    name = username or "friend"
    subject = "Welcome to MafiaChat!"
    
    text_content = f"Welcome, {name}! You have successfully registered on MafiaChat."
    
    html_content = f"""<!DOCTYPE html>
<html>
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <style>
        @keyframes gradient {{
            0% {{ background-position: 0% 50%; }}
            50% {{ background-position: 100% 50%; }}
            100% {{ background-position: 0% 50%; }}
        }}
    </style>
</head>
<body style="margin: 0; padding: 0; background: linear-gradient(-45deg, #8b0000, #000000, #8b0000, #000000); background-size: 400% 400%; animation: gradient 3s ease infinite; font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;">
    <table role="presentation" width="100%" cellspacing="0" cellpadding="0" border="0">
        <tr>
            <td align="center" style="padding: 50px 20px;">
                <table role="presentation" width="100%" max-width="500" cellspacing="0" cellpadding="0" border="0" style="background: #ffffff; border-radius: 20px; box-shadow: 0 20px 60px rgba(0,0,0,0.3); overflow: hidden;">
                    <tr>
                        <td style="background: linear-gradient(135deg, #8b0000 0%, #000000 100%); padding: 40px 30px; text-align: center;">
                            <h1 style="margin: 0; color: #ffffff; font-size: 28px; font-weight: 700; text-shadow: 2px 2px 4px rgba(0,0,0,0.2);">MafiaChat</h1>
                            <p style="margin: 10px 0 0 0; color: rgba(255,255,255,0.9); font-size: 14px;">Online Mafia Game</p>
                        </td>
                    </tr>
                    <tr>
                        <td style="padding: 40px 30px; text-align: center;">
                            <div style="width: 80px; height: 80px; background: linear-gradient(135deg, #4CAF50, #45a049); border-radius: 50%; display: inline-block; margin-bottom: 20px; line-height: 80px;">
                                <span style="color: white; font-size: 40px;">&#10003;</span>
                            </div>
                            <h2 style="margin: 0 0 15px 0; color: #333333; font-size: 24px; font-weight: 600;">Welcome, {name}!</h2>
                            <p style="margin: 0 0 30px 0; color: #666666; font-size: 16px; line-height: 1.6;">
                                You have successfully registered on <strong>MafiaChat</strong> — the online mafia game platform.
                            </p>
                            <a href="#" style="display: inline-block; padding: 15px 40px; background: linear-gradient(135deg, #8b0000 0%, #000000 100%); color: #ffffff; text-decoration: none; border-radius: 30px; font-weight: 600; font-size: 16px; margin-top: 20px; box-shadow: 0 4px 15px rgba(139,0,0,0.4);">Play Now</a>
                        </td>
                    </tr>
                    <tr>
                        <td style="background: #f8f9fa; padding: 25px 30px; text-align: center; border-top: 1px solid #eeeeee;">
                            <p style="margin: 0; color: #999999; font-size: 12px;">MafiaChat &copy; 2026. All rights reserved.</p>
                        </td>
                    </tr>
                </table>
            </td>
        </tr>
    </table>
</body>
</html>"""

    message = EmailMessage()
    message["From"] = SENDER_EMAIL
    message["To"] = recipient_email
    message["Subject"] = subject
    message.set_content(text_content, subtype="plain", charset="utf-8")
    message.add_alternative(html_content, subtype="html", charset="utf-8")
    
    server = smtplib.SMTP(SMTP_SERVER, SMTP_PORT)
    server.starttls()
    server.login(SENDER_EMAIL, APP_PASSWORD)
    server.send_message(message)
    server.quit()
    
    return True