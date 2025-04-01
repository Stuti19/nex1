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
    current_datetime = datetime.now().strftime("%B %d, %Y %H:%M")
    
    # Clean up each section's markdown
    clean_executive_summary = clean_markdown_for_html(executive_summary)
    clean_company_overview = clean_markdown_for_html(company_overview)
    clean_financial_overview = clean_markdown_for_html(financial_overview)
    clean_industry_overview = clean_markdown_for_html(industry_overview)
    clean_valuation = clean_markdown_for_html(valuation)
    clean_risks_and_shareholding = clean_markdown_for_html(risks_and_shareholding)
    
    html_content = f"""<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Investment Analysis: {stock_name}</title>
    <style>
        /* Modern minimalist styles with reduced spacing */
        :root {{
            --primary-color: #2d3748;
            --background-color: #ffffff;
            --text-color: #1a202c;
            --border-color: #e2e8f0;
            --accent-color: #4299e1;
            --section-spacing: 2rem;  /* Reduced from 4rem */
        }}

        * {{
            margin: 0;
            padding: 0;
            box-sizing: border-box;
        }}
        
        body {{
            font-family: 'Inter', -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif;
            line-height: 1.5;  /* Reduced from 1.7 */
            color: var(--text-color);
            background-color: var(--background-color);
            max-width: 1200px;
            margin: 0 auto;
            padding: 0 1rem;  /* Reduced from 2rem */
        }}

        /* Header styles */
        .report-header {{
            padding: 1.5rem 0;  /* Reduced from 3rem */
            margin-bottom: 1.5rem;  /* Reduced from var(--section-spacing) */
            border-bottom: 1px solid var(--border-color);
        }}

        .report-header h1 {{
            font-size: 2rem;  /* Reduced from 2.5rem */
            font-weight: 700;
            color: var(--primary-color);
            margin-bottom: 0.5rem;  /* Reduced from 1rem */
        }}

        .date-info {{
            color: #64748b;
            font-size: 0.9rem;
        }}

        /* Navigation styles */
        .report-nav {{
            position: sticky;
            top: 0;
            background-color: rgba(255, 255, 255, 0.95);
            padding: 0.5rem 0;  /* Reduced from 1rem */
            margin-bottom: 1rem;  /* Reduced from 2rem */
            border-bottom: 1px solid var(--border-color);
            z-index: 100;
            backdrop-filter: blur(5px);
        }}

        .nav-list {{
            list-style: none;
            display: flex;
            gap: 1rem;  /* Reduced from 2rem */
            overflow-x: auto;
            padding-bottom: 0.25rem;  /* Reduced from 0.5rem */
        }}

        .nav-item {{
            cursor: pointer;
            color: #64748b;
            font-weight: 500;
            white-space: nowrap;
            transition: color 0.2s ease;
            font-size: 0.9rem;  /* Added to reduce text size */
        }}

        .nav-item:hover {{
            color: var(--accent-color);
        }}

        .nav-item.active {{
            color: var(--primary-color);
        }}

        /* Section styles */
        .section {{
            margin-bottom: var(--section-spacing);
            scroll-margin-top: 3rem;  /* Reduced from 5rem */
        }}

        .section h2 {{
            font-size: 1.5rem;  /* Reduced from 2rem */
            color: var(--primary-color);
            margin-bottom: 1rem;  /* Reduced from 2rem */
            font-weight: 700;
        }}

        .section h3 {{
            font-size: 1.25rem;  /* Reduced from 1.5rem */
            color: var(--primary-color);
            margin: 1rem 0 0.5rem;  /* Reduced from 2rem 0 1rem */
        }}

        .section h4 {{
            font-size: 1.1rem;  /* Reduced from 1.25rem */
            color: var(--primary-color);
            margin: 1rem 0 0.5rem;  /* Reduced from 1.5rem 0 1rem */
        }}

        /* Content styles */
        p {{
            margin-bottom: 1rem;  /* Reduced from 1.5rem */
            color: #4a5568;
        }}

        ul, ol {{
            margin: 0.75rem 0;  /* Reduced from 1.5rem */
            padding-left: 1rem;  /* Reduced from 1.5rem */
        }}

        li {{
            margin-bottom: 0.5rem;  /* Reduced from 0.75rem */
            color: #4a5568;
        }}

        strong {{
            color: var(--primary-color);
            font-weight: 600;
        }}

        /* Table styles */
        table {{
            width: 100%;
            border-collapse: collapse;
            margin: 1rem 0;  /* Reduced from 2rem */
            font-size: 0.9rem;
        }}

        th, td {{
            padding: 0.5rem;  /* Reduced from 1rem */
            text-align: left;
            border-bottom: 1px solid var(--border-color);
        }}

        th {{
            font-weight: 600;
            color: var(--primary-color);
            background-color: #f8fafc;
        }}

        /* Responsive design */
        @media (max-width: 768px) {{
            body {{
                padding: 0 0.5rem;  /* Reduced from 1rem */
            }}

            .report-header {{
                padding: 1rem 0;  /* Reduced from 2rem */
            }}

            .report-header h1 {{
                font-size: 1.5rem;  /* Reduced from 2rem */
            }}

            .section h2 {{
                font-size: 1.25rem;  /* Reduced from 1.75rem */
            }}

            .nav-list {{
                gap: 0.5rem;  /* Reduced from 1rem */
            }}
        }}

        /* Print styles */
        @media print {{
            .report-nav {{
                display: none;
            }}

            body {{
                padding: 1rem;  /* Reduced from 2rem */
            }}

            .section {{
                page-break-inside: avoid;
            }}
        }}
    </style>
</head>
<body>
    <header class="report-header">
        <h1>Investment Analysis: {stock_name}</h1>
        <div class="date-info">Generated on {current_datetime}</div>
    </header>

    <nav class="report-nav">
        <ul class="nav-list">
            <li class="nav-item active" onclick="scrollToSection('executive-summary')">Executive Summary</li>
            <li class="nav-item" onclick="scrollToSection('company-overview')">Company Overview</li>
            <li class="nav-item" onclick="scrollToSection('financial-overview')">Financial Overview</li>
            <li class="nav-item" onclick="scrollToSection('industry-overview')">Industry Overview</li>
            <li class="nav-item" onclick="scrollToSection('valuation')">Valuation</li>
            <li class="nav-item" onclick="scrollToSection('risks-shareholding')">Risks & Shareholding</li>
        </ul>
    </nav>

    <main>
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
    </main>

    <script>
        function scrollToSection(sectionId) {{
            const section = document.getElementById(sectionId);
            if (section) {{
                section.scrollIntoView({{ behavior: 'smooth' }});
                
                // Update active nav item
                document.querySelectorAll('.nav-item').forEach(item => {{
                    item.classList.remove('active');
                }});
                
                const clickedItem = Array.from(document.querySelectorAll('.nav-item')).find(
                    item => item.getAttribute('onclick').includes(sectionId)
                );
                
                if (clickedItem) {{
                    clickedItem.classList.add('active');
                }}
            }}
        }}

        // Update active nav item on scroll
        const observerOptions = {{
            root: null,
            rootMargin: '-20% 0px -80% 0px',
            threshold: 0
        }};

        const observer = new IntersectionObserver(entries => {{
            entries.forEach(entry => {{
                if (entry.isIntersecting) {{
                    const sectionId = entry.target.id;
                    document.querySelectorAll('.nav-item').forEach(item => {{
                        item.classList.remove('active');
                        if (item.getAttribute('onclick').includes(sectionId)) {{
                            item.classList.add('active');
                        }}
                    }});
                }}
            }});
        }}, observerOptions);

        document.querySelectorAll('.section').forEach(section => {{
            observer.observe(section);
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