# FinSight AI Agent

An AI Agent that compares two companies’ financial performance using **Yahoo Finance** data via `yfinance`.
It analyzes and summarizes key metrics such as **market cap, profit margins, P/E ratio, and dividend yield**, then formats the output into a structured summary.

---

## Features

* Compare two publicly traded companies by ticker symbol (e.g., `AAPL` vs `MSFT`).
* Retrieves live financial data from Yahoo Finance.
* Outputs structured summaries with key financial insights.
* Built using **FastAPI** and **OpenAI’s API** for reasoning.

---

## Example Prompts

```
Compare Apple and Microsoft
How does Tesla compare to Ford?
Which performs better, Google or Amazon?
```

---

## Installation

1. **Clone the repository**

   ```bash
   git clone https://github.com/Toluwaa-o/FinSight-AI-Agent.git
   cd business-comparison-agent
   ```

2. **Install dependencies**

   ```bash
   pip install -r requirements.txt
   ```

3. **Set up environment variables**
   Create a `.env` file and add your OpenAI API key:

   ```env
   GOOGLE_API_KEY=your_api_key_here
   BASE_URL=your_llm_base_url
   MODEL=your_model_name
   ```

4. **Run the app**

   ```bash
   uvicorn main:app --reload
   ```

---

## Example Output

```
Summary:
Overall, Apple shows stronger revenue growth, while Microsoft maintains higher profit margins.

Key Points:
* Apple’s revenue growth is 12% vs Microsoft’s 8%.
* Microsoft’s profit margin is higher at 34%.
* Apple’s market cap remains larger.
* Microsoft maintains steadier expense control.

Choice:
Apple performs slightly better overall due to stronger top-line growth.
```

---

## Tech Stack

* **Python**
* **FastAPI**
* **OpenAI API**
* **yfinance**