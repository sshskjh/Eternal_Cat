import json
import os
import numpy as np

input_dim = 100058
output_dim = 57229
song_size = 0
song_to_idx = {}
tag_to_idx = {}
idx_to_item = []

PARENT_PATH = os.path.dirname(os.path.dirname(__file__))
data_path = os.path.join(PARENT_PATH, 'data')

with open(os.path.join(data_path, "song_to_idx.json"), 'r', encoding='utf-8') as f1:
    song_to_idx = json.load(f1)
    song_size = len(song_to_idx)
with open(os.path.join(data_path, "tag_to_idx.json"), 'r', encoding='utf-8') as f2:
    tag_to_idx = json.load(f2)
with open(os.path.join(data_path, "idx_to_item.json"), 'r', encoding='utf-8') as f3:
    idx_to_item = json.load(f3)


with open(os.path.join(data_path,"res_song_to_entityidx.json"), 'r', encoding='utf-8') as f3:
    song_to_entityidx = json.load(f3)
with open(os.path.join(data_path,"res_entity_to_idx.json"), 'r', encoding='utf-8') as f3:
    entity_to_idx = json.load(f3)

import model_inference as mi

def add_meta(input_one_hot ,noise_input_song):
    meta = np.zeros(len(entity_to_idx))
    for song in noise_input_song:
        if str(song) not in song_to_entityidx:
            continue
        for idx in song_to_entityidx[str(song)]:
            meta[idx] += 1
    return np.concatenate((input_one_hot , meta))

with open(os.path.join(data_path, "val.json"), "r", encoding = 'utf-8') as f3, open(os.path.join(data_path, "results.json"), "w", encoding = 'utf-8') as f4:
    ans_list = []
    val_list = json.load(f3)
    cnt = 0
    for playlist in val_list:
        cnt+=1
        input_one_hot = np.zeros(output_dim)
        noise_input_song = []
        inf_ans = {}
        for song in playlist["songs"]:
            noise_input_song.append(song)
            if song_to_idx.get(str(song)) != None:
                input_one_hot[song_to_idx[str(song)]] = 1
        for tag in playlist["tags"]:
            if tag_to_idx.get(tag) != None:
                input_one_hot[tag_to_idx[tag]] = 1
        playlist_vec = add_meta(input_one_hot ,noise_input_song)
        inferenced_vec = mi.inference(playlist_vec)
        inferenced_list = [(inferenced_vec[idx], idx) for idx in range(len(inferenced_vec))]
        inferenced_list = sorted(inferenced_list, reverse=True)
        tag_max = 10
        tag_ctr = 0
        song_max = 100
        song_ctr = 0
        loc_song = []
        loc_tag = []
        for val, idx in inferenced_list:
            if idx in range(song_size) and song_ctr < song_max:
                if idx_to_item[idx] in playlist['songs']:
                    continue
                else:
                    loc_song.append(int(idx_to_item[idx]))
                    song_ctr += 1
            if idx in range(song_size, output_dim) and tag_ctr < tag_max:
                if idx_to_item[idx] in playlist['tags']:
                    continue
                else:
                    loc_tag.append(idx_to_item[idx])
                    tag_ctr += 1
            if tag_ctr==tag_max and song_ctr == song_max:
                break
        inf_ans['id'] = playlist['id']
        inf_ans['songs'] = loc_song
        inf_ans['tags'] = loc_tag
        ans_list.append(inf_ans)
        if cnt%1000==0:
            print(cnt)
            print(inf_ans)
    json.dump(ans_list, f4, ensure_ascii=False)

