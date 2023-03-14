# 一个虚假的dbagent，用的是json
import json
import os


class GoddessDBAgent:
    def __init__(self, path):
        self.path = path

        # create if not exist
        if not os.path.exists(self.path):
            with open(self.path, 'w') as f:
                json.dump({}, f)

    def leave_channel(self, channel_id, user_id):
        with open(self.path, 'r') as f:
            data = json.load(f)
        data["user_list"][channel_id].remove(user_id)
        # write
        with open(self.path, 'w') as f:
            json.dump(data, f)

    def join_channel(self, channel_id, user_id):
        with open(self.path, 'r') as f:
            data = json.load(f)
        if not channel_id in data:
            data["user_list"][channel_id] = []
        data["user_list"][channel_id].append(user_id)
        # write
        with open(self.path, 'w') as f:
            json.dump(data, f)

    def get_channel_user_list(self, channel_id):
        with open(self.path, 'r') as f:
            data = json.load(f)
        if not ("user_list" in data and channel_id in data["user_list"]):
            return []
        return data["user_list"][channel_id]

    def init_user_id_list(self, channel_id, user_ids):
        with open(self.path, 'r') as f:
            data = json.load(f)
        data["user_list"] = {}
        data["user_list"][channel_id] = user_ids or []
        with open(self.path, 'w') as f:
            json.dump(data, f)

    def init_whistle(self, channel_id):
        with open(self.path, 'r') as f:
            data = json.load(f)
        data["whistle"] = {}
        data["whistle"][channel_id] = []
        with open(self.path, 'w') as f:
            json.dump(data, f)

    def add_whistle_msg(self, channel_id, msg, recipients):
        with open(self.path, 'r') as f:
            data = json.load(f)
        data["whistle"][channel_id].append({msg, recipients})
        with open(self.path, 'w') as f:
            json.dump(data, f)

    def get_whistle_recipients(self, channel_id, msg):
        with open(self.path, 'r') as f:
            data = json.load(f)
        if not ("whistle" in data and channel_id in data["whistle"] and msg in data["whistle"][channel_id]):
            return []
        return data["whistle"][channel_id][msg]
