---
name: bcrypt passlib incompatibility
description: passlib's bcrypt backend is broken with bcrypt v4+ (missing __about__ attribute)
---

## Rule
Do NOT use `passlib[bcrypt]` for password hashing. Use the `bcrypt` package directly.

```python
import bcrypt

def hash_password(password: str) -> str:
    return bcrypt.hashpw(password.encode("utf-8"), bcrypt.gensalt()).decode("utf-8")

def verify_password(plain: str, hashed: str) -> bool:
    return bcrypt.checkpw(plain.encode("utf-8"), hashed.encode("utf-8"))
```

**Why:** bcrypt v4+ removed `__about__` module. passlib's `_load_backend_mixin` reads `_bcrypt.__about__.__version__` and crashes. The `detect_wrap_bug` call then fails with `ValueError: password cannot be longer than 72 bytes` on a test password.

**How to apply:** Always use bcrypt directly in any FastAPI/Python project on Replit.
