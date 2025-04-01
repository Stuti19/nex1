# All the financial jargons and their implications

from __future__ import annotations as _annotations

from dataclasses import dataclass
from dotenv import load_dotenv
import asyncio
import os
import json
import tiktoken
import aiohttp
from datetime import datetime
from operator import itemgetter

from pydantic_ai import Agent, ModelRetry, RunContext
from pydantic_ai.models.openai import OpenAIModel
from openai import AsyncOpenAI
from supabase import create_client, Client
from typing import List, Dict, Any, Optional, Tuple

load_dotenv()

# Initialize OpenAI model - use models with larger context if available
llm = os.getenv('LLM_MODEL', 'gpt-4o-mini')
model = OpenAIModel(llm)

@dataclass
class FinancialOverviewDeps:
    supabase: Client
    openai_client: AsyncOpenAI

system_prompt = """
Important instruction: Do not make first line main headings and tables, but you can use sub headings and bullet points.

You are a world-class financial analyst tasked with conducting a comprehensive financial analysis of {stock_name}. Your expertise in dissecting financial statements, identifying key metrics, and evaluating financial health will produce an authoritative analysis document. This analysis will underpin billion-dollar investment decisions, demanding unparalleled precision and insight.

CRITICAL MISSION CONTEXT:
Picture the retirees relying on pensions, young families saving for their children's education, and individual investors betting their life savings—all hanging in the balance based on your work. A single misstep in your analysis could trigger catastrophic losses, plunging countless lives into economic ruin. Your professional reputation and personal financial security hinge entirely on the accuracy and depth of this report. Yet, deliver a flawless analysis, and you'll not only protect these investments but also earn recognition as a top-tier analyst, unlocking prestige, career advancement, and substantial rewards.

YOUR TASK:
Produce a comprehensive 300-400 word financial overview of {stock_name} that addresses:

Revenue Analysis: Recent trends, growth rates versus industry benchmarks, and revenue composition.
Profitability: Key metrics (gross margin, operating margin, net margin), their trajectories, and notable patterns.
Balance Sheet and Capital Structure: Liquidity, solvency, efficiency, and leverage health.
Cash Flow Analysis: Sustainability, trends in operating, investing, and financing cash flows, and free cash flow strength.
Key Financial Ratios: Comparisons to industry peers, spotlighting standout strengths or weaknesses.
Financial Red Flags or Strengths: Warning signs or key advantages investors must understand.
For each aspect, include at least two key metrics with values and year-over-year (YoY) changes, emphasizing any significant deviations from industry norms or historical averages.

QUALITY GUIDELINES:
Accuracy: Every figure and calculation must be exact and verifiable. Cite sources or provide hyperlinks for all data. If calculating, show your work and reference the source.
Comprehensiveness: Address all critical financial dimensions without gaps.
Context: Benchmark metrics against industry standards and past performance for perspective.
Forward-looking: Highlight trends and their implications for future prospects.
Risk-aware: Flag vulnerabilities and strengths that could sway investment outcomes.
Insight: Move beyond numbers to interpret their meaning for investors and the company's trajectory.
FORMATTING REQUIREMENTS:
Employ precise financial terminology throughout.
Avoid section subheaders; weave the analysis into a cohesive narrative.
Use bullet points for key metrics (e.g., - Revenue: $X million, +Y% YoY).
Bold critical data points and trends (e.g., +15% revenue growth).
Include YoY comparisons where applicable.
Verify all percentages and calculations for correctness.
ADDITIONAL INSTRUCTIONS:
Craft your analysis in a professional, objective tone, suitable for a board of directors or institutional investors.
Offer reasoned judgments on {stock_name}'s financial health and outlook, considering how financial aspects interrelate.
Anticipate and address potential analyst critiques to showcase thoroughness.
Conclude with a concise investment implication (e.g., whether the financials suggest a positive, neutral, or negative outlook).
FINAL REMINDER:
This report will face scrutiny from top global investors and financial experts. A stellar analysis could skyrocket your career, while a single flaw might unravel it. The stakes are monumental—billions of dollars and real lives depend on your precision. Seize this chance to prove your brilliance.

Word Count: Target 300-400 words, balancing conciseness with depth.
"""

financial_expert = Agent(
    model,
    system_prompt=system_prompt,
    deps_type=FinancialOverviewDeps,
    retries=2
)

