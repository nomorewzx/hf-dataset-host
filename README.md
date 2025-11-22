# MiniHFHub

MiniHFHub is a minimal HuggingFace-style dataset hub built on FastAPI, backed by Gitea + Git LFS for storage and a lightweight metadata cache. It is designed specifically to store and serve datasets compatible with the **HuggingFace Datasets** library, including the standard `dataset_info.json` metadata and split directories expected by `datasets.load_dataset`.

## Features

- Private Git repositories powered by Gitea with Git LFS for large files
- HuggingFace-compatible dataset endpoints (`info`, `tree`, `resolve`)
- Streaming proxy with HTTP range support for large artifacts
- Token-based authentication (Bearer tokens forwarded to Gitea)
- Simple SQLite metadata cache and lightweight HTML UI

## Supported dataset format

MiniHFHub expects each dataset repository to follow the HuggingFace Datasets layout:

- Repository path: `datasets/<owner>/<dataset_name>.git`
- Root files: `README.md` (dataset card) and `dataset_info.json`
- Split directories such as `train/`, `validation/`, `test/` containing Arrow shards (or other files tracked by Git LFS)

This layout matches what `datasets.load_dataset` needs, so storing HuggingFace datasets in MiniHFHub requires no custom adapters beyond pointing to the correct base URL.

## Repository layout

```
├── docker-compose.yaml
├── gitea/                   # Gitea data volume
├── minihfhub/
│   ├── Dockerfile
│   └── app/
│       ├── main.py
│       ├── routers/
│       ├── services/
│       ├── templates/
│       └── utils/
└── nginx/
    └── nginx.conf
```

## FastAPI endpoints

- `GET /datasets/{owner}/{dataset}/info` – dataset metadata (sha, splits, file list, cached `dataset_info.json`)
- `GET /datasets/{owner}/{dataset}/tree/{revision}` – Git tree listing
- `GET /datasets/{owner}/{dataset}/resolve/{revision}/{file_path}` – raw file streaming with range support
- `GET /` – basic dataset list UI (populated after first metadata refresh)
- `GET /datasets/{owner}/{dataset}` – dataset detail UI

Use `Authorization: Bearer <token>` to forward credentials to Gitea for private datasets.

## Running locally with Docker Compose

1. Ensure Docker + Docker Compose are installed.
2. Start the stack:

   ```bash
   docker compose up --build
   ```

3. Gitea will be available on http://localhost:3000 (LFS enabled). MiniHFHub API/UI will be exposed via Nginx on http://localhost/.

### Adding a dataset

1. Create a Gitea repository at `datasets/<owner>/<name>.git` (enable Git LFS).
2. Push dataset files:

   ```bash
   git lfs install
   git clone http://localhost:3000/datasets/<owner>/<name>.git
   cd <name>
   git lfs track "*.arrow"
   # Add dataset_info.json and split directories (train/0001.arrow, etc.)
   git add .
   git commit -m "Add dataset"
   git push
   ```

3. Query metadata to populate the cache:

   ```bash
   curl http://localhost/datasets/<owner>/<name>/info
   ```

### Using with `datasets.load_dataset`

Point `data_dir` or hub path to the MiniHFHub base URL:

```python
from datasets import load_dataset

ds = load_dataset(
    "<owner>/<name>",
    data_dir="http://localhost/datasets/<owner>/<name>",
)
```

For private datasets, pass `use_auth_token` matching the Bearer token configured in Gitea.

### Notes on authentication

- MiniHFHub expects `Authorization: Bearer <token>` headers.
- The same token is forwarded to Gitea (`token <token>` header).
- If a request is unauthenticated and the repository is private, Gitea will respond with 401/403 and the error will be propagated.

## Configuration

Environment variables (see `minihfhub/Dockerfile` for defaults):

- `DATABASE_URL` – database connection string (default `sqlite:///./data/minihfhub.db`)
- `GITEA_API_BASE` – Gitea API endpoint (`http://gitea:3000/api/v1`)
- `GITEA_RAW_BASE` – base URL for raw file serving (`http://gitea:3000`)

## Development

Install dependencies and run the API locally:

```bash
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
uvicorn minihfhub.app.main:app --reload
```

Data will be stored under `./data/minihfhub.db` by default.
