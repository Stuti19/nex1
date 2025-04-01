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
from typing import List, Dict, Any, Optional, Tuple
from supabase import create_client, Client as SupabaseClient

load_dotenv()

# Initialize OpenAI model - use models with larger context if available
llm = os.getenv('LLM_MODEL', 'gpt-4o-mini')
model = OpenAIModel(llm)

@dataclass
class RisksAndShareholdingDeps:
    supabase: SupabaseClient
    openai_client: AsyncOpenAI

system_prompt = """
You work in a team of the world's most elite financial analysts where your specific role is risk assessment and shareholding analysis. Your job is to identify all material risks facing {stock_name} and analyze its ownership structure to inform high-stakes investment decisions.

CRITICAL MISSION CONTEXT:
Institutional investors managing retirement funds, university endowments, and family wealth will make billion-dollar decisions influenced by your analysis. If you miss critical risks or misrepresent the ownership structure, catastrophic losses could ensue, devastating countless lives and financial futures. Your professional reputation and ability to support your family depend on the thoroughness of this work.

YOUR TASK:
Research and present a comprehensive 300-400 word analysis of {stock_name}'s:
- Strategic, operational, financial, and regulatory risks
- Risk mitigation strategies and vulnerabilities
- Major shareholders and ownership concentration
- Insider trading patterns and significant ownership changes
- Institutional vs. retail ownership balance
- Management/founder ownership alignment
- Potential shareholder activism or governance concerns

QUALITY GUIDELINES:
- Comprehensiveness: Identify all material risks, not just the obvious ones
- Probability assessment: Indicate likelihood of various risk scenarios
- Impact analysis: Estimate potential financial impact of key risks
- Ownership insights: Connect shareholding patterns to potential stock behavior
- Governance implications: Assess how ownership structure affects company decisions
- Disclosure quality: Evaluate the company's transparency about risks

FORMATTING REQUIREMENTS:
- Use precise risk management and financial terminology
- Do not make any section subheaders
- Use bullet points for key risks and major shareholders
- Bold critical risk factors and ownership changes
- Categorize risks by type and severity
- Present insider trading activities in chronological context

Your risk and shareholding analysis could be the difference between protecting or losing billions in investment capital. Lives literally depend on your thoroughness and accuracy.

"""

