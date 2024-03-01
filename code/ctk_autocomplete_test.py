# import customtkinter as ctk
# import tkinter as tk

# class AutocompleteEntry(ctk.CTkFrame):
#     def __init__(self, parent, suggestions, *args, **kwargs):
#         super().__init__(parent, *args, **kwargs)
#         self.entry = ctk.CTkEntry(self)
#         self.entry.pack()
#         self.entry.bind("<KeyRelease>", self.on_key_release)

#         self.suggestions_frame = ctk.CTkFrame(self)
#         self.suggestions = suggestions

#     def on_key_release(self, event):
#         value = self.entry.get()
#         filtered = [s for s in self.suggestions if value.lower() in s.lower()]

#         for widget in self.suggestions_frame.winfo_children():
#             widget.destroy()

#         for suggestion in filtered:
#             lbl = ctk.CTkButton(self.suggestions_frame, text=suggestion, command=lambda s=suggestion: self.set_value(s))
#             lbl.pack()

#         self.suggestions_frame.pack(fill=tk.BOTH, after=self.entry)

#     def set_value(self, value):
#         self.entry.delete(0, tk.END)
#         self.entry.insert(0, value)
#         self.suggestions_frame.pack_forget()

#     def update_suggestions_list(self, suggestions):
#         self.suggestions = suggestions
#         self.on_key_release(None)  # Trigger the filtering and display of suggestions


# # Example usage
# if __name__ == "__main__":
#     root = ctk.CTk()
#     root.geometry("400x300")

#     suggestions = ["Apple", "Banana", "Cherry", "Date", "Grape", "Kiwi"]
#     entry_with_autocomplete = AutocompleteEntry(root, suggestions=suggestions)
#     entry_with_autocomplete.pack(pady=20)

#     root.mainloop()

# ========================================================

import tkinter as tk
import customtkinter as ctk  # Use customtkinter for UI elements
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
from pandastable import Table  # For displaying pandas DataFrame in Tkinter
from whoosh.index import open_dir
import re
from helper_functions import get_suggestions, execute_and_capture_output, extract_code

# ctk.set_appearance_mode('dark')
ctk.set_default_color_theme('Oceanix.json')
history = []

import customtkinter as ctk
import tkinter as tk
import threading

# Set the color theme
# ctk.set_default_color_theme('light')
ctk.set_appearance_mode('light')

class AutocompleteEntry(ctk.CTkFrame):
    def __init__(self, parent, ix, suggestions=[], *args, **kwargs):
        super().__init__(parent, *args, **kwargs)
        self.entry = ctk.CTkEntry(self)
        self.entry.pack(side=tk.LEFT, fill=tk.X, expand=True)
        self.entry.bind("<KeyRelease>", self.on_key_release)

        # Construct the suggestions_frame with a specified width
        entry_width = self.entry.winfo_reqwidth()  # Request the required width for the entry widget
        entry_height = self.entry.winfo_reqheight()
        self.suggestions_frame = ctk.CTkFrame(self,width=entry_width,height=entry_height)
        self.ix = ix
        self.suggestions = suggestions if suggestions is not None else []

    def on_key_release(self, event):
        value = self.entry.get()
        if value == "":
            self.suggestions_frame.pack_forget()
            return
        else:
            # Call the function to filter suggestions based on input
            self.update_suggestions_list(get_suggestions(self.ix, value, enable_fuzzy=True))
        self.suggestions_frame.pack(fill=tk.BOTH, after=self.entry)
        
    def set_value(self, value):
        self.entry.delete(0, tk.END)
        self.entry.insert(0, value)
        self.suggestions_frame.pack_forget()

    def update_suggestions_list(self, suggestions):
        self.suggestions = suggestions
        self.show_suggestions()

    def update_ix(self, ix):
        self.ix = ix

    def show_suggestions(self):
        for widget in self.suggestions_frame.winfo_children():
            widget.destroy()

        for suggestion in self.suggestions:
            button = ctk.CTkButton(self.suggestions_frame, text=suggestion,
                                   command=lambda s=suggestion: self.set_value(s))
            button.pack()

        if self.suggestions:
            self.suggestions_frame.pack(fill=tk.BOTH)
        else:
            self.suggestions_frame.pack_forget()

