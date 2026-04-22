# SWD-Bench

<div align="center">
  <img src="logo.jpg" alt="SWD-Bench Logo" width="200"/>
</div>

## Overview

This repository contains the official resources for our paper: **"SWD-Bench: Evaluating Repository-level Software Documentation via Functionality-driven Question Answering"**.

Here, you will find the benchmark dataset, data construction scripts, and evaluation scripts necessary.

## Directory Structure

The repository is organized as follows:

    .
    ├── SWD-Bench.jsonl       # The main benchmark dataset
    ├── data_construction/    # Scripts and tools used for constructing the dataset
    ├── evaluation/           # Scripts and utilities for evaluating model performance
    ├── logo.jpg              # Project logo
    └── README.md             # This file

-   **`data_construction/`**: Contains the source code used to build the `SWD-Bench` dataset from scratch.
-   **`evaluation/`**: Includes the necessary scripts to run evaluations and calculate the metrics.

## The SWD-Bench Dataset
The core of this project is the `SWD-Bench.jsonl` file, which contains our functionality-driven question-answering benchmark. Each line in this file is a JSON object representing a single data entry.

### Data Structure
Each entry in `SWD-Bench.jsonl` follows this structure:
| Field             | Type   | Description                                                                       |
| ----------------- | ------ | --------------------------------------------------------------------------------- |
| `id`              | String | A unique identifier for the data entry.                                           |
| `repo`            | String | The name of the source GitHub repository.               |
| `task_1_question` | String | The question for Task 1 (Functionality Detection).                                |
| `task_1_answer`   | String | The ground-truth answer for Task 1.                                               |
| `task_2_question` | String | The question for Task 2 (Functionality Localization).                             |
| `task_2_answer`   | String | The ground-truth answer for Task 2.                                               |
| `task_3_question` | String | The question for Task 3 (Functionality Completion).                               |
| `task_3_answer`   | String | The ground-truth answer for Task 3.                                               |


**Example Entry:**
```json
{
  "id": "pylint-dev/pylint/pr/8824",

  "repo": "pylint-dev/pylint",

  "task_1_question": "# Functionality Description: \nThis change enhances the Pyreverse package diagram generator to visually distinguish between regular imports and type-checking-only imports by introducing dashed line representations. The modification addresses the need to differentiate imports that occur only within TYPE_CHECKING blocks from standard runtime imports. The implementation adds a new type_depends attribute to module nodes to track type-checking imports separately from regular dependencies, utilizes the in_type_checking_block utility function to detect when imports occur within type checking contexts, and introduces a TYPE_DEPENDENCY edge type with corresponding visual representations across all supported output formats including dot, MermaidJS, and PlantUML printers. The diagram generation logic was updated to create distinct relationship types, rendering type-checking imports with dashed lines while maintaining solid lines for runtime dependencies.\n\n# Query: Determine if the functionality is implemented in the current repository?",

  "task_1_answer": true,

  "task_2_question": "# Functionality Description: \nThis change enhances the Pyreverse package diagram generator to visually distinguish between regular imports and type-checking-only imports by introducing dashed line representations. The modification addresses the need to differentiate imports that occur only within TYPE_CHECKING blocks from standard runtime imports. The implementation adds a new type_depends attribute to module nodes to track type-checking imports separately from regular dependencies, utilizes the in_type_checking_block utility function to detect when imports occur within type checking contexts, and introduces a TYPE_DEPENDENCY edge type with corresponding visual representations across all supported output formats including dot, MermaidJS, and PlantUML printers. The diagram generation logic was updated to create distinct relationship types, rendering type-checking imports with dashed lines while maintaining solid lines for runtime dependencies.\n\n# Query: Identify the code file(s) responsible for implementing the functionality?",

  "task_2_answer": ["pylint/pyreverse/diagrams.py", "pylint/pyreverse/dot_printer.py", "pylint/pyreverse/inspector.py", "pylint/pyreverse/mermaidjs_printer.py", "pylint/pyreverse/plantuml_printer.py", "pylint/pyreverse/printer.py", "pylint/pyreverse/writer.py"],

  "task_3_question": "# Masked Functionality Description: \nThis change enhances the [MASK] package diagram generator to visually distinguish between regular imports and type-checking-only imports by introducing [MASK] representations. The modification addresses the need to differentiate imports that occur only within [MASK] blocks from standard runtime imports. The implementation adds a new [MASK] attribute to module nodes to track type-checking imports separately from regular dependencies, utilizes the [MASK] utility function to detect when imports occur within type checking contexts, and introduces a [MASK] edge type with corresponding visual representations across all supported output formats including [MASK], [MASK], and [MASK] printers. The diagram generation logic was updated to create distinct relationship types, rendering type-checking imports with [MASK] while maintaining [MASK] for runtime dependencies.\n\n# Query: Fill in the [MASK] placeholders with the correct details?",
  
  "task_3_answer": ["Pyreverse", "dashed line", "TYPE_CHECKING", "type_depends", "in_type_checking_block", "TYPE_DEPENDENCY", "dot", "MermaidJS", "PlantUML", "dashed lines", "solid lines"]
}

