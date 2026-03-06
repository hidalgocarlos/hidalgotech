---
name: supabase-auth-rls
description: Disenar y validar autenticacion, autorizacion y Row Level Security en Supabase. Usar cuando se definan roles, politicas RLS por tabla, manejo de claves (`anon` y `service_role`), flujo de migraciones, o pruebas de acceso para evitar exposicion de datos.
---

# Supabase Auth RLS

Implementar acceso minimo necesario, trazable y seguro para cada rol.

## Flujo

1. Definir roles de negocio y capacidades por rol.
2. Mapear recursos (tablas, vistas, storage) y acciones permitidas.
3. Traducir matriz rol-recurso-accion a politicas RLS explicitas.
4. Separar uso de claves cliente/backend y entorno.
5. Validar escenarios de acceso permitido y denegado.
6. Revisar migraciones y rollback de politicas.
7. Publicar decision final con riesgos residuales.

## Checklist minimo

- [ ] Cada tabla sensible tiene RLS habilitado.
- [ ] Politicas separan lectura y escritura por rol.
- [ ] `service_role` solo se usa en backend confiable.
- [ ] Cliente usa unicamente clave `anon`.
- [ ] No hay bypass de politicas por funciones inseguras.
- [ ] Casos negativos (acceso denegado) probados.
- [ ] Cambios versionados con migracion reproducible.

## Entregable

Generar matriz `rol -> recurso -> permisos` + resumen de politicas RLS + resultado de pruebas de acceso.
