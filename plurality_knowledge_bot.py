"""
Plurality Knowledge Bot

This script uses the Perplexity API to fetch the latest information about
organizations, researchers, papers, events, and jobs relevant to Plurality Institute.
It can be scheduled to run daily using cron, GitHub Actions, or any scheduler.

Usage:
  python plurality_knowledge_bot.py
"""
import requests
import json
import os
import time
import re
from datetime import datetime, timedelta
from dotenv import load_dotenv

load_dotenv()

API_KEY = os.environ.get("PERPLEXITY_API_KEY")
if not API_KEY:
    raise ValueError("Please set the PERPLEXITY_API_KEY environment variable")

PEOPLE_KEYWORDS = [
    "Alessandra Casella", "Allison Duettmann", "Allison Stanger", "Audrey Tang",
    "Aviv Ovadya", "Beth Noveck", "Bill Doherty", "Bruce Schneier", "CL Kao",
    "Charlotte Cavaillé", "Colin Megill", "Cory Doctorow", "Danielle Allen",
    "Daron Acemoglu", "David Bloomin", "Deepti Doshi", "Dimitrios Xefteris",
    "Divya Siddarth", "Edward Casternova", "Eli Pariser", "Eric A. Posner",
    "Eugene Leventhal", "Evan Miyazono", "Glen Weyl", "Helen Nissenbaum",
    "James Evans", "Jamie Joyce", "Jeffrey Fossett", "John Etchemendy",
    "Jon X. Eguia", "Joshua Tan", "Juan Benet", "Kevin Owocki", "Lisa Schirch",
    "Madeleine Daepp", "Mahnaz Roshanaei", "Manon Revel", "Margaret Levi",
    "Matthew Prewitt", "Mike Jordan", "Nathan Schneider", "Nicole Immorlica",
    "Percy Liang", "Primavera De Filippi", "Puja Ohlhaver", "Rob Reich",
    "Rose Bloomin", "Saffron Huang", "Shrey Jain", "Stefaan Verhulst",
    "Uma Viswanathan", "Uri Wilensky", "Victor Lange", "Vitalik Buterin",
    "Wes Chao", "Zoë Hitzig", "danah boyd"
]

# Define key people for "Our People" section (to be implemented later)
KEY_PEOPLE = [
    "Glen Weyl", "Divya Siddarth", "Audrey Tang", "Joshua Tan", 
    "Matt Prewitt", "E. Glen Weyl", "Puja Ohlhaver"
]

ORGANIZATION_KEYWORDS = [
    "Plurality Institute", "Berkman Klein Center for Internet & Society",
    "Harvard Democracy Renovation Lab", "MIT Media Lab",
    "Stanford Center for AI Governance and Policy", "Y Combinator Research",
    "OpenAI", "Anthropic", "Meta Government", "Civic Tech Field Guide",
    "New Public", "Public Interest Tech", "Tech for Good", "All Tech is Human",
    "RadicalX", "AI and Democracy Foundation", 
    "Microsoft Plural Technology Collaboratory", 
    "University of California, Berkeley CHAI", "Gitcoin",
    "Tech Policy Press"
]

CONCEPT_KEYWORDS = [
    "collective intelligence", "digital democracy", "collaborative governance",
    "distributed systems", "decentralized autonomous organizations", "plurality",
    "digital commons", "pluralism", "tech ethics", "tech policy", 
    "AI ethics", "AI governance", "AI policy", "AI regulation",
    "decentralized governance"
]

