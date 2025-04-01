from __future__ import annotations as _annotations

import os
import sys
import asyncio
from dotenv import load_dotenv
from typing import Dict, Any, Optional
import importlib.util
import argparse
from pathlib import Path
from datetime import datetime
import json
import shutil

from openai import AsyncOpenAI
from supabase import create_client, Client
from report_agents.executive_summary import executive_summary_expert, ExecutiveSummaryDeps







# Ensure all necessary paths are in sys.path
base_dir = os.path.dirname(os.path.abspath(__file__))
if base_dir not in sys.path:
    sys.path.insert(0, base_dir)
    
parent_dir = os.path.dirname(base_dir)
if parent_dir not in sys.path:
    sys.path.insert(0, parent_dir)

# Import HTML generator directly since it's in the same directory
from html_generator import create_html_report

# Import all report agents
from report_agents.company_overview import company_expert, CompanyOverviewDeps
from report_agents.financial_overview import financial_expert, FinancialOverviewDeps
from report_agents.industry_overview import industry_expert, IndustryOverviewDeps
from report_agents.valuation import valuation_expert, ValuationDeps  # Changed from ValuationAgentDeps
from report_agents.executive_summary import executive_summary_expert, ExecutiveSummaryDeps
from report_agents.risks_and_shareholding import risks_and_shareholding_expert, RisksAndShareholdingDeps

# Load environment variables
load_dotenv()

# Configure necessary environment variables
REQUIRED_ENV_VARS = [
    "OPENAI_API_KEY",
    "SUPABASE_URL",
    "SUPABASE_SERVICE_KEY"
]

async def initialize_connections() -> tuple[Client, AsyncOpenAI]:
    """Initialize Supabase and OpenAI connections."""
    supabase = create_client(
        os.getenv("SUPABASE_URL"),
        os.getenv("SUPABASE_SERVICE_KEY")
    )
    openai_client = AsyncOpenAI(api_key=os.getenv("OPENAI_API_KEY"))
    return supabase, openai_client

async def run_agent_with_timeout(agent, query: str, deps, timeout: int = 60) -> str:
    """Run an agent with a timeout."""
    try:
        async with asyncio.timeout(timeout):
            response = await agent.run(query, deps=deps)
            return response.data if hasattr(response, 'data') else str(response)
    except asyncio.TimeoutError:
        return "Analysis timed out after 60 seconds"
    except Exception as e:
        return f"Error in analysis: {str(e)}"

def check_env_vars() -> bool:
    """Check if all required environment variables are set."""
    missing_vars = [var for var in REQUIRED_ENV_VARS if not os.getenv(var)]
    if missing_vars:
        print(f"Error: Missing required environment variables: {', '.join(missing_vars)}")
        print("Please set these variables in a .env file or in your environment.")
        return False
    return True

def load_agent_module(module_path: str, module_name: str):
    """Dynamically load a Python module."""
    try:
        # Check if the file exists
        if not os.path.exists(module_path):
            print(f"Warning: Module {module_name} not found at {module_path}")
            return None
            
        spec = importlib.util.spec_from_file_location(module_name, module_path)
        if spec is None:
            raise ImportError(f"Could not find module at {module_path}")
        
        module = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(module)
        return module
    except Exception as e:
        print(f"Error loading module {module_name} from {module_path}: {e}")
        return None

