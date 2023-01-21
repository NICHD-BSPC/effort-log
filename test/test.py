from selenium import webdriver
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import Select

driver = webdriver.Firefox()
driver.get("http://127.0.0.1:3536")
driver.save_screenshot('1.png')
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

# Select a lab
pi_select = Select(driver.find_element(By.XPATH, "//select[@id='pi']"))
check_options(pi_select, ["---", "lab1", "lab2", "other"])
pi_select.select_by_visible_text("lab2")

# Now the project should be populated
check_options(proj_select, ["projectC", "projectD", "projectE", "other"])
proj_select.select_by_visible_text("projectD")

# Add a note
element = driver.find_element(By.XPATH, "//textarea")
element.send_keys("duly noted")
driver.save_screenshot('3.png')

# Submit form
driver.find_element(By.XPATH, "//input[@id='submit']").click()

# Ensure our just-added entry exists
driver.find_element(By.XPATH, "//td[contains(text(), 'duly noted')]")
driver.save_screenshot('4.png')
driver.close()
