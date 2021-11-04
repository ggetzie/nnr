package main

import (
	"bytes"
	"context"
	"encoding/base64"
	"encoding/json"
	"errors"
	"fmt"
	"io"
	"net/http"
	"os"
	"path"

	"github.com/aws/aws-lambda-go/events"
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

func processImage(
	img *bimg.Image,
	imageTypes []bimg.ImageType,
	dims map[string]bimg.ImageSize,
	save_to string) (string, error) {
	origOptions := bimg.Options{
		NoAutoRotate:  false,
		StripMetadata: true,
		Type:          bimg.JPEG,
	}
	origImage, err := img.Process(origOptions)
	if err != nil {
		fmt.Fprintln(os.Stderr, err)
		return "Error converting and autorotating", err
	}
	origDims, err := img.Size()
	if err != nil {
		fmt.Fprintln(os.Stderr, err)
		return "Error getting image size", err
	}
	origPath := path.Join(save_to, "orig.jpeg")
	saveImageLocal(origImage, origPath)
	for screenSize, dim := range dims {
		for _, iType := range imageTypes {
			savePath := buildPath(save_to, screenSize, iType)
			newDims := smartDims(origDims, dim)
			newImage, err := bimg.NewImage(origImage).Resize(newDims.Width, newDims.Height)
			if err != nil {
				fmt.Fprintln(os.Stderr, err)
				return fmt.Sprintf("Error resizing to %dWx%dH", newDims.Width, newDims.Height), err
			}
			newImage, err = bimg.NewImage(newImage).Convert(iType)
			if err != nil {
				fmt.Fprintln(os.Stderr, err)
				return fmt.Sprintf("Error converting to %s", bimg.ImageTypeName(iType)), err
			}
			saveImageLocal(newImage, savePath)
		}
	}
	return "Success", nil
}

type Response events.APIGatewayProxyResponse

func createResponse(payload map[string]interface{}, status int) (Response, error) {

	body, err := json.Marshal(payload)
	if err != nil {
		fmt.Fprintln(os.Stderr, err)
		return Response{StatusCode: 500}, err
	}
	var buf bytes.Buffer
	json.HTMLEscape(&buf, body)
	return Response{
		StatusCode:      status,
		IsBase64Encoded: false,
		Body:            buf.String(),
		Headers: map[string]string{
			"Content-Type": "application/json",
		},
	}, nil

}

func downloadImage(url string) (string, error) {
	response, err := http.Get(url)
	if err != nil {
		return "", err
	}
	defer response.Body.Close()
	if response.StatusCode != 200 {
		return "", errors.New("error downloading image")
	}
	buffer, err := io.ReadAll(response.Body)
	if err != nil {
		return "", err
	}
	img := bimg.NewImage(buffer)
	if !bimg.IsTypeNameSupported(img.Type()) {
		return "", errors.New("invalid image type")
	}
	filepath := fmt.Sprintf("/tmp/downloaded.%s", img.Type())
	bimg.Write(filepath, img.Image())
	return filepath, nil
}

type urls struct {
	Download string
	Upload   string
}

type payloadInput struct {
	Url string
}

type payloadOutput struct {
	Filename       string
	Width          int
	Height         int
	UploadUrl      string
	StripMetadata  bool
	AutoRotate     bool
	UploadOriginal bool
}

type payload struct {
	Input  payloadInput
	Output []payloadOutput
}

func decodeRequest(event events.APIGatewayProxyRequest) (payload, error) {
	var requestPayload payload
	if event.IsBase64Encoded {
		decoded, err := base64.StdEncoding.DecodeString(event.Body)
		if err != nil {
			fmt.Fprintln(os.Stderr, err)
			return requestPayload, err
		}
		err = json.Unmarshal(decoded, &requestPayload)
		if err != nil {
			fmt.Fprintln(os.Stderr, err)
			return requestPayload, err
		}
	} else {
		err := json.Unmarshal([]byte(event.Body), &requestPayload)
		if err != nil {
			fmt.Fprintln(os.Stderr, err)
			return requestPayload, err
		}
	}
	return requestPayload, nil
}

func Handler(ctx context.Context, event events.APIGatewayProxyRequest) (Response, error) {
	// download photo to /tmp
	body, err := decodeRequest(event)
	if err != nil {
		fmt.Fprintln(os.Stderr, err)
		return Response{StatusCode: 500}, err
	}

	filepath, err := downloadImage(body.Input.Url)
	if err != nil {
		fmt.Fprintln(os.Stderr, err)
		return Response{StatusCode: 500}, err
	}
	// resize photo in /tmp
	img, err := loadImageLocal(filepath)
	if err != nil {
		fmt.Fprintln(os.Stderr, err)
		return Response{StatusCode: 500}, err
	}
	dims := getDefaultDims()
	imageTypes := getDefaultImageTypes()
	processImage(img, imageTypes, dims, "/tmp")
	// upload to S3
	response, err := createResponse(map[string]interface{}{
		"message": "Success",
	}, 200)
	if err != nil {
		fmt.Fprintln(os.Stderr, err)
		return Response{StatusCode: 500}, err
	}
	return response, nil
}
