import os
import secrets
from dotenv import load_dotenv  # Load .env variables
from fastapi import FastAPI, Request
from authlib.integrations.starlette_client import OAuth
from starlette.middleware.sessions import SessionMiddleware
from starlette.responses import RedirectResponse, JSONResponse
import httpx

# Load environment variables
load_dotenv()

app = FastAPI()
SECRET_KEY = secrets.token_urlsafe(32)
app.add_middleware(SessionMiddleware, secret_key=SECRET_KEY)

PANEL_APP_URL = os.getenv("PANEL_APP_URL", "http://localhost:5006")

providers = {
    "github": {
        "CLIENT_ID": os.getenv("GITHUB_CLIENT_ID"),
        "CLIENT_SECRET": os.getenv("GITHUB_CLIENT_SECRET"),
        "USER_INFO_URL": "https://api.github.com/user",
    },
    "azure": {
        "CLIENT_ID": os.getenv("AZURE_CLIENT_ID"),
        "CLIENT_SECRET": os.getenv("AZURE_CLIENT_SECRET"),
        "TENANT_ID": os.getenv("AZURE_TENANT_ID"),
        "USER_INFO_URL": "https://graph.microsoft.com/v1.0/me?$select=displayName,mail,userPrincipalName,otherMails",
    },
}


oauth = OAuth()
oauth.register(
    name="github",
    client_id=providers["github"]["CLIENT_ID"],
    client_secret=providers["github"]["CLIENT_SECRET"],
    authorize_url="https://github.com/login/oauth/authorize",
    access_token_url="https://github.com/login/oauth/access_token",  # 🔹 Explicitly Set Here
    userinfo_endpoint=providers["github"]["USER_INFO_URL"],
    client_kwargs={"access_token_url": "https://github.com/login/oauth/access_token"}  # 🔹 Manually Forced
)
oauth.register(
    name="azure",
    client_id=providers["azure"]["CLIENT_ID"],
    client_secret=providers["azure"]["CLIENT_SECRET"],
    authorize_url=f"https://login.microsoftonline.com/{os.getenv('AZURE_TENANT_ID')}/oauth2/v2.0/authorize",
    access_token_url=f"https://login.microsoftonline.com/{os.getenv('AZURE_TENANT_ID')}/oauth2/v2.0/token",
    userinfo_endpoint="https://graph.microsoft.com/oidc/userinfo",
    server_metadata_url=f"https://login.microsoftonline.com/{os.getenv('AZURE_TENANT_ID')}/v2.0/.well-known/openid-configuration",
    client_kwargs={"scope": "openid profile email User.Read"},
)


@app.get("/login/{provider}")
async def login(provider: str, request: Request):
    if provider not in ["github", "azure"]:
        return JSONResponse({"error": "Invalid provider"}, status_code=400)

    oauth_client = oauth.create_client(provider)
    redirect_uri = request.url_for("auth_callback", provider=provider)
    return await oauth_client.authorize_redirect(request, redirect_uri)


async def get_user_info(provider, token):
    async with httpx.AsyncClient() as client:
        user_info_response = await client.get(
            providers[provider]["USER_INFO_URL"],
            headers={"Authorization": f"Bearer {token['access_token']}"},
        )
        user_info = user_info_response.json()
    return user_info


@app.get("/auth/callback/{provider}")
async def auth_callback(provider: str, request: Request):
    oauth_client = oauth.create_client(provider)

    # Debugging
    print(f"🔍 Debugging: Token URL for {provider} = {oauth_client.client_kwargs.get('token_url', None)}")

    try:
        token = await oauth_client.authorize_access_token(request)
        if not token:
            return JSONResponse({"error": "Failed to retrieve access token"}, status_code=400)

        user_info = await get_user_info(provider, token)

    except Exception as e:
        import traceback
        traceback.print_exc()  # Log full error traceback in console
        return JSONResponse({"error": f"OAuth callback error: {str(e)}"}, status_code=500)

    request.session["user"] = {"provider": provider, "info": user_info}
    return RedirectResponse(url=PANEL_APP_URL)

@app.get("/user")
async def get_user(request: Request):
    user = request.session.get("user")
    return JSONResponse(user if user else {"error": "Not authenticated"}, status_code=401 if not user else 200)

@app.get("/logout")
async def logout(request: Request):
    request.session.clear()  # Clear session
    return RedirectResponse(url=PANEL_APP_URL)  # Redirect back to the Panel app
