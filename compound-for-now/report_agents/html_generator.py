from __future__ import annotations as _annotations

import os
import re
import html
import asyncio
from datetime import datetime

def clean_markdown_for_html(markdown_text: str) -> str:
    """
    Clean and prepare markdown text for conversion to HTML.
    Handles basic markdown formatting.
    """
    if not markdown_text:
        return ""
    
    # Escape HTML
    text = html.escape(markdown_text)
    
    # Handle headers
    text = re.sub(r'^# (.*?)$', r'<h1>\1</h1>', text, flags=re.MULTILINE)
    text = re.sub(r'^## (.*?)$', r'<h2>\1</h2>', text, flags=re.MULTILINE)
    text = re.sub(r'^### (.*?)$', r'<h3>\1</h3>', text, flags=re.MULTILINE)
    text = re.sub(r'^#### (.*?)$', r'<h4>\1</h4>', text, flags=re.MULTILINE)
    text = re.sub(r'^##### (.*?)$', r'<h5>\1</h5>', text, flags=re.MULTILINE)
    text = re.sub(r'^###### (.*?)$', r'<h6>\1</h6>', text, flags=re.MULTILINE)
    
    # Handle bold and italic
    text = re.sub(r'\*\*(.*?)\*\*', r'<strong>\1</strong>', text)
    text = re.sub(r'\*(.*?)\*', r'<em>\1</em>', text)
    
    # Handle lists
    text = re.sub(r'^- (.*?)$', r'<li>\1</li>', text, flags=re.MULTILINE)
    text = re.sub(r'(<li>.*?</li>(\n|$))+', r'<ul>\g<0></ul>', text, flags=re.DOTALL)
    
    # Handle code blocks
    text = re.sub(r'```(.*?)```', r'<pre><code>\1</code></pre>', text, flags=re.DOTALL)
    
    # Handle line breaks
    text = text.replace('\n\n', '<br><br>')
    
    return text

