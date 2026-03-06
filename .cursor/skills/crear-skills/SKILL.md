---
name: crear-skills
description: Crear o mejorar skills de Cursor en `.cursor/skills/<nombre>/SKILL.md` con frontmatter YAML (`name`, `description`) e instrucciones Markdown claras. Usar cuando pidan disenar una skill nueva, refactorizar una skill existente, definir activadores en la descripcion, o estructurar recursos auxiliares como `scripts/`, `templates/` y `examples/`.
---

# Crear Skills de Cursor

Definir skills enfocadas, reutilizables y faciles de activar.

## Flujo

1. Definir el objetivo en una frase y 3-5 ejemplos reales de uso.
2. Elegir un nombre corto en kebab-case y crear la carpeta en `.cursor/skills/<nombre>/`.
3. Escribir frontmatter minimo en `SKILL.md`:
   - `name`: identificador en kebab-case.
   - `description`: que hace la skill y cuando usarla (esto activa el descubrimiento).
4. Redactar el cuerpo en Markdown con pasos accionables:
   - flujo recomendado;
   - restricciones y decisiones;
   - ejemplos de entrada/salida;
   - checklist final.
5. Agregar solo recursos necesarios:
   - `scripts/` para tareas repetitivas o deterministas;
   - `templates/` para base reutilizable;
   - `examples/` para patrones concretos.
6. Probar la skill con 2-3 prompts reales y ajustar descripcion o pasos si activa mal o responde ambiguo.

## Plantilla base

```md
---
name: mi-skill
description: Que hace la skill y cuando usarla, con palabras que el usuario realmente diria.
---

# Titulo de la skill

## Objetivo
Definir el resultado esperado.

## Pasos
1. ...
2. ...

## Checklist
- [ ] Cumplir formato y rutas de Cursor.
- [ ] Incluir ejemplos reales.
- [ ] Evitar instrucciones ambiguas.
```

## Criterios de calidad

- Mantener una sola responsabilidad por skill.
- Escribir instrucciones concretas, no teoria extensa.
- Priorizar terminos de activacion en `description`.
- Evitar archivos innecesarios fuera de `SKILL.md` y recursos utiles.
- Preferir iteracion rapida: crear, probar, ajustar.
