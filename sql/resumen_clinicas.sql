-- Resumen de cada clínica guardada en la nube (PostgreSQL en Neon).
--
-- Cómo usarla, en Neon → SQL Editor (solo lee datos, no cambia nada):
--   1. Ejecuta esta consulta. Devuelve una sola celda, "consulta_resumen", con otra consulta.
--      (Cada clínica tiene su propio esquema, clinica_1, clinica_2..., por eso hace falta este paso.)
--   2. Copia el contenido de esa celda, pégalo en el editor y ejecútalo.
--      Sale una fila por clínica: primero las reales y después las demos.
--
-- Columnas del resumen:
--   clinica, tipo (real o demo), pacientes, doctores_activos, citas,
--   citas_pendientes (programadas de hoy en adelante), usuarios_activos,
--   ultimo_uso (en UTC; se actualiza como mucho una vez por hora).
--
-- Si se crea una clínica nueva, vuelve a hacer el paso 1.

SELECT string_agg(format(
    $$SELECT %L AS clinica, %L AS tipo,
       (SELECT count(*) FROM %I.pacientes) AS pacientes,
       (SELECT count(*) FROM %I.doctores WHERE activo = 1) AS doctores_activos,
       (SELECT count(*) FROM %I.citas) AS citas,
       (SELECT count(*) FROM %I.citas WHERE estado = 'programada' AND fecha >= to_char(current_date, 'YYYY-MM-DD')) AS citas_pendientes,
       (SELECT count(*) FROM %I.usuarios WHERE activo = 1) AS usuarios_activos,
       %L AS ultimo_uso$$,
    nombre, CASE WHEN temporal THEN 'demo' ELSE 'real' END,
    esquema, esquema, esquema, esquema, esquema,
    to_char(ultimo_uso, 'YYYY-MM-DD HH24:MI')),
  E'\nUNION ALL\n' ORDER BY temporal, nombre) || ';' AS consulta_resumen
FROM public.clinicas
WHERE esquema IS NOT NULL;