def create_html_report(
    stock_name: str,
    executive_summary: str = "",
    company_overview: str = "",
    financial_overview: str = "",
    industry_overview: str = "",
    valuation: str = "",
    risks_and_shareholding: str = "",
    output_path: str = None
) -> str:
    """
    Generate a complete HTML report based on the outputs from different agents.
    
    Args:
        stock_name: Name of the stock being analyzed
        executive_summary: Output from the executive summary agent
        company_overview: Output from the company overview agent
        financial_overview: Output from the financial overview agent
        industry_overview: Output from the industry overview agent
        valuation: Output from the valuation agent
        risks_and_shareholding: Output from the risks and shareholding agent
        output_path: Path to save the HTML file (optional)
        
    Returns:
        HTML string of the complete report
    """
    # Get current date/time
    current_datetime = datetime.now().strftime("%B %d, %Y %H:%M")
    
    # Clean up each section's markdown
    clean_executive_summary = clean_markdown_for_html(executive_summary)
    clean_company_overview = clean_markdown_for_html(company_overview)
    clean_financial_overview = clean_markdown_for_html(financial_overview)
    clean_industry_overview = clean_markdown_for_html(industry_overview)
    clean_valuation = clean_markdown_for_html(valuation)
    clean_risks_and_shareholding = clean_markdown_for_html(risks_and_shareholding)
    
    # Create HTML
    html_content = f"""<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Investment Analysis: {stock_name}</title>
    <style>
        /* Reset and base styles */
        * {{
            margin: 0;
            padding: 0;
            box-sizing: border-box;
        }}
        
        body {{
            font-family: 'Segoe UI', Roboto, Oxygen, Ubuntu, Cantarell, 'Open Sans', 'Helvetica Neue', sans-serif;
            line-height: 1.6;
            color: #333;
            background-color: #f8f9fa;
            padding: 0;
            margin: 0;
        }}
        
        /* Top bar styling */
        .topbar {{
            background-color: #1a365d;
            color: white;
            padding: 1rem 2rem;
            position: sticky;
            top: 0;
            z-index: 1000;
            box-shadow: 0 2px 10px rgba(0,0,0,0.1);
            display: flex;
            justify-content: space-between;
            align-items: center;
        }}
        
        .topbar h1 {{
            font-size: 1.5rem;
            font-weight: 600;
            margin: 0;
        }}
        
        .topbar-right {{
            display: flex;
            align-items: center;
        }}
        
        .date-info {{
            font-size: 0.9rem;
            margin-right: 1rem;
        }}
        
        /* Container layout */
        .container {{
            display: flex;
            max-width: 1600px;
            margin: 0 auto;
            padding: 0;
            min-height: calc(100vh - 4rem);
        }}
        
        /* Sidebar styling */
        .sidebar {{
            width: 280px;
            background-color: #f0f4f8;
            padding: 2rem 1rem;
            border-right: 1px solid #e1e4e8;
            position: sticky;
            top: 4rem;
            height: calc(100vh - 4rem);
            overflow-y: auto;
        }}
        
        .sidebar-nav {{
            list-style: none;
        }}
        
        .sidebar-nav-item {{
            padding: 0.8rem 1rem;
            border-radius: 6px;
            margin-bottom: 0.5rem;
            transition: all 0.2s ease;
            cursor: pointer;
            font-weight: 500;
        }}
        
        .sidebar-nav-item:hover {{
            background-color: #e2e8f0;
        }}
        
        .sidebar-nav-item.active {{
            background-color: #2a4365;
            color: white;
        }}
        
        /* Main content styling */
        .main-content {{
            flex: 1;
            padding: 2rem;
            background-color: white;
        }}
        
        .section {{
            margin-bottom: 3rem;
            border-bottom: 1px solid #e1e4e8;
            padding-bottom: 2rem;
        }}
        
        .section:last-child {{
            border-bottom: none;
        }}
        
        h2 {{
            color: #2d3748;
            font-size: 1.8rem;
            margin-bottom: 1.5rem;
            padding-bottom: 0.5rem;
            border-bottom: 2px solid #edf2f7;
        }}
        
        h3 {{
            color: #4a5568;
            font-size: 1.4rem;
            margin-top: 1.5rem;
            margin-bottom: 1rem;
        }}
        
        h4 {{
            color: #4a5568;
            font-size: 1.2rem;
            margin-top: 1.2rem;
            margin-bottom: 0.8rem;
        }}
        
        p {{
            margin-bottom: 1rem;
        }}
        
        ul, ol {{
            margin-bottom: 1rem;
            padding-left: 1.5rem;
        }}
        
        li {{
            margin-bottom: 0.5rem;
        }}
        
        strong {{
            font-weight: 600;
            color: #2d3748;
        }}
        
        /* Table styling */
        table {{
            width: 100%;
            border-collapse: collapse;
            margin-bottom: 1.5rem;
        }}
        
        th, td {{
            padding: 0.75rem;
            text-align: left;
            border: 1px solid #e2e8f0;
        }}
        
        th {{
            background-color: #f0f4f8;
            font-weight: 600;
        }}
        
        /* Responsive adjustments */
        @media (max-width: 1024px) {{
            .container {{
                flex-direction: column;
            }}
            
            .sidebar {{
                width: 100%;
                height: auto;
                position: static;
                padding: 1rem;
                border-right: none;
                border-bottom: 1px solid #e1e4e8;
            }}
            
            .sidebar-nav {{
                display: flex;
                flex-wrap: wrap;
            }}
            
            .sidebar-nav-item {{
                margin-right: 0.5rem;
            }}
        }}
        
        /* Print styles */
        @media print {{
            .topbar, .sidebar {{
                display: none;
            }}
            
            .container {{
                display: block;
            }}
            
            .main-content {{
                padding: 0;
            }}
            
            body {{
                background-color: white;
            }}
        }}
    </style>
</head>
<body>
    <div class="topbar">
        <h1>Investment Analysis Report: {stock_name}</h1>
        <div class="topbar-right">
            <div class="date-info">Generated on: {current_datetime}</div>
        </div>
    </div>
    
    <div class="container">
        <div class="sidebar">
            <ul class="sidebar-nav">
                <li class="sidebar-nav-item active" onclick="scrollToSection('executive-summary')">Executive Summary</li>
                <li class="sidebar-nav-item" onclick="scrollToSection('company-overview')">Company Overview</li>
                <li class="sidebar-nav-item" onclick="scrollToSection('financial-overview')">Financial Overview</li>
                <li class="sidebar-nav-item" onclick="scrollToSection('industry-overview')">Industry Overview</li>
                <li class="sidebar-nav-item" onclick="scrollToSection('valuation')">Valuation</li>
                <li class="sidebar-nav-item" onclick="scrollToSection('risks-shareholding')">Risks & Shareholding</li>
            </ul>
        </div>
        
        <div class="main-content">
            <section id="executive-summary" class="section">
                <h2>Executive Summary</h2>
                {clean_executive_summary or "<p>Executive summary not available.</p>"}
            </section>
            
            <section id="company-overview" class="section">
                <h2>Company Overview</h2>
                {clean_company_overview or "<p>Company overview not available.</p>"}
            </section>
            
            <section id="financial-overview" class="section">
                <h2>Financial Overview</h2>
                {clean_financial_overview or "<p>Financial overview not available.</p>"}
            </section>
            
            <section id="industry-overview" class="section">
                <h2>Industry Overview</h2>
                {clean_industry_overview or "<p>Industry overview not available.</p>"}
            </section>
            
            <section id="valuation" class="section">
                <h2>Valuation</h2>
                {clean_valuation or "<p>Valuation not available.</p>"}
            </section>
            
            <section id="risks-shareholding" class="section">
                <h2>Risks & Shareholding</h2>
                {clean_risks_and_shareholding or "<p>Risks and shareholding analysis not available.</p>"}
            </section>
        </div>
    </div>
    
    <script>
        // JavaScript for navigation functionality
        function scrollToSection(sectionId) {{
            const section = document.getElementById(sectionId);
            if (section) {{
                section.scrollIntoView({{ behavior: 'smooth' }});
                
                // Update active status in sidebar
                const navItems = document.querySelectorAll('.sidebar-nav-item');
                navItems.forEach(item => {{
                    item.classList.remove('active');
                }});
                
                const clickedItem = Array.from(navItems).find(
                    item => item.getAttribute('onclick').includes(sectionId)
                );
                
                if (clickedItem) {{
                    clickedItem.classList.add('active');
                }}
            }}
        }}
        
        // Highlight nav items on scroll
        window.addEventListener('scroll', function() {{
            const sections = document.querySelectorAll('.section');
            const navItems = document.querySelectorAll('.sidebar-nav-item');
            
            let currentSection = '';
            
            sections.forEach(section => {{
                const sectionTop = section.offsetTop;
                const sectionHeight = section.clientHeight;
                if (pageYOffset >= (sectionTop - 100)) {{
                    currentSection = section.getAttribute('id');
                }}
            }});
            
            navItems.forEach(item => {{
                item.classList.remove('active');
                const onclick = item.getAttribute('onclick');
                if (onclick && onclick.includes(currentSection)) {{
                    item.classList.add('active');
                }}
            }});
        }});
    </script>
</body>
</html>
"""
    
    # Save the HTML to a file if output_path is provided
    if output_path:
        with open(output_path, 'w', encoding='utf-8') as f:
            f.write(html_content)
        print(f"HTML report saved to {output_path}")
    
    return html_content

