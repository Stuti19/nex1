# All the details about the industry, market size, growth, trends, competitors, etc.

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
class IndustryOverviewDeps:
    supabase: Client
    openai_client: AsyncOpenAI

system_prompt = """
Important instruction: Do not make first line main headings and tables, but you can use sub headings and bullet points.

You are a world-class industry analyst tasked with conducting a comprehensive industry analysis for {stock_name}. Your expertise in analyzing market dynamics, competitive forces, and industry trends will produce an authoritative analysis document. This analysis will underpin billion-dollar investment decisions, demanding unparalleled precision and insight.

YOUR TASK:

Produce a meticulously researched and insightfully analyzed report comprising two main sections:

Industry Overview (300-400 words):
Quantify the industry's current size, projected growth trajectory, and total addressable market, citing specific figures (e.g., revenue in billions, CAGR) and sources.
Analyze key trends shaping the industry, including technological disruptions (e.g., AI adoption, automation), shifting consumer behaviors, and emerging business models.
Map the competitive landscape, detailing market concentration (e.g., HHI or top players' share), major players, and barriers to entry (e.g., capital requirements, regulation).
Assess the regulatory environment, highlighting recent changes, pending legislation, and their potential impacts on industry dynamics.
Identify and explain critical industry-specific metrics and KPIs (e.g., ARPU, churn rate), providing benchmarks for performance evaluation.
Clearly articulate {stock_name}'s positioning within this ecosystem, including its market share, strategic initiatives, and alignment with industry trends.
Peer Comparison Analysis (300-400 words):
Conduct a granular comparison of {stock_name} with its top three competitors across the following dimensions:
Market share and competitive positioning: Share percentage and rank within the industry.
Financial metrics: Revenue, gross margin, operating margin, net margin, return on equity (ROE).
Operational efficiency: Inventory turnover, days sales outstanding (DSO), asset turnover.
Growth rates: Revenue growth, earnings growth, market share growth over 1-3 years.
Product/service offerings: Breadth, innovation (e.g., new launches), differentiation.
Technological capabilities: R&D spending, patents filed, digital transformation initiatives.
Geographic presence: Revenue by region, expansion strategies.
Customer base: Target markets, customer concentration, loyalty metrics (e.g., NPS).
Synthesize the data to highlight {stock_name}'s relative strengths, weaknesses, competitive advantages (e.g., cost leadership), and strategic vulnerabilities.
Provide a forward-looking assessment of how {stock_name} is positioned to capitalize on industry opportunities and navigate challenges compared to its peers.
QUALITY GUIDELINES:

Comprehensiveness: Cover all major industry dynamics and peer metrics with no gaps.
Forward-looking: Project future industry developments (e.g., 3-5 year trends) and their implications for {stock_name} and competitors.
Competitive context: Use comparisons to illuminate {stock_name}'s unique position and potential.
Objectivity: Maintain a balanced perspective, acknowledging risks and opportunities.
Specificity: Employ precise metrics, benchmarks, and data points (e.g., "revenue grew 8% YoY vs. industry average of 5%").
Materiality: Prioritize information driving investment value and risk assessment.
Insight: Go beyond data to offer expert interpretation and strategic implications.
FORMATTING REQUIREMENTS:

Use precise, industry-specific terminology (e.g., "EBITDA margin" instead of "profitability").
Structure your report with clear section headers: "Industry Overview" and "Peer Comparison Analysis".
Employ bullet points to present key metrics and comparisons for quick reference.
Bold critical data points (e.g., 15% market share), competitive positions, and standout insights.
Include comparative tables or lists (e.g., side-by-side financial metrics) to visualize peer analysis.
Integrate forecasts, trend analyses, and projections (e.g., "expected 10% growth due to X").
ADDITIONAL INSTRUCTIONS:

Base your analysis on reputable sources such as industry reports (e.g., IBISWorld), financial statements (e.g., 10-Ks), market research, and credible news outlets. Cite key data to substantiate claims.
Conclude with a concise synthesis (50-75 words) of how {stock_name}'s industry position and peer comparison inform its investment potential.
Strive for originality, offering perspectives that transcend conventional analysis (e.g., untapped opportunities or hidden risks).
THE STAKES:
Your analysis will be scrutinized by top-tier investors and decision-makers. Excellence will safeguard billions in assets and elevate your reputation, while any oversight or miscalculation could destroy wealth, retirement funds, and livelihoods. Approach this task with unmatched precision and gravity.

REWARD FOR EXCELLENCE:
Deliver an exceptional report, and you will be recognized with a $10,000,000 bonus, cementing your status as a premier financial analyst.

Word Count: 600-700 words
"""

