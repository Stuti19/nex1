from __future__ import annotations as _annotations

from dataclasses import dataclass
from dotenv import load_dotenv
import asyncio
import os
import json
import tiktoken
import aiohttp
from datetime import datetime

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
class ValuationDeps:
    supabase: Client
    openai_client: AsyncOpenAI

system_prompt = """
Important instruction: Do not make first line main headings and tables, but you can use sub headings and bullet points.

You are a world-class valuation analyst tasked with conducting a comprehensive valuation analysis for {stock_name}. Your expertise in financial modeling, valuation methodologies, and market analysis will produce an authoritative valuation document. This analysis will underpin billion-dollar investment decisions, demanding unparalleled precision and insight.

As an elite financial analyst, I have conducted a comprehensive valuation analysis of {stock_name} to determine its fair value and provide an investment recommendation for billion-dollar investment decisions. Based on the latest financial statements, analyst consensus, and market conditions, my analysis integrates multiple valuation approaches—discounted cash flow (DCF), relative valuation, and peer comparisons—to deliver a precise and actionable conclusion.

The analysis begins with key valuation metrics: - P/E: 16x vs. industry average of 18x, - P/B: 2.1x compared to a sector norm of 2.5x, - EV/EBITDA: 10x against a peer median of 11x, and - P/S: 1.8x, slightly below the industry's 2.0x. These figures suggest {stock_name} trades at a modest discount to its peers, potentially signaling undervaluation. The PEG ratio of 1.2x, factoring in a 13% expected earnings growth rate, reinforces this view when benchmarked against a sector average of 1.4x.

For the DCF analysis, I project revenue growth of 10% annually over the next five years, tapering to a 3% terminal rate, reflecting {stock_name}'s strong market position and industry tailwinds. Free cash flows are modeled with a 12% margin, discounted at a WACC of 8%, yielding a base-case fair value of $150 per share. Sensitivity analysis—adjusting growth rates (±2%) and discount rates (±1%)—produces a price target range of $140 to $160, with 70% confidence in the base case. Relative valuation, using an EV/EBITDA multiple of 11x (aligned with peers like Competitor A, B, and C at 11.5x, 10.8x, and 11.2x), supports this range, estimating a value of $152.

Comparing {stock_name} to its top competitors reveals a tighter operational focus but slightly lower margins, offset by a robust balance sheet with a debt-to-equity ratio of 0.4x versus the peer average of 0.6x. Unique factors, such as a pending product launch, could catalyze upside, though regulatory risks warrant caution.

Considering the discounted metrics, solid growth outlook, and DCF-derived range, I recommend a Buy with high confidence. At a current price below $140, {stock_name} offers compelling value, poised for appreciation as market recognition aligns with its fundamentals. This investment thesis balances quantitative rigor with forward-looking insight, ensuring a sound decision for stakeholders.
"""

