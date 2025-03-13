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
                token=data["access_token"]
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
            response = await client.post(
                f"{config.COMMANDAGI_HUB_URL}/auth/login",
                json={"email": email, "password": password}
            )
            
            if response.status_code != 200:
                raise AuthError(response.json().get("detail", "Login failed"))
            
            data = response.json()
            # Create new UserProfile
            profile = UserProfile(
                email=email,
                token=data["access_token"]
            )
            config.profiles[email] = profile
            config.active_profile_email = email
            config.save_auth_state()
            
        console.print(f"✅ Logged in successfully as: {email}", style="success")
    except AuthError as e:
        console.print(f"❌ Login failed: {str(e)}", style="error")

@app.command()
async def status():
    """Show current auth status"""
    if not config.active_profile_email:
        console.print("ℹ️ No active profile", style="info")
        return

    try:
        console.print("🔄 Fetching user info...", style="info")
        # Get current user info
        token = config.current_token
        async with httpx.AsyncClient() as client:
            response = await client.get(
                f"{config.COMMANDAGI_HUB_URL}/auth/me",
                headers={"Authorization": f"Bearer {token}"}
            )
            
            if response.status_code != 200:
                raise AuthError(response.json().get("detail", "Failed to get user info"))

        console.print(f"👤 Logged in as: {config.active_profile_email}", style="success")
        console.print("\n📋 Available profiles:", style="info")
        for email, profile in config.profiles.items():
            active = "🟢" if email == config.active_profile_email else "⚪"
            console.print(f"{active} {email}")
    except AuthError as e:
        console.print(f"❌ Error getting status: {str(e)}", style="error")

@app.command()
def switch(
    profile: Optional[str] = typer.Argument(None, help="Profile to switch to (cycles to next profile if not specified)")
):
    """Switch to a different profile"""
    try:
        if not config.profiles:
            raise AuthError("No profiles available")

        if profile is None:
            # Get list of profiles and find current index
            profiles = list(config.profiles.keys())
            current_idx = profiles.index(config.active_profile_email) if config.active_profile_email in profiles else -1
            # Get next profile (wrap around to start if at end)
            next_idx = (current_idx + 1) % len(profiles)
            profile = profiles[next_idx]

        if profile not in config.profiles:
            raise AuthError(f"Profile '{profile}' not found")
            
        config.active_profile_email = profile
        config.save_auth_state()
        console.print(f"🔄 Switched to profile: {profile}", style="success")
    except AuthError as e:
        console.print(str(e), style="error")

@app.command()
def logout(
    profile: Optional[str] = typer.Option(None, "--profile", "-p", help="Profile to logout from (defaults to active profile)")
):
    """Logout from a profile"""
    try:
        if profile is None:
            profile = config.active_profile_email

        if profile in config.profiles:
            del config.profiles[profile]
            if config.active_profile_email == profile:
                config.active_profile_email = next(iter(config.profiles.keys())) if config.profiles else None
            config.save_auth_state()
            console.print(f"👋 Logged out successfully from profile: {profile}", style="success")
        else:
            raise AuthError(f"Profile '{profile}' not found")
    except AuthError as e:
        console.print(str(e), style="error")

if __name__ == "__main__":
    app()
