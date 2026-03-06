---
name: rag-pipeline-eval
description: Disenar, auditar y evaluar pipelines RAG con foco en calidad, seguridad y costo. Usar cuando se defina ingestion, chunking, metadata, retrieval, guardrails, evaluacion de alucinaciones, control de fuga de datos, o criterios de release para sistemas con RAG.
---

# RAG Pipeline Eval

Asegurar respuestas utiles, citables y seguras antes de produccion.

## Flujo

1. Definir casos de uso, fuentes permitidas y datos restringidos.
2. Establecer estrategia de ingestion, chunking y versionado documental.
3. Disenar retrieval con filtros por tenant, rol y contexto.
4. Definir guardrails de seguridad y politicas de respuesta.
5. Crear set de evaluacion con casos positivos, ambiguos y adversariales.
6. Medir precision, cobertura, alucinacion, latencia y leakage.
7. Decidir liberar o bloquear por umbrales acordados.

## Checklist minimo

- [ ] Documentos con metadata util para filtros de acceso.
- [ ] Retrieval respeta aislamiento por tenant/rol.
- [ ] Respuestas incluyen evidencia o citas cuando aplique.
- [ ] Alucinaciones medidas con set representativo.
- [ ] Fuga de PII o datos sensibles evaluada explicitamente.
- [ ] Umbrales minimos definidos antes de pruebas.
- [ ] Existe plan de monitoreo continuo post-release.

## Entregable

Generar reporte con metricas, fallas criticas, recomendaciones y estado final: `listo` o `no listo`.
