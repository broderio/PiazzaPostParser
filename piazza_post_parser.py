from piazza_api import Piazza
from time import sleep
import json
import os

def filter_child_post(raw_post):
    post = {}
    post["history"] = []
    # for hist in raw_post["history"]:
    #     post["history"].append({"subject": hist["subject"], "content": hist["content"]})
    if "history" not in raw_post:
        post["history"].append({"subject": raw_post["subject"], "content": raw_post["subject"]})
    else:
        for hist in raw_post["history"]:
            post["history"].append({"subject": hist["subject"], "content": hist["content"]})
    post["responses"] = []
    for response in raw_post["children"]:
        post["responses"].append(filter_child_post(response))
    return post

def filter_post(raw_post):
    post = {}
    post["nr"] = raw_post["nr"]
    post["tags"] = raw_post["tags"]
    post["status"] = raw_post["status"]
    post["history"] = []
    # If history does not exist, use the subject as both the subject and content for history[0]
    if "history" not in raw_post:
        post["history"].append({"subject": raw_post["subject"], "content": raw_post["subject"]})
    else:
        for hist in raw_post["history"]:
            post["history"].append({"subject": hist["subject"], "content": hist["content"]})

    post["responses"] = []
    for response in raw_post["children"]:
        post["responses"].append(filter_child_post(response))
    return post

def get_post_json():
    if not os.path.exists("raw_posts.json"):
        return {"posts": [], "most_recent": 0, "count": 0}
    with open("raw_posts.json", "r") as f:
        return json.load(f)
    
def filter_raw_json(raw_json):
    filtered_posts_json = {"notes": [], "questions": []}
    for post in raw_json["posts"]:
        # If the post has been deleted or is private, skip it
        if (post["status"] == "deleted" or post["status"] == "private"):
            continue
        if post["type"] == "question":
            filtered_posts_json["questions"].append(filter_post(post))
        elif post["type"] == "note":
            filtered_posts_json["notes"].append(filter_post(post))
    return filtered_posts_json

def main():
    post_json = get_post_json()
    i = post_json["most_recent"] + 1

    p = Piazza()
    p.user_login()

    network_id = input("Enter the network ID (https://piazza.com/class/[THIS ID]/): ")
    course = p.network(network_id)

    print("Getting posts...")
    try:
        while True:
            print(i)
            try:
                post = course.get_post(i)
                post_json["posts"].append(post)
                sleep(0.25)
                i += 1
            except Exception as e:
                error_string = str(e)
                if "cannot be found" in error_string:
                    # Once we reach a post that cannot be found, we assume that
                    # we have reached the end of the posts
                    print("No more posts to get.")
                    break
                elif "Not permitted" in error_string:
                    # Ignore posts that are not permitted
                    i += 1
                    continue
                else:
                    # If we get an error that is not one of the above, print the
                    # error and try again
                    sleep(2)
                    print(e)
                    continue

    except KeyboardInterrupt:
        print("Interrupted. Saving posts...")

    print("Saving posts...")
    post_json["most_recent"] = i - 1
    post_json["count"] = len(post_json["posts"])

    with open("raw_posts.json", "w") as f:
        json.dump(post_json, f, indent=2)
        print("Saved raw posts to raw_posts.json")

    filtered_posts_json = filter_raw_json(post_json)
    with open("filtered_posts.json", "w") as f:
        json.dump(filtered_posts_json, f, indent=2)
        print("Saved filtered posts to filtered_posts.json")

    print("Done!")

if __name__ == "__main__":
    main()