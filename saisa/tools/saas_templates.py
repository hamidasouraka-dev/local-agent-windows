"""SaaS project generator — full-stack SaaS boilerplate templates.

Generate production-ready SaaS projects with:
- Authentication (JWT + sessions)
- User management
- Dashboard
- API endpoints
- Payment integration (Stripe stubs)
- Database models
"""

from __future__ import annotations

import json
from pathlib import Path


def generate_saas(name: str, stack: str = "fastapi", path: str = ".") -> str:
    """Generate a full SaaS project structure."""
    root = Path(path).resolve() / name
    if root.exists():
        return json.dumps({"error": f"Directory already exists: {root}"})

    generators = {
        "fastapi": _generate_fastapi_saas,
        "express": _generate_express_saas,
    }

    gen = generators.get(stack)
    if gen is None:
        return json.dumps({"error": f"Unknown stack: {stack}. Available: {', '.join(generators.keys())}"})

    try:
        files = gen(name)
        created: list[str] = []
        for rel_path, content in files.items():
            file_path = root / rel_path
            file_path.parent.mkdir(parents=True, exist_ok=True)
            file_path.write_text(content.replace("{{name}}", name), encoding="utf-8")
            created.append(rel_path)
        return json.dumps({
            "ok": True,
            "project": name,
            "stack": stack,
            "path": str(root),
            "files_created": created,
            "features": [
                "JWT Authentication",
                "User registration & login",
                "Role-based access control",
                "REST API with CRUD",
                "Database models (SQLite/PostgreSQL)",
                "Stripe payment stubs",
                "Admin dashboard API",
                "Health checks",
                "CORS configuration",
                "Environment configuration",
            ],
        })
    except Exception as e:
        return json.dumps({"error": str(e)})


def list_saas_templates() -> str:
    """List available SaaS templates."""
    return json.dumps({
        "templates": [
            {
                "stack": "fastapi",
                "description": "Python FastAPI SaaS with JWT auth, user management, Stripe, SQLite",
                "features": ["JWT Auth", "User CRUD", "Roles", "Stripe", "SQLite", "Admin API"],
            },
            {
                "stack": "express",
                "description": "Node.js Express SaaS with JWT auth, user management, Stripe",
                "features": ["JWT Auth", "User CRUD", "Roles", "Stripe", "SQLite", "Dashboard API"],
            },
        ],
    })


