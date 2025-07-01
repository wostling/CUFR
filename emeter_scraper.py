# ======================
# emeter_scraper.py
# Author: Ashton Dudley
# ======================

# See https://emeter.fsaeonline.com/TeamData.js for API 

import re, requests, urllib.parse, time 
from pathlib import Path
from tqdm import tqdm
from bs4 import BeautifulSoup

API_HOST = "https://emeter-api.fsaeonline.com"
SAVE_ROOT  = Path("data/raw/2025-Energy_Meter").resolve()
SAVE_ROOT.mkdir(exist_ok=True)

s = requests.Session()

def get_team_guid(teamdata_url: str):
    """Returns (competitionID, teamID) tuple from a TeamData.aspx URL)""" 
    qs = urllib.parse.urlparse(teamdata_url).query
    params = urllib.parse.parse_qs(qs)
    return params["CompetitionID"][0], params["TeamID"][0]
    
def teamdata_url_from_car(car_num: int) -> str | None:
    """Finds the team URL for the e-meter from the FSAE results pages"""
    url = f"https://results.fsaeonline.com/MyResults.aspx?carnum={car_num}&tab=notices"
    html = s.get(url, timeout=10).text
    soup = BeautifulSoup(html, "html.parser")
    a = soup.find("a", string=re.compile(r"E-?Meter Data", re.I))
    return a["href"] if a else None

def download_zip(comp_id: str, team_id: str, dest: Path):
    """Call the FSAE API and download the emeter ZIP """
    stub_url = f"{API_HOST}/DownloadCompetitionTeamData/{comp_id}/{team_id}"
    request1 = s.get(stub_url, headers={"Accept" : "*"}, timeout=30)
    request1.raise_for_status()
    zip_url = API_HOST + request1.text.strip('"')
    request2 = s.get(zip_url, stream=True, timeout=60)
    request2.raise_for_status()

    with dest.open("wb") as f, tqdm(total=int(request2.headers.get("content-length",0)),
                                unit="B", unit_scale=True,
                                desc=dest.name) as bar:
        for chunk in request2.iter_content(1<<15):
            f.write(chunk); bar.update(len(chunk))

def main(): 
    # [ ] loop through each cars 
    # [x] get emeter URL
    # [x] get UUID
    # [x] download zip files to disk 

    for car in range(201, 306):
        turl = teamdata_url_from_car(car)
        if not turl:
            continue
        comp_id, team_id = get_team_guid(turl)
        out = SAVE_ROOT / f"car_{car:03d}.zip"
        if out.exists():
            continue
        try: 
            download_zip(comp_id, team_id, out)
            print(f"[{car}] downloaded to {out}")
        except Exception as e:
            print(f"[{car}] failed: {e}")
        
        time.sleep(0.2) 

    print("Done...")

if __name__ == "__main__":
    main()