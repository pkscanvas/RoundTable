import sys
import re
import traceback
import pandas as pd
from PyQt5.QtCore import pyqtSlot, QThread, pyqtSignal,QStringListModel, Qt 
from PyQt5.QtWidgets import QApplication, QMainWindow, QTableWidget, QTableWidgetItem, QVBoxLayout, QWidget, QLineEdit, QPushButton, QTextEdit, QLabel, QApplication, QStyleFactory, QHBoxLayout, QComboBox, QCompleter
from PyQt5.QtGui import QPixmap, QFont
import importlib
import generate_prompt  
from generate_index import generate_index  
import io
import contextlib
import numpy as np
import textwrap
from search_suggestions import suggest_sentences
from whoosh.index import open_dir

# Message History
history = []

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
    
# Threading
class WorkerThread(QThread):
    finished = pyqtSignal()
    dataLoaded = pyqtSignal(pd.DataFrame)
    errorOccurred = pyqtSignal(str)

    def __init__(self, file_name):
        super().__init__()
        self.file_name = file_name


    def run(self):
        try:
            df = pd.read_csv(self.file_name)
            self.dataLoaded.emit(df)
        except Exception as e:
            error_message = f"Error loading file: {e} \n Please check the spelling if file exists."
            print(error_message)
            self.errorOccurred.emit(error_message)  # Emit the error message
        finally:
            self.finished.emit()

