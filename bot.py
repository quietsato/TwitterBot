import json
import sys
import random
import math

import MeCab as M
from requests_oauthlib import OAuth1Session
from argparse import ArgumentParser

ACCESS_TOKEN = "access token"
ACCESS_TOKEN_SECRET = "access token secret"
CONSUMER_KEY = "consumer key"
CONSUMER_KEY_SECRET = "consumer key secret"
USER_NAME = "screen name without @"

verbose = False
do_tweet = True
max_length = 20
tweet_count = 200


def get_tweet():
    session = OAuth1Session(CONSUMER_KEY, CONSUMER_KEY_SECRET,
                            ACCESS_TOKEN, ACCESS_TOKEN_SECRET)

    url = "https://api.twitter.com/1.1/statuses/home_timeline.json"
    params = {'count': tweet_count}

    res = session.get(url, params=params)

    if res.status_code == 200:
        timeline = json.loads(res.text)
        tweets = []
        tweet_id = 0

        if verbose:
            print('Got Tweets From API (count: ' + str(len(timeline)) + ')')

        for tweet in timeline:
            tw = ''
            text = str(tweet['text'])
            user = str(tweet['user']['screen_name'])

            isignore = False

            if(user == USER_NAME):
                # 自分のツイートから学習するとつまらない
                continue

            for prefix in ['@', 'RT @', 'http']:

                if not prefix in text:
                    continue
                if verbose:
                    print('Ignore:  ' + text)
                isignore = True

            if isignore:
                continue

            tw = (tw + text).strip()

            if len(tw) > 0:
                tweets.append((tw, tweet_id))
                tweet_id += 1
                if verbose:
                    print('Add: ' + tw)

        if verbose:
            print('Create Tweet List (count:' + str(len(tweets)) + ')')
        return tweets

    else:
        print('E: Could not get home timeline at error ' + str(res.status_code))
        sys.exit(1)


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

            # 長すぎる文はカット
            if(len(joined) > max_length):
                break

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
        if(len(joined) > 20):
            continue
        if (len(joined) - cost > math.floor(len(joined) * 0.5)):
            tmp.append(joined)

            if verbose:
                print('text: ' + convert_blocks_tostr(joined) + ' len: ' + str(len(joined)) +
                      ' cost: ' + str(cost))

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
        if verbose:
            print('Tweet success!!')
    else:
        print('E: Tweet failed at error: ' + str(res.status_code))


def argment_parser():
    usage = 'Usage: python3 {} [OPTIONS]'\
            .format(__file__)
    argparser = ArgumentParser(usage=usage)
    argparser.add_argument('-v', '--verbose',
                           action='store_true',
                           help='show verbose message')
    argparser.add_argument('-nt', '--no-tweet',
                           action='store_true',
                           help='don\'t post tweet, just console output')
    argparser.add_argument('-c', '--get-count',
                           help='count of tweets got from TimeLine, default is 200',
                           type=int)
    argparser.add_argument('-m', '--max-length',
                           help='set max count of blocks to generate sentence, default is 20',
                           type=int)

    args = argparser.parse_args()

    global verbose
    global do_tweet
    global tweet_count
    global max_length

    verbose = args.verbose
    do_tweet = not args.no_tweet
    if args.get_count:
        tweet_count = args.get_count
    if args.max_length:
        max_length = args.max_length


if __name__ == "__main__":
    argment_parser()
    tweets = get_tweet()
    blocks = create_tokenized_blocks(tweets)
    joined_blocks = join_blocks(blocks)
    block = select_block(joined_blocks)
    text = convert_blocks_tostr(block)
    print(text)
    if do_tweet:
        tweet(text)