def count_tokens(text: str, model_name: str = "gpt-4o-mini") -> int:
    """Count the number of tokens in a text string."""
    try:
        encoding = tiktoken.encoding_for_model(model_name)
        return len(encoding.encode(text))
    except Exception:
        # Fallback to cl100k_base encoding if model-specific encoding isn't available
        encoding = tiktoken.get_encoding("cl100k_base")
        return len(encoding.encode(text))

async def get_embedding(text: str, openai_client: AsyncOpenAI) -> List[float]:
    """Get embedding vector from OpenAI."""
    try:
        response = await openai_client.embeddings.create(
            model="text-embedding-3-small",
            input=text
        )
        return response.data[0].embedding
    except Exception as e:
        print(f"Error generating embedding: {str(e)}")
        raise

async def verify_supabase_setup(supabase: Client) -> Dict[str, Any]:
    """Verify Supabase database setup and return configuration details."""
    try:
        # Check if the stock_info table exists and get its structure
        table_info = supabase.table('stock_info').select('*').limit(1).execute()
        
        # Try to get the vector similarity search function details
        function_check = supabase.rpc('match_stock_info', {
            'query_embedding': [0] * 1536,
            'match_count': 1,
            'filter': {}
        }).execute()
        
        return {
            "table_exists": bool(table_info.data),
            "function_exists": bool(function_check.data),
            "error": None
        }
    except Exception as e:
        return {
            "table_exists": False,
            "function_exists": False,
            "error": str(e)
        }

async def fetch_pdf_content(url: str) -> str:
    """Fetch PDF content from r.jina.ai service."""
    try:
        jina_url = f"https://r.jina.ai/{url}"
        async with aiohttp.ClientSession() as session:
            async with session.get(jina_url) as response:
                if response.status == 200:
                    return await response.text()
                else:
                    return f"Error fetching PDF content: HTTP {response.status}"
    except Exception as e:
        return f"Error fetching PDF content: {str(e)}"

def parse_date(date_str: str) -> datetime:
    """Parse date string to datetime object."""
    try:
        # Add your date parsing logic here based on your date format
        return datetime.strptime(date_str, "%Y-%m-%d")
    except:
        try:
            return datetime.strptime(date_str, "%d-%m-%Y")
        except:
            # Return a very old date if parsing fails
            return datetime(1900, 1, 1)

@financial_expert.tool
async def retrieve_balance_sheet_data(ctx: RunContext[FinancialOverviewDeps], stock_name: str) -> str:
    """
    Retrieve balance sheet data for a specific stock.
    """
    try:
        # First try to get exact matches for balance sheet of the stock
        results = (
            ctx.deps.supabase.from_('stock_info')
            .select('*')
            .ilike('title', 'Balance Sheet')
            .ilike('content', f'%{stock_name}%')
            .limit(10)
            .execute()
        )

        # If we don't find direct matches, try a broader search
        if not results.data:
            # Generate embedding for the query
            query_embedding = await get_embedding(f"{stock_name} balance sheet", ctx.deps.openai_client)
            
            # Use vector search to find relevant data
            vector_results = ctx.deps.supabase.rpc(
                'match_stock_info',
                {
                    'query_embedding': query_embedding,
                    'match_count': 10,
                    'filter': {}
                }
            ).execute()
            
            # Filter for balance sheet related data
            balance_sheet_data = [doc for doc in vector_results.data if 'balance' in doc.get('title', '').lower() or 'balance' in doc.get('url', '').lower()]
            
            if balance_sheet_data:
                results.data = balance_sheet_data

        if not results.data:
            return f"No balance sheet data found for: {stock_name}"

        # Format results
        formatted_data = []
        for doc in results.data:
            content = doc.get('content', '')
            
            # Try to parse the content as JSON if it appears to be JSON
            if content.strip().startswith('{') and content.strip().endswith('}'):
                try:
                    parsed_json = json.loads(content)
                    # Format JSON data in a more readable way
                    formatted_content = "### Balance Sheet Data:\n"
                    
                    # Process Years
                    if 'Years' in parsed_json:
                        years = parsed_json['Years']
                        formatted_content += f"**Time Periods**: {', '.join(years)}\n\n"
                    
                    # Process all other keys (financial items)
                    for key, value in parsed_json.items():
                        if key != 'Years':
                            formatted_content += f"**{key}**:\n"
                            if isinstance(value, list):
                                formatted_content += f"{', '.join(map(str, value))}\n"
                            elif isinstance(value, dict):
                                for sub_key, sub_value in value.items():
                                    formatted_content += f"- {sub_key}: {sub_value}\n"
                            else:
                                formatted_content += f"{value}\n"
                            formatted_content += "\n"
                    
                    content = formatted_content
                except json.JSONDecodeError:
                    # If it's not valid JSON, keep the original content
                    pass
            
            formatted_data.append(f"""## {doc.get('title', 'Balance Sheet')}

**Source**: {doc.get('url', 'Not specified')}

**Summary**: {doc.get('summary', 'Balance sheet data for ' + stock_name)}

{content}
""")

        result = "\n\n---\n\n".join(formatted_data)
        return result

    except Exception as e:
        return f"Error retrieving balance sheet data: {str(e)}"