PLURALITY_CATEGORIES = {
    "research_papers": {
        "description": "Recent academic papers and publications",
        "keyword_groups": {
            "concepts": CONCEPT_KEYWORDS,
            "people": PEOPLE_KEYWORDS,
            "organizations": ORGANIZATION_KEYWORDS
        }
    },
    "industry_news": {
        "description": "Latest news and developments",
        "keyword_groups": {
            "concepts": CONCEPT_KEYWORDS,
            "people": PEOPLE_KEYWORDS,
            "organizations": ORGANIZATION_KEYWORDS
        }
    },
    "events": {
        "description": "Upcoming conferences, events, workshops, talks, virtual events, panels, panel discussions, and meetups",
        "keyword_groups": {
            "events": [
                "plurality conference", "digital democracy workshop",
                "collective intelligence symposium", "governance innovation",
                "tech ethics", "tech policy", "tech policy press",
                "tech policy conference", "tech policy workshop",
                "tech policy symposium", "tech policy panel",
                "tech policy panel discussion", "tech policy meetup",
                "AI ethics talk", "AI ethics symposium"
            ]
        }
    },
    "jobs": {
        "description": "Job opportunities, fellowships, grants, research funding and positions",
        "keyword_groups": {
            "jobs": [
                "plurality researcher", "digital democracy",
                "collective intelligence", "tech ethics researcher",
                "governance innovation", "All Tech is Human", "tech policy",
                "Tech For Good", "AI Safety", "AI Ethics", "AI Governance",
                "AI Policy", "AI Regulation", "Gitcoin Grants", "RadicalX",
                "New_ public"
            ]
        }
    }
}

def get_plurality_updates_for_group(category_name, group_name, keywords):
    """
    Fetches latest updates for a specific keyword group using Perplexity API.
    
    Args:
        category_name (str): Name of the category
        group_name (str): Name of the keyword group
        keywords (list): List of keywords to search for
        
    Returns:
        dict: Structured information about the latest updates
    """
    url = "https://api.perplexity.ai/chat/completions"
    
    MAX_KEYWORDS_PER_REQUEST = 15
    keyword_chunks = [keywords[i:i + MAX_KEYWORDS_PER_REQUEST] 
                     for i in range(0, len(keywords), MAX_KEYWORDS_PER_REQUEST)]
    
    all_items = []
    
    for chunk in keyword_chunks:
        keywords_str = ", ".join(chunk)
        
        headers = {
            "Authorization": f"Bearer {API_KEY}",
            "Content-Type": "application/json"
        }
        
        category_description = PLURALITY_CATEGORIES[category_name]["description"]
        
        prompt = f"""You are a content curator for Plurality Institute that sources jobs, events, research papers, media and other information.
Find {category_description} related to the following keywords:
{keywords_str}

IMPORTANT: 
- Today's date is {datetime.now().strftime("%Y-%m-%d")}
- Only include items from the past 30 days, with a strong preference for items from the past 7 days
- For events, prioritize events that occur ON OR AFTER {datetime.now().strftime("%Y-%m-%d")}
- For jobs and opportunities, prioritize positions that are currently open
- EXCLUDE any content older than 2 months except for research papers
- Include titles, dates, brief descriptions, links, and sources.

Format your response as a JSON object with the following structure:
{{
  "items": [
    {{
      "title": "Item title",
      "date": "Publication date in YYYY-MM-DD format when possible",
      "description": "Brief description (50 words max)",
      "link": "URL if available",
      "source": "Source name"
    }}
  ]
}}

Only include highly relevant items. Prioritize reputable sources.
Do NOT include any content from plurality.institute or the Plurality Institute's own website.
If you find fewer than 3 items, expand your search to include additional relevant content.
Include information from academic journals, podcasts, blogs, LinkedIn, news sites, conference websites, job boards, and social media as appropriate.
"""
        
        data = {
            "model": "sonar-pro", 
            "messages": [
                {
                    "role": "system",
                    "content": "You are a specialized research assistant and content curator for Plurality Institute, focused on finding and summarizing the latest relevant information."
                },
                {
                    "role": "user",
                    "content": prompt
                }
            ],
            "max_tokens": 1500,
            "temperature": 0.2  # Lower temperature for more factual responses
        }
        
        # Use lower temperature for jobs and events to reduce hallucination
        if category_name in ["jobs", "events"]:
            data["temperature"] = 0.1
        
        try:
            print(f"  Making API request for {category_name}/{group_name} (chunk of {len(chunk)} keywords)...")
            response = requests.post(url, headers=headers, json=data)
            response.raise_for_status()
            
            result = response.json()
            content = result["choices"][0]["message"]["content"]
            
            try:
                chunk_results = json.loads(content)
                if "items" in chunk_results and chunk_results["items"]:
                    # For events, double-check dates
                    if category_name == "events":
                        filtered_items = []
                        unfiltered_count = len(chunk_results["items"])
                        
                        for item in chunk_results["items"]:
                            date_str = item.get("date", "")
                            
                            try:
                                # Try to parse the date, allowing some flexibility
                                if date_str:
                                    # Various date formats
                                    for fmt in ("%Y-%m-%d", "%Y/%m/%d", "%B %d, %Y", "%d %B %Y"):
                                        try:
                                            parsed_date = datetime.strptime(date_str, fmt).date()
                                            current_date = datetime.now().date()
                                            
                                            # Keep future events
                                            if parsed_date >= current_date:
                                                filtered_items.append(item)
                                                break
                                            elif len(filtered_items) < 3 and parsed_date >= current_date - timedelta(days=14):
                                                # Keep some very recent past events if we don't have enough items
                                                item["date"] = f"Recent: {date_str}"
                                                filtered_items.append(item)
                                                break
                                        except ValueError:
                                            continue
                                else:
                                    # No date provided, include it
                                    filtered_items.append(item)
                            except Exception as e:
                                # Include items with parsing issues
                                print(f"  Error parsing event date: {e}")
                                filtered_items.append(item)
                        
                        if not filtered_items and chunk_results["items"]:
                            # If we filtered out everything, keep at least some items
                            filtered_items = chunk_results["items"][:3]
                            print(f"  Warning: All {unfiltered_count} events filtered out. Keeping some to prevent empty results.")
                        
                        all_items.extend(filtered_items)
                        print(f"  Found {len(filtered_items)} events for this chunk after date filtering")
                    else:
                        # For non-event categories, add items without date filtering
                        all_items.extend(chunk_results["items"])
                        print(f"  Found {len(chunk_results['items'])} items for this chunk")
            except json.JSONDecodeError:
                print(f"  Error parsing JSON response for {category_name}/{group_name}. Raw response:")
                print(content[:200] + "..." if len(content) > 200 else content)
                
        except requests.exceptions.RequestException as e:
            print(f"  Error making API request for {category_name}/{group_name}: {str(e)}")
        except (KeyError, IndexError) as e:
            print(f"  Error parsing API response for {category_name}/{group_name}: {str(e)}")
        except Exception as e:
            print(f"  Unexpected error for {category_name}/{group_name}: {str(e)}")
        
        time.sleep(2)
    
    return {"items": all_items}

