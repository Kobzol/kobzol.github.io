const ansi_up = new AnsiUp;

function showErrorWidget(data, id) {
    const errorWidget = document.getElementById("error-widget");
    errorWidget.innerHTML = "";

    const program = data.programs.find(program => program.name === id);

    // Create program panel
    const srcPanel = document.createElement('div');
    srcPanel.className = 'source-code';
    srcPanel.innerHTML = `
                <pre><code class="language-rust">${escapeHtml(program.source)}</code></pre>
            `;
    errorWidget.appendChild(srcPanel);

    // Add error container
    const errorContainer = document.createElement('div');
    errorContainer.className = 'error-container';

    // Add version slider
    const versionSliderContainer = document.createElement('div');
    versionSliderContainer.className = 'version-slider-container';

    const minVersionLabel = document.createElement('div');
    minVersionLabel.className = 'version-label';
    minVersionLabel.textContent = program.versions[0].release;

    const versionSlider = document.createElement('input');
    versionSlider.type = 'range';
    versionSlider.min = '0';
    versionSlider.max = (program.versions.length - 1).toString();
    versionSlider.value = '0';
    versionSlider.className = 'version-slider';

    const maxVersionLabel = document.createElement('div');
    maxVersionLabel.className = 'version-label';
    maxVersionLabel.textContent = program.versions[program.versions.length - 1].release;

    const currentVersionLabel = document.createElement('div');
    currentVersionLabel.className = 'version-label';
    currentVersionLabel.textContent = program.versions[0].release;

    const beforeButton = document.createElement("button");
    beforeButton.className = "version-before";
    beforeButton.innerText = "<";
    beforeButton.addEventListener("click", () => {
        versionSlider.value = Math.max(0, parseInt(versionSlider.value) - 1).toString();
        versionSlider.dispatchEvent(new Event('input'));
    });

    const afterButton = document.createElement("button");
    afterButton.className = "version-after";
    afterButton.innerText = ">";
    afterButton.addEventListener("click", () => {
        versionSlider.value = Math.min(program.versions.length - 1, parseInt(versionSlider.value) + 1).toString();
        versionSlider.dispatchEvent(new Event('input'));
    });

    versionSliderContainer.appendChild(beforeButton);
    versionSliderContainer.appendChild(minVersionLabel);
    versionSliderContainer.appendChild(versionSlider);
    versionSliderContainer.appendChild(maxVersionLabel);
    versionSliderContainer.appendChild(afterButton);

    // Add error message
    const errorMessage = document.createElement('div');
    errorMessage.className = 'error-message';
    errorMessage.innerHTML = ansi_up.ansi_to_html(program.versions[0].stderr);

    // Add event listener to slider
    versionSlider.addEventListener('input', function () {
        const versionIndex = parseInt(this.value);
        errorMessage.innerHTML = ansi_up.ansi_to_html(program.versions[versionIndex].stderr);
        currentVersionLabel.textContent = program.versions[versionIndex].release;
    });

    // Add current version display
    const currentVersionContainer = document.createElement('div');
    currentVersionContainer.style.textAlign = 'center';
    currentVersionContainer.style.marginBottom = '10px';
    currentVersionContainer.appendChild(currentVersionLabel);

    errorContainer.appendChild(versionSliderContainer);
    errorContainer.appendChild(currentVersionContainer);
    errorContainer.appendChild(errorMessage);

    errorWidget.appendChild(errorContainer);
    hljs.highlightAll();
}

document.addEventListener('DOMContentLoaded', async function () {
    const response = await fetch("/assets/posts/rustc-error-evolution/errors.json");
    const data = await response.json();

    const selectBox = document.getElementById("programs");
    showErrorWidget(data, selectBox.value);

    selectBox.addEventListener("change", () => {
        showErrorWidget(data, selectBox.value);
    });
});

// Helper function to escape HTML
function escapeHtml(unsafe) {
    return unsafe
        .replace(/&/g, "&amp;")
        .replace(/</g, "&lt;")
        .replace(/>/g, "&gt;")
        .replace(/"/g, "&quot;")
        .replace(/'/g, "&#039;");
}
