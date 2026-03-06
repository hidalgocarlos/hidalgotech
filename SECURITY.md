# Seguridad AppSec — ToolBox Pro

Evaluación según política security-appsec: activos, riesgos, controles OWASP, hardening y criterio de bloqueo.

---

## 1. Activos críticos, actores y superficies de ataque

| Activo | Descripción | Actores | Superficie |
|--------|-------------|---------|------------|
| Portal (login, dashboard, admin) | Autenticación, sesiones, gestión de usuarios | Usuarios, admins, atacantes | `/`, `/login`, `/admin`, `/api/rates` |
| Apps (TikTok, Instagram, etc.) | Funcionalidad por app, JWT compartido | Usuarios autenticados | Endpoints por app |
| Bases de datos SQLite | Usuarios, historiales, enlaces | Backend | Archivos `*.db` en volúmenes |
| Secretos | SECRET_KEY JWT, contraseñas hasheadas | Backend, env | Variables de entorno, BD |

---

## 2. Matriz de riesgo (probabilidad × impacto)

| ID | Riesgo | Prob. | Impacto | Nivel | Mitigación |
|----|--------|-------|---------|------|------------|
| R1 | SECRET_KEY en código por defecto | Media | Alto | **Alto** | SECRET_KEY desde env; en producción falla si no está definida |
| R2 | Contraseñas en logs | Baja | Alto | Medio | Eliminado: startup ya no imprime contraseña |
| R3 | Cookie sin flags seguros | Media | Medio | Medio | Cookie: httponly, secure (prod), samesite=lax, path=/, max_age |
| R4 | Fuerza bruta en login | Media | Medio | Medio | Rate limit: 5 intentos / IP, bloqueo 15 min |
| R5 | Contenedores como root | Media | Medio | Medio | USER appuser (UID 1000) en todos los Dockerfile |
| R6 | Clickjacking / MIME sniffing | Baja | Bajo | Bajo | Headers: X-Frame-Options, X-Content-Type-Options, Referrer-Policy |
| R7 | Dependencias vulnerables | Baja | Alto | Medio | Revisión manual; en CI se puede añadir `pip audit` |
| R8 | Datos sensibles en cliente | Baja | Medio | Bajo | JWT en cookie httponly; no se exponen secretos en HTML/JS |

---

## 3. Controles aplicados (baseline OWASP + checklist)

| # | Control | Estado |
|---|---------|--------|
| 1 | **No secretos en repo/logs/cliente** | ✅ .gitignore (.env, data, acme.json); SECRET_KEY solo desde env; startup no imprime contraseña |
| 2 | **AuthN/AuthZ por endpoint** | ✅ Login público; resto requiere verify_token; admin requiere require_admin |
| 3 | **Validación de entrada y errores** | ✅ Form con strip/validación; mensajes genéricos ("Credenciales inválidas"); no se filtra información sensible en errores |
| 4 | **Dependencias** | ⚠️ Sin pip audit en CI; revisión manual. Criterio de bloqueo: vulnerabilidades críticas sin parche = bloquear |
| 5 | **Contenedores no-root** | ✅ Todos los Dockerfile: USER appuser (1000), EXPOSE documentado |
| 6 | **CORS, headers y rate limit** | ✅ Headers: X-Frame-Options, X-Content-Type-Options, Referrer-Policy, Permissions-Policy. Rate limit solo en POST /login (5/15 min). CORS: no API pública cross-origin; mismo origen para portal y apps |
| 7 | **Criterio de bloqueo** | ✅ No desplegar si: SECRET_KEY por defecto en producción, vulnerabilidades críticas en dependencias, o fallos en tests de seguridad |

---

## 4. Riesgos residuales y decisión

| Riesgo residual | Nivel | Aceptación |
|-----------------|-------|------------|
| Dependencias sin escaneo automático en CI | Medio | Aceptado; añadir `pip audit` en pipeline recomendado |
| SQLite sin cifrado en reposo | Bajo | Aceptado para este contexto; opcional cifrado FS o BD externa |
| Rate limit solo en login (no en API global) | Bajo | Aceptado; API /api/rates requiere JWT |

---

## 5. Checklist final de aprobación

- [x] No hay secretos en repo, logs ni cliente.
- [x] AuthN/AuthZ definidos por endpoint y recurso.
- [x] Validación de entrada y manejo de errores sin fuga de datos.
- [x] Dependencias: sin auditoría automática; criterio = bloquear si hay críticas conocidas.
- [x] Contenedores corren con usuario no-root y permisos mínimos.
- [x] CORS, headers y rate limit documentados (este documento + DEPLOY.md).
- [x] Existe criterio de bloqueo de despliegue por riesgo alto.

---

## Decisión final

**APROBAR** despliegue en local y posterior push a git, con la condición de que en **producción** se definan siempre `SECRET_KEY` y contraseñas de admin vía variables de entorno (ver DEPLOY.md y .env.example).

**Criterio de bloqueo para futuros releases:**  
No hacer release si existe vulnerabilidad crítica conocida en dependencias sin mitigación o si SECRET_KEY sigue siendo el valor por defecto en entorno de producción.