def get_plurality_updates(category_name, category_info):
    """
    Fetches latest updates for all keyword groups in a category, combining results.
    
    Args:
        category_name (str): Name of the category
        category_info (dict): Dictionary with category description and keyword groups
        
    Returns:
        dict: Combined results from all keyword groups
    """
    print(f"Processing category: {category_name}...")
    all_items = []
    
    for group_name, keywords in category_info["keyword_groups"].items():
        group_results = get_plurality_updates_for_group(category_name, group_name, keywords)
        if "items" in group_results:
            all_items.extend(group_results["items"])
    
    unique_items = []
    seen_titles = set()
    
    for item in all_items:
        title = item.get("title", "").strip()
        if title and title not in seen_titles:
            seen_titles.add(title)
            unique_items.append(item)
    
    print(f"Found {len(unique_items)} unique items for {category_name}")
    return {"items": unique_items}

def get_previous_reports(max_reports=30):
    """
    Get a list of previous reports in the output directory.
    
    Args:
        max_reports (int): Maximum number of previous reports to include
        
    Returns:
        list: List of tuples (date, filename) of previous reports
    """
    import os
    import re
    
    reports = []
    
    if not os.path.exists("output"):
        return reports
    
    pattern = r"plurality_report_(\d{4}-\d{2}-\d{2})\.html"
    
    for filename in os.listdir("output"):
        match = re.match(pattern, filename)
        if match:
            date = match.group(1)
            reports.append((date, filename))
    
    reports.sort(reverse=True)
    
    return reports[:max_reports]

