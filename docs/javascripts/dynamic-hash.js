// Dynamically update hashes on MkDocs/Material code blocks.
// Limitations: it does not include the "copy to clipboard" button on the rendered code block.
//
// Example of usage:
// <div class="dynamic-hash" packages-json-url="https://raw.githubusercontent.com/valory-xyz/hello-world/main/packages/packages.json" key="service/valory/hello_world/0.1.0">
// ```
// autonomy fetch valory/hello_world:0.1.0:<hash> --service
// ```
// </div>

document.addEventListener('DOMContentLoaded', function() {
  const dynamicHashElements = document.querySelectorAll('.dynamic-hash');
  
  dynamicHashElements.forEach(dynamicHashElement => {
      const url = dynamicHashElement.getAttribute('packages-json-url');
      const key = dynamicHashElement.getAttribute('key');

      fetch(url)
        .then(response => {
          if (!response.ok) {
            throw new Error('Network response was not ok');
          }
          return response.json();
        })
        .then(data => {
          const hash = data.dev[key] || '<hash>';
          console.log(`hash=`, hash);
          const originalText = dynamicHashElement.innerText;
          const updatedText = originalText.replace(/<hash>/g, hash);
          console.log('originalText:', originalText);
          console.log('updatedText:', updatedText);
          dynamicHashElement.innerHTML = `<div class="highlight"><pre><span></span><code>${updatedText}</code></pre></div>`;
        })
        .catch(error => {
          console.error('Error:', error);
        });
  });
});