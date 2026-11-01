import sys
import os
import requests

sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..')))

from sqlmodel import Session, select
from app.core.database import engine
from app.models.vk_bot_connection import VkBotConnection

def check():
    with Session(engine) as session:
        connections = session.exec(select(VkBotConnection)).all()
        user_token = None
        for conn in connections:
            if conn.vk_user_token:
                user_token = conn.vk_user_token
                print(f"Found user token in connection: {conn.name}")
                break
                
        if not user_token:
            print("No vk_user_token found in any connection. Trying with bot_token just in case...")
            if connections:
                user_token = connections[0].vk_bot_token
            else:
                print("No connections at all")
                return

        # Получаем последние 5 постов из группы 186688777
        group_id = -186688777
        
        url_posts = "https://api.vk.com/method/wall.get"
        params_posts = {
            "owner_id": group_id,
            "count": 5,
            "access_token": user_token,
            "v": "5.131"
        }
        
        res = requests.get(url_posts, params=params_posts).json()
        if "error" in res:
            print(f"Error wall.get: {res['error']}")
            return
            
        posts = res.get("response", {}).get("items", [])
        print(f"Found {len(posts)} posts. Fetching comments...")
        
        for post in posts:
            post_id = post["id"]
            url_comments = "https://api.vk.com/method/wall.getComments"
            params_comments = {
                "owner_id": group_id,
                "post_id": post_id,
                "sort": "asc",
                "count": 10,
                "access_token": user_token,
                "v": "5.131"
            }
            res_c = requests.get(url_comments, params=params_comments).json()
            comments = res_c.get("response", {}).get("items", [])
            first_comment = "No comments from group"
            for comment in comments:
                # Группа сама себе комментирует, значит author_id == group_id
                if comment.get("from_id") == group_id:
                    first_comment = comment.get("text")
                    break
            print(f"Post {post_id}: '{post.get('text')[:30]}...' -> First comment: '{first_comment}'")

if __name__ == "__main__":
    check()