risks_and_shareholding_expert = Agent(
    model,
    system_prompt=system_prompt,
    deps_type=RisksAndShareholdingDeps,
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

async def get_embedding(text: str, client: AsyncOpenAI, model: str = "text-embedding-3-small") -> List[float]:
    """Get embedding for text using OpenAI API."""
    text = text.replace("\n", " ")
    return (await client.embeddings.create(input=[text], model=model)).data[0].embedding

def verify_supabase_setup(client: SupabaseClient) -> bool:
    """Verify that the Supabase database has the expected tables."""
    try:
        # Get available tables in the database
        result = client.table('stock_info').select('id').limit(1).execute()
        # If no exception occurs, the connection is successful
        return True
    except Exception as e:
        print(f"Error verifying Supabase setup: {e}")
        return False

async def fetch_pdf_content(url: str) -> str:
    """Simulate fetching PDF content from a URL."""
    # In a real implementation, this would use a PDF parsing library
    return f"Content extracted from PDF at {url}. This is a placeholder for actual PDF content."

def parse_date(date_string: str) -> Optional[datetime]:
    """Parse a date string into a datetime object."""
    date_formats = [
        "%Y-%m-%d",
        "%d/%m/%Y",
        "%d-%m-%Y",
        "%m/%d/%Y",
        "%Y/%m/%d",
        "%B %d, %Y",
        "%d %B %Y",
        "%Y"
    ]
    
    for fmt in date_formats:
        try:
            return datetime.strptime(date_string, fmt)
        except ValueError:
            continue
    
    return None

@risks_and_shareholding_expert.tool
async def retrieve_shareholding_patterns(ctx: RunContext[RisksAndShareholdingDeps], stock_name: str) -> str:
    """
    Retrieve shareholding pattern data for a specific stock.
    """
    try:
        # First try to get exact matches for shareholding patterns from 'documents' title
        results = (
            ctx.deps.supabase.from_('stock_info')
            .select('*')
            .eq('title', 'documents')  # Look for 'documents' title like annual_report.py
            .ilike('content', f'%{stock_name}%')
            .execute()
        )

        # If we don't find direct matches, try a broader search
        if not results.data:
            # Generate embedding for the query
            query_embedding = await get_embedding(f"{stock_name} shareholding pattern ownership structure", ctx.deps.openai_client)
            
            # Use vector search to find relevant data
            vector_results = ctx.deps.supabase.rpc(
                'match_stock_info',
                {
                    'query_embedding': query_embedding,
                    'match_count': 10,
                    'filter': {}
                }
            ).execute()
            
            # Filter for shareholding pattern related data
            shareholding_data = [
                doc for doc in vector_results.data 
                if any(term in doc.get('title', '').lower() or term in doc.get('url', '').lower() 
                      for term in ['shareholding', 'ownership', 'stakeholder', 'promoter'])
            ]
            
            if shareholding_data:
                results.data = shareholding_data

        if not results.data:
            return f"No shareholding pattern data found for: {stock_name}"

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
                    formatted_content = "### Shareholding Pattern:\n"
                    
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
            
            formatted_data.append(f"""## {doc.get('title', 'Shareholding Pattern')} - {doc.get('date', 'Date not specified')}

**Source**: {url}

**Summary**: {doc.get('summary', 'Shareholding pattern for ' + stock_name)}

{content}
""")

        result = "\n\n---\n\n".join(formatted_data)
        return result

    except Exception as e:
        return f"Error retrieving shareholding pattern data: {str(e)}"

@risks_and_shareholding_expert.tool
async def retrieve_insider_trading_data(ctx: RunContext[RisksAndShareholdingDeps], stock_name: str) -> str:
    """
    Retrieve insider trading data for a specific stock.
    """
    try:
        # First try to get exact matches from 'documents' title
        results = (
            ctx.deps.supabase.from_('stock_info')
            .select('*')
            .eq('title', 'documents')  # Look for 'documents' title
            .ilike('content', f'%{stock_name}%')
            .execute()
        )

        # If we don't find direct matches, try vector search
        if not results.data:
            query_embedding = await get_embedding(f"{stock_name} insider trading promoter transactions", ctx.deps.openai_client)
            
            vector_results = ctx.deps.supabase.rpc(
                'match_stock_info',
                {
                    'query_embedding': query_embedding,
                    'match_count': 10,
                    'filter': {}
                }
            ).execute()
            
            insider_data = [
                doc for doc in vector_results.data 
                if any(term in doc.get('title', '').lower() or term in doc.get('content', '').lower() 
                      for term in ['insider', 'promoter', 'transaction', 'trading'])
            ]
            
            if insider_data:
                results.data = insider_data

        if not results.data:
            return f"No insider trading data found for: {stock_name}"

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
                    formatted_content = "### Insider Trading:\n"
                    
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
            
            formatted_data.append(f"""## {doc.get('title', 'Insider Trading')} - {doc.get('date', 'Date not specified')}

**Source**: {url}

**Summary**: {doc.get('summary', 'Insider trading for ' + stock_name)}

{content}
""")

        result = "\n\n---\n\n".join(formatted_data)
        return result

    except Exception as e:
        return f"Error retrieving insider trading data: {str(e)}"

@risks_and_shareholding_expert.tool
async def retrieve_operational_risk_data(ctx: RunContext[RisksAndShareholdingDeps], stock_name: str) -> str:
    """
    Retrieve data related to operational risks for a specific stock.
    Includes supply chain issues, production bottlenecks, regulatory challenges, etc.
    """
    try:
        # First try exact match for risk-related documents
        result = (
            ctx.deps.supabase.table("stock_info")
            .select("*")
            .ilike("title", stock_name)
            .execute()
        )
        
        documents = result.data
        
        # If no exact matches, try vector search
        if not documents or len(documents) < 2:
            print(f"Limited risk data for {stock_name}, using vector search...")
            
            # Generate embedding for the search
            search_text = f"operational risks, supply chain risks, production risks, regulatory risks for {stock_name}"
            embedding = await get_embedding(search_text, ctx.deps.openai_client)
            
            # Vector search for relevant documents
            result = (
                ctx.deps.supabase.rpc(
                    "match_stock_info", 
                    {
                        "query_embedding": embedding,
                        "match_threshold": 0.7,
                        "match_count": 10
                    }
                )
                .execute()
            )
            
            # Combine with any existing documents
            documents.extend(result.data)
        
        if not documents:
            return f"No operational risk data found for {stock_name}."
        
        # Filter for risk-related content
        risk_keywords = ["risk", "challenge", "threat", "vulnerability", "disruption", "bottleneck", "compliance"]
        filtered_documents = []
        for doc in documents:
            content = doc.get("content", "").lower()
            if any(keyword in content for keyword in risk_keywords):
                filtered_documents.append(doc)
        
        if filtered_documents:
            documents = filtered_documents
        
        # Sort documents by date (most recent first)
        documents_with_dates = []
        for doc in documents:
            date_str = doc.get("date")
            date = parse_date(date_str) if date_str else None
            documents_with_dates.append((doc, date))
        
        documents_with_dates.sort(key=lambda x: x[1] if x[1] else datetime.min, reverse=True)
        documents = [doc for doc, _ in documents_with_dates]
        
        # Format the results
        results = []
        for doc in documents[:5]:  # Limit to most relevant 5 documents
            content = doc.get("content", "")
            metadata = doc.get("metadata", {})
            doc_type = metadata.get("type", "unknown")
            date = metadata.get("date", "unknown date")
            source = metadata.get("source", "unknown source")
            
            # Check if it's a PDF that needs to be fetched
            if doc_type.lower() == "pdf" and metadata.get("url"):
                content = await fetch_pdf_content(metadata.get("url"))
            
            results.append(f"--- Risk Document ---\nDate: {date}\nSource: {source}\nType: {doc_type}\n\nContent:\n{content}\n\n")
        
        return "\n".join(results)
        
    except Exception as e:
        return f"Error retrieving operational risk data: {str(e)}"

@risks_and_shareholding_expert.tool
async def retrieve_financial_risk_data(ctx: RunContext[RisksAndShareholdingDeps], stock_name: str) -> str:
    """
    Retrieve data related to financial risks for a specific stock.
    Includes liquidity issues, debt structures, currency exposures, etc.
    """
    try:
        # First try exact match for financial risk documents
        result = (
            ctx.deps.supabase.table("stock_info")
            .select("*")
            .ilike("title", stock_name)
            .execute()
        )
        
        documents = result.data
        
        # If no exact matches, try vector search
        if not documents or len(documents) < 2:
            print(f"Limited financial risk data for {stock_name}, using vector search...")
            
            # Generate embedding for the search
            search_text = f"financial risks, debt structure, liquidity, currency exposure for {stock_name}"
            embedding = await get_embedding(search_text, ctx.deps.openai_client)
            
            # Vector search for relevant documents
            result = (
                ctx.deps.supabase.rpc(
                    "match_stock_info", 
                    {
                        "query_embedding": embedding,
                        "match_threshold": 0.7,
                        "match_count": 10
                    }
                )
                .execute()
            )
            
            # Combine with any existing documents
            documents.extend(result.data)
        
        if not documents:
            return f"No financial risk data found for {stock_name}."
        
        # Filter for financial risk-related content
        financial_risk_keywords = ["debt", "leverage", "liquidity", "solvency", "currency", "interest rate", "default", "credit"]
        filtered_documents = []
        for doc in documents:
            content = doc.get("content", "").lower()
            if any(keyword in content for keyword in financial_risk_keywords):
                filtered_documents.append(doc)
        
        if filtered_documents:
            documents = filtered_documents
        
        # Sort documents by date (most recent first)
        documents_with_dates = []
        for doc in documents:
            date_str = doc.get("date")
            date = parse_date(date_str) if date_str else None
            documents_with_dates.append((doc, date))
        
        documents_with_dates.sort(key=lambda x: x[1] if x[1] else datetime.min, reverse=True)
        documents = [doc for doc, _ in documents_with_dates]
        
        # Format the results
        results = []
        for doc in documents[:5]:  # Limit to most relevant 5 documents
            content = doc.get("content", "")
            metadata = doc.get("metadata", {})
            doc_type = metadata.get("type", "unknown")
            date = metadata.get("date", "unknown date")
            source = metadata.get("source", "unknown source")
            
            # Check if it's a PDF that needs to be fetched
            if doc_type.lower() == "pdf" and metadata.get("url"):
                content = await fetch_pdf_content(metadata.get("url"))
            
            results.append(f"--- Financial Risk Document ---\nDate: {date}\nSource: {source}\nType: {doc_type}\n\nContent:\n{content}\n\n")
        
        return "\n".join(results)
        
    except Exception as e:
        return f"Error retrieving financial risk data: {str(e)}"

@risks_and_shareholding_expert.tool
async def retrieve_strategic_and_external_risks(ctx: RunContext[RisksAndShareholdingDeps], stock_name: str) -> str:
    """
    Retrieve data related to strategic and external risks for a specific stock.
    Includes competitive threats, market share pressures, regulatory risks, etc.
    """
    try:
        # First try to find annual reports which often contain risk factors
        result = (
            ctx.deps.supabase.table("stock_info")
            .select("*")
            .ilike("title", "annual_report")
            .ilike("content", f"%{stock_name}%")
            .execute()
        )
        
        annual_reports = result.data
        
        # Also look for risk-specific documents
        result = (
            ctx.deps.supabase.table("stock_info")
            .select("*")
            .ilike("title", stock_name)
            .execute()
        )
        
        risk_documents = result.data
        
        # Combine documents
        documents = annual_reports + risk_documents
        
        # If insufficient matches, try vector search
        if len(documents) < 3:
            print(f"Limited strategic risk data for {stock_name}, using vector search...")
            
            # Generate embedding for the search
            search_text = f"strategic risks, competitive threats, market share risks, regulatory risks for {stock_name}"
            embedding = await get_embedding(search_text, ctx.deps.openai_client)
            
            # Vector search for relevant documents
            result = (
                ctx.deps.supabase.rpc(
                    "match_stock_info", 
                    {
                        "query_embedding": embedding,
                        "match_threshold": 0.7,
                        "match_count": 10
                    }
                )
                .execute()
            )
            
            # Add additional documents
            documents.extend(result.data)
        
        if not documents:
            return f"No strategic or external risk data found for {stock_name}."
        
        # Filter for strategic and external risk-related content
        risk_keywords = ["competitive", "market share", "regulation", "policy", "legislation", "technology disruption", "obsolescence"]
        filtered_documents = []
        for doc in documents:
            content = doc.get("content", "").lower()
            if any(keyword in content for keyword in risk_keywords):
                filtered_documents.append(doc)
        
        if filtered_documents:
            documents = filtered_documents
        
        # Remove duplicates
        unique_documents = []
        doc_ids = set()
        for doc in documents:
            if doc.get("id") not in doc_ids:
                unique_documents.append(doc)
                doc_ids.add(doc.get("id"))
        
        documents = unique_documents
        
        # Sort documents by date (most recent first)
        documents_with_dates = []
        for doc in documents:
            date_str = doc.get("date")
            date = parse_date(date_str) if date_str else None
            documents_with_dates.append((doc, date))
        
        documents_with_dates.sort(key=lambda x: x[1] if x[1] else datetime.min, reverse=True)
        documents = [doc for doc, _ in documents_with_dates]
        
        # Format the results
        results = []
        for doc in documents[:5]:  # Limit to most relevant 5 documents
            content = doc.get("content", "")
            metadata = doc.get("metadata", {})
            doc_type = metadata.get("type", "unknown")
            date = metadata.get("date", "unknown date")
            source = metadata.get("source", "unknown source")
            
            # Check if it's a PDF that needs to be fetched
            if doc_type.lower() == "pdf" and metadata.get("url"):
                content = await fetch_pdf_content(metadata.get("url"))
            elif doc_type.lower() == "annual_report":
                # Look for risk sections in annual reports
                lower_content = content.lower()
                
                # Try to extract risk factors section
                risk_section_start = max(
                    lower_content.find("risk factors"),
                    lower_content.find("principal risks"),
                    lower_content.find("key risks")
                )
                
                if risk_section_start != -1:
                    # Find the next section header (usually uppercase or starts with #)
                    next_section_start = len(content)
                    possible_next_sections = ["#", "FINANCIAL", "MANAGEMENT", "GOVERNANCE", "BOARD", "DIRECTORS"]
                    
                    for section in possible_next_sections:
                        pos = content.find(section, risk_section_start + 100)  # Skip a bit to avoid finding matches in the risk section itself
                        if pos != -1 and pos < next_section_start:
                            next_section_start = pos
                    
                    # Extract the risk section
                    content = content[risk_section_start:next_section_start].strip()
            
            results.append(f"--- Strategic/External Risk Document ---\nDate: {date}\nSource: {source}\nType: {doc_type}\n\nContent:\n{content}\n\n")
        
        return "\n".join(results)
        
    except Exception as e:
        return f"Error retrieving strategic and external risk data: {str(e)}"

@risks_and_shareholding_expert.tool
async def web_search_for_recent_risks(ctx: RunContext[RisksAndShareholdingDeps], stock_name: str) -> str:
    """
    Simulate a web search for recent news about risks for a specific stock.
    """
    # This is a simulated web search - in a real implementation, this would call an actual search API
    return f"""
Simulated web search results for "{stock_name} risks":

1. [Financial News] {stock_name} Faces Supply Chain Disruptions Due to Global Semiconductor Shortage
   Summary: {stock_name} is experiencing challenges in its manufacturing operations due to ongoing semiconductor shortages. The company has reported potential delays in product shipments.

2. [Regulatory Update] {stock_name} Under Scrutiny by Regulators for Data Privacy Practices
   Summary: Regulatory authorities are investigating {stock_name}'s data collection and privacy practices, which could result in potential fines or required changes to business operations.

3. [Market Analysis] Competitive Pressure Intensifies for {stock_name} as New Market Entrants Gain Share
   Summary: Industry analysis indicates that {stock_name} is facing increased competition from newer, agile competitors who are gaining market share in key segments.

4. [Economic Outlook] Currency Volatility Poses Earnings Risk for {stock_name}
   Summary: Financial analysts note that {stock_name}'s significant international operations make it particularly vulnerable to currency fluctuations in the current economic environment.

5. [Investor Newsletter] Activist Investor Builds Stake in {stock_name}, Pressuring for Strategic Changes
   Summary: A prominent activist investment firm has accumulated a 4.8% stake in {stock_name} and is pushing for changes to capital allocation policies and board composition.
"""

async def main():
    try:
        print("\nInitializing connections...")
        # Initialize Supabase client
        supabase_url = os.getenv("SUPABASE_URL")
        supabase_key = os.getenv("SUPABASE_SERVICE_KEY")
        
        if not supabase_url or not supabase_key:
            print("Error: SUPABASE_URL and SUPABASE_SERVICE_KEY environment variables must be set")
            return
        
        supabase = create_client(supabase_url, supabase_key)
        
        # Initialize OpenAI client
        openai_client = AsyncOpenAI(api_key=os.getenv("OPENAI_API_KEY"))
        
        # Verify Supabase setup
        if not verify_supabase_setup(supabase):
            print("Error: Supabase setup verification failed")
            return
        
        deps = RisksAndShareholdingDeps(
            supabase=supabase,
            openai_client=openai_client
        )

        # Simple string variable to store the latest analysis
        risks_shareholding_result = ""

        while True:
            user_query = input("\nEnter stock name (or 'exit' to quit): ").strip()
            if user_query.lower() == 'exit':
                break

            print(f"\nAnalyzing risks and shareholding for {user_query}... Please wait...")
            try:
                # Run the agent
                agent_response = await risks_and_shareholding_expert.run(
                    f"Analyze the shareholding pattern and key risks for {user_query}. Provide a comprehensive risk and shareholding report.", 
                    deps=deps
                )
                
                print("\nRisks and Shareholding Analysis:")
                print("="*80)
                
                # Store and display the analysis
                if hasattr(agent_response, 'data'):
                    risks_shareholding_result = agent_response.data
                else:
                    risks_shareholding_result = str(agent_response)
                
                print(risks_shareholding_result)
                print("="*80)
                
                print("\nRisks and shareholding analysis has been stored in the variable 'risks_shareholding_result'")
                
                # Ask if the user wants to save the result to a file
                save_to_file = input("\nDo you want to save the analysis to a file? (yes/no): ").strip().lower()
                if save_to_file.startswith('y'):
                    filename = f"{user_query}_risks_shareholding_analysis.txt"
                    with open(filename, "w") as f:
                        f.write(risks_shareholding_result)
                    print(f"Analysis saved to {filename}")
                
            except Exception as e:
                print(f"\nError analyzing risks and shareholding: {str(e)}")
                print("\nDEBUGGING INFORMATION:")
                print("-"*40)
                print("1. Check your Supabase and OpenAI API credentials")
                print("2. Ensure your database has appropriate documents")
                print("3. Verify that the stock name is valid")

    except Exception as e:
        print(f"\nSetup error: {e}")
        print("\nPlease ensure you have set the SUPABASE_URL, SUPABASE_KEY, and OPENAI_API_KEY environment variables")

if __name__ == "__main__":
    asyncio.run(main()) 