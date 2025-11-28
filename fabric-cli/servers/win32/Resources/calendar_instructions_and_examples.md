---
name: 'Calendar Instructions and Examples'
description: 'Guidelines for creating Power BI calendar objects'
uriTemplate: 'resource://calendar_instructions_and_examples'
---
# Calendar Column Groups Guide

This guide explains how to define calendar column groups in a Power BI date table so time intelligence works as expected and consistently across models.

## Concepts

- Calendar Column Groups. Use these when a primary column cleanly represents a standard time unit such as Year, Quarter, Month, Week, or Date. Time units (including "of year" variants) are defined by a fixed enumeration; use the exact casing shown below.
- Time-related groups. Use these for relative columns that are time-aware but are not a standard time unit (for example, RelativeMonth with values like "Current"/"Previous"). They can be used to slice/label time-aware analyses but do not themselves define a standard unit.
- Primary vs. associated columns. When a column maps to a specific unit, make it the primaryColumn for that unit. If column A is sorted by column B (Power BI SortByColumn), then B should be the primaryColumn and A should be an associatedColumn. Optionally add other 1-to-1 associatedColumns for alternate labels (e.g., a long and a short month name).

## Mapping guidance

- Prefer a time unit group when the mapping is unambiguous; use the exact unit name from the list below.
- Use a time-related group for relative states (e.g., current/previous/next) that don't represent a standard unit. Time-related groups have unknown time units.
- For textual labels that are sorted by another column, use the sort column as the primary and add the text label as an associatedColumn.
- Add associatedColumns only for strict 1-to-1 label relationships.
- Each calendar definition should use columns from only its host table.
- Build hierarchies that roll up cleanly (Year → Quarter → Month → Date).
- Do not repeat a time unit within the same calendar.
- Columns tagged in a calendar must be tagged to the same time unit (or as a time-related column) across all calendars.
- Do not use the same physical column more than once in the same calendar.
- Associated columns are optional but must be 1-to-1 with the primary.
- Complete vs. Partial units:
  - Complete units uniquely identify a single period and must include the calendar context (e.g., include the year): Year, Quarter, Month, Week, Date.
    - Examples: 2024 (Year), Q3 2024 (Quarter), 2024-01 or "January 2024" (Month), 2024-W49 (Week), 2024-01-15 (Date).
  - Partial units are positions within a larger period and are not unique by themselves: QuarterOfYear (1–4), MonthOfYear (1–12 or names), WeekOfYear (1–52/53), DayOfYear (1–365/366). Variants exist for Quarter/Month (e.g., MonthOfQuarter).
    - Use these primarily for labels, slicers, or seasonality—not as keys or for hierarchical rollups.
  - Mapping examples:
    - "December 2024" → Month (complete, includes year). "December" → MonthOfYear (not unique across years).
    - "Q3 2023" → Quarter. "Q3" → QuarterOfYear.
    - "2024-W49" or "Week 49 of 2024" → Week. "Week 49" → WeekOfYear.
    - "15th day of month" → DayOfMonth. "15th day of the year" → DayOfYear.
  - Rules of thumb:
    - For standard hierarchies (Year → Quarter → Month → Date), use complete units at every level.
    - You may associate a partial label with a complete primary (e.g., Month primary: Year Month; associated label: MonthOfYear name) if it is 1-to-1 with the primary.
    - Do not map MonthOfYear to Month, WeekOfYear to Week, or QuarterOfYear to Quarter—these are different concepts.
    - For weeks, prefer ISO Year-Week for complete Week labels. If your organization uses a non-ISO week system, still include the year context and use your defined week-numbering convention.

## Allowed time units

```yaml
timeUnits:
  - id: Unknown
    example: "IsWeekend"
    note: "Used for both season-type and period-type time-related columns. Future enhancements may provide separate categories."
  - id: Year
    example: 2022
  - id: Quarter
    example: "Q3 2022"
  - id: QuarterOfYear
    example: 4        # 4th quarter of the year
  - id: Month
    example: "January 2022"
  - id: MonthOfYear
    example: "January"
  - id: MonthOfQuarter
    example: 2        # 2nd month of the quarter
  - id: Week
    example: "2022-W49"   # ISO Year-Week or unique year+week label
  - id: WeekOfYear
    example: 49
  - id: WeekOfQuarter
    example: 11
  - id: WeekOfMonth
    example: 3
  - id: Date
    example: "2022-01-01"
  - id: DayOfYear
    example: 241
  - id: DayOfQuarter
    example: 71
  - id: DayOfMonth
    example: 23
  - id: DayOfWeek
    example: 4         # e.g., Thursday if 1=Monday
```

## Example

```yaml
Tables:
  - Name: DimDate
    Columns:
      - Name: Date
        Type: Date
      - Name: Year
        Type: Integer
      - Name: Quarter
        Type: Text
        SortByColumnName: Year Quarter Number
      - Name: Year Quarter
        Type: Text
        SortByColumnName: Year Quarter Number
      - Name: Year Quarter Number
        Type: Integer
      - Name: Month
        Type: Text
        SortByColumnName: Month Number
      - Name: Month Short
        Type: Text
        SortByColumnName: Month Number
      - Name: Month Number
        Type: Integer
      - Name: Year Month
        Type: Text
        SortByColumnName: Year Month Number
      - Name: Year Month Short
        Type: Text
        SortByColumnName: Year Month Number
      - Name: Year Month Number
        Type: Integer
      - Name: Week of Year
        Type: Integer
      - Name: ISO Year-Week
        Type: Text
        SortByColumnName: ISO Year-Week Number
      - Name: ISO Year-Week Number
        Type: Integer
      - Name: Fiscal Year Number
        Type: Integer
      - Name: Fiscal Year Name
        Type: Text
        SortByColumnName: Fiscal Year Number
      - Name: Fiscal Year Month
        Type: Text
        SortByColumnName: Fiscal Year Month Number
      - Name: Fiscal Year Month Number
        Type: Integer
      - Name: Fiscal Month Number of Year
        Type: Integer
      - Name: Fiscal Month Name
        Type: Text
        SortByColumnName: Fiscal Month Number of Year
      - Name: RelativeMonth  # Period-type: represents relative states
        Type: Text
      - Name: Season         # Season-type: represents cyclical concepts
        Type: Text
    Calendars:
      - name: Gregorian Calendar
        calendarColumnGroups:
          - timeUnit: Year
            primaryColumn: Year
          - timeUnit: Quarter
            primaryColumn: Year Quarter Number
            associatedColumns:
              - Year Quarter
          - timeUnit: Month
            primaryColumn: Year Month Number
            associatedColumns:
              - Year Month
              - Year Month Short
          - timeUnit: Week
            primaryColumn: ISO Year-Week Number
            associatedColumns:
              - ISO Year-Week
          - timeUnit: WeekOfYear
            primaryColumn: Week of Year
          - timeUnit: Date
            primaryColumn: Date
      - name: Fiscal Calendar
        calendarColumnGroups:
          - timeUnit: Year
            primaryColumn: Fiscal Year Number
            associatedColumns:
              - Fiscal Year Name
          - timeUnit: Month
            primaryColumn: Fiscal Year Month Number
            associatedColumns:
              - Fiscal Year Month
          - timeUnit: MonthOfYear
            primaryColumn: Fiscal Month Number of Year
            associatedColumns:
              - Fiscal Month Name
        timeRelatedGroups:
          - column: RelativeMonth
          - column: Season
```
