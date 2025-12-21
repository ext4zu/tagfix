import requests
from PIL import Image
import io

def check_itunes():
    term = "The Dark Side of the Moon Pink Floyd"
    url = f"https://itunes.apple.com/search?term={term}&entity=album&limit=1"
    resp = requests.get(url)
    data = resp.json()
    if data['resultCount'] > 0:
        artwork = data['results'][0]['artworkUrl100']
        print(f"Original Artwork URL: {artwork}")
        
        # Test 1000x1000
        high_res = artwork.replace('100x100bb', '1000x1000bb')
        print(f"High Res URL: {high_res}")
        
        img_resp = requests.get(high_res)
        if img_resp.status_code == 200:
            img = Image.open(io.BytesIO(img_resp.content))
            print(f"High Res Image Size: {img.width}x{img.height}")
            
        # Test 500x500
        med_res = artwork.replace('100x100bb', '500x500bb')
        print(f"Med Res URL: {med_res}")
        
        img_resp = requests.get(med_res)
        if img_resp.status_code == 200:
            img = Image.open(io.BytesIO(img_resp.content))
            print(f"Med Res Image Size: {img.width}x{img.height}")
            
    else:
        print("No results found.")

if __name__ == "__main__":
    check_itunes()
