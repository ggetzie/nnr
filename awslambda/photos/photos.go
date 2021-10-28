package main

import (
	"fmt"
	"os"
	"path"

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

func getDefaultDims() map[string]bimg.ImageSize {
	// Array of {width, height} to resize photos to
	dims := map[string]bimg.ImageSize{
		"1200": {Width: 1090, Height: 818},
		"992":  {Width: 910, Height: 683},
		"768":  {Width: 670, Height: 503},
		"576":  {Width: 515, Height: 386},
	}
	return dims
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

func buildPath(folder string, name string, iType bimg.ImageType) string {
	filename := fmt.Sprintf("%s.%v", name, bimg.ImageTypeName(iType))
	return path.Join(folder, filename)
}

func resizeToHeight(originalDims bimg.ImageSize, height int) bimg.ImageSize {
	// adjust dimensions to match height, preserving aspect ratio
	newWidth := originalDims.Width * height / originalDims.Height
	return bimg.ImageSize{Width: newWidth, Height: height}
}

func resizeToWidth(originalDims bimg.ImageSize, width int) bimg.ImageSize {
	// adjust dimensions to match width, perserving aspect ratio
	newHeight := originalDims.Height * width / originalDims.Width
	return bimg.ImageSize{Width: width, Height: newHeight}
}

func smartDims(originalDims bimg.ImageSize, maxDims bimg.ImageSize) bimg.ImageSize {
	// Calculate dims within max width and height, perserving aspect ratio
	if (originalDims.Width <= maxDims.Width) && (originalDims.Height <= maxDims.Height) {
		// already small enough
		return originalDims
	}
	var resized bimg.ImageSize
	if originalDims.Width > originalDims.Height {
		// Landscape - more wide than tall
		resized = resizeToWidth(originalDims, maxDims.Width)
		if resized.Height > maxDims.Height {
			// Width correct, but still too tall
			resized = resizeToHeight(resized, maxDims.Height)
		}
	} else {
		// Portrait - more tall than wide
		resized = resizeToHeight(originalDims, maxDims.Height)
		if resized.Width > maxDims.Width {
			// height correct but still too wide
			resized = resizeToWidth(resized, maxDims.Width)
		}
	}
	return resized
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
	origDims, err := img.Size()
	if err != nil {
		fmt.Fprintln(os.Stderr, err)
	}
	origPath := path.Join(save_to, "orig.jpeg")
	saveImageLocal(origImage, origPath)

	imageTypes := getDefaultImageTypes()
	dims := getDefaultDims()

	for screenSize, dim := range dims {
		for _, iType := range imageTypes {
			savePath := buildPath(save_to, screenSize, iType)
			newDims := smartDims(origDims, dim)
			newImage, err := bimg.NewImage(origImage).Resize(newDims.Width, newDims.Height)
			if err != nil {
				fmt.Fprintln(os.Stderr, err)
			}
			newImage, err = bimg.NewImage(newImage).Convert(iType)
			if err != nil {
				fmt.Fprintln(os.Stderr, err)
			}
			saveImageLocal(newImage, savePath)
		}
	}
}
