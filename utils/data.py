compare_companies_json = {
    "name": "compare_companies",
    "description": "Use this tool to compare two companies' financial performance using Yahoo Finance data.",
    "parameters": {
        "type": "object",
        "properties": {
            "ticker1": {
                "type": "string",
                "description": "Stock ticker symbol of the first company (e.g., 'AAPL')"
            },
            "ticker2": {
                "type": "string",
                "description": "Stock ticker symbol of the second company (e.g., 'MSFT')"
            }
            ,
        },
        "required": ["ticker1", "ticker2"],
        "additionalProperties": False
    }
}

system_prompt = (
        "You are a financial analysis assistant. Your role is to compare companies to each other based on the data provided"
        "and provide a short analytical summary highlighting which company performs better, "
        "including key strengths and weaknesses AND finally, make a choice. Talk in clear bullet points and do not waste.\n\n"
)

output_format = """
\nFormat your final response as follows:

Summary:
Provide a short 2–3 sentence overview comparing the entities (e.g., companies, sectors, etc.). 
Focus on overall performance, trends, or key insights.

Key Points:
* Highlight 3–5 bullet points comparing important metrics or differences.
* Each point should start with either the entity name or the metric being compared.
* Be specific — use data-driven phrasing if applicable.

Choice:
Conclude with which entity performs better overall and briefly justify why.
"""

system_prompt += output_format