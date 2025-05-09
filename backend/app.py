from flask import Flask, request, jsonify
from flask_cors import CORS
import sqlite3
import numpy as np
from scipy.sparse import csc_matrix, csr_matrix, diags
import re
import os
import re
from nltk.stem import WordNetLemmatizer
from nltk.corpus import stopwords
import nltk
import joblib

nltk.download('wordnet')
nltk.download('stopwords')
nltk.download('omw-1.4')

app = Flask(__name__)

CORS(app)

DATABASE = 'database.db'
TABLE = 'articles_180k'
SVD_OUTPUT_DIR = 'svd_components'
DEFAULT_SVD_RANK = 300

dictionary = None
documents_info = None  
A_normalized = None
A_idf = None
idf_vector = None
N_docs = 0
M_terms = 0

current_svd_k = None
U_k = None       
s_k = None        
V_k_T = None       
s_k_inv = None     
doc_svd_norms = None

def load_svd_components(k):
    global current_svd_k, U_k, s_k, V_k_T, s_k_inv, doc_svd_norms

    if current_svd_k == k and U_k is not None:
        return True

    filename = os.path.join(SVD_OUTPUT_DIR, f'svd_k_{k}.joblib')
    print(f"Attempting to load SVD components for k={k} from {filename}...")

    try:
        svd_components = joblib.load(filename)
        loaded_k_from_file = svd_components['s_k'].shape[0]
        if loaded_k_from_file != k:
             print(f"Warning: SVD file '{filename}' contains components for rank {loaded_k_from_file}, but {k} was requested. Using loaded rank.")
             k = loaded_k_from_file

        U_k = svd_components['U_k']
        s_k = svd_components['s_k']
        V_k_T = svd_components['V_k_T']
        s_k_inv = svd_components['s_k_inv']
        doc_svd_norms = svd_components['doc_svd_norms']
        current_svd_k = k

        print(f"Successfully loaded SVD components for k={k}.")
        return True

    except FileNotFoundError:
        print(f"Error: SVD file not found for k={k} at {filename}.")
        current_svd_k, U_k, s_k, V_k_T, s_k_inv, doc_svd_norms = [None] * 6
        return False
    except KeyError as e:
         print(f"Error: Missing component in SVD file for k={k} at {filename}. Key '{e}' not found.")
         current_svd_k, U_k, s_k, V_k_T, s_k_inv, doc_svd_norms = [None] * 6
         return False
    except Exception as e:
        print(f"An error occurred loading SVD components for k={k}: {e}")
        current_svd_k, U_k, s_k, V_k_T, s_k_inv, doc_svd_norms = [None] * 6
        return False

def clean_text(text):
    if not text:
        return ""
    
    text = re.sub(r'&lt;.*?&gt;', '', text)
    text = re.sub(r'<.*?>', '', text)
    text = re.sub(r'\{\{.*?\}\}', '', text)
    text = re.sub(r'\[\[.*?\]\]', '', text)
    
    text = re.sub(r'formula[_ ]?\d+', '', text)
    text = re.sub(r'\(formula[^)]*\)', '', text)
    
    text = re.sub(r'oc\+sc', '', text)
    text = re.sub(r'oc sc', '', text)
    
    text = re.sub(r'[^a-zA-Z\s]', ' ', text)
    text = re.sub(r'\s+', ' ', text).strip()
    
    text = text.lower()
    
    tokens = text.split()
    
    stop_words = set(stopwords.words('english'))
    tokens = [token for token in tokens 
              if token not in stop_words 
              and len(token) > 2
              and not token.isdigit()]
    
    lemmatizer = WordNetLemmatizer()
    tokens = [lemmatizer.lemmatize(token) for token in tokens]
    
    unwanted_words = {'see', 'also', 'references', 'history', 'value', 'term'}
    tokens = [token for token in tokens if token not in unwanted_words]

    print(f"Przetworzono tekst: {text[:30]}...")
    
    return ' '.join(tokens)

