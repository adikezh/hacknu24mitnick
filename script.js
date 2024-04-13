// API keys
const iamKey = 't1.9euelZrJkImViYmaz82alY3Nmc-ax-3rnpWazpuUj8_InJTHiZDIzpWVzMvl9PclVxZP-e9Vc1iH3fT3ZQUUT_nvVXNYh83n9euelZqZx5HNyI6clMnKm5WLlpjIne_8zef1656VmpXOk5eXj8iOjJLPnpiUycrK7_3F656VmpnHkc3IjpyUycqblYuWmMid.xnIkwlQrsQ9dAYqwiadGkrjjP761JphxIwZ-zZjAoulFlMOLQLVK3Li_gnM1IFAZlZzNsvXNW08sIOsP2pe5Dg';
const apikey = 'AQVN1R6Me5L03YaXJpZaY6muWlvP4j7AwelVYB-C';

// HTML elements
const translateForm = document.getElementById('translate-form');
const sourceLangSelect = document.getElementById('source-lang');
const targetLangSelect = document.getElementById('target-lang');
const sourceTextArea = document.getElementById('source-text');
const translatedTextDiv = document.getElementById('translated-text');

// Fetch the list of languages on page load
getLanguages();

function getLanguages() {
  fetch('https://translate.api.cloud.yandex.net/translate/v2/languages', {
    method: 'POST',
    headers: {
      'Authorization': `Bearer ${iamKey}`,
      'Content-Type': 'application/json'
    },
    body: JSON.stringify({
      'folderId': folderId 
    })
  })
  .then(response => response.json())
  .then(data => {
    const languages = data.languages;
    populateLanguageSelect(languages, sourceLangSelect);
    populateLanguageSelect(languages, targetLangSelect);
  })
  .catch(error => console.error('Error fetching languages:', error));
}
function populateLanguageSelect(languages, selectElement) {
  languages.forEach(language => {
    const option = document.createElement('option');
    option.value = language.code;
    option.text = language.name;
    selectElement.appendChild(option);
  });
}

function translateText() {
  const sourceText = sourceTextArea.value;
  const sourceLanguage = sourceLangSelect.value;
  const targetLanguage = targetLangSelect.value;

  translatedTextDiv.textContent = 'Translating...';

  fetch('https://translate.api.cloud.yandex.net/translate/v2/translate', {
    method: 'POST',
    headers: {
      'Authorization': `Bearer ${iamKey}`,
      'Content-Type': 'application/json'
    },
    body: JSON.stringify({
      'sourceLanguageCode': sourceLanguage,
      'targetLanguageCode': targetLanguage,
      'texts': [sourceText],
      'folderId': folderId,
      'format': 'PLAIN_TEXT',
      'speller': true
    })
  })
  .then(response => response.json())
  .then(data => {
    const translatedText = data.translations[0].text;
    translatedTextDiv.textContent = translatedText;
  })
  .catch(error => console.error('Translation error:', error));
}

translateForm.addEventListener('submit', (event) => {
  event.preventDefault();
  translateText();
});