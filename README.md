# Round Table - Framework for Advanced TQA
![RoundTableLogo](https://github.com/pkscanvas/RoundTable/assets/16529904/d53bc719-6ee5-478f-90c1-f42ecf166a48)




https://github.com/pkscanvas/RoundTable/assets/16529904/a9449989-c4ba-42ae-a2be-4d320fd77015


## Overview
It is an application that lets you query datasets (spreadsheets) in plain English on your laptop using open source LLMs (something like ChatGPT's advanced data analysis but open source and on device). Performance of small and quantized LLMs are enhanced by the proposed 'RoundTable Framework,' which **boosts the performance of these small models on data analysis tasks by up to 25%**.

The Round Table Framework enhances the accuracy of querying databases through Text-to-Query method. It tackles the issue of converting vague, incomplete, or misspelled user queries into precise database queries (currently pandas). This is crucial for handling real-world datasets, which often contain a wide variety of attributes and complex data.

Traditional approaches (especially if performed using small quantized models) fail to adequately communicate the breadth and complexity of datasets to Large Language Models (LLMs), leading to inaccuracies in query identification. The Round Table Framework addresses this by integrating Full-Text Search (FTS) directly into the flow, improving the identification of specific values and columns, and thereby enhancing overall query precision.

Furthermore, the framework enhances user interaction with complex datasets through a custom autocomplete feature powered by FTS. This not only streamlines the LLM's search process but also offers query suggestions based on the dataset's actual content, greatly improving the user experience by reducing user navigation to the dataset to figure out exact columns/values.

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


### Usage

#### Environment Setup (Optional)

1. Install miniconda: https://docs.anaconda.com/free/miniconda/miniconda-install/
   
3. Create a new environment
```
   conda create -n roundtable python=3.10.13
```
3. Use the environment
```
   conda activate roundtable
```
4. Install the required dependencies:
```
   pip install -r requirements.txt
```
#### Running the Application

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
