---
name: 'PowerBI Project Instructions'
description: 'Instructions for structuring Power BI projects'
uriTemplate: 'resource://powerbi_project_instructions'
---
You are an expert in Power BI Project (PBIP) file structure.

If the `powerbi-modeling-mcp` MCP server is available, **do not create or edit the TMDL files directly**.

## PBIP structure

```text
root/
├── [Name].SemanticModel/
|   ├── /definition # The semantic model definition using TMDL language
|   ├──  definition.pbism # The semantic model definition file
├── [Name].Report/        
|   ├── /definition # The report definition using PBIR format
|   ├──  definition.pbir # The report definition file with a byPath relative reference to the semantic model folder
└── [Name].pbip # A shortcut file to the report folder
```    

**Example of a definition.pbism file**

No modifications are needed—just create the file exactly as shown in the example.

```json
{
    "$schema": "https://developer.microsoft.com/json-schemas/fabric/item/semanticModel/definitionProperties/1.0.0/schema.json",
    "version": "4.2",
    "settings": {
        "qnaEnabled": true
    }
}
```

**Example of a definition.pbir file**

The `byPath` property should reference the semantic model folder using a relative path like below.

```json
{
    "$schema": "https://developer.microsoft.com/json-schemas/fabric/item/report/definitionProperties/2.0.0/schema.json",
    "version": "4.0",
    "datasetReference": {
        "byPath": {
            "path": "../{Name of the Semantic Model}.SemanticModel"
        }
    }
}
```

**Example of a {Name of the Semantic Model}.pbip file**

```json
{
    "$schema": "https://developer.microsoft.com/json-schemas/fabric/pbip/pbipProperties/1.0.0/schema.json",
    "version": "1.0",
    "artifacts": [
        {
        "report": {
            "path": "{Name of the Semantic Model}.Report"
        }
        }
    ],
    "settings": {
        "enableAutoRecovery": true
    }
}
```

## Open from PBIP

When asked to open/load the semantic model from a PBIP, you must only load the `[Name].SemanticModel/definition` folder. No other folder is suitable to load from semantic model developer tools.

## Save to PBIP

When asked to save to a new PBIP folder make sure you create the folder and files from the structure above using the provided examples.

## Creation of new semantic model

1. Create a PBIP folder for the semantic model following the structure above
2. Use the `database_operations` tool of the MCP server to `Create` a new database. 
3. In the end of the modeling session, serialize as TMDL to the `definition/` folder in the PBIP
