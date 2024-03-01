import contextlib
from search_suggestions import suggest_sentences
import io
import traceback
import textwrap
import re
import numpy

def get_suggestions(ix, user_query:str, enable_fuzzy:bool):
    """
    Get a list of sentence suggestions based on the user's query and index. If fuzzy search is enabled, use it to generate suggestions; otherwise, enable spell correction and fuzzy searching.

    Args:
    - ix (inverted index): The inverted index used for generating sentence suggestions.
    - user_query (str): The input user's query.
    - enable_fuzzy (bool): A flag to determine whether to use fuzzy search or not.

    Returns:
    - list of str: A list of suggested sentences based on the user's query and index, with a maximum length of 5.
    """
    if ix is None:
        print("Index not initialized.")
        return []
    try:
        if enable_fuzzy:
            suggested_sentences = suggest_sentences(
                ix=ix, input_sentence=user_query, top_k=5
            )
        else:
            suggested_sentences = suggest_sentences(
                ix=ix,
                input_sentence=user_query,
                top_k=5,
                enable_spell_correct=True,
                enable_fuzzy=True,
            )
        return suggested_sentences if suggested_sentences is not None else []
    except Exception as e:
        print(f"Error getting suggestions: {e}")
        return []  # Return an empty list in case of an error

def execute_and_capture_output(code, local_vars=None):
    # Create a string buffer to capture the output to display on the output screen
    output_buffer = io.StringIO()
    error_occurred = False
    traceback_info = ""

    # Dedent the code to fix any indentation issues
    code = textwrap.dedent(code)

    # Prepare the local variables for execution
    if local_vars is None:
        local_vars = {}
    # Prepare the globals dictionary to include numpy
    custom_globals = globals().copy()
    custom_globals['np'] = numpy

    # Redirect standard output to the buffer
    with contextlib.redirect_stdout(output_buffer), contextlib.redirect_stderr(output_buffer):
        try:
            # Execute the code with local variables
            exec(code, globals(), local_vars)
        except Exception as e:
            # Add error traceback
            traceback_info  = traceback.format_exc()
            # If there is an error, #print it to the buffer
            #print(traceback_info)
            error_occurred = True

    # Get the contents of the buffer
    captured_output = output_buffer.getvalue()

    return captured_output, error_occurred, traceback_info


def extract_code(input_string):
    '''To extract the python code in the generated response for execution'''
    full_code = ""
    try:
        # Regular expression pattern to find text between "python```" and "```"
        pattern = r"```python(.*?)```"
        
        # Find all occurrences of the pattern
        matches = re.findall(pattern, input_string, re.DOTALL)

        if matches:
            for match in matches:
                full_code += match

        # print(f"Extracted Code:{full_code}")
        
        return full_code
    except Exception as e:
        print(f"Error in code extraction :(: {e}")
        return 'print("Error!")'

def extract_code(input_string):
    '''To extract the python code in the generated response for execution'''
    full_code = ""
    try:
        # Regular expression pattern to find text between "python```" and "```"
        pattern1 = r"```python(.*?)```"
        # Regular expression pattern to find text between "[CODE] [/CODE]"
        pattern2 = r"'''python(.*?)'''"

        # Find all occurrences of the first pattern
        matches1 = re.findall(pattern1, input_string, re.DOTALL)
        matches2 = re.findall(pattern2, input_string, re.DOTALL)

        # Combine matches from both patterns
        matches = matches1 + matches2

        if matches:
            for match in matches:
                full_code += match + '\n'

        return full_code
    except Exception as e:
        print(f"Error in code extraction :(: {e}")
        return 'print("Error!")'
    
def display_history(history:list, type='app'):
    '''Takes in the history list and creates a display format for it'''
    conversation = ""

    # If type = app will print latest first to display in the app
    if type == 'app':
        for conv in history[::-1]:
            conversation += f"""\n{str(conv['role']).upper()}:\n {conv['content']} \n"""
    elif type == 'console':
        for conv in history:
            conversation += f"""\n{str(conv['role']).upper()}:\n {conv['content']} \n"""       
    return conversation

