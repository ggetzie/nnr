# Recipe of the Day

This function randomly chooses a new recipe of the day, tweets it to @n_n_recipes on Twitter and posts it to the No Nonsense Recipes Facebook page.

It is intended to be run either in an AWS Lambda scheduled to run once a day or on the server as a cron job.

The following environment variables must be set and accessible:

```
nnr_DB_PW
DB_HOST
DB_USER
DB_NAME
TWITTER_CONSUMER_KEY
TWITTER_CONSUMER_SECRET
TWITTER_ACCESS_TOKEN
TWITTER_ACCESS_SECRET
FB_PAGE_ID
FB_PAGE_TOKEN
```

Build

```
go build -o build/rotd rotd.go
```

Run - Local
```
/usr/local/src/nnr/awslambda/rotd/build/rotd --local
```