from piazza_api import Piazza
from time import sleep
import json
import os
import argparse

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

def get_post_json(starter_file):
    if not os.path.exists(starter_file):
        return {"posts": [], "most_recent": 0, "count": 0}
    with open(starter_file, "r") as f:
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
    parser = argparse.ArgumentParser(description="Piazza Post Parser")
    parser.add_argument("starter_file", type=str, help="The file to store the raw posts. If the file exists, the script will continue from the most recent post and append to the file.")
    parser.add_argument("--network_id", type=str, help="The network ID of the Piazza class")
    parser.add_argument("--max_posts", type=int, help="The maximum number of posts to get")
    args = parser.parse_args()

    starter_file = args.starter_file
    post_json = get_post_json(starter_file)
    i = post_json["most_recent"] + 1

    p = Piazza()
    p.user_login()

    network_id = ""
    if args.network_id:
        network_id = args.network_id
    else:
        network_id = input("Enter the network ID (https://piazza.com/class/[THIS ID]/): ")
    course = p.network(network_id)

    max_posts = None
    if args.max_posts:
        max_posts = args.max_posts

    print("Getting posts...")
    try:
        while True:
            print(i)
            try:
                post = course.get_post(i)
                post_json["posts"].append(post)
                sleep(0.25)
                i += 1
                if max_posts and i >= max_posts:
                    break
            except Exception as e:
                error_string = str(e)
                print(e)
                if "cannot be found" in error_string or "Not permitted" in error_string:
                    # Ignore posts that cannot be found or are not permitted
                    i += 1
                    continue
                else:
                    # If we get an error that is not one of the above, print the
                    # error and try again
                    sleep(2)
                    continue

    except KeyboardInterrupt:
        print("Interrupted. Saving posts...")

    print("Saving posts...")
    post_json["most_recent"] = i - 1
    post_json["count"] = len(post_json["posts"])

    with open(starter_file, "w") as f:
        json.dump(post_json, f, indent=2)
        print("Saved raw posts to: " + starter_file)

    filtered_posts_json = filter_raw_json(post_json)
    filtered_file = starter_file.split(".")[0] + "_filtered.json"
    with open(filtered_file, "w") as f:
        json.dump(filtered_posts_json, f, indent=2)
        print("Saved filtered posts to: " + filtered_file)

    print("Done!")

if __name__ == "__main__":
    main()