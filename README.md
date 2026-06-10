# Calendario Mundial 2026

Template para generar un calendario `.ics` con los partidos del Mundial 2026 y compartirlo por QR.

## Idea

No conviene meter todos los eventos directamente dentro de un QR. El QR debe apuntar a una URL publica donde este el archivo `.ics`.

Flujo recomendado:

1. Descargar/actualizar partidos:

   ```bash
   python3 scripts/fetch_matches.py
   ```

2. Generar calendario:

   ```bash
   python3 scripts/build_calendar.py
   ```

3. Subir `dist/world-cup-2026.ics` a una URL publica.

4. Abrir `qr.html` y usar el QR resultante.

URL esperada en GitHub Pages:

```text
https://franja24.github.io/calendar_world_cup.github.io/dist/world-cup-2026.ics
```

## Archivos

- `data/matches.csv`: base de partidos normalizada.
- `scripts/fetch_matches.py`: descarga datos desde ESPN.
- `scripts/build_calendar.py`: crea `dist/world-cup-2026.ics`.
- `qr.html`: generador simple de QR para la URL publica del calendario.

## Notas

- El calendario usa horas UTC; iPhone, Android y Google Calendar las convierten a la zona horaria local del usuario.
- FIFA marca el calendario como sujeto a cambios. Si cambian horarios o sedes, vuelve a correr los scripts y reemplaza el `.ics`.
- Para actualizaciones automaticas reales, lo ideal es publicar siempre el mismo URL del `.ics`, no mandar archivos sueltos por WhatsApp.
