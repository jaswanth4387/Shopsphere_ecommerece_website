# Deploying ShopSphere on Render (free setup)

Stack stays the same: Flask + MySQL + Jinja/Bootstrap + Razorpay.
Free services used: Render (web), Aiven (MySQL), Cloudinary (product images), Brevo (OTP email).

## 0. Rotate leaked secrets first
Your old `cmail.py` (with the Gmail App Password) is in the git history of your public/private GitHub repo.
- Google Account -> Security -> App passwords -> delete the old one.
- Razorpay dashboard: regenerate the TEST key secret you used.
- Change your local MySQL root password if you reuse it anywhere.

## 1. Aiven MySQL
1. Create an Aiven account -> Create service -> MySQL -> choose the **Free** plan.
2. When it is running, copy Host, Port, User, Password (database name is usually `defaultdb`).
3. On your computer, create `.env` (copy `.env.example`) and fill the DB_* values with the Aiven ones.
4. Create the tables and sample products once:
   `pip install -r requirements.txt`
   `python init_db.py --seed`

## 2. Cloudinary
Create a free account -> Dashboard -> copy the **API Environment variable** (`cloudinary://KEY:SECRET@CLOUD`).
This becomes `CLOUDINARY_URL` on Render.

## 3. Brevo (OTP emails)
Create a free account -> Senders -> add and verify the email address you want OTPs to come from
-> SMTP & API -> create an **API key**. Use them as `BREVO_API_KEY` and `MAIL_SENDER`.

## 4. Razorpay
Use **Test mode** keys (`rzp_test_...`) as `RAZORPAY_KEY_ID` and `RAZORPAY_KEY_SECRET`.
Test card: 4111 1111 1111 1111, any future expiry, any CVV (use the test OTP shown by Razorpay).

## 5. Push to GitHub
Make sure `.env`, `venv/` are NOT in the commit (the new `.gitignore` handles it), then:
`git add . && git commit -m "Render-ready ShopSphere" && git push`

## 6. Render
1. Render dashboard -> New -> **Blueprint** -> pick your repo (it reads `render.yaml`).
   (Or New -> Web Service with: Build `pip install -r requirements.txt`,
   Start `gunicorn app:app --workers 2 --threads 4 --timeout 60 --bind 0.0.0.0:$PORT`.)
2. Fill the environment variables marked "sync: false":
   DB_HOST, DB_PORT, DB_USER, DB_PASSWORD, DB_NAME, RAZORPAY_KEY_ID, RAZORPAY_KEY_SECRET,
   CLOUDINARY_URL, BREVO_API_KEY, MAIL_SENDER. (SECRET_KEY is generated for you.)
3. Deploy. Open `https://<your-service>.onrender.com/healthz` - it should say `ok`.

## 7. Create your admin account
Admin sign-up is off by default so strangers cannot make themselves admin.
1. In Render -> Environment, set `ALLOW_ADMIN_SIGNUP` = `true` (service redeploys).
2. Open `/signup/admin`, register, enter the emailed OTP.
3. Set `ALLOW_ADMIN_SIGNUP` back to `false`.

## 8. Checklist (what "working" means)
- [ ] /home lists products with images
- [ ] User signup -> OTP email arrives -> login works
- [ ] Add to cart, +/- quantity, remove
- [ ] Checkout opens Razorpay, test payment succeeds, order shows in /admin/orders, cart empties, stock drops
- [ ] Admin: add product with image (image stays after a redeploy), edit, delete
- [ ] Review form appears only after a paid order for that product

## Good to know
- Free Render services sleep after 15 minutes idle; the first request afterwards takes about a minute.
- Free Render blocks SMTP, which is why email goes through Brevo's HTTPS API.
- If a customer pays but closes the tab before the redirect, the order stays "Pending". A Razorpay webhook
  would fix that; it is a good next upgrade.
