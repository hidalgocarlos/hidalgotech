# Seguridad — Portal ToolBox Pro

Resumen de controles aplicados y criterios de release (skillsecurity + security-appsec).

## Resumen ejecutivo

- **Decisión**: **Aprobar** para despliegue, con riesgo residual documentado.
- Controles OWASP aplicados: cabeceras, CSP, HSTS, CSRF, rate limit, política de contraseñas, no cache en rutas sensibles.
- Contenedor corre como usuario no-root; `SECRET_KEY` obligatorio en producción.

## Matriz de riesgo (resumen)

| Activo            | Amenaza        | Impacto | Prob. | Severidad | Control                                      | Estado        |
|-------------------|----------------|---------|-------|-----------|----------------------------------------------|---------------|
| Login / sesión    | Fuerza bruta   | Alto    | Medio  | Alto      | Rate limit login (5 intentos / 15 min)        | Mitigado      |
| Formularios       | CSRF           | Alto    | Medio  | Alto      | Token CSRF en cookie + formularios           | Mitigado      |
| Respuestas        | Clickjacking   | Medio   | Bajo   | Bajo      | X-Frame-Options, CSP frame-ancestors         | Mitigado      |
| Datos en tránsito | MitM           | Alto    | Bajo   | Medio     | HTTPS (Traefik), HSTS, cookie secure         | Mitigado      |
| Contraseñas       | Débiles        | Alto    | Medio  | Alto      | Mínimo 8 caracteres en crear/cambiar/reset   | Mitigado      |
| Páginas sensibles | Cache en cliente | Medio | Bajo   | Bajo      | Cache-Control no-store en /dashboard, /admin, /api | Mitigado  |
| Abuso general     | DoS / scraping | Medio  | Medio  | Medio     | Rate limit global 200 req/5 min por IP       | Mitigado      |
| Secretos          | Fuga en repo   | Alto    | Bajo   | Alto      | SECRET_KEY por env; .env no en git           | Mitigado      |
| Contenedor        | Escalada       | Alto    | Bajo   | Medio     | Usuario no-root (appuser) en Dockerfile      | Mitigado      |

## Checklist mínimo (security-appsec)

- [x] No hay secretos en repo, logs ni cliente.
- [x] AuthN/AuthZ definidos por endpoint (verify_token, require_admin).
- [x] Validación de entrada y manejo de errores sin fuga de datos (mensajes genéricos en login).
- [x] Dependencias sin vulnerabilidades críticas conocidas (revisar con `pip-audit` / CI).
- [x] Contenedores corren con usuario no-root y permisos mínimos.
- [x] Cabeceras de seguridad (CORS implícito vía mismo origen; rate limit documentado aquí).
- [x] Criterio de bloqueo: no desplegar si SECRET_KEY por defecto en producción o contraseña admin débil.

## Requisitos no funcionales de seguridad (RNFS) aplicados

1. **Integridad**: validación de entrada (trim, longitud mínima de contraseña); CSRF en todos los POST de formularios.
2. **Confidencialidad**: cookie de sesión HttpOnly, Secure en HTTPS, SameSite=Lax; Cache-Control no-store en rutas sensibles.
3. **Disponibilidad**: rate limit global y rate limit en login para mitigar abuso.
4. **Autenticidad**: JWT con SECRET_KEY obligatorio en producción; contraseñas con bcrypt.
5. **No repudio**: logs de aplicación (si se añaden auditorías, mantener trazabilidad).

## Plan de verificación

- **Pre-release**: Cambiar `DEFAULT_ADMIN_PASSWORD` y `SECRET_KEY` en producción; no usar valores de `.env.example`.
- **CI**: Ejecutar `pip-audit` (ver `.github/workflows/pip-audit.yml` si existe).
- **Manual**: Comprobar que login rechaza tras 5 intentos; que formularios sin CSRF devuelven 403; que /admin exige rol admin.

## Riesgo residual y remediación

| Riesgo residual                    | Prioridad | Acción recomendada                          |
|------------------------------------|-----------|---------------------------------------------|
| SECRET_KEY o admin por defecto     | Alta      | Variables de entorno obligatorias en deploy  |
| Dependencias con CVE               | Alta      | pip-audit en CI y parcheo antes de release  |
| Sin invalidación server-side de JWT | Media   | Opcional: blacklist de tokens en logout     |

---

*Documento generado aplicando skillsecurity. Actualizar al añadir nuevos endpoints o controles.*
