import logging
import pandas as pd
from typing import Dict, Any, Tuple, List
from tools.chart_tool import detect_column_types

logger = logging.getLogger(__name__)

def recommend_chart_config(df: pd.DataFrame) -> Dict[str, Any]:
    """
    Analyzes DataFrame columns and returns a recommended chart configuration:
    - Type: bar, line, pie, scatter, or none
    - Suggested x_axis column
    - Suggested y_axis column
    - List of numeric and categorical columns for frontend dropdown selections
    """
    default_config = {
        "recommended_type": "none",
        "x_axis": None,
        "y_axis": None,
        "all_columns": list(df.columns) if df is not None else [],
        "numeric_columns": [],
        "categorical_columns": [],
        "date_columns": []
    }

    if df is None or df.empty or len(df.columns) < 2:
        return default_config

    try:
        date_cols, numeric_cols, categorical_cols = detect_column_types(df)
        
        default_config["numeric_columns"] = numeric_cols
        default_config["categorical_columns"] = categorical_cols
        default_config["date_columns"] = date_cols

        # Scenario 1: Date/Time column exists along with a numeric column -> Line Chart
        if date_cols and numeric_cols:
            default_config["recommended_type"] = "line"
            default_config["x_axis"] = date_cols[0]
            default_config["y_axis"] = numeric_cols[0]
            return default_config

        # Scenario 2: Categorical column and numeric column
        if categorical_cols and numeric_cols:
            cat_col = categorical_cols[0]
            num_col = numeric_cols[0]
            
            # Check unique values count to determine Pie vs Bar
            unique_count = df[cat_col].nunique()
            if 1 < unique_count <= 10:
                default_config["recommended_type"] = "pie"
            else:
                default_config["recommended_type"] = "bar"
                
            default_config["x_axis"] = cat_col
            default_config["y_axis"] = num_col
            return default_config

        # Scenario 3: At least two numeric columns -> Scatter plot
        if len(numeric_cols) >= 2:
            default_config["recommended_type"] = "scatter"
            default_config["x_axis"] = numeric_cols[0]
            default_config["y_axis"] = numeric_cols[1]
            return default_config

        # Scenario 4: Multiple categorical columns -> Count Bar
        if len(categorical_cols) >= 2:
            default_config["recommended_type"] = "bar"
            default_config["x_axis"] = categorical_cols[0]
            default_config["y_axis"] = categorical_cols[1] # Used for grouping if supported
            return default_config

        # Fallback
        if len(df.columns) >= 2:
            default_config["recommended_type"] = "bar"
            default_config["x_axis"] = df.columns[0]
            default_config["y_axis"] = df.columns[1]

        return default_config

    except Exception as e:
        logger.error(f"Error suggesting chart configuration: {str(e)}")
        return default_config
