# Financial Analysis Report Generator

A comprehensive system for generating in-depth investment analysis reports for stocks. This tool utilizes AI agents to analyze various aspects of a company and produce a detailed HTML report.

## Features

- **Company Overview Agent**: Analyzes company background, business model, products, competitive advantages, and market position
- **Financial Overview Agent**: Examines balance sheets, quarterly results, ratios, and financial performance
- **Industry Overview Agent**: Analyzes industry context, competitive landscape, and market trends
- **Valuation Agent**: Provides valuation using appropriate methodologies (DCF, P/E, etc.) and investment recommendations
- **Risks & Shareholding Agent**: Examines shareholding patterns and key risks
- **Executive Summary Agent**: Creates a concise summary of all analyses
- **HTML Report Generator**: Compiles all analyses into a professional, interactive HTML report

## Setup

### Prerequisites

- Python 3.8+
- Supabase account (for database)
- OpenAI API key

### Installation

1. Clone the repository:
   ```
   git clone https://github.com/yourusername/financial-analysis-report-generator.git
   cd financial-analysis-report-generator
   ```

2. Install the required dependencies:
   ```
   pip install -r requirements.txt
   ```

3. Create a `.env` file in the root directory with the following variables:
   ```
   OPENAI_API_KEY=your_openai_api_key
   SUPABASE_URL=your_supabase_url
   SUPABASE_KEY=your_supabase_key
   LLM_MODEL=gpt-4o-mini  # optional, defaults to gpt-4o-mini
   ```

### Database Setup

This system uses Supabase to store and retrieve financial documents. Your Supabase database should have a `documents` table with the following structure:

- `id`: UUID (primary key)
- `content`: Text (document content)
- `metadata`: JSONB (containing fields like "type", "stock", "date", "source")
- `embedding`: Vector (for semantic search)

## Usage

### Running the Complete Analysis

Use the main entry point to generate a complete report:

```
python be/report_agents/main.py "Company Name"
```

Additional options:
```
python be/report_agents/main.py "Company Name" --output-dir ./reports --skip-agents industry_overview valuation
```

### Running Individual Agents

You can also run each agent individually:

```
python be/report_agents/company_overview.py
# Then enter the stock name when prompted
```

```
python be/report_agents/financial_overview.py
# Then enter the stock name when prompted
```

### Generating HTML from Existing Reports

If you already have the output from individual agents, you can use the HTML generator directly:

```
python be/report_agents/html_generator.py
# Follow the prompts to input each section
```

## Agent Descriptions

### Company Overview Agent
Analyzes company documents, earnings call transcripts, and web searches to build a comprehensive profile of the company, including its business model, product segments, and competitive advantages.

### Financial Overview Agent
Examines financial data from balance sheets, quarterly results, and ratios to provide insights into the company's financial health, highlighting green and red flags.

### Industry Overview Agent
Analyzes the competitive landscape, market size, and industry trends using annual reports, earnings calls, and web searches.

### Valuation Agent
Uses outputs from other agents to perform detailed valuation using relevant methodologies such as DCF, P/E ratio, or asset-based valuation, providing an investment recommendation.

### Risks & Shareholding Agent
Analyzes shareholding patterns and identifies key operational, financial, strategic, and external risks.

### Executive Summary Agent
Synthesizes outputs from all other agents to create a concise, comprehensive executive summary.

## Customization

You can modify the system prompt for each agent in their respective Python files to adjust the analysis parameters, report structure, or formatting requirements.

## License

[MIT License](LICENSE)

## Contributors

- [Your Name](https://github.com/yourusername)

## Acknowledgments

- OpenAI for providing the AI models
- Supabase for the vector database capabilities 