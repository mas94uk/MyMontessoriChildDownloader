#!/usr/bin/python3
import datetime
import lxml.html as lh
import getpass
import os
import pathlib
import shutil
import sys
import requests
import webbrowser

baseurl = 'https://www.mymontessorichild.com'

# Get username and password
if len(sys.argv) > 1:
    username = sys.argv[1]
else:
    username = input(f"Enter username for {baseurl}/parents: ")

if len(sys.argv) > 2:
    password = sys.argv[2]
else:
    password = getpass.getpass(f"Enter password for {username} at {baseurl}/parents: ")

# Log in
user = {'redirect':'view', 'tz':'', 'un':username, 'pw':password, 'login':'LOG+IN'}
session = requests.Session()
response = session.post(f"{baseurl}/parents/index.php?action=login", data=user)
if response.status_code != 200:
    print(f"Unable to login: response {response.status_code}")
    exit(-1)
# A wrong password still returns a 200 status code, but takes us to the wrong page.
body = response.text
if "<title>My Montessori Child (for Parents)</title>" not in body:
    print(f"Failed to login. Wrong username/password?")
    exit(-1)

# Create download directory
now = datetime.datetime.now()
dt_string = now.strftime("%Y%m%d_%H%M%S")
obs_dir = f"Observations_{dt_string}"
os.mkdir(obs_dir)
print(f"Downloading observations to {obs_dir}")

# Get the full set of observations, which is an HTML body
response = session.get(f"{baseurl}/parents/data.php?mode=history&data=observations")
body = response.text
with open(os.path.join(obs_dir, "observations_original.html"), "w") as f:
    f.write(body)

# Get all the images in the page
root = lh.fromstring(body)

images = root.xpath('''//img''')
print(f"Downloading {len(images)} images")
for image in images:
    # Get the src url
    src = image.xpath("""@src""")[0]

    # The src will be something like /parents/image.php?diary=16100190
    # Get just the number at the end
    number = src.split("=")[1]

    # Create a filename which doesn't include special characters
    filename = f"photo_id_{number}"

    # Get a higher res version of the image -- the one given on the MMC site under 'Donwload photo'
    photo_url = f"{baseurl}/parents/data.php?mode=photo&id={number}"
    image = session.get(f"{photo_url}")
    with open(os.path.join(obs_dir, filename), "wb") as f:
        f.write(image.content)

    # Rewrite the src url to just be non-special filename
    # (There's probably an elegant way to do this involving lxml, but this will do.)
    body = body.replace(src, filename)

# Save a full html, in which all images should resolve to local files
html = f"""<!doctype html>
<html>
<head>
<title>My Monessori Child Observations</title>
<meta name="description" content="My Monessori Child Observations">
<link rel="stylesheet" href="style.css">
</head>
<body>
{body}
</body>
</html>"""
output_html_file = os.path.join(obs_dir, "observations.html")
with open(output_html_file, "w") as f:
    f.write(html)

# Copy the stylesheet to the download directory
scriptdir = os.path.dirname(os.path.realpath(__file__))
stylesheet = os.path.join(scriptdir, "style.css")
shutil.copy(stylesheet, obs_dir)

# Open the result in the system browser
url = pathlib.Path(os.path.realpath(output_html_file)).as_uri()
webbrowser.open(url=url, new=0, autoraise=True)
