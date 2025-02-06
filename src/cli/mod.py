import argparse
from typing import Optional
import asyncio
from src.jobs import migrate, cleanup_downloads, logout_user, token_cleanup
from src.config import AppData

def parse_args() -> argparse.Namespace:
    # Create the top-level argument parser
    parser = argparse.ArgumentParser(
        description="CLI for running internal jobs",
        prog="app",  # Change as needed
        formatter_class=argparse.ArgumentDefaultsHelpFormatter
    )
    
    # Subcommands setup
    subparsers = parser.add_subparsers(dest="command")
    
    job_parser = subparsers.add_parser("job", help="Run an internal job")
    job_subparsers = job_parser.add_subparsers(dest="job_command")
    
    # Cleanup downloads command
    job_subparsers.add_parser("cleanup_downloads", help="Cleans up mod_downloads from more than 30 days ago")
    
    # Cleanup tokens command
    job_subparsers.add_parser("cleanup_tokens", help="Cleans up auth and refresh tokens that are expired")
    
    # Logout developer command
    logout_parser = job_subparsers.add_parser("logout_developer", help="Emergency logout for a developer")
    logout_parser.add_argument("username", type=str, help="Username of the developer")
    
    # Migrate command
    job_subparsers.add_parser("migrate", help="Runs migrations")
    
    return parser.parse_args()

async def maybe_cli(data: AppData) -> bool:
    # Parse command-line arguments
    args = parse_args()

    if args.command == "job":
        if args.job_command == "migrate":
            # Run the migration job
            async with data.db().acquire() as conn:
                await migrate(conn)
            return True

        elif args.job_command == "cleanup_downloads":
            # Run the cleanup downloads job
            async with data.db().acquire() as conn:
                await cleanup_downloads(conn)
            return True

        elif args.job_command == "logout_developer":
            # Run the logout developer job
            if args.username:
                async with data.db().acquire() as conn:
                    await logout_user(args.username, conn)
            return True

        elif args.job_command == "cleanup_tokens":
            # Run the token cleanup job
            async with data.db().acquire() as conn:
                await token_cleanup(conn)
            return True

    return False
