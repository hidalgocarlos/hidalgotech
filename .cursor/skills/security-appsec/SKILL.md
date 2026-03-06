---
name: security-appsec
description: Definir y ejecutar controles de seguridad de aplicacion para stacks con Docker, APIs, Next.js/React, Node.js y Python/FastAPI. Usar cuando se necesite prevenir vulnerabilidades OWASP, hardening de contenedores, gestion de secretos, autenticacion/autorizacion, validacion de dependencias, o gate de seguridad antes de desplegar.
---

# Security AppSec

Aplicar una base de seguridad pragmatica y verificable antes de liberar cambios.

## Flujo

1. Identificar activos criticos, actores y superficies de ataque.
2. Levantar riesgos por probabilidad e impacto (alto, medio, bajo).
3. Aplicar baseline OWASP para API y frontend.
4. Revisar secretos, variables de entorno y llaves de servicio.
5. Hardening de Docker e imagenes base.
6. Definir controles obligatorios de CI/CD para release.
7. Emitir checklist final de aprobacion o bloqueo.

## Checklist minimo

- [ ] No hay secretos en repo, logs ni cliente.
- [ ] AuthN/AuthZ definidos por endpoint y recurso.
- [ ] Validacion de entrada y manejo de errores sin fuga de datos.
- [ ] Dependencias sin vulnerabilidades criticas conocidas.
- [ ] Contenedores corren con usuario no-root y permisos minimos.
- [ ] CORS, headers y rate limit documentados.
- [ ] Existe criterio de bloqueo de despliegue por riesgo alto.

## Entregable

Generar una matriz de riesgo + controles aplicados + riesgos residuales con decision final: `aprobar` o `bloquear`.
