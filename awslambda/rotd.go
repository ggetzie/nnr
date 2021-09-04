package main

import (
	"bytes"
	"context"
	"encoding/json"
	"fmt"
	"io/ioutil"
	"math/rand"
	"net/http"
	"os"
	"regexp"
	"strings"
	"time"

	"github.com/aws/aws-lambda-go/events"
	"github.com/aws/aws-lambda-go/lambda"
	"github.com/dghubble/go-twitter/twitter"
	"github.com/dghubble/oauth1"
	"github.com/jackc/pgx/v4/pgxpool"
)

type recipe struct {
	id           int
	title        string
	ingredients  string
	instructions string
	url          string
	slug         string
}

func init() {
	rand.Seed(time.Now().UnixNano())
}

var rotdURL = "https://nononsense.recipes/rotd"

func stripTags(html string) string {
	// remove html tags
	res := strings.ReplaceAll(html, "</p>", "\n")
	re := regexp.MustCompile(`<[^>]*>`)
	res = re.ReplaceAllLiteralString(res, "")
	return res
}

func getTweetTitle(title string, url string) string {
	maxTitleLen := 280 - len("Recipe of the Day - ") - len(url) - 2
	titleLen := len(title)
	if titleLen > maxTitleLen {
		return fmt.Sprintf("%s...", title[:maxTitleLen-3])
	}
	return title
}

func postToFacebook(rotd recipe) (string, error) {
	fbPageId := os.Getenv("FB_PAGE_ID")
	fbPageToken := os.Getenv("FB_PAGE_TOKEN")
	fbUrlBase := "https://graph.facebook.com"

	message := fmt.Sprintf(
		"%s\n\n%s\n%s\n%s",
		rotd.title,
		stripTags(rotd.ingredients),
		stripTags(rotd.instructions),
		rotd.url,
	)

	fullUrl := fmt.Sprintf("%s/%s/feed", fbUrlBase, fbPageId)

	requestBody, err := json.Marshal(map[string]string{
		"message":      message,
		"access_token": fbPageToken,
	})
	if err != nil {
		return fmt.Sprintf("Error building FB request json: %v", err), err
	}

	resp, err := http.Post(fullUrl, "application/json", bytes.NewBuffer((requestBody)))
	if err != nil {
		return fmt.Sprintf("Error from http.Post to FB: %v", err), err
	}

	defer resp.Body.Close()

	body, err := ioutil.ReadAll(resp.Body)
	if err != nil {
		return fmt.Sprintf("Error reading FB response body: %v", err), err
	}

	return string(body), nil

}

func handler(ctx context.Context, event events.CloudWatchEvent) (string, error) {

	dbPW := os.Getenv("nnr_DB_PW")
	dbHost := os.Getenv("DB_HOST")
	dbUser := "nnr_db_user"
	dbName := "nnr_db"

	dbDSN := fmt.Sprintf("host=%s user=%s password=%s dbname= %s sslmode=disable",
		dbHost, dbUser, dbPW, dbName)

	fmt.Println("Attempting to access db")

	dbpool, err := pgxpool.Connect(context.Background(), dbDSN)
	if err != nil {
		return fmt.Sprintf("Unable to connect to database: %v\n", err), err
	}
	defer dbpool.Close()

	// get the current recipe of the day
	var oldRotdID int
	query := "SELECT id FROM recipes_recipe WHERE featured = TRUE"
	err = dbpool.QueryRow(context.Background(), query).Scan(&oldRotdID)
	if err != nil {
		return fmt.Sprintf("Find old rotd failed: %v\n", err), err
	}

	// Select a recipe that hasn't been featured in the last 30 days
	omago := time.Now().AddDate(0, 0, -30).Format("2006-01-02")

	// Find how many candidates there are
	countQuery := fmt.Sprintf("SELECT Count(*) FROM recipes_recipe WHERE last_featured < '%s'", omago)
	var candidateCount int
	err = dbpool.QueryRow(context.Background(), countQuery).Scan(&candidateCount)
	if err != nil {
		return fmt.Sprintf("Count candidates failed: %v\n", err), err
	}

	// Pick a random candidate from the eligible recipes
	selectIndex := rand.Intn(candidateCount)
	candidateQuery := "SELECT id, title, title_slug, ingredients_html, instructions_html FROM recipes_recipe WHERE last_featured < $1 LIMIT 1 OFFSET $2"

	var newRotd recipe
	err = dbpool.QueryRow(
		context.Background(),
		candidateQuery,
		omago,
		selectIndex).Scan(
		&newRotd.id,
		&newRotd.title,
		&newRotd.slug,
		&newRotd.ingredients,
		&newRotd.instructions)

	newRotd.url = fmt.Sprintf("https://nononsense.recipes/%s/", newRotd.slug)
	if err != nil {
		return fmt.Sprintf("Select new Rotd failed: %v\n", err), err

	}

	// Update the old recipe of the day so it's no longer featured
	_, err = dbpool.Exec(context.Background(), "UPDATE recipes_recipe SET featured = FALSE WHERE id = $1", oldRotdID)
	if err != nil {
		return fmt.Sprintf("Error updating old rotd: %v\n", err), err
	}

	// Update the new recipe of the day so it is featured
	_, err = dbpool.Exec(context.Background(), "UPDATE recipes_recipe SET featured = TRUE, last_featured = $1 WHERE id = $2",
		time.Now().Format("2006-01-02"), newRotd.id)
	if err != nil {
		return fmt.Sprintf("Error updating new rotd: %v\n", err), err
	}
	fmt.Println("Selected new Recipe of the Day")

	// Tweet title and link to rotd page to Twitter
	tweetStatus := fmt.Sprintf("Recipe of the Day - %s: %s",
		getTweetTitle(newRotd.title, newRotd.url), newRotd.url)
	twitterConsumerKey := os.Getenv("TWITTER_CONSUMER_KEY")
	twitterConsumerSecret := os.Getenv("TWITTER_CONSUMER_SECRET")
	twitterAccessToken := os.Getenv("TWITTER_ACCESS_TOKEN")
	twitterAccessSecret := os.Getenv("TWITTER_ACCESS_SECRET")
	config := oauth1.NewConfig(twitterConsumerKey, twitterConsumerSecret)
	token := oauth1.NewToken(twitterAccessToken, twitterAccessSecret)

	httpClient := config.Client(oauth1.NoContext, token)
	client := twitter.NewClient(httpClient)

	fmt.Println("sending tweet")
	tweet, resp, err := client.Statuses.Update(tweetStatus, nil)
	if err != nil {
		return fmt.Sprintf("Error sending tweet: %v\n", err), err
	}
	fmt.Println(tweet)
	fmt.Println(resp)

	// Post new recipe of the day to Facebook page
	fbResponse, err := postToFacebook(newRotd)
	if err != nil {
		return fmt.Sprintf("Error posting to Facebook: %v\n", err), err
	}
	fmt.Println("Response from Facebook post:", fbResponse)

	return "Recipe of the Day updated", nil

}

func main() {
	lambda.Start(handler)
}
