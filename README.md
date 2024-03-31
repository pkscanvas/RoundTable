# Round Table - Framework for Advanced TQA
![RoundTableLogo](https://github.com/pkscanvas/RoundTable/assets/16529904/d53bc719-6ee5-478f-90c1-f42ecf166a48)




https://github.com/pkscanvas/RoundTable/assets/16529904/a9449989-c4ba-42ae-a2be-4d320fd77015


## Overview
It is an application that lets you query datasets(spreadsheets) in plain english on your laptop using open source LLMs (something like chatGPTs advanced data analysis but open source and on device).
Performance of small and quantizied LLMs are enhanced by the proposed 'RoundTable Framework' which **boosts the performance of these small models on data analysis tasks by upto 25%**

The Round Table Framework is designed to advance query precision in TQA interfaces, which has become increasingly relevant with the advancements in text to query methods. This framework addresses the challenge of translating natural language queries into executable database queries, especially when dealing with real-world datasets that feature a vast array of attributes and complex values.

Traditional methods struggle to relay the dataset's size and complexity to the LLM, often resulting in less accurate query identification. The Round Table Framework overcomes these limitations by incorporating Full-Text Search (FTS) on the input table to facilitate specific detection of values and columns, thus enhancing query precision.

Additionally, our framework includes a custom autocomplete feature powered by the FTS. This feature not only narrows the search space for LLMs but also suggests queries grounded in the table's data, significantly refining the interaction between the user and complex datasets.

## Architecture
![Round Table Architecture](https://github.com/pkscanvas/RoundTable/assets/16529904/a79d86b4-a3d8-4162-9adc-0be5f45e47c3)


## Repository Structure

```
round-table-framework/
│
├── code/ - Python scripts for core functionalities and UI
│
├── datasets/ - Datasets for testing and benchmarking
│   ├── testing files - Testing datasets
│   └── benchmark datasets - Benchmarking Datasets
│
└── Round Table Architecture.png - Visual architecture of the Round Table Framework
```

## Features

- **100% On-Device**: Allows users to query databases in plain English using on device LLMs.
- **FTS-Enhanced Dynamic Schema**: Utilizes Full-Text Search to improve value detection accuracy.
- **Context-Aware Autocomplete**: Suggests relevant queries based on the underlying table data.
- **Tkinter-based UI**: A user-friendly interface to interact with the framework.
- **Multi-Turn Conversations**: Ability to chat for performing iterative operations

## Getting Started

### Prerequisites

- Python 3.x
- Required Python packages: `requirements.txt`

### Installation

1. Clone the repository to your local machine:
   ```
   git clone https://github.com/<your-username>/round-table-framework.git
   ```
2. Navigate to the cloned directory:
   ```
   cd round-table-framework
   ```
3. Install the required dependencies:
   ```
   pip install -r requirements.txt
   ```

### Usage

1. Keep the dataset in the code folder
2. Run the LM Studio server after choosing a model compatible with your system (I recommend -> **mistral-7b-instruct-v0.2.Q4_K_M.gguf** for it's small size and stability)
3. Start the Tkinter application:
   ```
   python code/ctk_ui.py
   ```
4. Enter filename(with extension) and click 'Create Index' (required once for a dataset)
5. Load Data and start asking questions about the data.
6. Utilize the autocomplete feature for query suggestions.
4. Submit the query and interact with your databset seamlessly.

## Acknowledgments

- This work is based on our paper "Advancing Query Precision in TQA Interfaces: Leveraging FTS-Enhanced Dynamic Schema and Context-Aware Autocomplete" (to be published).
---
