# visual_app.py
import streamlit as st
import pandas as pd
import plotly.express as px

# --------- PAGE CONFIG & STYLE ---------
st.set_page_config(page_title="CSV Visualizer", layout="wide")

# Simple custom CSS to brighten design
st.markdown(
    """
    <style>
    .main {
        background-color: #f8fafc;
    }
    .block-container {
        padding-top: 1.5rem;
        padding-bottom: 1.5rem;
    }
    h1, h2, h3 {
        color: #1f2933;
    }
    </style>
    """,
    unsafe_allow_html=True,
)

st.title("📊 CSV Data Visualizer & Insights")

st.markdown(
    "Upload your CSV, explore it interactively, and get quick automatically generated insights."
)

# --------- SIDEBAR ---------
with st.sidebar:
    st.header("⚙️ Controls")
    uploaded_file = st.file_uploader("Upload a CSV file", type=["csv"])
    st.markdown("---")
    st.caption("Tip: Use clean CSVs where each row has the same number of columns.")

# --------- MAIN APP ---------
if uploaded_file is not None:
    # Try normal read first, then fall back to a more tolerant parser
    try:
        df = pd.read_csv(uploaded_file)
    except pd.errors.ParserError:
        uploaded_file.seek(0)
        df = pd.read_csv(
            uploaded_file,
            on_bad_lines="skip",  # skip rows with wrong number of columns
            engine="python",      # more flexible parser
        )

    # Top: basic info
    st.subheader("📁 Dataset overview")
    c1, c2, c3 = st.columns(3)
    with c1:
        st.metric("Rows", len(df))
    with c2:
        st.metric("Columns", df.shape[1])
    with c3:
        st.metric("Numeric columns", df.select_dtypes(include=["number"]).shape[1])

    with st.expander("Show data preview", expanded=True):
        st.dataframe(df.head())

    numeric_cols = df.select_dtypes(include=["number"]).columns.tolist()
    all_cols = df.columns.tolist()

    if len(all_cols) == 0:
        st.warning("No columns found in this file.")
    else:
        # Layout: controls (left) and chart + insights (right)
        left_col, right_col = st.columns([1, 2])

        with left_col:
            st.subheader("🧩 Visualization settings")

            chart_type = st.selectbox(
                "Chart type",
                ["Line", "Bar", "Scatter", "Histogram"],
            )

            x_col = st.selectbox("X axis", all_cols, index=0)
            y_col = None

            if chart_type in ["Line", "Bar", "Scatter"]:
                if len(numeric_cols) == 0:
                    st.warning("No numeric columns available for Y axis.")
                else:
                    y_col = st.selectbox("Y axis (numeric)", numeric_cols, index=0)

            show_summary = st.checkbox("Show numeric summary (describe)", value=True)

        with right_col:
            st.subheader("📈 Visualization")

            fig = None
            if chart_type == "Line" and y_col:
                fig = px.line(df, x=x_col, y=y_col, title=f"{chart_type} chart of {y_col} by {x_col}")
                st.plotly_chart(fig, use_container_width=True)

            elif chart_type == "Bar" and y_col:
                fig = px.bar(df, x=x_col, y=y_col, title=f"{chart_type} chart of {y_col} by {x_col}")
                st.plotly_chart(fig, use_container_width=True)

            elif chart_type == "Scatter" and y_col:
                fig = px.scatter(df, x=x_col, y=y_col, title=f"{chart_type} plot of {y_col} vs {x_col}")
                st.plotly_chart(fig, use_container_width=True)

            elif chart_type == "Histogram":
                if len(numeric_cols) == 0:
                    st.warning("No numeric columns available for histogram.")
                else:
                    hist_col = st.selectbox("Column for histogram", numeric_cols, index=0)
                    fig = px.histogram(df, x=hist_col, nbins=30, title=f"Histogram of {hist_col}")
                    st.plotly_chart(fig, use_container_width=True)

            if show_summary and len(numeric_cols) > 0:
                st.markdown("### 📋 Numeric summary")
                st.dataframe(df[numeric_cols].describe().T)

        # --------- INSIGHTS GENERATOR ---------
        st.markdown("---")
        st.subheader("💡 Auto-generated insights")

        insights = []

        # Basic dataset-level insights
        if len(numeric_cols) > 0:
            num_stats = df[numeric_cols].describe()
            # Example: find column with largest mean
            mean_series = num_stats.loc["mean"].sort_values(ascending=False)
            max_mean_col = mean_series.index[0]
            max_mean_val = mean_series.iloc[0]
            insights.append(
                f"- The numeric column **{max_mean_col}** has the highest average value (≈ {max_mean_val:.2f})."
            )

            # Column with largest spread (std)
            std_series = num_stats.loc["std"].sort_values(ascending=False)
            spread_col = std_series.index[0]
            spread_val = std_series.iloc[0]
            insights.append(
                f"- **{spread_col}** shows the highest variability (standard deviation ≈ {spread_val:.2f}), indicating more spread-out values."
            )

        # Chart-specific insights
        if chart_type in ["Line", "Bar", "Scatter"] and y_col:
            y_series = df[y_col].dropna()
            if len(y_series) > 0:
                insights.append(
                    f"- The selected Y axis **{y_col}** ranges roughly from {y_series.min():.2f} to {y_series.max():.2f}."
                )
                if y_series.skew() > 1:
                    insights.append(
                        f"- **{y_col}** appears right-skewed (many smaller values and a few large ones)."
                    )
                elif y_series.skew() < -1:
                    insights.append(
                        f"- **{y_col}** appears left-skewed (many larger values and some much smaller ones)."
                    )

        if chart_type == "Histogram" and len(numeric_cols) > 0:
            col = hist_col
            col_series = df[col].dropna()
            if len(col_series) > 0:
                insights.append(
                    f"- The histogram for **{col}** suggests most values lie between approximately {col_series.quantile(0.1):.2f} and {col_series.quantile(0.9):.2f}."
                )

        if not insights:
            st.info("Not enough numeric data or selections to generate insights yet.")
        else:
            for ins in insights:
                st.markdown(ins)

else:
    st.info("Upload a CSV file from the sidebar to get started.")
