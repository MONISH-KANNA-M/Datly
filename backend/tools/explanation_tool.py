import logging
import pandas as pd
from services.llm_service import generate_completion
from agent.prompts import EXPLANATION_SYSTEM_PROMPT, EXPLANATION_USER_PROMPT_TEMPLATE

logger = logging.getLogger(__name__)

def explain_results(question: str, sql_query: str, df: pd.DataFrame) -> str:
    """
    Asks the LLM to explain the SQL query results in simple business terms.
    
    Includes a snippet of the returned dataset (markdown format) in the LLM prompt.
    """
    logger.info("Generating business explanation for query results...")
    
    if df is None or df.empty:
        return (
            "No records were returned by this query. "
            "This indicates there are no matches in the database for the given request."
        )
        
    # Build data context
    row_count = len(df)
    cols = list(df.columns)
    
    # Get a sample snippet of the data (up to 8 rows) to prevent prompt overload
    data_snippet = df.head(8).to_markdown(index=False)
    
    # Render user prompt template
    user_prompt = EXPLANATION_USER_PROMPT_TEMPLATE.format(
        question=question,
        sql_query=sql_query,
        row_count=row_count,
        columns=", ".join(cols),
        data_snippet=data_snippet
    )
    
    try:
        explanation = generate_completion(
            system_prompt=EXPLANATION_SYSTEM_PROMPT,
            user_prompt=user_prompt,
            temperature=0.3  # Slightly higher than SQL gen for readability/style
        )
        return explanation
    except Exception as e:
        logger.error(f"Failed to generate explanation from LLM: {str(e)}")
        # Provide fallback description in case of LLM error
        return (
            f"The query successfully executed, returning {row_count} rows with columns: {', '.join(cols)}.\n\n"
            f"*Fallback notice: Could not connect to LLM to generate business explanation.*"
        )
