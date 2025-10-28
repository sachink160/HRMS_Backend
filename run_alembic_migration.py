"""
Alembic Migration Runner for HRMS Backend

This script provides a convenient way to run Alembic migrations for the HRMS backend.
It uses async SQLAlchemy engines and supports all standard Alembic commands.

Usage:
    python run_alembic_migration.py upgrade head      # Apply all migrations
    python run_alembic_migration.py downgrade -1       # Rollback one migration
    python run_alembic_migration.py revision --autogenerate -m "Description"
    python run_alembic_migration.py current            # Show current version
    python run_alembic_migration.py history            # Show migration history
"""

import sys
import os
from pathlib import Path

# Add the Backend directory to the Python path
backend_dir = Path(__file__).parent
sys.path.insert(0, str(backend_dir))

# Import alembic command line
from alembic.config import Config
from alembic import command

def main():
    """Run Alembic commands."""
    # Create Alembic config
    alembic_cfg = Config(str(backend_dir / "alembic.ini"))
    
    # Parse command line arguments (skip script name)
    args = sys.argv[1:] if len(sys.argv) > 1 else ['--help']
    
    # Get the command
    if args[0] in ['upgrade', 'downgrade', 'revision', 'current', 'history', 'stamp', 'merge', 'heads', 'show', 'check']:
        cmd = args[0]
        cmd_args = args[1:]
        
        # Run the appropriate command
        if cmd == 'upgrade':
            command.upgrade(alembic_cfg, *cmd_args)
        elif cmd == 'downgrade':
            command.downgrade(alembic_cfg, *cmd_args)
        elif cmd == 'revision':
            command.revision(alembic_cfg, *cmd_args)
        elif cmd == 'current':
            command.current(alembic_cfg, *cmd_args)
        elif cmd == 'history':
            command.history(alembic_cfg, *cmd_args)
        elif cmd == 'stamp':
            command.stamp(alembic_cfg, *cmd_args)
        elif cmd == 'merge':
            command.merge(alembic_cfg, *cmd_args)
        elif cmd == 'heads':
            command.heads(alembic_cfg, *cmd_args)
        elif cmd == 'show':
            command.show(alembic_cfg, *cmd_args)
        elif cmd == 'check':
            command.check(alembic_cfg, *cmd_args)
    else:
        # Default help
        print(__doc__)
        print("\nAvailable commands:")
        print("  upgrade          Apply migrations")
        print("  downgrade        Rollback migrations")
        print("  revision         Create new migration")
        print("  current          Show current database version")
        print("  history          Show migration history")
        print("  heads            Show migration heads")
        print("  stamp            Mark database with version")
        print("  merge            Merge migration heads")
        print("\nExamples:")
        print("  python run_alembic_migration.py upgrade head")
        print("  python run_alembic_migration.py revision --autogenerate -m 'Add field'")
        print("  python run_alembic_migration.py downgrade -1")
        print("  python run_alembic_migration.py current")

if __name__ == '__main__':
    main()

