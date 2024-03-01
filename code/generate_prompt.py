# Script to generate the prompt using the Dynamic Schema, User Question and Few-Shot Examples
# TODO: Few-Shot Examples

from get_dynamic_schema import get_dynamic_schema
from openai import OpenAI

def generate_synonyms(column_name:str):
    '''To generate possible synonyms of a column name
    1. Splitting Camel and Snake Case
    2. Possible business synonyms'''
    # Point to the local server
    client = OpenAI(base_url="http://localhost:1234/v1", api_key="not-needed")
    messages = [
        {"role": "user", "content": f"""You are chat-gpt-4 trained by OpenAI):
         """},

          {"role":"user", "content": f"""### Instruction:
          You are provided with a Column Name from a table and you have to write 10 possible one word business synonyms for it.
          Strictly return a python list, nothing else. NO EXPLANATION AT ALL. ONLY SINGLE WORD SYNONYMS.
          No camelCase, snake_case or PascalCase synonyms should be created.
          Column Name: {column_name}
          ### Output:
          [' """},]
    
    completion = client.chat.completions.create(
    model="local-model", # this field is currently unused
    messages=messages,
    temperature=0,
    max_tokens=1000
    )

    synonym_list = completion.choices[0].message.content
    return synonym_list

def llm_call(history:list, topk_rows:str) -> str:
    # Point to the local server
    client = OpenAI(base_url="http://localhost:1234/v1", api_key="not-needed")
    messages = [
        {"role": "system", "content": f"""You are an experienced Data Analyst who is proficient in python(especially pandas
         coding using which you are able to write the code that can answer the Question asked by your Boss about a given Tabular Dataframe 'df'. Your primary objective is to be logically correct when you answer any question. So to make sure of that, you break complex questions into sub-tasks and write code for each step along with comments.
         Always use variables to store all intermediate operations.
         ## Top 3 rows of the dataframe 'df' for your reference(to understand what columns are present):
         {topk_rows}"""}]
    
    messages.extend(history)

    # print(f"From llm_call: {history}")
    
    completion = client.chat.completions.create(
    model="local-model", # this field is currently unused
    messages=messages,
    temperature=0,
    )

    db_query = completion.choices[0].message.content
    token_usage = completion.usage
    return (db_query,token_usage)

def generate_prompt(user_query:str, file_name:str, topk_rows:str=None, search_mode:str='strict')-> str:
    '''To generate the prompt using Dynamic Schema, User Question and Few-Shot Examples'''

    dynamic_schema = get_dynamic_schema(user_query=user_query, search_mode=search_mode, file_name=file_name)

    prompt = f"""
    ### Boss's Question:
    {user_query}. Always store intermediate operations in a variable
    ### Some values and their respective columns (if detected) from the Question are:
    {dynamic_schema}
    ## Instructions:
    It is in the format <column-name>, <data-type>, <unique-values>. Use the columns mentioned, their synonyms and it's unique values to frame your code in order to answer the question as correctly as possible.
    The dataframe in question has already been loaded as 'df', so you don't need to do it(i.e. never use the load data code).

    Always keep the python code(executable code only with proper line changes, no description) in this format:
    ```python 
    <generated-code>
    ```
    
    There's no need to show the output or how output might look because Boss will execute the generated code himself. 
    Always include a print() statement in the code to print the final result along with some text to frame your answer to Boss.
    And a plot.show() in case of graphs.

    No Code Explanation/Description is required at all. Just the executable python code should be your output. 
    Don't talk back to Boss!

    ### Your Code: df = """

    # print(prompt)

    # Generate db code
    (db_query, token_usage) = llm_call(history=[{"role": "user", "content": f"{prompt}"}], topk_rows=topk_rows)

    return (prompt, db_query, token_usage)

