# Script to generate a whoosh index for a given file

# Imports
import pandas as pd
import os
import re
from typing import Optional
from whoosh.index import create_in
from whoosh.fields import Schema, TEXT, ID
import generate_prompt
import json
import pickle

# Read the file in supported formats
def read_file(file_name: str) -> Optional[pd.DataFrame]:
    """Function to read different formats of spreadsheets like CSV, XLS, XLSX, and Parquet based on the extension of the file uploaded

    Args:
        file_name (str): The name of the spreadsheet file to be read

    Returns:
        Optional[pd.DataFrame]: A DataFrame object containing the spreadsheet data, or None if the file format is not supported

    Raises:
        NotImplementedError: If an unsupported file format is passed as a parameter"""

    # Determine the file format from its extension
    file_ext = file_name.split(".")[-1].lower()

    if file_ext == "csv":
        df = pd.read_csv(file_name)
    elif file_ext == "xls" or file_ext == "xlsx":
        df = pd.read_excel(file_name)
    elif file_ext == "parquet":
        df = pd.read_parquet(file_name)
    else:
        print(f"Unsupported file format: {file_ext}")
        return None

    # Return the DataFrame containing the spreadsheet data
    return df
    
# Getting Dtypes of the table:
# - TODO: Automatic inferring
# - TODO: Manual changing option of dtypes of columns

def get_dtypes(df: pd.DataFrame) -> dict[str, type]:
    """Function to get the data types of each column in a DataFrame and store them in a dictionary with column name as key and dtype as value

    Args:
        df (pd.DataFrame): The Pandas DataFrame object for which we want to get the data types

    Returns:
        dict[str, type]: A dictionary containing the column names and corresponding data types of the input DataFrame
    """

    # Get the dtypes of each column in the input DataFrame
    column_dtypes = df.dtypes.to_dict()

    # Rename the keys to be the column names instead of the dtype names
    col_name_dtypes = {k: v for k, v in column_dtypes.items()}

    # Return the dictionary containing the data types of each column
    return col_name_dtypes


# Getting Categorical Columns
# - From data_types

def get_cat_cols(data_types: dict) -> list[str]:
    """Function to return all the categorical column names from a schema dictionary

    Args:
        data_types (dict): A dictionary containing column names as keys and their corresponding data types as values

    Returns:
        list[str]: A list of categorical column names in the input schema dictionary
    """

    # Create an empty list to store the categorical column names
    cat_cols = []

    # Iterate over each column in the input schema dictionary and check if it is a categorical column or not
    for col, dtype in data_types.items():
        if dtype == 'object':
            cat_cols.append(col)
        elif dtype.name == 'category':
            cat_cols.append(col)
        # Add more conditions to check if a data type is categorical or not depending on the use case

    # Return the list of categorical column names
    return cat_cols


# Extracting Unique Values
# - Of Categorical Columns
# - TODO: Option to avoid indexing ID columns

def get_unique_values(df: pd.DataFrame, cat_cols: list) -> dict[str, list]:
    """Function to return all the unique values of a given set of columns in a DataFrame

    Args:
        df (pd.DataFrame): The Pandas DataFrame object for which we want to get the unique values
        cat_cols (str): A string containing a comma-separated list of column names for which we want to get the unique values

    Returns:
        dict[str, list]: A dictionary containing the unique values of each specified column as a list

    Raises:
        ValueError: If any of the specified columns do not exist in the DataFrame
    """

    # Create an empty dictionary to store the unique values of each column
    unique_values = {}

    # Iterate over each specified column and get its unique values
    for col in cat_cols:
        if col not in df.columns:
            raise ValueError(f"Column '{col}' does not exist in DataFrame")
        else:
            unique_values[col] = df[col].unique().tolist()

    # Return the dictionary containing the unique values of each column
    return unique_values

# To split different cases
def split_and_join_string(s):
    # Splitting snake_case
    if '_' in s:
        split_words = s.split('_')
    
    # Splitting camelCase and PascalCase
    else:
        split_words = re.findall('.+?(?:(?<=[a-z])(?=[A-Z])|(?<=[A-Z])(?=[A-Z][a-z])|$)', s)
    
    # Joining the split words with a space
    return ' '.join(split_words)

