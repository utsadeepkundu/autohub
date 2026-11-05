# AutoHub frontend

This folder contains the React 19 + Vite 8 customer and dealer application.

## Local development

1. Copy `.env.example` to `.env.local`.
2. Set `VITE_API_BASE_URL` to your Django API base, normally `http://127.0.0.1:8000/api` for local development.
3. Run `npm ci`.
4. Run `npm run lint` and `npm run build`.
5. Run `npm run dev` and open the local URL printed by Vite.

See the project-level `../README.md` and `../docs/LOCAL_SETUP.md` for backend setup and full application workflows.
