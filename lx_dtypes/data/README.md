# Knowledge Base Data
This module serves as template to illustrate a sample terminology.

*Content*
- [1. Configuration](#1-configuration)
- [2. Sample Knowledge Base Structure](#2-sample-knowledge-base-structure)
- [3. Overrides and Extensions](#3-overrides-and-extensions)

## 1\. Configuration
A knowledge base module requires a 'config.yaml' file at its root to define metadata and settings.

Field descriptions:
- **name**: The name of the terminology module.
- **version**: The version of the terminology module.
- **description**: A brief description of the terminology module.
- **modules**: A list of sub-modules included in this terminology module. Each sub-module should have its own directory with relevant models and data including a config.yaml file. Order of modules matters for loading precedence.
- **data_sources**: A list of data sources used by this terminology module. Each data source should be an absolute or relative path to a directory or .yaml File. Directories are recursively loaded (ordered by filename, ascending).

## 2\. Sample Knowledge Base Structure
'./sample_knowledge_base/' contains a sample knowledge base module with the following structure:

## 3\. Overrides and Extensions
To extend or override data in this knowledge base module, create a new module that lists this knowledge base as a dependency in its 'config.yaml' file under the 'depends_on' field. Your module's data will load after the dependencies, allowing you to override or extend existing entries.