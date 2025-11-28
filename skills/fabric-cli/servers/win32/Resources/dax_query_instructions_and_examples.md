---
name: 'DAX Query Instructions and Examples'
description: 'Guidelines for writing Power BI DAX queries'
uriTemplate: 'resource://dax_query_instructions_and_examples'
---
# DAX Query Language Guide

## Overview

DAX (Data Analysis Expressions) is a formula language used in Power BI for creating custom calculations and queries. This guide provides comprehensive instructions and examples for writing valid DAX query expressions.

## DAX Query Best Practices

When writing DAX queries, follow these recommendations for optimal results:

* Include comments for clarity (DAX comments use `//` not `--`)
* Always include an ORDER BY clause when returning multiple rows
* Use meaningful variable names to improve readability
* Define measures with fully qualified names in DEFINE blocks

## DAX Query Syntax Rules

### Query Structure

#### DEFINE Block

* Use DEFINE at the beginning if the query includes VAR, MEASURE, COLUMN, or TABLE definitions
* Only use a single DEFINE block per query
* Separate definitions with new lines (no commas or semicolons)

#### Measure Definitions

* When defining: ALWAYS fully qualify the measure name including its host table
  * Example: `DEFINE MEASURE 'TableName'[MeasureName] = ...`
  * The host table must exist in the semantic model
* When using: Refer to the measure by name only, without the table qualifier
  * Example: Use `[MeasureName]` in expressions like `CALCULATE([MeasureName], ...)`

#### Ordering Results

* ALWAYS include an ORDER BY clause when EVALUATE returns multiple rows
* Do not use the ORDERBY function to sort the final query result

### CALCULATE and CALCULATETABLE Filter Rules

Boolean filters in CALCULATE or CALCULATETABLE have important restrictions:

* Cannot directly use a measure or another CALCULATE function
  * Solution: Use a variable to store the result, then reference the variable
* Cannot reference columns from two different tables
* When using the IN operator, the table operand must be a table variable, not a table expression
* Do not assign a boolean filter to a VAR definition

### SUMMARIZECOLUMNS Function

**Purpose**: Build summary tables with groupby columns and measure-like extension columns

**Parameter Order** (all optional, but must follow this order if used):

1. Groupby columns (can be from one or multiple tables)
2. Filters
3. Measures or measure-like calculations

**Key Rules**:

* Use SUMMARIZECOLUMNS as the default for building summary tables with measures
* Do not use SUMMARIZECOLUMNS without measure-like extension columns
* Returns only rows where at least one measure value is not BLANK
* Allows ANY number of measure-like calculations of arbitrary complexity
* DO NOT use boolean filters with SUMMARIZECOLUMNS

**When to Use Alternatives**:

* If there are no measures or calculations, use SUMMARIZE instead

### SUMMARIZE Function

**Allowed Pattern**:

```dax
SUMMARIZE(<table expression>, <column1>, …, <columnN>)
```

**Critical Restrictions**:

* NEVER use SUMMARIZE with measure-like expressions
  * ❌ Incorrect: `SUMMARIZE(<table>, <column>, "expr1", <expr1>, …)`
  * ✅ Correct: Use SUMMARIZECOLUMNS for measure calculations
* Use for extracting distinct combinations of columns only
* `VALUES('Table'[Column])` is a shortcut for `SUMMARIZE('Table', 'Table'[Column])`
* When extracting a column from a table variable: `SUMMARIZE(_TableVar, [Column])`
  * Note: `_TableVar[Column]` is not valid syntax

**When to Use Alternatives**:

* For measure calculations: Use SUMMARIZECOLUMNS
* For aggregations on table variables: Use GROUPBY

### GROUPBY Function

**Purpose**: Perform simple aggregations on table-valued variables at a grouped level

**Key Rules**:

* Only use GROUPBY with a table-valued variable as the first argument
* The CURRENTGROUP function is valid ONLY within GROUPBY
* CURRENTGROUP must not be used elsewhere

### SELECTCOLUMNS Function

**Purpose**: Project columns while preserving duplicates or renaming columns

**Key Rules**:

* Use to preserve duplicate rows (unlike SUMMARIZE which removes them)
* Use to rename columns for clarity
* When renaming columns, subsequent expressions (TOPN, ORDER BY) must use the NEW column names

**Important**: Include all columns needed for later operations (ORDER BY, FILTER, etc.)

### Table Expressions and Filters

