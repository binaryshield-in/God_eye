"""
Reddit Data Collector
Note: Requires PRAW configuration
"""

import os
import praw
import logging
import asyncio
import os
from dotenv import load_dotenv


logger = logging.getLogger('GodEye')

load_dotenv()  # load .env variables

async def collect(query: str, session, query_type: str) -> dict:
    """Collect Reddit data using PRAW"""
    
    try:
        # Initialize Reddit instance
        reddit = praw.Reddit(
            client_id=os.getenv('REDDIT_CLIENT_ID'),
            client_secret=os.getenv('REDDIT_CLIENT_SECRET'),
            user_agent="GodEye OSINT Tool v1.0"
        )
        
        results = {}
        
        if query_type == 'username':
            # Get user information
            try:
                user = reddit.redditor(query)
                results['user'] = {
                    "name": user.name,
                    "created_utc": user.created_utc,
                    "comment_karma": user.comment_karma,
                    "link_karma": user.link_karma,
                    "is_mod": user.is_mod,
                    "has_verified_email": user.has_verified_email
                }
                
                # Get recent submissions
                submissions = []
                for submission in user.submissions.new(limit=5):
                    submissions.append({
                        "title": submission.title,
                        "subreddit": str(submission.subreddit),
                        "score": submission.score,
                        "created_utc": submission.created_utc,
                        "url": submission.url
                    })
                results['submissions'] = submissions
                
            except Exception as e:
                results['user_error'] = str(e)
        
        else:
            # Search Reddit
            submissions = []
            for submission in reddit.subreddit("all").search(query, limit=10):
                submissions.append({
                    "title": submission.title,
                    "subreddit": str(submission.subreddit),
                    "score": submission.score,
                    "created_utc": submission.created_utc,
                    "url": submission.url,
                    "author": str(submission.author) if submission.author else "[deleted]"
                })
            results['search_results'] = submissions
        
        return {
            "source": "Reddit",
            "data": results
        }
        
    except Exception as e:
        logger.error(f"Reddit collection failed: {str(e)}")
        return {
            "source": "Reddit",
            "data": None,
            "error": str(e)
        }