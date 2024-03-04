# Script to implement "Search as you type" functionality

import re
from whoosh.qparser import QueryParser, FuzzyTermPlugin


def get_column_name(text):
    '''Extracts column name fro the format: column_name, dtype'''
    words = text.split(",")
    return(words[0])

def get_column_namev2(text):
    '''Processes a string from the format 'Label'('column_name', 'type') to 'Label' <'column_name'>.
    Used for identify_column function'''
    
    # Regular expression to match the label and the first item within parentheses
    pattern = r"(.+?)\('([^']+)'(?:, '[^']+')?\)"
    
    # Search for matches using the pattern
    match = re.search(pattern, text)
    if match:
        label = match.group(1)  # The label part
        column_name = match.group(2)  # The first item within parentheses
        
        # Return the formatted string
        return f"{label} <'{column_name}'>"
    else:
        # If no match is found, return the original text
        return text


def get_spelling_suggestions(searcher, query_text, search_type="unique"):
    """To get spelling suggestions"""
    if search_type == "unique":
        search_attribute = "unique_values"
    else:
        search_attribute = "synonyms"
    corrected_query = []
    for term in query_text.split():
        suggestion = searcher.corrector(search_attribute).suggest(
            term, limit=3, maxdist=2, prefix=3
        )
        if suggestion:
            corrected_query.append(suggestion[0])
        else:
            corrected_query.append(term)
    return " ".join(corrected_query)


def identify_column(ix, keyword, enable_spell_correct=False, enable_fuzzy=False):
    """To detect column names present in query and return top 5 ranked suggestions."""

    columns_detected = []
    with ix.searcher() as searcher:
        parser = QueryParser("synonyms", ix.schema)
        ###Fuzzy lookup
        if enable_fuzzy:
            parser.add_plugin(FuzzyTermPlugin())
            query = parser.parse(keyword)
        ####
        else:
            query = parser.parse(keyword)

        results = searcher.search(query, limit=None)
        results.fragmenter.charlimit = None
        # Show more context before and after
        results.fragmenter.surround = 100

        for result in results:
            # Store both the column_name and its score in a tuple
            columns_detected.append((result["column_name"], result.score))

        if enable_spell_correct and not results:
            suggested_query = get_spelling_suggestions(
                searcher, keyword, search_type="synonym"
            )
            # print(f"Did you mean(identify_column): {suggested_query}?")
            corrected_query = QueryParser("synonyms", ix.schema).parse(suggested_query)
            corrected_results = searcher.search(corrected_query, limit=None)
            for result in corrected_results:
                # Store both the column_name and its score in a tuple
                columns_detected.append((result["column_name"], result.score))

    # Sort the columns_detected list based on the scores in descending order
    sorted_columns = sorted(columns_detected, key=lambda x: x[1], reverse=True)

    # Return only the column names for e.g. this is the column name indexing -> "'AccountManager','Account Manager','Edm.String'"  while only 'Account Manager' is returned
    return [(f"'{get_column_name(column[0])}'", column[1]) for column in sorted_columns]
    # return [(f"'{column[0]}'",column[1]) for column in sorted_columns]


def identify_column_from_value(ix, keyword, enable_spell_correct=False, enable_fuzzy=False):
    matched_values = []
    parser = QueryParser("unique_values", ix.schema)
    with ix.searcher() as searcher:
        # Fuzzy lookup
        if enable_fuzzy:
            parser.add_plugin(FuzzyTermPlugin())
            query = parser.parse(keyword)
        # If not using fuzzy
        else:
            query = QueryParser("unique_values", ix.schema).parse(keyword)

        results = searcher.search(query, limit=None)
        results.fragmenter.charlimit = None
        results.fragmenter.surround = 100

        for result in results:
            search_term = result.highlights("unique_values", top=1).replace("</b>", "")
            search_term = re.sub(r'<b class="match term\d+"', "", search_term)
            search_term = search_term.split(", '")
            search_term = [re.sub(r">", "", i) for i in search_term if ">" in i]

            for value in search_term:
                # Append the value and column name in the desired format
                matched_values.append((f"{value}({result['column_name']})", result.score))

        if enable_spell_correct and not results:
            suggested_query = get_spelling_suggestions(searcher, keyword)
            # Define corrected_query here based on suggested_query
            corrected_query = parser.parse(suggested_query)  # This line was missing in the provided code snippet

            # Debugging print statement to verify corrected_query (optional)
            # print(f"Did you mean (identify_column_from_value): {suggested_query}?")

            corrected_results = searcher.search(corrected_query, limit=None)
            for result in corrected_results:
                search_term = result.highlights("unique_values", top=1).replace("</b>", "")
                search_term = re.sub(r'<b class="match term\d+"', "", search_term)
                search_term = search_term.split(", '")
                search_term = [re.sub(r">", "", i) for i in search_term if ">" in i]

                for value in search_term:
                    # Append the value and column name in the desired format for corrected results as well
                    matched_values.append((f"{value} <{get_column_name(result['column_name'])}>", result.score))


    sorted_values = sorted(matched_values, key=lambda x: x[1], reverse=True)
    # Return the matched values including the column name in the format you specified
    return [(f"'{get_column_namev2(value[0])}'", value[1]) for value in sorted_values]



def combine_search_results(
    ix, last_word, enable_spell_correct=False, enable_fuzzy=False
):
    """Combine search results from both 'synonyms' and 'unique_values' fields."""

    columns_detected_synonyms = identify_column(
        ix, last_word, enable_spell_correct, enable_fuzzy
    )
    values_detected_unique_values = identify_column_from_value(
        ix, last_word, enable_spell_correct, enable_fuzzy
    )

    # # Combine suggestions from both categories
    # combined_results = sorted_synonyms[:5] + sorted_unique_values[:5]  # uncomment

    # Combine results from both fields and then sort by scores to get relevant results on top
    combined_results = columns_detected_synonyms + values_detected_unique_values  # new
    combined_results = sorted(combined_results, key=lambda x: x[1], reverse=True)  # new

    # Return only the top 5 column names or values
    # Using split to keep only column name and not it's dtype
    combined_results = [item[0] for item in combined_results]

    combined_results = list({item: None for item in combined_results}.keys())
    return combined_results


def suggest_sentences(
    ix, input_sentence, top_k=10, enable_spell_correct=True, enable_fuzzy=False
):
    """Suggest sentences by replacing the last word with spelling suggestions."""

    words = input_sentence.split()
    last_word = words[-1]

    if len(last_word) >= 3:
        if enable_fuzzy:
            # Check if word is greater than 3 characters then only allow Fuzzy
            last_word += "~1/3"  # max edit distance of 1 and min prefix match of 3
            # print(f"Fuzzy Search:{last_word}")

        # Use the combine_search_results function to get combined suggestions for the last word
        combined_suggestions = combine_search_results(
            ix, last_word, enable_spell_correct, enable_fuzzy
        )

        suggested_sentences = []
        for suggestion in combined_suggestions:
            new_sentence = words[:-1] + [suggestion]
            suggested_sentences.append(" ".join(new_sentence))

        return suggested_sentences[:top_k]


if __name__ == "__main__":
    import sys

    if len(sys.argv) > 1:
        input_sentence = " ".join(sys.argv[1:])
        suggestions = suggest_sentences(input_sentence)
        print("Suggested sentences:")
        for suggestion in suggestions:
            print(suggestion)
    else:
        print("Usage: python search_suggestions.py <your_search_query>")
