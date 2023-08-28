import feedparser
from markdownify import markdownify
from urllib.parse import urljoin
from bs4 import BeautifulSoup
import requests
import time
import os

rss_url = input("Input rss URL:")
c_md = input("Convert to markdown format? \n(y as default) y/n: ")
c_name = input('Convert to Windows friendly filenames?\n(n as default) y/n: ')

sess = requests.Session()

pid=0
while True:
    pid +=1
    # rss_url = 'https://coolshell.cn/feed?paged='+str(pid)

    # cont = True
    # while cont:
    print('Trying...', pid)
    #     # time.sleep(3)
    #     r = sess.get(rss_url)
    #     if r.ok:
    #         cont = False
    #     else:
    #         print(r.status_code, r.headers)


    # data = r.text
    try:
        with open('/home/yzqzss/git/haoel-articles/blogs/rss/feed-'+str(pid)+'.xml', 'r') as f:
            data = f.read()
    except FileNotFoundError:
        print('File not found, exit.')
        break


    feed = feedparser.parse(data)
    items = feed["items"]
    for item in items:
        item_url = item[ "link" ]
        time = item[ "published_parsed" ]
        format_time = str(time.tm_year)+'/'+str(time.tm_mon)+'/'+str(time.tm_mday)+'/ '+str(time.tm_hour)+':'+str(time.tm_min)+':'+str(time.tm_sec)
        title = item[ "title" ]
        # breakpoint()
        commentRss = item[ "wfw_commentrss" ]

        print(f'Pocessing: {title}+{commentRss}')

        # if c_name == 'y':
        #     fileName = str(time.tm_year) + '-' + str(time.tm_mon) + '-' + str(time.tm_mday) + ':' + title + '.html'
        #     fileName = "./output/"+fileName.replace('/', '_').replace('\\', '_').replace(':', '：').replace('*', '×').replace('?', '？').replace('"', '\'\'').replace('<', '[').replace('>', ']').replace('|', 'l')
        # else:
        #     fileName = str(time.tm_year) + '-' + str(time.tm_mon) + '-' + str(time.tm_mday) + ': ' + title + '.html'
        #     fileName = "./output/"+fileName.replace('/', '_')

        # if not os.path.exists("output"):
        #                 os.makedirs("output")

        # f = open(fileName,'w')
        # value = item["content"][0]['value']
        from legacy.boom import get_all
        assert commentRss is not None
        get_all(commentRss)

        # # find all img urls
        # soup = BeautifulSoup(value, 'html.parser')
        # imgs = soup.find_all('img')
        # for img in imgs:
        #     try:
        #         full_url = urljoin(item_url, img['src'])
        #     except KeyError:
        #         print('No src in img tag, skip.')
        #         print(img)
        #         continue
        #     print('Found img: ', full_url)
        #     img_urls.add(full_url)

#         f.write('---\nlayout: post\ntitle: '+title+'\ndate: '+format_time+'\nupdated: '+format_time)
#         f.write('''
# status: publish
# published: true
# type: post
# ---

# ''')
        # if c_md == 'n':
        #     f.write(value)
        # else:
        #     # value = html2text.html2text(value)
        #     # value = markdownify(value)
        #     f.write(value)
        # f.close()
    print('Done! please check out ./output')

# img_urls = list(img_urls)
# img_urls.sort()
# with open('img_urls.txt', 'w') as f:
#     f.write('\n'.join(img_urls)+'\n')
