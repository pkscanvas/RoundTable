import tkinter as tk
from tkinter import ttk
import customtkinter as ctk  # Use customtkinter for UI elements
import threading  # Import threading for asynchronous operations
import json
import generate_prompt  
from generate_index import generate_index, read_file
from pandastable import Table  # For displaying pandas DataFrame in Tkinter
from whoosh.index import open_dir
from helper_functions import get_suggestions, execute_and_capture_output, extract_code, display_history


ctk.set_appearance_mode('system')
ctk.set_default_color_theme('green')
history = []
    
class App(ctk.CTk):  # Inherit from ctk.CTk for the main application window
    def __init__(self):
        super().__init__()
        self.title('Round Table v0.2(Beta)')
        self.geometry('800x600')
        self.df = None
        self.history = []
        self.ix = None
        self.is_initial_question = True  # Flag to track if the current question is the first

        self.create_widgets()

    def create_widgets(self):
        # Replace tk and ttk widgets with customtkinter equivalents

        # File name input and buttons
        top_frame = ctk.CTkFrame(self)
        top_frame.pack(fill=tk.X, padx=10, pady=5)

        self.file_name_input = ctk.CTkEntry(top_frame)
        self.file_name_input.pack(side=tk.LEFT, expand=True, fill=tk.X, padx=(0, 5))
        self.file_name_input.insert(0, "Enter file name here...")
        # Set focus to file_name_input when the application launches
        self.file_name_input.focus_set()

        self.load_button = ctk.CTkButton(top_frame, text="Load Data", command=self.on_load_data, width=100)
        self.load_button.pack(side=tk.LEFT, padx=5)

        self.index_button = ctk.CTkButton(top_frame, text="Create Index", command=self.on_index, width=100)
        self.index_button.pack(side=tk.LEFT, padx=5)

        # Table display (No direct customtkinter equivalent; keep using a Frame)
        self.table_frame = ctk.CTkFrame(self)
        self.table_frame.pack(fill=tk.BOTH, expand=True)
        # Create a CTkTextbox within table_frame for displaying the DataFrame as text
        self.table_text_display = ctk.CTkTextbox(self.table_frame, state=tk.NORMAL, height=15)
        self.table_text_display.pack(fill=tk.BOTH, expand=True)
        self.table_text_display.configure(state=tk.DISABLED)  # Make it read-only

        # Query input and Listbox for suggestions
        bottom_frame = ctk.CTkFrame(self)
        bottom_frame.pack(fill=tk.X, padx=10, pady=5)

        self.query_input = ctk.CTkEntry(bottom_frame)
        self.query_input.pack(side=tk.LEFT, expand=True, fill=tk.X, padx=(0, 5))
        self.query_input.bind("<KeyRelease>", self.on_text_changed)

        # Load an image using tkinter's PhotoImage class
        self.submit_button = ctk.CTkButton(bottom_frame, text="Send", command=self.on_submit, width=100)
        self.submit_button.pack(side=tk.LEFT, padx=5)

        # Adding the 'New Question' button
        self.new_question_button = ctk.CTkButton(bottom_frame, text="New Question", command=self.on_new_question, width=100)
        self.new_question_button.pack(side=tk.LEFT, padx=5)

        # Suggestions Listbox (ctk doesn't provide a listbox, so we keep tk.Listbox)
        self.suggestions_listbox = tk.Listbox(self, height=4)
        self.suggestions_listbox.pack(fill=tk.X, padx=10, pady=5)
        self.suggestions_listbox.bind("<<ListboxSelect>>", self.on_suggestion_selected)

        # Result display (using ctk.CTkTextbox for text display)
        self.result_display = ctk.CTkTextbox(self, height=5, state=tk.DISABLED)
        self.result_display.pack(fill=tk.BOTH, expand=True, padx=10, pady=5)

        # Assuming self.result_display is the current full-width result display, remove it:
        self.result_display.pack_forget()

        # Create a new frame in the same area where self.result_display was
        result_display_frame = ctk.CTkFrame(self)
        result_display_frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=5)

        # Now create two new textboxes inside this frame
        self.result_display_1 = ctk.CTkTextbox(result_display_frame, height=5, state=tk.DISABLED)
        self.result_display_1.pack(side=tk.LEFT, fill=tk.BOTH, expand=True, padx=(0, 5), pady=5)

        self.result_display_2 = ctk.CTkTextbox(result_display_frame, height=5, state=tk.DISABLED)
        self.result_display_2.pack(side=tk.LEFT, fill=tk.BOTH, expand=True, padx=(5, 0), pady=5)



    def on_index(self):
        file_name = self.file_name_input.get()
        # Implement index creation logic here
        generate_index(file_name)
        self.result_display_1.configure(state=tk.NORMAL)
        self.result_display_1.insert(tk.END, "Index created successfully.\n")
        self.result_display_1.configure(state=tk.DISABLED)

    def on_load_data(self):
        file_name = self.file_name_input.get()
        # Implement data loading logic here
        try:
            self.df = read_file(file_name=file_name)
            self.display_dataframe()
            self.init_index()  # Automatically load the index after data is loaded
        except Exception as e:
            self.result_display_1.configure(state=tk.NORMAL)
            self.result_display_1.insert(tk.END, f"Error loading file: {e}\n")
            self.result_display_1.configure(state=tk.DISABLED)
    
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
        index_path = f"{file_name}_kb_index"

        try:
            self.ix = open_dir(index_path)  # Load the index
            self.result_display_2.configure(state=tk.NORMAL)
            self.result_display_2.delete('1.0', tk.END)
            self.result_display_2.insert(tk.END, "Index loaded successfully.\n")
            self.result_display_2.configure(state=tk.DISABLED)
        except Exception as e:
            self.result_display_2.configure(state=tk.NORMAL)
            self.result_display_2.delete('1.0', tk.END)
            self.result_display_2.insert(tk.END, f"Failed to load index: {e}\n")
            self.result_display_2.configure(state=tk.DISABLED)
            self.ix = None


    # def display_dataframe(self):
            """Using Pandas Table"""
    #     if self.df is not None:
    #         # Clear previous table
    #         for widget in self.table_frame.winfo_children():
    #             widget.destroy()
    #         # Use pandastable to display the DataFrame
    #         pt = Table(self.table_frame, dataframe=self.df.head(10), showtoolbar=False, showstatusbar=False)
    #         pt.show()
    #         self.result_display_2.configure(state=tk.NORMAL)
    #         self.result_display_2.insert(tk.END, "Data loaded successfully.\n")
    #         self.result_display_2.configure(state=tk.DISABLED)


    def display_dataframe(self):
        """Using TreeView"""
        if self.df is not None:
            # Clear previous table
            for widget in self.table_frame.winfo_children():
                widget.destroy()

            # Create the Treeview widget
            tree = ttk.Treeview(self.table_frame, show='headings')
            
            # Define the columns
            tree['columns'] = list(self.df.columns)
            
            # Format our columns
            tree.column("#0", width=0, stretch=tk.NO)  # This column is reserved for 'iid', so we hide it.
            for col in self.df.columns:
                tree.column(col, anchor=tk.CENTER, width=80)
            
            # Create Headings
            for col in self.df.columns:
                tree.heading(col, text=col, anchor=tk.CENTER)

            # Adding data to the Treeview
            for index, row in self.df.head(10).iterrows():  # Adjust row display limit as needed
                tree.insert("", tk.END, values=list(row))

            # Pack the Treeview to the window
            tree.pack(fill=tk.BOTH, expand=True)

            # Add a scrollbar
            scrollbar = ttk.Scrollbar(self.table_frame, orient=tk.VERTICAL, command=tree.yview)
            tree.configure(yscroll=scrollbar.set)
            scrollbar.pack(side=tk.RIGHT, fill=tk.Y)

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

    def on_suggestion_selected(self, event):
        selection = self.suggestions_listbox.curselection()
        if selection:
            index = selection[0]
            suggestion = self.suggestions_listbox.get(index)
            self.query_input.delete(0, tk.END)
            self.query_input.insert(0, suggestion)
            # self.suggestions_box.withdraw()  # Hide the suggestions box

    def on_new_question(self):
        self.is_initial_question = True  # Reset flag to treat the next question as the first
        self.history = []  # Clear the conversation history
        # Reset UI elements
        self.query_input.delete(0, tk.END)
        self.result_display_1.configure(state=tk.NORMAL)
        self.result_display_1.delete('1.0', tk.END)
        self.result_display_1.configure(state=tk.DISABLED)
        self.result_display_2.configure(state=tk.NORMAL)
        self.result_display_2.delete('1.0', tk.END)
        self.result_display_2.configure(state=tk.DISABLED)

    def print_history(self):
        gray_color = "\033[90m"
        reset_color = "\033[0m"
        print(f"{gray_color}\n{'-'*20} History dump {'-'*20}\n")
        # print(json.dumps(self.history, indent=2))
        print(display_history(self.history), type='console')
        print(f"\n{'-'*55}\n{reset_color}")

    def on_submit(self):
        self.result_display.configure(state=tk.NORMAL)
        self.result_display.delete('1.0', tk.END)  # Clear previous output
        try:
            user_query = self.query_input.get()
            file_name = self.file_name_input.get()
            max_attempts = 2
            attempt = 0
            error_occurred = False  # Initialize error flag

            if self.df is not None:
                top_3_rows = str(self.df.head(3).to_dict())
            else:
                top_3_rows = "[]"
                self.result_display.insert(tk.END, "DataFrame is not loaded.\n")

            if self.is_initial_question:
                prompt, db_query, token_usage = generate_prompt.generate_prompt(
                    user_query=user_query, 
                    file_name=file_name, 
                    topk_rows=top_3_rows, 
                    search_mode='flexi'
                )
                # Add the prompt to history to capture the full context of the initial question
                self.history.append({"role": "user", "content": prompt})
                self.print_history()  # Call after modifying the history

                # print("Initial question added to history:", display_history(self.history))  # Print the history after adding the initial question
                gray_color = "\033[90m"
                reset_color = "\033[0m"
                print(f"{gray_color}\n{'-'*20} History dump {'-'*20}\n")
                print(json.dumps(history, indent=2))
                print(f"\n{'-'*55}\n{reset_color}")

                self.is_initial_question = False  # Mark the initial question as processed
            else:
                # For follow-up questions, append the raw user query to history before re-calling LLM
                self.history.append({"role": "user", "content": user_query})

                # print("Follow-up question added to history:", display_history(self.history))  # Print the history after adding a follow-up question
                db_query, token_usage = generate_prompt.llm_call(
                    history=self.history, 
                    topk_rows=top_3_rows
                )

            self.history.append({"role": "assistant", "content": db_query})  # Add LLM's response to history
            # Print the history after adding the LLM response
            # print("LLM response added to history:", display_history(self.history))  
            self.print_history()

            while attempt < max_attempts:
                result, error_occurred, traceback_info = execute_and_capture_output(extract_code(db_query), {"df": self.df})
                extracted_code = extract_code(db_query)  # Extract the code
                print("Extracted code for execution:", extracted_code)  # Print the extracted code
                # self.result_display.insert(tk.END, f"Extracted code:\n{extracted_code}\n")  # Display extracted code in the app

                if error_occurred:
                    attempt += 1
                    self.result_display_2.configure(state=tk.NORMAL)
                    self.result_display_2.delete("1.0", tk.END)
                    self.result_display_2.insert(tk.END, "Code Execution Failed, trying to rework on it...\n")
                    self.result_display_2.configure(state=tk.DISABLED)

                    self.history.append({"role": "user", "content": f"Error encountered: {traceback_info}. Attempting to correct."})
                    # Print the history after adding the LLM response
                    self.print_history()
                    # print("Error in execution added to history:", display_history(self.history))  # Print the history after adding an execution error
                    db_query, token_usage = generate_prompt.llm_call(
                        history=self.history,
                        topk_rows=top_3_rows
                    )
                    # Update history with new attempt
                    self.history.append({"role": "assistant", "content": db_query}) 
                    # Add to the display area in app
                    self.result_display_2.configure(state=tk.NORMAL)
                    self.result_display_2.delete("1.0", tk.END)
                    self.result_display_2.insert(tk.END, f"\nGenerated Code:\n{extracted_code}\n")  # Display extracted code in the app
                    self.result_display_2.insert(tk.END, "="*25)
                    self.result_display_2.insert(tk.END, f"\n\nConversation Chain:\n {display_history(self.history)}")
                    self.result_display_2.configure(state=tk.DISABLED)

                    # Print the history after a new attempt
                    # print("New attempt after error added to history:", self.history)  
                    self.print_history()
                else:
                    self.result_display_1.configure(state=tk.NORMAL)
                    self.result_display_1.delete("1.0", tk.END)
                    self.result_display_1.insert(tk.END, "Result:\n" + result + "\n\n")  # Display the successful result
                    self.result_display_1.configure(state=tk.DISABLED)

                    self.result_display_2.configure(state=tk.NORMAL)
                    self.result_display_2.delete("1.0", tk.END)
                    self.result_display_2.insert(tk.END, f"\nGenerated Code:\n{extracted_code}\n")  # Display extracted code in the app
                    self.result_display_2.insert(tk.END, "="*25)
                    self.result_display_2.insert(tk.END, f"\n\nConversation Chain:\n {display_history(self.history)}")
                    self.result_display_2.configure(state=tk.DISABLED)
                    break

            if error_occurred:
                # If still error after max attempts, display the last error
                self.result_display_1.configure(state=tk.NORMAL)
                self.result_display_1.delete("1.0", tk.END)
                self.result_display_1.insert(tk.END, "Error after multiple attempts. Please try to reframe the query.\n")
                self.result_display_1.configure(state=tk.DISABLED)


        except Exception as e:
            error = f"Unexpected error: {e}"
            self.result_display_2.configure(state=tk.NORMAL)
            self.result_display_2.delete("1.0", tk.END)
            self.result_display_2.insert(tk.END, error + "\n")
            self.result_display_2.configure(state=tk.DISABLED)

            self.history.append({"role": "assistant", "content": error})  # Add error to history
            # Print the history after adding an unexpected error
            self.print_history()
            # print("Unexpected error added to history:", self.history)  

        finally:
            self.result_display.configure(state=tk.DISABLED)


if __name__ == "__main__":
    app = App()
    app.mainloop()
