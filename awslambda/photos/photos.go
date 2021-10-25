package main

import (
	"fmt"
	"os"

	"github.com/h2non/bimg"
)

func loadImageLocal(filepath string) (*bimg.Image, error) {
	buffer, err := bimg.Read(filepath)
	if err != nil {
		return nil, err
	}
	return bimg.NewImage(buffer), nil
}

func saveImageLocal(buffer []byte, filepath string) {
	bimg.Write(filepath, buffer)

}

func getDefaultImageTypes() []bimg.ImageType {
	return []bimg.ImageType{bimg.PNG, bimg.WEBP}
}

func getDefaultDims() [][]int {
	// Array of {width, height} to resize photos to
	return [][]int{{1040, 585}, {860, 484}, {620, 349}, {490, 276}}
}

func printMetadata(filepath string) {
	buffer, err := bimg.Read(filepath)
	if err != nil {
		fmt.Fprintln(os.Stderr, err)
	}

	metadata, err := bimg.Metadata(buffer)
	if err != nil {
		fmt.Fprintln(os.Stderr, err)
	}

	fmt.Printf("metadata\n%+v", metadata)

}

func processImage(img *bimg.Image, save_to string) {
	origOptions := bimg.Options{
		NoAutoRotate:  false,
		StripMetadata: true,
		Type:          bimg.JPEG,
	}
	origImage, err := img.Process(origOptions)
	if err != nil {
		fmt.Fprintln(os.Stderr, err)
	}

	imageTypes := getDefaultImageTypes()
	dims := getDefaultDims()

	// metadata, err := bimg.Metadata(newImage)
	// if err != nil {
	// 	fmt.Fprintln(os.Stderr, err)
	// }

}
