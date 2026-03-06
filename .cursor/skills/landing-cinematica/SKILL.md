---
name: landing-cinematica
description: Genera una landing page cinematográfica "1:1 Píxel Perfecto" para cualquier tipo de negocio usando React 19, Tailwind CSS y GSAP. El agente hace 8 preguntas de personalización (marca, paleta, hero, dashboard, manifiesto, colección, planes y footer). Usar cuando el usuario quiera crear una web premium, cinematográfica o de alto impacto visual.
---

# Landing Cinematográfica — 1:1 Píxel Perfecto

Esta skill construye una landing page de nivel _world-class_ para **cualquier tipo de negocio**. En lugar de pedir al usuario que rellene `{llaves}` manualmente, el agente realiza **8 preguntas estratégicas** que cubren cada variable del prompt maestro, y luego inyecta las respuestas para producir un sitio 100% personalizado.

---

## Cuando usar esta skill

- El usuario quiere crear una landing page premium, cinematográfica, de alto impacto visual o de lujo para cualquier tipo de negocio o marca.
- El usuario menciona: "landing page", "web cinematográfica", "web para mi negocio", "landing premium", "quiero una web de nivel mundial", "pixel perfect".

---

## Prerequisites

- Node.js instalado en el sistema.
- Acceso a Internet para cargar Google Fonts e imágenes de Unsplash.
- El usuario debe tener un directorio de trabajo activo.

---

## Instrucciones

### FASE 1 — Entrevista de personalización (OBLIGATORIA)

**Antes de escribir una sola línea de código**, el agente DEBE presentar las siguientes 8 preguntas en un único mensaje claro y estructurado, para que el usuario pueda responderlas todas de una vez.

Usa exactamente este bloque de apertura y preguntas:

---

> **Vamos a construir tu landing page cinematográfica.**
>
> Responde estas 8 preguntas y ajustaré cada detalle del diseño a tu marca. Cuanto más detalle des, más fiel al resultado ideal será el sitio. Puedes ser breve o extenderte.
>
> ---
>
> **1. Tu negocio y su esencia**
> - ¿Cómo se llama tu negocio?
> - ¿En una frase, qué hace o vende? (Ejemplo: _"Estudio de tatuajes de fine-line en Madrid"_ / _"Cafetería de especialidad con granos de origen único"_)
>
> **2. Identidad estética y referencias**
> - ¿Cómo definirías el "universo visual" de tu marca con 2 conceptos? (Ejemplo: _"Minimalismo Japonés" / "Ritual Industrial"_)
> - ¿Entre qué dos mundos o referencias está tu marca? (Ejemplo: _"entre un laboratorio de arte y una galería de moda contemporánea"_)
>
> **3. Paleta de colores**
> ¿Tienes una paleta definida? Si es así, dime el nombre y código hex de estos 4 roles:
> - **Principal** (color dominante, fondos oscuros o elementos clave)
> - **Acento** (botones, detalles, llamadas a la acción)
> - **Fondo** (color base de la web, suele ser claro o muy oscuro)
> - **Texto** (color principal de los textos y secciones oscuras)
>
> Si no tienes paleta, descríbeme la sensación general (_"quiero algo oscuro y dorado"_, _"azul eléctrico y negro"_, _"tierra y crema"_) y la crearé yo.
>
> **4. Sección Hero (portada)**
> Esto es lo primero que verá cada visitante, ocupa toda la pantalla:
> - ¿Cuál es el **titular principal**? Dímelo en dos partes: la primera en fuente Sans (sobria) y la segunda en fuente Serif Itálica (elegante). (Ejemplo: _Parte 1: "El arte de lo"_ / _Parte 2: "permanente."_)
> - ¿Cuál es el **tagline** corto tipo código? (Ejemplo: _"// Diseño único. Piel como lienzo."_)
> - ¿Cuál es el **texto del botón CTA** principal? (Ejemplo: _"Reserva tu sesión"_)
> - ¿Qué **tipo de imagen** describe mejor el ambiente de tu negocio? (Ejemplo: _"manos trabajando sobre piel"_, _"granos de café en luz cálida"_, _"ropa colgada en estudio industrial"_). Yo buscaré una URL de Unsplash adecuada.
>
> **5. Dashboard interactivo (sección de características)**
> Esta sección muestra 3 tarjetas animadas que parecen software real:
> - ¿Cómo se llama este bloque temáticamente? (Ejemplo: _"Sala de Control del Estudio"_, _"Dashboard del Barista"_)
> - **Tarjeta 1 — Clasificador**: ¿Qué 3 elementos o servicios quieres que roten y aparezcan? (Ejemplo: _"Fine-Line · Realismo · Acuarela"_ / _"Espresso · Cortado · Pour Over"_)
> - **Tarjeta 2 — Feed en vivo**: ¿Qué 3 mensajes de proceso quieres que se escriban solos? Y ¿qué estado "en tiempo real" mostrar? (Ejemplo mensajes: _"Preparando mezcla del día..."_, _"Calibrando temperatura de extracción..."_ / Estado: _"Sala Abierta"_)
> - **Tarjeta 3 — Protocolo semanal**: ¿Qué texto tendrá el botón final de esa tarjeta? (Ejemplo: _"Confirmar Reserva"_, _"Ver Disponibilidad"_)
>
> **6. Manifiesto (sección de filosofía)**
> Esta sección es oscura, contundente y emociona. Contrasta tu marca con la competencia genérica:
> - **Frase del "sector convencional"**: ¿Qué pregunta o afirmación haría tu competencia mediocre? (Ejemplo: _"La competencia pregunta: ¿Cuánto dura el efecto?"_)
> - **Contrapropuesta tuya**: ¿Cuál es tu respuesta diferencial? (Ejemplo: _"Nosotros preguntamos: ¿Cuenta tu historia?"_)
> - **Valores en una línea**: 3 valores de tu marca separados por ` · ` (Ejemplo: _"Sin atajos · Hecho a mano · Con propósito"_)
>
> **7. Colección de servicios o productos**
> Esta sección muestra 3 tarjetas a pantalla completa que se apilan una sobre otra al hacer scroll:
> - ¿Cuáles son tus **3 servicios o productos estrella**? Para cada uno dime:
>   - Nombre
>   - Descripción de 1-2 frases
>   - ¿Qué *sensación visual* quieres en esa tarjeta? (Ejemplo: _"algo que evoque precisión y filo"_, _"calor y vapor"_, _"fluidez y movimiento"_). Usaré esta descripción para crear un SVG animado único.
>
> **8. Planes / Suscripción + Footer**
> - ¿Tienes **planes de precio o membresía**? Si es así, dime el nombre y beneficio clave de cada uno (3 niveles). Si no tienes, pasaré a mostrar sección de newsletter VIP.
> - **Footer**: ¿Qué **4 enlaces** de utilidad quieres en el pie de página? (Ejemplo: _"Portafolio, Blog, Preguntas, Contacto"_)
> - ¿Cuál es el **estado operativo** que debe mostrar la web en tiempo real? (Ejemplo: _"Estudio Activo"_, _"Tienda Abierta"_, _"Producción en Curso"_)
> - ¿Dirección, email o redes sociales para el footer?