def load_data():

    global dictionary, documents_info, A_normalized, A_idf, idf_vector, N_docs, M_terms

    if not os.path.exists(DATABASE):
        print(f"Database file not found at {DATABASE}")
        return False

    if dictionary is not None:
         print("Base data already loaded.")
         return True

    print("Loading base data from database...")
    conn = None
    try:
        conn = sqlite3.connect(DATABASE)
        cursor = conn.cursor()

        cursor.execute("SELECT content FROM dictionary")
        dict_row = cursor.fetchone()
        if dict_row:
            dictionary = dict_row[0].split()
            M_terms = len(dictionary)
            print(f"Loaded dictionary with {M_terms} terms.")
        else:
            print("Dictionary not found in database or is empty.")
            dictionary = []
            M_terms = 0
            return False

        cursor.execute(f"SELECT id, vector, link, title FROM {TABLE}")
        articles_rows = cursor.fetchall()
        N_docs = len(articles_rows)
        print(f"Loaded {N_docs} articles info.")

        if N_docs == 0:
            print("No articles found in database.")
            documents_info = []
            A_idf = None
            A_normalized = None
            idf_vector = None
            return False

        documents_info = []
        data = []
        row_ind = []
        col_ind = []

        for doc_idx, row in enumerate(articles_rows):
            doc_id, vector_str, link, title = row
            documents_info.append({"doc_idx": doc_idx, "id": doc_id, "link": link, "title": title})

            if vector_str:
                pairs = vector_str.split()
                for pair in pairs:
                    if '=' in pair:
                        try:
                            term_idx_str, count_str = pair.split('=')
                            term_idx = int(term_idx_str)
                            count = int(count_str)
                            if 0 <= term_idx < M_terms and count > 0:
                                data.append(count)
                                row_ind.append(term_idx)
                                col_ind.append(doc_idx)
                        except ValueError as e:
                            print(f"Warning: Could not parse vector pair '{pair}' for doc_id {doc_id}: {e}")
                        except Exception as e:
                            print(f"Warning: Unexpected error parsing pair '{pair}' for doc_id {doc_id}: {e}")


        if not data:
            print("No valid vector data found in articles.")
            A_tf = csc_matrix(([], ([], [])), shape=(M_terms, N_docs))
        else:
             A_tf = csc_matrix((data, (row_ind, col_ind)), shape=(M_terms, N_docs))

        print(f"Built TF matrix: shape {A_tf.shape}, {A_tf.nnz} non-zero elements.")

        term_doc_counts = (A_tf > 0).sum(axis=1).A.flatten()
        idf_values = np.zeros(M_terms)
        non_zero_term_counts_mask = term_doc_counts > 0
        if N_docs > 0:
             idf_values[non_zero_term_counts_mask] = np.log(N_docs / term_doc_counts[non_zero_term_counts_mask])
        idf_vector = idf_values
        print("Calculated IDF vector.")

        if idf_vector is not None and idf_vector.shape[0] == M_terms:
             A_idf = A_tf.multiply(idf_vector[:, None])
             print("Applied IDF weighting (A_idf).")
        else:
             print("Warning: IDF vector is invalid. Cannot calculate A_idf.")
             A_idf = None
             return False

        if A_idf is not None:
            A_idf_col_norms = np.sqrt(A_idf.power(2).sum(axis=0)).A.flatten()
            inv_norms_data = np.zeros_like(A_idf_col_norms)
            non_zero_norms_mask = A_idf_col_norms > 1e-9
            inv_norms_data[non_zero_norms_mask] = 1.0 / A_idf_col_norms[non_zero_norms_mask]
            if N_docs > 0:
                D_inv_norms = diags(inv_norms_data, offsets=0, shape=(N_docs, N_docs), format='csc')
                A_normalized = A_idf @ D_inv_norms
                print("Normalized document vectors (A_normalized).")
            else:
                print("Warning: No documents to normalize.")
                A_normalized = None
                return False
        else:
            print("Warning: A_idf is not available. Cannot calculate A_normalized.")
            A_normalized = None
            return False

        return True

    except sqlite3.Error as e:
        print(f"Database error during base data loading: {e}")
        dictionary, documents_info, A_normalized, A_idf, idf_vector = [None] * 5
        N_docs, M_terms = 0, 0
        global current_svd_k, U_k, s_k, V_k_T, s_k_inv, doc_svd_norms
        current_svd_k, U_k, s_k, V_k_T, s_k_inv, doc_svd_norms = [None] * 6
        return False
    except Exception as e:
        print(f"An unexpected error occurred during base data loading: {e}")
        dictionary, documents_info, A_normalized, A_idf, idf_vector = [None] * 5
        N_docs, M_terms = 0, 0
        current_svd_k, U_k, s_k, V_k_T, s_k_inv, doc_svd_norms = [None] * 6
        return False
    finally:
        if conn:
            conn.close()

