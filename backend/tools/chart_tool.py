import re
import logging
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from typing import Optional, Tuple, List

logger = logging.getLogger(__name__)

def detect_column_types(df: pd.DataFrame) -> Tuple[List[str], List[str], List[str]]:
    """
    Analyzes DataFrame columns and classifies them into:
    - Date/Time columns
    - Numeric columns
    - Categorical columns
    """
    date_cols = []
    numeric_cols = []
    categorical_cols = []
    
    for col in df.columns:
        # Attempt to detect dates: datetime type or string columns ending with date/time terms
        col_lower = str(col).lower()
        is_datetime = pd.api.types.is_datetime64_any_dtype(df[col])
        
        # If it's string object, try to check if it's a date string
        is_date_name = any(word in col_lower for word in ["date", "time", "timestamp", "day", "month", "year"])
        
        if is_datetime:
            date_cols.append(col)
            continue
            
        if pd.api.types.is_numeric_dtype(df[col]):
            # Exclude typical ID columns from being plotted as value metrics if they are integer
            if col_lower.endswith("id") and pd.api.types.is_integer_dtype(df[col]):
                categorical_cols.append(col)
            else:
                numeric_cols.append(col)
            continue
            
        if is_date_name:
            # Check if values can be parsed as dates
            try:
                pd.to_datetime(df[col].dropna().head(5))
                date_cols.append(col)
                continue
            except (ValueError, TypeError):
                pass
                
        # Fallback to categorical
        categorical_cols.append(col)
        
    return date_cols, numeric_cols, categorical_cols

def generate_chart(df: pd.DataFrame) -> Optional[go.Figure]:
    """
    Inspects DataFrame column types and auto-generates a Plotly Figure:
    - Date + Numeric: Line chart
    - Small category count (<=10) + Numeric: Pie chart
    - 1 Categorical + 1 Numeric: Bar chart
    - 2 Numeric: Scatter plot
    - Else: None (displays as table only)
    """
    if df is None or df.empty or len(df.columns) < 2:
        return None
        
    try:
        date_cols, numeric_cols, categorical_cols = detect_column_types(df)
        logger.info(f"Column detection - Dates: {date_cols}, Numerics: {numeric_cols}, Categoricals: {categorical_cols}")
        
        # Style theme override for premium dark-mode look
        dark_layout = dict(
            template="plotly_dark",
            paper_bgcolor="rgba(0,0,0,0)",
            plot_bgcolor="rgba(0,0,0,0)",
            margin=dict(l=40, r=40, t=50, b=40),
            font=dict(family="Outfit, Inter, sans-serif", size=12),
            xaxis=dict(gridcolor="#2d2d2d", showgrid=True),
            yaxis=dict(gridcolor="#2d2d2d", showgrid=True),
        )
        
        # Case 1: Date + Numeric -> Line chart
        if date_cols and numeric_cols:
            x_col = date_cols[0]
            y_col = numeric_cols[0]
            
            # Sort by date for proper rendering sequence
            sorted_df = df.copy()
            try:
                sorted_df[x_col] = pd.to_datetime(sorted_df[x_col])
                sorted_df = sorted_df.sort_values(by=x_col)
            except Exception:
                pass
                
            fig = px.line(
                sorted_df, x=x_col, y=y_col,
                title=f"{y_col.replace('_', ' ').title()} over {x_col.replace('_', ' ').title()}",
                color_discrete_sequence=["#636EFA"]
            )
            fig.update_layout(**dark_layout)
            return fig
            
        # Case 2: Categorical + Numeric
        if categorical_cols and numeric_cols:
            cat_col = categorical_cols[0]
            num_col = numeric_cols[0]
            
            # Check unique values count to determine Pie vs Bar
            unique_count = df[cat_col].nunique()
            
            if unique_count <= 10:
                # Small distribution -> Pie chart
                fig = px.pie(
                    df, names=cat_col, values=num_col,
                    title=f"Distribution of {num_col.replace('_', ' ').title()} by {cat_col.replace('_', ' ').title()}",
                    color_discrete_sequence=px.colors.qualitative.Pastel
                )
                fig.update_layout(**dark_layout)
                return fig
            else:
                # Large distribution -> Bar chart
                fig = px.bar(
                    df, x=cat_col, y=num_col,
                    title=f"{num_col.replace('_', ' ').title()} by {cat_col.replace('_', ' ').title()}",
                    color_discrete_sequence=["#00CC96"]
                )
                fig.update_layout(**dark_layout)
                return fig
                
        # Case 3: Numeric + Numeric -> Scatter
        if len(numeric_cols) >= 2:
            x_col = numeric_cols[0]
            y_col = numeric_cols[1]
            fig = px.scatter(
                df, x=x_col, y=y_col,
                title=f"{y_col.replace('_', ' ').title()} vs {x_col.replace('_', ' ').title()}",
                color_discrete_sequence=["#AB63FA"]
            )
            fig.update_layout(**dark_layout)
            return fig
            
        # Fallback: categorical column distribution if no numeric found
        if len(categorical_cols) >= 2:
            cat1 = categorical_cols[0]
            cat2 = categorical_cols[1]
            # Group by and count to plot
            grouped = df.groupby([cat1, cat2]).size().reset_index(name="Count")
            fig = px.bar(
                grouped, x=cat1, y="Count", color=cat2,
                title=f"Record Counts of {cat1.replace('_', ' ').title()} by {cat2.replace('_', ' ').title()}",
                barmode="group"
            )
            fig.update_layout(**dark_layout)
            return fig
            
        return None
        
    except Exception as e:
        logger.error(f"Error creating visualization: {str(e)}")
        return None
