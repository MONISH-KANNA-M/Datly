import logging
import numpy as np
import pandas as pd
from typing import List, Dict, Any
from services.llm_service import generate_completion

logger = logging.getLogger(__name__)

def detect_statistical_outliers(df: pd.DataFrame) -> List[Dict[str, Any]]:
    """
    Computes statistical anomalies using Z-score and IQR methods on numeric columns.
    Returns a list of detected anomalies.
    """
    anomalies = []
    if df is None or df.empty:
        return anomalies

    numeric_cols = df.select_dtypes(include=[np.number]).columns.tolist()
    
    # We don't want to check ID columns for statistical outliers
    numeric_cols = [c for c in numeric_cols if not str(c).lower().endswith("id")]

    for col in numeric_cols:
        col_data = df[col].dropna()
        if len(col_data) < 5:  # Too few points for robust stats
            continue

        # 1. Check using Z-score (for normal distributions)
        mean = col_data.mean()
        std = col_data.std()
        
        if std > 0:
            z_scores = (col_data - mean) / std
            outliers_z = col_data[np.abs(z_scores) > 3.0]
            for idx, val in outliers_z.items():
                anomalies.append({
                    "column": col,
                    "row_index": int(idx),
                    "value": float(val),
                    "metric": "Z-Score",
                    "reason": f"Value {val} is extremely far from column mean ({mean:.2f}) with Z-score {z_scores[idx]:.2f} (std dev is {std:.2f})."
                })

        # 2. Check using IQR (Interquartile Range) for skewed distributions
        q1 = col_data.quantile(0.25)
        q3 = col_data.quantile(0.75)
        iqr = q3 - q1
        lower_bound = q1 - 1.5 * iqr
        upper_bound = q3 + 1.5 * iqr
        
        outliers_iqr = col_data[(col_data < lower_bound) | (col_data > upper_bound)]
        # Filter outliers that are not already flagged by Z-score to avoid duplication
        flagged_rows = {a["row_index"] for a in anomalies if a["column"] == col}
        
        for idx, val in outliers_iqr.items():
            if idx in flagged_rows:
                continue
            anomalies.append({
                "column": col,
                "row_index": int(idx),
                "value": float(val),
                "metric": "IQR",
                "reason": f"Value {val} is outside standard range bounds [{lower_bound:.2f}, {upper_bound:.2f}] based on Interquartile Range."
            })

    # Sort anomalies by row index to group them
    anomalies.sort(key=lambda x: x["row_index"])
    return anomalies

def explain_anomalies(question: str, df_summary_str: str, anomalies: List[Dict[str, Any]]) -> str:
    """
    Asks Ollama to interpret the detected statistical outliers and provide a business-friendly description
    of why they might be anomalies or what business risk they pose.
    """
    if not anomalies:
        return "No statistical anomalies detected in the results."

    # Format the list of statistical findings for LLM ingestion
    anomalies_list_str = ""
    for idx, a in enumerate(anomalies[:10]):  # Limit to top 10 to fit context window
        anomalies_list_str += f"- Row {a['row_index']} | Column '{a['column']}': Value {a['value']} | Detection method: {a['metric']}. Reason: {a['reason']}\n"

    system_prompt = (
        "You are an expert business data analyst and anomaly auditor. Your job is to examine "
        "a list of statistically flagged anomalies (outliers) and explain to business managers "
        "why these points were flagged, what they mean, and if they represent potential data entry errors, "
        "operational irregularities, or noteworthy business insights."
    )

    user_prompt = (
        f"The user asked the question: '{question}'\n\n"
        f"A SQL query was executed, and the following anomalies were flagged in the returned data:\n"
        f"{anomalies_list_str}\n"
        f"Brief description of data schema context:\n"
        f"{df_summary_str}\n\n"
        f"Please write a concise 1-2 paragraph business explanation summarizing:\n"
        f"1. Why these data points are statistically or logically anomalous.\n"
        f"2. What potential business problems or events they could indicate (e.g. fraudulent activity, pricing errors, high-performing outliers).\n"
        f"Make sure to explain the reasoning clearly in plain English."
    )

    try:
        explanation = generate_completion(
            system_prompt=system_prompt,
            user_prompt=user_prompt,
            temperature=0.3
        )
        return explanation
    except Exception as e:
        logger.error(f"Error generating LLM anomaly explanation: {str(e)}")
        return "Failed to generate LLM explanation for anomalies, but outliers were logged."

def check_for_data_anomalies(question: str, df: pd.DataFrame) -> List[Dict[str, Any]]:
    """
    Main entrypoint: performs statistical anomaly profiling on the query result DataFrame
    and triggers the LLM explanation for any flagged items.
    Returns a list of structured anomaly definitions.
    """
    if df is None or df.empty:
        return []

    # Get statistical outliers
    outliers = detect_statistical_outliers(df)
    if not outliers:
        return []

    # Get string representation of dataframe metadata / summary
    summary_str = f"DataFrame shape: {df.shape}. Columns: {list(df.columns)}. Summary Stats:\n{df.describe(include='all').to_string()}"
    
    # Generate explanation
    explanation = explain_anomalies(question, summary_str, outliers)
    
    # Bundle explanation with outliers
    # We append a single general explanation item or inject the explanation into each anomaly.
    # For UI rendering, we'll store a main explanation and list of rows.
    for outlier in outliers:
        outlier["llm_explanation"] = explanation
        
    return outliers
