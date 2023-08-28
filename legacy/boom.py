import requests
import os
sess = requests.Session()


def get_all(rss_url_in: str):
    rss_url_in = rss_url_in.rstrip('/')
    pid=0
    while pid != 1:
        pid +=1
        file_name_perf = rss_url_in.lstrip('https://').replace('/', '_')
        filename = f'data/feed-{file_name_perf}-'+str(pid)+'.xml'
        if os.path.exists(filename):
            if filename == 'feed-coolshell.cn_articles_22422.html_feed-1.xml':
                print('Haha')
                break

            print('File exists, skip.')
            continue
        # rss_url = 'https://coolshell.cn/feed?paged='+str(pid)
        rss_url = f'{rss_url_in}?paged='+str(pid)
        print(rss_url)

        cont = True
        while cont:
            print('Trying...', pid)
            # time.sleep(3)
            r = sess.get(rss_url)
            if r.ok:
                cont = False
            else:
                if r.status_code == 404:
                    print('404, exit.')
                    break
                print(r.status_code, r.headers)


        if r.status_code == 404:
            break


        data = r.text
        with open(filename, 'w') as f:
            f.write(data)

# get_all('https://coolshell.cn/comments/feed')