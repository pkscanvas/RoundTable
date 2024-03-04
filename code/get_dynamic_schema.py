# Script to take in the user query and generate the dynamic schema(context based on question)

# Imports
from whoosh.index import create_in
from whoosh.fields import Schema, TEXT, ID
from whoosh.qparser import QueryParser, FuzzyTermPlugin
import re

# Consuming Index
def load_index(file_name:str) -> None:
    '''Loads the index by file name'''
    # Load Index
    from whoosh.index import open_dir
    ix = open_dir(f"{file_name}_kb_index")
    return ix

def identify_column(ix, keyword):
    """
    Detect column names and the synonyms that matched the keyword.
    
    Parameters:
        ix (Index): The index to search in.
        keyword (str): The keyword to look for in the synonyms of the columns.
            
    Returns:
        dict: A dictionary where keys are column names and values are lists of matched synonyms.
    """
    identified_column_dict = dict()

    with ix.searcher() as searcher:
        # Setup fuzzy lookup with wildcard
        parser = QueryParser("synonyms", ix.schema)
        parser.add_plugin(FuzzyTermPlugin())
        query = parser.parse(f"*{keyword}*")
        
        results = searcher.search(query, limit=30)
        results.fragmenter.charlimit = None
        results.fragmenter.surround = 100

        for result in results:
            column_name = result["column_name"]
            # Process search highlights to extract matched synonyms
            search_term_highlights = result.highlights("synonyms", top=1).replace('</b>', '')
            search_term_highlights = re.sub(r'<b class="match term\d+"', '', search_term_highlights)
            search_terms = search_term_highlights.split(", '")
            search_terms = [re.sub(r'>','',i) for i in search_terms if '>' in i]
            
            identified_column_dict[column_name] = search_terms

    return identified_column_dict

def identify_column_from_value(ix, keyword, use_wildcard=True):
  
    """
    Identify column name from a given value using fuzzy search. 
    
    Parameters:
        ix (Index): The index to search in.
        keyword (str): The keyword to look for in the unique values of the columns.
        use_wildcard (bool): Whether to use wildcards or not. Default is True.
            
    Returns:
        dict: A dictionary where keys are column names and values are a list of unique values that match the keyword.
    """
    identified_column_dict = dict()
    with ix.searcher() as searcher:  
        ###Fuzzy lookup
        parser = QueryParser("unique_values", ix.schema)
        parser.add_plugin(FuzzyTermPlugin())
        if use_wildcard:
            query = parser.parse(f"*{keyword}*")  # Add wildcard characters to match any word that contains the keyword
        else:
            query = parser.parse(keyword)  
        ####
        results = searcher.search(query, limit=10)
        results.fragmenter.charlimit = None
        # Show more context before and after
        results.fragmenter.surround = 100

        for result in results:
            # print(result["column_name"], {result.score})
 
            # Remove '</b>' tags  
            search_term = result.highlights("unique_values", top=1).replace('</b>', '')  
            # Remove '<b class="match term[number]"' tags using regex  
            search_term = re.sub(r'<b class="match term\d+"', '', search_term)  
            # Split the text  
            search_term = search_term.split(", '") 
            # Remove char '>'
            search_term = [re.sub(r'>','',i) for i in search_term if '>' in i]
            # print(search_term)
            identified_column_dict[result["column_name"]] = search_term

    return identified_column_dict

