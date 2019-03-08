# TwitterBot
Tweet with the sentence that generated with tweets on TimeLine.

## How to run
Set these environment values.
```run.sh
export ACCESS_TOKEN="twitter access token"
export ACCESS_TOKEN_SECRET="twitter access token secret"
export CONSUMER_KEY="consumer key"
export CONSUMER_KEY_SECRET="consumer key secret"
export TWITTER_USER_NAME="user name without @"

python3 ./bot.py
```

## Dependences
- mecab
- requests-oauthlib
