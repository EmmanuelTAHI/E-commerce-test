# Testing Guide - Logout & Email Verification

## ✅ What Was Fixed

### 1. Logout Feature
**Status**: ✅ Fixed and Working
**Location**: Account dropdown → Logout button

### 2. Email Verification
**Status**: ✅ Implemented and Ready
**How**: Gmail SMTP sends 6-digit code to user's email

---

## 🚀 Quick Test Steps

### Step 1: Configure Email (Required)
Edit `mon_projet_ecommerce/settings.py`:

```python
# Line 126-128
EMAIL_HOST_USER = 'YOUR-GMAIL@gmail.com'
EMAIL_HOST_PASSWORD = 'YOUR-APP-PASSWORD'  # Get from Google
DEFAULT_FROM_EMAIL = 'YOUR-GMAIL@gmail.com'
```

**Get Gmail App Password**:
1. Visit: https://myaccount.google.com/apppasswords
2. Click "App passwords" → "Mail" → "Generate"
3. Copy the 16-character password (no spaces)

### Step 2: Restart Server
```bash
# Stop current server (Ctrl+C)
python manage.py runserver
```

### Step 3: Test Registration & Verification

1. **Register**: http://127.0.0.1:8000/register/
   - Fill in form: username, email, password, etc.
   - Click "Register"
   - You'll see: "Verification code sent to [email]"

2. **Check Email**:
   - Open your Gmail inbox
   - Look for subject: "Verify Your Email - Shop"
   - Copy the 6-digit code (e.g., 123456)

3. **Verify**: http://127.0.0.1:8000/verify-email/
   - Enter the 6-digit code
   - Click "Verify Email"
   - Success! You're logged in

### Step 4: Test Logout

1. Click your profile/avatar in top right
2. Click "Logout" from dropdown
3. You'll see: "You have been logged out successfully!"
4. Redirected to home page (logged out state)

---

## 🧪 Alternative: Test Without Real Email

For development testing, you can use console output instead of real emails:

### Update Settings
Edit `mon_projet_ecommerce/settings.py`:

```python
# Add this at the top after imports
EMAIL_BACKEND = 'django.core.mail.backends.console.EmailBackend'
```

Now emails will print to your console instead of being sent!
You'll see the verification code in your terminal.

---

## 📋 Expected Flow

### Successful Registration:
```
1. User fills registration form
2. System generates: Code 123456
3. Email sent to user@gmail.com
4. User checks email → finds code
5. User enters "123456"
6. ✅ Account created
7. ✅ User logged in automatically
8. Redirected to home page
```

### Successful Logout:
```
1. User clicks logout in dropdown
2. ✅ Session cleared
3. ✅ "Logged out successfully!" message
4. Redirected to home page
5. User now sees "Login" and "Register" buttons
```

---

## 🔍 What to Check

### ✅ Registration Tests:
- [ ] Form validation works
- [ ] Duplicate username shows error
- [ ] Duplicate email shows error
- [ ] Email is sent successfully
- [ ] Verification page loads
- [ ] Code entry works
- [ ] Account is created
- [ ] User is logged in

### ✅ Email Verification Tests:
- [ ] Code is exactly 6 digits
- [ ] Code expires after 10 minutes
- [ ] Invalid code shows error
- [ ] Successful verification logs in user
- [ ] Old codes can't be reused

### ✅ Logout Tests:
- [ ] Logout button visible when logged in
- [ ] Logout works from dropdown
- [ ] Success message appears
- [ ] Session cleared (cart cleared)
- [ ] Redirects to home
- [ ] Shows login/register buttons

---

## 🐛 Common Issues

### Issue: "SMTPAuthenticationError"
**Fix**: Use App Password, not regular password
**Guide**: See EMAIL_SETUP.md

### Issue: "Code not working"
**Check**:
- Code is 6 digits exactly
- Code hasn't expired (10 min limit)
- Email in Gmail (check spam)

### Issue: "Logout doesn't work"
**Fix**:
- Clear browser cache/cookies
- Restart Django server
- Make sure you're clicking the logout link in the dropdown

---

## 📱 Test Data Example

**Try registering with**:
```
Username: testuser123
Email: your-real-email@gmail.com
Password: TestPass123!
First Name: Test
Last Name: User
```

**Expected**: Email with code like: `429761`

---

## 🎯 Next Steps After Testing

1. ✅ Logout works properly
2. ✅ Email verification works
3. Configure real Gmail credentials
4. Add products via admin panel
5. Start using the app!

---

## 📚 More Information

- `EMAIL_SETUP.md` - Detailed email configuration
- `CHANGES.md` - All changes explained
- `README.md` - Full project documentation
- `QUICKSTART.md` - Quick start guide

---

**Happy Testing!** 🎉