---

### FASE 2 — Validación de respuestas

Una vez el usuario responda, el agente DEBE:

1. **Construir internamente la lista completa** de todas las variables `{llave}` del prompt maestro, asignando el valor correcto a cada una según las respuestas.
2. Para las variables que el usuario no haya especificado (colores, URLs de Unsplash, animaciones SVG), el agente las **inferirá y decidirá** de forma creativa y coherente con la identidad de la marca.
3. Presentar un **resumen visual** al usuario en forma de tabla o lista clara antes de proceder.
4. Preguntar: *"¿Todo correcto? ¿Empezamos a construir?"*

Ejemplo de resumen:

> **Aquí tienes el blueprint de tu landing antes de construir:**
>
> | Variable | Valor |
> |---|---|
> | Nombre del negocio | [respuesta] |
> | Descripción | [respuesta] |
> | Concepto estético | [respuesta] |
> | Color principal | [hex] |
> | Color acento | [hex] |
> | Titular Hero (parte 1) | [respuesta] |
> | Titular Hero (parte 2, serif) | [respuesta] |
> | CTA | [respuesta] |
> | Imagen Hero (URL inferida) | [URL Unsplash] |
> | Servicios/Productos | [lista] |
> | Planes | [lista] |
> | ... | ... |

---

### FASE 3 — Construcción del proyecto

Con todas las variables mapeadas y confirmadas, el agente ejecuta el siguiente prompt maestro **con todos los `{placeholders}` sustituidos por valores reales** para construir el sitio.

#### 3.1 — Inicializar el proyecto

```bash
npx -y create-vite@latest ./ --template react
npm install
npm install gsap lucide-react
npm install -D tailwindcss@3 postcss autoprefixer
npx tailwindcss init -p
```

Configurar `tailwind.config.js` para incluir los colores de la marca como tokens custom, las tipografías, y border-radius extendidos (`2rem`, `3rem`, `4rem`).

#### 3.2 — Prompt maestro a ejecutar (con variables ya sustituidas)

El agente debe construir la landing implementando **todos** estos componentes con los valores reales del usuario:

##### SISTEMA DE DISEÑO

- **Paleta:** 4 colores del usuario (Principal, Acento, Fondo, Texto).
- **Tipografías (Google Fonts):** Plus Jakarta Sans, Outfit, Cormorant Garamond (Itálica), JetBrains Mono — importar desde Google Fonts en `index.html`.
- **Textura visual:** Capa de ruido CSS con turbulencia SVG a 0.05 de opacidad en `body`. `border-radius` entre `2rem` y `3rem` en todos los contenedores.

##### COMPONENTES A CONSTRUIR

