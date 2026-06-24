# Gotchas técnicos

Decisiones no-obvias y bugs encontrados que no califican como ADRs
pero vale la pena tener documentados.

---

## Starlette 1.x — API de `TemplateResponse` cambió

**Versión afectada:** Starlette >= 1.0.0 (el proyecto usa 1.3.1)

**Síntoma:**

```bash
TypeError: cannot use 'tuple' as a dict key (unhashable type: 'dict')
El error explota dentro del cache de Jinja2 al intentar renderizar
cualquier template.
```

**Causa:**
La firma de `TemplateResponse` cambió entre 0.x y 1.x.

```python
# Starlette 0.x — name primero, context con "request" adentro
templates.TemplateResponse("index.html", {"request": request, "posts": posts})

# Starlette 1.x — request primero, context sin "request"
templates.TemplateResponse(request, "index.html", {"posts": posts})
```

En 1.x, pasar el template name como primer argumento hace que Starlette
interprete el dict del context como el `name`. Jinja2 intenta usarlo
como clave del cache y falla.

**Fix:** `request` como primer argumento, `"request"` fuera del context dict.
Starlette 1.x inyecta `request` y `url_for` automáticamente en el contexto
del template — no hace falta pasarlos a mano.
