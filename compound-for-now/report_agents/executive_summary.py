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
class ExecutiveSummaryDeps:
    supabase: Client
    openai_client: AsyncOpenAI
    financial_overview: str = ""  # Output from financial_overview agent
    industry_overview: str = ""  # Output from industry_overview agent
    valuation: str = ""  # Output from valuation_agent
    risks_and_shareholding: str = ""  # Output from risks_and_shareholding agent (if available)

system_prompt = """
Important instruction: Do not make first line main headings and tables, but you can use sub headings and bullet points.

You are a world-class financial analyst tasked with crafting a comprehensive executive summary and company overview for {stock_name}. Your expertise in blending meticulous company research with synthesis of specialist reports will produce an authoritative investment analysis document. This summary will underpin billion-dollar investment decisions, demanding unparalleled precision, insight, and integrity from your analysis.

YOUR PROCESS:
Execute these essential steps to deliver an exceptional summary:

Conduct In-Depth Research:
Leverage diverse data sources, including {stock_name}'s latest financial statements, earnings call transcripts, industry reports, market data, and competitor analyses.
Investigate:
Company Profile and Business Model: Core operations, strategic direction, and value drivers.
Product Segments and Revenue Streams: Key offerings and their revenue contributions.
Competitive Advantages and Market Position: Differentiators, market share, and peer comparison.
Financial Health and Trajectory: Critical metrics (e.g., revenue, margins, debt) and growth trends.
Industry Context and Market Dynamics: Market size, trends, regulatory factors, and economic influences.
Key Risks and Opportunities: Potential challenges and growth catalysts.

Analyze and Synthesize Specialist Reports:
Review expert analyses, including equity research, market forecasts, and economic outlooks relevant to {stock_name}.
Extract and integrate:
Prevailing strengths, weaknesses, risks, and opportunities.
Contrasting views that highlight uncertainty or potential.
Ensure all claims are data-backed, with hyperlinks to specific sections of PDF URLs (e.g., financial reports) for key figures or insights.

Craft a Compelling Executive Summary:
Distill your research and specialist insights into a 300-400 word narrative that drives investment clarity.
Emphasize:
Materiality: Highlight only decision-critical information.
Balance: Weigh strengths and risks objectively.
Integration: Link financials, market position, and industry trends cohesively.
Insight: Interpret data to reveal strategic implications.
Actionability: Offer clear, investor-ready conclusions.
Conclude with a succinct investment outlook (e.g., bullish, neutral, bearish) grounded in your analysis.

QUALITY GUIDELINES:
Precision: Verify every fact with data; cite sources via hyperlinks to exact PDF sections.
Materiality: Focus on high-impact insights that shape valuation or risk.
Balance: Present an unbiased view of pros and cons.
Integration: Show how components interrelate for a holistic perspective.
Insight: Provide analysis that goes beyond numbers to strategic meaning.
Actionability: Equip investors with decision-making clarity.

FORMATTING REQUIREMENTS:
Employ professional financial terminology.
Use bullet points for standout insights (e.g., - EBITDA: $X million, +Y% YoY).
Bold pivotal facts and figures (e.g., $500M revenue).
Maintain flawless grammar and a tone fit for C-suite and institutional investors.

HIGH-STAKES CONTEXT:
This executive summary will face rigorous scrutiny from top-tier investors and board members determining {stock_name}'s investment fate. Your work will directly influence billions in capital allocation, with no room for error. Excellence will earn you a $10,000,000 reward for the best reports, marking you as a premier analyst—while any lapse could jeopardize monumental financial outcomes.

FINAL DIRECTIVE:
Approach this with relentless precision and foresight. Your summary must transform complex data into a clear, actionable narrative that empowers billion-dollar decisions. Deliver brilliance, as the stakes—and rewards—are extraordinary.

Word Count: Aim for 300-400 words, balancing depth and brevity.
"""