def process_query_to_tfidf(query):
    if dictionary is None or idf_vector is None or M_terms == 0:
        print("Warning: Dictionary or IDF vector not loaded. Cannot process query.")
        return None

    query_tokens = re.findall(r'\w+', query.lower())
    if not query_tokens:
        return None

    query_tf = {}
    for token in query_tokens:
        try:
            term_idx = dictionary.index(token)
            query_tf[term_idx] = query_tf.get(term_idx, 0) + 1
        except ValueError:
            pass

    if not query_tf:
        return None

    q_data = list(query_tf.values())
    q_col_ind = list(query_tf.keys())
    q_row_ind = [0] * len(q_data)
    q_tf_sparse = csr_matrix((q_data, (q_row_ind, q_col_ind)), shape=(1, M_terms))

    idf_vector_row = idf_vector.reshape(1, -1)
    q_idf_sparse = q_tf_sparse.multiply(idf_vector_row)

    return q_idf_sparse


def fetch_content_snippets(top_results_basic_info, snippet_length=50):
    final_results = []
    if not top_results_basic_info:
        return final_results

    conn = None
    try:
        conn = sqlite3.connect(DATABASE)
        cursor = conn.cursor()

        for item in top_results_basic_info:
            doc_db_id = item["id"]

            cursor.execute("SELECT content FROM articles_180k WHERE id = ?", (doc_db_id,))
            content_row = cursor.fetchone()
            content_text = content_row[0] if content_row and content_row[0] else ""

            summary = content_text[:snippet_length]
            if len(content_text) > snippet_length:
                summary += "..."

            final_results.append({
                "title": item["title"],
                "link": item["link"],
                "summary": summary
            })

    except sqlite3.Error as e:
        print(f"Database error while fetching content for top results: {e}")
    except Exception as e:
        print(f"An unexpected error occurred while fetching content: {e}")
    finally:
        if conn:
            conn.close()

    return final_results


