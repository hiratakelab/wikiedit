"""
Meeting Slide Uploader

usage: wikiedit.py (<file>)

options:

"""

from docopt import docopt
from selenium import webdriver
import sys


def signin(path="signin.txt"):
    import os
    if os.path.isfile(path):
        with open(path) as f:
            return f.read()
    else:
        print("wikiの個人ページ作成時に使った情報を教えてください")
        print("入学年？(西暦の下2桁，例：13)")
        g = input()
        print("名字？")
        l = input()
        print("名前？")
        f = input()
        pagename = f"{g}_{f}_{l}"

        with open(path, mode='w') as f:
            f.write(pagename)
            return pagename


class Uploader:
    def __init__(self, args, browser, pagename):
        self.file = args['<file>']
        self.browser = browser
        self.pagename = pagename

        id_, pass_, self.uploadpass = self.load_idpass()
        self.url_top = f"http://{id_}:{pass_}@wiki.hiratakelab.jp/"

    def close(self):
        """
        ウィンドウを閉じる
        """

        print("ウィンドウを閉じますか？[y/n]")
        if input() == 'y':
            import time
            time.sleep(1)
            self.browser.quit()
            exit()
        else:
            pass

    @staticmethod
    def load_idpass():
        """
        wikiログインのID, PASS, ファイルアップロードのPASSを読み込む
        (注意) data.txtをコードと同じ場所に置いてほしい

        :rtype: tuple(String, String, ...)
        """
        try:
            with open('data.txt') as f:
                data = f.read()
            return tuple(data.split('\n'))
        except Exception as e:
            print(e)

    def upload(self):
        """
        ファイルを個人ページにアップロード
        """
        url = f"{self.url_top}?plugin=attach&pcmd=upload&page={self.pagename}"
        self.browser.get(url)

        import pathlib
        path = f"{pathlib.Path(self.file).resolve()}"
        self.browser.find_element_by_name("attach_file").send_keys(path)
        self.browser.find_element_by_name("pass").send_keys(self.uploadpass)
        self.browser.find_element_by_xpath("//input[@type='submit']").click()

        import time
        time.sleep(10)

    def add_newline(self, limsg):
        """
        行を新規に追加

        :param elem_msg: String
        :return: String
        """
        import datetime
        now = datetime.datetime.now()

        idx_new = [i + 2 for i, l in enumerate(limsg) if f"{now.year}年度" in l]

        if not f"{now.month}/{now.day}" in limsg[idx_new[0]]:
            print("今日はミーティングの日ですか？ [y/n]")
            is_replace = True if input() == 'y' else False
            idx_tmp = [i for i, l in enumerate(limsg) if f"テンプレ" in l]

            # テンプレの行が1グループ1つじゃなないとエラー吐く
            for i, (n, t) in enumerate(zip(idx_new, idx_tmp)):
                s = limsg[t + i].replace(\
                    "テンプレ", (f"{now.month}/{now.day}" if is_replace else " "))
                limsg.insert(n + i, s)

        return '\n'.join(limsg), idx_new

    def table_edit(self):
        import os

        url = f"{self.url_top}?cmd=edit&page=meeting_documents"
        self.browser.get(url)
        elem_msg = self.browser.find_element_by_name("msg")

        with open('log.txt', mode='w') as f:
            f.write(elem_msg.text)

        limsg = elem_msg.text.split("\n")
        msg, idx_new = self.add_newline(limsg)

        for i, idxg in enumerate(idx_new):
            for idxr, row in enumerate(limsg[idxg + i - 1].split('|')):
                if self.pagename in row:
                    limember = limsg[idxg + i].split('|')
                    limember[idxr] = \
                        f"&ref({self.pagename}/{os.path.basename(self.file)},,,スライド);"
                    limsg[idxg + i] = '|'.join(limember)
                    break

        print("ちょっと時間かかります...\n")
        elem_msg.clear()
        elem_msg.send_keys('\n'.join(limsg))

        self.browser.find_element_by_name("write").click()


def main(argv):
    uploader = Uploader(docopt(__doc__), webdriver.Firefox(), signin())
    uploader.upload()
    uploader.table_edit()
    uploader.close()


if __name__ == '__main__':
    main(sys.argv)