def generate_html_report(results):
    """
    Generates an HTML report from the collected results, including a sidebar for previous reports.
    
    Args:
        results (dict): Dictionary mapping categories to their results
        
    Returns:
        str: HTML content of the report
    """
    today = datetime.now().strftime("%Y-%m-%d")
    previous_reports = get_previous_reports()
    
    # Add JavaScript for better navigation
    navigation_script = """
    <script>
        // Store current report page in sessionStorage
        function storeCurrentPage() {
            sessionStorage.setItem('currentReport', window.location.href);
        }
        
        // Navigate back to most recent report
        function backToLatest() {
            window.location.href = 'plurality_report_' + getCurrentDate() + '.html';
            return false;
        }
        
        function getCurrentDate() {
            const now = new Date();
            return now.getFullYear() + '-' + 
                   String(now.getMonth() + 1).padStart(2, '0') + '-' + 
                   String(now.getDate()).padStart(2, '0');
        }
        
        // Initialize when the DOM is fully loaded
        document.addEventListener('DOMContentLoaded', function() {
            storeCurrentPage();
            
            // Add event listener to "Back to Latest" button
            const backBtn = document.getElementById('back-to-latest');
            if (backBtn) {
                backBtn.addEventListener('click', backToLatest);
            }
        });
    </script>
    """
    
    # Add CSS for the back button
    back_button_css = """
    .back-button {
        background-color: var(--primary-dark);
        color: white;
        border: none;
        padding: 8px 12px;
        margin: 10px 0;
        border-radius: var(--border-radius);
        cursor: pointer;
        width: 100%;
        font-weight: 500;
        transition: background-color var(--transition-speed);
    }
    
    .back-button:hover {
        background-color: var(--primary-color);
    }
    """
    
    html = f"""<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Plurality Daily Knowledge Report - {today}</title>
    <!-- Google Fonts -->
    <link rel="preconnect" href="https://fonts.googleapis.com">
    <link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
    <link href="https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600&family=Poppins:wght@400;500;600;700&display=swap" rel="stylesheet">
    <style>
        :root {{
            --primary-color: #7050b0;
            --primary-light: #9070d0;
            --primary-dark: #5a3a9a;
            --secondary-color: #aa90f0;
            --text-color: #333;
            --text-light: #7f8c8d;
            --bg-color: #f9f9f9;
            --card-color: white;
            --checked-color: #d4edda;
            --border-radius: 8px;
            --transition-speed: 0.3s;
        }}
        
        * {{
            box-sizing: border-box;
            margin: 0;
            padding: 0;
        }}
        
        body {{
            font-family: 'Inter', sans-serif;
            line-height: 1.6;
            color: var(--text-color);
            margin: 0;
            padding: 0;
            background-color: var(--bg-color);
            display: flex;
            min-height: 100vh;
        }}
        
        .sidebar {{
            width: 250px;
            background-color: var(--primary-light);
            color: white;
            padding: 20px;
            position: sticky;
            top: 0;
            height: 100vh;
            overflow-y: auto;
            box-shadow: 0 0 15px rgba(0,0,0,0.1);
            transition: all var(--transition-speed);
        }}
        
        .sidebar h2 {{
            font-family: 'Poppins', sans-serif;
            color: white;
            border-bottom: 1px solid rgba(255, 255, 255, 0.3);
            padding-bottom: 10px;
            margin-top: 0;
            font-weight: 600;
        }}
        
        .sidebar ul {{
            list-style: none;
            padding: 0;
            margin-top: 15px;
        }}
        
        .sidebar li {{
            margin-bottom: 8px;
            border-radius: var(--border-radius);
            overflow: hidden;
            transition: transform var(--transition-speed);
        }}
        
        .sidebar li:hover {{
            transform: translateX(5px);
        }}
        
        .sidebar a {{
            color: #ecf0f1;
            text-decoration: none;
            display: block;
            padding: 8px 10px;
            border-radius: var(--border-radius);
            transition: background-color var(--transition-speed);
        }}
        
        .sidebar a:hover {{
            background-color: var(--primary-dark);
        }}
        
        .sidebar a.active {{
            background-color: var(--primary-dark);
            font-weight: 500;
        }}
        
        .content {{
            flex: 1;
            padding: 30px;
            max-width: 1000px;
            margin: 0 auto;
        }}
        
        h1 {{
            font-family: 'Poppins', sans-serif;
            color: var(--primary-color);
            border-bottom: 2px solid var(--primary-light);
            padding-bottom: 10px;
            margin-top: 0;
            margin-bottom: 20px;
            font-weight: 600;
        }}
        
        h2 {{
            font-family: 'Poppins', sans-serif;
            color: var(--primary-color);
            border-left: 4px solid var(--primary-light);
            padding-left: 10px;
            margin-top: 30px;
            margin-bottom: 15px;
            font-weight: 500;
        }}
        
        .item {{
            background-color: white;
            border-radius: 8px;
            box-shadow: 0 2px 8px rgba(0,0,0,0.08);
            padding: 20px;
            margin-bottom: 20px;
            transition: box-shadow 0.3s ease;
        }}
        
        .item:hover {{
            box-shadow: 0 4px 12px rgba(0,0,0,0.12);
        }}
        
        .item h3 {{
            font-family: 'Poppins', sans-serif;
            color: var(--primary-color);
            margin-top: 0;
            margin-bottom: 8px;
            font-weight: 500;
        }}
        
        .item p {{
            margin: 5px 0;
        }}
        
        .date {{
            color: var(--text-light);
            font-size: 0.9em;
            margin-bottom: 8px;
        }}
        
        .source {{
            color: var(--text-light);
            font-size: 0.9em;
            text-align: right;
            margin-top: 10px;
        }}
        
        .description {{
            margin: 10px 0;
            line-height: 1.6;
        }}
        
        a {{
            color: var(--primary-color);
            text-decoration: none;
            transition: color var(--transition-speed);
        }}
        
        a:hover {{
            color: var(--primary-dark);
            text-decoration: underline;
        }}
        
        .report-date {{
            text-align: right;
            color: var(--text-light);
            font-size: 0.9em;
            margin-top: 10px;
            margin-bottom: 20px;
        }}
        
        .category-description {{
            font-style: italic;
            color: #555;
            margin-bottom: 20px;
        }}
        
        .no-items {{
            font-style: italic;
            color: var(--text-light);
            padding: 15px;
            background-color: var(--card-color);
            border-radius: var(--border-radius);
            box-shadow: 0 3px 10px rgba(0,0,0,0.05);
        }}
        
        {back_button_css}
    </style>
    {navigation_script}
</head>
<body>
    <div class="sidebar">
        <h2>Plurality Reports</h2>
        <button id="back-to-latest" class="back-button">Back to Latest</button>
        <ul id="sidebar-reports">
            <li><a href="plurality_report_{today}.html" class="active">Today ({today})</a></li>
"""
    
    # Add links to previous reports
    for date, filename in previous_reports:
        if date != today:  # Don't duplicate today's report
            html += f'            <li><a href="{filename}">{date}</a></li>\n'
    
    html += """
        </ul>
    </div>
    
    <div class="content">
        <h1>Plurality Institute Daily Content Curator</h1>
        <p class="report-date">Generated on: """ + today + """</p>
"""
    
    item_counter = 0
    for category_name, category_data in results.items():
        category_title = category_name.replace('_', ' ').title()
        category_description = PLURALITY_CATEGORIES[category_name]["description"]
        
        html += f"""
        <h2>{category_title}</h2>
        <p class="category-description">{category_description}</p>
"""
        
        if not category_data.get("items") or len(category_data["items"]) == 0:
            html += '        <p class="no-items">No recent items found.</p>'
            continue
            
        for item in category_data["items"]:
            item_counter += 1
            item_id = f"item-{category_name}-{item_counter}"
            
            title = item.get("title", "Untitled")
            date = item.get("date", "")
            description = item.get("description", "")
            link = item.get("link", "")
            source = item.get("source", "")
            
            html += f"""
        <div class="item" id="{item_id}">
            <div class="item-header">
                <div class="item-checkbox">
                    <input type="checkbox" data-id="{item_id}">
                </div>
                <h3>{"<a href='" + link + "' target='_blank'>" if link else ""}{title}{"</a>" if link else ""}</h3>
            </div>
            {f'<p class="date">{date}</p>' if date else ''}
            <p class="description">{description}</p>
            {f'<p class="source">Source: {source}</p>' if source else ''}
        </div>
"""
    
    html += """
    </div>
</body>
</html>"""
    
    return html