async def run_agent(agent_path: str, agent_name: str, stock_name: str) -> Optional[str]:
    """Run a specific agent and return its output."""
    print(f"\nRunning {agent_name} for {stock_name}...")
    
    # Construct absolute path
    base_dir = os.path.dirname(os.path.abspath(__file__))
    full_path = os.path.join(base_dir, agent_path)
    
    # Load the agent module
    module = load_agent_module(full_path, agent_name)
    if not module:
        print(f"Simulating output for {agent_name} since module could not be loaded.")
        return f"# {agent_name.title().replace('_', ' ')} Analysis for {stock_name}\n\nThis is a simulated analysis as the module was not found."
    
    # Check if the module has a main function
    if not hasattr(module, 'main'):
        print(f"Error: Module {agent_name} does not have a main function")
        return f"# {agent_name.title().replace('_', ' ')} Analysis for {stock_name}\n\nThis is a simulated analysis as the module does not have a main function."
    
    try:
        # Create a pipe to capture stdout
        original_stdout = sys.stdout
        sys.stdout = open('temp_output.txt', 'w', encoding='utf-8')
        
        # Call the module's main function with the stock name as input
        # Note: This assumes the main function accepts input via sys.stdin
        original_stdin = sys.stdin
        
        # Prepare a custom stdin that will provide the stock name
        class CustomStdin:
            def __init__(self, values):
                self.values = values
                self.index = 0
            
            def readline(self):
                if self.index < len(self.values):
                    value = self.values[self.index]
                    self.index += 1
                    return value + '\n'
                return 'exit\n'  # End with exit command
        
        # Set custom stdin that will provide the stock name and then exit
        sys.stdin = CustomStdin([stock_name])
        
        # Run the agent's main function
        await module.main()
        
        # Restore stdout and stdin
        sys.stdout.close()
        sys.stdout = original_stdout
        sys.stdin = original_stdin
        
        # Read the captured output
        with open('temp_output.txt', 'r', encoding='utf-8') as f:
            output = f.read()
        
        # Clean up
        os.remove('temp_output.txt')
        
        # Extract the relevant portion of the output (between the "=" lines)
        start_marker = "=" * 80
        end_marker = "=" * 80
        
        start_idx = output.find(start_marker) + len(start_marker)
        if start_idx == -1 + len(start_marker):
            print(f"Warning: Could not find start marker in {agent_name} output")
            return output
        
        end_idx = output.find(end_marker, start_idx)
        if (end_idx == -1):
            end_idx = len(output)
        
        relevant_output = output[start_idx:end_idx].strip()
        print(f"Successfully ran {agent_name}")
        
        return relevant_output
    
    except Exception as e:
        print(f"Error running {agent_name}: {e}")
        # Restore stdout and stdin in case of error
        if sys.stdout != original_stdout:
            sys.stdout.close()
            sys.stdout = original_stdout
        if 'original_stdin' in locals():
            sys.stdin = original_stdin
        return f"# {agent_name.title().replace('_', ' ')} Analysis for {stock_name}\n\nError encountered during analysis: {str(e)}"

async def generate_sample_report_content(stock_name: str) -> Dict[str, str]:
    """Generate sample content for each section when agents are not available."""
    
    sample_content = {
        "executive_summary": f"""# Executive Summary for {stock_name}

## Company Snapshot
{stock_name} is a company operating in its market segment with unique products and services. The company has established a position in the market and continues to demonstrate financial stability.

## Investment Highlights
The company shows potential for growth through strategic initiatives and competitive advantages. It maintains a strong financial position with opportunities in its market segment.

## Key Risks
Market competition and economic factors may pose challenges. The company faces typical industry risks that investors should consider.

## Financial Overview
The company has demonstrated stable revenue trends and profit margins. Its balance sheet appears to be well-managed with adequate cash flow.

## Industry Context
The industry in which {stock_name} operates has specific market dynamics and trends. The company is positioned within this competitive landscape.

## Valuation Summary
Based on available information, {stock_name} presents an investment opportunity with potential for growth. Further analysis is needed for precise valuation.""",

        "company_overview": f"""# Company Overview for {stock_name}

## Company Background
{stock_name} was established as a player in its market segment. The company has developed a reputation for its products and services.

## Business Model
The company generates revenue through its core business activities, serving customers in its target market.

## Product and Service Portfolio
{stock_name} offers a range of products and services designed to meet customer needs in its industry.

## Competitive Advantages
The company has several advantages including brand recognition and operational efficiency.

## Market Position
Within its industry, {stock_name} holds a position that allows it to compete effectively.""",

        "financial_overview": f"""# Financial Overview for {stock_name}

## Financial Performance Overview
{stock_name} has demonstrated financial performance consistent with its industry position. Revenue and profit metrics indicate the company's financial health.

## Balance Sheet Analysis
The company maintains a balance sheet with assets and liabilities managed to support operations and growth.

## Cash Flow Analysis
Cash flow patterns indicate the company's ability to generate and utilize cash for operations and investments.

## Ratio Analysis
Key financial ratios fall within industry parameters, highlighting the company's operational efficiency.

## Quarterly Performance Trends
Recent quarters show the company's performance trajectory and seasonal patterns if applicable.""",

        "industry_overview": f"""# Industry Overview for {stock_name}

## Industry Overview
The industry in which {stock_name} operates has specific characteristics, size, and growth potential.

## Market Dynamics
Market forces shape competition and opportunity in this sector. Supply and demand factors influence pricing and profitability.

## Competitive Landscape
{stock_name} competes with several other companies in this market space. Each has relative strengths and market share.

## Industry Trends
Current trends include technological changes, regulatory developments, and shifting customer preferences.

## Growth Opportunities
The industry presents opportunities for growth through innovation, market expansion, and strategic initiatives.""",

        "valuation": f"""# Valuation Analysis for {stock_name}

## Valuation Methodology
Multiple valuation approaches would be appropriate for assessing {stock_name}'s fair value, including DCF and comparable company analysis.

## Discounted Cash Flow Analysis
A DCF analysis would consider the company's projected cash flows, growth rate, and appropriate discount rate.

## Relative Valuation
Compared to peers, {stock_name}'s valuation multiples would provide perspective on relative value.

## Fair Value Range
Based on preliminary analysis, {stock_name} would have a fair value range dependent on growth assumptions and market conditions.

## Investment Recommendation
A formal investment recommendation would require detailed analysis of financials, growth prospects, and industry position.""",

        "risks_and_shareholding": f"""# Risks and Shareholding Analysis for {stock_name}

## Shareholding Pattern Analysis
The ownership structure of {stock_name} includes institutional investors, promoters, and public shareholders in proportions typical for its industry.

## Key Shareholders
Major shareholders likely include founding members, institutional investors, and possibly strategic partners.

## Operational Risks
The company faces operational challenges typical in its industry including supply chain management and production efficiency.

## Financial Risks
Financial risks include those related to capital structure, liquidity, and currency exposure if applicable.

## Strategic Risks
Competitive pressures and market evolution pose strategic challenges that management must navigate."""
    }
    
    return sample_content

