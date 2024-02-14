import requests
import json
import os

def read_si_data():
    with open(".skyinstaller.json", 'r') as file:
        data = json.load(file)
    return data

def write_si_data(data):
    with open(".skyinstaller.json", 'w') as file:
        json.dump(data, file, indent=2)

def read_installed_mods():
    files = os.listdir("mods")
    mods = []
    for file in files:
        if file.endswith(".jar"):
            mods.append(file)
    return mods

def get_mod_info(url):
    response = requests.get(url)
    release_info = response.json()

    name = release_info["name"]
    assets = release_info["assets"]
    description = release_info["body"]
    version = release_info["tag_name"]
    file_name = None
    download = None

    for asset in assets:
        asset_name = asset["name"]
        download_url = asset["browser_download_url"]
        if asset_name.endswith(".jar"):
            file_name = asset_name
            download = download_url
            break

    return {
        "update_name": name,
        "description": description,
        "version": version,
        "file": file_name,
        "download": download
    }

def download_mod(download_url, file_name):
    response = requests.get(download_url)
    file_path = os.path.join("mods", file_name)

    with open(file_path, 'wb') as f:
        f.write(response.content)

def update_metadata(old_metadata, new_info):
    metadata = read_si_data()
    for mod in metadata["mods"]:
        if mod["name"] == old_metadata["name"]:
            mod["version"] = new_info["version"]
            mod["file_name"] = new_info["file"]
            break

    write_si_data(metadata)


metadata = read_si_data()
mods = read_installed_mods()
download_queue = []
delete_queue = []

for mod in metadata["mods"]:

    # Mods in metadata but not in mods folder
    if mod["file_name"] not in mods:
        print(f"Found missing mod {mod['name']} (not in mods folder). Added to download queue.")
        info = get_mod_info(mod["git"])
        download_queue.append({"old_metadata": mod, "info": info})

    # Mods present in mod folder
    else:
        info = get_mod_info(mod["git"])
        if info["version"] != mod["version"]:
            print(f"Found outdated mod {mod['name']} (version {mod['version']} => {info['version']}). Queued for update")
            delete_queue.append(mod["file_name"])
            download_queue.append({"old_metadata": mod, "info": info})


# Mods in mods folder but not in metadata
for mod in mods:
    if mod not in [x["file_name"] for x in metadata["mods"]] and mod not in [y["file_name"] for y in metadata["ignore"]]:
        print(f"Unrecognised mod {mod}. {'Adding to delete queue due to preferences' if metadata['removeUnknownMods'] else 'You can autoremove these by setting removeUnknownMods to true'}")
        if metadata['removeUnknownMods']:
            delete_queue.append(mod)

print("\n\nDeleting mods:")
for mod in delete_queue:
    print(mod)

print("\nDownloading mods:")
for mod in download_queue:
    print(mod["info"]["file"])
    update_metadata(mod["old_metadata"], mod["info"])