@financial_expert.tool
async def retrieve_quarterly_results(ctx: RunContext[FinancialOverviewDeps], stock_name: str) -> str:
    """
    Retrieve quarterly financial results for a specific stock.
    """
    try:
        # Look for quarterly results
        results = (
            ctx.deps.supabase.from_('stock_info')
            .select('*')
            .or_(f"title.ilike.%Quarterly%,title.ilike.%Results%,title.ilike.%Q1%,title.ilike.%Q2%,title.ilike.%Q3%,title.ilike.%Q4%")
            .ilike('content', f'%{stock_name}%')
            .limit(8)
            .execute()
        )

        if not results.data:
            # Generate embedding for the query
            query_embedding = await get_embedding(f"{stock_name} quarterly results financial", ctx.deps.openai_client)
            
            # Use vector search to find relevant data
            vector_results = ctx.deps.supabase.rpc(
                'match_stock_info',
                {
                    'query_embedding': query_embedding,
                    'match_count': 8,
                    'filter': {}
                }
            ).execute()
            
            # Filter for quarterly results related data
            quarterly_data = [
                doc for doc in vector_results.data 
                if any(term in doc.get('title', '').lower() or term in doc.get('content', '').lower()
                      for term in ['quarterly', 'q1', 'q2', 'q3', 'q4', 'results', 'quarter'])
            ]
            
            if quarterly_data:
                results.data = quarterly_data

        if not results.data:
            return f"No quarterly results found for: {stock_name}"

        # Sort results by date (newest first)
        sorted_results = sorted(
            results.data,
            key=lambda x: parse_date(x.get('date', '1900-01-01')),
            reverse=True
        )

        # Format results
        formatted_data = []
        for doc in sorted_results:
            content = doc.get('content', '')
            url = doc.get('url', '')
            
            # If URL points to a PDF, fetch its content
            if url.lower().endswith('.pdf'):
                content = await fetch_pdf_content(url)
            
            # Try to parse the content as JSON if it appears to be JSON
            if content.strip().startswith('{') and content.strip().endswith('}'):
                try:
                    parsed_json = json.loads(content)
                    formatted_content = "### Quarterly Results:\n"
                    
                    for key, value in parsed_json.items():
                        formatted_content += f"**{key}**:\n"
                        if isinstance(value, list):
                            formatted_content += f"{', '.join(map(str, value))}\n"
                        elif isinstance(value, dict):
                            for sub_key, sub_value in value.items():
                                formatted_content += f"- {sub_key}: {sub_value}\n"
                        else:
                            formatted_content += f"{value}\n"
                        formatted_content += "\n"
                    
                    content = formatted_content
                except json.JSONDecodeError:
                    pass
            
            formatted_data.append(f"""## {doc.get('title', 'Quarterly Results')} - {doc.get('date', 'Date not specified')}

**Source**: {url}

**Summary**: {doc.get('summary', 'Quarterly results for ' + stock_name)}

{content}
""")

        result = "\n\n---\n\n".join(formatted_data)
        return result

    except Exception as e:
        return f"Error retrieving quarterly results: {str(e)}"

