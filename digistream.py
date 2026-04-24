import streamlit as st
import pandas as pd
import pyodbc

# Load configuration from Streamlit secrets
SERVER = st.secrets["database"].get("server", "WPVSQLFARMAGL01")
DATABASE = st.secrets["database"].get("database", "AFPE")
SCHEMA_NAME = st.secrets["database"].get("schema_name", "digitization")
TABLE_NAME = st.secrets["database"].get("table_name", "metadata_catalog")

st.set_page_config(page_title="Metadata Catalog Viewer", layout="wide")
st.title("Digitization Metadata Catalog Viewer")

@st.cache_resource
def get_connection():
    conn = pyodbc.connect(
        f"DRIVER={{ODBC Driver 17 for SQL Server}};"
        f"SERVER={SERVER};"
        f"DATABASE={DATABASE};"
        f"Trusted_Connection=yes;"
    )
    return conn

@st.cache_data
def load_data():
    query = f"""
        SELECT *
        FROM {SCHEMA_NAME}.{TABLE_NAME}
    """
    conn = get_connection()
    df = pd.read_sql(query, conn)
    return df

df = load_data()

st.write(f"Showing data from `{DATABASE}.{SCHEMA_NAME}.{TABLE_NAME}`")
st.dataframe(df, use_container_width=True)

# Sidebar filters
st.sidebar.header("Filters")
filtered_df = df.copy()

# Text search across all columns
search_text = st.sidebar.text_input("Search any value")
if search_text:
    mask = filtered_df.astype(str).apply(
        lambda col: col.str.contains(search_text, case=False, na=False)
    ).any(axis=1)
    filtered_df = filtered_df[mask]

# Per-column categorical filters
for col in filtered_df.columns:
    if filtered_df[col].dtype == "object" or str(filtered_df[col].dtype).startswith("category"):
        unique_vals = sorted(filtered_df[col].dropna().astype(str).unique())
        if 0 < len(unique_vals) <= 200:
            selected_vals = st.sidebar.multiselect(f"Filter {col}", unique_vals)
            if selected_vals:
                filtered_df = filtered_df[filtered_df[col].astype(str).isin(selected_vals)]

st.subheader("Filtered Results")
st.write(f"Rows: {len(filtered_df)}")
st.dataframe(filtered_df, use_container_width=True)