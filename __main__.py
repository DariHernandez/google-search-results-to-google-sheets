import os
import time
import urllib.parse
from config import Config
from logs import logger
from scraping_manager.automate import Web_scraping
from config import Config
from spreadsheet_manager.google_ss import SS_manager

keywords = "hola mundo programación"
def main (): 

    # Generate URL
    keywords_text = urllib.parse.quote(keywords.replace(" ", "+"))
    url = f"https://www.google.com/search?q={keywords_text}"

    # Get credentials from config
    credentials = Config()
    headless = not credentials.get ("show_browser")
    max_results = credentials.get ("max_results")
    gs_link = credentials.get ("gs_link")
    gs_credentials = os.path.join (os.path.dirname(__file__), "spreadsheet_manager", "credentials.json")

    ss_manager = ss_keywords = SS_manager(gs_link, gs_credentials, "Keywords")

    # # Connect google sheets
    # ss_keywords = SS_manager(gs_link, gs_credentials, "Keywords")
    # ss_results_meta = SS_manager(gs_link,gs_credentials, "Results meta")
    # ss_results_structure = SS_manager(gs_link, gs_credentials, "Results structure")

    # # Clean google sheets
    # ss_keywords.worksheet.clear ()
    # ss_results_meta.worksheet.clear ()
    # ss_results_structure.worksheet.clear ()

    # Start browser
    scraper = Web_scraping (headless=headless, web_page=url)

    # Get first results
    selector_results_elems = "#search > div .yuRUbf > a"
    result_links = []
    more_pages = True
    while more_pages:

        results_elems = scraper.get_elems (selector_results_elems)
        for result_elem in results_elems:

            # Get valid links
            link = result_elem.get_attribute("href")
            title = result_elem.find_element_by_css_selector ("h3").text
            if not title:
                continue

            # Skip pdf files
            if ".pdf" in link:
                continue

            # Save valid links
            result_links.append (link)
            if len (result_links) == max_results:
                more_pages = False
                break      

    # Go to next results page
    if more_pages:
        selector_next = "#pnnext"
        scraper.click (selector_next)

    # Extract data from links pages
    result_position = 0
    data = []
    for link in result_links:

        # Open next page
        result_position += 1
        scraper.set_page (link)
        time.sleep (1)

        # Get meta data (title)
        selector_title = "head > title"
        title = scraper.get_elem (selector_title).get_attribute('innerHTML')
        title_lenght = len(title)

        # Get meta data (description)
        selector_description = 'head > meta[name="description"]'
        try:
            description = scraper.get_elem (selector_description).get_attribute('innerHTML')
        except: 
            pass
        else:
            description = ""
        description_lenght = len(description)

        # Get page structure
        selector_structure = "h1, h2, h3, h4, h5, h3"
        headers_elem = scraper.get_elems (selector_structure)
        headers_formated = []
        for header in headers_elem:

            header_text = header.text
            header_tag = header.tag_name
            header_formated = f"<{header_tag}>{header_text}<{header_tag}/>"
            headers_formated.append (header_formated)
        
        # Save data
        data_row = {
            "url": link,
            "position": result_position,
            "title": title, 
            "title_lenght": title_lenght,
            "description": description, 
            "description_lenght": description_lenght,
            "structure": headers_formated
        }
        data.append (data_row)
    
    # KEYWORDS SHEET
    # Set sheet and clean
    ss_manager.change_sheet ("Keywords")
    ss_manager.worksheet.clear ()

    # Create header
    data_formated = []
    data_formated.append (["Google Main Keyword"])

    # Format data
    data_formated.append ([keywords])

    # Save
    ss_keywords.write_data (data_formated)

    # META SHEET
    # Set sheet and clean
    ss_manager.change_sheet ("Results meta")
    ss_manager.worksheet.clear ()

    # Create header
    data_formated = []
    data_formated.append (["Position", "Meta Title", "Length", "Meta Description", "Length", "URL"])

    # Format data
    for page in data:
        row_formated = [
            page["position"],
            page["title"],
            page["title_lenght"],
            page["description"],
            page["description_lenght"],
            page["url"],
        ]
        data_formated.append (row_formated)
    
    # Save
    ss_manager.write_data (data_formated)


if __name__ == "__main__":
    main()