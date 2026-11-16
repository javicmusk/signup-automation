
import os
import re
import time
import base64

from playwright.sync_api import sync_playwright
from googleapiclient.discovery import build
from google.oauth2.credentials import Credentials
from google.auth.transport.requests import Request



# 1. CONNECT TO GMAIL


SCOPES = ["https://www.googleapis.com/auth/gmail.readonly"]

creds = Credentials.from_authorized_user_file(
    "token.json", SCOPES
)

if creds.expired and creds.refresh_token:
    creds.refresh(Request())

service = build("gmail", "v1", credentials=creds)

OTP_EMAIL_QUERY = (
    'from:no-reply@theauthorizedpartner.com '
    'subject:"Signup Confirm OTP"'
)


def get_otp_message_ids():
    results = service.users().messages().list(
        userId="me",
        q=OTP_EMAIL_QUERY,
        maxResults=10
    ).execute()

    return {
        message["id"]
        for message in results.get("messages", [])
    }


def extract_email_text(payload):
    text = ""

    body = payload.get("body", {})
    data = body.get("data")

    if data:
        decoded = base64.urlsafe_b64decode(
            data + "=" * (-len(data) % 4)
        )
        text += decoded.decode(
            "utf-8",
            errors="ignore"
        )

    for part in payload.get("parts", []):
        text += extract_email_text(part)

    return text


def get_new_otp(old_message_ids, timeout=90):
    print("Waiting for a new OTP email...")

    start_time = time.time()

    while time.time() - start_time < timeout:

        results = service.users().messages().list(
            userId="me",
            q=OTP_EMAIL_QUERY,
            maxResults=10
        ).execute()

        messages = results.get("messages", [])

        for item in messages:
            if item["id"] not in old_message_ids:

                message = service.users().messages().get(
                    userId="me",
                    id=item["id"],
                    format="full"
                ).execute()

                email_text = extract_email_text(
                    message["payload"]
                )

                match = re.search(
                    r"(?:OTP|verification code|code)\D{0,30}(\d{6})",
                    email_text,
                    re.IGNORECASE
                )

                if not match:
                    match = re.search(
                        r"\b\d{6}\b",
                        email_text
                    )

                if match:
                    print("New OTP received and extracted.")
                    return (
                        match.group(1)
                        if match.lastindex
                        else match.group()
                    )

        time.sleep(3)

    raise Exception("Timed out waiting for a new OTP email.")



# 2. START BROWSER


