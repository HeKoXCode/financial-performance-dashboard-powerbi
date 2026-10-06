# 📊 Financial Power BI — guía de revisión

Creé este caso de portafolio con AdventureWorks, la muestra de Microsoft, para conectar ingresos, costos y márgenes con una lectura ejecutiva verificable.

## Qué conviene mirar primero

1. [Abrí el PDF nativo completo](media/technical/financial_reporte_completo_hq.pdf): resumen → drivers → USA → definiciones. El anexo final contiene los 22 estados de USA, generado desde la proyección SQL conciliada.
2. Revisá el período: 29/12/2010 a 28/01/2014. **2010 y 2014 son parciales**; no interpretés sus barras como años completos.
3. Contrastá ingresos, utilidad bruta, utilidad neta y márgenes con las [definiciones](dax_measure_catalog.md) y las [68 comparaciones SQL/DAX](sql_reconciliation.csv).

## Qué demuestro

- Definir un KPI y su contexto antes de compararlo.
- Comprobar el resultado por total, año, país, estado y categoría.
- Separar la inspección del resultado de la reconstrucción del modelo.

Las 60.398 filas son **líneas de venta**, no 60.398 pedidos distintos. Los importes usan la moneda de reporte de AdventureWorks; no incorporé conversión cambiaria ni datos contables de una empresa real.

## Elegí tu ruta

- **Sin herramientas:** PDF y previews del [README](../README.md).
- **Explorar:** `Financial_Report.pbix`, con datos embebidos; necesitás Power BI Desktop, no una conexión SQL para ver el snapshot.
- **Reconstruir/refrescar:** fuente JSON/TMDL y `Financial_Report.pbit`; el refresh requiere SQL Server y AdventureWorksDW2019.

El PDF es estático. No reproduce filtros, tooltips ni todas las filas de las tablas desplazables; para revisar el detalle USA completo incluí el anexo.
