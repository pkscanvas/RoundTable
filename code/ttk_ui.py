import tkinter as tk
import threading  # Import threading for asynchronous operations
from tkinter import ttk
import pandas as pd
import traceback
import io
import contextlib
import textwrap
# These imports assume you have equivalent functionality in your project
import generate_prompt  
from generate_index import generate_index  
from search_suggestions import suggest_sentences
from pandastable import Table  # For displaying pandas DataFrame in Tkinter
from whoosh.index import open_dir
import tkinter.font as tkFont
import re


# def list_and_check_themes(desired_theme):
#     # root = tk.Tk()  # Temporarily create a root window to initialize Tkinter
#     style = ttk.Style()
#     available_themes = style.theme_names()
#     print("Available themes:", available_themes)

#     if desired_theme in available_themes:
#         print(f"The theme '{desired_theme}' is available.")
#         return True
#     else:
#         print(f"The theme '{desired_theme}' is not available.")
#         return False

#     # root.destroy()  # Close the temporary window

# # Check if the 'clam' theme is available
# is_clam_available = list_and_check_themes('clam')

# if is_clam_available:
#     # Apply the 'clam' theme
#     style = ttk.Style()
#     style.theme_use('clam')
# else:
#     print("Using a default theme since 'clam' is not available.")

# style = ttk.Style()
# style.theme_use('clam')
# Message History
history = []

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
    