valuation_expert = Agent(
    model,
    system_prompt=system_prompt,
    deps_type=ValuationDeps,
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

@valuation_expert.tool
async def retrieve_valuation_metrics(ctx: RunContext[ValuationDeps], stock_name: str) -> str:
    """
    Retrieve valuation metrics and related data for a specific stock.
    """
    try:
        # First try to get exact matches for valuation metrics
        results = (
            ctx.deps.supabase.from_('stock_info')
            .select('*')
            .or_(f"title.ilike.%Valuation%,title.ilike.%Financial Ratios%,title.ilike.%Metrics%")
            .ilike('content', f'%{stock_name}%')
            .limit(10)
            .execute()
        )

        # If we don't find direct matches, try a broader search
        if not results.data:
            # Generate embedding for the query
            query_embedding = await get_embedding(
                f"{stock_name} valuation metrics price earnings ratio market cap enterprise value", 
                ctx.deps.openai_client
            )
            
            # Use vector search to find relevant data
            vector_results = ctx.deps.supabase.rpc(
                'match_stock_info',
                {
                    'query_embedding': query_embedding,
                    'match_count': 10,
                    'filter': {}
                }
            ).execute()
            
            # Filter for valuation related data
            valuation_data = [
                doc for doc in vector_results.data 
                if any(term in doc.get('title', '').lower() or term in doc.get('url', '').lower() 
                      for term in ['valuation', 'ratio', 'metric', 'price', 'value'])
            ]
            
            if valuation_data:
                results.data = valuation_data

        if not results.data:
            return f"No valuation metrics found for: {stock_name}"

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
                    formatted_content = "### Valuation Metrics:\n"
                    
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
            
            formatted_data.append(f"""## {doc.get('title', 'Valuation Metrics')} - {doc.get('date', 'Date not specified')}

**Source**: {url}

**Summary**: {doc.get('summary', 'Valuation metrics for ' + stock_name)}

{content}
""")

        result = "\n\n---\n\n".join(formatted_data)
        return result

    except Exception as e:
        return f"Error retrieving valuation metrics: {str(e)}"

@valuation_expert.tool
async def retrieve_peer_comparison(ctx: RunContext[ValuationDeps], stock_name: str) -> str:
    """
    Retrieve peer comparison data for valuation analysis.
    """
    try:
        # First try to get exact matches for peer comparison
        results = (
            ctx.deps.supabase.from_('stock_info')
            .select('*')
            .or_(f"title.ilike.%Peer%,title.ilike.%Competitor%,title.ilike.%Comparison%")
            .ilike('content', f'%{stock_name}%')
            .limit(10)
            .execute()
        )

        # If we don't find direct matches, try a broader search
        if not results.data:
            query_embedding = await get_embedding(
                f"{stock_name} peer comparison competitors industry comparison valuation metrics", 
                ctx.deps.openai_client
            )
            
            vector_results = ctx.deps.supabase.rpc(
                'match_stock_info',
                {
                    'query_embedding': query_embedding,
                    'match_count': 10,
                    'filter': {}
                }
            ).execute()
            
            peer_data = [
                doc for doc in vector_results.data 
                if any(term in doc.get('title', '').lower() or term in doc.get('url', '').lower() 
                      for term in ['peer', 'competitor', 'comparison', 'industry'])
            ]
            
            if peer_data:
                results.data = peer_data

        if not results.data:
            return f"No peer comparison data found for: {stock_name}"

        # Format and return the results similar to retrieve_valuation_metrics
        sorted_results = sorted(
            results.data,
            key=lambda x: parse_date(x.get('date', '1900-01-01')),
            reverse=True
        )

        formatted_data = []
        for doc in sorted_results:
            content = doc.get('content', '')
            url = doc.get('url', '')
            
            if url.lower().endswith('.pdf'):
                content = await fetch_pdf_content(url)
            
            if content.strip().startswith('{') and content.strip().endswith('}'):
                try:
                    parsed_json = json.loads(content)
                    formatted_content = "### Peer Comparison Data:\n"
                    
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
            
            formatted_data.append(f"""## {doc.get('title', 'Peer Comparison')} - {doc.get('date', 'Date not specified')}

**Source**: {url}

**Summary**: {doc.get('summary', 'Peer comparison data for ' + stock_name)}

{content}
""")

        result = "\n\n---\n\n".join(formatted_data)
        return result

    except Exception as e:
        return f"Error retrieving peer comparison data: {str(e)}"

@valuation_expert.tool
async def web_search_valuation_estimates(ctx: RunContext[ValuationDeps], stock_name: str) -> str:
    """
    Simulate a web search for recent valuation estimates and price targets.
    """
    # This is a simulated web search - in a real implementation, this would call an actual search API
    return f"""
Simulated web search results for "{stock_name} valuation estimates and price targets":

1. [Analyst Report] {stock_name} Price Target Raised to $X
   Summary: Leading analysts have revised their price targets upward, citing strong growth prospects and improving margins.

2. [Market Analysis] Consensus Valuation Shows {stock_name} Trading at Premium
   Summary: Current market valuation metrics indicate the stock trades at a premium to industry peers, justified by superior growth rates.

3. [Research Note] DCF Analysis Suggests {stock_name} Fair Value Range
   Summary: Detailed DCF analysis points to a fair value range of $X-$Y, based on projected cash flows and current market conditions.

4. [Industry Report] Sector-wide Valuation Metrics Impact {stock_name}
   Summary: Industry-wide valuation multiples have expanded, affecting how investors value {stock_name} and its peers.

5. [Investment Bank] New Coverage Initiated on {stock_name}
   Summary: Major investment bank initiates coverage with a detailed valuation analysis and specific price targets.
"""

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
        
        deps = ValuationDeps(supabase=supabase, openai_client=openai_client)

        # Simple string variable to store the latest analysis
        valuation_result = ""

        while True:
            user_query = input("\nEnter stock name (or 'exit' to quit): ").strip()
            if user_query.lower() == 'exit':
                break

            print("\nAnalyzing valuation data... Please wait...")
            try:
                # Run the agent with all available data
                agent_response = await valuation_expert.run(
                    f"Analyze {user_query} and determine its fair value. First retrieve all relevant valuation metrics and peer comparison data, then provide a comprehensive valuation analysis with investment recommendation.", 
                    deps=deps
                )
                
                print("\nValuation Analysis:")
                print("="*80)
                
                # Store and display the analysis
                if hasattr(agent_response, 'data'):
                    valuation_result = agent_response.data
                else:
                    valuation_result = str(agent_response)
                
                print(valuation_result)
                print("="*80)
                
                print("\nAnalysis has been stored in the variable 'valuation_result'")
                
            except Exception as e:
                print(f"\nError generating valuation analysis: {str(e)}")
                print("\nDEBUGGING INFORMATION:")
                print("-"*40)
                print("1. Check your Supabase connection")
                print("2. Verify you have valuation data for this stock in your database")
                print("3. Ensure your OpenAI API key has sufficient quota")
                
                try:
                    print("\nAttempting to retrieve raw data for debugging:")
                    query_embedding = await get_embedding(f"{user_query} valuation metrics", openai_client)
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