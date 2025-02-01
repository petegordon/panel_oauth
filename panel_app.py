import panel as pn
import requests
import os
from dotenv import load_dotenv  # Load .env variables
load_dotenv()

pn.extension()

FASTAPI_AUTH_URL = os.getenv("FASTAPI_AUTH_URL","http://localhost:8000")

def get_user():
    """Fetch user info from FastAPI OAuth service."""
    try:
        response = requests.get(f"{FASTAPI_AUTH_URL}/user", cookies=pn.state.cookies)
        if response.status_code == 401:
            return None
        return response.json()
    except:
        return None

user = get_user()

# JavaScript-based redirection using a hidden HTML pane
js_redirect = pn.pane.HTML("", width=0, height=0, name="js_redirect")

if not user:
    #pn.state.notifications.error("You need to authenticate to access the app.")

    login_buttons = pn.Column(
        pn.pane.Markdown("## Login with GitHub or Azure"),
        pn.widgets.Button(name="Login with GitHub", button_type="primary", width=200, align="center"), 
        pn.widgets.Button(name="Login with Azure", button_type="primary", width=200, align="center")
    )



    def redirect(provider):
        """Updates the hidden HTML pane to trigger JavaScript redirection."""
        js_redirect.object = f"""
        <script>
            window.location.href = "{FASTAPI_AUTH_URL}/login/{provider}";
        </script>
        """

    def login_github(event):
        redirect("github")

    def login_azure(event):
        redirect("azure")

    login_buttons[1].on_click(login_github)
    login_buttons[2].on_click(login_azure)
    pn.Column(login_buttons, js_redirect).servable()

else:
    logout_button = pn.widgets.Button(name="Logout", button_type="danger", width=200)

    def logout(event):
        print("Logging out...")
#        pn.state.location.href = f"{FASTAPI_AUTH_URL}/logout"
        
        js_redirect.object = f"""
        <script>
            window.location.href = '{FASTAPI_AUTH_URL}/logout';
        </script>
        """
        print("Should have redirected and logged out.")

    logout_button.on_click(logout)

    user_provider = user.get("provider")
    user_info = user.get("info", {})
    user_email = user_info.get("email") or user_info.get("mail") or user_info.get("otherMails", [None])[0] or user_info.get("userPrincipalName") or "[* No email found *]"
    user_name = user_info.get("name", user_info.get("displayName", "[* No name found *]"))

    panel_user = {
        "provider": user_provider,
        "name": user_name,
        "email": user_email
    }
    pn.Column(        
        f"Welcome, <span style='font-weight:800'>{panel_user['name']}</span>!",
        pn.pane.HTML(f"thanks for using <span style='font-weight:800'>{panel_user['provider']}</span>"),
        pn.pane.HTML(f"email: <span style='font-weight:800'>{panel_user['email']}</span>"),
        logout_button,
        js_redirect,
    ).servable()
