"""
Command Line Interface
Simple CLI for testing the Agno orchestration system.
"""

import asyncio
import argparse
from dotenv import load_dotenv

from .agno_orchestrator import AgnoOrchestrator
from .logging_system import get_logger
from .config import get_config


async def main():
    """Main CLI entry point."""
    # Load environment
    load_dotenv()
    
    # Parse arguments
    parser = argparse.ArgumentParser(
        description="Agno Orchestration System CLI",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  python -m src.cli "Tell me about Microsoft 2024 report"
  python -m src.cli "What happened in AI in 2024?" --format markdown
  python -m src.cli "Latest news on climate change" --max-results 10
        """
    )
    
    parser.add_argument(
        "query",
        type=str,
        help="Search query in natural language"
    )
    
    parser.add_argument(
        "--format",
        choices=["structured", "json", "markdown"],
        default="structured",
        help="Output format (default: structured)"
    )
    
    parser.add_argument(
        "--max-results",
        type=int,
        default=5,
        help="Maximum number of results (default: 5)"
    )
    
    parser.add_argument(
        "--stats",
        action="store_true",
        help="Show statistics after execution"
    )
    
    args = parser.parse_args()
    
    # Initialize logger and config
    logger = get_logger()
    config = get_config()
    
    # Validate config
    is_valid, error_msg = config.validate()
    if not is_valid:
        logger.error(f"Configuration error: {error_msg}")
        print(f"\n[ERROR] Configuration error: {error_msg}")
        print("\nPlease check your .env file or environment variables.")
        return
    
    # Initialize orchestrator
    logger.info("Initializing Agno Orchestration System...")
    orchestrator = AgnoOrchestrator()
    
    print("\n" + "=" * 80)
    print("AGNO ORCHESTRATION SYSTEM")
    print("=" * 80)
    print(f"\nQuery: {args.query}")
    print(f"Format: {args.format}")
    print(f"Max Results: {args.max_results}")
    print("\n" + "-" * 80)
    print("Processing...")
    print("-" * 80 + "\n")
    
    # Execute query
    try:
        response = await orchestrator.process_request(
            user_input=args.query,
            max_results=args.max_results
        )
        
        # Format and display response
        formatted_output = orchestrator.format_response(
            response,
            format_type=args.format
        )
        
        print(formatted_output)
        
        # Show statistics if requested
        if args.stats:
            print("\n\n" + "=" * 80)
            print("STATISTICS")
            print("=" * 80)
            stats = orchestrator.get_statistics()
            for key, value in stats.items():
                print(f"{key.replace('_', ' ').title()}: {value}")
        
    except KeyboardInterrupt:
        print("\n\n[WARN] Interrupted by user")
    except Exception as e:
        logger.error(f"CLI execution error: {str(e)}")
        print(f"\n[ERROR] Error: {str(e)}")


if __name__ == "__main__":
    asyncio.run(main())