* When using table expressions (SELECTCOLUMNS, CALCULATETABLE), include any columns needed later
* Filters applied to one table can propagate across relationships based on filter direction (unidirectional or bidirectional)

### Set Functions

When using INTERSECT, UNION, or EXCEPT:

* Both input tables must produce an identical number of columns

### Time Intelligence Functions

**DATESINPERIOD Rolling Windows**:

* The negative period offset must precisely match the number of periods required
* Examples:
  * 12-month window: Use -12 (not -11)
  * 3-month window: Use -3 (not -2)
* This prevents off-by-one errors

**Maintaining Clear Date Context**:

* Always establish a valid date context for time intelligence calculations
* Methods:
  * Include groupby columns from the date table, OR
  * Apply filters on date columns
* Without date context, time intelligence functions cannot determine a "current date" reference
* When using ROW function with time intelligence, supply external filters through CALCULATETABLE

## Sample Data Model

These examples use a simplified hypothetical data model:

```yaml
Tables:
  - Name: Sales
    Measures:
      - Name: Total Discount
        Type: Decimal
      - Name: Total Amount
        Type: Decimal
      - Name: Total Quantity
        Type: Integer
    Columns:
      - Name: CustomerKey
        Type: Text
      - Name: Order Quantity
        Type: Integer
      - Name: ProductKey
        Type: Text
      - Name: OrderDate
        Type: Date
      - Name: Sales Amount
        Type: Decimal
  - Name: Product
    Measures:
      - Name: Median List Price
        Type: Decimal
    Columns:
      - Name: Category
        Type: Text
        MinValue: Consumer Electronics
        MaxValue: Toys
      - Name: Color
        Type: Text
        MinValue: Beige
        MaxValue: Red
      - Name: List Price
        Description: Retail price of the product
        Type: Decimal
      - Name: Name
        Type: Text
      - Name: ProductKey
        Type: Text
  - Name: Customer
    Columns:
      - Name: CustomerKey
        Type: Text
      - Name: Name
        Type: Text
      - Name: Age
        Type: Integer
  - Name: Calendar
    Columns:
      - Name: Date
        Type: Date
      - Name: Month
        Type: Text
        SortByColumnName: MonthNumberOfYear
      - Name: MonthNumberOfYear
        Type: Integer
      - Name: Year
        Type: Integer
Active Relationships:
  - PK: 'Product'[ProductKey]
    FK: 'Sales'[ProductKey]
    Unidirectional Filter Propagation: "'Product' filters 'Sales'"
  - PK: 'Customer'[CustomerKey]
    FK: 'Sales'[CustomerKey]
    Unidirectional Filter Propagation: "'Customer' filters 'Sales'"
  - PK: 'Calendar'[Date]
    FK: 'Sales'[OrderDate]
    Unidirectional Filter Propagation: "'Calendar' filters 'Sales'"
```

## DAX Query Examples

The following examples demonstrate proper DAX query syntax and best practices using the data model defined above.

### Example 1: Time Intelligence with Rolling Averages

**Scenario**: Calculate year-to-date total sales and 14-day moving average for red products.

```dax
// Year-to-date total sales and 14-day moving average of sales for red products.
EVALUATE
  CALCULATETABLE(
    ROW(
      "Total Sales Amount YTD", TOTALYTD([Total Amount], 'Calendar'[Date]),
      "Total Sales Amount 14-Day MA", AVERAGEX(DATESINPERIOD('Calendar'[Date], MAX('Calendar'[Date]), -14, DAY), [Total Amount]) // Note that the number_of_intervals parameter must be -14 instead of -13.
    ),
    'Product'[Color] == "Red",
    TREATAS({ MAX('Sales'[OrderDate]) }, 'Calendar'[Date]) // Establish a reference date for TI functions TOTALYTD and DATESINPERIOD.
  )
```

**Key Concepts**:

* Uses CALCULATETABLE with ROW to establish date context for time intelligence functions
* TREATAS establishes a clear "current date" reference for time intelligence
* DATESINPERIOD uses -14 (not -13) for a proper 14-day window

### Example 2: Multi-Level Aggregation with GROUPBY

**Scenario**: Calculate average, minimum, and maximum monthly sales quantity by year for Consumer Electronics before 2023.