async def generate_complete_report(stock_name: str, agents_to_run: Dict[str, str], output_dir: str = None) -> Optional[str]:
    """Generate a complete report by running all specified agents or using sample content."""
    report_sections = {}
    
    # Check if any actual agent modules exist
    base_dir = os.path.dirname(os.path.abspath(__file__))
    any_modules_exist = any(os.path.exists(os.path.join(base_dir, path)) for path in agents_to_run.values())
    
    # If no modules exist, use sample content
    if not any_modules_exist:
        print("\nNo agent modules found. Using sample content for the report.")
        sample_content = await generate_sample_report_content(stock_name)
        report_sections = sample_content
    else:
        # Run each specified agent
        for agent_name, agent_path in agents_to_run.items():
            section_content = await run_agent(agent_path, agent_name, stock_name)
            report_sections[agent_name] = section_content or ""
    
    # Generate output path
    if not output_dir:
        output_dir = os.getcwd()
    
    output_file = f"{stock_name.replace(' ', '_')}_investment_report.html"
    output_path = os.path.join(output_dir, output_file)
    
    # Generate HTML report
    html_report = create_html_report(
        stock_name=stock_name,
        executive_summary=report_sections.get("executive_summary", ""),
        company_overview=report_sections.get("company_overview", ""),
        financial_overview=report_sections.get("financial_overview", ""),
        industry_overview=report_sections.get("industry_overview", ""),
        valuation=report_sections.get("valuation", ""),
        risks_and_shareholding=report_sections.get("risks_and_shareholding", ""),
        output_path=output_path
    )
    
    print(f"\nComplete investment report generated: {output_path}")

    public_path = os.path.join(os.path.dirname(__file__), "../public", output_file)
    shutil.copy(output_path, public_path)
    return output_path

def parse_arguments():
    """Parse command line arguments."""
    parser = argparse.ArgumentParser(description="Generate comprehensive investment reports for stocks")
    parser.add_argument("stock_name", nargs="?", help="Name of the stock to analyze")
    parser.add_argument("--output-dir", "-o", help="Directory to save the output report")
    parser.add_argument("--skip-agents", "-s", nargs="+", choices=[
        "company_overview", "financial_overview", "industry_overview", 
        "valuation", "executive_summary", "risks_and_shareholding"
    ], help="Skip specific agents")
    parser.add_argument("--use-sample", "-u", action="store_true", help="Use sample content instead of running agents")
    return parser.parse_args()