# ===================================
# Extract Keywords
def extract_keywords(text, money_words=[]):  
    '''Extract Keywords from the user query'''  

    # Remove 2 consecutive single quotes (to not pass quoted words coming from suggestions to the index)
    # text = text.replace("''","'")
    
    # Load Keywords
    with open(f'extra_words.txt') as f:
        money_words = f.read().splitlines()
    money_words = [word.lower() for word in money_words]

    is_date_present = False
    # Extract words inside single or double quotes  
    quoted_words = re.findall(r'"([^"]*)"|\'([^\']*)\'', text)  

    # Flatten the list of tuples and remove empty strings  
    quoted_words = [word for words in quoted_words for word in words if word]  
  
    # Remove quoted words from the original text  
    modified_text = re.sub(r'"[^"]*"|\'[^\']*\'', '', text)  
  
    # Proceed with the existing keyword extraction process  
    modified_text = modified_text.lower()  

    # Remove date related words
    pattern = r"\b(?:january|jan|february|feb|march|mar|april|apr|may|june|jun|july|jul|august|aug|september|sep|october|oct|november|nov|december|dec|20[0-4][0-9]|2050|quarter|year|month|ytd|mtd|today|yesterday|tomorrow|qtd)\b"  
    if re.search(pattern, modified_text, flags=re.IGNORECASE):  
        is_date_present = True

    modified_text = re.sub(pattern, "", modified_text, flags=re.IGNORECASE)  
    modified_text = re.sub(r'[^a-zA-Z0-9]', ' ', modified_text)  
    modified_text = modified_text.split()  
    modified_text = [word for word in modified_text if word not in money_words]  
    if is_date_present:
        modified_text.extend(['datetime64[', 'datetime32['])
    # Combine the quoted words and the extracted keywords  
    result = quoted_words + modified_text  

    print(f"Extracted Keywords: {result}")
  
    return result, is_date_present  

def extract_columns(ix, keywords):
    """
    
    Extract columns based on given keywords by searching in attribute synonym knowledge base (kb).

    Parameters:
        ix (Index): The index to search in.
        keywords (list): A list of keywords to look for in the column names and synonyms.
            
    Returns:
        set, dict: A set of column names detected from the synonym kb and a dictionary mapping each column name to a list of keywords that were matched in it.
    """
    columns_detected = set()
    column_keywords_mapping = {}  # Dictionary to store which columns had which keywords detected

    for keyword in keywords:
        matched_columns = identify_column(ix, keyword)  # Returns a dictionary of column names to matched synonyms
        for item in matched_columns.items():
            columns_detected.add(item[0])  # Add the column to the set of detected columns
            if item[0] not in column_keywords_mapping:
                column_keywords_mapping[item[0]] = item[1]
            else:
                # Add the keyword if not already in the list for this column
                if keyword not in column_keywords_mapping[item[0]]:
                    column_keywords_mapping[item[0]].append(item[1])

    return columns_detected, column_keywords_mapping


def extract_columns_from_values(ix, keywords, use_wildcard = False):
    """
    Step 2: Looking in attribute synonym kb if keyword not found in synonym kb
    Extract columns based on given keywords by searching in attribute unique values knowledge base if keyword not found in synonym kb.
    
    Parameters:
        ix (Index): The index to search in.
        keywords (list): A list of keywords to look for in the unique values of the columns.
            
    Returns:
        set, dict: A set of column names detected from the unique values kb and a dictionary mapping each column name to a list of unique values that match any keyword.
    """
    keyword_column_mapping = dict()
    columns_detected_from_values = []
    for keyword in keywords:
        if True:  # keyword not in keywords_matched_columns:
            # keyword_column_mapping[keyword] = identify_column_from_value(keyword) # Which word occurs where and how
            temp_dict = identify_column_from_value(ix, keyword, use_wildcard)
            for item in temp_dict.items():
                if item[0] not in keyword_column_mapping:
                    keyword_column_mapping[item[0]] = item[1]
                else:
                    keyword_column_mapping[item[0]].extend(item[1])
    columns_detected_from_values = list(keyword_column_mapping.keys())
    return set(columns_detected_from_values), keyword_column_mapping

# ===================================

