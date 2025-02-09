import os
import secrets
import tornado.ioloop
import tornado.web
from tornado.httpclient import AsyncHTTPClient
from authlib.integrations.httpx_client import AsyncOAuth2Client
from starlette.middleware.sessions import SessionMiddleware
from starlette.requests import Request
from starlette.responses import RedirectResponse, JSONResponse
from dotenv import load_dotenv
import certifi

# Load environment variables
load_dotenv()

# Secret Key for Session Middleware
SECRET_KEY = secrets.token_urlsafe(32)
PANEL_APP_URL = os.getenv("PANEL_APP_URL", "http://localhost:5006")

# OAuth Provider Configuration
PROVIDERS = {
    "github": {
        "client_id": os.getenv("GITHUB_CLIENT_ID"),
        "client_secret": os.getenv("GITHUB_CLIENT_SECRET"),
        "authorize_url": "https://github.com/login/oauth/authorize",
        "access_token_url": "https://github.com/login/oauth/access_token",
        "userinfo_endpoint": "https://api.github.com/user",
    }, 
    "azure": {
        "client_id": os.getenv("AZURE_CLIENT_ID"),
        "client_secret": os.getenv("AZURE_CLIENT_SECRET"),
        "authorize_url": f"https://login.microsoftonline.com/{os.getenv('AZURE_TENANT_ID')}/oauth2/v2.0/authorize",
        "access_token_url": f"https://login.microsoftonline.com/{os.getenv('AZURE_TENANT_ID')}/oauth2/v2.0/token",
        "userinfo_endpoint": "https://graph.microsoft.com/v1.0/me?$select=displayName,mail,userPrincipalName,otherMails",
        "client_kwargs": {"scope": "openid profile email User.Read"}
    },     
    "google": {
        "client_id": os.getenv("GOOGLE_CLIENT_ID"),
        "client_secret": os.getenv("GOOGLE_CLIENT_SECRET"),
        "authorize_url": "https://accounts.google.com/o/oauth2/auth",
        "access_token_url": "https://oauth2.googleapis.com/token",
        "userinfo_endpoint": "https://www.googleapis.com/oauth2/v1/userinfo",
        "client_kwargs":{
            'scope': 'openid email profile',
            'prompt': 'select_account',  # force to select account
        }        
    },
}


class TornadoOAuthHandler(tornado.web.RequestHandler):
    """Base OAuth handler for login and authentication callbacks"""

    async def get(self, provider):
        if provider not in PROVIDERS:
            self.set_status(400)
            self.write(JSONResponse({"error": "Invalid provider"}))
            return

        provider_data = PROVIDERS[provider]

        # Create OAuth2 client manually
        client = AsyncOAuth2Client(
            client_id=provider_data["client_id"],
            client_secret=provider_data["client_secret"],
            redirect_uri=f"{self.request.protocol}://{self.request.host}/auth/callback/{provider}",
            **provider_data.get("client_kwargs", {}),
        )

        # Redirect to OAuth provider login page
        authorization_url, state = client.create_authorization_url(provider_data["authorize_url"])
        self.set_secure_cookie("oauth_state", state)
        self.redirect(authorization_url)


class OAuthCallbackHandler(tornado.web.RequestHandler):
    """Handles OAuth authentication callback"""

    async def get(self, provider):
        if provider not in PROVIDERS:
            self.set_status(400)
            self.write(JSONResponse({"error": "Invalid provider"}))
            return

        provider_data = PROVIDERS[provider]
        client = AsyncOAuth2Client(
            client_id=provider_data["client_id"],
            client_secret=provider_data["client_secret"],
            redirect_uri=f"{self.request.protocol}://{self.request.host}/auth/callback/{provider}",
            ca_certs=certifi.where()
        )

        # Retrieve authorization response
        authorization_response = self.request.full_url()
        token = await client.fetch_token(
            provider_data["access_token_url"],
            authorization_response=authorization_response,
            
        )

        # Get user info
        user_info = await self.get_user_info(provider, token)

        self.set_secure_cookie("user", tornado.escape.json_encode({"provider": provider, "info": user_info}))
        self.redirect(PANEL_APP_URL)  # Redirect back to home

    async def get_user_info(self, provider, token):
        """Fetches user info from OAuth provider"""
        client = AsyncHTTPClient()
        response = await client.fetch(
            PROVIDERS[provider]["userinfo_endpoint"],
            headers={"Authorization": f"Bearer {token['access_token']}"},
            ca_certs=certifi.where()  # 🔹 Use certifi's CA bundle
        )
        return tornado.escape.json_decode(response.body)


class UserHandler(tornado.web.RequestHandler):
    """Retrieve user info from session"""
    
    def get(self):
        user = self.get_secure_cookie("user")
        if user:
            self.write(tornado.escape.json_decode(user))  # ✅ Return JSON
        else:
            self.set_status(401)  # ✅ Set 401 Unauthorized status
            self.write({"error": "Not authenticated"})  # ✅ Corrected JSON output


class LogoutHandler(tornado.web.RequestHandler):
    """Clears session and logs out the user"""
    
    def get(self):
        self.clear_cookie("user")
        self.redirect(PANEL_APP_URL)


def make_app():
    return tornado.web.Application(
        [
            (r"/", UserHandler),
            (r"/login/(.*)", TornadoOAuthHandler),
            (r"/auth/callback/(.*)", OAuthCallbackHandler),
            (r"/user", UserHandler),
            (r"/logout", LogoutHandler),
        ],
        cookie_secret=SECRET_KEY,
        debug=True,
    )


if __name__ == "__main__":
    app = make_app()
    app.listen(8000)
    print("🚀 Tornado OAuth Server running at http://localhost:8000")
    tornado.ioloop.IOLoop.current().start()