**A. NAVBAR — Isla Flotante**

- Fijo, forma de píldora, centrado.
- Estado inicial: transparente, texto blanco.
- Al scroll > 50px: glassmorphic blanco/60, borde sutil, texto en color principal.
- Logo: nombre del negocio de la respuesta 1.

**B. HERO**

- `100dvh`. Imagen Unsplash de fondo con overlay gradiente pesado (color principal → negro).
- Contenido en el tercio inferior-izquierdo.
- Titular en dos tipografías: Sans Bold (parte 1) + Cormorant Garamond Itálica Masiva (parte 2).
- Tagline en monospace.
- Botón CTA magnético con `overflow-hidden` y capa deslizante de color al hover.
- GSAP `fade-up` escalonado con `gsap.context()` en `useEffect`.

**C. DASHBOARD INTERACTIVO**

- Tres tarjetas estilo software real, en grid `1 col md:3 cols`.
- **Tarjeta 1 — Clasificador:** 3 elementos que ciclan verticalmente cada 3s usando `cubic-bezier(0.34, 1.56, 0.64, 1)`.
- **Tarjeta 2 — Feed en vivo:** Mensajes que se escriben solos ciclando, cursor parpadeante en color acento, punto pulsante con estado actual.
- **Tarjeta 3 — Protocolo semanal:** Grid D L M X J V S, días resaltados programáticamente, botón final configurado.

**D. MANIFIESTO**

- Sección fondo "texto" (color oscuro), imagen Unsplash con paralaje (GSAP ScrollTrigger).
- Tipografía gigante: frase de sector convencional vs. contrapropuesta de la marca.
- Tercera línea monospace con los valores separados por ` · `.
- Texto split reveal con ScrollTrigger.

**E. COLECCIÓN DE SERVICIOS (Sticky Stack)**

- 3 tarjetas `100vh` apiladas. Con ScrollTrigger: al entrar, la tarjeta inferior pasa a `scale(0.9)`, `blur(20px)`, `opacity(0.5)`.
- Cada tarjeta tiene: número de experiencia, nombre grande (Sans + Cormorant itálica), descripción, botón y un artefacto SVG animado único que evoca visualmente el servicio.

**F. PLANES / NEWSLETTER + FOOTER**

- Si hay planes: grid de 3 tarjetas, la del centro destacada con fondo en color principal y botón en color acento.
- Si no hay planes: sección de newsletter/círculo VIP con input email animado + botón.
- Footer: fondo texto profundo, `rounded-t-[4rem]`, 4 enlaces de utilidad, contacto/redes, indicador de estado operativo con punto verde pulsante y texto monospace.

##### REQUISITOS TÉCNICOS

- **Stack obligatorio:** React 19, Tailwind CSS v3, GSAP 3 con ScrollTrigger, Lucide React.
- **Todas las animaciones** dentro de `gsap.context()` con limpieza en el `return` del `useEffect`.
- **Micro-interacciones:** Botones con hover magnético (`scale(1.03)`), transición de color de fondo deslizante con `overflow-hidden`.
- **Sin placeholders.** Todas las URLs de Unsplash deben ser reales y temáticamente coherentes con la marca.
- **Responsive mobile-first:** Adaptar grids de 3 columnas a 1 columna en móvil. El Sticky Stack funciona en todos los tamaños.
- **Accesibilidad:** `prefers-reduced-motion` debe desactivar las animaciones GSAP si el usuario lo tiene activo.

#### 3.3 — Arrancar el servidor de desarrollo

```bash
npm run dev
```

Confirmar que el sitio carga en `http://localhost:5173` sin errores en consola.

---

### FASE 4 — Entrega

Al finalizar, el agente DEBE:

1. Mostrar la URL local: normalmente `http://localhost:5173`.
2. Listar los archivos creados con una breve descripción de cada uno (para usuarios con menos experiencia).
3. Ofrecer rondas de ajuste: colores, copy, nuevas secciones, micro-interacciones adicionales.

---

## Notas y casos especiales

- **Paleta no definida:** Si el usuario describe solo una sensación ("quiero algo oscuro y dorado"), el agente elige los 4 colores hex de forma coherente con esa descripción y los indica en el resumen de la Fase 2.
- **URLs de Unsplash:** El agente busca e inserta URLs reales con `?q=80&w=2600&auto=format&fit=crop` para calidad óptima. Nunca usar URLs inventadas.
- **Solo 2 servicios:** La tercera tarjeta de la colección muestra una sección "Próximamente" con estética coherente.
- **Sin planes de precio:** Sustituir la sección de planes por un módulo de newsletter/lista VIP de alta conversión.
- **Animaciones SVG:** Cada artefacto de la colección debe ser único y relacionado con la sensación visual descrita por el usuario. No repetir el mismo SVG en distintas tarjetas.
- El sitio no es solo una web; es **un ritual digital**. Cada interacción debe percibirse como una extensión de la experiencia real del negocio.