def update_report_index():
    """
    Creates or updates a JSON file that indexes all available reports.
    This will be used by the HTML reports to dynamically build the sidebar.
    """
    import os
    import re
    import json
    
    reports = []
    if not os.path.exists("output"):
        os.makedirs("output", exist_ok=True)
        return
    
    pattern = r"plurality_report_(\d{4}-\d{2}-\d{2})\.html"
    
    for filename in os.listdir("output"):
        match = re.match(pattern, filename)
        if match:
            date = match.group(1)
            reports.append({
                "date": date,
                "filename": filename
            })
    
    # Sort reports by date (newest first)
    reports.sort(key=lambda x: x["date"], reverse=True)
    
    # Write to index file
    index_path = os.path.join("output", "report_index.json")
    with open(index_path, "w", encoding="utf-8") as f:
        json.dump({"reports": reports}, f)
    
    return reports

def save_report(html_content, filename=None):
    """
    Saves the HTML report to a file and ensures all links are valid.
    
    Args:
        html_content (str): HTML content to save
        filename (str, optional): Filename to save to. Defaults to auto-generated name.
    
    Returns:
        str: Path to the saved file
    """
    if filename is None:
        today = datetime.now().strftime("%Y-%m-%d")
        filename = f"plurality_report_{today}.html"
    
    # Create output directory if it doesn't exist
    os.makedirs("output", exist_ok=True)
    
    # Create an index.html that redirects to the latest report
    index_html = f"""<!DOCTYPE html>
    <html>
    <head>
        <meta http-equiv="refresh" content="0; url=plurality_report_{datetime.now().strftime('%Y-%m-%d')}.html">
    </head>
    <body>
        <p>Redirecting to latest report...</p>
    </body>
    </html>
    """
    
    with open(os.path.join("output", "index.html"), "w", encoding="utf-8") as f:
        f.write(index_html)
    
    filepath = os.path.join("output", filename)
    with open(filepath, "w", encoding="utf-8") as f:
        f.write(html_content)
    
    return filepath

def main():
    """Main function that runs the Plurality Knowledge Bot."""
    print("Starting Plurality Knowledge Bot...")
    print(f"Gathering information for {len(PLURALITY_CATEGORIES)} categories...")
    
    results = {}
    
    for category_name, category_info in PLURALITY_CATEGORIES.items():
        results[category_name] = get_plurality_updates(category_name, category_info)
    html_report = generate_html_report(results)
    
    today = datetime.now().strftime("%Y-%m-%d")
    report_filename = f"plurality_report_{today}.html"
    report_path = save_report(html_report, report_filename)
    
    index_path = save_report(html_report, "index.html")
    
    print(f"Report generated successfully at: {report_path}")
    print(f"Latest report also saved to: {index_path}")

if __name__ == "__main__":
    main()