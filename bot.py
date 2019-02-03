import json
import os
import sys
import random
import math

import MeCab as M
from requests_oauthlib import OAuth1Session

ACCESS_TOKEN = None
ACCESS_TOKEN_SECRET = None
CONSUMER_KEY = None
CONSUMER_KEY_SECRET = None
USER_NAME = None


def get_environ():
    global ACCESS_TOKEN
    global ACCESS_TOKEN_SECRET
    global CONSUMER_KEY
    global CONSUMER_KEY_SECRET
    global USER_NAME

    ACCESS_TOKEN = os.getenv('ACCESS_TOKEN')
    ACCESS_TOKEN_SECRET = os.getenv('ACCESS_TOKEN_SECRET')
    CONSUMER_KEY = os.getenv('CONSUMER_KEY')
    CONSUMER_KEY_SECRET = os.getenv('CONSUMER_KEY_SECRET')
    USER_NAME = os.getenv('TWITTER_USER_NAME')

    for env in [ACCESS_TOKEN, ACCESS_TOKEN_SECRET, CONSUMER_KEY, CONSUMER_KEY_SECRET]:
        if env is None:
            print('E: Environment value is not set.')
            sys.exit(1)


def get_tweet():
    session = OAuth1Session(CONSUMER_KEY, CONSUMER_KEY_SECRET,
                            ACCESS_TOKEN, ACCESS_TOKEN_SECRET)

    url = "https://api.twitter.com/1.1/statuses/home_timeline.json"
    params = {'count': 200}

    res = session.get(url, params=params)

    if res.status_code == 200:
        timeline = json.loads(res.text)
        tweets = []
        tweet_id = 0

        for tweet in timeline:
            tw = ''
            text = str(tweet['text'])
            user = str(tweet['user']['screen_name'])

            if(text.startswith('@')):
                # @リプライは除外する
                continue
            if(text.startswith('RT @')):
                # リツイートは除外する
                continue
            if 'http' in text:
                # URL付きツイートは外部サービス感が出るから除外
                continue
            if(user == USER_NAME):
                # 自分のツイートから学習するとつまらない
                continue

            for word in text.split():
                if '@' in word:
                    # ツイート途中に@ユーザー名が出てきたら飛ばす
                    break
                if '#' in word:
                    # ハッシュタグ以降は取り入れない
                    break
                tw += ' ' + word

            tw = tw.strip()


            if len(tw) > 0:
                tweets.append((tw, tweet_id))
                tweet_id += 1

        return tweets

    else:
        print('E: Could not get home timeline at error ' + str(res.status_code))
        sys.exit(1)

    return tweets


def create_tokenized_blocks(tweets):
    # MeCabのモードをスペース区切りに設定する
    m = M.Tagger('-Owakati')
    block = []

    for tweet in tweets:
        words = str(m.parse(tweet[0])).split()

        # 文頭，文末を明示する
        words.insert(0, '__BEGIN__')
        words.insert(len(words), '__END__')

        _id = tweet[1]

        for i in range(len(words) - 2):
            block.append([words[i], words[i + 1], words[i + 2], _id])

    return block


def join_blocks(blocks):
    joined_blocks = []

    # 文頭となりえる要素を抽出
    heads = [b for b in blocks if b[0] == '__BEGIN__']

    for head in heads:
        joined = []
        joined.append(head)
        while True:
            # 生成文の末尾が先頭に来るような要素を見つけて配列にする
            nominated_blocks = [b for b in blocks
                                if b[0] == joined[len(joined) - 1][2]]

            if len(nominated_blocks) == 0:
                break

            # その中からランダムに文末にくっつける
            block = random.choice(nominated_blocks)
            joined.append(block)

        joined_blocks.append(joined)

    return joined_blocks


def select_block(joined_blocks):
    # 選ばれる候補
    # tmp = []
    tmp = []

    for joined in joined_blocks:
        # 何回同じのツイートからとってきたブロックが連続して連結されたか
        cost = 0
        for i in range(len(joined) - 1):
            if (joined[i][3] == joined[i + 1][3]):
                cost += 1

        # ツイートする組を選ぶ
        print(cost)
        if(len(joined) > 20):
            continue
        if (len(joined) - cost > math.floor(len(joined) * 0.5)):
            tmp.append(joined)

    for t in tmp:
        print(convert_blocks_tostr(t))
    return random.choice(tmp)


def convert_blocks_tostr(blocks):
    string = ''

    for block in blocks:
        for word in block[1:3]:
            if(word == '__BEGIN__'):
                break
            # ハッシュタグを生かす
            if(word.startswith('#')):
                string += ' '
            if(word == '__END__'):
                break
            string += word

    return string


def tweet(text):
    twitter = OAuth1Session(CONSUMER_KEY, CONSUMER_KEY_SECRET,
                            ACCESS_TOKEN, ACCESS_TOKEN_SECRET)

    url = 'https://api.twitter.com/1.1/statuses/update.json'
    params = {'status': text}

    res = twitter.post(url, params=params)

    if res.status_code == 200:
        print('success!!')
    else:
        print('E: Tweet failed at error: ' + str(res.status_code))


if __name__ == "__main__":
    get_environ()
    tweets = get_tweet()
    blocks = create_tokenized_blocks(tweets)
    joined_blocks = join_blocks(blocks)
    block = select_block(joined_blocks)
    text = convert_blocks_tostr(block)
    print(text)
    tweet(text)
