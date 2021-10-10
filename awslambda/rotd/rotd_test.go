package main

import (
	"testing"
)

func TestSlugToHashtag(t *testing.T) {
	slug := "slow-cooker"
	want := "#SlowCooker"
	hashtag := slugToHastag(slug)
	if hashtag != want {
		t.Fatalf(`slugToHashTag Failed Wanted %q Got %v`, want, hashtag)
	}

	slug = "4th-of-july"
	want = "#4thOfJuly"
	hashtag = slugToHastag(slug)
	if hashtag != want {
		t.Fatalf(`slugToHashTag Failed Wanted %q Got %v`, want, hashtag)
	}

	slug = "soup"
	want = "#Soup"
	hashtag = slugToHastag(slug)
	if hashtag != want {
		t.Fatalf(`slugToHashTag Failed Wanted %q Got %v`, want, hashtag)
	}

	slug = "vegetable-side-dish"
	want = "#VegetableSideDish"
	hashtag = slugToHastag(slug)
	if hashtag != want {
		t.Fatalf(`slugToHashTag Failed Wanted %q Got %v`, want, hashtag)
	}

}
