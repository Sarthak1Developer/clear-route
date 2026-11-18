## Evaluation deployment configuration (not a deployed-service verification)

- **Local:** `python scripts/run_local.py` builds the separate Gold-reconciled SQLite store and refuses to overwrite existing databases. Run `npm ci --prefix frontend`, then `npm --prefix frontend run dev` in another terminal.
- **Render:** the root `render.yaml` starts the same API on `0.0.0.0:$PORT`, exposes `/api/health`, and builds the derived store from the tracked Gold corpus on first startup. Configure `CORS_ORIGINS` as a JSON array containing your exact frontend URL, for example `["https://your-project.vercel.app"]`. No API key is needed for the public Open-Meteo provider. SQLite predictions are ephemeral unless you arrange durable storage; do not present this as a production persistent database deployment.
- **Vercel:** select the `frontend` root, use the committed Vite configuration, and set `VITE_API_URL=https://YOUR-BACKEND-HOST/api` before building. The Vite development proxy is not a production API proxy. Redeploy after changing this build-time variable.
- **Verify after deploying:** backend health, model registry, a four-model POST, CORS from the actual frontend origin, and each visible page. No deployment credentials or hosted URLs were supplied in this task, so deployed frontend/backend communication remains NOT VERIFIED.
- **Docker Compose:** the older compose file references missing Dockerfiles and a PostgreSQL setup that has not been reconciled with the new SQLite evaluation path. It remains NOT VERIFIED; use the tested launcher or validate a separate container deployment before claiming support.

Sources: [Render FastAPI deployment](https://render.com/docs/deploy-fastapi), [Vite on Vercel](https://vercel.com/docs/frameworks/frontend/vite).
