---
name: skillsecurity
description: Crear requisitos de seguridad web/API y un plan de verificacion continuo basado en riesgo. Usar cuando pidas auditoria de seguridad, checklist OWASP, hardening antes de release, pruebas de API, o gate de seguridad en CI/CD.
---

# SkillSecurity

Definir y ejecutar una estrategia de seguridad para aplicaciones web y APIs, desde requisitos tempranos hasta validacion pre-release.

## Objetivo
Entregar un paquete accionable de seguridad con: requisitos no funcionales, matriz de riesgo, controles tecnicos, pruebas y decision final de salida (`aprobar`, `aprobar con riesgo residual`, `bloquear`).

## Casos de uso reales (3-5)
- "Auditame este backend FastAPI contra OWASP API Top 10."
- "Necesito un checklist de seguridad para liberar mi app web."
- "Ayudame a definir requisitos de seguridad desde fase de analisis."
- "Quiero meter pruebas SAST/DAST y politica de bloqueo en CI/CD."
- "Haz un plan de hardening para Docker, secretos y autenticacion."

## Flujo recomendado
1. Delimitar alcance y activos
   - Identificar datos sensibles, endpoints criticos, roles, dependencias y entorno.
   - Clasificar impacto de negocio: confidencialidad, integridad, disponibilidad, autenticidad y no repudio.

2. Definir requisitos de seguridad tempranos (RNFS)
   - Convertir riesgos en requisitos verificables (ej. validacion de entrada, cifrado en transito/reposo, control de sesion, logs auditables).
   - Trazar cada requisito a un activo y a una amenaza concreta.

3. Modelar riesgos y priorizar
   - Usar severidad `alto/medio/bajo` combinando impacto y probabilidad.
   - Priorizar por explotabilidad y alcance de dano.
   - Marcar riesgos no mitigados como "riesgo residual".

4. Aplicar baseline de controles
   - OWASP Web/API: authn/authz robusta, validaciones server-side, rate limit, proteccion de secretos, manejo seguro de errores.
   - Datos: minimizacion, retencion definida, no exponer informacion interna.
   - Infra: hardening de imagenes/contendedores, principio de minimo privilegio, inventario de componentes.

5. Plan de verificacion continuo
   - Definir pruebas minimas: SAST, DAST, dependencia, pruebas de autorizacion por endpoint y fuzzing basico de inputs.
   - Establecer gates de release: bloquear si hay hallazgos criticos/altos sin mitigacion aceptada.
   - Guardar evidencias de prueba y trazabilidad requisito -> control -> evidencia.

6. Cerrar con decision operativa
   - Emitir estado final con justificacion y acciones pendientes.
   - Entregar backlog de remediacion por prioridad y fecha objetivo.

## Restricciones y decisiones
- Una sola responsabilidad: seguridad de aplicaciones web/API (no GRC corporativo completo).
- No proponer controles "cosmeticos"; cada control debe mapearse a una amenaza real.
- Evitar listas genericas: siempre contextualizar por stack, arquitectura y datos.
- Si falta contexto, asumir minimo privilegio, cifrado por defecto y verificacion continua.
- Nunca exponer secretos reales en ejemplos, logs o commits.

## Formato de salida esperado
1. Resumen ejecutivo (riesgos principales + decision final).
2. Matriz de riesgo (activo, amenaza, impacto, probabilidad, severidad, estado).
3. Requisitos de seguridad verificables (con criterio de aceptacion).
4. Controles implementados/recomendados (priorizados).
5. Plan de pruebas y evidencia minima.
6. Riesgo residual y plan de remediacion.

## Plantilla minima de matriz de riesgo
```md
| Activo | Amenaza | Impacto | Probabilidad | Severidad | Control | Evidencia | Estado |
|---|---|---|---|---|---|---|---|
| API de pagos | BOLA/IDOR | Alto | Medio | Alto | AuthZ por recurso + pruebas negativas | test_authz_api.py | Mitigado parcial |
```

## Ejemplos de entrada -> salida

### Ejemplo 1
Entrada:
"Revisa mi API Node y dime si puedo liberar hoy."

Salida esperada:
- 3-5 riesgos priorizados.
- checklist OWASP API aplicado.
- decision `bloquear` si existe hallazgo critico/alto sin fix.

### Ejemplo 2
Entrada:
"Define RNF de seguridad para mi nuevo sistema de RRHH."

Salida esperada:
- RNFS trazables por confidencialidad, integridad, disponibilidad, autenticidad y no repudio.
- criterios de aceptacion por requisito.
- plan de pruebas por requisito.

### Ejemplo 3
Entrada:
"Integra seguridad continua en mi pipeline."

Salida esperada:
- secuencia de jobs SAST/DAST/SCA.
- umbrales de bloqueo por severidad.
- artefactos de evidencia para auditoria.

## Checklist final
- [ ] La skill mantiene una sola responsabilidad (seguridad web/API).
- [ ] Hay requisitos verificables y trazables desde etapas tempranas.
- [ ] Se aplica priorizacion por riesgo (impacto x probabilidad).
- [ ] Incluye controles OWASP web/API y manejo de datos sensibles.
- [ ] Define pruebas continuas y gate de release.
- [ ] Emite decision final y riesgos residuales explicitos.

## Base conceptual utilizada
- Requisitos de seguridad tempranos y trazabilidad durante el ciclo de vida.
- Principios de confidencialidad, integridad, disponibilidad, autenticidad y no repudio.
- Enfoque combinado de habilidades tecnicas + operacion continua en ciberseguridad.
- Entrenamiento practico orientado a OWASP API Top 10 y priorizacion por riesgo.
