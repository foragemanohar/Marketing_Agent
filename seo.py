import time
import os
import pickle
import markdown
from playwright.sync_api import sync_playwright
from constants import SEO_SCORE_FILE
import time
import re

class BrowserManager:
    """Manages Playwright browser lifecycle and dynamic cookie handling."""

    def __init__(self, headless=False):
        print("Initializing Playwright...")
        self.playwright = sync_playwright().start()
        self.browser = self.playwright.chromium.launch(
            headless=headless, slow_mo=50)
        self.context = self.browser.new_context()
        self.cookies_loaded = self.load_cookies()
        self.page = self.context.new_page()

    def close_browser(self):
        """Properly closes the browser and stops Playwright."""
        print("Closing browser...")
        self.browser.close()
        self.playwright.stop()

    def load_cookies(self):
        """Loads cookies dynamically before login."""
        if os.path.exists("cookies.pkl"):
            print("Attempting to load cookies...")
            with open("cookies.pkl", "rb") as file:
                cookies = pickle.load(file)

            current_time = time.time()
            valid_cookies = [cookie for cookie in cookies if cookie.get(
                "expires", current_time + 1) > current_time]

            if valid_cookies:
                self.context.add_cookies(valid_cookies)
                print("✅ Cookies loaded successfully.")
                return True
            else:
                print("⚠️ No valid cookies found. Fresh login required.")
                return False
        return False

    def save_cookies(self, domain="https://www.semrush.com"):
        """Saves cookies dynamically after login."""
        cookies = self.context.cookies([domain])
        current_time = time.time()

        for cookie in cookies:
            if "expires" not in cookie or cookie["expires"] == -1:
                cookie["expires"] = current_time + \
                    (30 * 24 * 60 * 60)  # 30 days

        with open("cookies.pkl", "wb") as file:
            pickle.dump(cookies, file)

        print("✅ Cookies saved successfully for future sessions.")


class SEMrushLogin:
    """Handles login to SEMrush with cookie-based authentication."""

    def __init__(self, browser_manager: BrowserManager):
        self.page = browser_manager.page

    def login(self, username, password):
        """Logs in to SEMrush only if cookies are not valid."""
        print("🔑 Logging in to SEMrush...")

        self.page.goto("https://www.semrush.com/")
        self.page.click("//span[text()='Log In']")
        self.page.wait_for_selector('//*[@id="email"]', timeout=10000)
        self.page.fill('//*[@id="email"]', username)
        self.page.fill('//*[@id="password"]', password)
        self.page.click("//button[.//span[text()='Log in']]")

        time.sleep(3)

        try:
            self.page.wait_for_selector(
                "//h1[contains(text(), 'Projects')]", timeout=30000)
            print("✅ Login successful.")
            return True
        except:
            print("❌ Login failed.")
            return False


