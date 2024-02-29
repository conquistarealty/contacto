def test_hello_world_sb(sb):
    """Just test if SeleniumBase can work on hello world example from docs."""
    sb.open("https://seleniumbase.io/realworld/login")
    sb.type("#username", "demo_user")
    sb.type("#password", "secret_pass")
    sb.enter_mfa_code("#totpcode", "GAXG2MTEOR3DMMDG")  # 6-digit
    sb.assert_element("img#image1")
    sb.assert_exact_text("Welcome!", "h1")
    sb.click('a:contains("This Page")')
    sb.save_screenshot_to_logs()
