import panel as pn
import tornado
import requests
import os
import json
from dotenv import load_dotenv  # Load .env variables
load_dotenv()

pn.extension()

import auth_tornado


PANEL_APP_URL = os.getenv("PANEL_APP_URL", "http://localhost:5006")

# Use `pn.state.onload` to delay execution until Panel is fully loaded
def app_loaded():
    print("App Loaded...")

pn.state.onload(app_loaded)  # Ensure API is called only after Panel is loaded


class PanelApp():

    

    def get_user(self):        
        """Fetch user info from FastAPI OAuth service."""
        try:

            print("Getting user...")
            #urlparse(pn.state.location.href)._replace(path='', query='').geturl()
#            self.user = auth_tornado.UserHandler.get_user()
            #base_url = pn.state.location.href.rsplit("/", 1)[0]
#            if pn.state.location is None:
#                return None

            response = requests.get(f"{PANEL_APP_URL}/user", cookies=pn.state.cookies)
            print("Response Status Code: "+response.status_code)
#            print("Response: "+response.json())

#            if response.status_code == 401:
#                print("User not found. "+response.status_code)
#                return None
#            return response.json()
        except Exception as e:
            print("Error fetching user.")
            print(e)
            return None
        
    def redirect(self, provider):
        """Updates the hidden HTML pane to trigger JavaScript redirection."""
        self.js_redirect.object = f"""
        <script>
            window.location.href = "/login/{provider}";
        </script>
        """

    def login_github(self, event):
        self.redirect("github")

    def login_azure(self, event):
        self.redirect("azure")

    def login_google(self, event):
        self.redirect("google")
        
    def logout(self, event):
        print("Logging out...")
#        pn.state.location.href = f"{FASTAPI_AUTH_URL}/logout"
        
        self.js_redirect.object = f"""
        <script>
            window.location.href = '/logout';
        </script>
        """
        print("Should have redirected and logged out.")
        
    def __init__(self):
        # JavaScript-based redirection using a hidden HTML pane
        self.js_redirect = pn.pane.HTML("", width=0, height=0, name="js_redirect")        
        self.user = None

    def get_layout(self):

       # self.user = self.get_user()
        print("User:")
        print(self.user)
        print(pn.state.user)
        if pn.state.cookies.get("user") is not None:
            #user_cookie = pn.state.cookies.get("user")
            #self.user = tornado.escape.json_decode(user_cookie) #self.get_user()
            #self.user = self.get_user()
            print("User cookie found.")
            if isinstance(pn.state.user, str):
                self.user = json.loads(pn.state.user)

        if not pn.state.user:
            #pn.state.notifications.error("You need to authenticate to access the app.")

            login_buttons = pn.Column(
                pn.pane.Markdown("## Login with GitHub or Azure"),
                pn.widgets.Button(name="Login with GitHub", button_type="primary", width=200, align="center"), 
                pn.widgets.Button(name="Login with Azure", button_type="primary", width=200, align="center"),
                pn.widgets.Button(name="Login with Google", button_type="primary", width=200, align="center")
            )

            login_buttons[1].on_click(self.login_github)
            login_buttons[2].on_click(self.login_azure)
            login_buttons[3].on_click(self.login_google)
            layout = pn.Column(login_buttons, self.js_redirect)

        else:
            logout_button = pn.widgets.Button(name="Logout", button_type="danger", width=200)

            logout_button.on_click(self.logout)

            user_provider = self.user.get("provider")
            user_info = self.user.get("info", {})
            user_email = user_info.get("email") or user_info.get("mail") or user_info.get("otherMails", [None])[0] or user_info.get("userPrincipalName") or "[* No email found *]"
            user_name = user_info.get("name", user_info.get("displayName", "[* No name found *]"))

            panel_user = {
                "provider": user_provider,
                "name": user_name,
                "email": user_email
            }
            layout = pn.Column(        
                f"Welcome, <span style='font-weight:800'>{panel_user['name']}</span>!",
                pn.pane.HTML(f"thanks for using <span style='font-weight:800'>{panel_user['provider']}</span>"),
                pn.pane.HTML(f"email: <span style='font-weight:800'>{panel_user['email']}</span>"),
                logout_button,
                self.js_redirect,
            )
        return layout

def get_app():
    print("Getting app...")
    app = PanelApp()
    return app.get_layout()

ROUTES = auth_tornado.get_routes()
print(ROUTES)
pn.serve({"": get_app, "panel_app": get_app}, port=8000, allow_websocket_origin=["*"], extra_patterns=ROUTES)