class SEMrushSEOAssistant:
    """Handles SEMrush SEO Writing Assistant interactions."""

    def __init__(self, browser_manager: BrowserManager):
        self.page = browser_manager.page
        



    def scrape_suggestions(self):
        """Extracts readability, SEO, tone, and originality suggestions."""
        print("🔍 [DEBUG] Starting the scraping process...")
        try:

    # ✅ Step 1: Locate and Scroll the SEO Score & Suggestions Section
            div_xpath = "//div[@class='swa-nyjzmhOs']"
            print("🔍 [DEBUG] Locating SEO Score & Suggestions section...")

            if self.page.locator(div_xpath).count() > 0:
                self.page.wait_for_selector(div_xpath, timeout=10000)
                div = self.page.locator(div_xpath)
                print(
                    "✅ [DEBUG] Found SEO Score section. Attempting to scroll into view...")
                div.scroll_into_view_if_needed()
                print("✅ [DEBUG] Successfully scrolled to SEO Score section.")
            else:
                print("❌ [DEBUG] SEO Score section NOT found! Exiting...")
                return
        except :
            print("error in locating section\n")    
            
    # step:2 clicking readibility:
        try:
            readability_xpath = "//span[contains(@class, 'swa-LtXjBYII') and text()='Readability']"

            readability_button = self.page.locator(readability_xpath)

            print("🔍 [DEBUG] Checking if Readability button is interactable...")

            # ✅ Step 1: Wait for the element to be visible
            self.page.wait_for_selector(readability_xpath, timeout=5000)

            # ✅ Step 2: Convert to an element handle
            element_handle = readability_button.element_handle()

            if element_handle:
                print("🔍 [DEBUG] Element handle found. Waiting for stability...")

                # ✅ Step 3: Now wait for the element to be stable & enabled
                element_handle.wait_for_element_state("stable")
                element_handle.wait_for_element_state("enabled")

                print("✅ [DEBUG] Clicking Readability button...")
                readability_button.click(force=True)
                time.sleep(10)  # 🔥 Use force in case of overlays
                print("✅ [DEBUG] Successfully clicked Readability button!")
        except:
            print("error in clciking the reability\n")    
       

        try:
                slider_xpath = "//div[contains(@class, '___SSlider_') and @data-ui-name='Bar.Slider']"
                print("🔍 [DEBUG] Locating slider element...")

                if self.page.locator(slider_xpath).count() > 0:
                    self.page.wait_for_selector(slider_xpath, timeout=5000)
                    slider = self.page.locator(slider_xpath)
                    print("✅ [DEBUG] Slider found. Checking visibility...")

                if slider.is_visible():
                    print("✅ [DEBUG] Slider is visible. Attempting to move slider...")
                    box = slider.bounding_box()

                if box:
                    print(f"✅ [DEBUG] Slider bounding box found: {box}")

                    start_x = box["x"] + box["width"] / 2
                    start_y = box["y"] + box["height"] / 2

                    self.page.mouse.move(start_x, start_y)
                    self.page.mouse.down()

                    prev_y = start_y

                    while True:
                        # 🔽 Scroll down slowly (small step + 1s delay)
                        self.page.mouse.move(start_x, prev_y + 50, steps=10)
                        time.sleep(1)  # ✅ Added delay for slow scrolling

                        new_box = slider.bounding_box()

                        if not new_box:
                            print("❌ [DEBUG] Failed to get slider position during movement.")
                            break

                        new_y = new_box["y"] + new_box["height"] / 2
                        print(f"🔍 [DEBUG] Current slider Y position: {new_y}")

                        # ✅ Detect "Show More" button while scrolling
                        show_more_xpath = "//div[contains(@class, 'swa-KUtEB2tH') and @role='button']//span[text()='Show more']"
                        show_more_button = self.page.locator(show_more_xpath).first

                        if show_more_button.is_visible():
                            print("✅ [DEBUG] Clicking 'Show More' button...")
                            show_more_button.click(force=True)
                            # ✅ Wait for new content to load before continuing scroll
                            time.sleep(10)

                        # 🔥 Stop scrolling if there's little movement (indicates bottom reached)
                        if abs(new_y - prev_y) < 5:
                            print("✅ [DEBUG] Slider reached the bottom.")
                            break

                        prev_y = new_y

                    print("✅ [DEBUG] Slider fully scrolled down.")

                    # ✅ Scrape sentences after scrolling
                    sentence_xpath = "//div[@role='listitem']//div[contains(@class, '___SBoxInline_1vt8n_swa-addon_') and @aria-haspopup='true']"
                    sentences = self.page.locator(sentence_xpath).all_text_contents()
                    time.sleep(20)  # ✅ Ensure full page load

                    if sentences:
                        print(
                            f"✅ [DEBUG] Extracted {len(sentences)} hard-to-read sentences.")

                        # ✅ Save sentences sequentially with headings
                        with open("readability_suggestions.txt", "w", encoding="utf-8") as f:
                            f.write("Replace the below read to hard sentences and complex words\n\n")

                            for i, sentence in enumerate(sentences, 1):
                                cleaned_sentence = sentence.strip()
                                if cleaned_sentence:
                                    f.write(f"{i}. {cleaned_sentence}\n")

                            f.write("\n=== End of Extraction ===\n")

                        print("✅ [DEBUG] Hard sentences saved to 'hard_sentences.txt'")
                    else:
                        print("❌ [DEBUG] No hard-to-read sentences found.")


        except:
                print(f"❌ [ERROR] An error occurred: ")



    def open_seo_assistant(self):
        """Navigates to SEMrush SEO Writing Assistant."""
        print("📂 Opening SEMrush SEO Writing Assistant...")
        self.page.goto("https://www.semrush.com/swa/")
        self.page.wait_for_load_state("networkidle")
        time.sleep(3)

    def start_new_analysis(self):
        """Clicks 'Analyze new text' to start an SEO check."""
        print("📝 Starting new SEO analysis...")
        analyze_button_xpath = "(//a[@data-test='swa-spa-create-template-button'])[1]"
        self.page.wait_for_selector(analyze_button_xpath, timeout=30000)
        self.page.click(analyze_button_xpath)
        self.page.wait_for_selector(
            "//div[contains(@class, 'ql-editor') and @contenteditable='true']", timeout=60000)
        print("✅ Ready for text input.")
        time.sleep(2)

    def paste_text_and_analyze(self, file_path):
        """Reads Markdown content, converts it to HTML, and pastes into SEMrush editor."""
        print("✏️ Reading and converting Markdown to HTML...")

        # Read Markdown file
        with open(file_path, "r", encoding="utf-8") as file:
            md_content = file.read()

        # Convert Markdown to HTML
        html_content = markdown.markdown(md_content)
        # print("The html content is\n",html_content)

        html_content = re.sub(r'\s*<li>\s*', '', html_content)

        html_content = re.sub(r'\s*</li>\s*', '', html_content)

        # Remove <ul> and <ol> tags if they exist
        html_content = re.sub(r'\s*<ul>\s*', '', html_content)
        html_content = re.sub(r'\s*</ul>\s*', '', html_content)
        html_content = re.sub(r'\s*<ol>\s*', '', html_content)
        html_content = re.sub(r'\s*</ol>\s*', '', html_content)
        
        from pathlib import Path
        Path("test.html").write_text(html_content, encoding="utf-8")
        html_content = re.sub(
            r'(?<=</strong>)(?=<strong>)', '<br>', html_content
        )


      # Ensure line breaks after consecutive <strong> elements
        html_content = re.sub(
        r'(<strong>.*?</strong>)(?=<strong>)', r'\1<br>', html_content)


        # Remove leading/trailing spaces in headings
        html_content = re.sub(r'(<h[1-3]>)\s*', r'\1', html_content)
        html_content = re.sub(r'\s*(</h[1-3]>)', r'\1', html_content)

        # Reduce space between heading and first paragraph
        html_content = re.sub(r'(\s*</h[1-3]>)\s*<p>', r'\1<p>', html_content)

        # Reduce space between <h2> and first bolded text
        html_content = re.sub(r'(\s*</h2>)\s*<p>\s*<strong>',
                              r'\1<p><strong>', html_content)

        # Reduce space between main title and next heading
        html_content = re.sub(r'(</h1>)\s*<h[2-3]>', r'\1<h2>', html_content)

        # Adjust paragraph spacing to prevent excessive gaps
        html_content = re.sub(r'(\s*</p>)\s*<p>', r'\1<p>', html_content)

        # Convert H4-H6 into bold text instead of headings
        html_content = re.sub(r'<h[4-6]>(.*?)</h[4-6]>',
                              r'<p><strong>\1</strong></p>', html_content)

        # Remove empty paragraphs
        html_content = re.sub(r'<p>\s*</p>', '', html_content)

        # Preserve bold text inside list items
        html_content = re.sub(r'<li>\s*<strong>\s*',
                              '<li><strong>', html_content)
        html_content = re.sub(r'\s*</strong>\s*</li>',
                              '</strong></li>', html_content)

        # Fix bullet points disappearing after paragraphs
        html_content = re.sub(r'</p>\s*\n*\s*<(ul|ol)>',
                              r'</p><\1>', html_content)

        # Ensure each <li> ends properly before a new <li> begins (handle newlines within lists)
        html_content = re.sub(r'(<li>.*?)(\n\s*)(<li>)',
                              r'\1</li>\3', html_content)

        # Remove excessive newlines between list items and paragraphs
        html_content = re.sub(r'</li>\s*\n+\s*(<li>)',
                              r'</li><li>', html_content)
        html_content = re.sub(r'</ul>\s*\n+\s*(<p>)', r'</ul>\1', html_content)
        html_content = re.sub(r'</p>\s*\n+\s*(<ul>)',
                              r'</p><\1>', html_content)

        # Remove excessive newlines overall
        html_content = re.sub(r'\n{3,}', '\n', html_content)

        # Remove spaces between HTML tags
        html_content = re.sub(r'>\s+<', '><', html_content)

        # --- FINAL PASTE INTO SEMRUSH ---
        editor_xpath = "//div[contains(@class, 'ql-editor') and @contenteditable='true']"
        self.page.wait_for_selector(editor_xpath, timeout=10000)
        self.page.locator(editor_xpath).evaluate(
            "(element, value) => document.execCommand('insertHTML', false, value)", html_content
        )

        time.sleep(2)
        print("✅ Content pasted and formatted successfully!")

        # Click 'Extract from text' button
        extract_button_xpath = "//div[@role='button' and @aria-haspopup='true']//span[text()='Extract from text']"
        self.page.wait_for_selector(extract_button_xpath, timeout=10000)
        self.page.click(extract_button_xpath)

        time.sleep(3)
        print("✅ Content extracted and ready for SEO analysis!")


    def click_get_recommendations(self):
            """Clicks 'Get Recommendations' button."""
            print("📊 Fetching recommendations...")
            get_recommendations_button = "//button[@data-ui-name='Button' and @type='submit']//span[text()='Get recommendations']"
            self.page.wait_for_selector(get_recommendations_button, timeout=10000)
            self.page.click(get_recommendations_button)
            time.sleep(3)

    def get_seo_score(self):
        """Fetches the SEO quality score and saves it to a file."""
        time.sleep(20)
        print("📈 Fetching SEO Score...")
        rating_xpath = "//div[@data-ui-name='Hint' and contains(@aria-label, 'Quality score of the article')]"
        # time.sleep(2000)
        try:
            self.page.wait_for_selector(rating_xpath, timeout=120000)
            seo_score = self.page.locator(rating_xpath).inner_text()

            # ✅ Save the score to seo_score.txt
            with open(SEO_SCORE_FILE, "w", encoding="utf-8") as file:
                file.write(seo_score.strip())


            print(f"✅ SEO Score saved: {seo_score}")
            return seo_score
        except:
            print("⚠️ Failed to fetch SEO Score.")
            return None
    
   

    def change_target_score(self):
        """Clicks 'Change target readability' button and updates values."""
        print("📝 Changing target readability...")

        # Click the 'Change target readability' button
        change_readability_button = "//div[@role='button' and contains(@aria-label, 'Change target readability')]"
        button = self.page.locator(change_readability_button)
        button.wait_for(state="visible", timeout=30000)
        button.click()

        # Locate both input fields
        input_fields = self.page.locator("input[data-ui-name='InputNumber.Value']")

        if input_fields.count() < 2:
            print("⚠️ Error: Expected two input fields, but found", input_fields.count())
            return

        # Change 'Reading Ease' value to 35 (1st Input)
        input_fields.nth(0).click()
        input_fields.nth(0).fill("")
        input_fields.nth(0).fill("35")
        time.sleep(3)
        # Change 'Target Text Length' value to 1900 (2nd Input)
        input_fields.nth(1).click()
        input_fields.nth(1).fill("")
        input_fields.nth(1).fill("1900")
        time.sleep(3)

        # Wait for changes to reflect
            # Click the 'Change Target' button to confirm the changes
        input_fields.nth(1).press("Enter")

        self.page.wait_for_timeout(2000)

        print("✅ Target readability and text length updated successfully!")

        time.sleep(30)  # Keep the browser open for verification

    def scrape_readability(self):
        """Extracts readability, SEO, tone, and originality suggestions."""
        print("Extracting readability suggestions...")

        readability_points_xpath = "//section[contains(@class, 'swa-_NA_jY1H')]"
        try:
            self.page.wait_for_selector(
                readability_points_xpath, timeout=30000)
            readability_items = self.page.locator(
                readability_points_xpath).all_text_contents()

            # Categorize suggestions
            sections = {"Readability": [], "SEO": [],
                        "Tone of Voice": [], "Originality": []}
            for item in readability_items:
                item_lower = item.lower()
                for key in sections.keys():
                    if key.lower() in item_lower:
                        sections[key].append(item.replace(key, "").strip())

            # Save to file
            with open("readability_suggestions.txt", "w", encoding="utf-8") as file:
                file.write("SEO & Readability Suggestions\n")
                file.write("=" * 35 + "\n\n")
                for section, content in sections.items():
                    file.write(f"{section}:\n{'-' * 15}\n")
                    file.write("\n".join(content)
                               if content else "No suggestions found.\n")
                    file.write("\n\n")

            print("Readability suggestions saved.")
        except Exception as e:
            print(f"Error extracting readability suggestions: {e}")


            

   
        

