import os
import glob
import requests

# ================= कॉन्फ़िगरेशन =================
GITHUB_TOKEN = "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"
REPO_NAME = "apk-storage"
TAG_NAME = "v1.0"
RELEASE_NAME = "My Apps Release"
# ===============================================

HEADERS = {
    "Authorization": f"Bearer {GITHUB_TOKEN}",
    "Accept": "application/vnd.github+json"
}

def get_username():
    res = requests.get("https://api.github.com/user", headers=HEADERS)
    if res.status_code == 200:
        return res.json().get("login")
    print("[!] अमान्य GitHub टोकन। कृपया टोकन जांचें।")
    exit(1)

def create_repository(repo_name):
    url = "https://api.github.com/user/repos"
    payload = {"name": repo_name, "private": False, "auto_init": True}
    res = requests.post(url, headers=HEADERS, json=payload)
    if res.status_code == 201:
        print(f"[✔] नई रिपॉजिटरी बनाई गई: {repo_name}")
    elif res.status_code == 422:
        print(f"[*] रिपॉजिटरी '{repo_name}' पहले से मौजूद है।")

def get_or_create_release(username, repo_name, tag_name, release_name):
    url = f"https://api.github.com/repos/{username}/{repo_name}/releases"
    
    # चेक करें कि क्या रिलीज़ पहले से बनी है
    res_check = requests.get(f"{url}/tags/{tag_name}", headers=HEADERS)
    if res_check.status_code == 200:
        print(f"[*] रिलीज़ '{tag_name}' पहले से मौजूद है।")
        return res_check.json().get("upload_url")
    
    # नई रिलीज़ बनाएँ
    payload = {"tag_name": tag_name, "name": release_name, "draft": False, "prerelease": False}
    res = requests.post(url, headers=HEADERS, json=payload)
    if res.status_code == 201:
        print(f"[✔] नई रिलीज़ '{tag_name}' बनाई गई।")
        return res.json().get("upload_url")
    
    print(f"[!] रिलीज़ एरर: {res.text}")
    return None

def upload_apk(upload_url_template, file_path):
    file_name = os.path.basename(file_path)
    upload_url = upload_url_template.split("{")[0] + f"?name={file_name}"
    
    upload_headers = {
        "Authorization": HEADERS["Authorization"],
        "Content-Type": "application/vnd.android.package-archive"
    }

    print(f"[*] '{file_name}' अपलोड हो रहा है...")
    with open(file_path, "rb") as f:
        res = requests.post(upload_url, headers=upload_headers, data=f)

    if res.status_code == 201:
        download_url = res.json().get("browser_download_url")
        print(f"[✔] '{file_name}' अपलोड सफल!")
        return download_url
    elif res.status_code == 422:
        print(f"[!] '{file_name}' पहले से अपलोड है।")
        # अगर फ़ाइल पहले से है, तो उसका सीधा लिंक बना दें
        return None
    else:
        print(f"[!] अपलोड एरर ({file_name}): {res.status_code}")
        return None

def main():
    # 1. जिस फ़ोल्डर में स्क्रिप्ट है, उसी फ़ोल्डर के सभी .apk फ़ाइल ढूँढना
    script_dir = os.path.dirname(os.path.abspath(__file__))
    apk_files = glob.glob(os.path.join(script_dir, "*.apk"))

    if not apk_files:
        print(f"[!] इस फ़ोल्डर में कोई भी .apk फ़ाइल नहीं मिली:\n    {script_dir}")
        return

    print(f"[*] कुल {len(apk_files)} APK फ़ाइलें मिलीं।")
    print("[*] GitHub से कनेक्ट किया जा रहा है...")
    username = get_username()
    print(f"[*] यूज़रनेम: {username}")

    create_repository(REPO_NAME)
    upload_url = get_or_create_release(username, REPO_NAME, TAG_NAME, RELEASE_NAME)

    if not upload_url:
        return

    links = []
    print("\n--- अपलोडिंग शुरू ---")
    for apk_path in apk_files:
        file_name = os.path.basename(apk_path)
        link = upload_apk(upload_url, apk_path)
        if link:
            links.append((file_name, link))
        else:
            # अगर पहले से अपलोडेड थी तो उसका डायरेक्ट लिंक फॉर्मेट तैयार करके दिखाएँ
            fallback_link = f"https://github.com/{username}/{REPO_NAME}/releases/download/{TAG_NAME}/{file_name}"
            links.append((file_name, fallback_link))

    print("\n" + "=" * 65)
    print("सभी APK के डायरेक्ट डाउनलोड लिंक्स:")
    print("=" * 65)
    for name, link in links:
        print(f"• {name}:\n  {link}\n")

if __name__ == "__main__":
    main()
