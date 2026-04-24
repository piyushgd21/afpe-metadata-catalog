import streamlit as st
import pandas as pd
import pyodbc

# Load configuration from Streamlit secrets
DB_CFG = st.secrets.get("database", {})
SERVER = DB_CFG.get("server", "WPVSQLFARMAGL01")
DATABASE = DB_CFG.get("database", "AFPE")
SCHEMA_NAME = DB_CFG.get("schema_name", "digitization")
TABLE_NAME = DB_CFG.get("table_name", "metadata_catalog")
AUTH_MODE = DB_CFG.get("auth_mode", "sql").lower()
DB_USER = DB_CFG.get("username", "")
DB_PASSWORD = DB_CFG.get("password", "")
ODBC_DRIVER = DB_CFG.get("driver", "ODBC Driver 18 for SQL Server")

st.set_page_config(page_title="Metadata Catalog Viewer", layout="wide")
st.title("Digitization Metadata Catalog Viewer")

@st.cache_resource
def get_connection():
    conn_parts = [
        f"DRIVER={{{ODBC_DRIVER}}}",
        f"SERVER={SERVER}",
        f"DATABASE={DATABASE}",
        "Encrypt=yes",
        "TrustServerCertificate=yes",
        "Connection Timeout=15",
    ]

    if AUTH_MODE == "windows":
        conn_parts.append("Trusted_Connection=yes")
    else:
        conn_parts.append(f"UID={DB_USER}")
        conn_parts.append(f"PWD={DB_PASSWORD}")

    conn = pyodbc.connect(";".join(conn_parts) + ";")
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

try:
    df = load_data()
except pyodbc.Error as exc:
    st.error("Database connection failed from Streamlit Cloud.")
    st.info(
        "Set SQL credentials in app Secrets and confirm Purdue network/firewall allows access from Streamlit Cloud."
    )
    st.code(str(exc))
    st.stop()

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