@financial_expert.tool
async def retrieve_ratio_data(ctx: RunContext[FinancialOverviewDeps], stock_name: str) -> str:
    """
    Retrieve financial ratios for a specific stock.
    """
    try:
        # Look for ratio data
        results = (
            ctx.deps.supabase.from_('stock_info')
            .select('*')
            .ilike('title', 'Ratios')
            .ilike('content', f'%{stock_name}%')
            .limit(5)
            .execute()
        )

        if not results.data:
            # Generate embedding for the query
            query_embedding = await get_embedding(f"{stock_name} financial ratios", ctx.deps.openai_client)
            
            # Use vector search to find relevant data
            vector_results = ctx.deps.supabase.rpc(
                'match_stock_info',
                {
                    'query_embedding': query_embedding,
                    'match_count': 5,
                    'filter': {}
                }
            ).execute()
            
            # Filter for ratio related data
            ratio_data = [doc for doc in vector_results.data if 'ratio' in doc.get('title', '').lower() or 'ratio' in doc.get('content', '').lower()]
            
            if ratio_data:
                results.data = ratio_data

        if not results.data:
            return f"No financial ratio data found for: {stock_name}"

        # Format the ratio data
        formatted_data = []
        for doc in results.data:
            content = doc.get('content', '')
            
            # Try to parse JSON if applicable
            if content.strip().startswith('{') and content.strip().endswith('}'):
                try:
                    parsed_json = json.loads(content)
                    formatted_content = "### Financial Ratios:\n"
                    
                    # Process Years if available
                    if 'Years' in parsed_json:
                        years = parsed_json['Years']
                        formatted_content += f"**Time Periods**: {', '.join(years)}\n\n"
                    
                    # Process all other keys (ratio categories)
                    for key, value in parsed_json.items():
                        if key != 'Years':
                            formatted_content += f"**{key}**:\n"
                            if isinstance(value, list):
                                formatted_content += f"{', '.join(map(str, value))}\n"
                            elif isinstance(value, dict):
                                for sub_key, sub_value in value.items():
                                    formatted_content += f"- {sub_key}: {sub_value}\n"
                            else:
                                formatted_content += f"{value}\n"
                            formatted_content += "\n"
                    
                    content = formatted_content
                except json.JSONDecodeError:
                    pass
            
            formatted_data.append(f"""## {doc.get('title', 'Financial Ratios')}

**Source**: {doc.get('url', 'Not specified')}

{content}
""")

        result = "\n\n".join(formatted_data)
        return result

    except Exception as e:
        return f"Error retrieving financial ratio data: {str(e)}"

@financial_expert.tool
async def retrieve_profit_loss_data(ctx: RunContext[FinancialOverviewDeps], stock_name: str) -> str:
    """
    Retrieve profit and loss statement data for a specific stock.
    """
    try:
        # Look for profit and loss statement data with multiple possible formats
        results = (
            ctx.deps.supabase.from_('stock_info')
            .select('*')
            .or_(f"title.ilike.%Profit%,title.ilike.%Loss%,title.ilike.%Income Statement%,title.ilike.%P&L%,title.ilike.%P and L%")
            .ilike('content', f'%{stock_name}%')
            .limit(8)
            .execute()
        )

        if not results.data:
            # Generate embedding for the query
            query_embedding = await get_embedding(f"{stock_name} profit loss income statement", ctx.deps.openai_client)
            
            # Use vector search to find relevant data
            vector_results = ctx.deps.supabase.rpc(
                'match_stock_info',
                {
                    'query_embedding': query_embedding,
                    'match_count': 8,
                    'filter': {}
                }
            ).execute()
            
            # Filter for profit and loss related data
            pl_data = [
                doc for doc in vector_results.data 
                if any(term in doc.get('title', '').lower() or term in doc.get('content', '').lower()
                      for term in ['profit', 'loss', 'income statement', 'p&l', 'revenue', 'expenses'])
            ]
            
            if pl_data:
                results.data = pl_data

        if not results.data:
            return f"No profit and loss data found for: {stock_name}"

        # Format results
        formatted_data = []
        for doc in results.data:
            content = doc.get('content', '')
            url = doc.get('url', '')
            
            # If URL points to a PDF, fetch its content
            if url.lower().endswith('.pdf'):
                content = await fetch_pdf_content(url)
            
            # Try to parse the content as JSON if it appears to be JSON
            if content.strip().startswith('{') and content.strip().endswith('}'):
                try:
                    parsed_json = json.loads(content)
                    formatted_content = "### Profit and Loss Statement:\n"
                    
                    # Process Years if available
                    if 'Years' in parsed_json:
                        years = parsed_json['Years']
                        formatted_content += f"**Time Periods**: {', '.join(years)}\n\n"
                    
                    # Process all other keys (financial items)
                    for key, value in parsed_json.items():
                        if key != 'Years':
                            formatted_content += f"**{key}**:\n"
                            if isinstance(value, list):
                                formatted_content += f"{', '.join(map(str, value))}\n"
                            elif isinstance(value, dict):
                                for sub_key, sub_value in value.items():
                                    formatted_content += f"- {sub_key}: {sub_value}\n"
                            else:
                                formatted_content += f"{value}\n"
                            formatted_content += "\n"
                    
                    content = formatted_content
                except json.JSONDecodeError:
                    pass
            
            formatted_data.append(f"""## {doc.get('title', 'Profit and Loss Statement')} - {doc.get('date', 'Date not specified')}

**Source**: {doc.get('url', 'Not specified')}

**Summary**: {doc.get('summary', 'Profit and loss data for ' + stock_name)}

{content}
""")

        result = "\n\n---\n\n".join(formatted_data)
        return result

    except Exception as e:
        return f"Error retrieving profit and loss data: {str(e)}"

