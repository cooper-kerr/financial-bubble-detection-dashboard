
from playwright.sync_api import sync_playwright

def run(playwright):
    browser = playwright.chromium.launch(headless=True)
    page = browser.new_page()
    page.goto("http://localhost:3000")

    # Wait for the dashboard to load
    page.wait_for_selector('text="Financial Bubble Detection Dashboard"')

    # Take a screenshot of the initial state
    page.screenshot(path="jules-scratch/verification/verification_initial.png")

    # Select the "Yahoo Finance" data source
    page.click('button[id="data-source-select"]')
    page.click('div[role="option"]:has-text("Yahoo Finance")')


    # Take a screenshot of the new state
    page.screenshot(path="jules-scratch/verification/verification_yahoo.png")

    browser.close()

with sync_playwright() as playwright:
    run(playwright)
