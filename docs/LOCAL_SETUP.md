# AutoHub — Local setup (Windows PowerShell)

These steps are for the source ZIP. Keep your real credentials on your own computer; never send the `.env` file to anyone.

## 1. Extract the project

Extract `AutoHub_Completed.zip` to a folder such as:

`S:\Proj\AutoHub`

The project should contain `backend`, `frontend` and `docs` folders.

## 2. Configure the backend environment

Open PowerShell:

```powershell
cd S:\Proj\AutoHub\backend
Copy-Item .env.example .env
notepad .env
```

Edit these values in `backend\.env`:

- `DJANGO_SECRET_KEY`: replace the placeholder with a new random secret. Generate one with:

  ```powershell
  python -c "import secrets; print(secrets.token_urlsafe(50))"
  ```

- `MONGODB_URI`: paste your own MongoDB Atlas connection string. URL-encode special characters in the database username/password if required by MongoDB.
- `MONGODB_NAME`: keep `autohub_db` if you are continuing with the existing AutoHub database.
- Keep `DEBUG=True` and the local `ALLOWED_HOSTS`, `CORS_ALLOWED_ORIGINS`, and `CSRF_TRUSTED_ORIGINS` values for local development.

`REDIS_URL` is optional while `DEBUG=True`. Leave it commented to use Django's local-memory cache, or uncomment it when your local WSL Redis service is running:

`REDIS_URL=redis://127.0.0.1:6379/1`

Do not commit or share `backend\.env`.

## 3. Install and start the backend

If you already have the existing `backend\.venv`, activate it. Otherwise create a new environment using the Python version installed on your machine.

```powershell
cd S:\Proj\AutoHub\backend

# Activate an existing environment:
.\.venv\Scripts\Activate.ps1

# If no .venv exists, create one and activate it instead:
# python -m venv .venv
# .\.venv\Scripts\Activate.ps1

python -m pip install --upgrade pip
pip install -r requirements.txt
python manage.py check
python manage.py migrate
python manage.py runserver 127.0.0.1:8000
```

Keep this terminal running. The backend API base is `http://127.0.0.1:8000/api`.

If the database is new, or you need administrator access, open a second backend terminal, activate the same virtual environment, and run:

```powershell
python manage.py createsuperuser
```

Open `http://127.0.0.1:8000/admin/` and sign in with that administrator account. Review and approve dealer applications. Review dealer vehicle listings and publish appropriate listings; the dealer account cannot publish its own listings.

## 4. Configure and start the frontend

Open a second PowerShell terminal:

```powershell
cd S:\Proj\AutoHub\frontend
Copy-Item .env.example .env.local
notepad .env.local
```

For local development, the file should contain:

```dotenv
VITE_API_BASE_URL=http://127.0.0.1:8000/api
```

Install exact dependencies from the lockfile and verify the application:

```powershell
npm ci
npm run lint
npm run build
npm run dev
```

Open the local Vite URL printed in the terminal, normally `http://localhost:5173`.

Use a supported modern Node.js version. Node.js 26 is suitable for the versions in this project.

## 5. Test the main flows

1. Browse `/new-cars`, open a model, and inspect its variants/specifications.
2. Browse `/used-cars`, apply a filter, change sorting, paginate and open a listing detail.
3. Use `/compare` and select two or three different variants.
4. Use `/valuation` to request an estimate. Sign in to save a valuation to account history.
5. Register a customer account and sign out/in.
6. Open `/dealer`, apply as a dealer, then approve the dealer profile in Django admin.
7. As the approved dealer, add a listing. Publish it in Django admin, open `/dealer-marketplace`, and submit a customer enquiry. Check the enquiry in the dealer workspace.

## 6. Production deployment checklist

The ZIP does not deploy services or create hosting accounts. Before launch:

- Deploy the Django backend and set `DEBUG=False`, a strong `DJANGO_SECRET_KEY`, exact `ALLOWED_HOSTS`, `MONGODB_URI`, `MONGODB_NAME`, production `REDIS_URL`, frontend `CORS_ALLOWED_ORIGINS`, and `CSRF_TRUSTED_ORIGINS`.
- Configure SMTP credentials for real email delivery.
- Configure the real HTTPS/reverse-proxy behavior. Only set `USE_X_FORWARDED_PROTO=True` when the hosting proxy sets and protects the forwarded protocol header. Enable HSTS only after HTTPS has been verified.
- Set the production frontend `VITE_API_BASE_URL` to the deployed backend URL ending in `/api`, then run `npm run build` and deploy `frontend/dist/`.
- Configure MongoDB Atlas network access and least-privilege credentials; configure managed Redis accessible to the backend.
- Confirm data-source licensing, attribution, privacy disclosures, dealer verification processes and any marketplace legal requirements.
- Test registration/login/refresh/logout, dealer access boundaries, enquiry throttling, pricing behavior, HTTPS, CORS and deep-link refresh after deployment.

Do not copy local `.env` files into the deployment ZIP or Git repository. Configure secrets in the hosting provider's environment-variable dashboard.