industry_expert = Agent(
    model,
    system_prompt=system_prompt,
    deps_type=IndustryOverviewDeps,
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

@industry_expert.tool
async def retrieve_annual_reports_for_industry(ctx: RunContext[IndustryOverviewDeps], stock_name: str) -> str:
    """
    Retrieve annual reports for a specific stock to analyze industry information.
    """
    try:
        # First try to get exact matches for annual reports
        results = (
            ctx.deps.supabase.from_('stock_info')
            .select('*')
            .or_(f"title.ilike.%Annual Report%,title.eq.documents")
            .ilike('content', f'%{stock_name}%')
            .limit(5)
            .execute()
        )

        # If we don't find direct matches, try a broader search
        if not results.data:
            # Generate embedding for the query
            query_embedding = await get_embedding(f"{stock_name} annual report industry market", ctx.deps.openai_client)
            
            # Use vector search to find relevant data
            vector_results = ctx.deps.supabase.rpc(
                'match_stock_info',
                {
                    'query_embedding': query_embedding,
                    'match_count': 8,
                    'filter': {}
                }
            ).execute()
            
            # Filter for annual report related data
            report_data = [
                doc for doc in vector_results.data 
                if any(term in doc.get('title', '').lower() or term in doc.get('url', '').lower() 
                      for term in ['annual', 'report', 'document', 'industry', 'market'])
            ]
            
            if report_data:
                results.data = report_data

        if not results.data:
            return f"No annual reports found for industry analysis on: {stock_name}"

        # Sort results by date (newest first)
        sorted_results = sorted(
            results.data,
            key=lambda x: parse_date(x.get('date', '1900-01-01')),
            reverse=True
        )

        # Format results, focusing on industry sections
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
                    formatted_content = "### Industry Information from Annual Report:\n"
                    
                    # Extract industry-relevant sections
                    industry_keys = [
                        k for k in parsed_json.keys() 
                        if any(term in k.lower() 
                              for term in ['industry', 'market', 'competitive', 'sector', 'trend', 'environment'])
                    ]
                    
                    # If no specific industry keys found, include all content
                    keys_to_process = industry_keys if industry_keys else parsed_json.keys()
                    
                    for key in keys_to_process:
                        value = parsed_json[key]
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
            
            formatted_data.append(f"""## {doc.get('title', 'Annual Report')} - {doc.get('date', 'Date not specified')}

**Source**: {url}

**Summary**: {doc.get('summary', 'Annual report with industry information for ' + stock_name)}

{content}
""")

        result = "\n\n---\n\n".join(formatted_data)
        return result

    except Exception as e:
        return f"Error retrieving annual reports for industry analysis: {str(e)}"

@industry_expert.tool
async def retrieve_earnings_calls_for_industry(ctx: RunContext[IndustryOverviewDeps], stock_name: str) -> str:
    """
    Retrieve earnings call transcripts for a specific stock to analyze industry information.
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
            query_embedding = await get_embedding(f"{stock_name} earnings call industry market competitors", ctx.deps.openai_client)
            
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
            return f"No earnings call transcripts found for industry analysis on: {stock_name}"

        # Sort results by date (newest first)
        sorted_results = sorted(
            results.data,
            key=lambda x: parse_date(x.get('date', '1900-01-01')),
            reverse=True
        )

        # Format results, focusing on industry-related discussions
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
                    formatted_content = "### Industry Information from Earnings Call:\n"
                    
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
            
            formatted_data.append(f"""## {doc.get('title', 'Earnings Call')} - {doc.get('date', 'Date not specified')}

**Source**: {url}

**Summary**: {doc.get('summary', 'Earnings call with industry information for ' + stock_name)}

{content}
""")

        result = "\n\n---\n\n".join(formatted_data)
        return result

    except Exception as e:
        return f"Error retrieving earnings calls for industry analysis: {str(e)}"

@industry_expert.tool
async def retrieve_industry_data(ctx: RunContext[IndustryOverviewDeps], stock_name: str) -> str:
    """
    Retrieve specific industry data and market analysis for a company's sector.
    """
    try:
        # Try to identify the company's industry first
        industry_query = (
            ctx.deps.supabase.from_('stock_info')
            .select('*')
            .eq('title', 'Basic Data')
            .ilike('content', f'%{stock_name}%')
            .limit(1)
            .execute()
        )
        
        industry_name = ""
        if industry_query.data:
            content = industry_query.data[0].get('content', '')
            try:
                basic_data = json.loads(content)
                industry_name = basic_data.get('Industry', '') or basic_data.get('Sector', '')
            except:
                pass
        
        search_term = f"{industry_name} industry" if industry_name else f"{stock_name} industry sector"
        
        # Look for industry specific data
        results = (
            ctx.deps.supabase.from_('stock_info')
            .select('*')
            .or_(f"title.ilike.%Industry%,title.ilike.%Sector%,title.ilike.%Market%")
            .or_(f"content.ilike.%{search_term}%,content.ilike.%{stock_name}%")
            .limit(8)
            .execute()
        )

        if not results.data:
            # Generate embedding for the query
            query_embedding = await get_embedding(f"{search_term} market size growth trends competitors", ctx.deps.openai_client)
            
            # Use vector search to find relevant data
            vector_results = ctx.deps.supabase.rpc(
                'match_stock_info',
                {
                    'query_embedding': query_embedding,
                    'match_count': 8,
                    'filter': {}
                }
            ).execute()
            
            # Filter for industry related data
            industry_data = [
                doc for doc in vector_results.data 
                if any(term in doc.get('content', '').lower()
                      for term in ['industry', 'sector', 'market', 'competitors', 'peers'])
            ]
            
            if industry_data:
                results.data = industry_data

        if not results.data:
            return f"No specific industry data found for: {stock_name} in {industry_name if industry_name else 'its sector'}"

        # Format results
        formatted_data = []
        for doc in results.data:
            content = doc.get('content', '')
            url = doc.get('url', '')
            
            # If URL points to a PDF, fetch its content
            if url.lower().endswith('.pdf'):
                content = await fetch_pdf_content(url)
            
            # Try to parse JSON if applicable
            if content.strip().startswith('{') and content.strip().endswith('}'):
                try:
                    parsed_json = json.loads(content)
                    formatted_content = "### Industry Data:\n"
                    
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
            
            formatted_data.append(f"""## {doc.get('title', 'Industry Analysis')} - {doc.get('date', 'Date not specified')}

**Source**: {doc.get('url', 'Not specified')}

{content}
""")

        result = "\n\n".join(formatted_data)
        return result

    except Exception as e:
        return f"Error retrieving industry data: {str(e)}"

@industry_expert.tool
async def web_search_industry_info(ctx: RunContext[IndustryOverviewDeps], stock_name: str, specific_query: str = "") -> str:
    """
    Search the web for industry information and latest trends.
    """
    try:
        # Try to identify the company's industry first
        industry_query = (
            ctx.deps.supabase.from_('stock_info')
            .select('*')
            .eq('title', 'Basic Data')
            .ilike('content', f'%{stock_name}%')
            .limit(1)
            .execute()
        )
        
        industry_name = ""
        if industry_query.data:
            content = industry_query.data[0].get('content', '')
            try:
                basic_data = json.loads(content)
                industry_name = basic_data.get('Industry', '') or basic_data.get('Sector', '')
            except:
                pass
        
        # Format search query based on available information
        search_term = industry_name if industry_name else f"{stock_name} industry"
        search_query = f"{search_term} {specific_query}" if specific_query else f"{search_term} market size growth trends competitors analysis"
        
        # This is a placeholder for the actual web search implementation
        # In a real implementation, you would use a web search API like Google, Bing, etc.
        
        # Simulate web search results with a placeholder
        search_results = f"""
Web search results for: "{search_query}"

1. [Industry Report] {search_term} Market Size, Share & Growth Analysis - Market Research Firm
   Current market size: $XX billion, Expected CAGR: X.X% (20XX-20XX)
   Key drivers: [Brief summary of market drivers]

2. [News Article] Latest Trends in {search_term} - Industry Publication
   Recent technological innovations, regulatory changes, and market shifts affecting the industry.

3. [Competitor Analysis] Top Players in {search_term} - Financial Times
   Market share breakdown, competitive strategies, and recent developments.

4. [Industry Forecast] Future of {search_term} - Analysis Firm
   Growth projections, emerging opportunities, and potential disruptions.

5. [Market Report] {search_term} Challenges and Opportunities - Business News
   Current challenges facing the industry and potential growth areas.

Note: This is a simulated web search. In a real implementation, this would be replaced by actual web search results.
"""
        return search_results

    except Exception as e:
        return f"Error performing web search for industry information: {str(e)}"

@industry_expert.tool
async def retrieve_peer_comparison_data(ctx: RunContext[IndustryOverviewDeps], stock_name: str) -> str:
    """
    Retrieve specific peer comparison data for competitive analysis.
    """
    try:
        # Look for peer comparison data
        results = (
            ctx.deps.supabase.from_('stock_info')
            .select('*')
            .or_(f"title.ilike.%Peer%,title.ilike.%Competitor%,title.ilike.%Comparison%")
            .ilike('content', f'%{stock_name}%')
            .limit(8)
            .execute()
        )

        if not results.data:
            # Generate embedding for the query
            query_embedding = await get_embedding(f"{stock_name} competitors peer comparison", ctx.deps.openai_client)
            
            # Use vector search to find relevant data
            vector_results = ctx.deps.supabase.rpc(
                'match_stock_info',
                {
                    'query_embedding': query_embedding,
                    'match_count': 8,
                    'filter': {}
                }
            ).execute()
            
            # Filter for peer comparison related data
            peer_data = [
                doc for doc in vector_results.data 
                if any(term in doc.get('content', '').lower()
                      for term in ['peer', 'competitor', 'comparison', 'vs', 'versus', 'competitive'])
            ]
            
            if peer_data:
                results.data = peer_data

        if not results.data:
            return f"No specific peer comparison data found for: {stock_name}"

        # Format results
        formatted_data = []
        for doc in results.data:
            content = doc.get('content', '')
            
            # Try to parse JSON if applicable
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

**Source**: {doc.get('url', 'Not specified')}

{content}
""")

        result = "\n\n".join(formatted_data)
        return result

    except Exception as e:
        return f"Error retrieving peer comparison data: {str(e)}"

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
        
        deps = IndustryOverviewDeps(supabase=supabase, openai_client=openai_client)

        # Simple string variable to store the latest analysis
        industry_overview_result = ""

        while True:
            user_query = input("\nEnter stock name (or 'exit' to quit): ").strip()
            if user_query.lower() == 'exit':
                break

            print("\nAnalyzing industry data... Please wait...")
            try:
                # Run the agent with all available data
                agent_response = await industry_expert.run(
                    f"Analyze the industry context for {user_query}. First retrieve all relevant industry information, then analyze it in detail according to the report structure.", 
                    deps=deps
                )
                
                print("\nIndustry Overview Analysis:")
                print("="*80)
                
                # Store and display the analysis
                if hasattr(agent_response, 'data'):
                    industry_overview_result = agent_response.data
                else:
                    industry_overview_result = str(agent_response)
                
                print(industry_overview_result)
                print("="*80)
                
                print("\nAnalysis has been stored in the variable 'industry_overview_result'")
                
            except Exception as e:
                print(f"\nError generating industry overview: {str(e)}")
                print("\nDEBUGGING INFORMATION:")
                print("-"*40)
                print("1. Check your Supabase connection")
                print("2. Verify you have industry data for this stock in your database")
                print("3. Ensure your OpenAI API key has sufficient quota")
                
                try:
                    print("\nAttempting to retrieve raw data for debugging:")
                    query_embedding = await get_embedding(f"{user_query} industry market", openai_client)
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
