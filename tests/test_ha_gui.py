"""GUI test for Weather Bitch integration in Home Assistant."""

import time
from playwright.sync_api import sync_playwright

HA_URL = "http://localhost:8123"
USERNAME = "michaelcoletta"
PASSWORD = "Mike1982!!"


def test_weatherbitch_integration():
    """Test the weatherbitch integration in Home Assistant GUI."""
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        context = browser.new_context(viewport={"width": 1920, "height": 1080})
        page = context.new_page()

        print("=" * 60)
        print("WEATHER BITCH INTEGRATION GUI TEST")
        print("=" * 60)

        # Step 1: Navigate to Home Assistant
        print("\n[1/7] Navigating to Home Assistant...")
        page.goto(HA_URL)
        page.wait_for_load_state("networkidle")
        time.sleep(2)
        page.screenshot(path="/tmp/ha_01_initial.png")
        print(f"      Screenshot saved: /tmp/ha_01_initial.png")

        # Step 2: Log in
        print("\n[2/7] Logging in...")
        # HA uses material design inputs - need to find the actual input elements
        username_input = page.locator("input").first
        password_input = page.locator("input").nth(1)

        username_input.fill(USERNAME)
        password_input.fill(PASSWORD)

        # Click the Log in button
        page.locator("text=Log in").click()
        page.wait_for_load_state("networkidle")
        time.sleep(3)  # Wait for dashboard to fully load
        page.screenshot(path="/tmp/ha_02_logged_in.png")
        print(f"      Screenshot saved: /tmp/ha_02_logged_in.png")

        # Step 3: Navigate to Settings > Devices & Services
        print("\n[3/7] Navigating to Settings > Devices & Services...")
        page.goto(f"{HA_URL}/config/integrations")
        page.wait_for_load_state("networkidle")
        time.sleep(3)
        page.screenshot(path="/tmp/ha_03_integrations.png")
        print(f"      Screenshot saved: /tmp/ha_03_integrations.png")

        # Step 4: Look for Weather Bitch integration
        print("\n[4/7] Looking for Weather Bitch integration...")
        page_content = page.content()

        if "weather bitch" in page_content.lower() or "weatherbitch" in page_content.lower():
            print("      Found Weather Bitch integration!")
        else:
            print("      Weather Bitch not visible on main integrations page")

        page.screenshot(path="/tmp/ha_04_search.png")
        print(f"      Screenshot saved: /tmp/ha_04_search.png")

        # Step 5: Navigate directly to weatherbitch integration page
        print("\n[5/7] Checking weatherbitch integration details...")
        page.goto(f"{HA_URL}/config/integrations/integration/weatherbitch")
        page.wait_for_load_state("networkidle")
        time.sleep(2)
        page.screenshot(path="/tmp/ha_05_weatherbitch_page.png")
        print(f"      Screenshot saved: /tmp/ha_05_weatherbitch_page.png")

        # Check if integration loaded
        content = page.content()
        if "not found" in content.lower() or "404" in content:
            print("      WARNING: Integration page shows not found")
        else:
            print("      Integration page loaded")

        # Step 6: Check Developer Tools > States for weather entities
        print("\n[6/7] Checking weather entities in Developer Tools...")
        page.goto(f"{HA_URL}/developer-tools/state")
        page.wait_for_load_state("networkidle")
        time.sleep(2)

        # Try to filter for weather entities
        try:
            filter_input = page.locator("input").first
            filter_input.fill("weather.")
            time.sleep(1)
        except Exception as e:
            print(f"      Could not filter: {e}")

        page.screenshot(path="/tmp/ha_06_dev_states.png")
        print(f"      Screenshot saved: /tmp/ha_06_dev_states.png")

        # Get weather entity info
        content = page.content()

        # Step 7: Check logs for errors
        print("\n[7/7] Checking logs for weatherbitch errors...")
        page.goto(f"{HA_URL}/config/logs")
        page.wait_for_load_state("networkidle")
        time.sleep(2)
        page.screenshot(path="/tmp/ha_07_logs.png")
        print(f"      Screenshot saved: /tmp/ha_07_logs.png")

        # Check for weatherbitch in logs
        log_content = page.content()

        print("\n" + "=" * 60)
        print("RESULTS")
        print("=" * 60)

        if "weatherbitch" in log_content.lower():
            print("\n[LOGS] Found weatherbitch mentions in logs")
            if "error" in log_content.lower():
                print("       WARNING: Potential errors found - check screenshots")
        else:
            print("\n[LOGS] No weatherbitch entries in recent logs (may be good)")

        # Final check - go back to states and get entity list
        page.goto(f"{HA_URL}/developer-tools/state")
        page.wait_for_load_state("networkidle")
        time.sleep(1)

        # Take a full page screenshot
        page.screenshot(path="/tmp/ha_08_final_states.png", full_page=True)
        print(f"\n[STATES] Full states screenshot: /tmp/ha_08_final_states.png")

        browser.close()

        print("\n" + "=" * 60)
        print("TEST COMPLETE - Review screenshots in /tmp/ha_*.png")
        print("=" * 60)


if __name__ == "__main__":
    test_weatherbitch_integration()
