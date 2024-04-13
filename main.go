package main

import (
	"encoding/json"
	"fmt"
	"io/ioutil"
	"net/http"
)

// TODO: Replace with your actual Yandex Translate API key
var apiKey = "yAQVN1R6Me5L03YaXJpZaY6muWlvP4j7AwelVYB-C"

type TranslationRequest struct {
	SourceLanguageCode string   `json:"sourceLanguageCode"`
	TargetLanguageCode string   `json:"targetLanguageCode"`
	Texts              []string `json:"texts"`
}

type TranslationResponse struct {
	Translations []struct {
		Text string `json:"text"`
	} `json:"translations"`
}

func translateHandler(w http.ResponseWriter, r *http.Request) {
	if r.Method != http.MethodPost {
		w.WriteHeader(http.StatusMethodNotAllowed)
		return
	}

	// Read request body
	body, err := ioutil.ReadAll(r.Body)
	if err != nil {
		http.Error(w, "Error reading request body", http.StatusBadRequest)
		return
	}

	// Parse request JSON
	var request TranslationRequest
	err = json.Unmarshal(body, &request)
	if err != nil {
		http.Error(w, "Error parsing request JSON", http.StatusBadRequest)
		return
	}

	// Construct Yandex Translate API request URL
	apiUrl := fmt.Sprintf("https://translate.api.cloud.yandex.net/translate/v2/translate?key=%s&sourceLanguageCode=%s&targetLanguageCode=%s&texts=%s",
		apiKey, request.SourceLanguageCode, request.TargetLanguageCode, request.Texts[0])

	// Send request to Yandex Translate API
	resp, err := http.Get(apiUrl)
	if err != nil {
		http.Error(w, "Error sending request to Yandex API", http.StatusInternalServerError)
		return
	}
	defer resp.Body.Close()

	// Parse Yandex Translate API response
	var translationResponse TranslationResponse
	err = json.NewDecoder(resp.Body).Decode(&translationResponse)
	if err != nil {
		http.Error(w, "Error parsing Yandex API response", http.StatusInternalServerError)
		return
	}

	// Format output JSON with translated text
	output := struct {
		TranslatedText string `json:"translatedText"`
	}{
		TranslatedText: translationResponse.Translations[0].Text,
	}

	// Send JSON response
	w.Header().Set("Content-Type", "application/json")
	json.NewEncoder(w).Encode(output)
}

func main() {
	http.HandleFunc("/translate", translateHandler)
	fmt.Println("Server listening on port 8080")
	http.ListenAndServe(":5500", nil)
}
