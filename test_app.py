from app import create_app # application function factory function to create a test instance of the app
# defines a test to check
def test_home_page_redirects_to_login():
    print("Testing home page") # test starts
    app = create_app() # create the app instance
    client = app.test_client() # test client
    # sends a GET request to home route
    response = client.get("/")
    assert response.status_code == 302 # verifies it return a 302 redirect status

    print("Home page redirect test passed = 100%") # test passed

# defines a test to check over the login page
def test_login_page():
    print("Testing login page") # test starts
    app = create_app() # creates the app instance
    client = app.test_client() # test client
    # sends a GET request to the login route
    response = client.get("/login")
    assert response.status_code == 200 # verifies it return a 200 OK status
    print("Login page Passed = 100%") # test passed

# defines a test check to handle invalid routes
def test_invalid_page():
    print("Testing invalid route") # test starts
    app = create_app() # creates the app instance
    client = app.test_client() # test client
    # sends a GET request to a non-existent route
    response = client.get("/invalid")
    assert response.status_code == 404 # verifies it return a 404 Not Found status
    print("Invalid page test passed = 100%") # test passed
    
    
    
    
    