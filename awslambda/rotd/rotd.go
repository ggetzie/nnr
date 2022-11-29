package main

import (
	"bytes"
	"context"
	"encoding/json"
	"flag"
	"fmt"
	"io"
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
	"golang.org/x/text/cases"
	"golang.org/x/text/language"
)

type recipe struct {
	id           int
	title        string
	ingredients  string
	instructions string
	url          string
	slug         string
	hashtags     []string
}

func init() {
	rand.Seed(time.Now().UnixNano())
}

func slugToHashtag(slug string) string {
	c := cases.Title(language.English)
	output := "#" + c.String(slug)
	output = strings.ReplaceAll(output, "-", "")
	return output
}

func setRotd() (recipe, error) {
	dbPW := os.Getenv("nnr_DB_PW")
	dbHost := os.Getenv("DB_HOST")
	dbUser := os.Getenv("DB_USER")
	dbName := os.Getenv("DB_NAME")

	dbDSN := fmt.Sprintf("host=%s user=%s password=%s dbname= %s sslmode=disable",
		dbHost, dbUser, dbPW, dbName)

	fmt.Println("Attempting to access db")

	dbpool, err := pgxpool.Connect(context.Background(), dbDSN)
	if err != nil {
		return recipe{}, err
	}
	defer dbpool.Close()

	// get the current recipe of the day
	var oldRotdID int
	query := "SELECT id FROM recipes_recipe WHERE featured = TRUE"
	err = dbpool.QueryRow(context.Background(), query).Scan(&oldRotdID)
	if err != nil {
		return recipe{}, err
	}

	// Select a recipe that hasn't been featured in the last 30 days
	omago := time.Now().AddDate(0, 0, -30).Format("2006-01-02")

	// Find how many candidates there are
	countQuery := fmt.Sprintf("SELECT Count(*) FROM recipes_recipe WHERE last_featured < '%s'", omago)
	var candidateCount int
	err = dbpool.QueryRow(context.Background(), countQuery).Scan(&candidateCount)
	if err != nil {
		return recipe{}, err
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
	if err != nil {
		return recipe{}, err
	}

	// Update the old recipe of the day so it's no longer featured
	_, err = dbpool.Exec(context.Background(), "UPDATE recipes_recipe SET featured = FALSE WHERE id = $1", oldRotdID)
	if err != nil {
		return recipe{}, err
	}

	// Update the new recipe of the day so it is featured
	_, err = dbpool.Exec(context.Background(), "UPDATE recipes_recipe SET featured = TRUE, last_featured = $1 WHERE id = $2",
		time.Now().Format("2006-01-02"), newRotd.id)
	if err != nil {
		return recipe{}, err
	}

	newRotd.url = fmt.Sprintf("https://nononsense.recipes/%s/", newRotd.slug)
	newRotd.hashtags = []string{"#Recipes"}

	// Select tags for use as hashtags in tweets
	slugsQuery := `SELECT t.name_slug FROM recipes_usertag ut INNER JOIN recipes_tag t 
	ON t.id = ut.tag_id WHERE ut.recipe_id = $1 AND t.hashtag = TRUE 
	GROUP BY t.name_slug ORDER BY Count(*) DESC LIMIT 2`
	rows, err := dbpool.Query(context.Background(), slugsQuery, newRotd.id)
	if err != nil {
		return newRotd, err
	}
	defer rows.Close()
	for rows.Next() {
		var slug string
		err = rows.Scan(&slug)
		if err != nil {
			return newRotd, err
		}
		newRotd.hashtags = append(newRotd.hashtags, slugToHashtag(slug))
	}

	return newRotd, nil
}

func stripTags(html string) string {
	// remove html tags
	res := strings.ReplaceAll(html, "</p>", "\n")
	re := regexp.MustCompile(`<[^>]*>`)
	res = re.ReplaceAllLiteralString(res, "")
	return res
}

func recipeToTweet(rotd recipe) string {
	// Generate the tweet text with url and hashtags from the recipe
	intro := "Recipe of the Day - "
	title := rotd.title
	maxLength := 280
	minTweetLength := len(intro) + len(title) + len(rotd.url) + 1
	if minTweetLength > maxLength {
		// Need to truncate title
		overrun := minTweetLength - maxLength
		shortened := len(rotd.title) - overrun - 3
		title = rotd.title[:shortened] + "..."
	}
	tweet := intro + title + " " + rotd.url
	// add hashtags if there's room
	for _, hashtag := range rotd.hashtags {
		newLength := len(tweet) + len(hashtag) + 1
		if newLength <= maxLength {
			tweet += (" " + hashtag)
		}
	}
	return tweet
}

func postToTwitter(rotd recipe) (string, error) {
	// Tweet title and link to rotd page to Twitter
	tweetStatus := recipeToTweet(rotd)
	twitterConsumerKey := os.Getenv("TWITTER_CONSUMER_KEY")
	twitterConsumerSecret := os.Getenv("TWITTER_CONSUMER_SECRET")
	twitterAccessToken := os.Getenv("TWITTER_ACCESS_TOKEN")
	twitterAccessSecret := os.Getenv("TWITTER_ACCESS_SECRET")
	config := oauth1.NewConfig(twitterConsumerKey, twitterConsumerSecret)
	token := oauth1.NewToken(twitterAccessToken, twitterAccessSecret)

	httpClient := config.Client(oauth1.NoContext, token)
	client := twitter.NewClient(httpClient)
	_, _, err := client.Statuses.Update(tweetStatus, nil)
	if err != nil {
		return fmt.Sprintf("Error sending tweet: %v\n", err), err
	}

	return "Successful Twitter post", nil
}

func postToFacebook(rotd recipe) (string, error) {
	fbPageId := os.Getenv("FB_PAGE_ID")
	fbPageToken := os.Getenv("FB_PAGE_TOKEN")
	fbUrl := fmt.Sprintf("https://graph.facebook.com/%s/feed", fbPageId)

	message := fmt.Sprintf(
		"%s\n\n%s\n%s",
		rotd.title,
		stripTags(rotd.ingredients),
		stripTags(rotd.instructions),
	)

	requestBody, err := json.Marshal(map[string]string{
		"message":      message,
		"link":         rotd.url,
		"access_token": fbPageToken,
	})
	if err != nil {
		return fmt.Sprintf("Error building FB request json: %v", err), err
	}

	resp, err := http.Post(fbUrl, "application/json", bytes.NewBuffer((requestBody)))
	if err != nil {
		return fmt.Sprintf("Error from http.Post to FB: %v", err), err
	}

	defer resp.Body.Close()

	body, err := io.ReadAll(resp.Body)
	if err != nil {
		return fmt.Sprintf("Error reading FB response body: %v", err), err
	}

	return string(body), nil

}

func handler(ctx context.Context, event events.CloudWatchEvent) (string, error) {
	// select new Recipe of the day
	newRotd, err := setRotd()
	if err != nil {
		return fmt.Sprintf("Error selecting new rotd: %v\n", err), err
	}

	// Post new recipe of the day to Twitter
	twitterResponse, err := postToTwitter(newRotd)
	if err != nil {
		return fmt.Sprintf("Error posting to Twitter: %v\n", err), err
	}
	fmt.Println("Response from Twitter post:", twitterResponse)

	// Post new recipe of the day to Facebook page
	fbResponse, err := postToFacebook(newRotd)
	if err != nil {
		return fmt.Sprintf("Error posting to Facebook: %v\n", err), err
	}
	fmt.Println("Response from Facebook post:", fbResponse)

	return "Recipe of the Day updated", nil

}

func main() {
	testPtr := flag.Bool("test", false, "Run locally in test mode")
	flag.Parse()
	if *testPtr {
		newRotd, err := setRotd()
		if err != nil {
			fmt.Println("Error selecting rotd:", err)
		}

		twitterResponse, err := postToTwitter(newRotd)
		if err != nil {
			fmt.Println("Error posting to Twitter:", err)
		}
		fmt.Println("Response from Twitter post:", twitterResponse)

		fbResponse, err := postToFacebook(newRotd)
		if err != nil {
			fmt.Println("Error posting to Facebook:", err)
		}
		fmt.Println("Response from Facebook post:", fbResponse)

	} else {
		lambda.Start(handler)
	}

}