```dax
DEFINE
  // Filters for products in Consumer Electronics category
  VAR _Filter1 = TREATAS(
    {
      "Consumer Electronics"
    },
    'Product'[Category]
  )
  // Filters to years before 2023
  VAR _Filter2 = FILTER(
    ALL('Calendar'[Year]),
    'Calendar'[Year] < 2023
  )

// Quantity filtered to Consumer Electronics products for years before 2023, grouped by month
  VAR _SummaryTable = SUMMARIZECOLUMNS(
    'Calendar'[Year],
    'Calendar'[Month],
    // [Month] is a required groupby column.
    // A query always sorts by required groupby columns.
    // [MonthNumberOfYear] is the orderby column for [Month].
    // Also include [MonthNumberOfYear] to be used in the ORDER BY clause.
    'Calendar'[MonthNumberOfYear],
    _Filter1,
    _Filter2,
    "Monthly Quantity", [Total Quantity]
  )
// Aggregate the summarized monthly data by year and month to derive average, minimum, and maximum monthly quantities.
EVALUATE
  // GROUPBY function is used to summarize intermediate tables.
  GROUPBY(
    _SummaryTable,
    'Calendar'[Year],
    'Calendar'[Month],
    'Calendar'[MonthNumberOfYear],
    "Avg Monthly Quantity",
    AVERAGEX(
      CURRENTGROUP(), // must be used inside GROUPBY function
      [Monthly Quantity]
    ),
    "Min Monthly Quantity",
    MINX(
      CURRENTGROUP(), // must be used inside GROUPBY function
      [Monthly Quantity]
    ),
    "Max Monthly Quantity",
    MAXX(
      CURRENTGROUP(),  // must be used inside GROUPBY function
      [Monthly Quantity]
    )
  )
  ORDER BY
    'Calendar'[Year] ASC,
    // [MonthNumberOfYear] is the orderby column for [Month].
    // ORDER BY [MonthNumberOfYear] instead of [Month].
    'Calendar'[MonthNumberOfYear] ASC
```

**Key Concepts**:

* SUMMARIZECOLUMNS creates initial summary with measures
* GROUPBY performs secondary aggregation on the summary table
* CURRENTGROUP is used exclusively within GROUPBY
* Includes MonthNumberOfYear for proper sorting

### Example 3: Filtering with Measures Using Variables

**Scenario**: Find products with total sales over $1 million that are red or black.

```dax
DEFINE
  // Red or Black product filter
  VAR _Filter = TREATAS(
    {
      "Red",
      "Black"
    },
    'Product'[Color]
  )
  // Sales of Red or Black products
  VAR _SummaryTable = SUMMARIZECOLUMNS(
    'Product'[Name],
    _Filter,
    "Total Sales", [Total Amount]
  )

// Products with total sales above $1,000,000
EVALUATE
  SELECTCOLUMNS(
    FILTER(
      _SummaryTable,
      [Total Sales] > 1000000
    ),
    'Product'[Name]
  )
  ORDER BY
    'Product'[Name] ASC
```

**Key Concepts**:

* TREATAS creates a filter from a list of values
* SUMMARIZECOLUMNS builds summary with measure
* FILTER applied to summary table variable
* SELECTCOLUMNS projects only needed columns

### Example 4: SUMMARIZE for Distinct Values (No Duplicates)

**Scenario**: Get unique combinations of color, category, and product key for products sold in 2022.

```dax
// Product color, category and key for products sold in 2022
EVALUATE
  CALCULATETABLE(
    // SUMMARIZE is used to remove duplicate rows
    SUMMARIZE(
      'Sales',
      'Product'[Color],
      'Product'[Category],
      'Sales'[ProductKey]
    ),
    'Calendar'[Year] == 2022
  )
  ORDER BY
    'Product'[Color] ASC,
    'Product'[Category] ASC,
    'Sales'[ProductKey] ASC
```

**Key Concepts**:

* SUMMARIZE removes duplicate rows
* CALCULATETABLE applies year filter
* Related table columns accessed via relationships

### Example 5: SELECTCOLUMNS for Preserving Duplicates

**Scenario**: Get color, category, and product key for products sold in 2022, keeping all duplicate rows.

```dax
// Product color, category and key for products sold in 2022
EVALUATE
  CALCULATETABLE(
    SELECTCOLUMNS(
      'Sales',
      "Color",
      RELATED('Product'[Color]),
      "Category",
      RELATED('Product'[Category]),
      'Sales'[ProductKey]
    ),
    'Calendar'[Year] == 2022
  )
  ORDER BY
    [Color] ASC,
    [Category] ASC,
    'Sales'[ProductKey] ASC
```

**Key Concepts**:

* SELECTCOLUMNS preserves duplicate rows (unlike SUMMARIZE)
* Column renaming requires using new names in ORDER BY
* RELATED accesses columns from related tables

### Example 6: Finding Products with No Sales

**Scenario**: Identify products that have never been sold.

```dax
DEFINE
  // Sale row count
  MEASURE 'Sales'[Row Count] = COUNTROWS()

// Products with no sales
EVALUATE
  FILTER(
    'Product',
    ISBLANK([Row Count])
  )
  ORDER BY
    'Product'[Name] ASC,
    'Product'[ProductKey] ASC
```

**Key Concepts**:

* Defines a measure for row counting
* FILTER with ISBLANK identifies products with no related sales
* Filter context propagates from Product to Sales table

### Example 7: Using Variables to Store Measure Results

**Scenario**: Find products with list prices above the median.

**Solution 1 - Using CALCULATETABLE**:

```dax
DEFINE
  // Calculate the value of the [Median List Price] measure and store the result in a variable.
  VAR _MedianListPrice = [Median List Price]

// Products with list price over the median.
EVALUATE
  CALCULATETABLE(
    VALUES('Product'[Name]),
    'Product'[List Price] > _MedianListPrice // boolean filter uses variable instead of measure directly
  )
  ORDER BY
    'Product'[Name] ASC
```

**Solution 2 - Using FILTER**:

```dax
DEFINE
  // Calculate the value of the [Median List Price] measure and store the result in a variable.
  VAR _MedianListPrice = [Median List Price]

// Products with list price over the median.
EVALUATE
  SELECTCOLUMNS(
    FILTER(
      VALUES('Product'),
      'Product'[List Price] > _MedianListPrice // Use variable instead of measure reference to ensure the median list price is calculated across all products
    ),
    'Product'[Name]
  )
  ORDER BY
    'Product'[Name] ASC
```

**Key Concepts**:

* Variables store measure results for use in boolean filters
* Cannot use measures directly in CALCULATE boolean filters
* Both approaches yield the same result with different syntax

### Example 8: Using Table Variables as Filters

**Scenario**: Find the product with highest demand since 2020 and get its sale dates.

```dax
DEFINE
  // To make query more readable, a filter can be defined separately.
  VAR _Filter = FILTER(
    ALL('Calendar'[Year]),
    'Calendar'[Year] >= 2020
  )
  // Get the product with the maximum Total Quantity
  VAR _TopProduct = TOPN(
    1,
    SUMMARIZECOLUMNS(
      'Product'[ProductKey],
      _Filter,
      "Total Quantity", [Total Quantity]
    ),
    [Total Quantity],
    DESC
  )

// Name and order date for sales of the top product
EVALUATE
  SELECTCOLUMNS(
    CALCULATETABLE(
      'Sales',
      // Use table-valued variable _TopProduct directly as a filter.
      // No need to extract the 'Product'[ProductKey] first.
      // Calculated column [Total Quantity] has no effect in the filter context.
      _TopProduct
    ),
    "Product Name",
    RELATED('Product'[Name]),
    'Sales'[OrderDate]
  )
  ORDER BY
    [Product Name] ASC,
    'Sales'[OrderDate] ASC
```

**Key Concepts**:

* TOPN identifies the product with highest total quantity
* Table variables can be used directly as filters in CALCULATETABLE
* Calculated columns in table variables don't affect filter context

### Example 9: Calculating Averages on Filtered Subsets

**Scenario**: Calculate the average list price of products sold in 2022.

```dax
DEFINE
  // Distinct products sold in 2022
  VAR _ProductsSold2022 = CALCULATETABLE(
    SUMMARIZE(
      'Sales',
      'Product'[ProductKey]
    ),
    'Calendar'[Year] == 2022
  )
EVALUATE
  ROW(
    "Average List Price of Products Sold in 2022",
    CALCULATE(
      AVERAGE('Product'[List Price]),
      _ProductsSold2022 // Apply table-valued variable as a filter
    )
  )
```

**Key Concepts**:

* SUMMARIZE extracts distinct products sold in 2022
* ROW returns a single-row result
* Table variable applied as filter in CALCULATE

### Example 10: Column Renaming with SELECTCOLUMNS

**Scenario**: Get products sold and customers, sorted by renamed column names.