def _generate_fastapi_saas(name: str) -> dict[str, str]:
    return {
        "requirements.txt": """fastapi>=0.110.0
uvicorn[standard]>=0.29.0
sqlalchemy>=2.0.0
pyjwt>=2.8.0
passlib[bcrypt]>=1.7.4
python-dotenv>=1.0.0
httpx>=0.27.0
python-multipart>=0.0.9
stripe>=8.0.0
pytest>=8.0.0
pytest-asyncio>=0.23.0
""",
        ".env.example": f"""# {name} Configuration
DATABASE_URL=sqlite:///./app.db
SECRET_KEY=change-me-to-a-random-secret-key
JWT_ALGORITHM=HS256
JWT_EXPIRE_MINUTES=1440
STRIPE_SECRET_KEY=sk_test_...
STRIPE_WEBHOOK_SECRET=whsec_...
CORS_ORIGINS=http://localhost:3000,http://localhost:5173
""",
        "app/__init__.py": "",
        "app/main.py": '''"""{{name}} — SaaS API."""
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from .config import settings
from .routes import auth, users, admin, payments

app = FastAPI(
    title="{{name}}",
    version="0.1.0",
    description="SaaS API with authentication, user management, and payments",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(auth.router, prefix="/api/auth", tags=["Authentication"])
app.include_router(users.router, prefix="/api/users", tags=["Users"])
app.include_router(admin.router, prefix="/api/admin", tags=["Admin"])
app.include_router(payments.router, prefix="/api/payments", tags=["Payments"])


@app.get("/")
async def root():
    return {"name": "{{name}}", "version": "0.1.0", "status": "running"}


@app.get("/health")
async def health():
    return {"status": "ok"}
''',
        "app/config.py": '''"""Configuration management."""
import os
from pathlib import Path
from dotenv import load_dotenv

load_dotenv()


class Settings:
    database_url: str = os.getenv("DATABASE_URL", "sqlite:///./app.db")
    secret_key: str = os.getenv("SECRET_KEY", "dev-secret-change-me")
    jwt_algorithm: str = os.getenv("JWT_ALGORITHM", "HS256")
    jwt_expire_minutes: int = int(os.getenv("JWT_EXPIRE_MINUTES", "1440"))
    stripe_secret_key: str = os.getenv("STRIPE_SECRET_KEY", "")
    stripe_webhook_secret: str = os.getenv("STRIPE_WEBHOOK_SECRET", "")
    cors_origins: list[str] = os.getenv("CORS_ORIGINS", "http://localhost:3000").split(",")


settings = Settings()
''',
        "app/database.py": '''"""Database setup with SQLAlchemy."""
from sqlalchemy import create_engine
from sqlalchemy.orm import DeclarativeBase, sessionmaker

from .config import settings

engine = create_engine(settings.database_url, connect_args={"check_same_thread": False})
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)


class Base(DeclarativeBase):
    pass


def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


def init_db():
    Base.metadata.create_all(bind=engine)
''',
        "app/models.py": '''"""Database models."""
import time
from sqlalchemy import Boolean, Column, Float, Integer, String, Text

from .database import Base


class User(Base):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, index=True)
    email = Column(String(255), unique=True, index=True, nullable=False)
    username = Column(String(100), unique=True, index=True, nullable=False)
    password_hash = Column(String(255), nullable=False)
    role = Column(String(20), default="user")  # user, admin, premium
    is_active = Column(Boolean, default=True)
    created_at = Column(Float, default=time.time)
    stripe_customer_id = Column(String(255), nullable=True)
    subscription_plan = Column(String(50), default="free")  # free, pro, enterprise


class APIKey(Base):
    __tablename__ = "api_keys"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, index=True, nullable=False)
    key = Column(String(64), unique=True, nullable=False)
    label = Column(String(100), default="")
    created_at = Column(Float, default=time.time)
    is_active = Column(Boolean, default=True)
''',
        "app/auth.py": '''"""Authentication utilities."""
import time
from typing import Any
import jwt
from passlib.context import CryptContext

from .config import settings

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")


def hash_password(password: str) -> str:
    return pwd_context.hash(password)


def verify_password(plain: str, hashed: str) -> bool:
    return pwd_context.verify(plain, hashed)


def create_token(data: dict[str, Any]) -> str:
    payload = data.copy()
    payload["exp"] = time.time() + settings.jwt_expire_minutes * 60
    return jwt.encode(payload, settings.secret_key, algorithm=settings.jwt_algorithm)


def decode_token(token: str) -> dict[str, Any] | None:
    try:
        payload = jwt.decode(token, settings.secret_key, algorithms=[settings.jwt_algorithm])
        if payload.get("exp", 0) < time.time():
            return None
        return payload
    except jwt.PyJWTError:
        return None
''',
        "app/routes/__init__.py": "",
        "app/routes/auth.py": '''"""Auth routes — register, login, me."""
from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel, EmailStr
from sqlalchemy.orm import Session

from ..auth import create_token, hash_password, verify_password
from ..database import get_db, init_db
from ..models import User

router = APIRouter()


class RegisterRequest(BaseModel):
    email: str
    username: str
    password: str


class LoginRequest(BaseModel):
    email: str
    password: str


@router.post("/register")
def register(req: RegisterRequest, db: Session = Depends(get_db)):
    init_db()
    if db.query(User).filter(User.email == req.email).first():
        raise HTTPException(400, "Email already registered")
    if db.query(User).filter(User.username == req.username).first():
        raise HTTPException(400, "Username taken")
    user = User(
        email=req.email,
        username=req.username,
        password_hash=hash_password(req.password),
    )
    db.add(user)
    db.commit()
    db.refresh(user)
    token = create_token({"sub": str(user.id), "role": user.role})
    return {"token": token, "user": {"id": user.id, "username": user.username, "role": user.role}}


@router.post("/login")
def login(req: LoginRequest, db: Session = Depends(get_db)):
    init_db()
    user = db.query(User).filter(User.email == req.email).first()
    if not user or not verify_password(req.password, user.password_hash):
        raise HTTPException(401, "Invalid credentials")
    if not user.is_active:
        raise HTTPException(403, "Account deactivated")
    token = create_token({"sub": str(user.id), "role": user.role})
    return {"token": token, "user": {"id": user.id, "username": user.username, "role": user.role}}
''',
        "app/routes/users.py": '''"""User routes — profile, preferences."""
from fastapi import APIRouter, Depends, HTTPException, Header
from sqlalchemy.orm import Session

from ..auth import decode_token
from ..database import get_db, init_db
from ..models import User

router = APIRouter()


def get_current_user(authorization: str = Header(...), db: Session = Depends(get_db)):
    init_db()
    if not authorization.startswith("Bearer "):
        raise HTTPException(401, "Invalid token format")
    token = authorization[7:]
    payload = decode_token(token)
    if payload is None:
        raise HTTPException(401, "Token expired or invalid")
    user = db.query(User).filter(User.id == int(payload["sub"])).first()
    if not user:
        raise HTTPException(404, "User not found")
    return user


@router.get("/me")
def get_me(user: User = Depends(get_current_user)):
    return {
        "id": user.id,
        "email": user.email,
        "username": user.username,
        "role": user.role,
        "plan": user.subscription_plan,
    }
''',
        "app/routes/admin.py": '''"""Admin routes — user management, stats."""
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from ..database import get_db, init_db
from ..models import User
from .users import get_current_user

router = APIRouter()


@router.get("/users")
def list_users(current: User = Depends(get_current_user), db: Session = Depends(get_db)):
    if current.role != "admin":
        raise HTTPException(403, "Admin only")
    init_db()
    users = db.query(User).all()
    return [
        {"id": u.id, "email": u.email, "username": u.username, "role": u.role, "plan": u.subscription_plan}
        for u in users
    ]


@router.get("/stats")
def get_stats(current: User = Depends(get_current_user), db: Session = Depends(get_db)):
    if current.role != "admin":
        raise HTTPException(403, "Admin only")
    init_db()
    total = db.query(User).count()
    active = db.query(User).filter(User.is_active == True).count()
    plans = {}
    for plan_name in ["free", "pro", "enterprise"]:
        plans[plan_name] = db.query(User).filter(User.subscription_plan == plan_name).count()
    return {"total_users": total, "active_users": active, "plans": plans}
''',
        "app/routes/payments.py": '''"""Payment routes — Stripe integration stubs."""
from fastapi import APIRouter, Depends, HTTPException

from ..models import User
from .users import get_current_user

router = APIRouter()


@router.post("/create-checkout")
def create_checkout(
    plan: str = "pro",
    current: User = Depends(get_current_user),
):
    """Create a Stripe checkout session (stub)."""
    plans = {
        "pro": {"price": "price_pro_monthly", "amount": 999},
        "enterprise": {"price": "price_enterprise_monthly", "amount": 4999},
    }
    if plan not in plans:
        raise HTTPException(400, f"Invalid plan. Available: {list(plans.keys())}")

    # TODO: Integrate real Stripe checkout
    return {
        "checkout_url": f"https://checkout.stripe.com/pay/{plans[plan]['price']}",
        "plan": plan,
        "amount": plans[plan]["amount"],
        "currency": "usd",
        "note": "Stripe integration stub — connect your Stripe keys in .env",
    }


@router.get("/subscription")
def get_subscription(current: User = Depends(get_current_user)):
    """Get current user's subscription status."""
    return {
        "user_id": current.id,
        "plan": current.subscription_plan,
        "stripe_customer_id": current.stripe_customer_id,
    }
''',
        "Dockerfile": """FROM python:3.12-slim
WORKDIR /app
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt
COPY . .
EXPOSE 8000
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]
""",
        "docker-compose.yml": """services:
  api:
    build: .
    ports:
      - "8000:8000"
    env_file: .env
    volumes:
      - ./app:/app/app
    restart: unless-stopped
""",
        ".gitignore": """__pycache__/
*.pyc
.venv/
venv/
.env
*.db
*.sqlite3
""",
        "README.md": """# {{name}}

## SaaS API — Generated by SAISA

### Quick Start

```bash
pip install -r requirements.txt
cp .env.example .env
uvicorn app.main:app --reload
```

### API Endpoints

| Endpoint | Method | Description |
|----------|--------|-------------|
| `/api/auth/register` | POST | Register new user |
| `/api/auth/login` | POST | Login & get JWT |
| `/api/users/me` | GET | Get current user profile |
| `/api/admin/users` | GET | List all users (admin) |
| `/api/admin/stats` | GET | Dashboard stats (admin) |
| `/api/payments/create-checkout` | POST | Create payment session |
| `/api/payments/subscription` | GET | Get subscription status |
| `/health` | GET | Health check |

### Docker

```bash
docker compose up --build
```

### Test

```bash
pytest -v
```
""",
        "tests/__init__.py": "",
        "tests/test_auth.py": '''"""Test authentication."""
import pytest
from httpx import AsyncClient, ASGITransport
from app.main import app
from app.database import init_db


@pytest.mark.asyncio
async def test_register_and_login():
    init_db()
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as ac:
        # Register
        resp = await ac.post("/api/auth/register", json={
            "email": "test@example.com",
            "username": "testuser",
            "password": "secret123",
        })
        assert resp.status_code == 200
        data = resp.json()
        assert "token" in data

        # Login
        resp = await ac.post("/api/auth/login", json={
            "email": "test@example.com",
            "password": "secret123",
        })
        assert resp.status_code == 200
        assert "token" in resp.json()
''',
    }


