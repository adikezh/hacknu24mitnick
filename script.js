const translateForm = document.getElementById('translate-form');
const sourceLangSelect = document.getElementById('source-lang');
const targetLangSelect = document.getElementById('target-lang');
const sourceTextArea = document.getElementById('source-text');
const translatedTextDiv = document.getElementById('translated-text');

translateForm.addEventListener('submit', async (event) => {
  event.preventDefault();

  const sourceLang = sourceLangSelect.value;
  const targetLang = targetLangSelect.value;
  const textToTranslate = sourceTextArea.value;

  // Clear previous translation if any
  translatedTextDiv.textContent = '';

  // Show a loading indicator
  const loadingIndicator = document.createElement('p');
  loadingIndicator.textContent = 'Translating...'; 
  translatedTextDiv.appendChild(loadingIndicator);

  try {
    const response = await fetch('/translate', {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json'
      },
      body: JSON.stringify({
        sourceLanguageCode: sourceLang,
        targetLanguageCode: targetLang,
        texts: [textToTranslate]
      })
    });

    if (!response.ok) {
      throw new Error(`Translation error: HTTP ${response.status}`);
    }

    const translatedData = await response.json();
    translatedTextDiv.textContent = translatedData.translatedText; 
  } catch (error) {
    console.error(error);
    translatedTextDiv.textContent = 'An error occurred during translation. Please try again.';
  } finally {
    // Remove the loading indicator in any case
    loadingIndicator.remove();
  }
});
