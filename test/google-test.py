import requests, sys, webbrowser, bs4

res= requests.get('https://google.com/search?q=' + "".join(sys.argv[1:]))
res.raise_for_status()

soup = bs4.BeautifulSoup(res.text, "html.parser")
linkElements = soup.select(".r a")
linksToOpen = min(5, len(linkElements))
print(linksToOpen)
print(soup)
for i in range(linksToOpen):
    print(linkElements[i].get('href'))