executive_summary_expert = Agent(
    model,
    system_prompt=system_prompt,
    deps_type=ExecutiveSummaryDeps,
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

@executive_summary_expert.tool
async def retrieve_company_documents(ctx: RunContext[ExecutiveSummaryDeps], stock_name: str) -> str:
    """
    Retrieve documents related to a specific company that contain company profile information.
    """
    try:
        # First try to get exact matches for company documents from 'documents' title
        results = (
            ctx.deps.supabase.from_('stock_info')
            .select('*')
            .or_(f"title.ilike.%Company Profile%,title.ilike.%About%,title.ilike.%Overview%,title.eq.documents")
            .ilike('content', f'%{stock_name}%')
            .limit(10)
            .execute()
        )

        # If we don't find direct matches, try a broader search
        if not results.data:
            # Generate embedding for the query
            query_embedding = await get_embedding(f"{stock_name} company profile business model products services", ctx.deps.openai_client)
            
            # Use vector search to find relevant data
            vector_results = ctx.deps.supabase.rpc(
                'match_stock_info',
                {
                    'query_embedding': query_embedding,
                    'match_count': 10,
                    'filter': {}
                }
            ).execute()
            
            # Filter for company related data
            company_data = [
                doc for doc in vector_results.data 
                if any(term in doc.get('title', '').lower() or term in doc.get('url', '').lower() 
                      for term in ['company', 'profile', 'about', 'overview', 'business'])
            ]
            
            if company_data:
                results.data = company_data

        if not results.data:
            return f"No company documents found for: {stock_name}"

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
                    formatted_content = "Company Information:\n"
                    
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
            
            formatted_data.append(f"""Source: {url}

Summary: {doc.get('summary', 'Company information for ' + stock_name)}

{content}
""")

        result = "\n\n---\n\n".join(formatted_data)
        return result

    except Exception as e:
        return f"Error retrieving company documents: {str(e)}"

@executive_summary_expert.tool
async def retrieve_earnings_calls(ctx: RunContext[ExecutiveSummaryDeps], stock_name: str) -> str:
    """
    Retrieve earnings call transcripts for a specific stock to extract company information.
    """
    try:
        # First try to get exact matches for concall transcripts
        results = (
            ctx.deps.supabase.from_('stock_info')
            .select('*')
            .or_(f"title.ilike.%Earnings Call%,title.ilike.%Conference Call%,title.ilike.%Concall%")
            .ilike('content', f'%{stock_name}%')
            .limit(5)
            .execute()
        )

        # If we don't find direct matches, try a broader search
        if not results.data:
            # Generate embedding for the query
            query_embedding = await get_embedding(f"{stock_name} earnings call conference transcript company products segments", ctx.deps.openai_client)
            
            # Use vector search to find relevant data
            vector_results = ctx.deps.supabase.rpc(
                'match_stock_info',
                {
                    'query_embedding': query_embedding,
                    'match_count': 5,
                    'filter': {}
                }
            ).execute()
            
            # Filter for concall related data
            concall_data = [
                doc for doc in vector_results.data 
                if any(term in doc.get('title', '').lower() or term in doc.get('url', '').lower() 
                      for term in ['earnings', 'conference', 'concall', 'transcript', 'call'])
            ]
            
            if concall_data:
                results.data = concall_data

        if not results.data:
            return f"No earnings call transcripts found for extracting company information on: {stock_name}"

        # Sort results by date (newest first)
        sorted_results = sorted(
            results.data,
            key=lambda x: parse_date(x.get('date', '1900-01-01')),
            reverse=True
        )

        # Format results, but focus only on relevant parts that discuss company profile, products, etc.
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
                    formatted_content = "Earnings Call Information:\n"
                    
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
            
            formatted_data.append(f"""Source: {url}

Summary: {doc.get('summary', 'Earnings call transcript for ' + stock_name)}

{content}
""")

        result = "\n\n---\n\n".join(formatted_data)
        return result

    except Exception as e:
        return f"Error retrieving earnings calls for company information: {str(e)}"

@executive_summary_expert.tool
async def web_search_company_info(ctx: RunContext[ExecutiveSummaryDeps], stock_name: str, specific_query: str = "") -> str:
    """
    Search the web for latest information about the company.
    """
    try:
        # Format search query based on whether a specific query is provided
        search_query = f"{stock_name} {specific_query}" if specific_query else f"{stock_name} company profile products competitive advantages latest news"
        
        # This is a placeholder for the actual web search implementation
        # In a real implementation, you would use a web search API like Google, Bing, etc.
        # For now, we'll return a placeholder message
        
        # Simulate web search results with a placeholder
        search_results = f"""
Web search results for: "{search_query}"

1. [Company Website] {stock_name} - Official Website
   Company overview, products, services, and latest updates.

2. [News Article] {stock_name} Announces New Product Launch - Financial Times
   Latest news about the company's product portfolio expansion.

3. [Investor Relations] {stock_name} Investor Relations - Quarterly Results
   Financial performance and strategic updates.

4. [Industry Report] {stock_name} Market Position - Industry Analysis
   Competitive position and market share information.

5. [News] Recent Developments at {stock_name} - Business News
   Recent business developments and strategic initiatives.

Note: This is a simulated web search. In a real implementation, this would be replaced by actual web search results.
"""
        return search_results

    except Exception as e:
        return f"Error performing web search: {str(e)}"

@executive_summary_expert.tool
async def retrieve_product_segment_info(ctx: RunContext[ExecutiveSummaryDeps], stock_name: str) -> str:
    """
    Retrieve specific information about the company's product segments.
    """
    try:
        # Look for product segment information
        results = (
            ctx.deps.supabase.from_('stock_info')
            .select('*')
            .or_(f"title.ilike.%Product%,title.ilike.%Segment%,title.ilike.%Business Line%")
            .ilike('content', f'%{stock_name}%')
            .limit(8)
            .execute()
        )

        if not results.data:
            # Generate embedding for the query
            query_embedding = await get_embedding(f"{stock_name} product segments business lines offerings", ctx.deps.openai_client)
            
            # Use vector search to find relevant data
            vector_results = ctx.deps.supabase.rpc(
                'match_stock_info',
                {
                    'query_embedding': query_embedding,
                    'match_count': 8,
                    'filter': {}
                }
            ).execute()
            
            # Filter for product related data
            product_data = [
                doc for doc in vector_results.data 
                if any(term in doc.get('content', '').lower()
                      for term in ['product', 'segment', 'business line', 'offering', 'service'])
            ]
            
            if product_data:
                results.data = product_data

        if not results.data:
            return f"No specific product segment information found for: {stock_name}"

        # Format results
        formatted_data = []
        for doc in results.data:
            content = doc.get('content', '')
            
            # Try to parse JSON if applicable
            if content.strip().startswith('{') and content.strip().endswith('}'):
                try:
                    parsed_json = json.loads(content)
                    formatted_content = "Product Segment Information:\n"
                    
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
            
            formatted_data.append(f"""Source: {doc.get('url', 'Not specified')}

{content}
""")

        result = "\n\n".join(formatted_data)
        return result

    except Exception as e:
        return f"Error retrieving product segment information: {str(e)}"

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
        
        deps = ExecutiveSummaryDeps(supabase=supabase, openai_client=openai_client)

        # Simple string variable to store the latest analysis
        executive_summary_result = ""

        while True:
            user_query = input("\nEnter stock name (or 'exit' to quit): ").strip()
            if user_query.lower() == 'exit':
                break

            print("\nAnalyzing company information... Please wait...")
            try:
                # Run the agent with all available data
                agent_response = await executive_summary_expert.run(
                    f"Analyze {user_query} and create a comprehensive executive summary and company overview. First retrieve all relevant information about the company, then analyze it in detail according to the report structure.", 
                    deps=deps
                )
                
                print("\nExecutive Summary and Company Overview Analysis:")
                print("="*80)
                
                # Store and display the analysis
                if hasattr(agent_response, 'data'):
                    executive_summary_result = agent_response.data
                else:
                    executive_summary_result = str(agent_response)
                
                print(executive_summary_result)
                print("="*80)
                
                print("\nAnalysis has been stored in the variable 'executive_summary_result'")
                
            except Exception as e:
                print(f"\nError generating analysis: {str(e)}")
                print("\nDEBUGGING INFORMATION:")
                print("-"*40)
                print("1. Check your Supabase connection")
                print("2. Verify you have company data for this stock in your database")
                print("3. Ensure your OpenAI API key has sufficient quota")

    except Exception as e:
        print(f"\nSetup error: {e}")
        print("\nPlease ensure you have set these environment variables:")
        print("- SUPABASE_URL")
        print("- SUPABASE_SERVICE_KEY")
        print("- OPENAI_API_KEY")
        print("- LLM_MODEL (optional, defaults to gpt-4o-mini)")

if __name__ == "__main__":
    asyncio.run(main()) 