# UI
class App(QMainWindow):
    def __init__(self):
        super().__init__()
        self.title = 'Round Table v0.2(Beta)'
        self.df = None  # Initialize the DataFrame attribute
        self.history = [] # Initialize history to store interactions
        self.ix = None  # Initialize Index
        self.initUI()
        # Setup the completer with dynamic suggestions
        self.setupCompleter()
        self.suggestionsThread = None  # Keep track of the thread


    def initIndex(self):
        # Fetch the file name from fileNameInput
        file_name = self.fileNameInput.text()
        if not file_name:
            self.resultDisplay.setText("Please enter a file name to load the index.")
            return

        # Construct the path to the index directory based on the file name
        # Adjust this path according to your application's requirements
        index_path = f"{file_name}_kb_index"

        try:
            self.ix = open_dir(index_path)  # Load the index
            self.resultDisplay.setText("Index loaded successfully.")
        except Exception as e:
            print(f"Failed to load index: {e}")
            self.resultDisplay.setText(f"Failed to load index: {e}")
            self.ix = None

    def initUI(self):
        self.setWindowTitle(self.title)
        self.setGeometry(100, 100, 800, 600)

        mainWidget = QWidget(self)
        self.setCentralWidget(mainWidget)
        layout = QVBoxLayout(mainWidget)
        layout.setSpacing(10)
        layout.setContentsMargins(10, 10, 10, 10)

        mainWidget = QWidget(self)
        self.setCentralWidget(mainWidget)
        layout = QVBoxLayout(mainWidget)

        # Loader label for displaying a loading animation
        self.loaderLabel = QLabel(self)
        self.pixmap = QPixmap('loading.gif')  # Ensure you have a 'loading.gif' or replace with your gif file path
        self.loaderLabel.setPixmap(self.pixmap)
        self.loaderLabel.hide()
        layout.addWidget(self.loaderLabel)

        # Top bar for file name input and loading
        topLayout = QHBoxLayout()
        self.fileNameInput = QLineEdit()
        self.fileNameInput.setPlaceholderText('Enter file name here...')
        topLayout.addWidget(self.fileNameInput)

        self.indexButton = QPushButton('Create Index')
        self.indexButton.clicked.connect(self.onIndex)
        topLayout.addWidget(self.indexButton)

        self.loadButton = QPushButton('Load Data')
        self.loadButton.clicked.connect(self.onLoadData)
        self.loadButton.clicked.connect(self.initIndex)  # Connect button click to initIndex method
        topLayout.addWidget(self.loadButton)
        
        layout.addLayout(topLayout)

        # Table for displaying sample DataFrame
        self.tableWidget = QTableWidget()
        layout.addWidget(self.tableWidget, 1)
    
        # Bottom bar for query input and submission
        bottomLayout = QHBoxLayout()
        self.queryInput = QLineEdit()
        self.queryInput.setPlaceholderText('Enter your query here...')
        bottomLayout.addWidget(self.queryInput)
        # Connect the textChanged signal to onQueryTextChanged
        self.queryInput.textChanged.connect(self.onQueryTextChanged)

        self.submitButton = QPushButton('Send')
        self.submitButton.clicked.connect(self.onSubmit)
        bottomLayout.addWidget(self.submitButton)
        
        layout.addLayout(bottomLayout)

        # Text area for displaying results
        self.resultDisplay = QTextEdit()
        self.resultDisplay.setReadOnly(True)
        layout.addWidget(self.resultDisplay)

    def setupCompleter(self):
        # Initialize the completer without a model for now
        self.completer = QCompleter()
        self.completer.setCompletionMode(QCompleter.PopupCompletion)  # Example setting
        self.completer.setModelSorting(QCompleter.UnsortedModel)
        self.completer.setFilterMode(Qt.MatchStartsWith)
        self.completer.setMaxVisibleItems(10)
        self.completer.setCaseSensitivity(Qt.CaseInsensitive)
        self.queryInput.setCompleter(self.completer)
        
        # Update completer suggestions dynamically based on text changes
        # self.queryInput.textChanged.connect(self.onQueryTextChanged) 

    def onQueryTextChanged(self, text):
        if self.suggestionsThread is not None:
            self.suggestionsThread._interrupted = True
            self.suggestionsThread.wait()

        if text and self.ix is not None:
            self.suggestionsThread = SuggestionsThread(ix=self.ix, user_query=text, enable_fuzzy=True)
            self.suggestionsThread.suggestionsFetched.connect(self.updateCompleterModel)
            self.suggestionsThread.start()
        else:
            print("Index not loaded. Suggestions cannot be fetched.")

    def updateCompleterModel(self, suggestions):
        # Ensure suggestions are in the correct format (a list of strings)
        if isinstance(suggestions, list):
            model = QStringListModel(suggestions)
            print("Suggestions:", suggestions)
            # self.completer.setModel(model)
            self.completer.setModel(QStringListModel(['apple','job', 'employee']))  # Clear the model if format is incorrect

        else:
            # Log or handle the unexpected format
            print(f"Expected a list of strings, got: {type(suggestions)}")
            self.completer.setModel(QStringListModel(['A','B']))  # Clear the model if format is incorrect

    def onIndex(self):
        file_name = self.fileNameInput.text()
        try:
            generate_index(file_name=file_name)
            self.resultDisplay.setText("Index created successfully.")
        except Exception as e:
            error_message = f"Error generating index: {e}"
            print(error_message)
            self.resultDisplay.setText(error_message)

    def onLoadData(self):
        file_name = self.fileNameInput.text()
        self.loaderLabel.show()
        self.thread = WorkerThread(file_name)
        self.thread.dataLoaded.connect(self.displayDataFrame)
        self.thread.finished.connect(self.onLoadFinished)
        self.thread.errorOccurred.connect(self.handleError)
        self.thread.start()

    def onLoadFinished(self):
        self.loaderLabel.hide()
    
    def handleError(self, message):
        self.resultDisplay.setText(message)

    def displayDataFrame(self, df):
        try:
            #print(f"DataFrame received in displayDataFrame: {df.head(5)}")  # Debugging print
            self.df = df  # Store the loaded DataFrame
            self.loaderLabel.hide()
            self.tableWidget.setRowCount(10)
            self.tableWidget.setColumnCount(df.shape[1])
            self.tableWidget.setHorizontalHeaderLabels(df.columns)
            for row in range(10):
                for col in range(df.shape[1]):
                    self.tableWidget.setItem(row, col, QTableWidgetItem(str(df.iloc[row, col])))
        except Exception as e:
            print(f"Error displaying DataFrame: {e}")
    

    def onSubmit(self,df):
        self.loaderLabel.show()  # Show the loader
        QApplication.processEvents()
        try:
            user_query = self.queryInput.text()  # Use the current text of the suggestionsDropdown
            file_name = self.fileNameInput.text()
            max_attempts = 2
            attempt = 0

            if self.df is not None:
                top_3_rows = str(self.df.head(3).to_dict())  # Use the class attribute
                # print(f"Top 3 rows in onSubmit: {top_3_rows}")  # Debugging print
            else:
                top_3_rows = "[]"  # Default value if df is not loaded
                print("DataFrame is not loaded")  # Debugging print

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

            try:
                # Extract Code and Execute it
                result, error_occurred, traceback_info = execute_and_capture_output(extract_code(db_query), {"df": self.df})
                print(f"\n=======Extracted Code: {extract_code(db_query)}=======")
            
                while attempt < max_attempts and error_occurred:

                    attempt += 1
                    print("Error in code execution occured")
                    self.resultDisplay.setText("Code Execution Failed, trying to rework on it...")

                    # Append error to history and generate a new prompt
                    self.history.append({"role": "user", "content": f"Boss executed the code you generated but got very angry as it gave this error: {traceback_info}. Take a deep breath and being chatGPT trained by openai revisit the question and your earlier response(generated code) and generate a corrected version of it. Make sure it runs and answers the boss's question correctly this time as Boss will pay you a $100K bonus for this."})
                    
                    # Call generate_prompt again (assuming it can rectify based on error)
                    # You might need to modify generate_prompt to accept and process error messages
                    db_query, token_usage = generate_prompt.llm_call(
                        history=self.history,
                        topk_rows=top_3_rows 
                    )
                    result, error_occurred, traceback_info = execute_and_capture_output(extract_code(db_query), {"df": self.df})
                    result_text = f"DB Query:\n{db_query}\n\nToken Usage:\n{token_usage}"
                    print(f"\n=======result_text/re-execution: {result_text}=======")
                    print(f"\n=======Extracted Code (Rerun): {extract_code(db_query)}=======")


                if error_occurred:
                    # If still error after max attempts, display the last error and reset history
                    self.resultDisplay.setText("Error after multiple attempts. Please try to reframe the query.")
                    self.history = []  # Reset history due to persistent errors
                    print(f"History rest: {history}")

            except Exception as e:
                result = f"An Error Occurred in Code Execution: {e}"
                #print(f"In onSubmit: {result}")
                result, _, _ = execute_and_capture_output("print('An Error Occured!')", {"df": self.df})

            print(f"Value of error occured: {error_occurred}")

            # Display the result(executed code on app)    
            self.resultDisplay.setText(result)

        except Exception as e:
            error = f"Loader Error. Index not found!{e}"
            print(error)
            self.resultDisplay.setText(error)

        finally:
            self.loaderLabel.hide()  # Hide the loader regardless of success or failure

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

class SuggestionsThread(QThread):
    suggestionsFetched = pyqtSignal(list)  # This signal will carry the fetched suggestions

    def __init__(self, ix, user_query, enable_fuzzy):
        super().__init__()
        self.ix = ix
        self.user_query = user_query
        self.enable_fuzzy = enable_fuzzy
        self._interrupted = False  # Interruption flag

    def run(self):
        if self._interrupted:
           return  # Exit the thread cleanly
        suggestions = get_suggestions(self.ix, self.user_query, self.enable_fuzzy)
        if suggestions is None:  # Check if suggestions is None
            suggestions = []  # Ensure we always emit a list
        self.suggestionsFetched.emit(suggestions)

if __name__ == '__main__':
    app = QApplication(sys.argv)
    app.setStyle("Fusion")
    ex = App()
    ex.show()
    sys.exit(app.exec_())
