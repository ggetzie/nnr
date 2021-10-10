package main

import (
	"fmt"
	"testing"
)

func TestSlugToHashtag(t *testing.T) {
	slug := "slow-cooker"
	want := "#SlowCooker"
	hashtag := slugToHashtag(slug)
	if hashtag != want {
		t.Fatalf(`slugToHashTag Failed Wanted %q Got %v`, want, hashtag)
	}

	slug = "4th-of-july"
	want = "#4thOfJuly"
	hashtag = slugToHashtag(slug)
	if hashtag != want {
		t.Fatalf(`slugToHashTag Failed Wanted %q Got %v`, want, hashtag)
	}

	slug = "soup"
	want = "#Soup"
	hashtag = slugToHashtag(slug)
	if hashtag != want {
		t.Fatalf(`slugToHashTag Failed Wanted %q Got %v`, want, hashtag)
	}

	slug = "vegetable-side-dish"
	want = "#VegetableSideDish"
	hashtag = slugToHashtag(slug)
	if hashtag != want {
		t.Fatalf(`slugToHashTag Failed Wanted %q Got %v`, want, hashtag)
	}

}

func TestRecipeToTweet(t *testing.T) {
	rotd := recipe{
		title:    "Really Real Strawberry Cupcakes",
		url:      "https://nononsense.recipes/really-real-strawberry-cupcakes",
		hashtags: []string{"#Recipes", "#Cupcakes", "#Dessert"},
	}
	want := fmt.Sprintf(
		"Recipe of the Day - %s %s %s %s %s",
		rotd.title,
		rotd.url,
		rotd.hashtags[0],
		rotd.hashtags[1],
		rotd.hashtags[2])
	tweet := recipeToTweet(rotd)
	if tweet != want {
		t.Fatalf(`recipeToTweet Failed Wanted %q Got %v`, want, tweet)
	}
}

func TestRecipeToTweetTooLong(t *testing.T) {
	rotd := recipe{
		title: "Really Long Title Really Long Title Really Long Title Really Long Title Really Long Title Really Long Title Really Long Title",
		url:   "https://nononsense.recipes/really-long-title-really-long-title-really-long-title-really-long-title-really-long-title-really-long-title-really-long-title",
	}
	abbreviated := "Really Long Title Really Long Title Really Long Title Really Long Title Really Long Title Really Long Ti..."
	tweet := recipeToTweet(rotd)
	want := fmt.Sprintf(
		"Recipe of the Day - %s %s",
		abbreviated,
		rotd.url,
	)

	if len(tweet) > 280 {
		t.Fatalf("recipeToTweetTooLong Failed. Tweet still too long!")
	}

	if tweet != want {
		t.Fatalf(`recipeToTweetTooLong Failed Wanted %q Got %v`, want, tweet)
	}

}

func TestSetRotd(t *testing.T) {
	rotd, err := setRotd()
	if err != nil {
		t.Fatalf(`Error setting rotd %v`, err)
	}
	t.Log("Set new Recipe of the Day")
	t.Log("id:", rotd.id)
	t.Log("title:", rotd.title)
	t.Log("ingredients:", rotd.ingredients)
	t.Log("instructions:", rotd.instructions)
	t.Log("slug:", rotd.slug)
	t.Log("url:", rotd.url)
	t.Log("hashtags:", rotd.hashtags)
}