async def main():
    """Interactive interface to generate HTML reports."""
    print("\n=== HTML Report Generator ===\n")
    
    stock_name = input("Enter stock name: ").strip()
    
    print("\nFor each section below, you can either:")
    print("1. Enter the content directly")
    print("2. Enter a file path to load content from a file")
    print("3. Leave empty to skip that section\n")
    
    sections = {
        "Executive Summary": "",
        "Company Overview": "",
        "Financial Overview": "",
        "Industry Overview": "",
        "Valuation": "",
        "Risks & Shareholding": ""
    }
    
    for section_name in sections:
        input_type = input(f"\n{section_name} - Enter 'direct', 'file', or press Enter to skip: ").strip().lower()
        
        if input_type == 'direct':
            print(f"Enter {section_name} content (type 'END' on a new line when finished):")
            lines = []
            while True:
                line = input()
                if line == 'END':
                    break
                lines.append(line)
            sections[section_name] = '\n'.join(lines)
        
        elif input_type == 'file':
            file_path = input("Enter file path: ").strip()
            try:
                with open(file_path, 'r', encoding='utf-8') as f:
                    sections[section_name] = f.read()
                print(f"Successfully loaded content from {file_path}")
            except Exception as e:
                print(f"Error loading file: {e}")
    
    # Generate output file name
    default_output = f"{stock_name}_investment_report.html"
    output_path = input(f"\nEnter output file path (default: {default_output}): ").strip()
    
    if not output_path:
        output_path = default_output
    
    # Generate the HTML report
    html_content = create_html_report(
        stock_name=stock_name,
        executive_summary=sections["Executive Summary"],
        company_overview=sections["Company Overview"],
        financial_overview=sections["Financial Overview"],
        industry_overview=sections["Industry Overview"],
        valuation=sections["Valuation"],
        risks_and_shareholding=sections["Risks & Shareholding"],
        output_path=output_path
    )
    
    print(f"\nHTML report successfully generated and saved to {output_path}")
    
    # Ask if user wants to open the file
    open_file = input("\nDo you want to open the HTML file now? (y/n): ").strip().lower()
    if open_file == 'y':
        try:
            if os.name == 'nt':  # Windows
                os.system(f'start {output_path}')
            elif os.name == 'posix':  # macOS and Linux
                if os.uname().sysname == 'Darwin':  # macOS
                    os.system(f'open {output_path}')
                else:  # Linux
                    os.system(f'xdg-open {output_path}')
            print(f"Opened {output_path}")
        except Exception as e:
            print(f"Could not open file: {e}")

if __name__ == "__main__":
    asyncio.run(main()) 