def _generate_express_saas(name: str) -> dict[str, str]:
    return {
        "package.json": """{"name": "{{name}}",
  "version": "0.1.0",
  "scripts": {
    "dev": "tsx watch src/index.ts",
    "build": "tsc",
    "start": "node dist/index.js"
  },
  "dependencies": {
    "express": "^5.0.0",
    "jsonwebtoken": "^9.0.0",
    "bcryptjs": "^3.0.0",
    "better-sqlite3": "^11.0.0",
    "cors": "^2.8.5",
    "dotenv": "^16.4.0",
    "stripe": "^17.0.0"
  },
  "devDependencies": {
    "@types/express": "^5.0.0",
    "@types/jsonwebtoken": "^9.0.0",
    "@types/bcryptjs": "^3.0.0",
    "@types/better-sqlite3": "^7.6.0",
    "@types/cors": "^2.8.0",
    "@types/node": "^22.0.0",
    "tsx": "^4.19.0",
    "typescript": "^5.5.0"
  }
}
""",
        "tsconfig.json": """{
  "compilerOptions": {
    "target": "ES2022",
    "module": "NodeNext",
    "moduleResolution": "NodeNext",
    "outDir": "./dist",
    "strict": true,
    "esModuleInterop": true,
    "skipLibCheck": true
  },
  "include": ["src"]
}
""",
        "src/index.ts": '''import express from "express";
import cors from "cors";
import { config } from "dotenv";
import { authRouter } from "./routes/auth";
import { usersRouter } from "./routes/users";
import { paymentsRouter } from "./routes/payments";
import { initDB } from "./database";

config();
initDB();

const app = express();
const PORT = process.env.PORT || 3000;

app.use(cors());
app.use(express.json());

app.use("/api/auth", authRouter);
app.use("/api/users", usersRouter);
app.use("/api/payments", paymentsRouter);

app.get("/", (_req, res) => {
  res.json({ name: "{{name}}", version: "0.1.0", status: "running" });
});

app.get("/health", (_req, res) => {
  res.json({ status: "ok" });
});

app.listen(PORT, () => {
  console.log(`{{name}} running on http://localhost:${PORT}`);
});
''',
        "src/database.ts": '''import Database from "better-sqlite3";
import path from "path";

let db: Database.Database;

export function getDB(): Database.Database {
  if (!db) {
    db = new Database(process.env.DATABASE_PATH || "app.db");
    db.pragma("journal_mode = WAL");
  }
  return db;
}

export function initDB(): void {
  const database = getDB();
  database.exec(`
    CREATE TABLE IF NOT EXISTS users (
      id INTEGER PRIMARY KEY AUTOINCREMENT,
      email TEXT UNIQUE NOT NULL,
      username TEXT UNIQUE NOT NULL,
      password_hash TEXT NOT NULL,
      role TEXT DEFAULT 'user',
      is_active INTEGER DEFAULT 1,
      created_at REAL DEFAULT (unixepoch()),
      subscription_plan TEXT DEFAULT 'free',
      stripe_customer_id TEXT
    );
  `);
}
''',
        "src/auth.ts": '''import jwt from "jsonwebtoken";
import bcrypt from "bcryptjs";

const SECRET = process.env.SECRET_KEY || "dev-secret-change-me";
const EXPIRE = process.env.JWT_EXPIRE_HOURS || "24";

export function hashPassword(password: string): string {
  return bcrypt.hashSync(password, 10);
}

export function verifyPassword(plain: string, hash: string): boolean {
  return bcrypt.compareSync(plain, hash);
}

export function createToken(payload: Record<string, unknown>): string {
  return jwt.sign(payload, SECRET, { expiresIn: `${EXPIRE}h` });
}

export function decodeToken(token: string): Record<string, unknown> | null {
  try {
    return jwt.verify(token, SECRET) as Record<string, unknown>;
  } catch {
    return null;
  }
}
''',
        "src/routes/auth.ts": '''import { Router, Request, Response } from "express";
import { getDB } from "../database";
import { hashPassword, verifyPassword, createToken } from "../auth";

export const authRouter = Router();

authRouter.post("/register", (req: Request, res: Response) => {
  const { email, username, password } = req.body;
  if (!email || !username || !password) {
    res.status(400).json({ error: "Missing fields" });
    return;
  }
  const db = getDB();
  const existing = db.prepare("SELECT id FROM users WHERE email = ?").get(email);
  if (existing) {
    res.status(400).json({ error: "Email already registered" });
    return;
  }
  const hash = hashPassword(password);
  const result = db.prepare(
    "INSERT INTO users (email, username, password_hash) VALUES (?, ?, ?)"
  ).run(email, username, hash);
  const token = createToken({ sub: result.lastInsertRowid, role: "user" });
  res.json({ token, user: { id: result.lastInsertRowid, username, role: "user" } });
});

authRouter.post("/login", (req: Request, res: Response) => {
  const { email, password } = req.body;
  const db = getDB();
  const user = db.prepare("SELECT * FROM users WHERE email = ?").get(email) as any;
  if (!user || !verifyPassword(password, user.password_hash)) {
    res.status(401).json({ error: "Invalid credentials" });
    return;
  }
  const token = createToken({ sub: user.id, role: user.role });
  res.json({ token, user: { id: user.id, username: user.username, role: user.role } });
});
''',
        "src/routes/users.ts": '''import { Router, Request, Response, NextFunction } from "express";
import { getDB } from "../database";
import { decodeToken } from "../auth";

export const usersRouter = Router();

function authMiddleware(req: Request, res: Response, next: NextFunction) {
  const auth = req.headers.authorization;
  if (!auth?.startsWith("Bearer ")) {
    res.status(401).json({ error: "Missing token" });
    return;
  }
  const payload = decodeToken(auth.slice(7));
  if (!payload) {
    res.status(401).json({ error: "Invalid token" });
    return;
  }
  (req as any).userId = payload.sub;
  (req as any).userRole = payload.role;
  next();
}

usersRouter.get("/me", authMiddleware, (req: Request, res: Response) => {
  const db = getDB();
  const user = db.prepare("SELECT id, email, username, role, subscription_plan FROM users WHERE id = ?")
    .get((req as any).userId) as any;
  if (!user) {
    res.status(404).json({ error: "User not found" });
    return;
  }
  res.json(user);
});
''',
        "src/routes/payments.ts": '''import { Router, Request, Response } from "express";

export const paymentsRouter = Router();

paymentsRouter.post("/create-checkout", (req: Request, res: Response) => {
  const { plan = "pro" } = req.body;
  const plans: Record<string, { price: string; amount: number }> = {
    pro: { price: "price_pro_monthly", amount: 999 },
    enterprise: { price: "price_enterprise_monthly", amount: 4999 },
  };
  if (!plans[plan]) {
    res.status(400).json({ error: `Invalid plan. Available: ${Object.keys(plans)}` });
    return;
  }
  res.json({
    checkout_url: `https://checkout.stripe.com/pay/${plans[plan].price}`,
    plan,
    amount: plans[plan].amount,
    currency: "usd",
    note: "Stripe stub — connect your keys in .env",
  });
});
''',
        ".env.example": """SECRET_KEY=change-me-to-random
JWT_EXPIRE_HOURS=24
DATABASE_PATH=app.db
STRIPE_SECRET_KEY=sk_test_...
CORS_ORIGINS=http://localhost:3000
""",
        ".gitignore": "node_modules/\ndist/\n.env\n*.db\n",
        "README.md": """# {{name}}

## SaaS API (Express + TypeScript) — Generated by SAISA

### Quick Start

```bash
npm install
cp .env.example .env
npm run dev
```

### API

| Endpoint | Method | Description |
|----------|--------|-------------|
| `/api/auth/register` | POST | Register |
| `/api/auth/login` | POST | Login |
| `/api/users/me` | GET | Profile |
| `/api/payments/create-checkout` | POST | Payment |
| `/health` | GET | Health |
""",
    }
