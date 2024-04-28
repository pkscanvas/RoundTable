<h1 align="center">Round Table - Text-to-Data Analysis</h1>

<p align="center">
  <img src="https://github.com/pkscanvas/RoundTable/assets/16529904/d53bc719-6ee5-478f-90c1-f42ecf166a48" alt="Description of Image">
</p>


## Overview
RoundTable is a native Mac and Windows application that lets you query datasets (spreadsheets) in plain English on your laptop using open source LLMs (something like ChatGPT's advanced data analysis but open source and on device or you can can call it LM Studio for Data Analysis). Performance of small and quantized LLMs are enhanced by the proposed 'RoundTable Framework,' which **boosts the performance of these small models on data analysis tasks by up to 25%**.

It is based on our paper "Advancing Query Precision in TQA Interfaces: Leveraging FTS-Enhanced Dynamic Schema and Context-Aware Autocomplete" (to be published).

The Round Table Framework enhances the accuracy of querying databases through Text-to-Query method. It tackles the issue of converting vague, incomplete, or misspelled user queries into precise database queries (currently pandas). This is crucial for handling real-world datasets, which often contain a wide variety of attributes and complex data.

Traditional approaches (especially if performed using small quantized models) fail to adequately communicate the breadth and complexity of datasets to Large Language Models (LLMs), leading to inaccuracies in query identification. The Round Table Framework addresses this by integrating Full-Text Search (FTS) directly into the flow, improving the identification of specific values and columns, and thereby enhancing overall query precision.

Furthermore, the framework enhances user interaction with complex datasets through a custom autocomplete feature powered by FTS. This not only streamlines the LLM's search process but also offers query suggestions based on the dataset's actual content, greatly improving the user experience by reducing user navigation to the dataset to figure out exact columns/values.

## Demo 
https://github.com/pkscanvas/RoundTable/assets/16529904/a9449989-c4ba-42ae-a2be-4d320fd77015

https://github.com/pkscanvas/RoundTable/assets/16529904/cb7e3281-47f9-4023-be55-e8bc08488a9e

## Architecture
![Round Table Architecture](https://github.com/pkscanvas/RoundTable/assets/16529904/a79d86b4-a3d8-4162-9adc-0be5f45e47c3)


## Features

- **100% On-Device**: Allows users to query databases in plain English using on device LLMs.
- **FTS-Enhanced Dynamic Schema**: Utilizes Full-Text Search to improve value detection accuracy.
- **Context-Aware Autocomplete**: Suggests relevant queries based on the underlying table data.
- **Simple UI**: A user-friendly interface to interact with the framework.
- **Multi-Turn Conversations**: Ability to chat for performing iterative operations
---

## Getting Started

### Step 1: Setup Your Local Language Model
1. **Download [LM Studio](https://lmstudio.ai/):** Begin by installing the LM Studio on your computer.
2. **Choose and Download a Model:** Select a model that fits your needs and hardware capabilities:
   - For lower-end hardware, use `Phi-3-mini` (path: `microsoft/Phi-3-mini-4k-instruct-gguf/Phi-3-mini-4k-instruct-q4.gguf`).
   - For more robust hardware, try `Mistral-7B-Instruct-v0.2` (path: `TheBloke/Mistral-7B-Instruct-v0.2-GGUF/mistral-7b-instruct-v0.2.Q4_K_M.gguf`).
   - Other models and quantizations (8 or 16-bit) are available based on hardware compatibility.
3. **[Start the Server](https://lmstudio.ai/docs/local-server#:~:text=Using%20the%20local,will%20keep%20running.):** Once you've selected your model, initiate the server.

### Step 2: Install RoundTable
1. **Download RoundTable:** Choose the correct version of the application for your operating system (Windows or macOS).
2. **Initial Setup:** Launch the application. The first startup might take a minute.

### Step 3: Organize Your Data
1. **Locate the Data Folder:** Upon startup, a dialog box will display the path to place your datasets. Typically, this is `round-table-datasets` in the user directory.
2. **Transfer Data:** Move your dataset files into the specified folder.

### Step 4: Load Your Data
1. **Create an Index:** Enter the name of your dataset file (including the file extension like .csv) and click 'Create Index'. This is required only once per dataset.
2. **Load Data:** Click 'Load Data' to display your dataset in table format.

### Step 5: Ask your question!
1. **Ask Questions:** Type your question and press 'Send'. You can continue to ask follow-up questions related to the initial query.
2. **New Queries:** For new topics, use 'New Question' to reset the context.
3. **Use Autocomplete:** Enhance query efficiency by selecting suggestions from the dropdown menu.

--- 

### TODO:
- Support for Ollama
- Better Indication for a running background task
- Option to rectify the generated code directly and rerun
- Better Prompt Engineering

