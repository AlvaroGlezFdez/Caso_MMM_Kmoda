# Memoria del Proyecto - K-Moda MMM
Fecha de inicio: 2026-04-22

## 1. Decisiones de diseno
- Granularidad: semanal nacional (todas las ciudades sumadas)
- Raiz: semanas de inversion_medios_semanal (semana_inicio, semana_fin, anio, semana_iso)
- JOINs: siempre LEFT JOIN, nunca INNER JOIN
- Variable dependiente: venta_neta_sin_iva_eur (suma semanal nacional)
- Inversion: pivotada en 8 columnas
- Controles: MAX flags binarios, AVG temperatura/lluvia/turismo

## 2. Validacion de Jacinto

| Ano | Facturacion Bruta | Referencia | OK |
|-----|-------------------|------------|-----|
| 2020 | 92.1 Me | ~96 Me | OK |
| 2021 | 138.0 Me | ~143 Me | OK |
| 2022 | 160.9 Me | ~167 Me | OK |
| 2023 | 176.2 Me | ~184 Me | OK |
| 2024 | 198.6 Me | ~207 Me | ?? |
| 2025 | 1.1 Me | ~0 Me | OK |

## 3. Tabla de entrenamiento
- Shape: 261 semanas x 25 columnas
- Ventas netas totales: 766.8 Me

## 4. Inversion total por canal (2020-2024)
- Paid Search: 13.40 Me
- Social Paid: 10.48 Me
- Video Online: 9.09 Me
- Display: 4.80 Me
- Email CRM: 2.94 Me
- Exterior: 7.23 Me
- Prensa: 5.45 Me
- Radio Local: 6.60 Me

## 5. Proximo paso
- EDA, Adstock, Ridge MMM