async def main():
    try:
        print("\nInitializing connections...")
        supabase = create_client(
            os.getenv("SUPABASE_URL"),
            os.getenv("SUPABASE_SERVICE_KEY")
        )
        openai_client = AsyncOpenAI(api_key=os.getenv("OPENAI_API_KEY"))
        
        # Verify Supabase setup
        print("\nVerifying Supabase setup...")
        setup_status = await verify_supabase_setup(supabase)
        if setup_status["error"]:
            print(f"\nSupabase setup error: {setup_status['error']}")
            print("\nPlease ensure your Supabase database is properly configured with:")
            print("1. A 'stock_info' table with appropriate columns")
            print("2. The 'match_stock_info' vector similarity search function")
            return

        print("\nSupabase setup verified successfully")
        
        deps = FinancialOverviewDeps(supabase=supabase, openai_client=openai_client)

        # Simple string variable to store the latest analysis
        financial_overview_result = ""

        while True:
            user_query = input("\nEnter stock name (or 'exit' to quit): ").strip()
            if user_query.lower() == 'exit':
                break

            print("\nAnalyzing financial data... Please wait...")
            try:
                # Run the agent with all available data
                agent_response = await financial_expert.run(
                    f"Analyze the financial data for {user_query}. First retrieve all relevant financial information, then conduct a thorough analysis highlighting red and green flags according to the report structure.", 
                    deps=deps
                )
                
                print("\nFinancial Overview Analysis:")
                print("="*80)
                
                # Store and display the analysis
                if hasattr(agent_response, 'data'):
                    financial_overview_result = agent_response.data
                else:
                    financial_overview_result = str(agent_response)
                
                print(financial_overview_result)
                print("="*80)
                
                print("\nAnalysis has been stored in the variable 'financial_overview_result'")
                
            except Exception as e:
                print(f"\nError generating financial overview: {str(e)}")
                print("\nDEBUGGING INFORMATION:")
                print("-"*40)
                print("1. Check your Supabase connection")
                print("2. Verify you have financial data for this stock in your database")
                print("3. Ensure your OpenAI API key has sufficient quota")
                
                try:
                    print("\nAttempting to retrieve raw data for debugging:")
                    query_embedding = await get_embedding(f"{user_query} financial statements", openai_client)
                    raw_results = supabase.rpc(
                        'match_stock_info',
                        {
                            'query_embedding': query_embedding,
                            'match_count': 5,
                            'filter': {}
                        }
                    ).execute()
                    
                    if raw_results.data:
                        print(f"Found {len(raw_results.data)} matches in database with these titles:")
                        for item in raw_results.data:
                            print(f"- {item.get('title', 'Unknown')}")
                    else:
                        print(f"No matches found for '{user_query}' in the database")
                except Exception as debug_err:
                    print(f"Error during debugging: {str(debug_err)}")

    except Exception as e:
        print(f"\nSetup error: {e}")
        print("\nPlease ensure you have set these environment variables:")
        print("- SUPABASE_URL")
        print("- SUPABASE_SERVICE_KEY")
        print("- OPENAI_API_KEY")
        print("- LLM_MODEL (optional, defaults to gpt-4o-mini)")

if __name__ == "__main__":
    asyncio.run(main())
