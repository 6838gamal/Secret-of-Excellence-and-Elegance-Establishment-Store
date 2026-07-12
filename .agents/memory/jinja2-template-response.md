---
name: FastAPI Jinja2 TemplateResponse signature
description: Starlette 0.36+ changed TemplateResponse to take request as first positional arg
---

## Rule
Use `templates.TemplateResponse(request, "template.html", {...context without request...})` — NOT the old `templates.TemplateResponse("template.html", {"request": request, ...})`.

**Why:** Starlette 0.36+ changed the signature. Passing a dict as the second positional arg causes `TypeError: unhashable type: 'dict'` inside Jinja2's LRU cache because the dict gets used as a cache key.

**How to apply:** Always put `request` as first arg and the context dict (without `request`) as the third arg when using Jinja2Templates in FastAPI projects.