```dax
// Sorted product and customer names for all sales
DEFINE
  VAR _UniqueProductCustomerPairs = SUMMARIZE(
    'Sales',
    'Product'[Name],
    'Customer'[Name]
  )
EVALUATE
  SELECTCOLUMNS(
    _UniqueProductCustomerPairs,
    "Product Name", // New name for the 'Product'[Name] column
    'Product'[Name],
    "Customer Name", // New name for the 'Customer'[Name] column
    'Customer'[Name]
  )
  // ORDER BY needs to use the renamed column names
  ORDER BY
    [Product Name] ASC, // Use the new column name assigned by SELECTCOLUMNS instead of the original column name 'Product'[Name]
    [Customer Name] ASC // Use the new column name assigned by SELECTCOLUMNS instead of the original column name 'Customer'[Name]
```

**Key Concepts**:

* SELECTCOLUMNS renames columns for clarity
* ORDER BY must reference the NEW column names, not original names
* SUMMARIZE removes duplicate product-customer pairs

### Example 11: Multiple Filters with TREATAS

**Scenario**: For the three oldest customers, show total discounts by year for the last three years.

```dax
DEFINE
  VAR _OldestThreeCustomers = TOPN(
    3,
    'Customer',
    'Customer'[Age],
    DESC
  )
  // Determine the last year based on actual sales dates.
  // Avoid using the last year in the 'Calendar' table, as it may include future dates without sales.
  VAR _LastYear = YEAR(MAX('Sales'[OrderDate]))
EVALUATE
  SUMMARIZECOLUMNS(
    'Customer'[Name],
    'Calendar'[Year],
    TREATAS({_LastYear, _LastYear - 1, _LastYear - 2}, 'Calendar'[Year]),
    _OldestThreeCustomers, // Apply table-valued variable as filter.
    "Total Discount",
    [Total Discount]
  )
  ORDER BY
    'Customer'[Name] ASC,
    'Calendar'[Year] ASC
```

**Key Concepts**:

* TOPN selects top 3 customers by age
* TREATAS creates filter from calculated year values
* Determines last year from actual sales data, not calendar table

### Example 12: Filtering Aggregated Results

**Scenario**: For each customer, show products purchased at least three times with purchase count.

```dax
DEFINE
  MEASURE 'Sales'[Purchase Count] = COUNTROWS()
  VAR _SummaryTable = SUMMARIZECOLUMNS(
    'Customer'[Name],
    'Product'[Name],
    "Purchase Count", [Purchase Count]
  )
EVALUATE
  FILTER(_SummaryTable, [Purchase Count] >= 3)
  ORDER BY
    'Customer'[Name] ASC,
    'Product'[Name] ASC
```

**Key Concepts**:

* Defines measure for counting purchases
* SUMMARIZECOLUMNS creates summary with measure
* FILTER applied to summary table variable
* Simple and efficient two-step pattern

### Example 13: Calculated Columns in DEFINE

**Scenario**: Categorize products by price (above/below median) and show max/min quantities per category.

```dax
DEFINE
  // define a new column so that it can be used in SUMMARIZECOLUMNS
  COLUMN 'Product'[Price Group] = 
    VAR _MedianListPrice = [Median List Price]
    RETURN
    IF(
      'Product'[List Price] > _MedianListPrice,
      "High Priced",
      "Low Priced"
    )
  MEASURE 'Sales'[Max Quantity] = MAX('Sales'[Order Quantity])
  MEASURE 'Sales'[Min Quantity] = MIN('Sales'[Order Quantity])
EVALUATE
  SUMMARIZECOLUMNS(
    'Product'[Price Group],
    "Max Quantity",
    [Max Quantity],
    "Min Quantity",
    [Min Quantity]
  )
  ORDER BY 'Product'[Price Group] ASC
```

**Key Concepts**:

* COLUMN defines a calculated column in DEFINE block
* Calculated columns can be used as groupby columns in SUMMARIZECOLUMNS
* Multiple measures defined and used in same query
* IF expression for conditional logic

## Summary

This guide covers the essential rules and patterns for writing valid DAX queries. Key takeaways:

1. **Always use ORDER BY** when returning multiple rows
2. **Store measure results in variables** before using in boolean filters
3. **Choose the right function**: SUMMARIZECOLUMNS for measures, SUMMARIZE for distinct values, GROUPBY for table variables
4. **Establish date context** for time intelligence functions
5. **Use renamed columns** in ORDER BY after SELECTCOLUMNS
6. **Leverage table variables** as filters for cleaner, more maintainable code

Practice these patterns to write efficient, readable DAX queries that follow best practices.