# Synonyms:
def create_synonym_dict(data_types: dict, generate_synonyms: bool = False) -> dict:
    """
    Creates a dictionary with keys as Attributes and their plural forms as basic synonyms.

    Args:
         data_types: A dictionary containing attribute names as keys.

    Returns: 
        A dictionary with attribute names as keys and their plural forms as values.
    """
    
    synonyms = {}
    for column_name in data_types.keys():

        # Split and create a single word in case of camelCase, PascalCase or snake_case for better search results
        split_col_name = split_and_join_string(column_name)
        synonyms[column_name] = [split_col_name]

        if column_name[-1] == "y":
            synonyms[column_name].append(f"{split_col_name[:-1]}ies")
        elif column_name[-1] in ("s", "x"):
            synonyms[column_name].append(f"{split_col_name[:-1]}es")
        else:
            synonyms[column_name].append(f"{split_col_name}s")
        
        # Appending generated synonyms
        if generate_synonyms:
            try:
                synonyms[column_name].extend(eval(generate_prompt.generate_synonyms([split_col_name])))
                # In case LLM output is not a list
            except Exception as e:
                print(f"Error in Generating Synonyms: {e}")
                synonyms[column_name].extend(generate_prompt.generate_synonyms([split_col_name]))

    return synonyms



def split_and_join_string(s):
    # Splitting snake_case
    if '_' in s:
        split_words = s.split('_')
    
    # Splitting camelCase and PascalCase
    else:
        split_words = re.findall('.+?(?:(?<=[a-z])(?=[A-Z])|(?<=[A-Z])(?=[A-Z][a-z])|$)', s)
    
    # Joining the split words with a space
    return ' '.join(split_words)

# Create schema
def create_schema(data_types, categorical_columns, synonyms):
    schema_dict = {'data_type':data_types,'categorical_columns':categorical_columns,'synonyms':synonyms}
    return schema_dict

# Indexing Knowledgebase
def create_index(file_name, schema_dict):

    # Save dict
    try:
        # with open(f"{file_name}.json", 'w') as fj:
        #     json.dump(schema_dict, fj, indent=4)
        with open(f"{file_name}.pkl", 'wb') as fp:
            pickle.dump(schema_dict, fp)
    except Exception as e:
        print(f"JSON Error: {e}")


    # Define the schema for the index 
    schema = Schema(column_name=ID(stored=True), synonyms=TEXT(stored=True), unique_values=TEXT(stored=True))  

    # Create an index directory if it doesn't exist  
    index_path = f"{file_name}_kb_index"
    if not os.path.exists(index_path):  
        os.mkdir(index_path)  
    
    # Create the index  
    ix = create_in(index_path, schema)  
    
    writer = ix.writer()  
    
    for k,v in schema_dict['data_type'].items():

        column_name = f"'{k}', '{v}'" 
        print('column_name:', column_name)

        # If it's Edm.DateTime store in 'synonyms' field
        if 'datetime' in str(v):
            synonyms = f"{str(schema_dict['synonyms'][k])}, {schema_dict['data_type'][k]}"
            print('synonyms:', synonyms)
        else:
            synonyms = str(schema_dict['synonyms'][k])
            print('synonyms:', synonyms)
        # Catch exception in unique_values as only categorical columns are present in it
        try:
            unique_values = str(schema_dict['categorical_columns'][k])
            print("unique_values:", unique_values)
        except:
            unique_values = ''
        
        writer.add_document(column_name=column_name, synonyms=synonyms, unique_values=unique_values)
    
    writer.commit()

# Execute all functions to create and save the index of the provided file
def generate_index(file_name: str) -> None:
    """
    Processes a given file and generates an index based on its contents.

    This function reads the file, identifies data types and categorical columns,
    creates synonyms based on the data types, and then uses this information to
    create an index for the file.

    Args:
        file_name (str): The name of the file to be processed and indexed.

    Returns:
        None: This function does not return anything. It prints messages to
        indicate the status of the operation.

    Raises:
        ValueError: If any issues are encountered in reading the file or during
        indexing.
    """
    try:
        # Step 1: Read the file
        df = read_file(file_name)
        if df is None:
            raise ValueError("Error reading file.")

        # Step 2: Get the Data Types
        data_types = get_dtypes(df)

        # Step 3: Get Categorical Columns
        categorical_columns = get_unique_values(df=df, cat_cols=get_cat_cols(data_types=data_types))

        # Step 4: Create synonyms
        synonyms = create_synonym_dict(data_types=data_types, generate_synonyms=False)

        # Step 5: Create schema
        schema_dict = create_schema(data_types, categorical_columns, synonyms)

        # Step 6: Create Index
        create_index(file_name=file_name, schema_dict=schema_dict)

        print("Index successfully created.")

    except Exception as e:
        print(f"An error occurred: {e}")




    