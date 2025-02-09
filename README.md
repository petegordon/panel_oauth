Making fun Panel apps, this one with multiple OAuth is a bit tricky.

You need to register with Github, Azure, and Google to get ClientID, ClientSecret, and Azure TenantID.

I have updated this to all work within Panel using Tornado endpoints. The examples that include running the authentication server (Tornado or FastAPI) separately are also documented below.

## Register with Providers

[Github App Registration](https://docs.github.com/en/apps/creating-github-apps/registering-a-github-app/registering-a-github-app)

[Microsoft Azure App Registration](https://learn.microsoft.com/en-us/entra/identity-platform/quickstart-register-app?tabs=certificate)

[Google App Registration](https://console.cloud.google.com/auth/clients)

## Run Application that includes Tornado Authentication [endpoints](https://panel.holoviz.org/how_to/server/endpoints.html).
```bash
python auth_panel.py
```


## Run Separate Authentication Server
Run Tornado authentication application server 
```bash
python auth_tornado.py
```

Run FASTAPI authentication application server
```bash
uvicorn auth_fastapi:app --reload --host 0.0.0.0 --port 8000
```

Run Python Panel application that uses separate authentication server
```bash
panel serve panel_app.py --allow-websocket-origin="*"
```

![alt text](images/login.png)

![alt text](images/logout.png)