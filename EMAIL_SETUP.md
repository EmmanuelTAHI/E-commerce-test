# Email Setup Guide

## Email Verification Feature

Your e-commerce application now includes **email verification** with Gmail SMTP authentication.

## How It Works

1. User registers with their email address
2. System generates a 6-digit verification code
3. Code is sent to user's email via Gmail SMTP
4. User enters the code on the verification page
5. Account is activated after successful verification

## Setup Instructions

### For Gmail Users

1. **Enable 2-Step Verification**
   - Go to: https://myaccount.google.com/security
   - Turn on 2-Step Verification

2. **Generate App Password**
   - Go to: https://myaccount.google.com/apppasswords
   - Select "Mail" and your device
   - Click "Generate"
   - Copy the 16-character password (e.g., `abcd efgh ijkl mnop`)

3. **Update Settings**
   - Open: `mon_projet_ecommerce/settings.py`
   - Update these lines (around line 126-128):
   ```python
   EMAIL_HOST_USER = 'your-actual-email@gmail.com'  # Your Gmail address
   EMAIL_HOST_PASSWORD = 'abcd efgh ijkl mnop'     # 16-char app password (no spaces)
   DEFAULT_FROM_EMAIL = 'your-actual-email@gmail.com'
   ```

### For Other Email Providers

#### Outlook/Hotmail
```python
EMAIL_HOST = 'smtp-mail.outlook.com'
EMAIL_PORT = 587
EMAIL_USE_TLS = True
```

#### Yahoo Mail
```python
EMAIL_HOST = 'smtp.mail.yahoo.com'
EMAIL_PORT = 587
EMAIL_USE_TLS = True
```

#### Custom SMTP
```python
EMAIL_HOST = 'smtp.yourdomain.com'
EMAIL_PORT = 587  # or 465 for SSL
EMAIL_USE_TLS = True  # Use False for port 465 with SSL
EMAIL_USE_SSL = False  # Use True for port 465
```

## Testing Email

After configuring, test your email settings:

### Option 1: Using Django Shell
```bash
python manage.py shell
```

Then run:
```python
from django.core.mail import send_mail

send_mail(
    subject='Test Email',
    message='This is a test email from your e-commerce app.',
    from_email=None,  # Uses DEFAULT_FROM_EMAIL
    recipient_list=['your-test-email@gmail.com'],
    fail_silently=False,
)
```

### Option 2: Register a Test Account
1. Go to http://127.0.0.1:8000/register/
2. Fill in the registration form
3. Check your email for the verification code
4. Enter the code to complete registration

## Troubleshooting

### "SMTPAuthenticationError: (535, '5.7.8 Username and Password not accepted')"
- Check that you're using an **App Password**, not your regular Gmail password
- Make sure the app password doesn't have spaces
- Enable "Less secure app access" (older Gmail accounts only)

### "Connection Refused"
- Check your firewall settings
- Try using port 465 with SSL instead:
  ```python
  EMAIL_PORT = 465
  EMAIL_USE_SSL = True
  EMAIL_USE_TLS = False
  ```

### "Email not in inbox"
- Check spam/junk folder
- Verify email address is correct
- Check the email provider's security settings

### Testing in Development
For testing without sending real emails, use the **console email backend**:

```python
# In settings.py, add:
if DEBUG:
    EMAIL_BACKEND = 'django.core.mail.backends.console.EmailBackend'
```

This will print emails to the console instead of sending them.

## Security Notes

⚠️ **Important**: Never commit your email credentials to version control!

1. Add to `.gitignore`:
   ```
   .env
   local_settings.py
   ```

2. Use environment variables:
   ```python
   import os

   EMAIL_HOST_USER = os.environ.get('EMAIL_HOST_USER', '')
   EMAIL_HOST_PASSWORD = os.environ.get('EMAIL_HOST_PASSWORD', '')
   ```

3. Or use Django-environ:
   ```bash
   pip install django-environ
   ```

## Code Expiration

Verification codes expire after **10 minutes** for security.

## Features

✅ Secure 6-digit verification codes
✅ 10-minute expiration
✅ One-time use codes
✅ Gmail SMTP integration
✅ Beautiful verification UI
✅ Email with clear instructions

## Using the Feature

### For Users:
1. Register at `/register/`
2. Check email (including spam folder)
3. Enter the 6-digit code at `/verify-email/`
4. Start shopping!

### For Developers:
- Codes are stored in `EmailVerification` model
- Admin panel shows all verification attempts
- Old codes are automatically deleted when new ones are generated

## Next Steps

1. Configure your Gmail credentials in `settings.py`
2. Test the registration flow
3. Verify emails are being sent correctly
4. Deploy with proper security measures

Happy email verification! 📧✨