with sync_playwright() as p:

    browser = p.chromium.launch(
        channel="chrome",
        headless=False
    )

    page = browser.new_page()

    page.goto(
        "https://authorized-partner.vercel.app/register"
    )

  
    # 3. TERMS AND CONDITIONS
  

    page.get_by_role("checkbox").check()

    page.get_by_role(
        "button",
        name="Continue"
    ).click()

    page.get_by_placeholder(
        "Enter Your First Name"
    ).wait_for()

    print("Account Setup page opened.")

    
    # 4. ACCOUNT DETAILS
 

    page.get_by_placeholder(
        "Enter Your First Name"
    ).fill("Test")

    page.get_by_placeholder(
        "Enter Your Last Name"
    ).fill("User")

    # a fresh email address
    page.get_by_placeholder(
        "Enter Your Email Address"
    ).fill("tvrittech+qa004@gmail.com")

    password_fields = page.locator(
        "input[type='password']"
    )

    password_fields.nth(0).fill("Test@12345")
    password_fields.nth(1).fill("Test@12345")

    # test phone number
    page.get_by_placeholder(
        "00-00000000"
    ).fill("9801011015")

    print("Account details filled.")

    # Record existing OTP emails BEFORE requesting a new one
    old_otp_ids = get_otp_message_ids()

    page.get_by_role(
        "button",
        name="Next"
    ).click()

    print("Registration details submitted.")

   
    # 5. AUTOMATIC OTP
    

    page.locator(
        "input[maxlength='6']"
    ).wait_for()

    otp_code = get_new_otp(old_otp_ids)

    page.locator(
        "input[maxlength='6']"
    ).fill(otp_code)

    page.get_by_role(
        "button",
        name="Verify Code"
    ).click()

    print("OTP submitted automatically.")

   
    # 6. AGENCY DETAILS
    

    page.get_by_placeholder(
        "Enter Agency Name"
    ).wait_for()

    page.get_by_placeholder(
        "Enter Agency Name"
    ).fill("ABC Education Consultancy")

    page.get_by_placeholder(
        "Enter Your Role in Agency"
    ).fill("Education Consultant")

    page.get_by_placeholder(
        "Enter Your Agency Email Address"
    ).fill("agency@example.com")

    page.get_by_placeholder(
        "Enter Your Agency Website"
    ).fill("www.example.com")

    page.get_by_placeholder(
        "Enter Your Agency Address"
    ).fill("Kathmandu, Nepal")

    page.get_by_text(
        "Select Your Region of Operation"
    ).click()

    page.get_by_text(
        "Nepal",
        exact=True
    ).click()

    page.get_by_text(
        "Canada",
        exact=True
    ).click()

    print("Agency details filled.")

    page.get_by_role(
        "button",
        name="Next"
    ).click()

   
    # 7. PROFESSIONAL EXPERIENCE
   

    page.get_by_placeholder(
        "Enter an approximate number."
    ).wait_for()

    page.locator("select").select_option(
        label="2 years"
    )

    page.get_by_placeholder(
        "Enter an approximate number."
    ).fill("50")

    page.get_by_placeholder(
        "E.g., Undergraduate admissions to Canada."
    ).fill("Undergraduate admissions to Canada")

    page.get_by_placeholder(
        "E.g., 90%"
    ).fill("90")

    services = [
        "Career Counseling",
        "Admission Applications",
        "Visa Processing",
        "Test Prepration"
    ]

    for service in services:
        page.get_by_text(
            service,
            exact=True
        ).click()

    print("Professional Experience filled.")

    page.get_by_role(
        "button",
        name="Next"
    ).click()

   
    # 8. VERIFICATION AND PREFERENCES
    

    page.get_by_placeholder(
        "Enter your registration number"
    ).wait_for()

    page.get_by_placeholder(
        "Enter your registration number"
    ).fill("TEST-REG-2026-001")

    page.locator(
        "button[role='combobox']"
    ).click()

    page.get_by_text(
        "Nepal",
        exact=True
    ).click()

    page.get_by_role(
        "checkbox",
        name="Universities"
    ).click()

    page.get_by_placeholder(
        "E.g., ICEF Certified Education Agent"
    ).fill("Not applicable - test account")

   
    # 9. TEST DOCUMENTS
  

    folder = os.path.join(
        os.path.dirname(__file__),
        "test_documents"
    )

    company_file = os.path.join(
        folder,
        "test_company_registration.txt"
    )

    education_file = os.path.join(
        folder,
        "test_education_certificate.txt"
    )

    if not os.path.exists(company_file):
        raise FileNotFoundError(company_file)

    if not os.path.exists(education_file):
        raise FileNotFoundError(education_file)

    uploads = page.locator(
        "input[type='file']"
    )

    uploads.nth(0).set_input_files(company_file)
    uploads.nth(1).set_input_files(education_file)

    print("Both test documents uploaded.")


    # 10. SUBMIT AND VERIFY
    

    submit_button = page.get_by_role(
        "button",
        name="Submit"
    )

    if not submit_button.is_enabled():
        raise Exception("Submit button is disabled.")

    submit_button.click()

    page.wait_for_timeout(4000)

    print("\nFINAL PAGE RESULT:")
    print(page.locator("body").inner_text()[:3000])

    print("\nAutomation run finished.")

    browser.close()