@app.route('/linear_search', methods=['POST'])
def linear_search():
    if A_normalized is None:
        success = load_data()
        if not success:
            return jsonify({"error": "Search data not available. Failed to load from database."}), 500
        if A_normalized is None or N_docs == 0 or M_terms == 0:
             return jsonify({"error": "Search data is empty (no dictionary or articles found)."}), 500

    data = request.get_json()
    query = clean_text(data.get('query', ''))
    print(f"Received linear search query: '{query}'")

    q_idf_sparse = process_query_to_tfidf(query)
    if q_idf_sparse is None:
        print("Query processing failed or yielded no dictionary terms.")
        return jsonify([])

    q_idf_norm = np.linalg.norm(q_idf_sparse.data)
    if q_idf_norm > 1e-9:
        q_normalized = q_idf_sparse / q_idf_norm
    else:
        print("Normalized query vector has zero norm.")
        return jsonify([])

    scores = q_normalized @ A_normalized
    scores_arr = scores.A.flatten()

    sorted_indices = np.argsort(scores_arr)[::-1]

    potential_results_basic_info = []
    for doc_idx in sorted_indices:
        score = scores_arr[doc_idx]
        if score > 1e-9:
             doc_info = documents_info[doc_idx]
             potential_results_basic_info.append({
                 "doc_idx": doc_idx,
                 "id": doc_info["id"],
                 "title": doc_info.get("title", "No Title"),
                 "link": doc_info.get("link", "#"),
             })
        else:
             break


    top_5_results_basic_info = potential_results_basic_info[:10]
    final_results = fetch_content_snippets(top_5_results_basic_info, snippet_length=100)

    print(f"Returning {len(final_results)} top results with snippets for linear search.")
    return jsonify(final_results)

@app.route('/svd_search', methods=['POST'])
def svd_search():

    data = request.get_json()
    raw_query = data.get('query', '')
    query = clean_text(raw_query)

    if not query:
         print("Cleaned query is empty.")
         return jsonify([])

    q_idf_sparse = process_query_to_tfidf(query)
    if q_idf_sparse is None or q_idf_sparse.nnz == 0: # Dodano sprawdzenie nnz > 0
        print("Query processing failed or yielded no dictionary terms.")
        return jsonify([])

    requested_k = data.get('k', DEFAULT_SVD_RANK)

    if not isinstance(requested_k, int) or requested_k <= 0:
        print(f"Invalid k value received: {requested_k}")
        return jsonify({"error": "Invalid 'k' parameter. Must be a positive integer."}), 400

    success_svd_load = load_svd_components(requested_k)
    if not success_svd_load:
        return jsonify({"error": f"SVD components for k={requested_k} could not be loaded."}), 500

    print(f"Received SVD search query: '{query}' (SVD Rank: {current_svd_k})")

    q_svd_proj_unscaled = q_idf_sparse @ U_k
    q_svd = q_svd_proj_unscaled * s_k_inv
    dot_products = q_svd @ V_k_T
    q_svd_norm = np.linalg.norm(q_svd)

    scores_arr = np.zeros(N_docs)
    denominator = q_svd_norm * doc_svd_norms
    non_zero_denominator_mask = denominator > 1e-9
    scores_arr[non_zero_denominator_mask] = dot_products.flatten()[non_zero_denominator_mask] / denominator[non_zero_denominator_mask]

    sorted_indices = np.argsort(scores_arr)[::-1]

    potential_results_basic_info = []
    for doc_idx in sorted_indices:
        score = scores_arr[doc_idx]
        if score > 1e-6:
             doc_info = documents_info[doc_idx]
             potential_results_basic_info.append({
                 "doc_idx": doc_idx,
                 "id": doc_info["id"],
                 "title": doc_info.get("title", "No Title"),
                 "link": doc_info.get("link", "#"),
             })
        else:
            break

    top_results_basic_info = potential_results_basic_info[:10] # Używamy top_n
    final_results = fetch_content_snippets(top_results_basic_info, snippet_length=200)

    print(f"Returning {len(final_results)} top results with snippets for SVD search (k={current_svd_k}).") # Zmieniono komunikat
    return jsonify(final_results)

load_data()

if __name__ == '__main__':
    if A_idf is None and (os.path.exists(DATABASE) and (M_terms > 0 or N_docs > 0)):
         print("Application starting, but data loading had issues. Search may not function.")
    elif A_idf is None and not os.path.exists(DATABASE):
         print(f"Application starting, but database file '{DATABASE}' not found. Search will not function.")
    elif A_idf is None:
         print("Application starting, but no data is available for search. Check database.")
    else:
         print("Application starting. Data and SVD components loaded successfully.")


    print("Starting Flask server...")
    app.run(port=5000, threaded=True)