class App(tk.Tk):
    def __init__(self):
        super().__init__()
        self.title('Round Table v0.2(Beta)')
        self.geometry('800x600')
        self.df = None
        self.history = []
        self.ix = None

        self.create_widgets()

    def create_widgets(self):

        # File name input and buttons
        top_frame = tk.Frame(self)
        top_frame.pack(fill=tk.X, padx=10, pady=5)

        self.file_name_input = tk.Entry(top_frame)
        self.file_name_input.pack(side=tk.LEFT, expand=True, fill=tk.X, padx=(0, 5))
        self.file_name_input.insert(0, "Enter file name here...")

        # Index Button
        self.index_button = ttk.Button(top_frame, text="Create Index", command=self.on_index)
        self.index_button.pack(side=tk.LEFT, padx=5)

        # Load Button
        self.load_button = ttk.Button(top_frame, text="Load Data", command=self.on_load_data)
        self.load_button.pack(side=tk.LEFT, padx=5)

        # Table display
        self.table_frame = tk.Frame(self)
        self.table_frame.pack(fill=tk.BOTH, expand=True)

        # Query input and Listbox for suggestions
        bottom_frame = tk.Frame(self)
        bottom_frame.pack(fill=tk.X, padx=10, pady=5)

        self.query_input = tk.Entry(bottom_frame)
        self.query_input.pack(side=tk.LEFT, expand=True, fill=tk.X, padx=(0, 5))
        # Query input and Listbox for suggestions modification
        self.query_input.bind("<KeyRelease>", self.on_text_changed)  # Update the event binding

        self.submit_button = tk.Button(bottom_frame, text="Send", command=self.on_submit)
        self.submit_button.pack(side=tk.LEFT, padx=5)

        # Suggestions Listbox
        self.suggestions_listbox = tk.Listbox(self, height=4)
        self.suggestions_listbox.pack(fill=tk.X, padx=10, pady=5)
        self.suggestions_listbox.bind("<<ListboxSelect>>", self.on_suggestion_selected)

        # Result display
        self.result_display = tk.Text(self, height=5)
        self.result_display.pack(fill=tk.BOTH, expand=True, padx=10, pady=5)
        self.result_display.config(state=tk.DISABLED)

    def on_index(self):
        file_name = self.file_name_input.get()
        # Implement index creation logic here
        generate_index(file_name)
        self.result_display.config(state=tk.NORMAL)
        self.result_display.insert(tk.END, "Index created successfully.\n")
        self.result_display.config(state=tk.DISABLED)

    def on_load_data(self):
        file_name = self.file_name_input.get()
        # Implement data loading logic here
        try:
            self.df = pd.read_csv(file_name)  # Assuming CSV file for simplicity
            self.display_dataframe()
            self.init_index()  # Automatically load the index after data is loaded
        except Exception as e:
            self.result_display.config(state=tk.NORMAL)
            self.result_display.insert(tk.END, f"Error loading file: {e}\n")
            self.result_display.config(state=tk.DISABLED)
    
    def init_index(self):
        # Fetch the file name from file_name_input Entry widget
        file_name = self.file_name_input.get()
        if not file_name:
            self.result_display.config(state=tk.NORMAL)
            self.result_display.delete('1.0', tk.END)
            self.result_display.insert(tk.END, "Please enter a file name to load the index.\n")
            self.result_display.config(state=tk.DISABLED)
            return

        # Construct the path to the index directory based on the file name
        # Adjust this path according to your application's requirements
        index_path = f"{file_name}_kb_index"

        try:
            self.ix = open_dir(index_path)  # Load the index
            self.result_display.config(state=tk.NORMAL)
            self.result_display.delete('1.0', tk.END)
            self.result_display.insert(tk.END, "Index loaded successfully.\n")
            self.result_display.config(state=tk.DISABLED)
        except Exception as e:
            self.result_display.config(state=tk.NORMAL)
            self.result_display.delete('1.0', tk.END)
            self.result_display.insert(tk.END, f"Failed to load index: {e}\n")
            self.result_display.config(state=tk.DISABLED)
            self.ix = None


    def display_dataframe(self):
        if self.df is not None:
            # Clear previous table
            for widget in self.table_frame.winfo_children():
                widget.destroy()
            # Use pandastable to display the DataFrame
            pt = Table(self.table_frame, dataframe=self.df.head(10), showtoolbar=False, showstatusbar=False)
            pt.show()
            self.result_display.config(state=tk.NORMAL)
            self.result_display.insert(tk.END, "Data loaded successfully.\n")
            self.result_display.config(state=tk.DISABLED)

    # Implement fetch_and_update_suggestions method
    def fetch_and_update_suggestions(self, input_text):
        suggestions = get_suggestions(self.ix, input_text, enable_fuzzy=True) if self.ix else []
        self.update_suggestions(suggestions)
    
    # Update the update_suggestions method for the App class
    def update_suggestions(self, suggestions):
        self.suggestions_listbox.delete(0, tk.END)  # Clear existing suggestions
        for suggestion in suggestions:
            self.suggestions_listbox.insert(tk.END, suggestion)

    # Implement on_text_changed method for the App class
    def on_text_changed(self, event):
        input_text = self.query_input.get()
        # Start a new thread to fetch and update suggestions without blocking the UI
        thread = threading.Thread(target=self.fetch_and_update_suggestions, args=(input_text,))
        thread.start()

    def on_query_text_changed(self, event):
        user_query = self.query_input.get()
        suggestions = get_suggestions(self.ix, user_query, enable_fuzzy=True) if self.ix else []
        print(f"Suggestions: {suggestions}")  # Debug print
        
        if suggestions:
            self.suggestions_listbox.delete(0, tk.END)  # Clear existing suggestions
            for suggestion in suggestions:
                self.suggestions_listbox.insert(tk.END, suggestion)
            
            if not self.suggestions_box.winfo_viewable():
                # Position and show the suggestions box
                x = self.query_input.winfo_rootx()
                y = self.query_input.winfo_rooty() + self.query_input.winfo_height()
                # Set the width of the suggestions box to match the query_input Entry widget
                width = self.query_input.winfo_width()
                # Optionally, adjust the height based on the number of suggestions
                height = self.suggestions_listbox.winfo_reqheight()
                self.suggestions_box.geometry(f"{width}x{height}+{x}+{y}")
                self.suggestions_box.deiconify()
                self.suggestions_box.lift()
        else:
            self.suggestions_box.withdraw()

    def on_suggestion_selected(self, event):
        selection = self.suggestions_listbox.curselection()
        if selection:
            index = selection[0]
            suggestion = self.suggestions_listbox.get(index)
            self.query_input.delete(0, tk.END)
            self.query_input.insert(0, suggestion)
            self.suggestions_box.withdraw()  # Hide the suggestions box

    def on_submit(self):
        self.result_display.config(state=tk.NORMAL)
        self.result_display.delete('1.0', tk.END)  # Clear previous output
        try:
            user_query = self.query_input.get()  # Use the current text of the suggestionsDropdown
            file_name = self.file_name_input.get()
            max_attempts = 2
            attempt = 0

            if self.df is not None:
                top_3_rows = str(self.df.head(3).to_dict())  # Use the class attribute
            else:
                top_3_rows = "[]"  # Default value if df is not loaded
                self.result_display.insert(tk.END, "DataFrame is not loaded.\n")  # Debugging print

            prompt, db_query, token_usage = generate_prompt.generate_prompt(
                user_query=user_query, 
                file_name=file_name, 
                topk_rows=top_3_rows, 
                search_mode='flexi'
            )

            result_text = f"Prompt:\n{prompt}\n\nDB Query:\n{db_query}\n\nToken Usage:\n{token_usage}"
            print(f"\n=======Initial Input to LLM: {result_text}=======")

            # Add the prompt generated from user query to history
            self.history.append({"role": "user", "content": f"{prompt}"})
            # Add llm response to history
            self.history.append({"role": "assistant", "content": f"{db_query}"})

            while attempt < max_attempts:
                result, error_occurred, traceback_info = execute_and_capture_output(extract_code(db_query), {"df": self.df})
                print(f"\n=======Extracted Code: {extract_code(db_query)}=======")

                if error_occurred:
                    attempt += 1
                    self.result_display.insert(tk.END, "Code Execution Failed, trying to rework on it...\n")

                    # Append error to history and generate a new prompt
                    self.history.append({"role": "user", "content": f"Boss executed the code you generated but got very angry as it gave this error: {traceback_info}. Take a deep breath and being chatGPT trained by openai revisit the question and your earlier response(generated code) and generate a corrected version of it. Make sure it runs and answers the boss's question correctly this time as Boss will pay you a $100K bonus for this."})
                    
                    # Call generate_prompt again (assuming it can rectify based on error)
                    db_query, token_usage = generate_prompt.llm_call(
                        history=self.history,
                        topk_rows=top_3_rows 
                    )
                    result_text = f"DB Query:\n{db_query}\n\nToken Usage:\n{token_usage}"
                    print(f"\n=======result_text/re-execution: {result_text}=======")
                    print(f"\n=======Extracted Code (Rerun): {extract_code(db_query)}=======")
                else:
                    break  # Exit loop if no error

            if error_occurred:
                # If still error after max attempts, display the last error and reset history
                self.result_display.insert(tk.END, "Error after multiple attempts. Please try to reframe the query.\n")
                self.history = []  # Reset history due to persistent errors
                print("History reset: {}".format(self.history))

            # Display the result(executed code on app)
            self.result_display.insert(tk.END, result + "\n")

        except Exception as e:
            error = f"Loader Error. Index not found!{e}"
            print(error)
            self.result_display.insert(tk.END, error + "\n")

        finally:
            self.result_display.config(state=tk.DISABLED)  # Assuming you want to disable editing after operation

if __name__ == "__main__":
    app = App()
    app.mainloop()
