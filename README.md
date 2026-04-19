# Setup

- Rename the src/app_name module accordingly
- Update imports for the new name
- Adjust the pyproject.toml file for the new name
- Run `pip install -e .` from the project root
- Create .env.dev using example `cp .env.example .env.dev` and update accordingly

# Writing a sample script and DB connection

```python
import json
from pathlib import Path
from alembic import op
from sqlalchemy import text

# Import env vars and overwrite the connection string to the running DB (outside the container service)

import os
from dotenv import load_dotenv
load_dotenv(".env.dev")
os.environ['DATABASE_URL'] = "postgresql+psycopg://app_user:app_password@localhost:5432/app_db"

from fastapi.testclient import TestClient

from app.__main__ import app

client = TestClient(app)

response = client.get("/users/1")
print(response.json())
```