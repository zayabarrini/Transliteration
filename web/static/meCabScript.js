document.addEventListener('DOMContentLoaded', function () {
  const analyzeBtn = document.getElementById('analyzeBtn');
  const sentenceInput = document.getElementById('sentenceInput');
  const resultsDiv = document.getElementById('results');
  const clearBtn = document.getElementById('clearBtn');
  const targetLanguageSelect = document.getElementById('targetLanguage');

  analyzeBtn.addEventListener('click', analyzeSentences);
  if (clearBtn) {
    clearBtn.addEventListener('click', clearSentences);
  }

  // Example sentences
  sentenceInput.value = '私は本を読みました。\n彼女は学校に行きます。\nこれは美味しい食べ物です。';

  function analyzeSentences() {
    const sentences = sentenceInput.value.split('\n').filter((s) => s.trim());
    const targetLanguage = targetLanguageSelect ? targetLanguageSelect.value : 'en';

    if (sentences.length === 0) {
      alert('Please enter at least one Japanese sentence.');
      return;
    }

    resultsDiv.innerHTML = '<div class="loading">Analyzing sentences...</div>';

    fetch('/analyze', {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
      },
      body: JSON.stringify({
        sentences: sentences,
        target_language: targetLanguage,
      }),
    })
      .then((response) => {
        if (!response.ok) {
          throw new Error('Network response was not ok');
        }
        return response.json();
      })
      .then((data) => {
        displayResults(data.results);
      })
      .catch((error) => {
        console.error('Error:', error);
        resultsDiv.innerHTML =
          '<div class="error">Error analyzing sentences. Please check if the server is running and try again.</div>';
      });
  }

  function clearSentences() {
    sentenceInput.value = '';
    resultsDiv.innerHTML = '';
  }

  function displayResults(results) {
    if (results.length === 0) {
      resultsDiv.innerHTML = '<div class="error">No results returned.</div>';
      return;
    }

    resultsDiv.innerHTML = '';

    results.forEach((result, index) => {
      const sentenceDiv = document.createElement('div');
      sentenceDiv.className = 'sentence-result';

      let analysisHTML = `
        <div class="sentence-header">
          <div class="original-sentence">${result.original}</div>
          <div class="translated-sentence">${result.translated}</div>
        </div>
        <div class="analysis-grid">
      `;

      result.analysis.forEach((word) => {
        // Only show translation if it exists
        const translationDisplay = word.translation
          ? `<div class="word-translation">${word.translation}</div>`
          : '';

        analysisHTML += `
          <div class="word-card" data-pos="${word.part_of_speech}">
            <div class="word-japanese">${word.word}</div>
            ${translationDisplay}
            <div class="word-details">
              <div class="detail-item"><strong>POS:</strong> ${word.part_of_speech}</div>
              <div class="detail-item"><strong>Role:</strong> ${word.syntax_role}</div>
              ${
                word.particle_type !== 'None'
                  ? `<div class="detail-item"><strong>Particle:</strong> ${word.particle_type}</div>`
                  : ''
              }
              ${
                word.verb_form !== 'None'
                  ? `<div class="detail-item"><strong>Verb Form:</strong> ${word.verb_form}</div>`
                  : ''
              }
              ${
                word.honorific_level !== 'PLAIN'
                  ? `<div class="detail-item"><strong>Honorific:</strong> ${word.honorific_level}</div>`
                  : ''
              }
              <div class="detail-item"><strong>Category:</strong> ${word.semantic_category}</div>
            </div>
          </div>
        `;
      });

      analysisHTML += '</div>';
      sentenceDiv.innerHTML = analysisHTML;
      resultsDiv.appendChild(sentenceDiv);
    });
  }

  // Auto-analyze on page load
  setTimeout(analyzeSentences, 1000);
});
