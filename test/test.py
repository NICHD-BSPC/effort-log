"""
Usage:

    (
      source app/.env; source app/.test_env; 
      docker compose --env-file app/.env -f compose.yml -f compose-test.yml up -d
    )
    python test/test.py

Then to stop:

    docker compose --env-file app/.env -f compose.yml -f compose-test.yml down

"""

from selenium import webdriver
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import Select

driver = webdriver.Remote(
    # This is the port configured in compose-test.yml for the selenium
    # container
    command_executor='http://localhost:4444',
    options=webdriver.FirefoxOptions()
)

# Since it's the selenium container that's doing the GET, this is *within the
# docker network*, which uses hostnames as configured in docker compose.
driver.get("http://web:80")

# Save an initial screenshot
driver.save_screenshot('1.png')

# Click the "Add entry" button from the home page
add_entry_button = driver.find_element(By.XPATH, "//a[contains(text(), 'Add entry')]")
add_entry_button.click()

def check_options(element, expected):
    """
    Helper function to make sure a drop-down select element has the right
    options
    """
    observed = [i.text for i in element.options]
    assert observed == expected, observed

# Make sure the project starts off empty
proj_select = Select(driver.find_element(By.XPATH, "//select[@id='project']"))
assert proj_select.options == []

# Confirm the set of selection, and choose lab2
pi_select = Select(driver.find_element(By.XPATH, "//select[@id='pi']"))
check_options(pi_select, ["---", "lab1", "lab2", "other"])
pi_select.select_by_visible_text("lab2")

# Now the project dropdown should be populated
check_options(proj_select, ["projectC", "projectD", "projectE", "other"])

# Choose projectD
proj_select.select_by_visible_text("projectD")

# Add a note
element = driver.find_element(By.XPATH, "//textarea")
element.send_keys("duly noted")

# Save a screenshot of the filled-in form before submitting
driver.save_screenshot('3.png')

# Submit form
driver.find_element(By.XPATH, "//input[@id='submit']").click()

# Ensure our just-added entry exists
driver.find_element(By.XPATH, "//td[contains(text(), 'duly noted')]")

# and take a screenshot of the home page with table and plot.
driver.save_screenshot('4.png')
driver.close()
