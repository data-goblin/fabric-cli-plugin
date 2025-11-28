---
name: 'DAX UDF Instructions and Examples'
description: 'Guidelines for creating Power BI DAX user-defined functions (UDFs)'
uriTemplate: 'resource://dax_udf_instructions_and_examples'
---
# DAX User-Defined Functions (UDFs) Guide

## Overview

DAX User-Defined Functions (UDFs) allow you to create reusable function definitions in Power BI semantic models. This guide explains the syntax, type system, and best practices for defining UDFs.

## Basic Syntax

A UDF definition consists of a function name and a function definition with parameters and a body:

```yaml
FunctionName: MyFunction
FunctionDefinition: |-
  (param1 [: Type [Scalar Subtype] [Val|Expr]],
   param2 [: Type [Scalar Subtype] [Val|Expr]],
   ...
  ) =>
      <Function body>
```

## Type System

### Parameter Types

DAX UDFs support three main parameter types:

* **Scalar**: A single value (number, text, date/time, boolean)
* **Table**: A DAX table expression
* **AnyRef**: A direct reference to an existing semantic model object without pre-evaluation

#### Scalar Subtypes

When using `Scalar` type, you can optionally specify a subtype:

* `Int64`: Integer values
* `Decimal`: Decimal numbers
* `Double`: Double-precision floating-point numbers
* `String`: Text values
* `DateTime`: Date and time values
* `Boolean`: True/false values
* `Numeric`: Any numeric type (Int64, Decimal, or Double)
* `Variant`: Any scalar type (use when the expression may yield different types)

**Note**: `BLANK()` is valid for any subtype.

### AnyRef Type

Use `AnyRef` when you need a direct reference to a model object rather than its evaluated value. This is useful for functions that need to pass references to functions like CALCULATE, TREATAS, or SAMEPERIODLASTYEAR.

Allowed reference forms:

* Column reference: `'Table'[Column]`
* Table reference: `'Table'`
* Measure reference: `[Measure]`
* Calendar reference: `MyCalendar`

### Parameter Modes

Parameters can be evaluated in two modes:

* **Val** (value mode - default): The argument expression is evaluated at the call site before entering the function. The resulting value is substituted wherever the parameter is used.
* **Expr** (expression mode): The raw argument expression is substituted into the function body and evaluated in its inner context. Use this when you want the expression to be re-evaluated within inner contexts created by CALCULATE, FILTER, or iteration functions.

## Example Schema

The following examples reference this sample data model:

```yaml
Tables:
  - Name: Sales
    Measures:
      - Name: Total Amount
        Type: Decimal
      - Name: Total Quantity
        Type: Integer
    Columns:
      - Name: CustomerKey
        Type: Text
      - Name: ProductKey
        Type: Text
      - Name: OrderDate
        Type: Date
  - Name: Product
    Columns:
      - Name: ProductKey
        Type: Text
      - Name: Name
        Type: Text
      - Name: Color
        Type: Text
  - Name: Customer
    Columns:
      - Name: CustomerKey
        Type: Text
      - Name: Name
        Type: Text
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

## Examples

### Example 1: Simple Numeric Calculation

Calculate the area of a circle from its radius.

```yaml
FunctionName: CircleArea
FunctionDefinition: |-
    (radius : Scalar Numeric) =>
        PI() * radius * radius
```

**Usage**: `CircleArea(5)` returns approximately 78.54

### Example 2: Basic Value Transformation

Double an input value.

```yaml
FunctionName: DoubleValue
FunctionDefinition: |-
    (inputValue : Scalar Numeric Val) =>
        inputValue * 2
```

**Usage**: `DoubleValue(10)` returns 20

### Example 3: Working with AnyRef - Statistical Function

Returns the most frequently occurring value in a column.

```yaml
FunctionName: Mode
FunctionDefinition: |-
    (tab : AnyRef,
     col : AnyRef
    ) =>
        MINX(
            TOPN(
                1,
                ADDCOLUMNS(
                    VALUES(col),
                    "Freq", CALCULATE(COUNTROWS(tab))
                ),
                [Freq], DESC
            ),
            col
        )
```

**Explanation**: This function uses `AnyRef` for both parameters because it needs to pass the table and column references to DAX functions like VALUES and CALCULATE. The function finds the value that appears most frequently by counting occurrences.

**Usage**: `Mode('Sales', 'Sales'[ProductKey])`

### Example 4: Using Expr Mode for Time Intelligence

Evaluate any scalar expression in the prior year.

```yaml
FunctionName: PriorYearValue
FunctionDefinition: |-
    (expression : Scalar Variant Expr,
     dateColumn : AnyRef
    ) =>
        CALCULATE(
            expression,
            SAMEPERIODLASTYEAR(dateColumn)
        )
```

**Explanation**: The `expression` parameter uses `Expr` mode so it's evaluated within the CALCULATE context with the prior year filter applied. The `dateColumn` uses `AnyRef` to pass the column reference to SAMEPERIODLASTYEAR.

**Usage**: `PriorYearValue([Total Amount], 'Calendar'[Date])`

### Example 5: Returning a Table Filter

Return today's date as a one-row table for filtering.

```yaml
FunctionName: TodayAsDate
FunctionDefinition: |-
    () =>
        TREATAS(
            { TODAY() },
            'Date'[Date]
        )
```

**Explanation**: This function demonstrates a UDF that returns a table. It uses TREATAS to convert the single-value table into a filter compatible with the Date table.

**Usage**: `CALCULATE([Total Amount], TodayAsDate())`

### Example 6: Table-Returning Function

Return a table of the top 3 Products by the [Sales] measure.

```yaml
FunctionName: Top3ProductsBySales
FunctionDefinition: |-
    () =>
        TOPN(
            3,
            VALUES('Product'[ProductKey]),
            [Sales], DESC
        )
```

**Explanation**: This parameterless function returns a table containing the top 3 products. It can be used anywhere a table expression is expected.

**Usage**: `CALCULATE([Total Amount], Top3ProductsBySales())`

### Example 7: String Manipulation with Table Return

Split a text by a delimiter and return a single-column table.

```yaml
FunctionName: SplitString
FunctionDefinition: |-
    (s : Scalar String,
     delimiter : Scalar String
    ) =>
    VAR str =
        SUBSTITUTE(s, delimiter, "|")
    VAR len =
        PATHLENGTH(str)
    RETURN
        SELECTCOLUMNS(
            GENERATESERIES(1, len),
            "Value", PATHITEM(str, [Value], TEXT)
        )
```

**Explanation**: This function uses variables (VAR) and demonstrates how to build complex logic. It converts the delimiter to a path separator, counts the parts, and returns a table with each part as a row.

**Usage**: `SplitString("apple,banana,cherry", ",")`

## Best Practices

1. **Use appropriate type hints**: Specify types and subtypes to make your functions more robust and self-documenting
2. **Choose the right parameter mode**: Use `Expr` when you need the expression to be evaluated in the function's context, otherwise use `Val` (default)
3. **Use AnyRef for references**: When passing columns, tables, or measures to DAX functions that expect references, use `AnyRef`
4. **Document your functions**: Include clear descriptions of what each function does
5. **Test with edge cases**: Consider BLANK values and empty tables in your function logic
6. **Keep functions focused**: Each function should have a single, well-defined purpose
7. **Use variables**: For complex functions, use VAR to break down logic and improve readability