class App(ctk.CTk):
    def __init__(self):
        super().__init__()
        self.title('Round Table v0.2(Beta)')
        self.geometry('800x600')
        self.df = None
        self.history = []
        self.ix = None
        self.create_widgets()

    def create_widgets(self):
        top_frame = ctk.CTkFrame(self)
        top_frame.pack(fill=tk.X, padx=10, pady=5)

        self.file_name_input = ctk.CTkEntry(top_frame)
        self.file_name_input.pack(side=tk.LEFT, expand=True, fill=tk.X, padx=(0, 5))
        self.file_name_input.insert(0, "Enter file name here...")

        self.index_button = ctk.CTkButton(top_frame, text="Create Index", command=self.on_index)
        self.index_button.pack(side=tk.LEFT, padx=5)

        self.load_button = ctk.CTkButton(top_frame, text="Load Data", command=self.on_load_data)
        self.load_button.pack(side=tk.LEFT, padx=5)

        self.table_frame = ctk.CTkFrame(self)
        self.table_frame.pack(fill=tk.BOTH, expand=True)

        bottom_frame = ctk.CTkFrame(self)
        bottom_frame.pack(side=tk.TOP, fill=tk.X, expand=True, padx=10, pady=5)
        
        self.submit_button = ctk.CTkButton(bottom_frame, text="Send", command=self.on_submit)
        self.submit_button.pack(side=tk.RIGHT, padx=5)

        self.autocomplete_entry = AutocompleteEntry(bottom_frame, self.ix, suggestions=[])
        self.autocomplete_entry.pack(side=tk.LEFT, expand=True, fill=tk.X, padx=(0, 5))

        self.result_display = ctk.CTkTextbox(self, height=5, state=tk.DISABLED)
        self.result_display.pack(fill=tk.BOTH, expand=True, padx=10, pady=5)

    def on_index(self):
        file_name = self.file_name_input.get()
        # Implement index creation logic here
        generate_index(file_name)
        self.result_display.configure(state=tk.NORMAL)
        self.result_display.insert(tk.END, "Index created successfully.\n")
        self.result_display.configure(state=tk.DISABLED)

    def on_load_data(self):
        file_name = self.file_name_input.get()
        # Implement data loading logic here
        try:
            self.df = pd.read_csv(file_name)  # Assuming CSV file for simplicity
            self.display_dataframe()
            self.init_index()  # Automatically load the index after data is loaded
        except Exception as e:
            self.result_display.configure(state=tk.NORMAL)
            self.result_display.insert(tk.END, f"Error loading file: {e}\n")
            self.result_display.configure(state=tk.DISABLED)

    def init_index(self):
        # Fetch the file name from file_name_input Entry widget
        file_name = self.file_name_input.get()
        if not file_name:
            self.result_display.configure(state=tk.NORMAL)
            self.result_display.delete('1.0', tk.END)
            self.result_display.insert(tk.END, "Please enter a file name to load the index.\n")
            self.result_display.configure(state=tk.DISABLED)
            return

        # Construct the path to the index directory based on the file name
        # Adjust this path according to your application's requirements
        index_path = f"{file_name}_kb_index"

        try:
            self.ix = open_dir(index_path)  # Load the index
            # Update ix in AutocompleteEntry
            self.autocomplete_entry.update_ix(self.ix)
            self.result_display.configure(state=tk.NORMAL)
            self.result_display.delete('1.0', tk.END)
            self.result_display.insert(tk.END, "Index loaded successfully.\n")
            self.result_display.configure(state=tk.DISABLED)
        except Exception as e:
            self.result_display.configure(state=tk.NORMAL)
            self.result_display.delete('1.0', tk.END)
            self.result_display.insert(tk.END, f"Failed to load index: {e}\n")
            self.result_display.configure(state=tk.DISABLED)
            self.ix = None

    def display_dataframe(self):
        if self.df is not None:
            # Clear previous table
            for widget in self.table_frame.winfo_children():
                widget.destroy()
            # Use pandastable to display the DataFrame
            pt = Table(self.table_frame, dataframe=self.df.head(10), showtoolbar=False, showstatusbar=False)
            pt.show()
            self.result_display.configure(state=tk.NORMAL)
            self.result_display.insert(tk.END, "Data loaded successfully.\n")
            self.result_display.configure(state=tk.DISABLED)

    def on_submit(self):
        self.result_display.configure(state=tk.NORMAL)
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
            self.result_display.configure(state=tk.DISABLED)  # Assuming you want to disable editing after operation

    # ... Rest of the App class ...

if __name__ == "__main__":
    app = App()
    app.mainloop()