async def main(stock_name: str):
    """Main entry point for the report generation system."""
    print("\n===== Financial Analysis Report Generator =====\n")
    
    try:
        print("\nInitializing connections...")
        supabase, openai_client = await initialize_connections()
        
        print(f"\nAnalyzing {stock_name}...")
        print("Each analysis will run for up to 40 seconds.")
        
        # Initialize all dependencies
        company_deps = CompanyOverviewDeps(supabase=supabase, openai_client=openai_client)
        financial_deps = FinancialOverviewDeps(supabase=supabase, openai_client=openai_client)
        industry_deps = IndustryOverviewDeps(supabase=supabase, openai_client=openai_client)
        valuation_deps = ValuationDeps(supabase=supabase, openai_client=openai_client)
        executive_deps = ExecutiveSummaryDeps(supabase=supabase,openai_client=openai_client)
        risks_deps = RisksAndShareholdingDeps(supabase=supabase, openai_client=openai_client)
        
        # Run agents sequentially with timeouts
        print("\n1. Company Overview Analysis...")
        company_result = await run_agent_with_timeout(
            company_expert,
            f"Analyze the company information for {stock_name}",
            company_deps
        )
        
        print("\n2. Financial Overview Analysis...")
        financial_result = await run_agent_with_timeout(
            financial_expert,
            f"Analyze the financial data for {stock_name}",
            financial_deps
        )
        
        print("\n3. Industry Overview Analysis...")
        industry_result = await run_agent_with_timeout(
            industry_expert,
            f"Analyze the industry context for {stock_name}",
            industry_deps
        )
        
        print("\n4. Valuation Analysis...")
        valuation_result = await run_agent_with_timeout(
            valuation_expert,
            f"Perform valuation analysis for {stock_name}",
            valuation_deps
        )
        
        # Update executive_deps with results from other agents
        executive_deps.company_overview = company_result
        executive_deps.financial_overview = financial_result
        executive_deps.industry_overview = industry_result
        executive_deps.valuation = valuation_result
        
        print("\n5. Executive Summary Analysis...")
        executive_result = await run_agent_with_timeout(
            executive_summary_expert,
            f"Generate executive summary for {stock_name}",
            executive_deps
        )
        
        print("\n6. Risks and Shareholding Analysis...")
        risks_result = await run_agent_with_timeout(
            risks_and_shareholding_expert,
            f"Analyze risks and shareholding for {stock_name}",
            risks_deps
        )
        
        # Create output directory for reports
        output_dir = os.path.join(os.path.dirname(__file__), "../public/generated_reports")
        os.makedirs(output_dir, exist_ok=True)
        
        # Generate timestamp for unique filenames
        timestamp = datetime.now().strftime("%Y%m%d")
        
        # Save JSON report
        json_file = os.path.join(output_dir, f"{stock_name}_{timestamp}_analysis.json")
        with open(json_file, 'w', encoding='utf-8') as f:
            json.dump({
                "stock_name": stock_name,
                "timestamp": timestamp,
                "executive_summary": executive_result,
                "company_overview": company_result,
                "financial_overview": financial_result,
                "industry_overview": industry_result,
                "valuation": valuation_result,
                "risks_and_shareholding": risks_result
            }, f, indent=2, ensure_ascii=False)
        
        # Save HTML report
        output_dir = os.path.join(os.path.dirname(__file__), "../public/generated_reports")
        os.makedirs(output_dir, exist_ok=True)

        date_str = datetime.now().strftime("%Y%m%d")
        html_file = os.path.join(output_dir, f"{stock_name}_{date_str}_report.html")
        create_html_report(
            stock_name=stock_name,
            executive_summary=executive_result,
            company_overview=company_result,
            financial_overview=financial_result,
            industry_overview=industry_result,
            valuation=valuation_result,
            risks_and_shareholding=risks_result,
            output_path=html_file
        )
        
        print(f"\nReports generated successfully:")
        print(f"1. JSON Report: {json_file}")
        print(f"2. HTML Report: {html_file}")
    
    except Exception as e:
        print(f"\nSetup error: {e}")
        print("\nPlease ensure you have set these environment variables:")
        print("- SUPABASE_URL")
        print("- SUPABASE_SERVICE_KEY")
        print("- OPENAI_API_KEY")
    
    print("\nReport generation complete. Thank you for using the Financial Analysis Report Generator.")

if __name__ == "__main__":
    args = parse_arguments()
    asyncio.run(main(args.stock_name))