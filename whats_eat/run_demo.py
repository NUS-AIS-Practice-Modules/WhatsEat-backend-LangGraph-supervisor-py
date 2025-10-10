"""WhatsEat demo runner"""
import asyncio
import logging
from .supervisor.workflow import create_whatseat_supervisor

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

async def run_demo():
    """Run WhatsEat demo with sample query"""
    
    # Create supervisor
    supervisor = create_whatseat_supervisor()
    
    # Sample query
    query = "Looking for highly rated sushi restaurants in downtown Portland, any price range, for dinner tonight with 4 people"
    
    try:
        # Run supervisor
        logger.info("Starting WhatsEat pipeline with query: %s", query)
        response = await supervisor.ainvoke({"messages": [query]})
        
        # Log results
        state = response.state
        logger.info("Pipeline complete!")
        logger.info("Query spec: %s", state.query_spec)
        if state.user_profile:
            logger.info("User profile: %s", state.user_profile)
        logger.info("Found %d candidates", len(state.candidates or []))
        if state.ranking:
            logger.info("Top recommendations:")
            for item in state.ranking["items"][:3]:
                logger.info("- %s (score: %.2f)", item["name"], item["score"])
                if item.get("why"):
                    logger.info("  Why: %s", ", ".join(item["why"]))
        
        return response
        
    except Exception as e:
        logger.error("Pipeline failed: %s", str(e))
        raise

if __name__ == "__main__":
    asyncio.run(run_demo())