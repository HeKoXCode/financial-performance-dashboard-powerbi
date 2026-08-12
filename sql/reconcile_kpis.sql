WITH base AS (
    SELECT
        CAST(OrderDateKey / 10000 AS INTEGER) AS CalendarYear,
        CountryRegionCode AS Country,
        StateProvinceName AS StateProvince,
        ProductCategory AS Category,
        CAST(SalesAmount AS REAL) AS Revenue,
        CAST(TotalProductCost AS REAL) AS COGS,
        CAST(Freight AS REAL) AS Shipping,
        CAST(TaxAmt AS REAL) AS Tax
    FROM financial_source
),
contexts AS (
    SELECT 'Total' AS Granularity, 'All' AS Member,
           SUM(Revenue) AS Revenue, SUM(COGS) AS COGS,
           SUM(Shipping) AS Shipping, SUM(Tax) AS Tax
    FROM base
    UNION ALL
    SELECT 'Year', CAST(CalendarYear AS TEXT),
           SUM(Revenue), SUM(COGS), SUM(Shipping), SUM(Tax)
    FROM base
    GROUP BY CalendarYear
    UNION ALL
    SELECT 'Country', Country,
           SUM(Revenue), SUM(COGS), SUM(Shipping), SUM(Tax)
    FROM base
    GROUP BY Country
    UNION ALL
    SELECT 'State', Country || ' / ' || StateProvince,
           SUM(Revenue), SUM(COGS), SUM(Shipping), SUM(Tax)
    FROM base
    GROUP BY Country, StateProvince
    UNION ALL
    SELECT 'Category', Category,
           SUM(Revenue), SUM(COGS), SUM(Shipping), SUM(Tax)
    FROM base
    GROUP BY Category
),
metrics AS (
    SELECT
        Granularity,
        Member,
        Revenue,
        COGS,
        Shipping,
        Tax,
        Revenue - COGS AS GrossProfit,
        Revenue - COGS - Shipping - Tax AS NetProfit
    FROM contexts
)
SELECT
    current.Granularity,
    current.Member,
    current.Revenue,
    current.COGS,
    current.Shipping,
    current.Tax,
    current.GrossProfit,
    current.NetProfit,
    current.GrossProfit / NULLIF(current.Revenue, 0) AS GrossMargin,
    current.NetProfit / NULLIF(current.Revenue, 0) AS NetMargin,
    CASE
        WHEN current.Granularity = 'Year' THEN prior.Revenue
        ELSE NULL
    END AS RevenueLY
FROM metrics AS current
LEFT JOIN metrics AS prior
    ON current.Granularity = 'Year'
   AND prior.Granularity = 'Year'
   AND CAST(prior.Member AS INTEGER) = CAST(current.Member AS INTEGER) - 1
ORDER BY
    CASE current.Granularity
        WHEN 'Total' THEN 1
        WHEN 'Year' THEN 2
        WHEN 'Country' THEN 3
        WHEN 'State' THEN 4
        WHEN 'Category' THEN 5
    END,
    current.Member;