def run_seo_analysis():
    """Run the SEMrush SEO analysis."""
    browser_manager = BrowserManager(headless=False)

    try:
        if not browser_manager.cookies_loaded:
            login_manager = SEMrushLogin(browser_manager)
            if login_manager.login("amol.divakaran@forage.ai", "Buzz+Hive202X"):
                browser_manager.save_cookies()

        seo_assistant = SEMrushSEOAssistant(browser_manager)
        seo_assistant.open_seo_assistant()
        seo_assistant.start_new_analysis()

        html_content_path = "generated_content.md"
        time.sleep(10)
        seo_assistant.paste_text_and_analyze(html_content_path)
        time.sleep(10)
        seo_assistant.click_get_recommendations()
        time.sleep(20)
        seo_assistant.change_target_score()
        time.sleep(10)
        seo_score = seo_assistant.get_seo_score()
        time.sleep(20)
        seo_assistant.scrape_readability()
        time.sleep(10)
        seo_assistant.scrape_suggestions()
        print(f"Final SEO Score: {seo_score}")
    except Exception as e:
        print(f"🚨 Error: {e}")


if __name__ == "__main__":
    run_seo_analysis()


# self.page.locator(editor_xpath): Finds the editor (<div>).
# .evaluate(...): Runs JavaScript inside the browser.
# "element.innerHTML = value": Replaces the existing content with html_content.
# html_content: The formatted HTML text converted from Markdown.







