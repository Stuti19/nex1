from __future__ import annotations as _annotations

from dataclasses import dataclass
import asyncio
import os
from bs4 import BeautifulSoup
import tiktoken
from typing import Optional

from pydantic_ai import Agent, ModelRetry, RunContext
from pydantic_ai.models.openai import OpenAIModel
from openai import AsyncOpenAI

# Initialize OpenAI model
llm = os.getenv('LLM_MODEL', 'gpt-4o-mini')
model = OpenAIModel(llm)

@dataclass
class ReportDeps:
    openai_client: AsyncOpenAI
    content: str  # Store the report content in deps

system_prompt = """
You have to present the given report in a reading friendly way.
Do not remove any information from the report.
You just have make a better structured report, easpeically structure the executive summary part better (as it is creating a lot of new headings and repeating of the headings).
Format the report better by customizing the css. Presenting the data in forms of table and charts.
Each financial report shares a story, so make the report readinf a jouney.
Use professional financial report writing style.
The final report should look like a modern professional financial report that any investor would love to read.
Also, After reading these reports the readers invest billions of dollars in company they will stop trusting you if you genearte a bad report, and you will lose all of the
"""

report_expert = Agent(
    model,
    system_prompt=system_prompt,
    deps_type=ReportDeps
)

def count_tokens(text: str, model_name: str = "gpt-4o-mini") -> int:
    """Count the number of tokens in a text string."""
    try:
        encoding = tiktoken.encoding_for_model(model_name)
        return len(encoding.encode(text))
    except Exception:
        encoding = tiktoken.get_encoding("cl100k_base")
        return len(encoding.encode(text))

def extract_text_from_html(html_content: str) -> str:
    """Extract text content from HTML while preserving structure."""
    soup = BeautifulSoup(html_content, 'html.parser')
    
    # Extract text while preserving some structure
    text = ""
    
    # Process main content sections
    for section in soup.find_all('section', class_='section'):
        # Get section title
        title = section.find('h2')
        if title:
            text += f"\n\n### {title.text.upper()}\n"
        
        # Process paragraphs and lists
        for elem in section.find_all(['p', 'ul', 'li', 'h3', 'h4']):
            if elem.name == 'h3':
                text += f"\n## {elem.text}\n"
            elif elem.name == 'h4':
                text += f"\n# {elem.text}\n"
            elif elem.name == 'ul':
                text += "\n"
            elif elem.name == 'li':
                text += f"- {elem.text}\n"
            else:
                text += f"\n{elem.text}\n"
    
    return text

@report_expert.tool
async def get_report_content(ctx: RunContext[ReportDeps]) -> str:
    """Get the report content from deps."""
    return ctx.deps.content

async def process_report(html_file_path: str) -> Optional[str]:
    """Process an HTML report file and generate a refined report."""
    try:
        # Read HTML file
        # Initialize OpenAI client
        openai_client = AsyncOpenAI(api_key=os.getenv("OPENAI_API_KEY"))
        
        with open(html_file_path, 'r', encoding='utf-8') as f:
            html_content = f.read()
        
        # Create deps with the content
        deps = ReportDeps(
            openai_client=openai_client,
            content=html_content
        )
        
        # Process the report content
        response = await report_expert.run(
            "Please improve this financial report's structure and presentation while maintaining all information.",
            deps=deps
        )
        
        # Generate output filename
        base_name = os.path.basename(html_file_path)
        output_name = f"improved_{base_name}"
        output_path = os.path.join(os.path.dirname(html_file_path), output_name)
        
        # Save the improved report
        with open(output_path, 'w', encoding='utf-8') as f:
            f.write(response.data if hasattr(response, 'data') else str(response))
        
        print(f"\nImproved report saved to: {output_path}")
        return output_path
        
    except Exception as e:
        print(f"Error processing report: {str(e)}")
        return None

async def main():
    """Main entry point for the report processing system."""
    print("\n===== Financial Report Enhancement System =====\n")
    print("\n===== Report Improvement System =====\n")
    try:
        while True:
            file_path = input("\nEnter path to HTML report (or 'exit' to quit): ").strip()
            # Get input file path
            if file_path.lower() == 'exit':
                break
            
            if not os.path.exists(file_path):
                print(f"Error: File not found at {file_path}")
                continue
            
            print("\nProcessing report... Please wait...")
            output_path = await process_report(file_path)
            
            if output_path:
                print("\nWould you like to view the improved report? (y/n): ")
                if input().lower() == 'y':
                    with open(output_path, 'r', encoding='utf-8') as f:
                        print("\n" + "="*80)
                        print(f.read())
                        print("="*80)
    
    except Exception as e:
        print(f"\nSetup error: {e}")
        print("\nPlease ensure you have set the environment variable:")
        print("\nPlease ensure you have set these environment variables:")
        print("- OPENAI_API_KEY")
        print("- LLM_MODEL (optional, defaults to gpt-4o-mini)")
if __name__ == "__main__":
    asyncio.run(main())
