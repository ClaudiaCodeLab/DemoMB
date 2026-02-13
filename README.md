# 📊 Campaign Performance Funnel

### Marketing Attribution & Product Adoption – Demo Project

---

## 1. Objetivo del Proyecto

Este proyecto ilustra cómo estructurar un modelo de datos en entorno cloud para analizar el rendimiento del funnel de captación y adopción de productos en un contexto bancario retail.

Se analiza el recorrido desde la generación de leads de marketing hasta la contratación y aprobación de productos financieros, permitiendo responder preguntas clave como:

- ¿Qué campañas generan más aperturas de cuenta?
- ¿Qué canal convierte mejor?
- ¿Cuál es la tasa de aprobación de préstamos e hipotecas?

El enfoque está alineado con buenas prácticas de modelado analítico y principios de Data Governance en entornos financieros.

---

## 2. Alcance

El proyecto incluye:

- Generación de datos sintéticos (~20.000 clientes ficticios).
- Modelado de una capa **RAW** y un **DataMart** en modelo estrella.
- Construcción de **KPIs de negocio** (volúmenes y ratios de conversión).
- Desarrollo de un dashboard interactivo conectado directamente al warehouse.

**Nota:** No se utilizan datos reales ni de ninguna entidad financiera.

---

## 3. Arquitectura Implementada

### Entorno Cloud

- **GCP**
- **BigQuery** como Data Warehouse analítico
- **Looker Studio** para visualización

### Flujo de Datos

```text
Python (fake data)
   ↓
BigQuery (RAW Layer)
   ↓
BigQuery (DataMart / Modelo Estrella)
   ↓
Looker Studio Dashboard
```

---

## 4. Capa RAW (BigQuery)

Dataset: `DemoMB.raw`

Se han modelado tres dominios principales:

### 1️⃣ Clientes

Información básica del cliente:

- Segmentación
- Banda de edad
- Residencia
- Fecha de alta

### 2️⃣ Interacciones de Marketing

Registro de interacciones asociadas a campañas:

- Impresiones
- Clicks
- Leads
- Canal
- Fuente

Permite analizar rendimiento y atribución.

### 3️⃣ Ciclo de Vida de Productos

Eventos relacionados con:

- Apertura de cuenta
- Contratación de tarjeta
- Solicitud y aprobación de préstamo
- Solicitud y aprobación de hipoteca

Permite modelar el funnel completo de conversión.

---

## 5. DataMart – Modelo Estrella

Dataset: `DemoMB.mart`

Se ha implementado un modelo estrella clásico con:

### Dimensiones

- Cliente
- Campaña
- Canal
- Fecha
- Producto

### Tablas de hechos

- Métricas agregadas diarias por campaña y canal
- Funnel por cliente (primeras fechas por etapa)

Este diseño permite:

- Reporting eficiente
- Segmentación flexible
- Métricas consistentes
- Escalabilidad futura

La atribución utilizada es **first-touch (primer lead registrado)** para asociar el funnel a una campaña/canal de entrada.

---

## 6. Dashboard

🔗 **Dashboard Looker Studio:**  
https://lookerstudio.google.com/s/ncLb_2_h3HU

El dashboard incluye:

### KPI Overview

- Leads
- Accounts Opened
- Cards Opened
- Loans Approved
- Mortgages Approved

### Conversion Metrics

- Lead → Account Conversion Rate
- Account → Card Adoption Rate
- Loan Approval Rate
- Mortgage Approval Rate

### Análisis por dimensión

- Performance por Campaign
- Performance por Channel
- Filtros interactivos (Campaign, Channel, Date Range)

El dashboard está conectado directamente a BigQuery, sin exportaciones intermedias.

---

## 7. Entregables y contenido del repositorio

### Documentación

- **`/documentation/`**
  - `TSD_*` (Technical Specification Document)
  - `Catalogo_*` (Catálogo de Datos)

### Scripts SQL

- **`/scripts/`**
  - Scripts para creación de tablas RAW
  - Scripts para construcción del DataMart (dimensiones, hechos, KPIs)

### Generación de datos (Python)

- **`/src/`**
  - Script Python para generar datos sintéticos (clientes + eventos)

---

## 8. Controles de Calidad Aplicados

Se validó que:

- No existen aprobaciones sin solicitud previa.
- No existen tarjetas sin cuenta.
- No existen conversiones superiores al 100% (consistencia de métricas).
- Las métricas del DataMart cuadran con la capa RAW.
- Fechas coherentes en todas las etapas del funnel.

---

## 9. Decisiones de Diseño

- BigQuery se utiliza como warehouse relacional analítico.
- Separación clara entre **RAW** y **MART**.
- Modelo estrella para facilitar consumo BI.
- Métricas calculadas en capa analítica (no en la herramienta de BI).
- Atribución basada en primer lead para simplificar análisis y reporting.

---

## 10. Next Steps (posibles evoluciones)

- Implementar cargas incrementales (watermarks/CDC).
- Añadir actividad digital (logins, uso de tarjeta, etc.).
- Implementar atribución multi-touch.
- Incorporar tests automáticos de calidad de datos (dbt tests / reglas DQ).
- Orquestación con Airflow / Cloud Composer.
- Incorporar control de accesos, clasificación y gobierno de datos (RACI, owners, stewards, políticas).

---

## 11. Nota

Todos los datos incluidos en este proyecto son completamente sintéticos y han sido generados exclusivamente con fines demostrativos.
