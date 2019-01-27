import json
import os
import sys
from random import randint
from pprint import pprint

import MeCab as M
import requests
from requests_oauthlib import OAuth1Session

ACCESS_TOKEN = None
ACCESS_TOKEN_SECRET = None
CONSUMER_KEY = None
CONSUMER_KEY_SECRET = None
USER_NAME = None


def main():
    get_environ()
    tweets = get_tweet()
    chain_block = create_chain_block(tweets)
    sentences = generate_sentences(chain_block)
    sentence = choose_sentence(sentences)
    fmt_sentence = format_sentence(sentence)
    print(fmt_sentence)
    tweet(fmt_sentence)


def get_tweet():
    tweets = []
    _id = 0

    req = access_twitter_api()

    if req.status_code == 200:
        timeline = json.loads(req.text)
        for tweet in timeline:
            tw = ''
            st = str(tweet['text'])
            user = str(tweet['user']['screen_name'])

            if(st.startswith('@')):
                # @リプライは除外する
                continue
            if(st.startswith('RT @')):
                # リツイートは除外する
                continue
            if 'http' in st:
                #URL付きツイートは外部サービス感が出るから除外
                continue
            if(user == USER_NAME):
                # 自分のツイートから学習するとつまらない
                continue

            for w in st.split():
                if '@' in w:
                    # ツイート途中の@ユーザー名は除外する
                    break 
                if '#' in w:
                    # ハッシュタグ以降は取り入れない
                    break
                tw += ' ' + w
            
            tw = tw.strip()
            if len(tw) > 0:
                tweets.append((tw, _id))
                _id += 1    

    else:
        print('E: Could not get home timeline at error ' + str(req.status_code))

    return tweets

def create_chain_block(tweets):
    # MeCabのモードをスペース区切りに設定する
    m = M.Tagger('-Owakati')
    chain_block = []

    for tweet in tweets:
        words = str(m.parse(tweet[0])).split()

        # 文頭，文末を明示する
        words.insert(0, '__BEGIN__')
        words.insert(len(words), '__END__')

        _id = tweet[1]

        for i in range(len(words) - 2):
            chain_block.append([words[i], words[i + 1], words[i + 2], _id])

    return chain_block


def generate_sentences(chain_block):
    sentences = []

    # 文頭となりえる要素を抽出
    heads = [b for b in chain_block if b[0] == '__BEGIN__']

    for head in heads:
        sentence = []
        blocks = chain_block
        sentence.append(head)
        while True:
            # 生成文の末尾が先頭に来るような要素を見つけて配列にする
            block_available = [b for b in chain_block if b[0]
                            == sentence[len(sentence) - 1][2]]
            if len(block_available) == 0:
                break

            # その中からランダムに文末にくっつける
            block = block_available[randint(0, len(block_available) - 1)]
            sentence.append(block)

            blocks.remove(block)
        
        sentences.append(sentence)

    return sentences

def choose_sentence(sentences):
    # 選ばれる候補
    tmp = []

    for st in sentences:
        # 何回1つのツイートが連続して連結されたか
        cost = 0
        for i in range(len(st) - 1):
            if(st[i][3] == st[i + 1][3]):
                cost += 1
        
        # 左辺==1のとき、ツイートがそのまま吐き出されるので除く
        # オリジナリティーが欲しいので2まで除いてやる
        if (len(st) - cost > 2):
            tmp.append(st)
    
    idx = randint(0,len(tmp))

    sentence = tmp[idx]

    return sentence


def format_sentence(sentence):
    fmt_sentence = ''

    for block in sentence:
        for word in block[1:3]:
            if(word != '__BEGIN__'):
                # ハッシュタグを生かす
                if(word.startswith('#')):
                    fmt_sentence += ' '
                fmt_sentence += word

    return fmt_sentence


def tweet(sentence):
    twitter = OAuth1Session(CONSUMER_KEY, CONSUMER_KEY_SECRET,
                            ACCESS_TOKEN, ACCESS_TOKEN_SECRET)

    url = 'https://api.twitter.com/1.1/statuses/update.json'
    params = {'status': sentence}

    res = twitter.post(url, params=params)

    if res.status_code == 200:
        print('success!!')
    else:
        print('E: Tweet failed at error: ' + str(res.status_code))


def access_twitter_api():
    twitter = OAuth1Session(CONSUMER_KEY, CONSUMER_KEY_SECRET,
                            ACCESS_TOKEN, ACCESS_TOKEN_SECRET)

    url = "https://api.twitter.com/1.1/statuses/home_timeline.json"
    params = {'count': 200}

    req = twitter.get(url, params=params)
    return req


def get_environ():
    global ACCESS_TOKEN
    global ACCESS_TOKEN_SECRET
    global CONSUMER_KEY
    global CONSUMER_KEY_SECRET
    global USER_NAME

    ACCESS_TOKEN = os.getenv('ACCESS_TOKEN', default=None)
    ACCESS_TOKEN_SECRET = os.getenv('ACCESS_TOKEN_SECRET', default=None)
    CONSUMER_KEY = os.getenv('CONSUMER_KEY', default=None)
    CONSUMER_KEY_SECRET = os.getenv('CONSUMER_KEY_SECRET', default=None)
    USER_NAME = os.getenv('TWITTER_USER_NAME', default=None)

    for env in [ACCESS_TOKEN, ACCESS_TOKEN_SECRET, CONSUMER_KEY, CONSUMER_KEY_SECRET, USER_NAME]:
        if env is None:
            print('E: Environment value is not set.')
            sys.exit(1)


if __name__ == "__main__":
    main()