def get_columns_detected(ix, keywords, use_wildcard):
    """
    Extracts column names based on the given index and keywords.

    Args:
        ix: The index used to look up the columns.
        keywords: A list of keywords to match with the columns.

    Returns:
        Tuple[List[str], List[str]]: A tuple containing two lists - the first one is the columns
        detected and the second one is the columns detected from values.

    Raises:
        Exception: If an error occurs during the extraction of columns.

    Note:
        This function relies on 'extract_columns' and 'extract_columns_from_values' functions
        to perform its operations.
    """
    try:
        columns_detected, keywords_matched_columns = extract_columns(ix, keywords)
        columns_detected_from_values, keyword_column_mapping = extract_columns_from_values(ix, keywords,use_wildcard)
        return columns_detected, columns_detected_from_values
    except Exception as e:
        raise Exception(f"Error in getting columns detected: {e}")
    
def get_column_intersection_union(columns_detected, columns_detected_from_values, type='union'):
    """
    Calculates the intersection or union of two column sets.

    Args:
        columns_detected (set): A set of columns detected.
        columns_detected_from_values (set): Another set of columns detected from values.
        type (str, optional): The type of operation to perform - 'union' or 'intersection'. Defaults to 'union'.

    Returns:
        set: The resulting set of columns after performing the specified operation.

    Raises:
        ValueError: If the 'type' argument is not 'union' or 'intersection'.
    """
    if type == 'union':
        return columns_detected_from_values.union(columns_detected)
    elif type == 'intersection':
        return columns_detected_from_values.intersection(columns_detected)
    else:
        raise ValueError("Invalid type specified. Choose 'union' or 'intersection'.")


# def generate_table_schema(keyword_column_mapping, column_union):
#     """
#     Generates a schema string for a table based on the provided columns and their mapping.

#     Args:
#         keyword_column_mapping (dict): A mapping of keywords to columns.
#         column_union (set): A set of column names.

#     Returns:
#         str: A string representation of the table schema.

#     Note:
#         This function does not fetch the data type of the columns dynamically; it's set as an empty string.
#     """
#     schema_string = ''
#     for column in column_union:
#         column_data_type = ''  # Placeholder for data type extraction logic
#         if column in keyword_column_mapping:
#             schema_string += f"{column} {column_data_type}, -- has these unique values: {keyword_column_mapping[column]}\n"
#         else:
#             pass
#             schema_string += f"{column} {column_data_type}\n"
#     return schema_string

def generate_table_schema(keyword_column_mapping, keywords_matched_columns, column_union):
    schema_string = ''
    for column in column_union:
        column_data_type = ''#columns_df[columns_df['COLUMN_NAME']==column]['DATA_TYPE'].values[0].upper()
        if column in keyword_column_mapping:
            schema_string += f"{column} -- has these unique values: {str(keyword_column_mapping[column])[1:-1]} \n"
        else:
            schema_string += f"{column} -- also referred to as: {str(keywords_matched_columns[column])[1:-1]}\n"
    return schema_string


def get_dynamic_schema(user_query: str, file_name: str, search_mode:str='strict') -> str:
    """
    Generates a dynamic schema based on the user's query.

    Args:
        user_query (str): The user's query to analyze.
        file_name (str): The name of the file to load the index from.

    Returns:
        str: A string representation of the dynamic schema.

    Raises:
        Exception: If there is an error in processing the user query or loading the index.
    """
    try:
        # Get keywords
        keywords, is_date_present = extract_keywords(text=user_query)

        # Load Index
        ix = load_index(file_name=file_name)

        # Process columns and keywords
        columns_detected, keywords_matched_columns = extract_columns(ix, keywords)

        if search_mode == 'strict':
            use_wildcard = False
        else:
            use_wildcard = True

        columns_detected_from_values, keyword_column_mapping = extract_columns_from_values(ix, keywords, use_wildcard)
        column_union = get_column_intersection_union(columns_detected, columns_detected_from_values)
        schema_string = generate_table_schema(keyword_column_mapping, keywords_matched_columns, column_union)

        return schema_string
    except Exception as e:
        raise Exception(f"Error in getting dynamic schema: {e}")





