import sqlite3
import numpy as np
from scipy.sparse import csc_matrix, csr_matrix, diags
from scipy.sparse.linalg import svds
import re
import math
import os
import joblib # Import joblib for saving/loading objects

# --- Configuration ---
DATABASE = 'database.db'
TABLE = 'articles_180k' # Adjust table name if needed
SVD_OUTPUT_DIR = 'svd_components' # Directory to save SVD files

# List of SVD ranks (k) to compute and save
SVD_RANKS_TO_COMPUTE = [900, 1000]

# --- Data Loading (partial, only what's needed for SVD) ---
def load_base_data_for_svd(db_path, table_name):
    """
    Loads dictionary and articles to build the A_idf matrix.
    Returns A_idf, dictionary, documents_info, idf_vector.
    """
    print(f"Loading base data from {db_path}...")
    conn = None
    try:
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()

        # 1. Load dictionary
        cursor.execute("SELECT content FROM dictionary")
        dict_row = cursor.fetchone()
        if dict_row:
            dictionary = dict_row[0].split() # Assuming space-separated terms
            M_terms = len(dictionary)
            print(f"Loaded dictionary with {M_terms} terms.")
        else:
            print("Dictionary not found or empty.")
            return None, [], [], None

        # 2. Load articles info and parse vectors
        cursor.execute(f"SELECT id, vector, link, title FROM {table_name}")
        articles_rows = cursor.fetchall()
        N_docs = len(articles_rows)
        print(f"Loaded {N_docs} articles info.")

        if N_docs == 0:
            print("No articles found.")
            return None, dictionary, [], None

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
                        except ValueError:
                            print(f"Warning: Could not parse vector pair '{pair}' for doc_id {doc_id}")

        # 3. Build Term-by-Document Matrix (TF)
        A_tf = csc_matrix((data, (row_ind, col_ind)), shape=(M_terms, N_docs))
        print(f"Built TF matrix: shape {A_tf.shape}, {A_tf.nnz} non-zero elements.")

        # 4. Calculate IDF Vector
        term_doc_counts = (A_tf > 0).sum(axis=1).A.flatten()
        idf_values = np.zeros(M_terms)
        non_zero_term_counts_mask = term_doc_counts > 0
        idf_values[non_zero_term_counts_mask] = np.log(N_docs / term_doc_counts[non_zero_term_counts_mask])
        idf_vector = idf_values
        print("Calculated IDF vector.")

        # 5. Apply IDF weighting --> This is A_idf
        A_idf = A_tf.multiply(idf_vector[:, None])
        print("Applied IDF weighting (A_idf).")

        return A_idf, dictionary, documents_info, idf_vector

    except sqlite3.Error as e:
        print(f"Database error: {e}")
        return None, [], [], None
    except Exception as e:
        print(f"An unexpected error occurred during data loading: {e}")
        return None, [], [], None
    finally:
        if conn:
            conn.close()

# --- SVD Computation and Saving ---
def compute_and_save_svd(A_idf, k, output_dir):
    """
    Computes SVD for a given rank k and saves the components.
    """
    M, N = A_idf.shape
    k_svd = min(k, min(M, N) - 1) # Ensure k is valid for svds

    if k_svd <= 0:
         print(f"Skipping SVD for k={k}: Rank {k_svd} is invalid for matrix size {M}x{N}.")
         return False

    print(f"Computing SVD for k={k_svd}...")
    try:
        # svds returns singular values in ascending order
        U, s, Vh = svds(A_idf, k=k_svd)

        # Sort components by descending singular values
        sort_indices = s.argsort()[::-1]
        s_k = s[sort_indices]          # Sorted singular values (k,)
        U_k = U[:, sort_indices]       # U columns sorted accordingly (m x k)
        V_k_T = Vh[sort_indices, :]    # Vh rows sorted accordingly (k x n)

        # Calculate inverse singular values (needed for query projection)
        s_k_inv = np.zeros_like(s_k)
        non_zero_s_mask = s_k > 1e-9
        s_k_inv[non_zero_s_mask] = 1.0 / s_k[non_zero_s_mask]

        # Calculate norms of document vectors in the SVD space (rows of V_k)
        # V_k_T is k x n, so V_k is n x k. Norms are along axis=1 of V_k.
        # More efficiently: norms of columns of V_k_T
        doc_svd_norms = np.linalg.norm(V_k_T, axis=0)

        # Package components into a dictionary
        svd_components = {
            'U_k': U_k,
            's_k': s_k,
            'V_k_T': V_k_T,
            's_k_inv': s_k_inv, # Store the 1D inverse array
            'doc_svd_norms': doc_svd_norms
        }

        # Ensure output directory exists
        if not os.path.exists(output_dir):
            os.makedirs(output_dir)

        # Define filename
        filename = os.path.join(output_dir, f'svd_k_{k_svd}.joblib')

        # Save components using joblib
        print(f"Saving SVD components for k={k_svd} to {filename}...")
        joblib.dump(svd_components, filename)
        print(f"Successfully saved SVD components for k={k_svd}.")
        return True

    except Exception as e:
        print(f"An error occurred during SVD computation or saving for k={k}: {e}")
        return False

# --- Main Execution ---
if __name__ == '__main__':
    A_idf, dictionary, documents_info, idf_vector = load_base_data_for_svd(DATABASE, TABLE)

    if A_idf is None or len(dictionary) == 0 or len(documents_info) == 0 or idf_vector is None:
        print("Failed to load base data. Cannot compute SVD.")
    else:
        print("\n--- Starting SVD Computation and Saving ---")
        for k in SVD_RANKS_TO_COMPUTE:
            compute_and_save_svd(A_idf, k, SVD_OUTPUT_DIR)

        print("\n--- SVD Computation and Saving Complete ---")