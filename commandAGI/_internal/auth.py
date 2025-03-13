import json
from pathlib import Path
from typing import Optional, Dict
import typer
import httpx
from datetime import datetime
import webbrowser
from rich.console import Console
from rich.theme import Theme
from ._internal.config import config
from ._internal.models import UserProfile

console = Console(theme=Theme({"info": "cyan", "success": "green", "error": "red"}))

class AuthError(Exception):
    pass

app = typer.Typer(help="Manage authentication and profiles")

async def register(
    email: str = typer.Option(..., prompt=True),
    password: str = typer.Option(..., prompt=True, hide_input=True),
    name: str = typer.Option(..., prompt=True)
):
    """Register a new account"""
    try:
        console.print("🔄 Registering new account...", style="info")
        async with httpx.AsyncClient() as client:
            response = await client.post(
                f"{config.COMMANDAGI_HUB_URL}/auth/register",
                json={"email": email, "password": password, "name": name}
            )
            
            if response.status_code != 200:
                raise AuthError(response.json().get("detail", "Registration failed"))
            
            data = response.json()
            # Create new UserProfile
            profile = UserProfile(
                name=name,
                email=email,
                api_key=data["api_key"]
            )
            config.profiles[email] = profile
            config.active_profile_email = email
            config.save_auth_state()
            
        console.print("✨ Registration successful! Please check your email to verify your account.", style="success")
        console.print(f"👤 Logged in as: {email}", style="success")
    except AuthError as e:
        console.print(f"❌ Registration failed: {str(e)}", style="error")

@app.command()
async def login(
    email: str = typer.Option(..., prompt=True),
    password: str = typer.Option(..., prompt=True, hide_input=True)
):
    """Login with email and password"""
    try:
        console.print("🔄 Logging in...", style="info")
        async with httpx.AsyncClient() as client:
            # First get the bearer token
            response = await client.post(
                f"{config.COMMANDAGI_HUB_URL}/auth/login",
                json={"email": email, "password": password}
            )
            
            if response.status_code != 200:
                raise AuthError(response.json().get("detail", "Login failed"))
            
            bearer_token = response.json()["access_token"]

            # Use bearer token to get API key
            response = await client.post(
                f"{config.COMMANDAGI_HUB_URL}/api/auth/get-api-key",
                headers={"Authorization": f"Bearer {bearer_token}"}
            )

            if response.status_code != 200:
                raise AuthError(response.json().get("detail", "Failed to get API key"))

            data = response.json()
            api_key = data["api_key"]
            
            # Create new UserProfile
            profile = UserProfile(
                email=email,
                api_key=api_key
            )
            config.profiles[api_key] = profile  # Now indexed by API key
            config.active_api_key = api_key
            config.save_auth_state()
            
        console.print(f"✅ Logged in successfully as: {email}", style="success")
    except AuthError as e:
        console.print(f"❌ Login failed: {str(e)}", style="error")

@app.command()
async def status():
    """Show current auth status"""
    if not config.active_api_key:
        console.print("ℹ️ No active profile", style="info")
        return

    try:
        console.print("🔄 Fetching user info...", style="info")
        async with httpx.AsyncClient() as client:
            response = await client.get(
                f"{config.COMMANDAGI_HUB_URL}/auth/me",
                headers={"X-API-Key": config.active_api_key}
            )
            
            if response.status_code != 200:
                raise AuthError(response.json().get("detail", "Failed to get user info"))

        current_profile = config.current_profile
        if current_profile:
            console.print(f"👤 Logged in as: {current_profile.email}", style="success")
        
        console.print("\n📋 Available profiles:", style="info")
        for api_key, profile in config.profiles.items():
            active = "🟢" if api_key == config.active_api_key else "⚪"
            console.print(f"{active} {profile.email}")
    except AuthError as e:
        console.print(f"❌ Error getting status: {str(e)}", style="error")

@app.command()
def switch(
    api_key: Optional[str] = typer.Argument(None, help="API key to switch to (cycles to next profile if not specified)", envvar="COMMANDAGI_API_KEY")
):
    """Switch to a different profile"""
    try:
        if not config.profiles:
            raise AuthError("No profiles available")

        if api_key is None:
            # Get list of API keys and find current index
            keys = list(config.profiles.keys())
            current_idx = keys.index(config.active_api_key) if config.active_api_key in keys else -1
            # Get next key (wrap around to start if at end)
            next_idx = (current_idx + 1) % len(keys)
            api_key = keys[next_idx]

        if api_key not in config.profiles:
            raise AuthError(f"Profile with API key '{api_key}' not found")
            
        config.active_api_key = api_key
        config.save_auth_state()
        console.print(f"🔄 Switched to profile: {config.current_profile.email}", style="success")
    except AuthError as e:
        console.print(str(e), style="error")

@app.command()
def logout(
    api_key: Optional[str] = typer.Option(None, "--api-key", "-k", help="API key to logout from (defaults to active profile)")
):
    """Logout from a profile"""
    try:
        if api_key is None:
            api_key = config.active_api_key

        if api_key in config.profiles:
            email = config.profiles[api_key].email
            del config.profiles[api_key]
            if config.active_api_key == api_key:
                config.active_api_key = next(iter(config.profiles.keys())) if config.profiles else None
            config.save_auth_state()
            console.print(f"👋 Logged out successfully from profile: {email}", style="success")
        else:
            raise AuthError(f"Profile with API key '{api_key}' not found")
    except AuthError as e:
        console.print(str(e), style="error")

if __name__ == "__main__":
    app()
